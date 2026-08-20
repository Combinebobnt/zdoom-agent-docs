# GameSkill

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** [GameSkill - ZDoom Wiki](https://zdoom.org/w/index.php?title=GameSkill&oldid=36570), verified against Zandronum 3.3-alpha fork source (`p_acs.cpp` PCD_GAMESKILL, `g_skill.cpp` G_SkillProperty/ParseSkill)
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

**Signature:** `int GameSkill()`

## Summary

Returns the current skill level as an ACS-readable property. **Critical divergence from the wiki: the return value is not the skill index but the `ACSReturn` property of the active skill definition in MAPINFO.** This is not a fork-specific enhancement — it holds identically on UZDoom, whose `PCD_GAMESKILL` handler is the same one-line `G_SkillProperty(SKILLP_ACSReturn)` call (`src/playsim/p_acs.cpp:8938-8940`) as Zandronum's (`src/p_acs.cpp:11173-11175`). See "Wiki/engine divergence" below.

For the stock Doom skill set (SKILL_VERY_EASY=0 through SKILL_VERY_HARD=4), the default `ACSReturn` values match their indices, so the common pattern `if (GameSkill() <= SKILL_NORMAL)` works out of the box. However, custom MAPINFO skill definitions can set arbitrary `ACSReturn` values via the `ACSReturn <int>` field, **potentially making `GameSkill()` return any integer, including values outside 0-4 or duplicates across multiple skills.**

## Return value

An `int` read directly from `AllSkills[gameskill].ACSReturn` (`G_SkillProperty(SKILLP_ACSReturn)`; UZDoom `src/gamedata/g_skill.cpp:390-391`, Zandronum `src/g_skill.cpp:373-374` — identical on both engines):

- Stock Doom skills default to their index (0–4), named via the anonymous enum in `zt-bcc/lib/zcommon.bcs`:
  - `SKILL_VERY_EASY = 0` ("I'm Too Young to Die")
  - `SKILL_EASY = 1` ("Hey, Not Too Rough")
  - `SKILL_NORMAL = 2` ("Hurt Me Plenty")
  - `SKILL_HARD = 3` ("Ultra-Violence")
  - `SKILL_VERY_HARD = 4` ("Nightmare!")

- **Custom MAPINFO:** If a mod author defines new skill entries or redefines existing ones, each skill's `ACSReturn <int>` value is arbitrary and author-settable. If omitted (confirmed identical `ParseSkill` logic on both engines — UZDoom `src/gamedata/g_skill.cpp:326-346`, Zandronum `src/g_skill.cpp:293-313`):
  - A redefinition of an existing skill inherits the original's `ACSReturn` value.
  - A new skill definition auto-assigns `ACSReturn = AllSkills.Size()` at parse time (one higher than the previous skill index).

- **Failure case:** If no skills are defined (`AllSkills.Size() == 0`), returns `0` (UZDoom `src/gamedata/g_skill.cpp:415`, Zandronum `src/g_skill.cpp:389` — same guard on both).

## Multiplayer / Netcode

`gameskill` is declared `CVAR_SERVERINFO | CVAR_LATCH` on both engines (UZDoom `src/g_game.cpp:203`; Zandronum `src/g_game.cpp:145`), so it is server-authoritative and replicated to clients, and `CVAR_LATCH` means a value set mid-game doesn't take effect until the next level/game start. `CLIENTSIDE` scripts therefore read the server's current skill setting, not a client-local value — and there's no live-update case to worry about, since the cvar itself can't change mid-level on either engine.

A pre-existing claim in this doc that Zandronum's sync happens "on map load and when the server admin changes skill (e.g., via the Invasion skill-up commands)" does not hold up under a fresh read: the only two call sites of `SERVERCOMMANDS_SetGameSkill` (`src/sv_commands.cpp:2509`) are both full-state sends to a single (re)connecting/authenticating client (`src/sv_main.cpp:1532` and `:7048`), not a broadcast triggered by an admin skill change or any Invasion-mode mechanic — Invasion mode only *reads* `gameskill` to scale per-wave monster counts (`src/invasion.cpp:1541`), it never writes it. That parenthetical has been removed as inaccurate rather than carried forward.

## Engine-family divergence: server→client sync mechanism

Zandronum syncs `gameskill` via an explicit named command pair — `SERVERCOMMANDS_SetGameSkill` (`src/sv_commands.cpp:2509`) on the server, `client_SetGameSkill` (`src/cl_main.cpp:6139`) on the client — sent as part of the connect/authentication handshake. The server-side function packs the skill index and `botskill` into an `SVC_SETGAMESKILL` command; the client clamps the received byte to `[0, AllSkills.Size() - 1]` before applying it.

UZDoom has no equivalent named per-cvar function. It syncs `gameskill` as part of the generic `CVAR_SERVERINFO` cvar block written by `Net_SetGameInfo` (`C_WriteCVars(stream, CVAR_SERVERINFO, true)`, `src/d_net.cpp:1906`) alongside every other serverinfo cvar, rather than a dedicated per-cvar command. The practical effect for `GameSkill()` is the same on both engines — a joining client receives the server's `gameskill` value before scripts run — only the wire mechanism differs.

## Wiki/engine divergence: ACSReturn vs. wiki's "skill level"

- **Wiki source:** ZDoom wiki, which describes the function as "returns the skill level of the current game" — read literally, this implies the return value is simply the skill slot index. It is not, on either currently-verified engine: `GameSkill()` returns the MAPINFO `ACSReturn` property of the active skill definition, which only happens to equal the slot index for the stock skills, or when a custom skill's author leaves `ACSReturn` unset. A prior revision of this doc framed the richer semantics as "Zandronum's custom-MAPINFO-skill support," as if it were a fork-specific enhancement over a simpler upstream; that framing has been corrected here — `ParseSkill`'s `ACSReturn` handling is essentially identical between UZDoom and Zandronum (see "Return value" above), so the gap is between the wiki's description and both actual engines, not between the two engines.
- **Constants location:** The wiki lists these as `zdefs.acs` constants; this project's `zt-bcc` compiler exposes them instead as an anonymous enum in `zcommon.bcs` — a compiler/library naming difference, not an engine one.

## See also

- [ChangeLevel](changelevel.md) — note that omitting the optional `skill` argument compiles to `0` (resetting to `SKILL_VERY_EASY`), unlike unset MAPINFO `ACSReturn` fields.
