# `State A_CheckBlock(StateLabel label, int flags = 0, int ptr = AAPTR_DEFAULT, double xofs = 0, double yofs = 0, double zofs = 0, double angle = 0)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki `A_CheckBlock` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_CheckBlock&oldid=50190) + verified against the UZDoom source's `src/playsim/p_actionfunctions.cpp:4694`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, CheckBlock)` — native primitive is a bool check that the DECORATE wrapper resolves into a state jump.

Checks if a specified actor pointer would be blocked at a position computed from offsets relative to the caller's current angle. If the position is blocked, the caller jumps to the given state. Otherwise, execution continues.

## Parameters

- **label**: The state to jump to if the position would be blocked. If the position is clear, the jump does not occur.
- **flags**: Bitwise-OR'd combination of blocking-check flags (see Flags section below). Default `0` checks for both line and actor obstacles.
- **ptr**: Which actor pointer (target/master/tracer/default) to check for blockage at the target position. Defaults to `AAPTR_DEFAULT` (the caller itself).
- **xofs**: Forward offset from the pointer's position, in map units, calculated relative to the caller's current facing angle. Positive values move away from the caller along its heading.
- **yofs**: Lateral offset from the pointer's position, in map units, calculated relative to the caller's current facing angle. **Positive values offset to the right of the caller's facing direction** (wiki states "left", contradicting the source code).
- **zofs**: Vertical offset from the pointer's position, in map units. Positive values move upward.
- **angle**: Angular offset from the caller's current angle, in degrees. Positive values rotate counter-clockwise. This parameter is ignored if the `CBF_ABSOLUTEANGLE` flag is set.

## Flags

- **CBF_NOLINES** — Ignore line obstacles; only check for actor blockage and (if `CBF_DROPOFF` is set) dropoff hazards.
- **CBF_SETTARGET** — If an actor blocks the test position, set that actor as the caller's target.
- **CBF_SETMASTER** — If an actor blocks the test position, set that actor as the caller's master.
- **CBF_SETTRACER** — If an actor blocks the test position, set that actor as the caller's tracer.
- **CBF_SETONPTR** — Apply the `CBF_SET*` pointer changes to the tested actor pointer itself, not the caller. Has no effect if none of the `CBF_SET*` flags are set.
- **CBF_DROPOFF** — Perform full movement checking (including dropoff detection) instead of a basic position test. When set, the function tests whether the pointer can actually move to the target position and drop safely if gravity applies; without it, only checks whether the position itself is passable.
- **CBF_NOACTORS** — Ignore actor obstacles; only check for line blockage and dropoff hazards.
- **CBF_ABSOLUTEPOS** — Interpret `xofs`, `yofs`, and `zofs` as absolute map coordinates rather than offsets relative to the pointer's position. The `angle` parameter is ignored when this flag is set.
- **CBF_ABSOLUTEANGLE** — Interpret `angle` as an absolute map direction (in degrees) rather than an offset from the caller's current angle.

## Return value

Returns the state the caller should jump to if the position is blocked, or null if the position is clear and no jump occurs. The return value is only meaningful in anonymous or custom ZScript functions; in standard DECORATE action syntax, the jump happens automatically if blockage is detected.

## Blocking detection behavior

The function tests whether the pointer can exist at the target position without colliding with map geometry or other actors. Two distinct test modes apply depending on the `CBF_DROPOFF` flag:

- **Without `CBF_DROPOFF`** (basic check): Tests whether the position is passable via `P_TestMobjLocation`, which ignores some complexity that would prevent actual movement. The `CBF_SETTARGET`/`CBF_SETMASTER`/`CBF_SETTRACER` pointers are still set even when combined with `CBF_NOACTORS`, though they are not set when `CBF_DROPOFF` is also active.
- **With `CBF_DROPOFF`** (full movement check): Uses `P_CheckMove` with flags such as `PCM_DROPOFF`, `PCM_NOACTORS`, and `PCM_NOLINES` to perform realistic movement simulation. This catches dropoffs and step heights the basic check would miss, but returns `false` (no blockage detected) only if the move would actually succeed.

## Examples

A monster that runs away if obstacles appear near it:

```text
Actor NervousZombieman : Zombieman
{
    States
    {
    See:
        POSS AA 4 Fast A_Chase
        POSS A 0 A_CheckBlock("Nervous", CBF_SETTARGET, AAPTR_DEFAULT, radius + 1)
        POSS BB 4 Fast A_Chase
        POSS B 0 A_CheckBlock("Nervous", CBF_SETTARGET, AAPTR_DEFAULT, radius + 1)
        POSS CC 4 Fast A_Chase
        POSS C 0 A_CheckBlock("Nervous", CBF_SETTARGET, AAPTR_DEFAULT, radius + 1)
        POSS DD 4 Fast A_Chase
        POSS D 0 A_CheckBlock("Nervous", CBF_SETTARGET, AAPTR_DEFAULT, radius + 1)
        Loop
    Missile:
        POSS E 10 A_FaceTarget
        POSS F 8 A_PosAttack
        POSS E 8
        Goto See
    Pain:
        POSS G 3
        POSS G 3 A_Pain
        Goto Nervous
    Nervous:
        POSS AABBCCDD 2 Fast A_Wander
        POSS A 0 A_Jump(64, "See")
        Loop
    Raise:
        POSS K 5
        POSS JIH 5
        Goto See
    }
}
```

## Engine-family divergence

This action exists only in UZDoom/GZDoom-family engines (including GZDoom 2.3.1 and later). It does not exist in Zandronum's DECORATE codebase, which traces to an older ZDoom baseline predating this function's introduction.
