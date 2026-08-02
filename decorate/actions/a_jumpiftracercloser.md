# `A_JumpIfTracerCloser (float distance, state label)` / `A_JumpIfTracerCloser (float distance, int offset)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_JumpIfTracerCloser` (retrieved 2026-08-01, oldid=44216) + verified against Zandronum source's `src/thingdef/thingdef_codeptr.cpp:898-901` and `src/thingdef/thingdef_codeptr.cpp:856-873` (`DoJumpIfCloser` helper).
**Bucket:** AActor — callable from any actor's state table. Shared implementation via the `DoJumpIfCloser()` helper, which also backs `A_JumpIfCloser` and `A_JumpIfMasterCloser`.

Jumps to a target state (or forward by an offset) if the calling actor's tracer is closer than a specified distance.

## Parameters

- **`distance`** (float, fixed-point units) — Threshold distance for the jump. The distance calculation uses octagonal approximation (via `P_AproxDistance`, not true Euclidean), so the actual "radius" of the test varies slightly with angle. Units match the actor radius convention (where Doom map units are `FRACUNIT` units internally).
- **`label` or `offset`** — Target state label or state offset to jump to if the condition is met. Two overloads: pass a string (quoted in DECORATE) to jump to a named state, or an integer offset to jump forward by that many frame states from the current one.

## Wiki/engine divergence

The source ZDoom wiki describes an optional third parameter, `noz` (boolean), to disable vertical distance checking. **This parameter does not exist in Zandronum 3.2.1** — attempting to pass it causes a parse error. Vertical distance is always checked in Zandronum's implementation (unless both z-comparison branches in the condition happen to be false, which is an edge case with actor positioning).

## Behavior notes

- **No tracer = no jump.** If `self->tracer` is `NULL`, the function returns without jumping, regardless of the distance threshold. A check for a valid tracer is required before calling this function if your code expects conditional behavior.
- **Distance calculation does not account for actor radius.** Both the calling actor and its tracer are treated as points. If either or both actors are very wide (large radius), it's possible the jump condition can never be met. Workaround: increase the distance threshold to account for radii, e.g. `A_JumpIfTracerCloser(radius + desired_dist, "label")`.
- **Network synchronization.** In multiplayer, the jump decision is server-authoritative, but clients receive a position synchronization update (`CLIENTUPDATE_FRAME|CLIENTUPDATE_POSITION`) to keep the actor state aligned after a jump occurs. In client-mode (when `NETWORK_InClientMode()` is true), the early-return gate checks `NETFL_CLIENTSIDEONLY` on the actor's network flags — if the actor is not client-side only, the function returns without executing, deferring the jump decision to the server.

## See also

- `A_JumpIfCloser` — same logic applied to the actor's `target` field instead of its `tracer`.
- `A_JumpIfMasterCloser` — same logic applied to the actor's `master` field instead of its `tracer`.
