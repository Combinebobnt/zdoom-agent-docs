# A_JumpIfTargetInLOS

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_JumpIfTargetInLOS` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_JumpIfTargetInLOS&oldid=44161) + verified against Zandronum source `src/thingdef/thingdef_codeptr.cpp:4242-4340`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_JumpIfTargetInLOS)` (callable from any actor's state table).

Jumps to a target state if the calling actor can see its target, optionally subject to field-of-view and distance constraints. Behavior differs between monster/projectile callers and player weapon/inventory callers.

## Signatures

```text
state A_JumpIfTargetInLOS(int offset[, float fov[, int flags[, float dist_max[, float dist_close]]]])
state A_JumpIfTargetInLOS(str "state"[, float fov[, int flags[, float dist_max[, float dist_close]]]])
```

## Parameters

**state / offset** — Target state (by name string or relative frame offset) to jump to if the condition is met.

**fov** (optional, default 0) — Field of vision cone (in degrees) centered on the **caller's** facing direction. A value of 0 disables the FOV check (sight-only). Values up to 360 are valid. **Note:** For weapon/inventory callers (the player branch), FOV behavior depends on the flags: when neither `JLOSF_TARGETLOS` nor `JLOSF_FLIPFOV` is set, the FOV parameter is internally zeroed and becomes meaningless; the jump depends only on aiming crosshair and distance. When either flag is set, FOV is preserved and checked.

**flags** (optional, default 0) — Integer flags controlling behavior. Flags can be combined with bitwise OR (`|`). Available flags:

- **JLOSF_PROJECTILE** (1) — If the caller is a missile with `SEEKERMISSILE`, use the missile's `tracer` pointer as the target instead of the normal `target`. Non-seekers or non-missiles: no effect.
- **JLOSF_NOSIGHT** (2) — Disables the line-of-sight check; the jump depends on FOV and distance alone.
- **JLOSF_CLOSENOFOV** (4) — If the target is within `dist_close` distance, disables the FOV check.
- **JLOSF_CLOSENOSIGHT** (8) — If the target is within `dist_close` distance, disables the sight check.
- **JLOSF_CLOSENOJUMP** (16) — If the target is within `dist_close` distance, prevents the jump entirely.
- **JLOSF_DEADNOJUMP** (32) — Does not jump if the target is dead (`target->health <= 0`).
- **JLOSF_CHECKMASTER** (64) — Uses the caller's `master` pointer as the target instead of `target`.
- **JLOSF_TARGETLOS** (128) — Reverses the sight check: checks whether the **target** can see the **caller** (instead of the caller seeing the target). The FOV cone becomes the target's FOV. Useful in combination with other flags for asymmetric visibility logic.
- **JLOSF_FLIPFOV** (256) — When used with `JLOSF_TARGETLOS`, the caller's FOV is checked instead of the target's. Without `JLOSF_TARGETLOS`, reverses the direction of the FOV check.
- **JLOSF_ALLYNOJUMP** (512) — Does not jump if the actors are allied to each other (determined by `IsFriend`).
- **JLOSF_COMBATANTONLY** (1024) — Does not jump unless the target is a player or has `MF3_ISMONSTER` set.
- **JLOSF_NOAUTOAIM** (2048) — For weapon/inventory callers only: the target must be under the exact crosshair (both horizontal and vertical), not just within autoaim tolerances. Has no effect for non-player callers.

**Wiki divergence:** The ZDoom Wiki lists `JLOSF_CHECKTRACER` (described as checking the calling actor's `tracer` instead of `target` for non-missile actors), but this flag does not exist in the Zandronum constant table and is not supported. Attempting to use it will compile but have no effect.

**dist_max** (optional, default 0) — Maximum distance (map units, fixed-point) between the caller and target for the jump to occur. A value of 0 disables the distance check. Distance is 3D approximated via two `P_AproxDistance` calls (XY distance, then incorporating Z), not true Euclidean distance. For weapon/inventory callers, the target search itself is capped at `MISSILERANGE` (2048 map units), so `dist_max` can further constrain it but cannot extend it beyond that engine limit.

**dist_close** (optional, default 0) — If non-zero and the target is closer than this distance, applies the `JLOSF_CLOSE*` modifiers (above). Otherwise has no effect.

## Engine-family divergence: JLOSF_CHECKTRACER flag

Unlike Zandronum (see the Wiki divergence note above), UZDoom does implement `JLOSF_CHECKTRACER` (value 4096, `1 << 12`) — the `JLOS_flags` enum in the UZDoom source's `src/playsim/p_actionfunctions.cpp` includes it alongside the twelve flags Zandronum defines. When set, target resolution for non-player callers uses `tracer` unconditionally: the flag both enters the tracer-selection branch (bypassing the `MF_MISSILE`+`JLOSF_PROJECTILE` gate) and, within that branch, selects `tracer` over `NULL` regardless of `MF2_SEEKERMISSILE`. This matches the ZDoom Wiki's description of the flag ("checks the calling actor's tracer instead of target for non-missile actors") that Zandronum does not support — on UZDoom it is fully functional, for missile and non-missile callers alike.

## Behavior

### Monster/Projectile Callers (non-player)

The function resolves the target as follows (in order):

1. If **JLOSF_CHECKMASTER** is set, use `master`.
2. Else if the caller is a missile (`MF_MISSILE`) and **JLOSF_PROJECTILE** is set, use `tracer` if `MF2_SEEKERMISSILE` is set; otherwise NULL.
3. Else use `target`.

If target is NULL, the function returns without jumping. Then, in sequence:

1. **Dead target:** If **JLOSF_DEADNOJUMP** is set and `target->health <= 0`, return without jumping.
2. **Max distance:** If `dist_max` is non-zero and the 3D distance exceeds it, return without jumping.
3. **Close distance modifiers:** If `dist_close` is non-zero and distance is less than it:
   - If **JLOSF_CLOSENOJUMP** is set, return without jumping.
   - If **JLOSF_CLOSENOFOV** is set, disable FOV check.
   - If **JLOSF_CLOSENOSIGHT** is set, disable sight check.
4. **Combatant check:** If **JLOSF_COMBATANTONLY** is set, return without jumping unless the target is a player or has `MF3_ISMONSTER`.
5. **Ally check:** If **JLOSF_ALLYNOJUMP** is set and the actors are allied, return without jumping.
6. **Visibility checks:** Apply sight and/or FOV checks based on flags and preceding modifiers.
7. **Jump:** If all checks pass, perform the state jump with `ACTION_JUMP(jump, CLIENTUPDATE_FRAME | (!self->player ? CLIENTUPDATE_POSITION : ...))`.

### Weapon/Inventory Callers (player branch)

When `self->player` is non-NULL, the function performs a weapon aim trace:

1. Call `P_AimLineAttack(self, self->angle, MISSILERANGE, &target, ...)` to find what the player is aiming at. The autoaim tolerance is halved if **JLOSF_NOAUTOAIM** is set.
2. If no valid target is found, return without jumping.
3. Apply a switch on `flags & (JLOSF_TARGETLOS | JLOSF_FLIPFOV)`:
   - Both set (384): `fov = 0`; continue to next case.
   - `JLOSF_TARGETLOS` only (128): Check `JLOSF_NOSIGHT` flag to set `doCheckSight`.
   - Neither or `JLOSF_FLIPFOV` only: `fov = 0` (default case); fall through to FOV flip logic, `doCheckSight = false`.
   - `JLOSF_FLIPFOV` only (256): FOV is **not** zeroed; `doCheckSight = false`.

**Key note:** The default case (no special flags) zeros `fov`, making the FOV parameter meaningless for plain weapon aiming; the jump depends only on whether the aiming crosshair touches a valid target.

4. Continue with Ally and Combatant checks (as in the non-player path).
5. Distance and close-distance checks proceed as in the non-player path.
6. Sight and FOV checks occur as determined above.
7. If all checks pass, jump with position updates: `ACTION_JUMP(jump, CLIENTUPDATE_FRAME | (!self->player ? CLIENTUPDATE_POSITION : ...))`.

## Engine-family divergence: distance calculation

Zandronum computes the caller-to-target distance via two chained `P_AproxDistance` calls (the Zandronum source's `src/thingdef/thingdef_codeptr.cpp`, in this function's `A_JumpIfTargetInLOS` body: an XY approximation, then combined with the Z delta) — the classic Doom octagonal approximation (`dx+dy-(min(dx,dy)>>1)`), which overestimates true Euclidean distance by up to ~6% along a 45-degree diagonal. UZDoom instead calls `AActor::Distance3D` (the UZDoom source's `src/playsim/actor.h`), which computes `(Pos() - otherpos).Length()` — a true 3D Euclidean distance via vector length. The two engines can therefore disagree on whether a target is within `dist_max`/`dist_close` for targets sitting near the boundary distance off-axis, since Zandronum's approximation reads as farther away than UZDoom's exact calculation for the same true position.

## Network Synchronization

Unlike `A_JumpIfInTargetLOS` (which is server-authoritative with an explicit client-mode gate), `A_JumpIfTargetInLOS` does not check `NETWORK_InClientModeAndActorNotClientHandled` at the start. The function evaluates sight logic on both server and client, but for non-player callers, it sends a position update (`CLIENTUPDATE_POSITION`) alongside the frame jump to sync any movement that occurred on the client during prediction. For player callers, only the frame is updated (`CLIENTUPDATE_FRAME`). This asymmetry is important: a networked non-player actor's position may diverge between client and server during tick-local evaluation, and the position update re-syncs it. Player weapon actions are less subject to this desync because the player's own position is more frequently synchronized through other channels.

## Engine-family divergence: network execution model

The client/server authority split described above (`CLIENTUPDATE_FRAME`/`CLIENTUPDATE_POSITION`, and the general server-authoritative/client-prediction split it implies) is specific to Zandronum's netcode. UZDoom has no equivalent concept: a search of UZDoom's entire source tree turns up zero occurrences of `NETWORK_InClientMode`/`SERVERCOMMANDS_*` or any comparable mechanism, for this function or in general. UZDoom's `A_JumpIfTargetInLOS` (the UZDoom source's `wadsrc/static/zscript/actors/checks.zs`, calling the native `CheckIfTargetInLOS` in `src/playsim/p_actionfunctions.cpp`) is a plain boolean check followed by a `ResolveState`/state-return — no client-mode branch, no server-authoritative early return, and no cross-machine update-flag distinction between the player and non-player branches. The entire "Network Synchronization" topology above, including the position-vs-frame-only update asymmetry, does not apply to UZDoom.

## Null Safety

The function safely handles NULL targets: if target resolution returns NULL, or if the target becomes NULL during distance/ally/combatant checks, the function returns without jumping. All dereferences of `target` are guarded.

## Related

- `A_JumpIfInTargetLOS` — The inverse direction: checks whether the **caller** is in the **target's** field of view (not the target in the caller's FOV). Uses a different code path, is server-authoritative, and does not support the weapon/inventory branch. Different set of flags is inert in that function compared to this one.
- `A_CheckSight` — Line-of-sight check without FOV/distance machinery.
- `A_JumpIf` — Conditional jump based on a DECORATE expression.
