# `sv_colorstripmethod`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02), enum values verified against raw wiki HTML. Zandronum source: declaration `src/sv_main.cpp:279`; mode handling `V_StripColors` in `src/v_text.cpp:450-471`, called only from `SERVERCONSOLE_Print` (`src/platform.cpp:93-97` for GUI-less builds, `src/win32/serverconsole/serverconsole.cpp:2258-2260` for the Win32 server window); console print path in `src/c_console.cpp` (logfile copy always stripped at 1064-1065, RCON sent unstripped at 1115, console print at 1120); `TEXTCOLOR_ESCAPE` in `src/v_text.h:46`; `sv_markchatlines` at `src/sv_main.cpp:282,1312`; `sv_logfiletimestamp` at `src/c_console.cpp:248,1069`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Controls how color codes in messages are displayed in the server console: the Win32 server window, or standard output on a GUI-less dedicated server. It does not affect the logfile, which always has color escapes stripped (see below). It also does not affect RCON clients, which receive each line before it is stripped, or color codes sent to players in-game.

## Value modes

| Value | Behavior |
|-------|----------|
| 0 | Strips color codes. Literal `\cX` text is first converted to the engine's color escape, then every color escape is removed along with its color character (or `[name]` bracket), leaving plain text. |
| 1 | Keeps color codes. Literal `\cX` text is converted to the engine's internal color escape byte (`TEXTCOLOR_ESCAPE`, byte 0x1C) followed by the color character, and nothing is removed. The console receives the raw escape byte, which an ordinary terminal does not render as color. |
| 2 | Leaves the message unchanged, in whatever form it arrived. Literal `\c<x>` text stays literal, but a message the engine had already colorized keeps its raw 0x1C escape bytes rather than `\c` text. Any value other than 0 or 1 behaves like 2. |

Default is 0 (strip color codes).

## Log parsing and debugging

The logfile is not controlled by this cvar. Every line written to the logfile is passed through the engine's color-code remover first, regardless of the value, so color escapes never reach it. Literal `\c` text that was never converted to an escape is not touched by that remover and passes through as written.

Tooling that needs to see color codes has to read the console stream instead. On a GUI-less server that is standard output, with this cvar at 1 or 2.

## Network and storage

This is a local server-side setting for console display, not replicated to clients. Marked `0` in the flags column (no special replication). Zandronum declares it `CVAR_ARCHIVE`, so it persists to the config file.

## Related cvars

- **`sv_markchatlines`** — adds 'CHAT' tags to chat messages in the server console; works independently of color-strip behavior.
- **`sv_logfiletimestamp`** — adds timestamps to logfile lines; orthogonal to color-code handling.

## Wiki/engine divergence: logfile

The Zandronum Wiki describes this cvar as governing the server console and the logfile. In Zandronum source it governs only the console print path. The logfile copy of each line is always stripped of color escapes, and has been since 2010 (commit `1af0e5ced`, well before 3.2.1).

## Engine-family divergence

`sv_colorstripmethod` does not exist in UZDoom at all — confirmed absent from the engine's source
(no matching `CVAR`/`CUSTOM_CVAR` declaration, and no bare mention of the name anywhere in the
tree), not merely undocumented.

Setting it under UZDoom from the console or a config file prints
`Unknown command "sv_colorstripmethod"` to the console/log and does nothing else: visible if
someone's watching the console at the time, easy to miss if triggered from an unattended server
startup script, since the attempted write silently fails to apply and no cvar of this name is ever
created. ACS's `ConsoleCommand()` never reaches the console dispatcher on UZDoom; it only prints
"UZDoom doesn't support execution of console commands from scripts" (`src/playsim/p_acs.cpp`) and
does nothing else. Consequently a UZDoom server administrator has no cvar-driven control over how `\cX` color
codes appear in the server console/logfile — there is no strip/passthrough/raw-format toggle to
choose from, so any console-output tooling built around this cvar's modes has nothing to configure
on UZDoom.
