# `int GetGamemodeState(void)`

**Tier:** A.
**Engine:** Zandronum 3.2.1 (function predates the 3.2.1 version-bump commit, confirmed via git ancestry — see "Version note" above).
**Provenance:** wiki page `GetGameModeState - Zandronum Wiki.html` (`_intake/`, retrieved 2026-07-29, `oldid=1288`) + source-verified against `p_acs.cpp:7219-7222`, `gamemode.cpp:594-684, 1170-1184`, `gamemode.h:98-103`, `zt-bcc/lib/zcommon.bcs:1184-1188,1740`, and git ancestry check against `28f736fb3`.
**Bucket:** extension function.

Returns the current game-mode's state as a `GAMESTATE_*` enum value. Extension function
(`ACSF_GetGamemodeState`, index `-107` in the zt-bcc source's `lib/zcommon.bcs:1740`), implementation
`case ACSF_GetGamemodeState:` in the Zandronum source's `src/p_acs.cpp:7219-7222`, which just returns
`GAMEMODE_GetState()` (the Zandronum source's `src/gamemode.cpp:1170-1184`).

**Naming note:** the wiki page (and its title) call this `GetGameModeState` (capital "M"). The
actual declared name in `zcommon.bcs:1740` is `GetGamemodeState` (lowercase "m" in "mode"). ACS/BCS
identifier lookup is case-insensitive, so both spellings compile and resolve to the same function
in practice — but if you're grepping source for this call, search case-insensitively or you'll
miss it under the wiki's spelling.

Takes no arguments.

## Return value

The `GAMESTATE_*` constants (the zt-bcc source's `lib/zcommon.bcs:1184-1188`):

- `GAMESTATE_UNSPECIFIED = -1` — fallback value; `GAMEMODE_GetState()`'s final `return` if none of
  the checks below match (shouldn't normally happen, per the engine's own comment at
  `gamemode.cpp:1183`: "Some of the above should apply, but this function always has to return
  something.").
- `GAMESTATE_WAITFORPLAYERS = 0`
- `GAMESTATE_COUNTDOWN = 1`
- `GAMESTATE_INPROGRESS = 2`
- `GAMESTATE_INRESULTSEQUENCE = 3`

`GAMEMODE_GetState()` evaluates these in order (`WAITFORPLAYERS` → `COUNTDOWN` → `INPROGRESS` →
`INRESULTSEQUENCE` → `UNSPECIFIED`), and each check's actual definition depends heavily on which
mode is currently active (`gamemode.cpp:594-676`):

- **Survival / Invasion / Duel / (Team)LMS / (Team)Possession** each have their own internal state
  machine (`SURVIVAL_GetState()`, `INVASION_GetState()`, etc.) that's mapped directly to one of the
  four states — e.g. for Invasion, `IS_INPROGRESS`, `IS_BOSSFIGHT`, **and** `IS_WAVECOMPLETE` all
  count as `GAMESTATE_INPROGRESS`; `IS_FIRSTCOUNTDOWN` and `IS_COUNTDOWN` both count as
  `GAMESTATE_COUNTDOWN`.
- **All other (non-listed) modes**, i.e. anything without its own state machine, fall back to a
  player-count/flag-based approximation instead of a real state machine:
  - Non-cooperative (`GMF_COOPERATIVE` flag clear): `WAITFORPLAYERS` when fewer than 2 active
    players; `INPROGRESS` when >= 2 active players **and** the end-of-level delay is 0.
  - Cooperative (`GMF_COOPERATIVE` flag set): `WAITFORPLAYERS` when 0 active players;
    `INPROGRESS` when >= 1 active player **and** the end-of-level delay is 0.
  - These modes have no real countdown, so `GAMESTATE_COUNTDOWN` is never returned for them
    (`IsGameInCountdown()` hard-codes `false` in the `else` branch, `gamemode.cpp:628`).
  - `GAMESTATE_INRESULTSEQUENCE` for these modes is a substitute, defined as "the end-of-level
    delay is currently > 0" (`gamemode.cpp:675`, comment: "As substitute for such a sequence we
    consider whether the game is frozen because of the end level delay").

This matches the wiki's per-mode description closely (worth flagging: the wiki doesn't mention
that Invasion's `IS_WAVECOMPLETE`/`IS_BOSSFIGHT` sub-states also count as `INPROGRESS`, or that
LMS/Possession have an extra "next round countdown" sub-state folded into `COUNTDOWN`).

## Version note

`GetGamemodeState` was added in commit `d30fce6ae` ("Added new ACS command GetGamemodeState...").
Verified via `git merge-base --is-ancestor d30fce6ae 28f736fb3` (the "changed the version string
to 3.2.1" commit) — it returns true, i.e. this function **predates and is present in 3.2.1**, not
a post-3.2.1 addition from the `3.3-alpha` checkout.
