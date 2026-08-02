# `int ChangeSkill(int skill)`

Changes the game's difficulty level. Action special (positive index `179` in `zcommon.bcs`'s
`special` table), implemented as `FUNC(LS_ChangeSkill)` in
the Zandronum source's `src/p_lnspec.cpp:3276-3287`.

**Bucket:** action special.

- `skill` — 0-based skill index to switch to. Valid range depends on the current game
  configuration; Zandronum's default skill definitions use indices 0–4:
  - `0` — Very Easy (`SKILL_VERY_EASY`)
  - `1` — Easy (`SKILL_EASY`)
  - `2` — Normal (`SKILL_NORMAL`)
  - `3` — Hard (`SKILL_HARD`)
  - `4` — Nightmare! (`SKILL_VERY_HARD`)
  
  Other skill indices (5–15) are available if the current mod or UDMF map defines them. **Out-of-bounds
  indices are handled gracefully:** the fork validates `skill` against `AllSkills.Size()` (checked at
  `p_lnspec.cpp:3278`), and invalid indices set a sentinel value (`NextSkill = -1`) that suppresses
  the skill change at the next level load (rather than crashing or silently wrapping). **The skill
  change takes effect at the next map transition**, not immediately — `NextSkill` is processed during
  `G_DoLoadLevel()` at `g_level.cpp:2076-2081`, where it sets the `gameskill` cvar and then resets
  `NextSkill` to `-1`. Changing skill mid-map has no immediate effect on the current level's
  difficulty.

**Returns:** `true` (success). The return value does not distinguish between valid and out-of-bounds
calls — even an invalid `skill` argument returns `true` (it just fails silently by setting
`NextSkill = -1`).

**Provenance:** wiki page `ChangeSkill - ZDoom Wiki.html` (`_intake/`, source URL
`https://zdoom.org/w/index.php?title=ChangeSkill&oldid=37542`) + source-verified
(`p_lnspec.cpp:3276-3287`, `g_level.cpp:2076-2081`, `doomstat.cpp:NextSkill declaration`,
`g_level.cpp:NextSkill initialization`). The wiki correctly describes the skill-index parameters
(0–4 are the defaults) and that skill changes take effect "at the next map change." The wiki's
statement "you can also use the following (defined in zdefs.acs)" applies to ZDoom; Zandronum
defines skill constants in `zcommon.bcs` rather than `zdefs.acs`, but the names (`SKILL_VERY_EASY`,
etc.) are identical. **Engine:** Zandronum 3.2.1 (function was introduced in 2007, ancestry of the
`28f736fb3` version-bump commit, so present in all versions including 3.2.1). **Tier:** A.
