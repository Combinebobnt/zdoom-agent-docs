# A toucher's position change during a pickup's touch handler gets overwritten

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** The mechanism itself (the call-stack trace and the position-overwrite behavior) is
source-verified end-to-end against `src/p_map.cpp`, `src/p_interaction.cpp`,
`src/g_shared/a_pickups.cpp`, and `src/p_acs.cpp` (2026-08-01) and holds regardless of what
prompted the investigation. Not a wiki-intake page — this is engine behavior no wiki documents.
**Attribution:** this was written up while investigating a real reported bug — a `CustomInventory`
item whose `Pickup:` chain called ACS `SetActorPosition` on the toucher appeared to have no lasting
effect. **Confirmed as the actual cause of that historical bug**: the affected item was
`CustomInventory`-derived at the time and triggered its position-setting ACS call from `Pickup:`
(reached by the toucher walking into it), matching this mechanism exactly. The project later
reworked the item to trigger from a `Spawn:` state proximity check instead of native touch, which
(as a side effect of no longer routing through `Pickup:`/`P_TryMove` at all) resolved it — see
[`SetActorPosition`](../../acs/functions/setactorposition.md)'s own restore-on-blocked-destination
behavior for a second, distinct mechanism confirmed to still cause an occasional, much rarer
position-not-applied symptom in that reworked code, unrelated to this one.

## The mechanism

Touching an item by walking into it runs entirely inside the mover's own `P_TryMove` call, nested
several frames deep:

```
P_TryMove(thing, x, y, ...)                    // src/p_map.cpp:1889 — x, y captured as locals
  → P_CheckPosition(thing, x, y, tm)           // pure query: "can thing legally reach x, y?"
    → PIT_CheckThing(...)                      // src/p_map.cpp:1354, per nearby-item blockmap entry
      → P_TouchSpecialThing(item, thing)       // src/p_interaction.cpp:123
        → AInventory::Touch → CallTryPickup → <item class>::TryPickup
          → (for CustomInventory) CallStateChain runs the Pickup: state chain
            → any action/ACS call in that chain can move `thing` (the toucher) right now
  // P_CheckPosition returns true — MF_SPECIAL pickups never block a move, pickup outcome
  // (success or failure) plays no part in this
  // back in P_TryMove, src/p_map.cpp:2146-2158:
  thing->UnlinkFromWorld();
  ...
  thing->x = x;      // <-- the ORIGINAL destination captured at entry, before any of the above ran
  thing->y = y;
  thing->LinkToWorld();
```

`P_TryMove`'s `x`/`y` parameters are locals fixed before `P_CheckPosition` (and everything nested
under it, including the entire pickup touch) ever runs. When that nested code changes `thing->x`/
`thing->y` — e.g. an ACS `SetActorPosition` call (`PCD_SETACTORPOSITION`, `src/p_acs.cpp:11987`,
which calls `P_MoveThing`, `src/p_things.cpp:164`, which calls `AActor::SetOrigin` directly) run
from a `CustomInventory` item's `Pickup:` chain via `ACS_NamedExecuteWithResult` — that change is
silently discarded a few dozen lines later when `P_TryMove` finishes the move it was already
computing and stamps `thing->x = x; thing->y = y;` unconditionally.

## Why this isn't tied to the pickup's success or failure

Pickup items are non-solid (`MF_SPECIAL`, not `MF_SOLID`), so `PIT_CheckThing` never treats a
touch as blocking regardless of whether the touched item's `TryPickup` ultimately returns true or
false — see the `solid = ...` computation and the unconditional `P_TouchSpecialThing` call in
`PIT_CheckThing`, `src/p_map.cpp:1338-1351`. `P_CheckPosition` therefore returns `true` and
`P_TryMove` reaches its position-finalizing block **the same way whether the `Pickup:` chain
succeeded or failed.** If a mod's `Pickup:` chain only calls `SetActorPosition` from one branch
(commonly the failure branch — "reject the pickup and knock the player back/away"), the visible
symptom lines up with "the position resets on failure," but that's a property of which branch
happens to call `SetActorPosition`, not something the engine decides based on the chain's result.
Any `Pickup:`-triggered position change on the toucher is discarded this way, success or failure
alike.

## Scope: `Pickup:` triggered by movement, not `Use:` or a stationary touch

This specific clobbering only applies when the touch happens **as a side effect of the toucher's
own `P_TryMove` call** — i.e. walking into the item. It does not apply to:
- **`Use:`** (`ACustomInventory::Use`, called from `AActor::UseInventory`) — reached from ticcmd
  handling (`d_net.cpp`, `cl_main.cpp`, `sv_main.cpp`), never from inside `P_TryMove`. A
  `SetActorPosition` call from a `Use:` chain is not subject to this overwrite.
- **A stationary item given directly** (`A_GiveInventory` spawning and immediately granting an
  item with no intervening `P_TryMove` on the receiver) — same reasoning: no enclosing `P_TryMove`
  call to clobber the position afterward.

## Fix/avoidance

Don't set the toucher's own position synchronously from inside a `Pickup:` chain reached by
walking into the item — it will be overwritten before the tic ends. Options that avoid the
enclosing `P_TryMove` call entirely:
- Do the position change from a `Use:` chain instead, if the design can require the player to
  activate the item rather than just touch it.
- Have the `Pickup:` chain only set a flag/counter (inventory item, user variable, or ACS global),
  and perform the actual `SetActorPosition` from a separate script tick (e.g. a per-tic `ENTER`/
  looping script polling that flag) that runs outside the touching player's own `P_TryMove` call
  entirely.

## See also

- [CustomInventory](../classes/custominventory.md) — the class whose `Pickup:` chain is the
  practical way to get arbitrary ACS to run from inside a touch; its own "no rollback" findings are
  a related but distinct mechanism (`CallStateChain` never undoes an action's side effects), not
  the cause of this specific position-overwrite behavior.
- [Crash-and-bug checklist](crash-and-bug-checklist.md) — the terse review-index entry for this
  pattern.
