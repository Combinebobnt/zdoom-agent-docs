# `A_SetPitch(float pitch = 0, int flags = 0)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_SetPitch` (retrieved 2026-08-01, oldid=55322) + verified against
the Zandronum source's native declaration `wadsrc/static/actors/actor.txt:297` and implementation
`src/thingdef/thingdef_codeptr.cpp:4988-5011`, plus `src/p_mobj.cpp:3929-3940` and `src/d_player.h:675-676`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_SetPitch)` — actor action on AActor.

Sets the actor's pitch (vertical angle/viewing angle) to a specified value in degrees, with optional interpolation and clamping. In DECORATE, this is the only way to change an actor's pitch; ZScript allows direct assignment to the `pitch` field but this function enables sub-tic interpolation for smoother visual updates.

## Parameters

- **pitch**: The actor's new pitch angle in degrees. Negative values point up, positive values point down (per the engine's convention). Absolute value, not relative — to rotate by a relative amount, reference the actor's current `pitch` field in the expression (e.g., `pitch - 5` to look 5 degrees higher).

- **flags**: Bitfield controlling interpolation and clamping behavior:
  - `SPF_INTERPOLATE` (value 2) — if set and the actor has a `player` field, interpolation is enabled for that frame by setting the `CF_INTERPVIEW` flag, making pitch rotation appear smooth across the frame rather than snapping to the new angle. Non-player actors ignore this flag (pitch changes apply immediately).
  - `SPF_FORCECLAMP` (value 1) — if set, pitch is clamped regardless of whether the actor has a `player` field. When not set, clamping only applies to actors with a `player` field (player-controlled actors).

## Engine scope

**The upstream ZDoom Wiki documents a 3-parameter form with an `int ptr` parameter that does not exist in Zandronum.** Zandronum's `A_SetPitch` takes only 2 parameters (pitch and flags) and always operates on the calling actor — there is no pointer parameter to redirect to a different actor.

## Clamping behavior

Pitch values are clamped as follows when applicable:

- **For actors with a `player` field** (player-controlled actors): pitch is clamped to `player->MinPitch` and `player->MaxPitch`, which are typically −32° (looking up) to +56° (looking down) on the server, but may vary based on renderer settings or configuration on clients.

- **For non-player actors with `SPF_FORCECLAMP` set**: pitch is clamped to approximately ±90° (with a fine-angle unit adjustment to avoid exact boundaries).

- **For non-player actors without `SPF_FORCECLAMP`**: no clamping is applied.

The wiki's claim that clamping always applies "`SPF_FORCECLAMP`" to player actors "(Verification needed)" is imprecise — players are always clamped regardless of the flag; the flag only forces clamping on non-players.

## Behavior

For actors with a `player` field and `SPF_INTERPOLATE` set, if the pitch value actually changes, the engine sets the `CF_INTERPVIEW` flag to enable view interpolation for that frame. The action function itself performs no network replication; whether the resulting pitch reaches clients via the general actor-update replication path is untraced.

## Example

A weapon that kicks the player's view vertically when fired:

```
ACTOR KickingRifle : DoomWeapon
{
  Weapon.SelectionOrder 1300
  Weapon.AmmoUse 1
  Weapon.AmmoGive 20

  States
  {
    Fire:
      RIFG A 4;
      RIFG A 4
      {
        A_FireBullets(5.6, 0, 1, 5);
        A_SetPitch(pitch + 2, SPF_INTERPOLATE | SPF_FORCECLAMP);
      }
      RIFG A 0 A_ReFire;
      Goto Ready;

    Ready:
      RIFG A 1 A_WeaponReady;
      Loop;

    Deselect:
      RIFG A 1 A_Lower;
      Loop;

    Select:
      RIFG A 1 A_Raise;
      Loop;
  }
}
```

## See also

- `A_SetAngle` — analogous function for yaw (facing angle); shares the `SPF_INTERPOLATE` flag but `SPF_FORCECLAMP` has different meaning there (unused vs. here where it controls non-player clamping).
