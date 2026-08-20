# `int ChangeSkill(int skill)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes — function was introduced in 2007, ancestry of the
`28f736fb3` version-bump commit, so present in all Zandronum versions including 3.2.1 (UZDoom's own
introduction history wasn't traced this pass).
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** wiki page `ChangeSkill - ZDoom Wiki.html` (`_intake/`, source URL
`https://zdoom.org/w/index.php?title=ChangeSkill&oldid=37542`) + source-verified
(`p_lnspec.cpp:3276-3287`, `g_level.cpp:2076-2081`, `doomstat.cpp:NextSkill declaration`,
`g_level.cpp:NextSkill initialization`). The wiki correctly describes the skill-index parameters
(0–4 are the defaults) and that skill changes take effect "at the next map change." The wiki's
statement "you can also use the following (defined in zdefs.acs)" applies to ZDoom; Zandronum
defines skill constants in `zcommon.bcs` rather than `zdefs.acs`, but the names (`SKILL_VERY_EASY`,
etc.) are identical.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** action special.

Changes the game's difficulty level. Action special (positive index `179` in `zcommon.bcs`'s
`special` table, and `179` in UZDoom's `actionspecials.h` `DEFINE_SPECIAL(ChangeSkill, 179, 1, 1,
1)`), implemented as `FUNC(LS_ChangeSkill)` in the Zandronum source's `src/p_lnspec.cpp:3276-3287`
and the UZDoom source's `src/playsim/p_lnspec.cpp:3165-3176` — the two implementations are
byte-for-byte identical.

- `skill` — 0-based skill index to switch to. Valid range depends on the current game
  configuration; the default skill definitions use indices 0–4:
  - `0` — Very Easy (`SKILL_VERY_EASY`)
  - `1` — Easy (`SKILL_EASY`)
  - `2` — Normal (`SKILL_NORMAL`)
  - `3` — Hard (`SKILL_HARD`)
  - `4` — Nightmare! (`SKILL_VERY_HARD`)
  
  Other skill indices (5–15) are available if the current mod or UDMF map defines them. **Out-of-bounds
  indices are handled gracefully:** both engines validate `skill` against `AllSkills.Size()` (Zandronum
  `p_lnspec.cpp:3278`; UZDoom `src/playsim/p_lnspec.cpp:3167`), and invalid indices set a sentinel value
  (`NextSkill = -1`) that suppresses the skill change at the next level load (rather than crashing or
  silently wrapping). **The skill change takes effect at the next map transition**, not immediately —
  `NextSkill` is processed inside `G_DoLoadLevel` on Zandronum (`g_level.cpp:1337-1342`) and inside
  the equivalent `FLevelLocals::DoLoadLevel` on UZDoom (`src/g_level.cpp:1394-1400`), where it sets
  the `gameskill` cvar and then resets `NextSkill` to `-1`.
  Changing skill mid-map has no immediate effect on the current level's difficulty.

**Returns:** `true` (success). The return value does not distinguish between valid and out-of-bounds
calls — even an invalid `skill` argument returns `true` (it just fails silently by setting
`NextSkill = -1`).
