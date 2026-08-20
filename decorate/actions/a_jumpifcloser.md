# `A_JumpIfCloser (float distance, state label)` / `A_JumpIfCloser (float distance, int offset)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `A_JumpIfCloser` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_JumpIfCloser&oldid=44127) + verified against Zandronum source's `src/thingdef/thingdef_codeptr.cpp:875-896` and `src/thingdef/thingdef_codeptr.cpp:856-873` (`DoJumpIfCloser` helper).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
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

## Engine-family divergence: distance calculation

The "Distance calculation does not account for actor radius" note above describes Zandronum's `P_AproxDistance`, an octagonal (Doom-classic) approximation of 2D distance, not a true Euclidean calculation. **UZDoom's `A_JumpIfCloser` uses true Euclidean distance instead** — the underlying `CheckIfCloser()` helper compares against `Distance2D()`, which computes `(pos.xy - target.pos.xy).Length()` (an exact `sqrt(dx*dx + dy*dy)`). The two engines' distance thresholds therefore don't line up exactly at all angles: `P_AproxDistance` over-estimates true distance by up to ~6% at a 45° angle (its `max + 3*min/8` formula peaks at `1.5x` the true diagonal distance vs. Euclidean's `~1.414x`) and is exact only along the axes, so a jump right at the threshold can trigger slightly earlier or later on one engine than the other for diagonal approaches. The vertical (z) portion of the check is unaffected by this — the two engines compute the same z-clamp formula (see Behavior notes above). The threshold parameter itself is also declared differently (Zandronum's `ACTION_PARAM_FIXED` fixed-point vs. UZDoom's native `double`), but both represent the same map-unit value to a modder writing DECORATE.

Separately, the doc title's `int offset` overload (jumping forward by a state count rather than to a named label) is preserved on UZDoom, but not as a distinct function signature — UZDoom's DECORATE frontend generically casts any numeric argument passed where a `statelabel` parameter is expected into a state-index jump (`src/scripting/backend/codegen_doom.cpp`'s `CustomTypeCast`, guarded to only anonymous state-action calls), so `A_JumpIfCloser(64, 3)` still resolves to "jump forward 3 states" the same as in Zandronum.

## Engine-family divergence: `noz` parameter

The "Wiki/engine divergence" section above documents that Zandronum lacks the wiki's optional third `noz` parameter. **UZDoom does implement it:** `A_JumpIfCloser(double distance, statelabel label, bool noz = false)` matches the wiki description — passing `true` disables the vertical distance check entirely, testing only the 2D (`Distance2D`) distance regardless of either actor's z-position. This parameter is UZDoom/wiki-only; it remains unavailable in Zandronum, where the vertical check is always performed.

## Engine-family divergence: network synchronization

The "Network synchronization" behavior note above is Zandronum-specific and does not apply to UZDoom. UZDoom has no client/server authority split anywhere in its source tree for this function — no `NETWORK_InClientMode()`-style gate, and no position/frame sync signal sent after a jump. On UZDoom, `A_JumpIfCloser` simply evaluates the condition and jumps (or doesn't); there is no networking consideration at all.

## See also

- `A_JumpIfTracerCloser` — same logic applied to the actor's `tracer` field instead of its `target`.
- `A_JumpIfMasterCloser` — same logic applied to the actor's `master` field instead of its `target`.
- [Jump functions and network synchronization](../concepts/network-jump-synchronization.md) — detailed coverage of how state jumps interact with client/server in multiplayer (Zandronum-specific; see the divergence note above for UZDoom).
