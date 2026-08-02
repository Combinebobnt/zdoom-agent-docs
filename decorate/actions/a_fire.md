# `void A_Fire(float spawnheight = 0)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_Fire` (retrieved 2026-08-01, oldid=52463) + verified against the Zandronum source's `src/g_doom/a_archvile.cpp:44` and `wadsrc/static/actors/actor.txt:90`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_Fire)` at `src/g_doom/a_archvile.cpp:44`.

Repositions the calling actor to orbit around its `tracer` pointer at a fixed 24 map units forward (along the tracer's facing direction) with an optional vertical offset. Primarily used by the Arch-Vile's flame attack (`ArchvileFire` actor) to keep flame sprites positioned on the attack target.

**Engine-family divergence: Zandronum's implementation includes server-side-only network gating and a mandatory mutual-visibility check absent from the ZDoom-wiki ZScript version.** The wiki shows UZDoom/GZDoom code with no netcode at all; Zandronum enforces that the movement is server-authoritative and requires `target` to have line-of-sight to `tracer` before the reposition succeeds.

## Parameters

- **`float spawnheight`** — Vertical (Z-axis) offset in map units. Default: 0 (positions the actor at the tracer's floor level). Positive values move the actor upward, negative downward. Internally converted to `fixed_t` (fixed-point) format.

## Behavior

The function requires both pointers to be valid and configured:

1. **`tracer` must be set** — the actor this function orbits around. This is typically set via `A_VileTarget` or manually assigned in ACS/state-machine logic.
2. **`target` must be set** — the actor being attacked. The function checks whether `target` can see `tracer` via line-of-sight before executing the reposition; if the sight check fails, the function silently returns without moving.
3. **Offset calculation** — the calling actor is positioned 24 map units along `tracer->angle` plus the `spawnheight` Z offset, using the engine's fixed-point trigonometry.
4. **Silent early-returns** — the function returns immediately (no side effects, no error flag) if:
   - The engine is in client mode and the calling actor is not `+CLIENTSIDEONLY` (server-side only, per `NETWORK_InClientMode()` check).
   - Either `tracer` or `target` is null.
   - The sight check (`P_CheckSight(target, tracer, ...)`) fails, indicating the target has lost line-of-sight.

## Network behavior

In networked multiplayer, the repositioning is **server-side only**. The server computes the new position and broadcasts it to all clients via `SERVERCOMMANDS_MoveThingExact`. Clients receive the position synchronously but do not execute their own computation. This is asymmetric with sound playback — see "Related functions" below.

## Related functions

**`A_StartFire` and `A_FireCrackle`** are thin wrappers around the same file-local `A_Fire` helper (not DECORATE actions themselves, so they do not appear in the action table). Both play a sound before calling the reposition:

- `A_StartFire` plays `vile/firestrt` on the body sound channel, then calls `A_Fire(0)` (ignoring any provided parameter; default height always used).
- `A_FireCrackle` plays `vile/firecrkl` on the body sound channel, then calls `A_Fire(0)`.

These sounds play **client-side** (not gated by the server-side check), making them a reliable audio cue even when reposition fails. Only the sprite movement is server-authoritative.

## Example

From Zandronum's native `ArchvileFire` actor:

```
actor ArchvileFire
{
    +NOBLOCKMAP +NOGRAVITY
    RenderStyle Add
    Alpha 1
    States
    {
    Spawn:
        FIRE A 2 Bright  A_StartFire
        FIRE BAB 2 Bright  A_Fire
        FIRE C 2 Bright  A_FireCrackle
        FIRE BCBCDCDCDEDED 2 Bright  A_Fire
        FIRE E 2 Bright  A_FireCrackle
        FIRE FEFEFGHGHGH 2 Bright  A_Fire
        Stop
    }
}
```

The flame spawns at `target` (the victim), initially offset by `A_StartFire`, then repositioned every frame to follow the target's position and the Arch-Vile's facing direction (via `tracer->angle`). If the Arch-Vile loses line-of-sight, the flame stops moving but continues to animate.

## See also

- **`A_Warp`** — more versatile repositioning action with per-axis offset control, collision checks, and interpolation options. Originally designed as a generalization of `A_Fire`'s orbit behavior.
- **`A_VileStart` / `A_VileTarget` / `A_VileAttack`** — the Arch-Vile's attack sequence, which sets up `tracer` (the flame actor) and `target` (the victim) pointers prior to calling `A_Fire`.
