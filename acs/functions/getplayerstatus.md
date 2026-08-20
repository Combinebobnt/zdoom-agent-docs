# `int GetPlayerStatus(int player)`

**Tier:** A.
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-28)
**Provenance:** wiki page `GetPlayerStatus - Zandronum Wiki.html` (`_intake/`, retrieved
2026-07-28, `https://wiki.zandronum.com/w/index.php?title=GetPlayerStatus&oldid=2251`) + source-verified (`p_acs.cpp:8713-8716`, `d_player.h:271-280`,
`p_interaction.cpp:3006-3014`, `zcommon.bcs:1346-1352`, `sv_main.cpp:5066-5077`,
`voicechat.cpp:545-732`, `wi_stuff.cpp:2801`). The wiki's 5-flag bitmask and invalid-index-returns-0
behavior both check out exactly; the `READYTOGOON` sixth bit and the server-authoritative/sync
notes are this doc's source-verified additions, not from the wiki (the wiki page states no
examples and no caveats beyond the 5-flag table).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Returns a bitmask of a player's UI/network status flags (chatting, talking, in the console, in a
menu, lagging) — the same states the scoreboard/HUD use to draw a status icon above a player's
name. Extension function (`ACSF_GetPlayerStatus`, index -173 in `zcommon.bcs`), implementation at
the Zandronum source's `src/p_acs.cpp:8713-8716`.

```cpp
case ACSF_GetPlayerStatus:
{
    return PLAYER_IsValidPlayer( args[0] ) ? players[args[0]].statuses : 0;
}
```

- `player` — player number. Returns the raw `player_t::statuses` bitfield (`d_player.h:271-280`)
  unmodified — no masking, no filtering.
- **Invalid player → `0`.** `PLAYER_IsValidPlayer` (`p_interaction.cpp:3006-3014`) rejects both
  `player >= MAXPLAYERS` and `playeringame[player] == false`; `args[0]` (a signed `int`) is passed
  straight into a `const ULONG` parameter, so a negative index wraps to a huge unsigned value and
  still fails the bound check (no out-of-bounds read). Matches the wiki's stated behavior, but note
  this means "player 0 has no statuses set" and "player 0 doesn't exist" are indistinguishable from
  the return value alone — same ambiguity as `PlayerIsSpectator` (see `playerisspectator.md`).
- **The bitmask only has 5 named BCS constants, but the engine field has a 6th bit the wiki and
  `zcommon.bcs` both omit.** `zcommon.bcs:1346-1352` defines exactly:
  - `PLAYERSTATUS_CHATTING` = `1<<0` (`1`)
  - `PLAYERSTATUS_TALKING` = `1<<1` (`2`)
  - `PLAYERSTATUS_INCONSOLE` = `1<<2` (`4`)
  - `PLAYERSTATUS_INMENU` = `1<<3` (`8`)
  - `PLAYERSTATUS_LAGGING` = `1<<4` (`16`)

  but the engine's own enum (`d_player.h:271-280`) also has `PLAYERSTATUS_READYTOGOON = 1<<5`
  (`32`, "Player is ready for the next map? (intermission)"), which is set during intermission
  (`wi_stuff.cpp:2801`, `p_interaction.cpp:2941`) and readable through this exact same `statuses`
  field. **`GetPlayerStatus` can and will return bit `32` set with no BCS constant name for it** —
  a script masking against only the 5 documented constants will still see the raw value include
  it, so `GetPlayerStatus(p) & 31` is the safe way to check only the "UI activity" bits the wiki
  describes, if `READYTOGOON` isn't wanted.
- **Not a pure clientside read — the field is server-authoritative and synced.** `statuses` lives
  in `player_t` and is replicated: the server masks a subset (`CHATTING|INCONSOLE|INMENU`,
  `sv_main.cpp:5066-5077`) from client status updates, sets `LAGGING`/`READYTOGOON` itself
  server-side, and `TALKING` is toggled by the voice-chat subsystem (`voicechat.cpp:545-732`,
  `cl_main.cpp:4441-4447`). Practical effect: calling `GetPlayerStatus` from a server-run script
  (the normal case for map/library scripts) sees the server's up-to-date view of other
  players' statuses, not just the local client's own — it isn't restricted to `consoleplayer`.

**Returns:** `int` — bitmask of `PLAYERSTATUS_*` (see above; may include the undocumented `32`/
`READYTOGOON` bit during intermission), or `0` for an invalid/not-in-game player index.

## Engine-family divergence

`GetPlayerStatus` is bound as ACSF index 173 (`-173:GetPlayerStatus(int):int` in `zcommon.bcs`),
inside the 100-199 range UZDoom reserves for Zandronum's own extensions and implements none of.
UZDoom's `CallFunction` dispatcher falls through the `default: break;` case for that index with no
error and no log line — a Zandronum-compiled object calling `GetPlayerStatus` under UZDoom always
gets `0` back, regardless of the target player's real chat/console/menu/lag state.

That `0` is a plausible-looking wrong answer, not an obviously broken one: `0` is also the correct
return for a player with no `PLAYERSTATUS_*` bits set — the ordinary, most-common case (not
chatting, not talking, not in the console or a menu, not lagging). A script polling this function
under UZDoom will silently see "no status flags" for every player, every time, including the ones
that actually are chatting or lagging, and nothing distinguishes that from a genuinely idle player
without cross-checking on Zandronum. See [Zandronum/UZDoom
compatibility](../concepts/zandronum-uzdoom-compat.md) for the general reserved-ACSF-range
mechanism this is an instance of.
