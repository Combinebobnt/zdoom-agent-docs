# `A_NoBlocking` / `A_Fall` (actor unblocking and item drops)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `A_NoBlocking` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_NoBlocking&oldid=53222) + verified against the Zandronum source's `src/p_enemy.h:60`, `src/g_shared/a_action.cpp:72-128` and `130-138`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_NoBlocking)` and `DEFINE_ACTION_FUNCTION(AActor, A_Fall)` in `src/g_shared/a_action.cpp` — both wrap `A_Unblock()` implemented at `src/g_shared/a_action.cpp:72-128`.

Marks an actor as no longer blocking collision and spawns any items attached to the actor (dialogue-set drops and regular drop items). `A_Fall` is Doom's original name for this function; both names are equivalent in Zandronum.

**Zandronum-specific:** In multiplayer, the `MF_SOLID` flag clear is **server-side only** — clients return early from this action until the server replicates the change via `SERVERCOMMANDS_SetThingFlags`. This means a client-side actor remains solid locally until network synchronization arrives. See "Network synchronization" below.

## Signature

```text
void A_NoBlocking()
void A_Fall()
```

## Behavior

When called, the action performs these steps:

1. **Stealth handling**: If the actor has the `MF_STEALTH` flag set, sets its alpha to fully opaque (`OPAQUE` = 1.0) and clears stealth-tracking state.

2. **Solid flag clear**: Removes the `MF_SOLID` flag, making the actor non-blocking to other objects. (In multiplayer, this happens server-side; clients don't execute this until the server replicates it — see "Network synchronization" below.)

3. **Dialogue-set drop priority**: If the actor's `Conversation` field is set (assigned via a dialogue lump), spawns the dialogue's associated drop item (`Conversation->DropType`) at a fixed height and immediately clears the `Conversation` field, then **returns** — skipping the regular drop item list.

4. **Regular drop items**: If the actor has a `DropItem` list and the `Conversation` field was not set (step 3 didn't return), iterates the list and spawns each item according to its probability roll. This list is **not** cleared, so subsequent calls to `A_NoBlocking` will spawn the items again (or the action could be called multiple times if the actor remains in a state that calls it).

5. **PlayerPawn exclusion**: Regular drop items (step 4) are not spawned if the actor is a `PlayerPawn` or a subclass of it.

## Parameters

None. Unlike the ZDoom/UZDoom/GZDoom-family versions, Zandronum's `A_NoBlocking` takes no optional parameters — it always spawns drop items (step 4 above always happens unless Conversation was set). The wiki describes an optional `drop` parameter present in upstream engines; **Zandronum does not support this**.

## Drop item behavior

**Dialogue-set vs. regular drops (from the source):** The action prioritizes dialogue-set drops. If both exist, only the dialogue-set item spawns on the current call; the `Conversation` field is cleared, so all subsequent calls spawn regular items instead. If only regular items exist, they spawn on every call until manually cleared.

**Probability rolls:** Both dialogue-set and regular drop items spawn at a fixed 256-unit height offset from the actor, and probability is rolled per-item in the regular list (dialogue-set drops have a fixed drop type, no probability). See the "Creating monsters" concept page for the verified `DropItem` roll mechanism and the idiom that `256` represents "always drop".

## Network synchronization

**Zandronum multiplayer only.** The `A_Unblock` function (which both `A_NoBlocking` and `A_Fall` call) has a server-mode check: in client mode, it returns early without clearing the `MF_SOLID` flag locally. The server separately replicates the flag clear via `SERVERCOMMANDS_SetThingFlags`, and stealth-visibility changes via `SERVERCOMMANDS_FlashStealthMonster`.

**Implication:** In a networked game, if a client-side pawn (a player's actor) calls `A_NoBlocking`, the client's local collision will remain solid until the server's replication arrives. For server-side monsters and projectiles, this is transparent (the server decides when to call the action), but in any `+CLIENTSIDEONLY` actor or a client-run state callback, items/projectiles can still collide with the actor briefly until the network catch-up.

## Engine-family divergence: `drop` parameter support

UZDoom's `A_NoBlocking` exposes an optional `bool drop = true` parameter — declared `native void A_NoBlocking(bool drop = true);` in `wadsrc/static/zscript/actors/actor.zs`, and thunked via `DEFINE_ACTION_FUNCTION_NATIVE(AActor, A_NoBlocking, A_Unblock)` in `src/scripting/vmthunks_actors.cpp`, which pulls a `PARAM_BOOL(drop)` from the DECORATE/ZScript call site and forwards it straight to `A_Unblock`. Calling `A_NoBlocking(false)` skips step 4 above (the regular `DropItem` list) while the `MF_SOLID` clear, stealth handling, and any dialogue-set drop (step 3) still happen unconditionally. `A_Fall` stays a plain wrapper with no exposed parameter of its own (`void A_Fall() { A_NoBlocking(); }` in `actor.zs`, always passing the default `true`). This confirms — rather than contradicts — what the "Parameters" section above already anticipated from the wiki: UZDoom is exactly the "ZDoom/UZDoom/GZDoom-family" upstream the wiki's optional-parameter description refers to, and it does support it. Zandronum does not: its `DEFINE_ACTION_FUNCTION(AActor, A_NoBlocking)` wrapper (`src/g_shared/a_action.cpp:130-133`) always calls `A_Unblock(self, true)` and never exposes a `drop` parameter to DECORATE, even though the underlying `A_Unblock` C++ function accepts one.

## Engine-family divergence: no client/server authority split

UZDoom's `A_Unblock` (`src/playsim/a_action.cpp:40-82`) unconditionally clears `MF_SOLID` and updates stealth alpha/`visdir` — there is no client-mode gate, and no equivalent of Zandronum's `NETWORK_InClientMode` check or `SERVERCOMMANDS_SetThingFlags`/`SERVERCOMMANDS_FlashStealthMonster` replication calls exists anywhere in the UZDoom source tree (confirmed by a tree-wide grep for both symbols). The entire "Network synchronization" section above, and the header's "Zandronum-specific" callout, are therefore Zandronum-only behavior: on UZDoom, `A_NoBlocking`/`A_Fall` take effect immediately and identically regardless of caller or connection role, with no server-replication lag for a client-side actor to catch up on.

## Alternatives

- **`A_ScreamAndUnblock`** — a composite action that calls `A_Scream` followed by `A_Unblock`, used in standard death states (e.g., `A_Scream` plays a sound, then `A_NoBlocking` unblocks and drops items).
- **`+NODROPOFF` actor flag** — affects actor movement constraints, not item drops; see the "Creating monsters" concept for flag bundles.

## Related

- `A_ScreamAndUnblock` — calls `A_Scream` then `A_NoBlocking` in sequence.
- `A_Scream` — plays the actor's death sound without unblocking.
- `A_FreezeDeathChunks` — an unrelated Hexen-specific action that also calls `A_Unblock` at its end.
- **DECORATE concept:** "Creating monsters" — covers `DropItem`, `Monster` property, and other death-related mechanics.
