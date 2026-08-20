# Skill block definition

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `MAPINFO/Skill_definition` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=MAPINFO%2FSkill_definition&oldid=54710) + verified against Zandronum source (`src/g_skill.cpp:56-314`) and UZDoom source (`src/gamedata/g_skill.cpp:55-357`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

A `skill` block in MAPINFO defines a single difficulty level, setting monster health/damage scaling, ammo/pickup multipliers, respawn behavior, and actor replacement rules specific to that skill. Skill definitions are used to populate the difficulty selection menu and affect gameplay behavior when the skill is selected.

## Block structure and parsing

The `skill <name> { properties }` syntax defines a skill with an arbitrary internal name (used to reference the skill; must be unique within the MAPINFO), followed by a properties block containing key-value pairs. Each property is either a flag (presence only, no value) or a key with an assigned value (numeric or string). Unknown properties are handled differently by engine (see "Engine-family divergence" below).

## Skill properties

Properties supported in this block:

**Pickup/damage scaling:**
- `AmmoFactor = <float>` — multiplier for ammo pickups; e.g., `2.0` doubles ammo, `0.5` halves it. Defaults to 1.0.
- `DoubleAmmoFactor = <float>` — multiplier used when the "Double Ammo" DMFlag is active (overrides `AmmoFactor`). Defaults to 2.0.
- `DropAmmoFactor = <float>` — multiplier for ammo and weapons dropped by monsters; overrides `AmmoFactor` for drops. When unset (`-1`), `AmmoFactor` is used instead. Defaults to -1 (inherit from `AmmoFactor`).
- `ArmorFactor = <float>` — multiplier for armor pickups (`BasicArmorBonus`, `BasicArmorPickup`). Defaults to 1.0.
- `DamageFactor = <float>` — multiplier for incoming damage (including sector effects like lava/slime). `0.5` takes half damage; `2.0` takes double. Defaults to 1.0.
- `KickbackFactor = <float>` — multiplier for knockback when hit (Zandronum: not supported; UZDoom: supported, defaults to 1.0).
- `HealthFactor = <float>` — multiplier for healing received (Zandronum: not supported; UZDoom: supported, defaults to 1.0).
- `MonsterHealth = <float>` — multiplier for all hostile monster health. `1.0` is normal. Defaults to 1.0.
- `FriendlyHealth = <float>` — multiplier for all friendly monster health. `1.0` is normal. Defaults to 1.0.

**Respawn and spawning:**
- `RespawnTime = <float>` — time in seconds before monsters respawn; stored internally as tics (`float * TICRATE`, truncated to integer). Setting to 0 disables respawn. Defaults to 0. When `dmflags & DF_MONSTERS_RESPAWN` is set and respawn is 0, the engine falls back to `TICRATE * gameinfo.defaultrespawntime`.
- `RespawnLimit = <int>` — number of times a monster respawns before staying dead; 0 means infinite respawns. Defaults to 0.
- `SpawnFilter = <int or keyword>` — bitmask controlling which actor thing-flags spawn on this skill. Values 1–16 are valid (UDMF-format maps only support skills 1–5). Keywords: `baby` (1), `easy` (2), `normal` (3), `hard` (4), `nightmare` (5). Defaults to 0 (all flags).
- `SpawnMulti = true` — Zandronum: not supported. UZDoom: only actors flagged for both cooperative and single-player spawn in single-player mode.
- `SpawnMultiCoopOnly = true` — Zandronum: not supported. UZDoom: only actors flagged for cooperative spawn in single-player mode.
- `PlayerRespawn = true` — Zandronum: not supported. UZDoom: enables player respawn, equivalent to the `AllowRespawn` map flag for this skill only.

**Difficulty/AI settings:**
- `Aggressiveness = <float>` — stored internally as `1.0 - clamp(value, 0, 1)`, so supplied value is clamped to 0–1, then inverted. Higher supplied values mean lower stored aggression (reversed semantics). Defaults to 1.0 (stored as 0).
- `FastMonsters = true` — halves the duration of actor states with the `Fast` keyword; monsters use their `FastSpeed` property if set. Flag only (no value).
- `SlowMonsters = true` — doubles the duration of actor states with the `Slow` keyword. Flag only.
- `EasyBossBrain = true` — makes the BossEye actor shoot `SpawnShots` at a decreased rate. Flag only.
- `EasyKey = true` — shows keys on the automap even without cheats. Flag only.
- `AutoUseHealth = true` — enables automatic use of Raven-style health items and any actor with `HealthPickup.AutoUse` set to 1 or 2 (not 3, which is Strife-style automatic). Flag only.
- `NoPain = true` — actors never enter their pain states. Flag only.
- `InstantReaction = true` — Zandronum: not supported. UZDoom: monsters perform their first ranged attack immediately upon spawning without taking initial steps.
- `NoInfighting = true` — Zandronum: not supported. UZDoom: monsters do not infight (overridden by map-level infighting settings if present).
- `TotalInfighting = true` — Zandronum: not supported. UZDoom: monsters infight even with same species (overridden by map-level infighting settings if present).
- `DisableCheats = true` — cheats are disabled at the console unless `sv_cheats cvar` is set to true. Flag only.

**Actor and menu properties:**
- `ReplaceActor = "<original>", "<replacement>"` — replaces spawned actors of type `<original>` with `<replacement>` for this skill. Applied before DECORATE-level replacements. **Non-transitive:** if skill replaces A→B and B→C, A is not replaced by C. Repeatable.
- `Name = "<text>"` — display name shown in the skill menu (supports `$<msgid>` language string references).
- `PicName = "<lump>"` — lump name of a graphic used in the skill menu (mutually exclusive with `Name` for display purposes — only one is shown).
- `PlayerClassName = "<class name>", "<skill name>"` — class-specific skill display name (e.g., `"Marine", "Extreme"` for the Marine class). `<class name>` must be the display name, not the actor class name. Repeatable per class.
- `TextColor = "<color>"` — color of the skill name in the menu; accepts named colors like `"RED"` or `"BLUE"`.
- `Key = "<hotkey>"` — single-character hotkey for the menu (lowercased; only first character is used).
- `MustConfirm` or `MustConfirm = "<text>"` — requires the player to confirm difficulty choice (like Nightmare). Optional custom confirmation text replaces the default message.
- `DefaultSkill = true` — makes this skill highlighted in the menu by default and selected if an episode has `noskillmenu`. **Zandronum only:** fatal error if more than one skill declares this; **UZDoom:** last declaration wins. Flag only.
- `NoMenu = true` — Zandronum: not supported. UZDoom: this skill does not appear in the menu.
- `ACSReturn = <int>` — value returned by the ACS `GameSkill` function for this skill. When not set, defaults to the skill's array index in `AllSkills` (0-based). When redefining an existing skill by name, the previous skill's `ACSReturn` is inherited unless explicitly set.

## Engine-family divergence

The wiki page describes upstream ZDoom/GZDoom-family features. **Zandronum implements a subset of the properties listed above.** Properties not appearing in this section exist only in UZDoom/GZDoom and are silently ignored at runtime in Zandronum (see "Behavior on unknown properties" below).

**Zandronum-only or not in UZDoom (verified absent):**
None identified.

**UZDoom/GZDoom-only (verified absent from Zandronum):**
`KickbackFactor`, `HealthFactor`, `SpawnMulti`, `SpawnMultiCoopOnly`, `InstantReaction`, `NoInfighting`, `TotalInfighting`, `NoMenu`, `PlayerRespawn`.

## Behavior on unknown properties

- **Zandronum:** unknown properties trigger a non-fatal console message (`ScriptMessage`), and parsing skips to the next property. The skill is still created and loaded.
- **UZDoom:** unknown properties trigger a non-fatal console warning and are skipped similarly.

## Other known behaviors and gotchas

**`clearskills` fatality:** Using `clearskills` (outside any block) with no subsequent `skill` definitions causes `I_FatalError("You cannot use clearskills in a MAPINFO if you do not define any new skills after it")` in both engines. The wiki does not document this.

**`DefaultSkill` error behavior differs:** Zandronum fatally errors if a second skill declares `DefaultSkill` (engine call is `sc.ScriptError`, fatal). UZDoom silently keeps the last one declared. If targeting both engines, declare `DefaultSkill` on exactly one skill.

**Fixed-point quantization on Zandronum:** Zandronum stores ammo, damage, armor, health, and kickback factors as 16.16 fixed-point (via `FLOAT2FIXED`), while UZDoom stores them as native doubles. Very small factors on Zandronum (e.g., `0.001` in the wiki's example) quantize to the nearest fixed-point step (~0.000015), potentially rounding to zero. This affects the wiki's "Dante" nightmare example with `monsterhealth = 0.001`: on Zandronum, that becomes 0 (monsters are unkillable), while on UZDoom it remains sub-millimeter precision.

**`Aggressiveness` inversion:** Both engines store this field as `1.0 - clamp(value, 0, 1)`, so the authored value is inverted. An authored `0.0` stores as `1.0` (maximum aggression), and `1.0` stores as `0.0` (minimum). Querying via ACS (`GameSkill(SKILLP_Aggressiveness)`) returns the stored (inverted) value.

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
