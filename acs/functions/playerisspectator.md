# `int PlayerIsSpectator(int player)`

**Tier:** A.
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-28)
**Provenance:** wiki page `PlayerIsSpectator - Zandronum Wiki.html` (`_intake/`, retrieved
2026-07-28, `https://wiki.zandronum.com/w/index.php?title=PlayerIsSpectator&oldid=1320`) + source-verified (`p_acs.cpp:7148-7161`, `d_player.h:736-740`,
`gamemode_enums.h:72`, `p_interaction.cpp:2441-2453,3006-3014`). The wiki's 0/1/2 mapping holds
exactly; the mode-gating on `2` and the invalid-index-vs-non-spectator ambiguity are this doc's
source-verified additions.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Checks whether a player is a spectator, and distinguishes "true" spectators from players waiting
to respawn after dying. Extension function (`ACSF_PlayerIsSpectator`, index -101 in
`zcommon.bcs`), implementation at the Zandronum source's `src/p_acs.cpp:7148-7161`.

```cpp
case ACSF_PlayerIsSpectator:
{
    const ULONG ulPlayer = static_cast<ULONG>( args[0] );
    if ( PLAYER_IsValidPlayer( ulPlayer ) )
    {
        if ( ( GAMEMODE_GetCurrentFlags() & GMF_DEADSPECTATORS ) && players[ulPlayer].bDeadSpectator )
            return 2;
        else
            return players[ulPlayer].bSpectating;
    }
    else
        return 0;
}
```

- **Return `1`** — backed directly by `player_t::bSpectating` (`d_player.h:736-737`, "This player
  is currently spectating").
- **Return `2`** — requires *both* the current game mode to have the `GMF_DEADSPECTATORS` flag
  (`gamemode_enums.h:72`) *and* `player_t::bDeadSpectator` (`d_player.h:739-740`, "This player is
  currently spectating after dying in LMS or survival co-op") to be set. `bDeadSpectator` is a
  qualifier on `bSpectating`, not an independent state — `PLAYER_SetSpectator()`
  (`p_interaction.cpp:2441-2453`) only ever sets it while `bSpectating` is also true. Practical
  effect: in a game mode *without* `GMF_DEADSPECTATORS` (most non-LMS/non-survival modes), a
  player who is mechanically in this "waiting to respawn" state still reads back as plain `1`
  ("true spectator"), not `2` — the distinction only surfaces in modes that support it.
- **Return `0`** covers two different situations that are indistinguishable from the return value
  alone: a genuinely non-spectating in-game player, **and** an invalid `player` index.
  `PLAYER_IsValidPlayer` (`p_interaction.cpp:3006-3014`) rejects both `player >= MAXPLAYERS` and
  `playeringame[player] == false`. `args[0]` is cast to `ULONG` before the check, so a negative
  `player` wraps to a huge unsigned value and still fails the `>= MAXPLAYERS` bound (no
  out-of-bounds read, no crash) — but callers cannot tell "player 0 isn't spectating" apart from
  "player 0 isn't in the game" or "player index doesn't exist."

**Example** (from the wiki, a `DISCONNECT` script distinguishing a true disconnect from becoming
a spectator):

```text
Script 1 (int player) DISCONNECT
{
    if (!PlayerIsSpectator(player))
        PrintBold(s: "Someone disconnected.");
    else if (PlayerIsSpectator(player))
        PrintBold(s: "Someone became a spectator.");
}
```

**Returns:** `int` — `0` not a spectator (or invalid player), `1` true spectator, `2` dead
spectator (mode-dependent, see above).

## Engine-family divergence

`PlayerIsSpectator` is bound at ACSF index 101 — inside the 100–199 range UZDoom's own ACSF enum
skips entirely, reserved for Zandronum's extensions and never implemented. A Zandronum-compiled
object calling it under UZDoom always gets `0` back, unconditionally, regardless of the target
player's actual spectator state — no error, no log line.

This collapses this function's three-way return above into a single, wrong constant: a script
testing for `1` (true spectator) or `2` (dead spectator) will never observe either value under
UZDoom, only ever the `0` case — indistinguishable, per this file's own "Return `0`" bullet, from
"genuinely not a spectator" or "invalid player index." The `DISCONNECT` example above would
misreport every real spectator as a disconnect.

Worth noting the trap is easy to miss in testing: a singleplayer session has no spectators anyway,
so `PlayerIsSpectator` returning `0` there looks coincidentally correct on both engines. See
[Zandronum/UZDoom compatibility](../concepts/zandronum-uzdoom-compat.md) for the general
reserved-ACSF-range mechanism and its other affected functions.
