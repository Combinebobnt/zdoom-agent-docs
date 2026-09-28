# Skulltag-lineage native powerups

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes — file-level claim for `PowerDrain`, `PowerRegeneration`, `PowerHighJump`, `PowerDoubleFiringSpeed` and `PowerReflection`, which exist on both engines with different mechanics; `PowerSpread`, `PowerProsperity`, `PowerRespawnInvulnerable`, `PowerTerminatorArtifact`, `PowerPossessionArtifact`, `ReturningPowerupGiver`, `RandomPowerup` and the three DECORATE-only sphere powers are Zandronum-only (UZDoom=no), see "Engine-family divergence" below
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-22); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** engine source only. Zandronum 3.3-alpha @bdd0f7beb (line numbers are HEAD's): `wadsrc/static/actors/shared/inventory.txt:137-165,308-347`, `wadsrc/static/actors/Skulltag/skulltagartifacts.txt:1-295`, `wadsrc/static/actors/doom/doomartifacts.txt`, `doomhealth.txt`, `doomweapons.txt:27,65,116`, `src/g_shared/a_artifacts.h:218-341`, `src/g_shared/a_artifacts.cpp:55-100,120-127,271-300,380-500,1718-1860,1967-2442`, `src/g_doom/a_doomartifacts.cpp:20-209`, `src/d_player.h:242-266,638`, `src/p_interaction.cpp:419-468,584-613,791,1152-1379,1498-1534,1654-1684`, `src/p_pspr.cpp:1170-1220,1424-1459`, `src/p_user.cpp:2181-2330,2425-2439,3170-3208,3903-3915`, `src/p_mobj.cpp:5388,5683-5704`, `src/p_map.cpp:5074-5127,6180-6221`, `src/p_local.h:164-187`, `src/thingdef/thingdef_codeptr.cpp:1554-1640,1739-1790,1834,1982,2106`, `src/thingdef/thingdef_properties.cpp:2131-2170`, `src/g_shared/a_pickups.cpp:217-300,1882-1893,1979-2030`, `src/g_shared/a_armor.cpp:248-300,350-390`, `src/p_lnspec.cpp:1154-1175`, `src/g_game.cpp:444,470,4313-4413`, `src/gamemode.cpp:1050-1107`, `src/possession.cpp:481,712`, `src/doomdef.h:293`, `src/d_main.cpp:559`. UZDoom: `wadsrc/static/zscript/actors/inventory/powerups.zs:47-60,84-160,1817-1913`, `wadsrc/static/zscript/actors/player/player.zs:288-304,1485-1503,2820-2836`, `wadsrc/static/zscript/constants.zs:1222-1226`, `src/playsim/p_interaction.cpp:1259-1293,1464-1492`, `src/playsim/p_pspr.cpp:217,342,346`, `src/playsim/p_lnspec.cpp:2925-2940`, `src/doomdef.h:144`, `src/d_main.cpp:749`; absence of the Zandronum-only classes checked by grepping UZDoom's `src/` and `wadsrc/`.
**Bucket:** Zandronum native C++ classes: `APowerDrain`, `APowerRegeneration`, `APowerHighJump`, `APowerDoubleFiringSpeed` (`src/g_shared/a_artifacts.h:218,226,233,241`), `APowerPossessionArtifact`, `APowerTerminatorArtifact` (`:276,285`), `APowerRespawnInvulnerable : APowerInvulnerable` (`:295`), `APowerSpread`, `APowerProsperity`, `APowerReflection` (`:321,329,337`), all others `: APowerup`, implemented in `src/g_shared/a_artifacts.cpp`; `AReturningPowerupGiver : APowerupGiver` is declared and defined inside `a_artifacts.cpp:1975` (no header); `ARandomPowerup : AInventory` in `src/g_doom/a_doomartifacts.cpp:34` with its `A_RandomPowerupFrame` action on `AActor` (`:66`). UZDoom: plain ZScript classes `PowerDrain`, `PowerRegeneration`, `PowerHighJump`, `PowerDoubleFiringSpeed`, `PowerReflection` (`wadsrc/static/zscript/actors/inventory/powerups.zs:1817,1832,1859,1873,1902`), effects read by name from C++ (`src/playsim/p_interaction.cpp`) and ZScript (`player.zs`).
**Family rationale:** Shared implementation. On Zandronum every member except `RandomPowerup`/`ReturningPowerupGiver` is a thin `InitEffect`/`EndEffect` pair that toggles one `player->cheats` or `cheats2` bit, and the real behavior lives at scattered effect sites that test that bit; the stacking and removal caveats below are identical across all of them.

Skulltag added these powers for its runes, spheres and game modes; Zandronum kept them as native classes. For the generic `Powerup` lifecycle (duration, re-pickup, blink, destruction on death/level change) see [`Powerup`](../classes/powerup.md). Runes wrap most of these classes through `Rune<Name>` subclasses; see [`RuneGiver`](../classes/runegiver.md). For the damage-reduction sphere, see [`PowerProtection`](../classes/powerprotection.md).

## Shared mechanics (Zandronum)

- **Player owners only.** Every cheat-bit member returns early in `InitEffect` when `Owner->player` is null, so giving one to a monster does nothing (the exception is `PowerPossessionArtifact`, which does not check; see its section).
- **The bit is cleared unconditionally on expiry.** `EndEffect` does `cheats &= ~CF_<X>` with no re-scan of inventory. Two instances of *different* classes that set the same bit (for example a permanent `RuneHighJump` plus a timed `PowerHighJump` from a giver: `HandlePickup` only merges identical classes, so both are held) lose the effect as soon as the first one ends, even though the other is still in inventory. Traced from the code; not play-tested. UZDoom's surviving members scan inventory at the effect site instead, so they don't have this problem.
- **Default durations are in the DECORATE definitions**: negative `Powerup.Duration` is seconds (`thingdef_properties.cpp:2150`, `-i * TICRATE`). `PowerHighJump`, `PowerDoubleFiringSpeed`, `PowerRespawnInvulnerable` declare none, and `PowerTerminatorArtifact`/`PowerPossessionArtifact` declare `0`. On Zandronum `EffectTics == 0` never times out (`APowerup::Tick`, `a_artifacts.cpp:127`), so these last until death or a level change unless a giver supplies a duration.
- The bits live in `src/d_player.h:242-246` (`CF_DRAIN`, `CF_HIGHJUMP`, `CF_REFLECTION`, `CF_PROSPERITY`, `CF_DOUBLEFIRINGSPEED`) and `:264-266` (`CF2_POSSESSIONARTIFACT`, `CF2_TERMINATORARTIFACT`, `CF2_SPREAD`).

## `PowerDrain`

Default `Powerup.Duration -60` (60 s). Sets `CF_DRAIN`. Effect site: `P_DamageMobj` (`p_interaction.cpp:1665-1679`), after armor absorption has already reduced `damage`. When a player with the bit damages anything that isn't themselves and lacks `+DONTDRAIN`, they heal `MIN(targetHealthBeforeHit, damage) / 2` via `P_GiveBody`. So it is half of the damage that actually reached health, capped by what the target had left (no overkill credit), integer-divided (a 1-point hit drains 0). Healing respects the normal max health, or the Prosperity cap (see `PowerProsperity`). Plays `misc/i_pkup` on a successful heal. `Powerup.Strength` is ignored. Server-side only; the server sends the new health with `SERVERCOMMANDS_SetPlayerHealth`.

## `PowerRegeneration`

Default `Powerup.Duration -120`, `Powerup.Strength 5`. `DoEffect` (`a_artifacts.cpp:1766`) calls `P_GiveBody(Owner, Strength/FRACUNIT)` whenever `level.time & 31 == 0` and the owner is alive: 5 HP every 32 tics (about 0.91 s) by default. `Strength` is fixed-point, so a fractional value truncates (`2.5` heals 2). Healing uses `P_GiveBody`'s default cap, so it stops at max health (plus `MaxHealthBonus`), or at the Prosperity cap. Plays `*regenerate` on a successful heal. Server-side (`NETWORK_InClientMode()` returns early); health is pushed to clients.

## `PowerHighJump`

No default duration (indefinite, see above). Sets `CF_HIGHJUMP`. Two effect sites in `p_user.cpp`:

- `APlayerPawn::CalcJumpVelz` (`:2425`): jump velocity `JumpZ` is doubled. A spring-pad floor (`PLANEF_SPRINGPAD`) then halves it, so the two cancel.
- `P_MovePlayer` (`:3197`): the post-jump delay is doubled. That only matters under the `ZACOMPATF_SKULLTAG_JUMPING` compat flag, where the delay goes from 18 to 36 tics. In the default path the delay is the sentinel `-1` stored through a `ULONG`; doubling it gives `-2`. The counter then decrements each tic and resets once it is below `-18` on landing (`:3910`), so the wait is at most one tic *shorter* (17 instead of 18), the opposite of the intent, and in practice no change since a normal jump is airborne longer than that (inferred from the arithmetic).

`Powerup.Strength` is ignored; the factor is a hard-coded 2.

## `PowerDoubleFiringSpeed`

No default duration (indefinite). Sets `CF_DOUBLEFIRINGSPEED`. Effect site: `P_MovePsprites` (`p_pspr.cpp:1453`). Each tic every active psprite layer (weapon and flash) decrements its tic count, then decrements once more if that left it nonzero. A state of `n` tics therefore lasts `ceil(n/2)`; 1-tic states gain nothing, 0-tic states are unaffected. It applies to every weapon state (ready, raise, lower, fire), not only attacks.

## `PowerReflection`

Default `Powerup.Duration -60`. Sets `CF_REFLECTION`. Effect site: `P_DamageMobj` (`p_interaction.cpp:1360-1375`). When a player holding it takes damage from a `source` other than themselves, and the damage type isn't `Reflection`, the engine calls `P_DamageMobj(source, NULL, target, (damage*3)/4, "Reflection")`.

- **The amount is 75%, not 50%.** The source comment says 50%; the code multiplies by 3/4.
- The damage it scales is taken after the attacker's active and the victim's passive `ModifyDamage` modifiers and `TakeSpecialDamage`, but *before* the victim's armor absorbs anything, so armor doesn't shrink what gets reflected.
- The reflected hit has no inflictor (no thrust) and credits the reflector as source. The `Reflection` damage type stops two reflecting players from ping-ponging.
- An invulnerable victim returns from `P_DamageMobj` earlier (`:1212`), so Invulnerability plus Reflection reflects nothing (inferred from ordering).
- Server-side only. `DamageFactor` and `Powerup.Strength` on the class are ignored.

## `PowerSpread`

Default `Powerup.Duration -30`. Sets `CF2_SPREAD`. Every honoring attack fires two extra copies at `ANGLE_45/3` = ±15° horizontally, so three attacks total for one ammo use. Only when the attacker is a player. The extra attacks run server-side like the main one; clients only see the results (the hitscan-decal and predicted-puff paths in `A_FireBullets` are the only client-side exception).

- **Generic DECORATE actions that honor it:** `A_FireBullets` (`thingdef_codeptr.cpp:1633`, the whole bullet set is repeated per copy), `A_FireCustomMissile` (`:1783`), `A_RailAttack` and `A_CustomRailgun` (via `P_RailAttackWithPossibleSpread`, `p_map.cpp:5074`).
- **`A_CustomPunch` does not** (`:1834`, no spread check).
- Stock hard-coded weapon actions that honor it: `A_Punch`, `A_FirePistol`, `A_Saw`, `A_FireShotgun`, `A_FireShotgun2`, `A_FireCGun`, `A_FireBFG` and the plasma/rocket missiles (via `P_SpawnPlayerMissileWithPossibleSpread`, `p_local.h:164,177`, extra missiles spawn without a sound), plus most Heretic and Hexen weapon actions.

## `PowerProsperity`

Default `Powerup.Duration -120`. Sets `CF_PROSPERITY`. It *replaces* the owner's health and armor caps with fixed values instead of adding to them:

| Site | Normal cap | With Prosperity |
|---|---|---|
| `P_GiveBody` when called with no explicit max (`a_pickups.cpp:242`) | max health + stamina + `MaxHealthBonus` | `deh.MaxSoulsphere + 50` (250 by default) |
| `AMaxHealth::TryPickup` (`:2007`) | item `Health`, or max health + bonuses | 250 |
| `ABasicArmorPickup::Use` (`a_armor.cpp:264`) | item's `SaveAmount` + `BonusCount` | `deh.BlueAC * 100 + 50` (250 by default) |
| `ABasicArmorBonus::Use` (`:379`) | `MaxSaveAmount` + `BonusCount` | 250 |
| `HealThing` special with max 0 (`p_lnspec.cpp:1168`) | spawn health + `MaxHealthBonus` | 250 |

Caveats:

- **Only `Health` items with `Inventory.MaxAmount 0` are lifted.** `AHealth::TryPickup` passes the item's `MaxAmount` to `P_GiveBody`, and the prosperity branch only runs when that is `<= 0`. `Stimpack`/`Medikit` inherit `Health`'s `MaxAmount 0` and heal up to 250; `Soulsphere`, `HealthBonus` and `MegasphereHealth` declare `MaxAmount 200` and stay capped at 200.
- Because `PowerDrain` and `PowerRegeneration` heal through `P_GiveBody` with no explicit max, they also heal up to 250 while Prosperity is held.
- `BasicArmorPickup` adds to existing armor (`Amount += SaveAmount`, a Zandronum change) then clamps, so with Prosperity successive armor pickups stack to 250.
- The Doom status bar also shows the raised maximums.

## `PowerTerminatorArtifact`

`Powerup.Duration 0` (indefinite). Given by the `Terminator` sphere (`skulltagartifacts.txt:193`, doomednum `-1`). On `InitEffect` it sets `CF2_TERMINATORARTIFACT` and, server-side, gives the owner a `Megasphere`. Its `ModifyDamage` (`a_artifacts.cpp:2144`) multiplies all outgoing (active) damage by 4 for every damage type. No `DamageFactor` lookup and no active sound, unlike `PowerDamage`. It passes the multiplied value down the inventory chain, and `PowerDamage` does the same, so holding a Doomsphere too gives x16 (inferred from the chain code). In any game mode:

- A kill of the carrier is worth `sv_terminatorfragaward` frags (default 10, clamped to a minimum of 1) instead of 1, and a carrier suicide, environment kill, or teamkill costs the same (`p_interaction.cpp:592,607,609,791`). Master after 3.2.1 (not in 3.2.1) replaced the hard-coded 10 with this cvar (`f3a9eb474`, "Port sv_terminatorfragaward from Q-Zandronum"); the default still matches 3.2.1's fixed value, so the frag counts above hold on 3.2.1 too.

In Terminator mode specifically, the carrier's death (or leaving) goes through `APlayerPawn::DropImportantItems` (`p_user.cpp:2296-2308`), which drops a fresh `Terminator` sphere with `P_DropItem` and tells clients to remove the power. The dropped sphere is a `ReturningPowerupGiver`.

## `PowerPossessionArtifact`

`Powerup.Duration 0` (indefinite). Given by `PossessionStone` (`skulltagartifacts.txt:232`, doomednum `-1`). Sets `CF2_POSSESSIONARTIFACT`. In (team) possession mode, server-side, it starts the hold timer with `POSSESSION_ArtifactPickedUp(player, sv_possessionholdtime * TICRATE)` (`sv_possessionholdtime` defaults to 30, `possession.cpp:712`). `DoEffect` clears the weapon psprite every tic, so the carrier can't fire in any mode. The `weapnext`/`weapprev` console commands are also refused for the carrier (`g_game.cpp:444,470`). On death or leaving in possession mode, `DropImportantItems` (`p_user.cpp:2312-2328`) drops a new `PossessionStone` and notifies the possession module.

**Crash hazard:** unlike every other member, `InitEffect` (`a_artifacts.cpp:2021`) writes `Owner->player->cheats2` without checking `Owner->player`. Giving this power to a non-player actor dereferences a null pointer. Inferred from the code, not tested.

## `ReturningPowerupGiver`

Native `PowerupGiver` subclass (`skulltagartifacts.txt:183`), the base of `Terminator` and `PossessionStone`. "Returning" means relocation on a timer, not a return to the item's own spawn spot:

- `BeginPlay` sets a countdown of `sv_artifactreturntime * TICRATE` (cvar default 30 seconds, `a_artifacts.cpp:1973`). `Tick` counts it down server-side, paused during a game-mode result sequence. The timer runs for every instance, whether engine-spawned at map start or dropped by a dying carrier, and is not reset by anything but a new spawn. A cvar value of `0` or less disables it.
- When it hits 0 the item is destroyed and, if it `IsKindOf("Terminator")` or `"PossessionStone"` (looked up by name), `GAME_SpawnTerminatorArtifact`/`GAME_SpawnPossessionArtifact` (`g_game.cpp:4372,4395`) spawns a new one.
- The new one goes to a random `TerminatorStart`/`PossessionStart` if the map has any, else a random deathmatch start, else nowhere. `GAME_SelectRandomSpotForArtifact` (`:4313`) tries up to `2 * spots` random spots for a clear position, then falls back to any spot. It refuses to spawn if someone already carries the artifact in the current mode. The spawn uses `ALLOW_REPLACE`, so a mod's `replaces Terminator` class is what appears.
- The same respawn happens when a Terminator/Possession giver is crushed by a moving sector in those modes (`P_DoCrunch`, `p_map.cpp:6208-6218`, which checks `PowerupType` instead of the class name).
- A mod subclass of `ReturningPowerupGiver` that doesn't descend from `Terminator` or `PossessionStone` just disappears when its timer runs out.
- Both game modes spawn the first artifact from `GAMEMODE_SpawnSpecialGamemodeThings` (`gamemode.cpp:1096`); the classes are not map-placeable.

## `RandomPowerup`

`Inventory` subclass, doomednum 5039, `Game Doom` only (`skulltagartifacts.txt:260`). Despite the name, it isn't random at pickup time:

- Its Spawn state cycles eight 6-tic frames (Megasphere, Soulsphere, Guardsphere, Blursphere, TimeFreezeSphere, InvisibilitySphere, Doomsphere, Turbosphere art). Each frame calls `A_RandomPowerupFrame`, which records the frame index or, if that index is not allowed, jumps straight to the next frame.
- On touch (`+INVENTORY.AUTOACTIVATE`), `Use` spawns the class for the frame currently showing and tries to give it to the toucher. If that fails, the `RandomPowerup` pickup fails and it stays in the world.
- The map thing's first argument is a bitmask of allowed frames: 1 Megasphere, 2 Soulsphere, 4 Guardsphere, 8 Blursphere, 16 TimeFreezeSphere, 32 InvisibilitySphere, 64 Doomsphere, 128 Turbosphere; 0 means all. TimeFreezeSphere (16) is always disallowed outside single player.
- The frame-to-item mapping is by state offset from the Spawn state and hard-coded in C++, so a subclass that reorders or changes its Spawn states changes which item each frame gives.
- A mask with no allowed frame (for example `16` in multiplayer) makes `A_RandomPowerupFrame` jump from frame to frame without ever stopping. This is inferred from the code (unbounded recursion through `SetState`), not tested.
- Netcode: `Use` returns false on clients; the server sends the given item and the pickup message.

## `PowerRespawnInvulnerable`

Subclass of `PowerInvulnerable` (`skulltagartifacts.txt:293`), Zandronum's spawn protection.

- **Who gets it:** `P_SpawnPlayer` (`p_mobj.cpp:5686-5704`) gives it server-side on respawn or entry when the `DF2_NO_RESPAWN_INVUL` dmflag (`sv_norespawninvul`) is off, the game is deathmatch, a team game, or `alwaysapplydmflags` is on, and the player isn't a spectator. So protection is on by default in those modes.
- **Duration:** `InitEffect` forces `EffectTics = 3*TICRATE` (105 tics) and `BlendColor = 0`, and sets `IF_UNDROPPABLE`, overriding any `Powerup.Duration` or giver values.
- **Ended early by raising a weapon:** in `A_Raise` (`p_pspr.cpp:1206-1220`), once a weapon finishes raising, the power is destroyed server-side unless the weapon has [`+WEAPON.ALLOW_WITH_RESPAWN_INVUL`](../notes/allow_with_respawn_invul.md). In Doom that flag is on `Fist`, `Pistol` and `Chainsaw` (`doomweapons.txt:27,65,116`), so switching to anything else ends protection.
- **Visual:** chosen by the client-side cvar `cl_respawninvuleffect` (`a_artifacts.cpp:2160`, default 1). `0` = none, `1` = translucent with alpha randomly 25/50/75% each tic, `2` = the `FX_RESPAWNINVUL` particle effect.
- On expiry it restores the default alpha. It also re-applies `MF2_INVULNERABLE` if another `PowerInvulnerable` is still held, so it doesn't cancel a real invulnerability sphere. The base `PowerInvulnerable` has two matching special cases: it keeps the respawn effect when stacked (`:396`) and doesn't clear colormaps when this subclass ends (`:497`).
- Master after 3.2.1 (not in 3.2.1) changes two details: the server skips the visual effect (`39e4da5ca`), and expiry restores the default render style directly instead of guessing normal-vs-translucent (`c420c57f3`).

## DECORATE-only Skulltag sphere powers (Zandronum)

Defined in `skulltagartifacts.txt` with no native class of their own:

- `PowerTurbo` (`:8`): `PowerSpeed` with a HUD icon; the `Turbosphere` gives it for 1050 tics (30 s).
- `PowerQuadDamage` (`:101`): `PowerDamage` with `DamageFactor "normal", 4`; given by the `Doomsphere`.
- `PowerQuarterDamage` (`:138`): [`PowerProtection`](../classes/powerprotection.md) with `DamageFactor "normal", 0.25`; given by the `Guardsphere`.

## Engine-family divergence

**Absent on UZDoom.** `PowerSpread`, `PowerProsperity`, `PowerTerminatorArtifact`, `PowerPossessionArtifact`, `PowerRespawnInvulnerable`, `ReturningPowerupGiver`, `RandomPowerup`, `PowerTurbo`, `PowerQuadDamage` and `PowerQuarterDamage` don't exist in UZDoom's DECORATE, ZScript or C++. A mod that uses them has to define its own replacements to run there. UZDoom's `constants.zs` still defines `CF_DRAIN`, `CF_HIGHJUMP`, `CF_REFLECTION`, `CF_PROSPERITY` and `CF_DOUBLEFIRINGSPEED`, but as `0`, so code testing those bits compiles and never matches.

**Present on both, different mechanics.** UZDoom doesn't use cheat bits. Each effect site scans the player's inventory for the class (subclasses included) and, where several are held, uses the strongest. That removes the "first expiry clears the bit" caveat above.

| Class | Zandronum 3.2.1 | UZDoom 5.0.0-pre |
|---|---|---|
| `PowerDrain` | fixed 50% of `MIN(oldHealth, damage)`, sound `misc/i_pkup`, server-side | `Powerup.Strength` fraction (default 0.5) of damage, not capped by the target's remaining health; an actor `OnDrain` virtual can change the amount; sound `*drainhealth` |
| `PowerRegeneration` | `Strength` HP every 32 tics | same period and default (`Level.maptime & 31`, `Strength 5`) |
| `PowerHighJump` | fixed x2 velocity, doubled delay under Skulltag jumping compat, no default duration | `Powerup.Strength` multiplier (default 2), no delay change, no default duration |
| `PowerDoubleFiringSpeed` | every psprite layer, no default duration | only layers with the `PSPF_POWDOUBLE` flag (on by default for weapon layers); default `Powerup.Duration -40`; also a `SetPlayerProperty` slot, which Zandronum's table lacks |
| `PowerReflection` | fixed 75%, pre-armor, no `damage > 0` check | `DamageFactor 0.5` by default, so 50%, scaled per damage type through the item's damage factors, plus a `Powerup.Strength` "always reflect" fraction; `ReflectType` property keeps the original damage type; requires `damage > 0` |

**Zero-duration trap.** Neither engine gives `PowerHighJump` a default duration, and Zandronum gives `PowerDoubleFiringSpeed` none either. On Zandronum `EffectTics == 0` means "never expires". On UZDoom the base `Powerup.Tick` destroys a powerup whose `EffectTics` is 0 (see [`Powerup`](../classes/powerup.md)), and `PowerupGiver.Use` only overrides the duration when its own is nonzero. So a bare `A_GiveInventory("PowerHighJump")` lasts until death on Zandronum and is gone after one tic on UZDoom. Give it through a `PowerupGiver` or subclass with an explicit `Powerup.Duration` to behave the same on both.

**Respawn protection.** UZDoom has no `PowerRespawnInvulnerable`. `PlayerPawn.OnRespawn` gives a plain `PowerInvulnerable` for 3 s with no weapon-raise cancel. It is **opt-in** through `sv_respawnprotect` (dmflags2 `DF2_YES_RESPAWN_INVUL`), deathmatch or `alwaysapplydmflags` only. Zandronum's is **opt-out** through `sv_norespawninvul` (`DF2_NO_RESPAWN_INVUL`) and also covers team games. Both flags are dmflags2 bit `1 << 10` with opposite meanings, so the same numeric `dmflags2` value turns protection off on Zandronum and on on UZDoom (see [dmflags](../../console/concepts/dmflags.md)).
