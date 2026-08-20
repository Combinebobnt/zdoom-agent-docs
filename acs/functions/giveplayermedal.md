# `int GivePlayerMedal(int player, str medal, bool silent)`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-18)
**Provenance:** Zandronum Wiki page `GivePlayerMedal` (retrieved 2026-08-18, https://wiki.zandronum.com/w/index.php?title=GivePlayerMedal&oldid=2253) + source-verified against the Zandronum source's `src/p_acs.cpp:8900-8910` (case ACSF_GivePlayerMedal implementation) and `src/medal.cpp:412-487` (MEDAL_GiveMedal implementation), `zt-bcc/lib/zcommon.bcs:-179` (function signature in extension-function table).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (index −179 in `zcommon.bcs`'s `special` table; dispatched as `ACSF_GivePlayerMedal` in `src/p_acs.cpp:8900-8910`).

Awards a medal to a player. Server-side only; the function will always return `0` when called from a client or in single-player mode.

## Parameters

- **`player`**: player number (index) of the player to award the medal to. Must be a valid player index (0 through `MAXPLAYERS-1`).
- **`medal`**: the name of the medal to be awarded as a string. The medal must exist in the server's medal definition list; an invalid medal name causes the function to return `0`.
- **`silent`**: if `true`, suppresses the medal's visual and audio feedback — the medal is recorded as earned but not displayed on the screen, above the player's head, or accompanied by any medal sounds. If `false`, the normal medal announcements occur (subject to the `cl_medals` cvar on the receiving client and `ZADF_NO_MEDALS` admin flag on the server).

## Return value

Returns **`1`** on success (medal awarded), **`0`** on failure. Failure occurs when:

- The function is called from a client (or in single-player mode via `NETWORK_InClientMode()` check).
- The player index is invalid (out of range, player actor is null, or player disconnected).
- The medal name is invalid (not found in the server's medal list).
- The server has medals disabled via the `ZADF_NO_MEDALS` admin flag.
- The game mode is in a countdown phase or is configured so players don't earn medals (`GMF_PLAYERSEARNMEDALS` flag is not set).

## Server-side execution

This function enforces server-side execution: a client that calls `GivePlayerMedal` will receive an immediate return value of `0`, even if the player index and medal name are otherwise valid. This is a strict check in `src/p_acs.cpp:8902` via `NETWORK_InClientMode()` — any environment that is not the authoritative server (including spectators running a `CLIENTSIDE` script) cannot execute the medal award.

## Medal display behavior

The `silent` parameter controls client-side medal display logic (`src/medal.cpp:437`). When `silent` is `false`:
- The medal is queued for visual display on the player's client (subject to `cl_medals` cvar).
- The medal announcement is triggered (medal icon animation, associated sounds).
- If the player is a bot, the bot is notified via `BOTEVENT_RECEIVEDMEDAL`.

When `silent` is `true`, none of the client-side display occurs; the medal is only recorded internally as earned for statistics/event purposes.

If the server is in countdown or medals are administratively disabled, the medal is neither displayed nor recorded, regardless of the `silent` flag.

## Zandronum-specific: UZDoom absence

This function **exists only in Zandronum and has no UZDoom/GZDoom-family implementation.** It does not appear in any form in UZDoom's source (`src/playsim/p_acs.cpp` or `src/playsim/actionspecials.h`), and is not available to scripts compiled for or running on UZDoom-family engines. This is a Zandronum-specific multiplayer feature with no equivalent on other engine forks.

## See also

- `A_GivePlayerMedal` — the corresponding DECORATE action function that awards a medal to the calling actor's player.
