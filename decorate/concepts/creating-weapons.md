# Creating weapons

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-26); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** ZDoom Wiki "Creating new weapons" (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=Creating_new_weapons&oldid=52274), cross-checked against the Zandronum source's weapon-state handlers (`src/g_shared/a_weapons.cpp:827-890`), action-function implementations (`src/p_pspr.cpp:907-1275`), property definitions (`src/thingdef/thingdef_properties.cpp:1777-1990`), and the generic state-machine machinery. The wiki page describes ZDoom/GZDoom-family engines, where DECORATE is currently deprecated in favor of ZScript; for Zandronum, DECORATE is the only scripting surface available for weapon definitions.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

This page covers what distinguishes a weapon from other inventory items in DECORATE, the states that make one work, and how to define variations (alternate fire, hold sequences). It does not cover action-function semantics themselves — see the `actions/` directory for those — or the state-machine model (label/state-line grammar, control flow, duration semantics, special sprite tokens), which is already covered in `state-machine.md`.

## What makes a weapon: inheritance from Weapon

The only requirement to create a new weapon is to inherit from the `Weapon` class (directly or indirectly through a parent weapon like `Shotgun`). The parent weapon provides:

- **Class membership**: only the `Weapon` class and its descendants have states that the engine looks up by weapon-specific label names (`Ready`, `Select`, `Deselect`, `Fire`, `Hold`, `AltFire`, `AltHold`, `Flash`, `AltFlash`), so non-weapons cannot use them. See "Weapon-specific states" below.
- **Ammunition handling**: the `AmmoType1`/`AmmoType2`, `AmmoUse1`/`AmmoUse2`, and `AmmoGive1`/`AmmoGive2` properties specific to the `Weapon` class (shorthand forms `AmmoType`, `AmmoUse`, `AmmoGive` map to the `1` variants — `thingdef_properties.cpp:1777-1855`). Non-weapons cannot hold or fire ammunition.
- **Selection priority**: the `Weapon.SelectionOrder` property, which governs automatic weapon choice (lower values have higher priority). It does not order next/previous-weapon cycling or slot keys; those follow the weapon slots (see `Weapon.SlotNumber` below). On pickup, Zandronum compares it only under the default `switchonpickup 1`: the new weapon becomes pending if its `SelectionOrder` is lower than the pending weapon's, or the ready weapon's when none is pending. `switchonpickup 2` always switches, `0` never does, and `+WEAPON.NO_AUTO_SWITCH` opts a weapon out (`g_shared/a_weapons.cpp:397-442`, `d_netinfo.cpp:87`). UZDoom's pickup doesn't compare `SelectionOrder`: it makes the new weapon pending unless the player's never-switch setting or the weapon's no-auto-switch flag is set (`Weapon.AttachToOwner` in `wadsrc/static/zscript/actors/inventory/weapons.zs`).
- **Weapon-layer animation**: two-layer sprite rendering. A weapon layer (the weapon grip/hand) and a flash layer (the muzzle flash). On Zandronum both layers (`ps_weapon`, `ps_flash`, `p_pspr.h:46-47`) belong to the player and always run the ready weapon's states; a non-weapon inventory item has no layer of its own. The `Flash`/`AltFlash` states run in the flash layer independently from `Fire`/`AltFire` sequences in the weapon layer. See "Engine-family divergence" below for how these layers are referenced in each engine.

Inheriting from an existing weapon (e.g. `Shotgun`, `PlasmaRifle`) is simpler than reimplementing every property from scratch, since the parent provides defaults for all of the above — you can override only what you need to customize.

## Actor properties for weapons

Beyond the minimum inheritance, weapons typically define:

- **`Health`** — the weapon is sometimes treated as a destructible pickup; this is optional and rarely used for actual weapons, unlike `Monster`-type actors.
- **`Radius` and `Height`** — collision cylinder (when lying on the ground as a pickup). Typical values are around 20 (radius) and 16 (height) for weapon pickups.
- **`Inventory.PickupSound`** — sound lump name played when the weapon is picked up (must be defined in the SNDINFO lump). A property of the `Inventory` class (the parent of `Weapon`).
- **`Inventory.PickupMessage`** — message shown to the player when picking up the weapon (e.g. `"You got the heavy cannon!"`). Optional. If omitted, the parent's message is inherited, falling back to `Inventory`'s generic `"$TXT_DEFAULTPICKUPMSG"` (`wadsrc/static/actors/shared/inventory.txt:8`, class metadata copied on derive at `dobjtype.cpp:307`).
- **`Weapon.SlotNumber`** — integer slot (0–9) controlling which weapon-switching key selects this weapon. Slot 3 is typical for shotgun-type weapons. Order within a slot comes from `Weapon.SlotPriority`, not `SelectionOrder` (`g_shared/a_weapons.cpp:1455-1460`, `thingdef_properties.cpp:1996`). A weapon the player class's own slot list already places keeps that placement.
- **`Weapon.SelectionOrder`** — integer priority for automatic weapon choice (lower values = higher priority; `g_shared/a_weapons.cpp:442`). When the player runs out of ammo (or a script takes the ready weapon), the engine picks the usable weapon with the lowest `SelectionOrder` value (`BestWeapon`, `p_user.cpp:1158`, `1188`). Manual cycling uses the slots instead.
- **`Weapon.AmmoGive`** (or `AmmoGive1`/`AmmoGive2`) — how many rounds of ammunition the weapon grants to the player on pickup. This is **not** the maximum ammo capacity; it's just what one weapon pickup provides. The maximum is controlled by the ammo item itself (e.g. `Shells` has its own `MaxAmount` property).
- **`Weapon.AmmoUse`** (or `AmmoUse1`/`AmmoUse2`) — how many rounds of `AmmoType1` primary fire consumes (`AmmoUse2`: rounds of `AmmoType2`, consumed by alternate fire). Ammo is taken once per call of an ammo-using attack action such as `A_FireBullets` (whose default `flags` include `FBF_USEAMMO`), not once per pass through `Fire` (`DepleteAmmo`, `g_shared/a_weapons.cpp:713-752`, called from e.g. `thingdef/thingdef_codeptr.cpp:1579`; UZDoom `wadsrc/static/zscript/actors/inventory/weapons.zs:1055`, `stateprovider.zs:111-115`). The same value is the threshold `CheckAmmo` requires before `Fire`/`AltFire` is entered (`g_shared/a_weapons.cpp:630-701`; UZDoom `weapons.zs:974`). If not set or 0, the weapon never consumes ammo.
- **`Weapon.AmmoType`** (or `AmmoType1`/`AmmoType2`) — the class name of the ammunition item (e.g. `"Shell"`, `"Clip"`). Must match an actual inventory item that inherits from `Ammo`.
- **`AttackSound`** — sound lump name played when the weapon fires (if the fire sequence calls `A_FireBullets` or another firing action; see below). This is an actor property (inherited from the root `Actor` class), not a `Weapon.` property, so the DECORATE spelling is just `AttackSound` (`thingdef_properties.cpp:689`). The property reads from the weapon actor itself. It is its own sound name, resolved independently of `Inventory.PickupSound`, so it needs its own SNDINFO entry.

The unnumbered forms (`AmmoType`, `AmmoUse`, `AmmoGive`) are aliases mapping to the `1` variants (`AmmoType1`, `AmmoUse1`, `AmmoGive1`), allowing shorter declarations when only primary fire matters.

## Weapon-specific states

Every weapon (and only weapons) recognizes a set of reserved label names looked up by the engine at specific points during gameplay. The engine finds these states via the same label lookup documented in `state-machine.md`. A weapon with no `Hold` state falls back to `Fire` when the player holds the fire button because `GetAtkState` tries `Hold` first and then `Fire` (`g_shared/a_weapons.cpp:864-869`; see "Hold sequences and alternate fire" below). `Ready`, `Select`, `Deselect` and `Fire` are mandatory, not optional: a weapon class that has any of the four (inherited ones count) but lacks another fails DECORATE loading with "Weapon <name> doesn't define a ... state" (`thingdef/thingdef.cpp:253-282`, fatal at `359`). A base class with none of the four is exempt. UZDoom has the same check.

### Core weapon sequence

- **`Spawn:`** The idle animation when the weapon lies on the ground as a pickup. Optional; if omitted, the weapon is invisible on pickup.
- **`Ready:`** The default animation when the weapon is selected and the player is not firing. Must call `A_WeaponReady` (or an equivalent idle action) to allow the weapon to fire, be deselected, and bob naturally.
  - `A_WeaponReady` takes optional flags (e.g. `WRF_NOPRIMARY`, `WRF_NOSECONDARY`) to disable specific fire modes and prevent the weapon from being used in certain circumstances. See "Engine-family divergence" below for differences in where this action is defined and which `WRF_*` flag variants are available.
- **`Select:`** Entered when the player switches to this weapon. Typically calls `A_Raise` repeatedly in a loop to slide the weapon up from the bottom of the screen. `A_Raise` itself jumps to `Ready` once the sprite reaches the top (`p_pspr.cpp:1192-1199`), so the usual `Loop` needs no `Goto Ready`. A `Select` sequence that never calls `A_Raise` must reach `Ready` itself. If a switch is pending (on Zandronum, unless `ZACOMPATF_FULL_WEAPON_LOWER` is set), `A_Raise` instead drops the weapon into `Deselect` (`p_pspr.cpp:1185-1189`).
- **`Deselect:`** Entered when the player switches away from this weapon. Typically calls `A_Lower` repeatedly in a loop to slide the weapon off the bottom of the screen. Once the weapon is fully lowered, `A_Lower` calls `P_BringUpWeapon`, which starts the pending weapon's `Select` from the bottom of the screen, or, with no switch pending, puts the same weapon straight back into `Ready` at full height (`p_pspr.cpp:1161`, `279-329`). A dead player's weapon just stays hidden. So `Deselect` need not explicitly `Goto` anything.

`A_Raise` and `A_Lower` move the weapon sprite by a fixed increment (`FRACUNIT*6`) per call, regardless of duration (`p_pspr.cpp:46-47`, `1120`, `1170`). This is why a zero-tic `A_Raise` or `A_Lower` on the same line (e.g. `TNT1 A 0 A_Raise` followed by `WEAP A 1 A_Raise`) produces faster animation — the zero-tic line executes the movement immediately without consuming a game tic.

### Fire sequences

- **`Fire:`** Entered when the player presses the primary-fire button while in the `Ready` state. Performs the firing animation and action(s). After firing, typically calls `A_ReFire` at the end to check whether the fire button is still held. If it is (and there's enough ammo), `A_ReFire` re-enters the attack sequence. If not, `A_ReFire` never jumps anywhere itself: execution falls through to the next state line, conventionally `Goto Ready`.
  - When the button is held, `A_ReFire` increments the player's refire counter and re-fires, which picks `Hold` if the weapon defines it and `Fire` otherwise (via `GetAtkState(hold)`, `g_shared/a_weapons.cpp:864-869`). An optional state argument replaces that lookup. If the ammo check fails at that point, the re-fire is abandoned, the weapon auto-switches, and the sequence falls through as above. When the button is released (or a weapon change is pending, or the player is dead), `A_ReFire` resets the refire counter and runs the same auto-switching ammo check (`p_pspr.cpp:338-381`, `1054-1082`; UZDoom `wadsrc/static/zscript/actors/inventory/stateprovider.zs:434-461`, `wadsrc/static/zscript/actors/player/player.zs:410-434`, `weapons.zs:190-196`). With no `Hold` state, `A_ReFire` re-enters `Fire` for as long as the button stays held and ammo lasts.
- **`Hold:`** (optional) Chosen instead of `Fire` whenever the player's refire counter is nonzero at fire time. `A_ReFire` is what makes it nonzero, so in practice `Hold` is reached through `A_ReFire` with the button held. If a weapon defines `Hold`, it typically repeats the attack at a different pace or with reduced recoil (e.g. semi-auto fire mode vs. full auto). If no `Hold` state exists, `A_ReFire` instead loops in `Fire`, producing continuous rapid-fire.
- **`A_CheckReload`** — action function that checks whether the weapon has enough ammo for another shot in the currently active fire mode (chosen by `bAltFire`: `AmmoUse1` after primary fire, `AmmoUse2` after alternate fire), and if not, calls `PickNewWeapon(NULL)` to auto-switch to the next available weapon in priority order (`p_pspr.cpp:1104-1112`, `g_shared/a_weapons.cpp:630-701`; UZDoom `weapons.zs:477-484`). Unlike states, this is called explicitly by a firing sequence when you want to check ammo mid-animation (e.g. after every shot or after a reload sequence).

### Alternate fire

- **`AltFire:`** (optional) Entered when the player presses the alternate-fire button (separate from primary fire) while in the `Ready` state. Same structure as the `Fire` sequence — perform animation/action and end with `A_ReFire` (which will check for alternate-fire hold via `bAltFire` flag). If no `AltFire` state is defined, the weapon cannot perform alternate fire; pressing the button has no effect.
- **`AltHold:`** (optional) Analogous to `Hold` for alternate-fire sequences. Reached via `A_ReFire` if the alternate-fire button is held and an `AltHold` state exists (via `GetAltAtkState(hold)`, `g_shared/a_weapons.cpp:883-884`).

The engine distinguishes primary and alternate fire through internal flags (`bAltFire`) and separate internal fire paths (`P_FireWeapon` vs. `P_FireWeaponAlt` in Zandronum, `PlayerPawn.FireWeapon` vs. `FireWeaponAlt` in UZDoom; neither is a DECORATE action function), not through anything visible in DECORATE — a fire sequence just calls `A_ReFire` and the engine's internal state tracks which button was pressed.

### Flash sequences

- **`Flash:`** (optional) A special state that runs *simultaneously* in a separate sprite layer while the weapon-layer state (`Fire`, `Hold`, etc.) is executing. When a fire sequence calls `A_GunFlash`, the engine looks up the `Flash` state (or `AltFlash` if alternate fire is active) and runs it in the flash layer in parallel with the weapon layer. The flash state typically shows a muzzle-flash sprite and then stops; while it's running, the weapon layer continues its animation independently.
  - **Note on wiki inconsistency**: The ZDoom Wiki page's top-level code example shows `Flash: USGF A 6 A_FireBullets(...)`, calling a firing action in the flash state, which would cause a second volley. The same page's prose section correctly describes `Flash: USGF A 6 BRIGHT` with no action, letting the BRIGHT keyword render the flash at full brightness regardless of lighting. The correct pattern is the latter — the flash state should show the muzzle-flash sprite, optionally with BRIGHT, but should never call attack actions, as those run in the weapon layer already (called by the primary `Fire` sequence).
- **`AltFlash:`** (optional) Analog of `Flash` for alternate-fire sequences; looked up and run in parallel when `A_GunFlash` is called during an `AltFire` sequence with `bAltFire` set. On Zandronum a weapon with no `AltFlash` falls back to `Flash` there (`p_pspr.cpp:1270-1274`).

If no `Flash` state is defined, calling `A_GunFlash` has no visible effect (the flash layer simply remains empty). This is legal but unusual; most weapons define at least a simple flash sequence for visual feedback.

Outside a weapon's own states, Zandronum's `A_GunFlash` returns at once when the calling actor has no player (e.g. a monster, `p_pspr.cpp:1248-1251`). A `CustomInventory` chain runs with its owner as the caller (`g_shared/a_pickups.cpp:1829`), so for a player it plays the attack pose (unless `GFF_NOEXTCHANGE`) and, with no state argument, runs the ready weapon's `AltFlash`/`Flash` in the flash layer (`p_pspr.cpp:1252-1275`). On UZDoom, `CustomInventory`'s `A_GunFlash` is an empty deprecated stub (`stateprovider.zs:484`), so it does nothing.

## Example: a basic custom weapon

```text
actor ExampleCannon : Shotgun 9990
{
  Weapon.SelectionOrder 350
  Weapon.AmmoGive 8
  Weapon.AmmoUse 2
  Weapon.SlotNumber 3
  AttackSound "weapons/cannon"
  Inventory.PickupSound "misc/cannonpickup"
  Inventory.PickupMessage "You got the cannon!"
  States
  {
  Spawn:
    EXWP A -1
    Stop
  Ready:
    EXWP A 1 A_WeaponReady
    Loop
  Deselect:
    EXWP A 1 A_Lower
    Loop
  Select:
    EXWP A 1 A_Raise
    Loop
  Fire:
    EXWP B 3
    EXWP B 0 A_FireBullets(8, 8, 3, 15, "BulletPuff")
    EXWP B 5 A_GunFlash
    EXWP C 5
    EXWP D 5 A_CheckReload
    EXWP A 5 A_ReFire
    Goto Ready
  Flash:
    EXFL A 6 BRIGHT
    Stop
  }
}
```

This weapon:
- Inherits from `Shotgun` so it uses shells and most properties are pre-configured.
- Overrides `SelectionOrder` (350, preferred over the parent `Shotgun`'s 1300) and `AmmoGive` (8 shells per pickup), `AmmoUse` (2 shells per shot).
- Defines a simple pickup sprite in `Spawn:`.
- Uses standard `Ready`, `Select`, `Deselect` with `A_WeaponReady`, `A_Raise`, `A_Lower`.
- The `Fire` sequence calls `A_FireBullets` (which plays `AttackSound` automatically), then `A_GunFlash` to trigger the flash sequence, then checks ammo with `A_CheckReload`, and finally `A_ReFire` to loop or return to ready.
- The `Flash` state shows a bright muzzle-flash sprite and stops; it runs in the flash layer while `Fire` animates in the weapon layer.

## Hold sequences and alternate fire

To create a weapon with a hold-fire mode (e.g. semi-auto vs. full-auto):

```text
actor ExampleRifle : Pistol 9991
{
  States
  {
  Fire:
    EXRI A 2
    EXRI A 0 A_FireBullets(5, 5, 1, 10, "BulletPuff")
    EXRI B 2 A_GunFlash
    EXRI A 2 A_ReFire
    Goto Ready
  Hold:
    EXRI A 1
    EXRI A 0 A_FireBullets(5, 5, 1, 10, "BulletPuff")
    EXRI B 1 A_GunFlash
    EXRI A 1 A_ReFire
    Goto Ready
  Flash:
    EXFL A 3 BRIGHT
    Stop
  }
}
```

The difference: `Fire` spends 2 tics per shot (semi-auto pace), and when the fire button is held, `A_ReFire` jumps to `Hold`, which spends only 1 tic per shot (full-auto pace). If the fire button is released, `A_ReFire` does nothing to the state and the sequence falls through to `Goto Ready`. If no `Hold` state existed, `A_ReFire` would loop in `Fire` instead, repeating the semi-auto sequence continuously while held.

Alternate fire works the same way: define `AltFire` and optionally `AltHold`, and the engine automatically routes the alternate-fire button to them via internal `bAltFire` flag tracking and `GetAltAtkState()` logic (analogous to `GetAtkState()` for primary fire). Both sequences can `A_ReFire` at the end; the engine remembers which button was pressed and directs the fallback accordingly.

## Cross-references

- `state-machine.md` — covers state-line grammar (sprites, frames, duration, flags, actions), duration semantics, control-flow keywords (`Goto`, `Stop`, `Loop`, `Wait`), and reserved label names (this page names only the weapon-specific subset).
- `actor-definition-syntax.md` — covers actor-definition header syntax and inheritance basics.
- `actions/a_look.md` — `A_Look` semantics for monsters; not weapon-specific but illustrates action-function documentation pattern.
- The `actions/` directory — `A_WeaponReady`, `A_Raise`, `A_Lower`, `A_ReFire`, `A_GunFlash`, `A_FireBullets`, `A_CheckReload`, etc. when documented individually.

## Engine-family divergence

**`A_WeaponReady` and `A_GunFlash` class scope.** On Zandronum, both functions are defined on the `AInventory` class (`src/p_pspr.cpp:907` and `1234`), so they are callable from any inventory item's state sequence. On UZDoom, both are defined on the `Weapon` class only (`wadsrc/static/zscript/actors/inventory/weapons.zs:220` and `458`), and are not available to non-weapon actors; on `CustomInventory` they exist only as empty `deprecated` stubs (`stateprovider.zs:484` and `488`). This means Zandronum code that calls `A_WeaponReady` or `A_GunFlash` from a `CustomInventory` item's state sequence will not work in UZDoom — those calls simply have no effect.

**`A_CheckReload` on non-weapons.** The same split applies to `A_CheckReload`. Zandronum declares it on `AInventory` (`src/p_pspr.cpp:1104`, `wadsrc/static/actors/shared/inventory.txt:42`), so a `CustomInventory` state can reach the real body. UZDoom's real implementation is on `Weapon` only (`weapons.zs:477`); `CustomInventory` instead carries an empty `deprecated("2.3", "must be called from Weapon")` stub (`wadsrc/static/zscript/actors/inventory/stateprovider.zs:487`), so the call compiles with a deprecation warning and does nothing. See `../actions/a_checkreload.md` for the Zandronum-side non-weapon caveat this removes.

**`A_ReFire` `autoSwitch` parameter.** UZDoom's `A_ReFire` takes a second parameter, `A_ReFire(statelabel flash = null, bool autoSwitch = true)` (`stateprovider.zs:434`), forwarded to `Weapon.CheckAmmo` on the button-released path (`stateprovider.zs:459`). Passing `false` still runs the ammo check but skips the `PickNewWeapon` auto-switch, so nothing forces a weapon switch from `A_ReFire` itself. Zandronum's `A_ReFire` takes only the state argument (`inventory.txt:40`, `p_pspr.cpp:1054`) and always auto-switches, with no DECORATE-level way to suppress it. The default `true` matches Zandronum, so existing one-argument calls behave the same on both. See `../actions/a_refire.md`.

**`WRF_*` flag availability.** Both engines support `WRF_NOBOB`, `WRF_NOSWITCH`, `WRF_NOPRIMARY`, `WRF_NOSECONDARY`, `WRF_NOFIRE`, `WRF_ALLOWRELOAD`, `WRF_ALLOWZOOM`, and `WRF_DISABLESWITCH`. UZDoom adds four additional flags — `WRF_ALLOWUSER1`, `WRF_ALLOWUSER2`, `WRF_ALLOWUSER3`, `WRF_ALLOWUSER4` (defined in `wadsrc/static/zscript/constants.zs`) — which have no Zandronum equivalent. Zandronum's `A_WeaponReady` implementation explicitly acts on `WRF_AllowReload` and `WRF_AllowZoom` (calling `DoReadyWeaponToReload` and `DoReadyWeaponToZoom` respectively); UZDoom's does not have those branches, instead setting internal weapon-state flags via `GetButtonStateFlags()`.

**Sprite layers: nomenclature and constants.** Zandronum uses C++ enum names `ps_weapon` (layer 0) and `ps_flash` (layer 1) in its internal code. UZDoom's ZScript-based implementation uses `PSP_WEAPON` and `PSP_FLASH` constants (defined in `wadsrc/static/zscript/constants.zs`). DECORATE syntax is identical on both — a `Fire:` sequence and a `Flash:` sequence are looked up by label name, not by layer constant — so this divergence only matters when reading engine source, not when writing DECORATE.

**`A_Raise` and `A_Lower` speed argument.** `A_Raise` and `A_Lower` take an optional speed argument on UZDoom (defaulting to the same rate Zandronum uses, so existing DECORATE that calls them with no arguments behaves the same), letting a weapon override the raise/lower rate per call. Zandronum's implementations take no parameters at all — the per-call increment described above is fixed, with no DECORATE-visible way to change it. Passing one anyway (e.g. `A_Raise(12)`) is a fatal DECORATE parse error ("You cannot pass parameters ..."), since any `(` after a parameterless action is rejected (`thingdef/thingdef_states.cpp:432-437`).
