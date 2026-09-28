# `msg` (console cvar)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-16); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `CVARs:Messages` (retrieved 2026-08-02, https://zdoom.org/w/index.php?title=CVARs%3AMessages&oldid=48195 — describes message levels but not the cvar itself) + verified against Zandronum source's `src/c_console.cpp:307`, `src/c_console.cpp:1022`, `src/c_console.cpp:687`, `src/doomtype.h:151-159` and `src/chat.cpp:1016-1021,1043-1050,1076-1079,1176-1180`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

## Message-level filter (minimum severity to display)

This integer cvar controls the minimum message priority/severity level that will be displayed. Any message with a lower priority than this value is suppressed.

How much is suppressed differs by engine. On Zandronum, a message below `msg` is dropped before it reaches anything: it never appears in the console, the HUD notify area or the log file (`PrintString`, `src/c_console.cpp:1022`). Zandronum's chat sound is also skipped for a chat line below `msg` (`src/chat.cpp:1180`). On UZDoom, the filter only keeps the message out of the HUD notify area; the console and log file still get it.

**Declared in source:** the internal C++ name is `msglevel` on both engines, but the cvar name visible to users is `msg`. Zandronum declares it as `FIntCVar msglevel ("msg", 0, CVAR_ARCHIVE)` (`src/c_console.cpp:307`).

**Default:** 0 (show all messages, starting with item pickups)

## Message levels

The wiki page `CVARs:Messages` describes the message-level enumeration but does not document the cvar itself by name. The levels are:

- **0** — Item pickup (the default `msg` value of 0 shows every level)
- **1** — Obituaries (kill messages)
- **2** — Critical messages (typically printed via ACS/BCS `Log` or DECORATE `A_Log`/`A_LogInt`)
- **3** — Chat messages (public chat)
- **4** — Team chat messages

Zandronum adds **level 5** (private chat messages); see `msg5color` for details. On Zandronum, `/me` lines in public or team chat, and non-private messages from the server console, print at level 2 rather than 3 or 4 (`src/chat.cpp:1016-1021,1043-1050,1076-1079`), so `msg 3` hides them.

## Interaction with other cvars

- `show_messages`: if false, hides every message from the HUD notify area regardless of `msg` level. Messages still reach the console (`src/c_console.cpp:687`).
- `msg0color`, `msg1color`, `msg2color`, `msg3color`, `msg4color` — set colors per level
- `msg5color` — color for level 5 (private chat)

## Known limitation

This cvar sets a *minimum* level, not an enumerated mask. You cannot suppress level 2 (critical) while showing level 3 (chat) — setting `msg` to 2 suppresses levels 0 and 1 (pickups and obituaries) while allowing 2, 3 and 4 through (and 5 on Zandronum).
