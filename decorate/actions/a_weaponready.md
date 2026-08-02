# `action void A_WeaponReady(int flags = 0)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_WeaponReady` (retrieved 2026-07-31, oldid=52259) + verified against
the Zandronum source's `src/p_pspr.cpp:907-919` (`DEFINE_ACTION_FUNCTION_PARAMS(AInventory,
A_WeaponReady)`), flag definitions at `src/p_pspr.cpp:895-905` (`enum EWRF_Options`), and
supporting functions at `src/p_pspr.cpp:785-893`.
**Bucket:** `src/p_pspr.cpp:907` (`DEFINE_ACTION_FUNCTION_PARAMS(AInventory, A_WeaponReady)`) —
note that the owning class is `AInventory`, not `Weapon` as the wiki states.

Prepares a weapon for firing, bobbing, or deselection by setting internal weapon-state flags based
on the provided flags parameter. Called once per weapon-ready state frame or loop (not every tic) —
once set, the enabled flags persist until the current state ends and the next state is entered via
`P_SetPsprite`.

## Parameters

| Flag | Value | Effect |
|---|---|---|
| `WRF_NoBob` | 1 | Weapon sprite does not bob. |
| `WRF_NoSwitch` | 2 | Player cannot deselect the weapon during this call (switch-pending requests are held until the next `A_WeaponReady` call). |
| `WRF_NoPrimary` | 4 | Weapon cannot enter its `Fire` state. |
| `WRF_NoSecondary` | 8 | Weapon cannot enter its `AltFire` state. |
| `WRF_NoFire` | 12 | Shorthand for `WRF_NoPrimary \| WRF_NoSecondary` — disables all firing. |
| `WRF_AllowReload` | 16 | Player can enter the weapon's `Reload` state if the Reload key is pressed. |
| `WRF_AllowZoom` | 32 | Player can enter the weapon's `Zoom` state if the Zoom key is pressed. |
| `WRF_DisableSwitch` | 64 | Weapon deselection is completely blocked (not just held) until the next `A_WeaponReady` call. Unlike `WRF_NoSwitch` which just delays switching, this clears pending weapon-switch requests. |

## Behavior

- **Default state without flags** (when `A_WeaponReady(0)` or `A_WeaponReady()` is called): the
  function sets flags enabling all firing modes and bobbing, allowing deselection, and allowing
  switching (but not Reload/Zoom without their respective flags).
- **Flag persistence across tics**: once a flag is set by a single `A_WeaponReady` call, it remains
  set for the entire duration of the weapon state (e.g., a 10-tic state set with `A_WeaponReady`
  only once on the first tic will allow firing/bobbing/switching for all 10 tics). The flags are
  cleared only when the state ends and `P_SetPsprite` transitions to the next weapon state.
- **No per-tic clearing**: despite a misleading internal comment, flags are not cleared every tic —
  they persist across the state's entire duration per `P_MovePsprites`'s state timer countdown.
- **Silent no-op if no player or no ready weapon**: the function includes early checks for the
  calling actor's owning player and ready weapon. If either is missing, the function returns
  immediately and all flag-setting is skipped. This is typical for weapon actions but worth knowing
  if testing in isolation.

## Zandronum-specific: no User# weapon states

The wiki page documents `WRF_ALLOWUSER#` flags (for `User1`, `User2`, `User3`, `User4` weapon
states). **These flags and states do not exist in Zandronum.** The weapon-state set in Zandronum
is hardcoded to: `Ready`, `Select`, `Deselect`, `Fire`, `Hold`, `AltFire`, `AltHold`, `Reload`,
`Zoom` — there is no configurable user-defined state. Any mod targeting Zandronum should omit these
flags and not expect such states to exist.

## Common usage

A typical weapon `Ready` state loop:

```
Ready:
  WEAP A 1 A_WeaponReady;
  Loop;
```

To allow firing without bobbing (e.g., during a cooldown):

```
Cooldown:
  WEAP A 5 A_WeaponReady(WRF_NoBob);
  Goto Ready;
```

To prevent player weapon-switching mid-attack sequence:

```
Fire:
  WEPF A 4;
  WEPF B 4 A_FireProjectile('Rocket');
  WEPF C 4;
  WEPF D 4 A_WeaponReady(WRF_NOSWITCH); // Allow firing, but lock weapon
  WEPF E 4;
  Goto Ready;
```

## See also

- [Creating weapons](../concepts/creating-weapons.md) — weapon states and reserved state names.
- [A_Lower](a_lower.md) / [A_Raise](a_raise.md) — weapon selection/deselection animation actions.
