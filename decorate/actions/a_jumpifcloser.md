# `A_JumpIfCloser (float distance, state label)` / `A_JumpIfCloser (float distance, int offset)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki `A_JumpIfCloser` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_JumpIfCloser&oldid=44127) + verified against Zandronum source's `src/thingdef/thingdef_codeptr.cpp:875-896` and `src/thingdef/thingdef_codeptr.cpp:856-873` (`DoJumpIfCloser` helper), `src/thingdef/thingdef_codeptr.cpp:695-753` (`DoJump`), `src/p_maputl.cpp:59-64` (`P_AproxDistance`), `src/thingdef/thingdef_states.cpp:377-397` (integer offset for a state parameter).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** AActor — callable from any actor's state table. Shared implementation via the `DoJumpIfCloser()` helper, which also backs `A_JumpIfTracerCloser` and `A_JumpIfMasterCloser`.

Jumps to a target state (or forward by an offset) if the calling actor's target is closer than a specified distance.

## Parameters

- **`distance`** (float, fixed-point units) — Threshold distance for the jump. On Zandronum the horizontal distance uses an octagonal approximation (via `P_AproxDistance`, not true Euclidean), so the actual "radius" of the test varies slightly with angle. Units match the actor radius convention (where Doom map units are `FRACUNIT` units internally).
- **`label` or `offset`** — Target state label or state offset to jump to if the condition is met. On Zandronum this is one `state` parameter, not two overloads. It accepts either a quoted state label or a non-negative integer offset, which jumps forward by that many states from the calling state. An offset of `0` means no jump. A negative offset is a parse error, and so is a positive offset on a sprite line that defines more than one frame (e.g. `POSS AB 4`).

## Wiki/engine divergence

The source ZDoom wiki describes an optional third parameter, `noz` (boolean), to disable vertical distance checking. **This parameter does not exist in Zandronum (3.2.1 through 3.3-alpha)** — attempting to pass it causes a parse error. Vertical distance is always checked in Zandronum's implementation (see the vertical-check note under Behavior notes).

## Behavior notes

- **Distance calculation does not account for actor radius.** For the horizontal test, both the calling actor and its target are treated as points. If either or both actors are very wide (large radius), it's possible the jump condition can never be met. Workaround: increase the distance threshold to account for radii, e.g. `A_JumpIfCloser(radius + desired_dist, "label")`.
- **Vertical check uses actor heights.** Besides the horizontal test, the vertical gap between the higher actor's bottom and the lower actor's top must also be less than `distance`. Actors that overlap vertically always pass this part, since the gap is negative.
- **Player-specific behavior.** When the calling actor is a player, the "target" is whatever `P_BulletSlope()`'s autoaim trace finds (the actor in the player's crosshair), not the calling actor's `target` field. This covers weapon states, CustomInventory states run on the player, and the player class's own states. If the trace finds nothing, there is no jump. For non-player actors, the target is always `self->target`.
- **Network synchronization.** In multiplayer, the jump decision is server-authoritative. When the jump changes the actor's own current state, the server sends clients the new frame plus a position update (`CLIENTUPDATE_FRAME|CLIENTUPDATE_POSITION`). When called from a weapon or flash state, the server sends only a weapon state jump, with no position update. Jumps inside a CustomInventory state chain send nothing. In client-mode (when `NETWORK_InClientMode()` is true), the early-return gate checks `NETFL_CLIENTSIDEONLY` on the actor's network flags — if the actor is not client-side only, the function returns without executing, deferring the jump decision to the server.

## Engine-family divergence: distance calculation

The `distance` parameter note above describes Zandronum's `P_AproxDistance`, an octagonal (Doom-classic) approximation of 2D distance, not a true Euclidean calculation. **UZDoom's `A_JumpIfCloser` uses true Euclidean distance instead** — the underlying `CheckIfCloser()` helper compares against `Distance2D()`, which computes `(pos.xy - target.pos.xy).Length()` (an exact `sqrt(dx*dx + dy*dy)`). The two engines' distance thresholds therefore don't line up exactly at all angles: `P_AproxDistance` computes `dx + dy - min(dx,dy)/2` (that is, `max + min/2`). It never under-estimates, is exact only along the axes, over-estimates by ~6% at 45°, and peaks at ~11.8% over near 26.6° off-axis. So for off-axis approaches Zandronum's jump fires at the same or a shorter true distance than UZDoom's, never a longer one. The vertical (z) portion of the check is unaffected by this. The two engines compute the same vertical-gap formula (see Behavior notes above). The threshold parameter itself is also declared differently (Zandronum's `ACTION_PARAM_FIXED` fixed-point vs. UZDoom's native `double`), but both represent the same map-unit value to a modder writing DECORATE.

Separately, the doc title's `int offset` overload (jumping forward by a state count rather than to a named label) is preserved on UZDoom, but not as a distinct function signature — UZDoom's DECORATE frontend generically casts any numeric argument passed where a `statelabel` parameter is expected into a state-index jump (`src/scripting/backend/codegen_doom.cpp`'s `CustomTypeCast`, guarded to only anonymous state-action calls), so `A_JumpIfCloser(64, 3)` still resolves to "jump forward 3 states" the same as in Zandronum.

## Engine-family divergence: `noz` parameter

The "Wiki/engine divergence" section above documents that Zandronum lacks the wiki's optional third `noz` parameter. **UZDoom does implement it:** `A_JumpIfCloser(double distance, statelabel label, bool noz = false)` matches the wiki description — passing `true` disables the vertical distance check entirely, testing only the 2D (`Distance2D`) distance regardless of either actor's z-position. This parameter is UZDoom/wiki-only; it remains unavailable in Zandronum, where the vertical check is always performed.

## Engine-family divergence: network synchronization

The "Network synchronization" behavior note above is Zandronum-specific and does not apply to UZDoom. UZDoom has no client/server authority split anywhere in its source tree for this function — no `NETWORK_InClientMode()`-style gate, and no position/frame sync signal sent after a jump. On UZDoom, `A_JumpIfCloser` simply evaluates the condition and jumps (or doesn't); there is no networking consideration at all.

## See also

- `A_JumpIfTracerCloser` — same logic applied to the actor's `tracer` field instead of its `target`.
- `A_JumpIfMasterCloser` — same logic applied to the actor's `master` field instead of its `target`.
- [Jump functions and network synchronization](../concepts/network-jump-synchronization.md) — detailed coverage of how state jumps interact with client/server in multiplayer (Zandronum-specific; see the divergence note above for UZDoom).
