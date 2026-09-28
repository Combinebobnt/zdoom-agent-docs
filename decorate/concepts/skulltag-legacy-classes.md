# Skulltag legacy actor classes

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes — about a quarter of the classes only exist when `skulltag_actors.pk3` (built alongside the engine, never autoloaded) is loaded
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki "Classes:Skulltag" (retrieved 2026-09-22, https://zdoom.org/w/index.php?title=Classes:Skulltag&oldid=26902), every listed class name checked against the Zandronum source's shipped DECORATE (`wadsrc/static/decorate.txt` and its includes, `wadsrc_st/static/decorate.txt` and its includes), the base-file loading code (`src/d_main.cpp`, `AddAutoloadFiles` and the `BASEWAD` search), and hard-coded class lookups (`src/p_user.cpp:1685-1693`, `src/lastmanstanding.cpp:580-603`, `src/g_doom/a_doomweaps.cpp:932`); absence checked across the UZDoom source's `wadsrc/static` (DECORATE and ZScript) and `src/`. The checkout used is `master` HEAD reporting `3.3-alpha`; none of the cited actor files, `lastmanstanding.cpp`, or `a_doomweaps.cpp` differ from the 3.2.1 version-bump commit, and the cited `p_user.cpp`/`d_main.cpp` logic was re-read at that commit (line numbers above are the 3.3-alpha checkout's).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

The wiki's "Classes:Skulltag" list (294 names) is an old page, but its content is still live: every
class on it except three misspellings still exists in Zandronum. What the page doesn't say is that
Zandronum splits those classes across **two different pk3s**, and only one of them is ever loaded
automatically. None of them exist in UZDoom.

## The two pk3s

| pk3 | Built from | Loaded | Wiki classes found there |
|---|---|---|---|
| `zandronum.pk3` | `wadsrc/static` | always (`BASEWAD`, a fatal error if missing) | 211 |
| `skulltag_actors.pk3` | `wadsrc_st/static` | **never automatically**; must be passed like any add-on (`-file`, a launcher, or an autoload section) | 80 |

`AddAutoloadFiles` in `src/d_main.cpp` only picks up the `skins/`, `announcer/`, and `bots/`
subdirectories plus the ini's `*.Autoload` sections (and `AddPostloadFiles` the `postload/`
directory); nothing in `src/` loads `skulltag_actors.pk3` by name. The engine's own comment at
`src/p_user.cpp:1685` ("Since Railgun was moved out to skulltag_actors, its presence must be checked
for") confirms the split was deliberate.

Consequences of a missing `skulltag_actors.pk3`:

- A DECORATE class inheriting from, replacing, or `A_SpawnItem`-ing one of its classes (e.g.
  `actor MyImp : DarkImp`) fails to resolve, the same as any undefined class.
- A map thing using one of its editor numbers (e.g. `Abaddon`, `RegenerationRune` 5105) spawns
  nothing, since the doomednum is only registered by that pk3's DECORATE.
- **Instagib** (`p_user.cpp:1686-1688`) calls `I_Error("Tried to play instagib without a
  railgun!")` from `GiveDefaultInventory` in deathmatch/teamgame, because `Railgun` lives there.
- Last Man Standing's allowed-weapons filter (`lastmanstanding.cpp`) and `A_CheckRailReload`'s
  refire logic (`a_doomweaps.cpp:932`) look up `Minigun`/`GrenadeLauncher`/`Railgun` by name. A
  failed lookup returns null and just never matches, so these degrade quietly rather than error.

Sprites are a third, separate dependency. The engine source only provides a little Skulltag art:
46 rune-pickup sprite files in `wadsrc_st/static/sprites/`, plus TEXTURES-composited sprites
(`wadsrc_st/static/textures.txt`: `ARM3` red armor, `BON3`/`BON4` max bonuses, a few torches and
lamps; `wadsrc/static/textures.txt`: the flag sprites). Most of the rest (the new monsters and
weapons, the spheres, the skulls) isn't in either source tree; historically it shipped in
`skulltag_data.pk3`, which Zandronum stopped autoloading (`docs/zandronum-history.txt`:
"skulltag_data.pk3 should now be loaded explicitly like any other add-on").

## Base and native classes

The derived classes below are plain DECORATE and readable straight from `wadsrc/`/`wadsrc_st/`.
The engine-side behavior lives in their native bases, documented separately:

- [`RuneGiver`](../classes/runegiver.md): runes, `Rune.Type`.
- [`TeamItem` / `Flag` / `WhiteFlag` / `Skull` / `ReturnZone`](../families/team-items.md): CTF,
  one-flag CTF and Skulltag items, score pillars.
- [Invasion spots](../families/invasion-spots.md): `Base*`/`Custom*` monster, pickup and weapon
  spots.
- [Skulltag-lineage powers](../families/skulltag-powers.md): the rune and sphere `Power*`
  classes, `ReturningPowerupGiver`, `RandomPowerup`, spawn protection.
- [`MaxHealth`](../classes/maxhealth.md): base of `MaxHealthBonus`.
- [`FloatyIcon`](../classes/floatyicon.md): overhead player icons and medals, plus
  `SpringPadZone` and `PathNode`.

## Always available: `zandronum.pk3`

- **Invasion spawn spots**: every Doom/Heretic/Hexen `*Spot` class on the wiki's list whose
  target is a stock-game actor, plus the random spawners built from them: `doom/doomspawners.txt`,
  `heretic/hereticspawners.txt`, `hexen/hexenspawners.txt`. This includes the rune spots
  (`HasteRuneSpot` etc.) and Skulltag-powerup spots (`DoomsphereSpot`, `TurbosphereSpot`, ...)
  even though the runes themselves are in the opt-in pk3. Base classes:
  `CustomMonsterInvasionSpot`/`CustomPickupInvasionSpot` (`shared/sharedmisc.txt:187,200`, native).
- **Powerups** (`Skulltag/skulltagartifacts.txt`): `Turbosphere`, `TimeFreezeSphere`,
  `InvisibilitySphere`, `Doomsphere`, `Guardsphere`, `Terminator`, `PossessionStone`,
  `RandomPowerup` (native).
- **Health/armor**: `MaxHealthBonus` (`Skulltag/skulltaghealth.txt`), `MaxArmorBonus`
  (`Skulltag/skulltagarmor.txt`).
- **Team-game items** (`Skulltag/skulltagteamitems.txt`): `Flag` and `Skull` (native bases),
  `BlueFlag`, `RedFlag`, `WhiteFlag`, `BlueSkullST`, `RedSkullST`.
- **Score pillar / Heretic skulls** (`Skulltag/skulltagscorepillars.txt`): `HellScorePillar`,
  `hereticredskull`, `hereticblueskull`.
- **Sector zones** (`Skulltag/skulltagmisc.txt`): `ReturnZone` 5067, `SpringPadZone` 5068 (native).
- **`RuneGiver`** (`shared/inventory.txt:350`, native): the rune base class, see
  [`runegiver.md`](../classes/runegiver.md).

## Opt-in only: `skulltag_actors.pk3`

All paths under `wadsrc_st/static/actors/`.

- **Monsters and their projectiles** (`skulltagmonsters.txt`): `Abaddon`, `Belphegor`,
  `BloodDemon`, `Cacolantern`, `DarkImp`, `Hectebus`, `SuperShotgunGuy`; `AbaddonBall`,
  `BelphegorBall`, `CacolanternBall`, `DarkImpBall`, `HectShot`.
- **Weapons** (`skulltagweapons.txt`): `BFG10K` (+ `BFG10kShot`), `GrenadeLauncher`, `Minigun`,
  `Railgun`.
- **Runes** (`skulltagrunes.txt`): `DrainRune`, `HasteRune`, `HighJumpRune`, `ProsperityRune`,
  `RageRune`, `ReflectionRune`, `RegenerationRune`, `ResistanceRune`, `SpreadRune`, `StrengthRune`.
- **Armor**: `RedArmor` (`skulltagarmor.txt`).
- **Invasion spots for the classes above** (`skulltagspawners.txt`): `AbaddonSpot`,
  `BelphegorSpot`, `CacolanternSpot`, `DarkImpSpot`, `HectebusSpot`, `BFG10KSpot`,
  `GrenadeLauncherSpot`, `MinigunSpot`, `RailgunSpot`, `RedArmorSpot`, and the mixed random spots
  `AnyMonsterSpot`, `WeakMonsterSpot`, `PowerfulMonsterSpot`, `VeryPowerfulMonsterSpot`.
- **Decorations** (`skulltagdecorations.txt`): the tech/hell props (`BlueColumn`, `RedColumn`,
  `RedTechLamp`, `RedTechLamp2`, candlesticks, evil eyes, torches, columns,
  `FloatingBobbingSkull`), the gore set (`ImpalingSpike` through `ImpalingSpike11`, `ImpHead`,
  `MarineHelmetGibs`, `RevenantHand`), and `Impse`.
- **Statues** (`skulltagstatues.txt`): `ArchvileStatue`, `BaronStatue`, `CyberdemonStatue`,
  `DemonStatue`, `ImpStatue`, `MassmouthStatue`.
- **Other**: `DeadCyberdemon` (`skulltagdeadthings.txt`), `Hissy` (`skulltagmisc.txt`; faces the
  console player via `A_FaceConsolePlayer`).

## Wiki errors

Three names on the wiki's list don't exist under that spelling. The real class names are:

| Wiki says | Actual class | Where |
|---|---|---|
| `RengenerationRune` | `RegenerationRune` | `wadsrc_st/.../skulltagrunes.txt:201` |
| `CacolaternSpot` | `CacolanternSpot` | `wadsrc_st/.../skulltagspawners.txt:157` |
| `ReventantSpot` | `RevenantSpot` | `wadsrc/.../doom/doomspawners.txt:172` |

The list is also incomplete; treat it as a partial index, not an inventory. See the next section.

## Classes the wiki list omits

- **Rune powers** (`wadsrc_st/.../skulltagrunes.txt:11-49`, opt-in pk3): `RuneDoubleDamage`,
  `RuneDoubleFiringSpeed`, `RuneDrain`, `RuneSpread`, `RuneHalfDamage`, `RuneRegeneration`,
  `RuneProsperity`, `RuneReflection`, `RuneHighJump`, `RuneSpeed25`, each a thin subclass of the
  matching `Power*` class. These are what `Rune.Type` names: the property prepends `Rune` to its
  argument and looks the class up (`src/thingdef/thingdef_properties.cpp:2224-2238`), calling
  `I_Error("Unknown rune type ...")` if it isn't found. So **a mod's own `RuneGiver` subclass using
  `Rune.Type DoubleDamage` is a fatal startup error unless `skulltag_actors.pk3` is loaded**, even
  though `RuneGiver` itself is always available. To avoid the dependency, declare a mod-defined
  `Rune<Name>` class (any `Powerup` descendant) *before* the giver, or use `Powerup.Type` instead,
  which doesn't depend on declaration order. See [`runegiver.md`](../classes/runegiver.md).
- **Sphere powers** (`Skulltag/skulltagartifacts.txt`, always loaded): `PowerTurbo`,
  `PowerQuadDamage`, `PowerQuarterDamage`, `PowerTerminatorArtifact`, `PowerPossessionArtifact`,
  `PowerRespawnInvulnerable` (the spawn-protection power), and `ReturningPowerupGiver`, the base of
  `Terminator`/`PossessionStone`.
- **Native bases** (always loaded): `TeamItem` (base of `Flag`/`Skull`), `MaxHealth` (base of
  `MaxHealthBonus`).
- **`FloatyIcon`** (`Skulltag/skulltagmisc.txt:7`, native): the icon drawn above a player's head
  for chatting, console/menu open, carried team items, and awarded medals. Engine-spawned, not
  something a map places. See [`floatyicon.md`](../classes/floatyicon.md).
- **`PathNode`** (`Skulltag/skulltagmisc.txt:118`): a bot-pathfinding debug marker whose frames
  show open/closed-list state.
- **Team variants**: `GreenFlag`/`GoldFlag`/`GreenSkullST`/`GoldSkullST`
  (`skulltagteamitems.txt:108-233`).
- **Spawners and puffs**: `BloodDemonSpot` 5209 and `SuperShotgunGuySpot` 5213 (opt-in pk3; the wiki
  lists their monsters but not their spots), `RailgunPuff`, and a full set of Strife invasion
  spawners (`strife/strifespawners.txt`, always loaded).

## Engine-family divergence

None of these classes exist in UZDoom (checked at 5.1.0-pre @98b16b78fc), in DECORATE or ZScript. The only trace is two leftover
colormap entries in `src/common/utility/palette.cpp` commented as the Doomsphere and Guardsphere
tints, with no class behind them. A mod that depends on any Skulltag class has to define it itself
to run on UZDoom.
