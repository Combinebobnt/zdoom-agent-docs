# `msg5color` (console cvar)

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `CVARs:Messages` (retrieved 2026-08-02, https://zdoom.org/w/index.php?title=CVARs%3AMessages&oldid=48195 — cvar not documented in the wiki) + verified against Zandronum source's `src/c_console.cpp:335-339` (declaration with default 21), `src/doomtype.h:143-147,154-156` (level 5 is `PRINT_PRIVATECHAT`), `src/chat.cpp:1017-1020,1087-1090` (private messages print at level 5), `src/v_font.h:47-70` (`EColorRange`, 21 = `CR_CYAN`) and `src/c_console.cpp:662-667` (`setmsgcolor` range check).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

## Zandronum-specific: private chat message color

This cvar is specific to Zandronum and does not appear in the ZDoom or GZDoom-family engines. It controls the color used to display private chat messages (message level 5, `PRINT_PRIVATECHAT`). That is distinct from public chat (level 3, `msg3color`) and team chat (level 4, `msg4color`). Every private message prints at level 5: messages you send or receive, `/me` lines inside a private message, and private messages to or from the server.

Default value: **21** (cyan).

The cvar is declared as `CUSTOM_CVAR (Int, msg5color, 21, CVAR_ARCHIVE)`, preceded by a comment identifying it as the private chat message color. The value is a text color index in the engine's `EColorRange` order (`CR_BRICK` = 0 through `CR_CYAN` = 21). Its callback stores the value as the level-5 print color. A value outside `0` to `NUM_TEXT_COLORS - 1` is stored as `0` (`CR_BRICK`) instead.

## Related cvars

- `msg3color` - public chat message color (level 3)
- `msg4color` - team chat message color (level 4)
- `msg` (C++ variable `msglevel`) - minimum message level to display

## Engine-family divergence

`msg5color` does not exist in UZDoom at all. UZDoom also has no private chat message level: its print levels stop at `PRINT_TEAMCHAT` (4), and level 5 there is `PRINT_LOG`. Team chat still has its own color in UZDoom via `msg4color`.

What happens when something tries to set it under UZDoom depends on the path:

- Typed at the console, or run from an `exec`'d `.cfg` script: prints `Unknown command "msg5color"` and changes nothing.
- A `msg5color` key in the engine's ini config file: loading the ini silently creates an auto-created string cvar of that name holding the value, with no message. The value has no effect on any chat color.
- ACS `ConsoleCommand()`: never reaches the console dispatcher. UZDoom prints its "doesn't support execution of console commands from scripts" message instead.
