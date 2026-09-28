# Skill block definition

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** ZDoom Wiki `MAPINFO/Skill_definition` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=MAPINFO%2FSkill_definition&oldid=54710) + verified against Zandronum source (`src/g_skill.cpp:56-314`; corrections from `src/p_enemy.cpp:395-396,3405-3450`, `src/p_mobj.cpp:6003-6007,7830-7847`, `src/p_interaction.cpp:1266-1271,1771-1772`, `src/p_setup.cpp:1807-1814`, `src/p_udmf.cpp:558-559`, `src/p_acs.cpp:11174`, `src/menu/menudef.cpp:1656-1667`, `wadsrc/static/mapinfo/doomcommon.txt:97`) and UZDoom source (`src/gamedata/g_skill.cpp:55-357`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

A `skill` block in MAPINFO defines a single difficulty level, setting monster health/damage scaling, ammo/pickup multipliers, respawn behavior, and actor replacement rules specific to that skill. Skill definitions are used to populate the difficulty selection menu and affect gameplay behavior when the skill is selected.

## Block structure and parsing

The `skill <name> { properties }` syntax defines a skill with an arbitrary internal name (used to reference the skill; must be unique within the MAPINFO), followed by a properties block containing key-value pairs. Each property is either a flag (presence only, no value) or a key with an assigned value (numeric or string). Unknown properties are handled differently by engine (see "Engine-family divergence" below).

## Skill properties

Properties supported in this block:

**Pickup/damage scaling:**
- `AmmoFactor = <float>` — multiplier for ammo pickups; e.g., `2.0` doubles ammo, `0.5` halves it. Defaults to 1.0.
- `DoubleAmmoFactor = <float>` — multiplier used when the "Double Ammo" DMFlag is active (overrides `AmmoFactor`). Defaults to 2.0.
- `DropAmmoFactor = <float>` — multiplier for ammo dropped by monsters (and the ammo a dropped weapon gives). When set, the dropped item is flagged to ignore skill, so `AmmoFactor` does not also apply on pickup. When unset (internal sentinel `-1`), drops get half their normal amount and `AmmoFactor` still applies on pickup. On Zandronum an authored `DropAmmoFactor = -1` is stored as fixed-point -1.0, not the sentinel, so it cannot restore the default.
- `ArmorFactor = <float>` — multiplier for armor pickups (`BasicArmorBonus`, `BasicArmorPickup`). Defaults to 1.0.
- `DamageFactor = <float>` — multiplier for damage taken by players (including sector effects like lava/slime); monsters are unaffected. `0.5` takes half damage; `2.0` takes double. In `P_DamageMobj`, hits of 1 point are not scaled, nor is telefrag-magnitude damage (UZDoom scales it on a target with `LAXTELEFRAGDMG`). Defaults to 1.0.
- `KickbackFactor = <float>` — multiplier for knockback when hit (Zandronum: not supported; UZDoom: supported, defaults to 1.0).
- `HealthFactor = <float>` — multiplier for healing received (Zandronum: not supported; UZDoom: supported, defaults to 1.0).
- `MonsterHealth = <float>` — multiplier for the spawn health of non-friendly monsters. `1.0` is normal. The scaled health is clamped to at least 1. Defaults to 1.0.
- `FriendlyHealth = <float>` — multiplier for the spawn health of friendly monsters. `1.0` is normal. The scaled health is clamped to at least 1. Defaults to 1.0.

**Respawn and spawning:**
- `RespawnTime = <float>` — time in seconds before monsters respawn; stored internally as tics (`float * TICRATE`, truncated to integer). Setting to 0 disables respawn. Defaults to 0. When `dmflags & DF_MONSTERS_RESPAWN` is set and respawn is 0, the engine falls back to `TICRATE * gameinfo.defaultrespawntime`.
- `RespawnLimit = <int>` — number of times a monster respawns before staying dead; 0 means infinite respawns. Defaults to 0.
- `SpawnFilter = <int or keyword>` — selects which map things spawn on this skill: a number N ORs in skill bit N, and the property can be repeated to OR in several. Values 1-16 are meaningful. UDMF things carry `skill1`-`skill16`; Doom/Hexen-format things only have the easy/medium/hard flags, which cover skills 1-2, 3 and 4-5. Keywords: `baby` (1), `easy` (2), `normal` (3), `hard` (4), `nightmare` (5). An unknown keyword is silently ignored on Zandronum and a script error on UZDoom. Defaults to 0, which matches no thing's skill bits, so a skill that never sets it spawns no map things except player starts (UZDoom also exempts DoomEdNums marked `NoSkillFlags`).
- `SpawnMulti = true` — Zandronum: not supported. UZDoom: only actors flagged for both cooperative and single-player spawn in single-player mode.
- `SpawnMultiCoopOnly = true` — Zandronum: not supported. UZDoom: only actors flagged for cooperative spawn in single-player mode.
- `PlayerRespawn = true` — Zandronum: not supported. UZDoom: enables player respawn, equivalent to the `AllowRespawn` map flag for this skill only.

**Difficulty/AI settings:**
- `Aggressiveness = <float>` — clamped to 0-1, then stored as `1.0 - value`. The stored value multiplies each monster's `MinMissileChance`, so a higher authored value makes monsters fire missiles more often: `0` is normal, `1` means a monster always fires once the other range checks pass. Unset, the stored value is 1.0 (same as authoring 0).
- `FastMonsters = true` — halves the duration of actor states with the `Fast` keyword; monsters use their `FastSpeed` property if set. Flag only (no value).
- `SlowMonsters = true` — doubles the duration of actor states with the `Slow` keyword. Flag only.
- `EasyBossBrain = true` — makes the BossEye actor shoot `SpawnShots` at a decreased rate. Flag only.
- `EasyKey = true` — shows keys on the automap even without cheats. Flag only.
- `AutoUseHealth = true` — enables automatic use of Raven-style health items and any actor with `HealthPickup.AutoUse` set to 1 or 2 (not 3, which is Strife-style automatic). Flag only.
- `NoPain = true` — non-player actors never enter their pain states; players still do. Flag only.
- `InstantReaction = true` — Zandronum: not supported. UZDoom: monsters perform their first ranged attack immediately upon spawning without taking initial steps.
- `NoInfighting = true` — Zandronum: not supported. UZDoom: monsters do not infight (overridden by map-level infighting settings if present).
- `TotalInfighting = true` — Zandronum: not supported. UZDoom: monsters infight even with same species (overridden by map-level infighting settings if present).
- `DisableCheats = true` — cheats are disabled at the console unless `sv_cheats cvar` is set to true. Flag only.

**Actor and menu properties:**
- `ReplaceActor = "<original>", "<replacement>"` — replaces spawned actors of type `<original>` with `<replacement>` for this skill. Applied before DECORATE-level replacements. **Non-transitive:** if skill replaces A→B and B→C, A is not replaced by C. Repeatable.
- `Name = "<text>"` — display name shown in the skill menu (supports `$<msgid>` language string references).
- `PicName = "<lump>"` — lump name of a graphic used in the skill menu. Only one of the graphic and `Name` is shown per entry. On Zandronum the graphic wins when both are set, unless a `PlayerClassName` entry matches the selected class. The text-only fallback menu used for overlong skill lists always shows text.
- `PlayerClassName = "<class name>", "<skill name>"` — class-specific skill display name (e.g., `"Marine", "Extreme"` for the Marine class). `<class name>` must be the display name, not the actor class name. Repeatable per class.
- `TextColor = "<color>"` — color of the skill name in the menu; accepts named colors like `"RED"` or `"BLUE"`.
- `Key = "<hotkey>"` — single-character hotkey for the menu (lowercased; only first character is used).
- `MustConfirm` or `MustConfirm = "<text>"` — requires the player to confirm difficulty choice (like Nightmare). Optional custom confirmation text replaces the default message.
- `DefaultSkill = true` — makes this skill highlighted in the menu by default and selected if an episode has `noskillmenu`. **Zandronum:** fatal error if a default skill already exists. The stock game MAPINFO already marks `normal` as default, so a PWAD `DefaultSkill` is fatal unless `clearskills` came first. **UZDoom:** last declaration wins. Flag only.
- `NoMenu = true` — Zandronum: not supported. UZDoom: this skill does not appear in the menu.
- `ACSReturn = <int>` — value returned by the ACS `GameSkill` function for this skill. When not set, defaults to the skill's array index in `AllSkills` (0-based). When redefining an existing skill by name, the previous skill's `ACSReturn` is inherited unless explicitly set.

## Engine-family divergence

The wiki page describes upstream ZDoom/GZDoom-family features. **Zandronum implements a subset of the properties listed above.** Properties not appearing in this section exist only in UZDoom/GZDoom; Zandronum prints an unknown-property message and skips them (see "Behavior on unknown properties" below).

**Zandronum-only or not in UZDoom (verified absent):**
None identified.

**UZDoom/GZDoom-only (verified absent from Zandronum):**
`KickbackFactor`, `HealthFactor`, `SpawnMulti`, `SpawnMultiCoopOnly`, `InstantReaction`, `NoInfighting`, `TotalInfighting`, `NoMenu`, `PlayerRespawn`.

## Behavior on unknown properties

- **Zandronum:** unknown properties trigger a non-fatal console message (`ScriptMessage`), and parsing skips to the next property. The skill is still created and loaded.
- **UZDoom:** unknown properties trigger a non-fatal console warning and are skipped similarly.

## Other known behaviors and gotchas

**`clearskills` fatality:** Using `clearskills` (outside any block) with no subsequent `skill` definitions is a fatal startup error in both engines: "You cannot use clearskills in a MAPINFO if you do not define any new skills after it." The wiki does not document this.

**`DefaultSkill` error behavior differs:** Zandronum raises a fatal script error ("<skill> is already the default skill") whenever `DefaultSkill` appears while a default already exists. The check runs before a same-named redefinition is matched, and the stock Doom, Heretic, Hexen and Strife MAPINFOs already mark a default, so even `skill normal { DefaultSkill }` is fatal unless `clearskills` came first. UZDoom silently keeps the last one declared. If targeting both engines, use `clearskills` and declare `DefaultSkill` on exactly one of your skills.

**Fixed-point quantization on Zandronum:** Zandronum stores the ammo, double-ammo, drop-ammo, damage, armor, monster-health and friendly-health factors and `Aggressiveness` as 16.16 fixed-point (via `FLOAT2FIXED`), while UZDoom stores them as doubles. Zandronum's factors are quantized to a 1/65536 step, so only extremely small factors collapse to 0. This does not make a tiny `MonsterHealth` (e.g. the wiki's `monsterhealth = 0.001` example) behave differently: both engines clamp the scaled spawn health to at least 1, so affected monsters spawn with 1 health.

**`Aggressiveness` inversion:** Both engines store this field as `1.0 - clamp(value, 0, 1)`. The stored value scales `MinMissileChance`, so an authored `0.0` (stored `1.0`) is normal behavior and an authored `1.0` (stored `0.0`) is maximum aggression. ACS cannot read it: `GameSkill()` takes no argument and returns only the skill's `ACSReturn`.

**`RespawnTime` interaction with dmflags:** When `dmflags & DF_MONSTERS_RESPAWN` is set and a skill's respawn counter is 0, `G_SkillProperty(SKILLP_Respawn)` returns `TICRATE * gameinfo.defaultrespawntime` instead of 0, overriding the skill's zero value. This allows global-dmflag respawn to kick in despite the skill declaring no respawn.

## Examples

Nightmare difficulty:
```text
skill nightmare
{
   AmmoFactor = 2
   FastMonsters
   DisableCheats
   RespawnTime = 12
   SpawnFilter = Nightmare
   PicName = "M_NMARE"
   MustConfirm
   Key = "n"
}
```

"I'm Too Young To Die" difficulty:
```text
skill baby
{
   AutoUseHealth
   AmmoFactor = 2
   DamageFactor = 0.5
   EasyBossBrain
   SpawnFilter = Baby
   PicName = "M_JKILL"
   Key = "i"
}
```

Hard difficulty with actor replacement:
```text
skill hellish
{
  FastMonsters
  DisableCheats
  SpawnFilter = Hard
  Name = "Hellish"
  ReplaceActor = "Medikit", "Stimpack"
  ReplaceActor = "HellKnight", "BaronOfHell"
  ReplaceActor = "ZombieMan", "ShotgunGuy"
}
```

## See also

- [MAPINFO format](mapinfo-format.md) — overview of MAPINFO structure and supported block types.
- [GameInfo block definition](gameinfo-block.md) — global game-wide settings.
- [Map block definitions and inheritance](map-block-and-inheritance.md) — map-level and inherited properties.
