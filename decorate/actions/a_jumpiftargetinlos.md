# A_JumpIfTargetInLOS

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki `A_JumpIfTargetInLOS` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_JumpIfTargetInLOS&oldid=44161) + verified against Zandronum source `src/thingdef/thingdef_codeptr.cpp:4242-4340`; unknown-constant handling `src/thingdef/thingdef_expression.cpp:1914` and `src/thingdef/thingdef.cpp:357-359`; `NOAUTOAIM` aim window `src/p_map.cpp:4045-4057`; distance approximation `src/p_maputl.cpp:59-64`.
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

**fov** (optional, default 0) — Field of vision cone (in degrees) centered on the **caller's** facing direction. A value of 0 disables the FOV check (sight-only). Values up to 360 are valid. **Note:** For weapon/inventory callers (the player branch), FOV behavior depends on the flags: when neither `JLOSF_TARGETLOS` nor `JLOSF_FLIPFOV` is set, or when both are set, the FOV parameter is internally zeroed and becomes meaningless. When exactly one of the two is set, FOV is preserved and checked.

**flags** (optional, default 0) — Integer flags controlling behavior. Flags can be combined with bitwise OR (`|`). Available flags:

- **JLOSF_PROJECTILE** (1) — If the caller is a missile with `SEEKERMISSILE`, use the missile's `tracer` pointer as the target instead of the normal `target`. A missile without `SEEKERMISSILE` gets no target at all, so it never jumps. Non-missiles: no effect.
- **JLOSF_NOSIGHT** (2) — Disables the line-of-sight check; the jump depends on FOV and distance alone.
- **JLOSF_CLOSENOFOV** (4) — If the target is within `dist_close` distance, disables the FOV check.
- **JLOSF_CLOSENOSIGHT** (8) — If the target is within `dist_close` distance, disables the sight check.
- **JLOSF_CLOSENOJUMP** (16) — If the target is within `dist_close` distance, prevents the jump entirely.
- **JLOSF_DEADNOJUMP** (32) — Does not jump if the target is dead (`target->health <= 0`). Checked for non-player callers only.
- **JLOSF_CHECKMASTER** (64) — Uses the caller's `master` pointer as the target instead of `target`. Non-player callers only.
- **JLOSF_TARGETLOS** (128) — Reverses the sight check: checks whether the **target** can see the **caller** (instead of the caller seeing the target). The FOV cone becomes the target's FOV. Useful in combination with other flags for asymmetric visibility logic.
- **JLOSF_FLIPFOV** (256) — When used with `JLOSF_TARGETLOS`, the caller's FOV is checked instead of the target's. Without `JLOSF_TARGETLOS`, reverses the direction of the FOV check.
- **JLOSF_ALLYNOJUMP** (512) — Does not jump if the actors are allied to each other (determined by `IsFriend`).
- **JLOSF_COMBATANTONLY** (1024) — Does not jump unless the target is a player or has `MF3_ISMONSTER` set.
- **JLOSF_NOAUTOAIM** (2048) — For weapon/inventory callers only: narrows the aim trace's vertical window to half a degree (as for a `WIF_NOAUTOAIM` weapon) instead of the player's autoaim setting. The trace is a single line along the player's angle either way, so there is no horizontal tolerance to narrow. Has no effect for non-player callers.

**Wiki divergence:** The ZDoom Wiki lists `JLOSF_CHECKTRACER` (described as checking the calling actor's `tracer` instead of `target` for non-missile actors), but this flag does not exist in the Zandronum constant table and is not supported. Writing the name is a DECORATE "Unknown identifier" error, which aborts startup. Passing the raw value 4096 compiles but is ignored.

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
2. **Combatant check:** If **JLOSF_COMBATANTONLY** is set, return without jumping unless the target is a player or has `MF3_ISMONSTER`.
3. **Ally check:** If **JLOSF_ALLYNOJUMP** is set and the actors are allied, return without jumping.
4. **Max distance:** If `dist_max` is non-zero and the 3D distance exceeds it, return without jumping.
5. **Close distance modifiers:** If `dist_close` is non-zero and distance is less than it:
   - If **JLOSF_CLOSENOJUMP** is set, return without jumping.
   - If **JLOSF_CLOSENOFOV** is set, disable FOV check.
   - If **JLOSF_CLOSENOSIGHT** is set, disable sight check.
6. **Visibility checks:** Apply the sight check, then the FOV check, based on flags and preceding modifiers.
7. **Jump:** If all checks pass, perform the state jump with `ACTION_JUMP(jump, CLIENTUPDATE_FRAME | (!self->player ? CLIENTUPDATE_POSITION : ...))`.

### Weapon/Inventory Callers (player branch)

When `self->player` is non-NULL, the function performs a weapon aim trace:

1. Call `P_AimLineAttack(self, self->angle, MISSILERANGE, &target, ...)` to find what the player is aiming at. If **JLOSF_NOAUTOAIM** is set, the vertical aim window is a fixed half degree instead of the player's autoaim setting.
2. If no valid target is found, return without jumping.
3. Apply a switch on `flags & (JLOSF_TARGETLOS | JLOSF_FLIPFOV)`:
   - Both set (384): `fov = 0`; continue to next case.
   - `JLOSF_TARGETLOS` only (128): Check `JLOSF_NOSIGHT` flag to set `doCheckSight`.
   - Neither set (default case): `fov = 0`; falls through to the `JLOSF_FLIPFOV` case, so `doCheckSight = false`.
   - `JLOSF_FLIPFOV` only (256): FOV is **not** zeroed; `doCheckSight = false`.

**Key note:** The default case (no special flags) zeros `fov`, making the FOV parameter meaningless for plain weapon aiming; the jump depends only on whether the aim trace finds a valid target, plus the combatant, ally and distance filters.

4. Continue with Combatant and Ally checks (as in the non-player path).
5. Distance and close-distance checks proceed as in the non-player path.
6. Sight and FOV checks occur as determined above.
7. If all checks pass, jump. A player caller gets a frame update only, with no position update (see Network Synchronization).

## Engine-family divergence: distance calculation

Zandronum computes the caller-to-target distance via two chained `P_AproxDistance` calls (the Zandronum source's `src/thingdef/thingdef_codeptr.cpp`, in this function's `A_JumpIfTargetInLOS` body: an XY approximation, then combined with the Z delta) — the classic Doom octagonal approximation (`dx+dy-(min(dx,dy)>>1)`), which never underestimates true Euclidean distance. In 2D it reads about 6% long on a 45-degree diagonal and up to about 12% long where one axis delta is half the other (about 26.6 degrees). Chaining the Z pass compounds this to up to about 22% in 3D. UZDoom instead calls `AActor::Distance3D` (the UZDoom source's `src/playsim/actor.h`), which computes `(Pos() - otherpos).Length()` — a true 3D Euclidean distance via vector length. The two engines can therefore disagree on whether a target is within `dist_max`/`dist_close` for targets sitting near the boundary distance off-axis, since Zandronum's approximation reads as farther away than UZDoom's exact calculation for the same true position.

## Pitfall: `JLOSF_CLOSENOJUMP` as an "abort if too far" gate

`A_JumpIfTargetInLOS("Abort", 0, JLOSF_CLOSENOJUMP, 0, d)` reads like "jump to `Abort` when the target is at least `d` away", but the sight check still runs after the distance checks (step 6 above). So it jumps only when the target is far **and** visible. A far target behind cover falls through to whatever follows, the opposite of the intent. Add `JLOSF_NOSIGHT` (and keep `fov` at 0) to make it a pure distance gate. When the gate runs in the same tic as the `A_Chase` that entered the state, though, `P_CheckMissileRange` has already required sight (even on the `MF_JUSTHIT` path, which skips `MaxTargetRange`; see [Damage retaliation](../../shared/concepts/monster-target-retaliation.md)). The two checks then agree except across a `BLOCKEVERYTHING` line: `P_CheckMissileRange` sees past one (`SF_SEEPASTBLOCKEVERYTHING`), this function doesn't (`SF_IGNOREVISIBILITY` only). The pitfall bites when time passes between entering the state and the gate. Source: Zandronum `src/thingdef/thingdef_codeptr.cpp`, this function's body (distance checks, then `P_CheckSight`, then the FOV check); UZDoom's `CheckIfTargetInLOS` in `src/playsim/p_actionfunctions.cpp` has the same order.

## Network Synchronization

Unlike `A_JumpIfInTargetLOS` (which is server-authoritative with an explicit client-mode gate), `A_JumpIfTargetInLOS` does not check `NETWORK_InClientModeAndActorNotClientHandled` at the start. The function runs on both server and client. A client usually has no target for a monster, so its local call returns early without jumping. For non-player callers, the server sends a position update (`CLIENTUPDATE_POSITION`) alongside the frame jump, because client-side movement prediction may have moved the actor while the client ignored the jump. For player callers, only the frame is updated (`CLIENTUPDATE_FRAME`).

## Engine-family divergence: network execution model

The client/server authority split described above (`CLIENTUPDATE_FRAME`/`CLIENTUPDATE_POSITION`, and the general server-authoritative/client-prediction split it implies) is specific to Zandronum's netcode. UZDoom has no equivalent concept: a search of UZDoom's entire source tree turns up zero occurrences of `NETWORK_InClientMode`/`SERVERCOMMANDS_*` or any comparable mechanism, for this function or in general. UZDoom's `A_JumpIfTargetInLOS` (the UZDoom source's `wadsrc/static/zscript/actors/checks.zs`, calling the native `CheckIfTargetInLOS` in `src/playsim/p_actionfunctions.cpp`) is a plain boolean check followed by a `ResolveState`/state-return — no client-mode branch, no server-authoritative early return, and no cross-machine update-flag distinction between the player and non-player branches. The entire "Network Synchronization" topology above, including the position-vs-frame-only update asymmetry, does not apply to UZDoom.

## Null Safety

The function safely handles NULL targets: if target resolution (or the player's aim trace) yields NULL, the function returns without jumping before any dereference of `target`.

## Related

- `A_JumpIfInTargetLOS` — The inverse direction: checks whether the **caller** is in the **target's** field of view (not the target in the caller's FOV). Uses a different code path, is server-authoritative, and does not support the weapon/inventory branch. Different set of flags is inert in that function compared to this one.
- `A_CheckSight` — Line-of-sight check without FOV/distance machinery.
- `A_JumpIf` — Conditional jump based on a DECORATE expression.
