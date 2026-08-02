# `A_JumpIfCloser (float distance, state label)` / `A_JumpIfCloser (float distance, int offset)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_JumpIfCloser` (retrieved 2026-07-31, oldid=44127) + verified against Zandronum source's `src/thingdef/thingdef_codeptr.cpp:875-896` and `src/thingdef/thingdef_codeptr.cpp:856-873` (`DoJumpIfCloser` helper).
**Bucket:** AActor — callable from any actor's state table. Shared implementation via the `DoJumpIfCloser()` helper, which also backs `A_JumpIfTracerCloser` and `A_JumpIfMasterCloser`.

Jumps to a target state (or forward by an offset) if the calling actor's target is closer than a specified distance.

## Parameters

- **`distance`** (float, fixed-point units) — Threshold distance for the jump. The distance calculation uses octagonal approximation (via `P_AproxDistance`, not true Euclidean), so the actual "radius" of the test varies slightly with angle. Units match the actor radius convention (where Doom map units are `FRACUNIT` units internally).
- **`label` or `offset`** — Target state label or state offset to jump to if the condition is met. Two overloads: pass a string (quoted in DECORATE) to jump to a named state, or an integer offset to jump forward by that many frame states from the current one.

## Wiki/engine divergence

The source ZDoom wiki describes an optional third parameter, `noz` (boolean), to disable vertical distance checking. **This parameter does not exist in Zandronum 3.2.1** — attempting to pass it causes a parse error. Vertical distance is always checked in Zandronum's implementation (unless both z-comparison branches in the condition happen to be false, which is an edge case with actor positioning).

## Behavior notes

- **Distance calculation does not account for actor radius.** Both the calling actor and its target are treated as points. If either or both actors are very wide (large radius), it's possible the jump condition can never be met. Workaround: increase the distance threshold to account for radii, e.g. `A_JumpIfCloser(radius + desired_dist, "label")`.
- **Player-specific behavior for weapons/inventory.** When called from a weapon or inventory item state (i.e., from a PSprite), the "target" is determined by `P_BulletSlope()` — the actor in the player's crosshair — not the calling actor's `target` field. For non-player actors, the target is always `self->target`.
- **Network synchronization.** In multiplayer, the jump decision is server-authoritative, but clients receive a position synchronization update (`CLIENTUPDATE_FRAME|CLIENTUPDATE_POSITION`) to keep the actor state aligned after a jump occurs. In client-mode (when `NETWORK_InClientMode()` is true), the early-return gate checks `NETFL_CLIENTSIDEONLY` on the actor's network flags — if the actor is not client-side only, the function returns without executing, deferring the jump decision to the server.

## See also

- `A_JumpIfTracerCloser` — same logic applied to the actor's `tracer` field instead of its `target`.
- `A_JumpIfMasterCloser` — same logic applied to the actor's `master` field instead of its `target`.
