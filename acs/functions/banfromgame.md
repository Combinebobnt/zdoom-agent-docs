# `int BanFromGame(int player, int duration[, str reason])`

**Tier:** A.
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** Zandronum Wiki page `BanFromGame` (retrieved 2026-08-18, https://wiki.zandronum.com/w/index.php?title=BanFromGame&oldid=2241) + source-verified against the Zandronum source's `src/p_acs.cpp:8695-8711` (case ACSF_BanFromGame implementation) and `src/p_acs.cpp:104-109` (sv_maxacsbanduration cvar definition), `src/sv_ban.cpp:498-508` and `src/sv_ban.cpp:512-561` (bot rejection, IP ban and kick), `zt-bcc/lib/zcommon.bcs:1800` (function signature in extension-function table).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (index −172 in `zcommon.bcs`'s `special` table; dispatched as `ACSF_BanFromGame` in `src/p_acs.cpp:8695-8711`).

Temporarily bans a player from the server. This server-side only function works only if `sv_maxacsbanduration` is configured to allow bans (a value greater than zero; the default is 0, which forbids the function). The cvar is `CVAR_NOSETBYACS`, so a script can't enable bans for itself, and a negative value is reset to 0.

The ban is by IP address: the player's address is added to the first ban list file (file index 0) with the given reason, the player is kicked with that reason as the kick message, and any other connected client whose address is now banned is kicked too (`src/sv_ban.cpp:498-508`, `512-561`).

## Parameters

- **`player`**: 0-based player number (as returned by `PlayerNumber()`), not a thing ID. Must be a player slot that is in the game. Bots can't be banned (see Return value).
- **`duration`**: the duration of the ban in minutes. Will be clamped to the range `[1, sv_maxacsbanduration]` — i.e., at least 1 minute, and no longer than the server's configured maximum ban duration.
- **`reason`** (optional): a ban reason string, also used as the kick message. If omitted, the ban is recorded without a reason and the kick message is empty.

## Return value

Returns **`0`** when not running on a server, when `sv_maxacsbanduration` is 0, or when `player` is out of range or not in the game. Otherwise it returns **`1`**, even if the ban itself then fails: a bot target is rejected inside the ban routine (the server console prints `Error: bad player index, or player is a bot.`) and nothing is banned, but the function still returns 1 (`src/sv_ban.cpp:498-508`). Check the target isn't a bot (`PlayerIsBot()`) before treating 1 as success.

## Server-side execution

This function is server-side only. It will always return 0 on a client or single-player machine, regardless of other conditions. The `NETSTATE_SERVER` check in `src/p_acs.cpp:8698` enforces this — a script running in single-player or as a client cannot execute the ban, even if the player index is valid.

The duration clamping logic is hard-coded to assume minutes; the Zandronum source (`src/p_acs.cpp:8705`) formats the clamped duration as `"%dmin"` when constructing the ban string passed to `SERVERBAN_BanPlayer`, so specifying a duration of (for example) 60 results in a 60-minute ban, not a 60-second one.

## Zandronum-specific: UZDoom absence

This function **exists only in Zandronum and has no UZDoom/GZDoom-family implementation.** It does not appear in any form in UZDoom's source (`src/playsim/p_acs.cpp` or `src/playsim/actionspecials.h`), and is not available to scripts compiled for or running on UZDoom-family engines. This is a Zandronum-specific multiplayer server function with no equivalent on other engine forks.

## Wiki/engine divergence: cvar name error

**The Zandronum Wiki page lists the wrong cvar name in its parameter description.** The page states:

> Will be clamped in the range of 1 to `sv_allowacsbanfunction`.

This is incorrect. The actual Zandronum source (`src/p_acs.cpp:8703`) clamps against **`sv_maxacsbanduration`**, not `sv_allowacsbanfunction`. There is no cvar named `sv_allowacsbanfunction` in the Zandronum source. The function requires `sv_maxacsbanduration > 0` (line 8698) to execute at all, and the clamped duration range is `[1, sv_maxacsbanduration]` (line 8703). This doc's parameter description above corrects this to match the actual engine behavior.

## See also

- `KickFromGame` — server function to kick (but not ban) a player from the server immediately.
