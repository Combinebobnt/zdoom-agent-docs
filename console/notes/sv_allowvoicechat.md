# `sv_allowvoicechat`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02) for the value-mode description; Zandronum source voice-chat implementation and version ancestry (commit `50f4ac1e5` vs. the 3.2.1 version-bump commit `28f736fb3`) to correct the wiki's version-availability claim. Zandronum source backing the mode, flag and storage corrections: `src/voicechat.cpp:193` (declaration, flags, clamp), `src/voicechat.h:72` (mode enum), `src/sv_commands.cpp:1286` (server-side packet relay filter) and `:201` (`PlayersAreTeammates`), `src/voicechat.cpp:686` and `:1100` (client transmit gate), `src/sv_commands.cpp:2570` / `src/cl_main.cpp:6279` (settings sync), `src/sv_master.cpp:490` (launcher field), `src/gameconfigfile.cpp:576` (server-cvar archive filter), `docs/zandronum-history.txt:107` (listed under 3.2).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Controls whether voice chat is enabled and who can communicate via voice. Four modes control voice-chat scope: disabled, all players, teammates only, or separate player/spectator channels.

## Wiki/engine divergence: version availability

The Zandronum Wiki page states "development version 3.2-alpha and above only." The version floor is right, but the "development version" qualifier is stale: voice chat is not limited to development builds. Voice chat support (commit `50f4ac1e5`, "Added support for voice chat") is listed under the 3.2 release in `docs/zandronum-history.txt` and is an ancestor of the 3.2.1 version-bump commit (`28f736fb3`), so voice chat **is available in released Zandronum 3.2.1**. So are mode 3 (commit `883df573b`) and the launcher-query field (commit `276d00bdc`). No commit after `28f736fb3` adds or removes a use of the cvar.

## Value modes

Default is 1. Out-of-range values are clamped to 0-3. The mode filters are applied on the server as it relays each voice packet, alongside each client's own transmit/listen filters and the last-man-standing rule that can bar spectators from talking to live players.

- **0:** Voice chat completely disabled. The server relays no voice packets, and a client pressing the voice key is told the server has disabled voice chat.
- **1:** No mode restriction: everyone can voice chat with everyone, players and spectators alike.
- **2:** Teammates only, in team game modes. A packet reaches only the sender's teammates. True spectators count as each other's teammates, so spectators can still talk among themselves, just not to players on a team. In game modes without teams this mode imposes no restriction and behaves like 1.
- **3:** Live players and spectators (dead spectators included) voice chat separately. A packet is never relayed from a player to a spectator or the reverse.

## Related proximity-voice cvars

Voice chat can be configured as proximity-based (local range) using:
- **`sv_proximityvoicechat`** — enable proximity mode (players only hear voice in nearby map range).
- **`sv_minproximityrolloffdist`** — distance at which proximity voice begins fading (becomes quieter).
- **`sv_maxproximityrolloffdist`** — distance at which proximity voice is no longer audible.

When `sv_proximityvoicechat` is false, voice chat is global (heard across the entire map regardless of player position).

## Network and storage

Declared `CVAR_NOSETBYACS | CVAR_SERVERINFO` (no `CVAR_GAMEPLAYSETTING`, no `CVAR_ARCHIVE`). The server sends the value to clients in its game-settings command at connect time and again whenever the cvar changes, and the client force-sets its local copy. It is also reported to launcher queries as the `SQF2_VOICECHAT` field. `CVAR_NOSETBYACS` means ACS's `ConsoleCommand()` cannot change it. Because it lacks `CVAR_ARCHIVE`, it is **not** saved to the config file; set it on the server's command line or in a config it executes at startup.

## Related cvars

- **`sv_proximityvoicechat`** — enable proximity-based (map-range-limited) voice chat.
- **`sv_minproximityrolloffdist`** — proximity voice rolloff distance (begin fade).
- **`sv_maxproximityrolloffdist`** — proximity voice max distance (silence threshold).

## Engine-family divergence

`sv_allowvoicechat` does not exist in UZDoom at all — confirmed absent from the engine's source (no
matching `CVAR`/`CUSTOM_CVAR` declaration, and no bare mention of the name anywhere in the tree),
not merely undocumented.

Setting it under UZDoom from the console or a config file prints
`Unknown command "sv_allowvoicechat"` to the console/log and does nothing else: visible if
someone's watching the console at the time, easy to miss if triggered from an unattended server
startup script, since the attempted write silently fails to apply and no cvar of this name is ever
created. ACS's `ConsoleCommand()` never reaches the console dispatcher on UZDoom; it only prints
"UZDoom doesn't support execution of console commands from scripts" (`src/playsim/p_acs.cpp`) and
does nothing else. Consequently a UZDoom server has no cvar-driven way to enable or scope in-game voice chat
(all-players, teammates-only, or split player/spectator channels) the way Zandronum does — the
entire mode-selection mechanism this cvar exposes is simply absent on UZDoom.
