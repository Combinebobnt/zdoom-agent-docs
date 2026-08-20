# `A_Weave` (generalized sinusoidal movement)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `A_Weave` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_Weave&oldid=34283) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:5325-5376` and cross-checked against UZDoom.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_Weave)` in `src/thingdef/thingdef_codeptr.cpp`.

A generalized projectile-weaving action that moves an actor in sinusoidal patterns along two independent axes: horizontal (XY plane) and vertical (Z). Must be called each time the state runs (the effect depends on state duration) to maintain continuous weaving. Equivalent to, and a generalization of, the earlier `A_BishopMissileWeave` and `A_CStaffMissileSlither` actions (which remain available but are considered deprecated).

## Signature

```text
void A_Weave(int horzspeed, int vertspeed, float horzdist, float vertdist)
```

## Parameters

### `horzspeed` (int)

Horizontal phase-advance speed. Controls how quickly the weaving pattern cycles through the horizontal wave. The speed is applied modulo 64 to an internal 6-bit phase counter (`WeaveIndexXY`); a cycle completes in `64 / horzspeed` calls (e.g., a speed of 2 yields a 32-call cycle). Negative speeds run the weave backwards. A speed of 0 disables horizontal weaving; when paired with zero `horzspeed`, nonzero `horzdist` is ignored and the horizontal phase counter does not advance.

**Edge case:** A `horzspeed` of 64 or any multiple thereof produces zero net displacement (the phase increments wrap the counter to itself), though the branch still executes, including the `MF_NOBLOCKMAP` side effect on actors with `MF5_NOINTERACTION` set.

### `vertspeed` (int)

Vertical phase-advance speed. Controls the vertical weaving cycle, identically to `horzspeed` but for the Z axis and the `WeaveIndexZ` phase counter. A speed of 0 disables vertical weaving.

### `horzdist` (float)

Horizontal amplitude scaling. The maximum distance the projectile weaves from its linear trajectory in the XY plane is **8 times** the passed value due to the fixed-point sine-table scale (peak sine value is `FRACUNIT`, scaled via `MulScale13` with `xydist`, yielding `FRACUNIT * xydist >> 13` = `xydist * 8`). A value of `1.0` produces ±8 map units of horizontal displacement; `2.0` produces ±16 map units. Paired with `horzspeed` 0, this parameter is ignored (no horizontal motion).

**Wiki divergence:** The ZDoom wiki states this is "the maximum distance to which the projectile will horizontally stray" without accounting for the 8× scaling — its figure is off by a factor of 8. Both Zandronum and UZDoom apply the same scaling (UZDoom's `BobSin` includes an explicit `* 8` factor).

### `vertdist` (float)

Vertical amplitude scaling. Same scaling as `horzdist`: a value of `1.0` produces ±8 map units of vertical displacement. Paired with `vertspeed` 0, this parameter is ignored.

## Behavior

### Horizontal motion

When `horzspeed != 0` and `horzdist != 0`, the actor's XY position is adjusted perpendicular to its current facing angle (`self->angle + ANG90`). The displacement is computed as a sinusoidal delta between the old phase and the new phase, then applied via `P_TryMove` — **collision-checked**. If the move is blocked, the actor's position does not change, but the phase counter (`WeaveIndexXY`) still advances.

### Vertical motion

When `vertspeed != 0` and `vertdist != 0`, the actor's Z position is adjusted directly via `self->z += / -= ...` — **not collision-checked**. The actor can weave through the ceiling or floor. The phase counter (`WeaveIndexZ`) always advances when vertical weaving is enabled.

### Phase independence

The two axes' phase counters are independent. Disabling one axis via a zero speed does not affect the other's counter.

### Special case: `MF5_NOINTERACTION` flag

Actors with the `MF5_NOINTERACTION` flag set (non-interactive decorations, etc.) do not call `P_TryMove` for horizontal motion. Instead, the actor is unlinked from the blockmap, `MF_NOBLOCKMAP` is set via `|=` (and **never cleared by A_Weave**), and the position is updated directly. This is a one-time side effect that persists after the action returns.

### Network/clientside behavior

**No client-mode guard.** Unlike many state-altering actions (e.g. `A_BishopDecide`), `A_Weave` runs its full logic on both server and client — it advances the phase counters and calls `P_TryMove` on both sides. If the server and client disagree about whether a horizontal move was blocked, their `WeaveIndexXY` counters diverge and stay diverged on subsequent calls. The practical impact of this desync beyond the phase-counter divergence was not traced.

### Phase aliasing

The `WeaveIndexXY` and `WeaveIndexZ` fields are 6-bit counters (range [0, 63]). Initial phase can be set via the `weaveindexXY` and `weaveindexZ` DECORATE properties; values are stored as-is and masked modulo 64 on first use inside `A_Weave`.

## Equivalent actions

- `A_Weave(2, 2, 2.0, 1.0)` — equivalent to the older `A_BishopMissileWeave`
- `A_Weave(3, 0, 1.0, 0.0)` — equivalent to the older `A_CStaffMissileSlither`

Both of these actions are deprecated but still callable in DECORATE.

## Notes

- **Call frequency matters**: A_Weave's effect depends on how frequently it is called. Called from a 1-tic state produces finer motion; from a 4-tic state produces larger jumps. The displacement per call is a function of the phase increment and the sine curve, not a fixed distance per tic.
- **Weave axis orientation**: The horizontal plane is perpendicular to the actor's facing angle. A projectile spinning mid-flight will see its weave axis rotate with it.
- **No collision checking on Z adjustment**: The Z branch writes `self->z` directly with no `P_TryMove` and no floor/ceiling clamp. A_Weave itself will not prevent the actor from being displaced into a floor or ceiling; whether anything else corrects that per tic was not traced.
