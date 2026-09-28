# `action void A_WeaponReady(int flags = 0)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki `A_WeaponReady` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_WeaponReady&oldid=52259) + verified against
the Zandronum source's `src/p_pspr.cpp:907-919` (`DEFINE_ACTION_FUNCTION_PARAMS(AInventory,
A_WeaponReady)`), flag definitions at `src/p_pspr.cpp:895-905` (`enum EWRF_Options`), and
supporting functions at `src/p_pspr.cpp:785-893`. **Tic-timing addition (2026-09-22):** the
"Tic timing" section and its A_Jump divergence are source-derived, read from the Zandronum source's
`src/p_pspr.cpp:174-267` (`P_NewPspriteTick`, `P_SetPsprite`), `:1424-1468` (`P_MovePsprites`),
`:931` (`P_CheckWeaponFire`) and `src/thingdef/thingdef_codeptr.cpp:695-723` (`DoJump`), bodies
unchanged since `28f736fb3`; and the UZDoom source (@98b16b78fc) `src/playsim/p_pspr.cpp:452-585`
(`DPSprite::NewTick`, `DPSprite::SetState`), `src/p_tick.cpp:206` and
`wadsrc/static/zscript/actors/player/player.zs:474,543` (`CheckWeaponFire`, `TickPSprites`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `src/p_pspr.cpp:907` (`DEFINE_ACTION_FUNCTION_PARAMS(AInventory, A_WeaponReady)`) —
note that the owning class is `AInventory`, not `Weapon` as the wiki states.

Prepares a weapon for firing, bobbing, or deselection by setting internal weapon-state flags based
on the provided flags parameter. Called once per weapon-ready state frame or loop (not every tic) —
once set, the enabled flags persist until the next `P_SetPsprite` call on the weapon layer (see
"Tic timing" for what counts as one call).

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
  cleared once at the start of each weapon-layer `P_SetPsprite` call, not once per state entered:
  a run of 0-tic states walked inside one call shares a single clear.
- **No per-tic clearing**: despite a misleading internal comment, flags are not cleared every tic —
  they persist across the state's entire duration per `P_MovePsprites`'s state timer countdown.
- **No-op only when there is no player; a player with no ready weapon still sets some flags**: each
  helper `A_WeaponReady` calls checks for `self->player` on its own, so with no player none of the
  flags are set. With a player but no `ReadyWeapon`, only the fire-enabling and bobbing flags (and
  the ready sound) are skipped. The switch-ok, refire-switch-ok, reload-ok, zoom-ok and
  disable-switch flags are still set. In practice `P_SetPsprite` never runs a weapon-layer action
  without a `ReadyWeapon`, so the no-weapon case only arises if `A_WeaponReady` is invoked outside
  the normal psprite path.

## Tic timing

Both engines, same shape.

- **Order within a tic.** Each tic the player's psprite update first ticks every layer (which may
  advance the weapon into a Ready state and run `A_WeaponReady`), then checks for a weapon switch,
  then runs the fire check (Zandronum `P_MovePsprites` then `P_CheckWeaponFire`; UZDoom
  `PlayerPawn.TickPSprites` then `CheckWeaponFire`). The fire check fires if the ready bit is set
  and attack is held.
- **Fire is accepted the same tic a Ready state is entered.** A Fire sequence that falls back into
  a Ready state calling `A_WeaponReady` can start the next Fire in that very tic, so the Ready state
  adds no time to a held-fire cycle. A 4+6+4-tic `Fire` sequence ending in `Goto Ready` (with
  `WEAP A 1 A_WeaponReady`) cycles in 14 tics held, not 15. Doom's own weapons loop through
  [A_ReFire](a_refire.md) instead and never pass through Ready while held.
- **No +1 per shot either.** The Fire state set by the fire check is not decremented until the
  next tic: every psprite's pending-tick flag is re-armed once at the start of each game tic
  (Zandronum `P_NewPspriteTick`, UZDoom `DPSprite::NewTick`, both called from the ticker), and
  setting a state mid-tic clears it for that layer.
- **A 0-tic `A_WeaponReady` still latches.** The bits are cleared once on entry to a `P_SetPsprite`
  call, before its 0-tic loop. `A_WeaponReady` on a 0-tic state sets them, the loop runs on into the
  next timed state without clearing again, and the bits stay set for that whole timed state. So

  ```decorate
  Ready:
    WEAP A 0 A_WeaponReady;
    WEAP A 10;
    Loop;
  ```

  accepts fire on the tic it is reached and on every tic of the 10-tic state that follows, the
  same as `WEAP A 10 A_WeaponReady`. See the divergence below for the one exception.
- `sv_fastweapons` (both engines) and Zandronum's double-firing-speed cheat change psprite
  durations, not the ordering above.

## Engine-family divergence: A_Jump inside a 0-tic Ready chain

If a jump action taken later in the same 0-tic chain moves the weapon layer, the engines differ.
In Zandronum, a jump from a weapon state (`DoJump`) calls `P_SetPsprite` again, nested, which
clears the ready bits a second time: a 0-tic `A_WeaponReady` followed by a taken `A_Jump` no
longer latches, unless the jump target calls `A_WeaponReady` itself. In UZDoom, a jump returns
its target to the running `DPSprite::SetState` loop, which continues without a second clear, so
the bits set earlier in the chain survive.

## Engine-family divergence: implementation and owning class

In UZDoom, `A_WeaponReady` is implemented entirely in ZScript as an `action` method directly on
the `Weapon` class itself (`wadsrc/static/zscript/actors/inventory/weapons.zs`), not as a native
C++ function on `AInventory` as in Zandronum. This means the wiki's claim that the owning class is
`Weapon` — which this file's `Bucket:` field calls out as incorrect for Zandronum — is actually
correct for UZDoom. The documented flag/parameter behavior above (default state, flag persistence
across a state's duration via `P_SetPsprite`/`DPSprite::SetState`, `WRF_NoFire` semantics, the
misleading "cleared every tic" comment) holds identically on UZDoom; only the underlying
implementation language and owning class differ.

## Zandronum-specific: no User# weapon states

The wiki page documents `WRF_ALLOWUSER#` flags (for `User1`, `User2`, `User3`, `User4` weapon
states). **These flags and states do not exist in Zandronum.** The weapon-state set in Zandronum
is hardcoded to: `Ready`, `Select`, `Deselect`, `Fire`, `Hold`, `AltFire`, `AltHold`, `Reload`,
`Zoom` — there is no configurable user-defined state. Any mod targeting Zandronum should omit these
flags and not expect such states to exist.

## Common usage

A typical weapon `Ready` state loop:

```text
Ready:
  WEAP A 1 A_WeaponReady;
  Loop;
```

To allow firing without bobbing (e.g., during a cooldown):

```text
Cooldown:
  WEAP A 5 A_WeaponReady(WRF_NoBob);
  Goto Ready;
```

To prevent player weapon-switching mid-attack sequence:

```text
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
