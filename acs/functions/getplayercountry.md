# `str GetPlayerCountry(int player, int type)`

**Tier:** A
**Engine:** Zandronum 3.2.1 — confirmed present: the introducing commit `624c7a394` ("Added ACS function: \"GetPlayerCountry\"...", 2024-03-11) is an ancestor of the 3.2.1 version-bump commit `28f736fb3` (2025-08-04) in the Zandronum source's checkout, so this predates the 3.2.1 target rather than being a post-3.2.1 addition.
**Provenance:** wiki page `GetPlayerCountry - Zandronum Wiki.html` (`_intake/`, retrieved 2026-07-29, `oldid=2247`) + source-verified (`p_acs.cpp:8853-8879`, `p_interaction.cpp:3006-3014`, `network.cpp:1137-1183`, `network.h:261`, `bots.cpp:1770`, `g_level.cpp:604`, `cl_main.cpp:3832,4392`, `sv_main.cpp:1774`). The wiki's core behavior (three format constants, `"N/A"` for unknown/hidden, `"LAN"` for bots/local network) holds; the exact mechanics below (player-validity gate, what actually sets `ulCountryIndex`, and the client-vs-server split) are this doc's source-verified additions.
**Bucket:** extension function.

Returns the country a player's client is connecting from, in one of three string formats.
Extension function (`ACSF_GetPlayerCountry`, index `-177` in `zcommon.bcs`), implementation in
the Zandronum source's `src/p_acs.cpp:8853-8879`.

- `player` — a player index. Validated with `PLAYER_IsValidPlayer` (`p_interaction.cpp:3006-3014`:
  rejects `player >= MAXPLAYERS` or a slot with `playeringame[player] == false`). **Any invalid
  player index silently falls through to the final `return "N/A"`** — same fail-closed pattern as
  other player-indexed ACSFs in this fork (e.g. `PlayerIsBot`), not called out by the wiki.
- `type` — output format, matching the wiki exactly (values verified against the `enum` inside the
  `ACSF_GetPlayerCountry` case itself, `p_acs.cpp:8854-8859`):
  - `PLAYERCOUNTRY_ALPHA2` (`0`) — ISO 3166-1 alpha-2 code, e.g. `CA`.
  - `PLAYERCOUNTRY_ALPHA3` (`1`) — ISO 3166-1 alpha-3 code, e.g. `CAN`.
  - `PLAYERCOUNTRY_NAME` (`2`) — full country name, e.g. `Canada`.
  - These constants are **not** defined in `zcommon.bcs`/BCS headers — they only exist as a local
    `enum` inside the C++ case statement. A calling script must define its own matching constants
    (or just pass the literal `0`/`1`/`2`) since `bcc`/`zt-bcc` has no built-in for them.
  - Any other `type` value falls through both `if`/`else if` branches with no explicit `return`
    inside that block, so it also ends up returning `"N/A"` via the function's final fallback —
    not a distinct error path, just the same catch-all.
- **`"LAN"` is returned via a real sentinel value, not a special-cased string compare on the
  caller's data:** `ulCountryIndex` is set to `COUNTRYINDEX_LAN` (`network.h:261`, `= UCHAR_MAX`)
  for bots (`bots.cpp:1770`), the local/console player in singleplayer or a listen-server host
  (`g_level.cpp:604`, `cl_main.cpp:3832`), and any server-side connection whose IP is in a private
  range — `172.16.0.0`-`172.31.255.255`, `10.0.0.0/8`, `192.168.0.0/16`, or `127.0.0.0/8`
  (`network.cpp:1137-1153`, `NETWORK_GetCountryIndexFromAddress`). The shared string-lookup helper
  (`network_GetCountryStringFromIndex`, `network.cpp:1161-1169`) special-cases exactly this sentinel
  to return the literal string `"LAN"` before ever consulting GeoIP, for all three `type` values.
- **`"N/A"` covers three distinct cases**, all converging on the same string: (1) the player has
  `ulCountryIndex == 0` (never resolved — e.g. GeoIP database isn't loaded server-side,
  `NETWORK_IsGeoIPAvailable()` false, `network.cpp:1149-1150`, or the client hasn't sent/been
  assigned a country yet), (2) the requesting side is the server and that player's
  `bWantHideCountry` is set (`cl_hidecountry`, checked at `p_acs.cpp:8866`), or (3) GeoIP resolves
  the index but returns a null/empty string (`network.cpp:1166-1168`). The function itself only
  guards case (1)/(2) explicitly; case (3) is handled one layer down in
  `network_GetCountryStringFromIndex`.
- **Country resolution only happens server-side, from the connecting IP** — `sv_main.cpp:1774`
  calls `NETWORK_GetCountryIndexFromAddress` once per connecting client using
  `SERVER_GetClient(...)->Address`. A client-side script asking about another player still reads
  whatever `ulCountryIndex` the server replicated to it; it isn't independently resolved
  per-caller.
- Return value is added to the transient ACS string table via `GlobalACSStrings.AddString(...)`
  like any other ACS-returned string (`p_acs.cpp:8872,8875,8878`) — no special lifetime caveat
  beyond the usual ACS string-table rules.

**Example:**

```
str country = GetPlayerCountry(playernumber, 0); // e.g. "CA", "LAN", or "N/A"
```

**Returns:** `str` — the country in the requested format, `"LAN"` for bots/local-network/loopback
connections, or `"N/A"` for an invalid player index, a hidden (`cl_hidecountry`) country as seen
from the server, or an unresolved/unrecognized GeoIP lookup.
