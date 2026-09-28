# `int GivePlayerMedal(int player, str medal, bool silent)`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** Zandronum Wiki page `GivePlayerMedal` (retrieved 2026-08-18, https://wiki.zandronum.com/w/index.php?title=GivePlayerMedal&oldid=2253) + source-verified against the Zandronum source's `src/p_acs.cpp:8900-8907` (case ACSF_GivePlayerMedal implementation) and `src/medal.cpp:412-487` (MEDAL_GiveMedal implementation), `wadsrc/static/gamemode.txt` (which modes set `PLAYERSEARNMEDALS`), `src/cl_main.cpp:4904-4907` and `protocolspec/spec.players.txt:273-277` (client side of the broadcast), `zt-bcc/lib/zcommon.bcs:-179` (function signature in extension-function table).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (index −179 in `zcommon.bcs`'s `special` table; dispatched as `ACSF_GivePlayerMedal` in `src/p_acs.cpp:8900-8907`).

Awards a medal to a player. It runs wherever the calling script runs except on a client: offline it awards locally, on a server it awards and tells clients, and on a client (or during client demo playback) it returns `0` without doing anything. In a stock cooperative, survival or invasion game (including ordinary single-player) it also returns `0`, because those game modes don't earn medals.

## Parameters

- **`player`**: player number (index) of the player to award the medal to. Must be a valid player index (0 through `MAXPLAYERS-1`).
- **`medal`**: the name of the medal to be awarded as a string. The medal must exist in the loaded MEDALDEF medal list; an unknown medal name causes the function to return `0`.
- **`silent`**: if `true`, suppresses the medal's visual and audio feedback. The medal is still counted as earned, but it is not queued for the on-screen display, no icon floats above the player's head and no medal sound plays. If `false`, a client (or an offline game) shows the normal announcement unless its `cl_medals` cvar is off. `silent` does not affect anything else: the `ZADF_NO_MEDALS` flag refuses the whole award either way (see below).

## Return value

Returns **`1`** on success (medal awarded), **`0`** on failure. Failure occurs when:

- The function is called on a client, or during client demo playback (`NETWORK_InClientMode()`).
- The game is in a countdown, or the current game mode lacks the `PLAYERSEARNMEDALS` flag. In stock `gamemode.txt` every mode sets it except Cooperative, Survival and Invasion.
- The player index is invalid (out of range, or the player has no body, e.g. not in the game).
- The medal name is invalid (not found in the medal list).
- Medals are disabled via the `ZADF_NO_MEDALS` flag.
- A `GAMEEVENT_MEDALS` `EVENT` script sets the event result to `0`, vetoing the award (`src/medal.cpp:430-432`).

## Where it runs

The only network gate in the function itself is the client check at `src/p_acs.cpp:8903`: a client script (including a `CLIENTSIDE` script) gets `0` even if the player index and medal name are otherwise valid. Offline, the award and its display happen locally. On a server, the award is applied and then broadcast with the `GivePlayerMedal` server command (`src/medal.cpp:482-484`), carrying the player, the medal index and the `silent` flag (`protocolspec/spec.players.txt:273-277`). Each client re-runs the same award routine with those values (`src/cl_main.cpp:4904-4907`), so the client's own countdown, game-mode and `ZADF_NO_MEDALS` checks and its `cl_medals` setting decide what it shows.

## Medal display behavior

Display is gated on three things at `src/medal.cpp:437`: the machine is not a server, `cl_medals` is on, and `silent` is `false`. When all hold:
- The medal is queued for visual display (replacing a lower medal of the same chain already in the queue).
- If it is at the front of the queue, the announcement is triggered (on-screen text and icon, the floating icon above the player, associated sounds).

When `silent` is `true`, none of the display occurs. The rest of the award still happens: the medal's awarded count goes up, a bot player is notified via `BOTEVENT_RECEIVEDMEDAL` (`src/medal.cpp:476-480`, regardless of `silent`), and a server still sends the command to clients.

If the game is in a countdown or medals are disabled, the medal is neither displayed nor recorded, regardless of the `silent` flag.

## Zandronum-specific: UZDoom absence

This function **exists only in Zandronum and has no UZDoom/GZDoom-family implementation.** It does not appear in any form in UZDoom's source (`src/playsim/p_acs.cpp` or `src/playsim/actionspecials.h`), and is not available to scripts compiled for or running on UZDoom-family engines. This is a Zandronum-specific multiplayer feature with no equivalent on other engine forks.

## See also

- `A_GivePlayerMedal` — the corresponding DECORATE action function that awards a medal to the calling actor's player.
