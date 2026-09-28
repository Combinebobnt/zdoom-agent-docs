# `+WEAPON.ALLOW_WITH_RESPAWN_INVUL` (weapon flag)

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-22); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** engine source only. Zandronum: `src/g_shared/a_pickups.h:379`, `src/thingdef/thingdef_data.cpp:384`, `src/p_pspr.cpp:1206-1220` (`A_Raise`, the only consumer; the block is unchanged since 3.2.1), `src/g_shared/a_artifacts.cpp:1117-1147` (`APowerWeaponLevel2::InitEffect`), and the stock weapon definitions under `wadsrc/static/actors/`. UZDoom: `wadsrc/static/zscript/actors/inventory/weapons.zs:120`, `src/scripting/thingdef_data.cpp:507-545` (`FindFlag`), `src/scripting/zscript/zcc_compile_doom.cpp:150-205` (`CompileFlagDefs`), `:798` (strict lookup for `Default` blocks), `src/scripting/thingdef_properties.cpp` (`HandleDeprecatedFlags`/`CheckDeprecatedFlags`).
**Bucket:** Zandronum: `DEFINE_FLAG(WIF, ALLOW_WITH_RESPAWN_INVUL, AWeapon, WeaponFlags)` (`WIF_ALLOW_WITH_RESPAWN_INVUL` = `0x00020000`). UZDoom: a ZScript `flagdef Allow_With_Respawn_Invul: none, 0;` under "no-op flags", with no storage.

Zandronum only in effect. It marks a weapon the player may finish raising without losing
[`PowerRespawnInvulnerable`](../families/skulltag-powers.md#powerrespawninvulnerable), the
3-second spawn protection. UZDoom accepts the flag and ignores it.

## Zandronum

- **When protection ends.** At the end of `A_Raise`, once the weapon sprite reaches the top and
  the ready state is set, the server (or an offline game) checks the player's `ReadyWeapon`. If
  the player holds `PowerRespawnInvulnerable` and that weapon lacks this flag, the power is
  destroyed, and a server tells clients to take it too. Clients never run the check themselves.
- **Only a completed raise ends it.** Firing, holding or lowering a weapon never does, whether or
  not it has the flag. A player spawning with a flagged weapon can fire it freely for the full
  3 seconds.
- **The spawn raise counts.** The weapon a player spawns with also goes through `A_Raise`. A mod
  whose starting weapon lacks the flag ends spawn protection a few tics after every spawn, as soon
  as that first raise finishes. Set the flag on any replacement starting weapon if protection
  should survive spawning.
- **A Select state without `A_Raise`** never reaches the check, so switching to such a weapon
  doesn't end protection even without the flag.
- **Stock weapons with the flag:** Doom `Fist`, `Pistol`, `Chainsaw` (`doomweapons.txt:27,65,116`);
  Heretic `Staff`, `GoldWand`, `Gauntlets` (`hereticweaps.txt:17,119,411`); Hexen `FWeapFist`,
  `CWeapMace`, `MWeapWand`; Strife `PunchDagger` (`strifeweapons.txt:51`).
- **Heretic's powered versions clear it.** `StaffPowered`, `GoldWandPowered` and
  `GauntletsPowered` inherit from their base weapon and then set `-WEAPON.ALLOW_WITH_RESPAWN_INVUL`.
  Using the Tome of Power doesn't itself end protection: `APowerWeaponLevel2::InitEffect` swaps
  `ReadyWeapon` to the powered sister and sets its ready state directly, with no `A_Raise`. The
  cleared flag matters only when the powered weapon finishes a raise of its own, for example when
  switching weapons while the Tome is active (inferred from the code, not tested).
- Both spellings work: `+ALLOW_WITH_RESPAWN_INVUL` and `+WEAPON.ALLOW_WITH_RESPAWN_INVUL` (stock
  Heretic uses both).

## UZDoom

The flag parses without error. DECORATE accepts both spellings. A ZScript `Default` block looks
flags up in strict mode, which skips the bare alias on a prefixed class like `Weapon`, so there
only `+Weapon.Allow_With_Respawn_Invul` works. With no storage field and bit 0, it resolves to the `DEPF_UNUSED` deprecated-flag slot:
setting or clearing it does nothing, and checking it (for example via ACS `CheckFlag`) always
returns false.

UZDoom's own respawn protection is a plain `PowerInvulnerable` from `PlayerPawn.OnRespawn`, which
no weapon raise cancels. See the "Respawn protection" paragraph of
[Skulltag powers](../families/skulltag-powers.md#engine-family-divergence) for the opposite
dmflag meanings on the two engines.
