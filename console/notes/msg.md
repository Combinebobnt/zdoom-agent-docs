# `msg` (console cvar)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-16); Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** ZDoom Wiki `CVARs:Messages` (retrieved 2026-08-02, https://zdoom.org/w/index.php?title=CVARs%3AMessages&oldid=48195 — describes message levels but not the cvar itself) + verified against Zandronum source's `src/c_console.cpp:308`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

## Message-level filter (minimum severity to display)

This integer cvar controls the minimum message priority/severity level that will be displayed. Any message with a lower priority than this value is suppressed.

**Declared in source:** `FIntCVar msglevel ("msg", 0, CVAR_ARCHIVE)` — note that the internal name is `msglevel` but the cvar name visible to users is `msg`.

**Default:** 0 (show all messages, starting with item pickups)

## Message levels

The wiki page `CVARs:Messages` describes the message-level enumeration but does not document the cvar itself by name. The levels are:

- **0** — Item pickup (default, always shown unless `show_messages` is false)
- **1** — Obituaries (kill messages)
- **2** — Critical messages (typically printed via `Log`, `A_Log`, `A_LogInt` in ACS/BCS)
- **3** — Chat messages (public chat)
- **4** — Team chat messages

Zandronum adds **level 5** (private chat messages) — see `msg5color` for details.

## Interaction with other cvars

- `show_messages` — suppresses all message display if false, regardless of `msg` level
- `msg0color`, `msg1color`, `msg2color`, `msg3color`, `msg4color` — set colors per level
- `msg5color` — color for level 5 (private chat)

## Known limitation

This cvar sets a *minimum* level, not an enumerated mask. You cannot suppress level 2 (critical) while showing level 3 (chat) — setting `msg` to 2 suppresses levels 0 and 1 (pickups and obituaries) while allowing 2, 3, 4, and 5 through.
