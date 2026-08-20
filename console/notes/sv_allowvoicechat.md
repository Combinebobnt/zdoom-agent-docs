# `sv_allowvoicechat`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02) for the value-mode description; Zandronum source voice-chat implementation and version ancestry (commit `50f4ac1e5` vs. the 3.2.1 version-bump commit `28f736fb3`) to correct the wiki's version-availability claim.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Controls whether voice chat is enabled and who can communicate via voice. Four modes control voice-chat scope: disabled, all players, teammates only, or separate player/spectator channels.

## Wiki/engine divergence: version availability

The Zandronum Wiki page states "development version 3.2-alpha and above only," implying voice chat is unavailable in released Zandronum 3.2.1. This is **incorrect**. Voice chat support was committed to the Zandronum codebase (commit `50f4ac1e5`, "Added support for voice chat") before the 3.2.1 version-bump commit (`28f736fb3`), and voice chat **is available in released Zandronum 3.2.1**. The wiki description is likely stale or describes an earlier development snapshot where voice-chat features were still in alpha.

## Value modes

- **0:** Voice chat completely disabled.
- **1:** All players can voice chat with all other players and spectators (no team restriction).
- **2:** Players can only voice chat with teammates; spectators cannot use voice chat in this mode.
- **3:** Voice chat streams are separate — players have one channel, spectators have another, with no cross-channel communication.

## Related proximity-voice cvars

Voice chat can be configured as proximity-based (local range) using:
- **`sv_proximityvoicechat`** — enable proximity mode (players only hear voice in nearby map range).
- **`sv_minproximityrolloffdist`** — distance at which proximity voice begins fading (becomes quieter).
- **`sv_maxproximityrolloffdist`** — distance at which proximity voice is no longer audible.

When `sv_proximityvoicechat` is false, voice chat is global (heard across the entire map regardless of player position).

## Network and storage

Marked `CVAR_SERVERINFO | CVAR_GAMEPLAYSETTING`, so the value replicates to clients and is treated as a gameplay-affecting setting. Persists to config file.

## Related cvars

- **`sv_proximityvoicechat`** — enable proximity-based (map-range-limited) voice chat.
- **`sv_minproximityrolloffdist`** — proximity voice rolloff distance (begin fade).
- **`sv_maxproximityrolloffdist`** — proximity voice max distance (silence threshold).

## Engine-family divergence

`sv_allowvoicechat` does not exist in UZDoom at all — confirmed absent from the engine's source (no
matching `CVAR`/`CUSTOM_CVAR` declaration, and no bare mention of the name anywhere in the tree),
not merely undocumented.

Setting it under UZDoom — from the console, a config file, or ACS's `ConsoleCommand()` — prints
`Unknown command "sv_allowvoicechat"` to the console/log and does nothing else: visible if
someone's watching the console at the time, easy to miss if triggered from an unattended server
startup script, since the attempted write silently fails to apply and no cvar of this name is ever
created. Consequently a UZDoom server has no cvar-driven way to enable or scope in-game voice chat
(all-players, teammates-only, or split player/spectator channels) the way Zandronum does — the
entire mode-selection mechanism this cvar exposes is simply absent on UZDoom.
