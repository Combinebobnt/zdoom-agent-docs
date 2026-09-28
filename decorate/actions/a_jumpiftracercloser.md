# `A_JumpIfTracerCloser (float distance, state label)` / `A_JumpIfTracerCloser (float distance, int offset)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki `A_JumpIfTracerCloser` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_JumpIfTracerCloser&oldid=44216) + verified against Zandronum source's `src/thingdef/thingdef_codeptr.cpp:898-901` and `src/thingdef/thingdef_codeptr.cpp:856-873` (`DoJumpIfCloser` helper), `src/thingdef/thingdef_codeptr.cpp:695-753` (`DoJump` client updates), `src/p_maputl.cpp:59-64` (`P_AproxDistance`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** AActor — callable from any actor's state table. Shared implementation via the `DoJumpIfCloser()` helper, which also backs `A_JumpIfCloser` and `A_JumpIfMasterCloser`.

Jumps to a target state (or forward by an offset) if the calling actor's tracer is closer than a specified distance.

## Parameters

- **`distance`** (float, map units; converted to fixed point internally) — Threshold distance for the jump. On Zandronum the horizontal distance uses an octagonal approximation (`P_AproxDistance`, `max + min/2`, not true Euclidean). It never under-estimates and over-estimates by up to about 11.8% (near 26.6 degrees off an axis), so the effective test radius is exact along the axes and up to about 10.6% smaller at those angles.
- **`label` or `offset`** — Target state label or state offset to jump to if the condition is met. Two overloads: pass a string (quoted in DECORATE) to jump to a named state, or an integer offset to jump forward by that many frame states from the current one.

## Wiki/engine divergence

The source ZDoom wiki describes an optional third parameter, `noz` (boolean), to disable vertical distance checking. **This parameter does not exist in Zandronum** (3.2.1 or 3.3-alpha). Passing it is a fatal DECORATE parse error (`Expected ')', got ','.`). Vertical distance is always checked in Zandronum's implementation: the vertical gap between the two actors' boxes (the caller's bottom to the tracer's top when the caller is higher, otherwise the tracer's bottom to the caller's top) must also be less than `distance`. Overlapping heights give a negative gap, which always passes.

## Engine-family divergence: `noz` parameter

UZDoom implements `A_JumpIfTracerCloser` in ZScript as `action state A_JumpIfTracerCloser(double distance, statelabel label, bool noz = false)` (the UZDoom source's `wadsrc/static/zscript/actors/checks.zs:81`), delegating to a shared `CheckIfCloser()` helper (same file, line 53) that also backs `A_JumpIfCloser` and `A_JumpIfMasterCloser` — the same shared-implementation pattern Zandronum uses via `DoJumpIfCloser()`. Unlike Zandronum, UZDoom's `noz` parameter genuinely exists and matches the ZDoom Wiki's description in the "Wiki/engine divergence" section above: when `true`, the helper's condition (`Distance2D(targ) < dist && (noz || <z-check>)`) short-circuits past the vertical-distance check entirely, so only the 2D distance is tested. The "does not exist" claim in that section is Zandronum-specific; on UZDoom, `A_JumpIfTracerCloser(distance, "label", true)` compiles and disables the z check as documented by the wiki.

## Engine-family divergence: distance calculation

UZDoom's distance test uses `Actor.Distance2D()`, whose native implementation is `(Pos().XY() - otherpos.XY()).Length()` (the UZDoom source's `src/playsim/actor.h:1042-1046`) — a true Euclidean 2D distance. This differs from Zandronum's `P_AproxDistance` octagonal approximation described in the Parameters section above: on UZDoom the threshold is an exact circular radius around the tracer with no per-angle approximation error, whereas on Zandronum the effective test radius varies slightly with angle.

## Engine-family divergence: no network authority split

The "Network synchronization" behavior note below (`CLIENTUPDATE_FRAME|CLIENTUPDATE_POSITION` updates sent by the server on a jump) is Zandronum-specific netcode. UZDoom's source tree has zero occurrences of `NETWORK_InClientMode`, `NETFL_CLIENTSIDEONLY`, or `CLIENTUPDATE_FRAME` anywhere — `A_JumpIfTracerCloser` is plain ZScript with no client-mode branch, evaluated identically regardless of network role.

## Behavior notes

- **No tracer = no jump.** If `self->tracer` is `NULL`, the function returns without jumping, regardless of the distance threshold. A check for a valid tracer is required before calling this function if your code expects conditional behavior.
- **Distance calculation does not account for actor radius.** Horizontally, both the calling actor and its tracer are treated as points (only the vertical check uses their heights). If either or both actors are very wide (large radius), it's possible the jump condition can never be met. Workaround: increase the distance threshold to account for radii, e.g. `A_JumpIfTracerCloser(radius + desired_dist, "label")`.
- **Network synchronization (Zandronum).** Unlike `A_JumpIfCloser`, this function has no client-mode gate: clients run the check too, against their own `tracer` pointer. The protocol never sends `tracer`, so a client's copy is only whatever its own simulation set. When the server jumps from the actor's own state, it sends clients the new frame plus an x/y/z position update (`CLIENTUPDATE_FRAME|CLIENTUPDATE_POSITION`). From a player's weapon or flash state it sends a weapon state jump instead, and from a CustomInventory state chain it sends nothing.

## See also

- `A_JumpIfCloser` — same logic applied to the actor's `target` field instead of its `tracer`.
- `A_JumpIfMasterCloser` — same logic applied to the actor's `master` field instead of its `tracer`.
