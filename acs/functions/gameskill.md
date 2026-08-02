# GameSkill

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** [GameSkill - ZDoom Wiki](https://zdoom.org/w/index.php?title=GameSkill&oldid=36570), verified against Zandronum 3.3-alpha fork source (`p_acs.cpp` PCD_GAMESKILL, `g_skill.cpp` G_SkillProperty/ParseSkill)

**Signature:** `int GameSkill()`

## Summary

Returns the current skill level as an ACS-readable property. **Critical divergence from the wiki: the return value is not the skill index but the `ACSReturn` property of the active skill definition in MAPINFO.**

For the stock Doom skill set (SKILL_VERY_EASY=0 through SKILL_VERY_HARD=4), the default `ACSReturn` values match their indices, so the common pattern `if (GameSkill() <= SKILL_NORMAL)` works out of the box. However, custom MAPINFO skill definitions can set arbitrary `ACSReturn` values via the `ACSReturn <int>` field, **potentially making `GameSkill()` return any integer, including values outside 0-4 or duplicates across multiple skills.**

## Return value

An `int` read directly from `AllSkills[gameskill].ACSReturn`:

- Stock Doom skills default to their index (0–4), named via the anonymous enum in `zt-bcc/lib/zcommon.bcs`:
  - `SKILL_VERY_EASY = 0` ("I'm Too Young to Die")
  - `SKILL_EASY = 1` ("Hey, Not Too Rough")
  - `SKILL_NORMAL = 2` ("Hurt Me Plenty")
  - `SKILL_HARD = 3` ("Ultra-Violence")
  - `SKILL_VERY_HARD = 4` ("Nightmare!")

- **Custom MAPINFO:** If a mod author defines new skill entries or redefines existing ones, each skill's `ACSReturn <int>` value is arbitrary and author-settable. If omitted:
  - A redefinition of an existing skill inherits the original's `ACSReturn` value.
  - A new skill definition auto-assigns `ACSReturn = AllSkills.Size()` at parse time (one higher than the previous skill index).

- **Failure case:** If no skills are defined (`AllSkills.Size() == 0`), returns `0`.

## Multiplayer / Netcode

In multiplayer, `gameskill` is replicated server→client, so `CLIENTSIDE` scripts read the server's current skill setting, not a client-local value. The skill is read via the `gameskill` global cvar, which is synchronized by `SERVERCOMMANDS_SetGameSkill` / `client_SetGameSkill` on map load and when the server admin changes skill (e.g., via the Invasion skill-up commands).

## Fork divergence

- **Wiki source:** ZDoom wiki, which describes the function as "returns the skill level of the current game" — accurate for ZDoom's simpler skill model. Zandronum's custom-MAPINFO-skill support makes the semantics richer; the return value is a MAPINFO property, not the skill slot index.
- **Constants location:** The wiki lists these as `zdefs.acs` constants; Zandronum's zt-bcc exposes them as an anonymous enum in `zcommon.bcs`.

## See also

- [ChangeLevel](changelevel.md) — note that omitting the optional `skill` argument compiles to `0` (resetting to `SKILL_VERY_EASY`), unlike unset MAPINFO `ACSReturn` fields.
