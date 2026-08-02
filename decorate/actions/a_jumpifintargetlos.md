# A_JumpIfInTargetLOS

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_JumpIfInTargetLOS` (retrieved 2026-07-31, oldid=42406) + verified against Zandronum source `src/thingdef/thingdef_codeptr.cpp:4373-4448`.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_JumpIfInTargetLOS)` (`src/thingdef/thingdef_codeptr.cpp:4373`).

Jumps to a target state if the calling actor is visible and in the line of sight of its target, optionally subject to a field-of-view cone centered on the target.

## Signatures

```
state A_JumpIfInTargetLOS(int offset[, float fov[, int flags[, float dist_max[, float dist_close]]]])
state A_JumpIfInTargetLOS(str "state"[, float fov[, int flags[, float dist_max[, float dist_close]]]])
```

## Parameters

**state / offset** — Target state (by name string or relative frame offset) to jump to if the condition is met.

**fov** (optional, default 0) — Field of vision angle (degrees) defining the cone within which the calling actor must fall to pass the sight check. The cone is centered on the **target's** current facing direction, not the caller's — the target must be "looking at" the calling actor, not the reverse. A value of 0 disables the FOV check entirely (sight check only); values up to 360 are valid. **Wiki note:** The ZDoom Wiki describes FOV as "the center of which is the actor's current facing direction" referring to the *caller*'s facing, but this is inaccurate for Zandronum — the cone is centered on the **target's** facing. This was corrected in Zandronum to test whether the target can see the caller within its view cone, not whether the caller sees the target.

**flags** (optional, default 0) — Integer flags controlling sight and distance behavior. Flags can be combined with bitwise OR (`|`). Only the following flags have meaning in this function:

- **JLOSF_PROJECTILE** (1) — If set and the caller is a missile with the `SEEKERMISSILE` flag, use the missile's `tracer` pointer as the target instead of the normal target. Non-seekers become NULL-targeted. Ignored for non-missiles.
- **JLOSF_NOSIGHT** (2) — Disables the line-of-sight check; the function jumps based on FOV and distance alone.
- **JLOSF_DEADNOJUMP** (32) — If set, does not jump if the target is dead (`target->health <= 0`).
- **JLOSF_CLOSENOJUMP** (16) — If the target is within `dist_close` distance, prevents the jump entirely.
- **JLOSF_CLOSENOFOV** (4) — If the target is within `dist_close` distance, disables the FOV check (sight-only).
- **JLOSF_CLOSENOSIGHT** (8) — If the target is within `dist_close` distance, disables the sight check (FOV-only).
- **JLOSF_CHECKMASTER** (64) — Uses the caller's `master` pointer as the target instead of `target`, overriding all other target-resolution flags.

**Other `JLOSF_*` flags** (`JLOSF_TARGETLOS`, `JLOSF_FLIPFOV`, `JLOSF_ALLYNOJUMP`, `JLOSF_COMBATANTONLY`, `JLOSF_NOAUTOAIM`) are defined in the shared `JLOS_flags` enum alongside this function (used by the related `A_JumpIfTargetInLOS`) but are inert in `A_JumpIfInTargetLOS` — they compile without error but have no effect in this function's logic.

**dist_max** (optional, default 0) — Maximum distance (map units, fixed-point) between the caller and target for the jump to occur. A value of 0 disables the distance check. Distance is 3D (approximated via `P_AproxDistance`, not Euclidean) and includes the z-axis difference.

**dist_close** (optional, default 0) — Used to modify behavior of the `JLOSF_CLOSE*` flags when the target is within this distance. No effect if 0, or if none of the `JLOSF_CLOSE*` flags are set.

## Behavior

The function resolves the target actor using the rules below (in order), then returns without jumping if the target is NULL or if the result is NULL at any step.

- If **JLOSF_CHECKMASTER** is set, use `master` (target resolution stops here).
- Else if the caller is a missile (`MF_MISSILE` flag) and **JLOSF_PROJECTILE** is set, use `tracer` if the caller has `MF2_SEEKERMISSILE`; otherwise NULL.
- Else use the normal `target` pointer.

Once a target is resolved, the function checks:

1. **Dead target:** If **JLOSF_DEADNOJUMP** is set and `target->health <= 0`, return without jumping.
2. **Max distance:** If `dist_max` is non-zero and the 3D distance exceeds it, return without jumping.
3. **Close distance:** If `dist_close` is non-zero and the 3D distance is less than it, apply the `JLOSF_CLOSE*` modifiers:
   - If **JLOSF_CLOSENOJUMP** is set, return without jumping.
   - If **JLOSF_CLOSENOFOV** is set, clear `fov` (effectively `fov = 0`).
   - If **JLOSF_CLOSENOSIGHT** is set, disable the sight check.
4. **FOV check:** If `fov` is non-zero, calculate the angle from the target's facing direction to the caller. If the caller is outside the cone (half-angle = `fov / 2`), return without jumping.
5. **Sight check:** If not disabled, call `P_CheckSight(target, self, SF_IGNOREVISIBILITY)`. If false, return without jumping.
6. **Jump:** Perform the state jump, updating the calling actor's frame on both server and client.

## Network synchronization

Unlike `A_JumpIf`, which evaluates its condition expression before checking client-side status (risking RNG desync), `A_JumpIfInTargetLOS` is **server-authoritative**. The check at the start (`NETWORK_InClientModeAndActorNotClientHandled(self)`) causes client-side callers in networked games to return immediately without evaluating any sight logic — the server synchronizes the jump outcome via `ACTION_JUMP(jump, CLIENTUPDATE_FRAME)`. No target pointer update (`CLIENTUPDATE_POSITION`) is sent, only the frame. This is simpler than `A_JumpIfTargetInLOS` (which adds position updates for non-players) because the target resolution here is asymmetric: if the caller is a non-player, the server must arbitrate what the target "sees."

See [`concepts/network-jump-synchronization.md`](../concepts/network-jump-synchronization.md) for a broader network synchronization model and risks of RNG-bearing conditions in state jumps.

## Null-safety

If the resolved target is NULL or becomes NULL during the above checks, the function returns without jumping. This includes:

- `JLOSF_PROJECTILE` on a non-seeker missile (becomes NULL).
- `JLOSF_CHECKMASTER` on an actor with no `master` (NULL).
- Normal `target` resolution if the caller has no current target.

No null-pointer dereference occurs in any of these cases; all dereferences of `target` are guarded.

## Related

- `A_JumpIfTargetInLOS` — The inverse direction: checks whether the target is in the *caller's* field of view, not the target's. Also supports the additional flags `JLOSF_TARGETLOS`, `JLOSF_FLIPFOV`, `JLOSF_ALLYNOJUMP`, `JLOSF_COMBATANTONLY`, and `JLOSF_NOAUTOAIM`, which are inert in `A_JumpIfInTargetLOS`.
- `A_CheckSight` — Line-of-sight check without the FOV/distance machinery.
- `A_JumpIf` — Conditional jump based on a DECORATE expression; evaluates the expression before the client-mode gate, unlike this function's server-authoritative model.
