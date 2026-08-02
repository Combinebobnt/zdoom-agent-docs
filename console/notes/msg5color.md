# `msg5color` (console cvar)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `CVARs:Messages` (retrieved 2026-08-02, oldid=48195 — cvar not documented in the wiki) + verified against Zandronum source's `src/c_console.cpp:335-339` (declaration with default 21).

## Zandronum-specific: private chat message color

This cvar is specific to Zandronum and does not appear in the ZDoom or GZDoom-family engines. It controls the color used to display private/team chat messages (message level 5), distinct from public chat (level 3).

Default value: **21** (cyan).

The cvar is declared as `CUSTOM_CVAR (Int, msg5color, 21, CVAR_ARCHIVE)` with an inline comment identifying it as a private chat message color. See the `TEXTCOLOR` encoding table in the parent section's inventory for the color code meanings.

## Related cvars

- `msg3color` — public chat message color (level 3)
- `msg4color` — team chat message color (level 4)
- `msglevel` (`msg`) — minimum message level to display
