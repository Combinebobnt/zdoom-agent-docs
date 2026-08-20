# `msg5color` (console cvar)

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** ZDoom Wiki `CVARs:Messages` (retrieved 2026-08-02, https://zdoom.org/w/index.php?title=CVARs%3AMessages&oldid=48195 — cvar not documented in the wiki) + verified against Zandronum source's `src/c_console.cpp:335-339` (declaration with default 21).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

## Zandronum-specific: private chat message color

This cvar is specific to Zandronum and does not appear in the ZDoom or GZDoom-family engines. It controls the color used to display private/team chat messages (message level 5), distinct from public chat (level 3).

Default value: **21** (cyan).

The cvar is declared as `CUSTOM_CVAR (Int, msg5color, 21, CVAR_ARCHIVE)` with an inline comment identifying it as a private chat message color. See the `TEXTCOLOR` encoding table in the parent section's inventory for the color code meanings.

## Related cvars

- `msg3color` — public chat message color (level 3)
- `msg4color` — team chat message color (level 4)
- `msglevel` (`msg`) — minimum message level to display

## Engine-family divergence

`msg5color` does not exist in UZDoom at all — confirmed absent from the engine's source (no
matching `CVAR`/`CUSTOM_CVAR` declaration, and no bare mention of the name anywhere in the tree),
not merely undocumented.

Setting it under UZDoom — from the console, a config file, or ACS's `ConsoleCommand()` — prints
`Unknown command "msg5color"` to the console/log and does nothing else: visible if someone's
watching the console at the time, easy to miss if triggered from an unattended context such as a
saved client config file, since the attempted write silently fails to apply and no cvar of this
name is ever created. Consequently a UZDoom client has no way to independently recolor private/team
chat text (message level 5) apart from public chat — whatever color public chat uses is what
private chat gets too, since the level-5-specific override this cvar provides doesn't exist there.
