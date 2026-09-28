# `A_FireRailgun` (stock railgun weapon attack)

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-22); Zandronum 3.3-alpha @bdd0f7beb (2026-09-22)
**Provenance:** engine source only. Zandronum, read at upstream `master` @bdd0f7beb: `src/g_doom/a_doomweaps.cpp:846-916` (`FireRailgun` and the three action wrappers), `src/p_map.cpp` (`P_RailAttackWithPossibleSpread`, and `P_RailAttack`'s null-puff fallback), `src/unlagged.cpp:368-382` (`UNLAGGED_DrawRailClientside`), `src/g_shared/a_weapons.cpp:713-750` (`AWeapon::DepleteAmmo`), `src/d_dehacked.cpp:188-202`, `wadsrc/static/actors/shared/inventory.txt:33-35`, `wadsrc_st/static/actors/skulltagweapons.txt:59-116`. The action has been in Zandronum since the Skulltag import, an ancestor of the 3.2.1 commit 28f736fb3. UZDoom: `wadsrc/static/zscript/actors/doom/doomweapons.zs:36-82`, `src/gamedata/d_dehacked.cpp:320`.
**Bucket:** Zandronum: `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_FireRailgun)` (plus plain `A_FireRailgunLeft`/`A_FireRailgunRight`) in `src/g_doom/a_doomweaps.cpp`, all wrapping one static `FireRailgun`; declared on `Inventory`. UZDoom: ZScript `action` methods in an `extend class StateProvider` block.

Fires a fixed-damage player rail through the weapon's own ammo and flash handling. Both engines
have it, but the damage, the parameters and the colour and network behavior all differ. For the
fully configurable attack use [A_RailAttack](a_railattack.md).

## Signatures

Zandronum:

```text
A_FireRailgun(class<Actor> puffType = "None")
A_FireRailgunLeft()
A_FireRailgunRight()
```

UZDoom takes a second parameter, `int offset_xy = 0`, and defaults `puffType` to `BulletPuff`.
`A_FireRailgunLeft`/`Right` are the same call with a horizontal offset of -10/+10 on both
engines. A Zandronum DECORATE call with a second argument doesn't compile, so
`A_FireRailgun` or `A_FireRailgun("SomePuff")` are the only portable forms.

## Zandronum behavior

In order:

1. Returns if the caller has no player.
2. If the player has a ready weapon, it depletes ammo with the enough-ammo check on, and returns
   without firing if there isn't enough. The weapon's own `AmmoUse` applies; the hardcoded `1`
   passed along only matters for DeHackEd-ammo weapons. There's no check that the calling state
   belongs to the weapon. It then sets the weapon's `Flash` state, picking `Flash` or the state
   after it at random.
3. **Clients stop here**, having predicted the ammo and flash, unless the rail is theirs to draw
   under unlagged: unlagged not disabled by the `ZADF_NOUNLAGGED` dmflag, the shooter's own
   unlagged client setting on, and the shooter being this client's own player. In that case the
   client draws its own rail locally and the server still does the authoritative trace.
4. **Damage is fixed by game mode:** 200 in single player and cooperative; in deathmatch or any
   team game, 75, or 1000 when the `instagib` setting is on. Either way, with `instagib` on
   `P_RailAttack` then overrides every rail hit to 999 in any game mode (`src/p_map.cpp:4956-4958`),
   so the effective instagib damage is 999, co-op included.
5. The rail fires through `P_RailAttackWithPossibleSpread` with default colours and no flags.
   A null puff (the `"None"` default) becomes `BulletPuff` inside the trace, so the effective
   default matches UZDoom's.
6. Bots are told a railgun was fired.

Because the colours are always passed as 0, the player-colour override described in
[A_RailAttack](a_railattack.md#engine-family-divergence-color-defaults-and-no-playerteam-color-override)
always applies here: the rail uses the shooter's configured railgun colour, or their team's in a
team game. The same helper also fires two extra rails 15 degrees either side while the player
holds the spread rune, and resets the player's consecutive-railgun-hit streak (used for
railgun medals) when the shot hit no player.

The stock Skulltag `RailGun` calls `A_FireRailgun("RailgunPuff")`. That puff has
`+PIERCEARMOR` and `DamageType Railgun`, so the stock weapon ignores armor; a bare
`A_FireRailgun()` does not. It pairs the attack with
[A_CheckRailReload](a_checkrailreload.md). As a DeHackEd codepointer, `A_FireRailgun` defaults
to 1 ammo per attack.

## Engine-family divergence

UZDoom's version, read from its ZScript:

- **Damage** is 100 in deathmatch and 150 otherwise. Team games and `instagib` play no part.
- **Ammo** is depleted only when the calling state is a weapon sprite state of the ready weapon
  itself. Called from anywhere else it fires without spending ammo or setting a flash. The same
  guard the rest of UZDoom's weapon actions use.
- **The attack** is a plain `A_RailAttack` call with its own ammo use off, so the rail gets
  `A_RailAttack`'s UZDoom colour defaults: random grey, with no per-player or per-team colour.
- **No network split.** No client early return, no unlagged path, no spread-rune rails, no
  railgun medal bookkeeping, no bot events.
- `offset_xy` is exposed as a parameter (see Signatures).
- UZDoom ships no railgun weapon of its own using this action; it exists for DeHackEd patches
  and custom weapons.

## Example

```decorate
ACTOR SimpleRailRifle : Weapon
{
  Weapon.AmmoType "Cell"
  Weapon.AmmoUse 10
  Weapon.AmmoGive 40
  States
  {
  Ready:
    RLGG A 1 A_WeaponReady
    Loop
  Deselect:
    RLGG A 1 A_Lower
    Loop
  Select:
    RLGG A 1 A_Raise
    Loop
  Fire:
    RLGG E 12 A_FireRailgun
    RLGG A 18 A_ReFire
    Goto Ready
  Flash:
    TNT1 A 5 Bright A_Light1
    TNT1 A 5 Bright A_Light2
    Goto LightDone
  Spawn:
    RAIL A -1
    Stop
  }
}
```
