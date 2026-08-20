# `A_JumpIfTracerCloser (float distance, state label)` / `A_JumpIfTracerCloser (float distance, int offset)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_JumpIfTracerCloser` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_JumpIfTracerCloser&oldid=44216) + verified against Zandronum source's `src/thingdef/thingdef_codeptr.cpp:898-901` and `src/thingdef/thingdef_codeptr.cpp:856-873` (`DoJumpIfCloser` helper).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** AActor — callable from any actor's state table. Shared implementation via the `DoJumpIfCloser()` helper, which also backs `A_JumpIfCloser` and `A_JumpIfMasterCloser`.

Jumps to a target state (or forward by an offset) if the calling actor's tracer is closer than a specified distance.

## Parameters

- **`distance`** (float, fixed-point units) — Threshold distance for the jump. The distance calculation uses octagonal approximation (via `P_AproxDistance`, not true Euclidean), so the actual "radius" of the test varies slightly with angle. Units match the actor radius convention (where Doom map units are `FRACUNIT` units internally).
- **`label` or `offset`** — Target state label or state offset to jump to if the condition is met. Two overloads: pass a string (quoted in DECORATE) to jump to a named state, or an integer offset to jump forward by that many frame states from the current one.

## Wiki/engine divergence

The source ZDoom wiki describes an optional third parameter, `noz` (boolean), to disable vertical distance checking. **This parameter does not exist in Zandronum 3.2.1** — attempting to pass it causes a parse error. Vertical distance is always checked in Zandronum's implementation (unless both z-comparison branches in the condition happen to be false, which is an edge case with actor positioning).

## Engine-family divergence: `noz` parameter

UZDoom implements `A_JumpIfTracerCloser` in ZScript as `action state A_JumpIfTracerCloser(double distance, statelabel label, bool noz = false)` (the UZDoom source's `wadsrc/static/zscript/actors/checks.zs:81`), delegating to a shared `CheckIfCloser()` helper (same file, line 53) that also backs `A_JumpIfCloser` and `A_JumpIfMasterCloser` — the same shared-implementation pattern Zandronum uses via `DoJumpIfCloser()`. Unlike Zandronum, UZDoom's `noz` parameter genuinely exists and matches the ZDoom Wiki's description in the "Wiki/engine divergence" section above: when `true`, the helper's condition (`Distance2D(targ) < dist && (noz || <z-check>)`) short-circuits past the vertical-distance check entirely, so only the 2D distance is tested. The "does not exist" claim in that section is Zandronum-specific; on UZDoom, `A_JumpIfTracerCloser(distance, "label", true)` compiles and disables the z check as documented by the wiki.

## Engine-family divergence: distance calculation

UZDoom's distance test uses `Actor.Distance2D()`, whose native implementation is `(Pos().XY() - otherpos.XY()).Length()` (the UZDoom source's `src/playsim/actor.h:1042-1046`) — a true Euclidean 2D distance. This differs from Zandronum's `P_AproxDistance` octagonal approximation described in the Parameters section above: on UZDoom the threshold is an exact circular radius around the tracer with no per-angle approximation error, whereas on Zandronum the effective test radius varies slightly with angle.

## Engine-family divergence: no network authority split

The "Network synchronization" behavior note below (server-authoritative jump decision, `NETWORK_InClientMode()` gate, `NETFL_CLIENTSIDEONLY` check, `CLIENTUPDATE_FRAME|CLIENTUPDATE_POSITION` sync) is Zandronum-specific netcode. UZDoom's source tree has zero occurrences of `NETWORK_InClientMode`, `NETFL_CLIENTSIDEONLY`, or `CLIENTUPDATE_FRAME` anywhere — `A_JumpIfTracerCloser` is plain ZScript with no client-mode branch, evaluated identically regardless of network role.

## Behavior notes

- **No tracer = no jump.** If `self->tracer` is `NULL`, the function returns without jumping, regardless of the distance threshold. A check for a valid tracer is required before calling this function if your code expects conditional behavior.
- **Distance calculation does not account for actor radius.** Both the calling actor and its tracer are treated as points. If either or both actors are very wide (large radius), it's possible the jump condition can never be met. Workaround: increase the distance threshold to account for radii, e.g. `A_JumpIfTracerCloser(radius + desired_dist, "label")`.
- **Network synchronization.** In multiplayer, the jump decision is server-authoritative, but clients receive a position synchronization update (`CLIENTUPDATE_FRAME|CLIENTUPDATE_POSITION`) to keep the actor state aligned after a jump occurs. In client-mode (when `NETWORK_InClientMode()` is true), the early-return gate checks `NETFL_CLIENTSIDEONLY` on the actor's network flags — if the actor is not client-side only, the function returns without executing, deferring the jump decision to the server.

## See also

- `A_JumpIfCloser` — same logic applied to the actor's `target` field instead of its `tracer`.
- `A_JumpIfMasterCloser` — same logic applied to the actor's `master` field instead of its `tracer`.
