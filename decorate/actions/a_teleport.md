# `A_Teleport` (actor teleportation)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_Teleport` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_Teleport&oldid=44219) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:5221-5287`, `wadsrc/static/actors/actor.txt:252`, `src/p_map.cpp:352-474` (`P_TeleportMove`), `src/g_shared/a_specialspot.cpp:156-174,261-281`, `src/thingdef/thingdef_parse.cpp:124-145`, `src/thingdef/thingdef_expression.cpp:2740-2757`, `src/thingdef/thingdef_codeptr.cpp:695-753` (`DoJump`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_Teleport)` in `src/thingdef/thingdef_codeptr.cpp`.

Attempts to teleport the calling actor to a random `SpecialSpot`-derived actor (or any actor type specified via `targettype`) within a specified distance range. On successful teleport, spawns a fog actor at the departure location and jumps the actor to a specified state (UZDoom's `TF_NOJUMP` can skip the jump). On Zandronum, nothing happens if no valid spot is found or if no target state resolves (an unknown state label also prints a "Jump target ... not found" console message at runtime).

## Engine-family divergence

**Zandronum vs. UZDoom/GZDoom-family:** The wiki page describes ZDoom/UZDoom behavior, which includes many flags and parameters that **do not exist in Zandronum 3.2.1**. See "Zandronum-only parameters and flags" below. If you are writing DECORATE for Zandronum, only use the listed flags and parameters. Writing an absent flag's name is an unknown-identifier error that aborts startup, and passing the wiki's 7th `ptr` argument is a fatal parse error (`Expected ')', got ','.`). Only raw numeric flag bits other than 1 and 2 are silently ignored.

(Verified directly against UZDoom's own `A_Teleport` implementation, not just the wiki: every flag and the `ptr` parameter listed below as wiki-only does in fact exist in UZDoom's `T_Flags`/parameter declarations — see the further divergences below for behavioral specifics the wiki page and this file's Zandronum-only sections don't otherwise surface.)

## Engine-family divergence: fog spawning, state-jump gating, and network authority

Three further Zandronum-vs-UZDoom behavioral differences, found verifying `A_Teleport`'s own UZDoom implementation directly (`src/playsim/p_actionfunctions.cpp`) rather than inferred from the flag-existence list above:

- **Destination fog also spawns by default on UZDoom.** With `flags=0` and the default `fogtype` of `TeleportFog`, UZDoom's implementation spawns a fog actor at *both* the departure location (unless `TF_NOSRCFOG`) and the arrival location (unless `TF_NODESTFOG`). Zandronum's implementation (see "Teleportation process" below) only ever spawns a fog at the departure location — it has no destination-fog spawn at all, consistent with `TF_NODESTFOG` not existing there.
- **A missing/invalid `teleportstate` blocks the move itself on Zandronum, but not on UZDoom.** Zandronum resolves `teleportstate` (falling back to a "Teleport" state, then failing) *before* it ever searches for a spot or attempts the move — no valid state means the actor never teleports at all. UZDoom resolves `teleport_state` *after* the move, fog spawn, and Z/angle/velocity updates have already happened (inside the post-move success branch, immediately before the state jump) — so on UZDoom the actor does teleport (new position, fog, zeroed velocity, facing the spot) even with no valid target state; only the state jump itself is skipped. The "nothing happens... if no target state resolves" framing in this file's intro and "Teleportation process" section is accurate for Zandronum only.
- **No client/server authority split on UZDoom.** Zandronum's implementation returns immediately on a client unless the actor is client-side-only, so in a networked game the server runs it (see "Network behavior" below). UZDoom's implementation has no equivalent check and runs unconditionally wherever it's called, consistent with UZDoom having no client/server authority split anywhere in its source tree.

## Signature (Zandronum)

```text
A_Teleport [(state teleportstate [, class targettype [, class fogtype [, int flags
            [, float mindist [, float maxdist]]]]])]
```

Declared in `wadsrc/static/actors/actor.txt:252` with defaults `teleportstate = ""` (use the `Teleport` label), `targettype = "BossSpot"`, `fogtype = "TeleportFog"`, `flags = 0`, `mindist = 128`, `maxdist = 0`. There is no return value; Zandronum DECORATE has no return values. Call it bare (`A_Teleport`) to take every default: empty parentheses `A_Teleport()` are a parse error on Zandronum.

Note: The wiki lists a 7th parameter `ptr` for actor-pointer semantics (determining who gets teleported) and many additional flags. These **do not exist in Zandronum**.

## Parameters (Zandronum only)

### `teleportstate` (state, optional)

The state label to jump to after a successful teleport. If `""`, `"None"`, `0`, omitted, or not found on the calling actor, the function falls back to the actor's "Teleport" state. If no "Teleport" state exists either, the function returns without teleporting. A label that doesn't exist is not silent: it prints `Jump target '...' not found in <class>` to the console each time it is evaluated.

- **Note:** Empty string (`""`) on the wiki means "use Teleport state"; Zandronum treats `""` and `"None"` the same way. A bare `NULL` is not accepted: the state parameter must be a quoted string or an integer offset.

### `targettype` (actor class, optional)

The actor class to search for as a valid teleport destination. Defaults to `BossSpot` if omitted or `"None"`. Only `SpecialSpot`-derived actors register themselves in the spot list, and the lookup matches the exact class only: instances of a subclass of `targettype` are not found. Zandronum's parser only checks that the name is an actor class, so a non-`SpecialSpot` class loads fine and simply never finds a spot; an unknown class name prints a load-time warning.

The search (`GetSpotWithMinMaxDistance`) starts at a random index in that class's spot list and takes the first spot, walking the list in order, whose distance satisfies `mindist`/`maxdist`. The pick is therefore not uniform when only some spots are in range.

### `fogtype` (actor class, optional)

The actor class to spawn at the departure location (the actor's old position before teleporting). Defaults to `TeleportFog` if omitted. Pass `"None"` to spawn no fog. There is no `TF_NOSRCFOG` flag on Zandronum.

### `flags` (int, optional)

Bitfield controlling teleport behavior. Flags are combined using `|`. **Only 2 flags exist in Zandronum**; see "Flags listed in the wiki but NOT in Zandronum" for a complete list of what this section does *not* support.

#### Zandronum-only flags (Zandronum 3.2.1)

- `TF_TELEFRAG` (1) — Lets the teleporting actor telefrag: shootable actors overlapping the destination take telefrag damage and the move goes ahead. Without this flag, an overlapping shootable actor makes the teleport fail, unless the caller has `+TELESTOMP`, the map allows monster telefrags, or the occupant has `+ALWAYSTELEFRAG`. `+NOTELESTOMP` on the caller disables telefragging even with the flag, and a `+NOTELEFRAG` occupant always blocks the teleport. Non-shootable actors never block.

- `TF_RANDOMDECIDE` (2) — Randomly fail teleportation based on the actor's current health ratio, like `A_Srcr2Decide`. Uses the following decision table (health as a fraction of spawn health, mapped to success chance):

  | Health / SpawnHealth | Success probability |
  |---|---|
  | 8/8 or more | 0% (always fail) |
  | 7/8 | 6.25% |
  | 6/8 | 12.5% |
  | 4/8 | 25% |
  | 1/8 | 46.875% |
  | Less than 1/8 | 75% |

  This simulates a "desperation teleport" pattern where weak or injured actors are more likely to escape.

### `mindist` (float, optional)

The minimum distance the teleport destination must be from the calling actor's current position. Defaults to **128**, so spots closer than that are skipped unless you pass a smaller value (pass `0` for no minimum). Measured in map units, horizontally only.

### `maxdist` (float, optional)

The maximum distance the teleport destination may be from the calling actor's current position. Defaults to 0, which means **no maximum limit** (can teleport to any distance). If `maxdist > 0`, destinations beyond this range are skipped.

Both bounds are inclusive and use the `P_AproxDistance` approximation, which over-estimates true distance by up to about 12%. A spot slightly inside `maxdist` can be rejected, and one slightly inside `mindist` can pass.

## Teleportation process

1. On a client, return immediately unless the actor is client-side-only.
2. If `TF_RANDOMDECIDE` is set, consult the health-ratio table above; if the roll fails, return without teleporting.
3. Resolve the `teleportstate` label (use specified state, or default to "Teleport", or return if not found).
4. Get or create the global `DSpotState` (the registry every `SpecialSpot` adds itself to when spawned).
5. Search for an actor of exactly type `targettype` (defaulting to `BossSpot`) within the `mindist`–`maxdist` range; return if none.
6. Attempt to move the actor to the spot's x/y/z via `P_TeleportMove()` (with `TF_TELEFRAG` gating telefrag behavior).
7. On success, in this order:
   - Spawn `fogtype` (if not `"None"`) at the old position.
   - Jump to `teleportstate`. The new state's own action runs here, before the next three steps.
   - Set the actor's Z position to the destination floor.
   - Set the actor's angle to face the spot's angle.
   - **Zero out the actor's velocity** (stops all movement; the wiki's `TF_KEEPVELOCITY` flag does *not exist in Zandronum*).
8. On failure (the move was blocked by an occupant), return with no state jump.

## Flags listed in the wiki but **NOT in Zandronum**

The following flags appear in the ZDoom/UZDoom wiki but are **not defined in Zandronum**. Using one of these names aborts startup with an unknown-identifier error; passing the equivalent numeric bit is silently ignored:

- `TF_FORCED` — ignore obstacles in the destination
- `TF_KEEPVELOCITY` — preserve actor velocity after teleport (Zandronum always zeros velocity)
- `TF_KEEPANGLE` — preserve actor angle instead of facing the destination spot's angle
- `TF_KEEPORIENTATION` — equivalent to `TF_KEEPVELOCITY | TF_KEEPANGLE`
- `TF_USESPOTZ` — use the destination spot's Z position instead of flooring
- `TF_NOSRCFOG` — skip spawning fog at departure location
- `TF_NODESTFOG` — skip spawning fog at destination
- `TF_NOFOG` — equivalent to `TF_NOSRCFOG | TF_NODESTFOG`
- `TF_USEACTORFOG` — use custom fog types from actor properties
- `TF_NOJUMP` — do not jump to state after teleport
- `TF_OVERRIDE` — allow teleporting even if actor has `NOTELEPORT` flag
- `TF_SENSITIVEZ` — fail teleport instead of adjusting Z position to avoid obstacles

If you need any of these behaviors in Zandronum, you will need to implement a custom action function or design a workaround (e.g., manually setting actor properties before calling a simpler `A_Teleport`).

## Related functions and concepts

- **`SpecialSpot`** — base actor class for teleport destination spots. Custom spots can inherit from `SpecialSpot` and be passed as `targettype`.
- **`BossSpot`** — the default teleport destination type if `targettype` is not specified.
- **`TeleportFog`** — the default fog actor spawned at departure and/or destination. Can be customized via the `fogtype` parameter.
- **`A_Srcr2Decide`** — another action that uses a health-ratio-based random decision (the basis for `TF_RANDOMDECIDE` logic).

## Special notes

### Network behavior (Zandronum multiplayer)

On a client, `A_Teleport` returns immediately unless the actor is client-side-only (`NETFL_CLIENTSIDEONLY`), so in a networked game only the server runs it. The only thing it sends is the state jump (`ACTION_JUMP(..., CLIENTUPDATE_FRAME)`): a `SetThingFrame` when called from the actor's own state, a weapon state jump from a weapon or flash state, and nothing from a CustomInventory state chain. Nothing sends the new position, angle or zeroed velocity, and the departure fog is a plain server-side spawn that clients never receive (unlike line/ACS teleports, which send an explicit teleport command, `src/p_teleport.cpp:241`). Clients see a monster's new position once the server sends its next movement update, e.g. when its chase logic picks a new direction (`P_DoNewChaseDir`, `src/p_enemy.cpp`). An actor that does not move afterwards stays at its old position on clients.

### Interaction with NOTELEPORT flag

On Zandronum, `A_Teleport` ignores the `NOTELEPORT` actor flag: neither it nor `P_TeleportMove` checks it, so an actor with `+NOTELEPORT` still teleports. On UZDoom, an actor with `NOTELEPORT` does not teleport unless `TF_OVERRIDE` is passed.

### Z-position adjustment

Zandronum always places the actor on the destination's floor: `P_TeleportMove` moves it to the spot's x/y/z, then `A_Teleport` sets its Z to the resulting floor height. The spot's own height does not survive, and there is no ceiling-fit check, so a destination too low for the actor does not make the teleport fail. There is no `TF_USESPOTZ` or `TF_SENSITIVEZ` flag to change this.

### No `PreTeleport`/`PostTeleport` interception (UZDoom)

UZDoom's `Actor` base class declares `PreTeleport`/`PostTeleport` virtuals (`wadsrc/static/zscript/actors/actor.zs`) that can cancel or react to a teleport — but they are invoked only by `FLevelLocals::EV_Teleport` (`src/playsim/p_teleport.cpp`), the line/sector-teleporter and ACS `Teleport()`-special code path. `A_Teleport` never calls `EV_Teleport`; it moves the actor directly via the lower-level `P_TeleportMove()` primitive (`src/playsim/p_map.cpp`), which has no hook calls at all. This does **not** carry over the ACS-side `Teleport()` special's documented `PreTeleport`/`PostTeleport` cancellation behavior: overriding `PreTeleport` to return `false`, or overriding `PostTeleport`, has no effect on a DECORATE `A_Teleport()` call, on UZDoom or otherwise.

## Example (Zandronum DECORATE)

```decorate
actor TeleportImp : DoomImp 601
{
  States
  {
  See:
    TROO AABBCCDD 3 A_Chase
    TROO A 0 A_Jump(8, "Teleport")
    Loop
  Teleport:
    TROO A 0 A_Teleport("See", "ImpSpot")
    Goto See
  }
}

actor ImpSpot : SpecialSpot 600
{
  +INVISIBLE
}
```

This example shows a simple teleportation pattern: while chasing, the imp occasionally jumps (via `A_Jump`) to its `Teleport` state, where `A_Teleport` searches for an `ImpSpot` at least 128 map units away (the default `mindist`). On success, it jumps to the explicitly passed "See" state. On failure, it falls through to `Goto See` and keeps chasing; ending that 0-tic state in `Loop` instead would loop it on itself with no tic delay. Because "See" is passed explicitly, the `Teleport` label is only used for the `A_Jump`, not as the fallback target.

## Wiki page source

This entry was adapted from the ZDoom Wiki page on `A_Teleport` (oldid=44219). The wiki describes features ahead of Zandronum 3.2.1 — notably the additional flags and the `ptr` parameter. Zandronum's simpler implementation supports only the core teleportation mechanic and the two listed flags.
