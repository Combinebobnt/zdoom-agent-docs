# `sv_timestampformat`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02), enum values verified against raw wiki HTML. Zandronum 3.3-alpha @bdd0f7beb: declaration and flags `src/sv_main.cpp:277-278`; formats and gating `src/win32/serverconsole/serverconsole.cpp:2237-2254`; logfile stamp `src/c_console.cpp:248-251, 1069-1081`; non-Windows console path `src/platform.cpp:93-97` with `NO_SERVER_GUI` set at `src/CMakeLists.txt:277-278`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Selects the time format for timestamps in the server console when `sv_timestamp` is enabled. Does not affect in-game HUD time display.

## Value modes

| Value | Format | Example |
|-------|--------|---------|
| 0 | Hours:Minutes:Seconds (24-hour) | `14:32:07` |
| 1 | Hours:Minutes:Seconds AM/PM | `02:32:07 PM` |
| 2 | Hours:Minutes:Seconds am/pm (lowercase) | `02:32:07 pm` |
| 3 | Hours:Minutes (24-hour) | `14:32` |
| 4 | Hours:Minutes AM/PM | `02:32 PM` |
| 5 | Hours:Minutes am/pm (lowercase) | `02:32 pm` |

Default is 0 (24-hour HH:MM:SS). The stamp is written in brackets with a trailing space, e.g. `[14:32:07] `. There is no range check: the value indexes the six-entry format table directly, so a value outside 0-5 set from the console reads past the table. The GUI's settings dialog only offers 0-5.

## Enabling timestamps

This cvar only takes effect when `sv_timestamp` is set to true. If `sv_timestamp` is false, no timestamps are added to console output regardless of the format selected. Stamps are also only added while `gamestate` is `GS_LEVEL`, so startup output before the first map loads carries none.

## Windows server console only

The only consumer is the Windows GUI server console. Non-Windows builds define `NO_SERVER_GUI`, and their stub server-console print writes each line to stdout with colors stripped and no timestamp. On a Linux server `sv_timestamp` and `sv_timestampformat` therefore have no effect.

## Server logfile interaction

`sv_timestampformat` does not affect the logfile. Logfile timestamps are controlled by `sv_logfiletimestamp` and always use a fixed 24-hour format: `[HH:MM:SS] `, or `[YY:MM:DD;HH:MM:SS] ` when `sv_logfiletimestamp_usedate` is on.

## Network and storage

This is a local server-side setting for console display only. Flags are `CVAR_ARCHIVE|CVAR_NOSETBYACS`: it is saved to the config, cannot be set from ACS, and is not `CVAR_SERVERINFO`, so it is not replicated to clients.

## Related cvars

- **`sv_timestamp`** — enables/disables timestamps in the server console (boolean on/off).
- **`sv_logfiletimestamp`** — enables timestamps in the logfile (boolean on/off).
- **`sv_logfiletimestamp_usedate`** — prepends the date (`YY:MM:DD`) to per-line logfile timestamps.

## Engine-family divergence

`sv_timestampformat` does not exist in UZDoom at all — confirmed absent from source, not merely undocumented. Attempting to set it under UZDoom via the console or a config file prints `Unknown command "sv_timestampformat"` to console/log and the write silently fails to apply: a visible failure if someone is watching the console at the time, but easy to miss in an unattended context such as a server startup script or an `autoexec.cfg` line. ACS's `ConsoleCommand()` never reaches the console dispatcher on UZDoom; it only prints "UZDoom doesn't support execution of console commands from scripts" (`src/playsim/p_acs.cpp`) and does nothing else.

UZDoom has no equivalent cvar for selecting between the six 12/24-hour timestamp formats this cvar switches between, so a server operator relying on this to format server console timestamps for downstream log-parsing tooling has no configuration knob for that on UZDoom at all.
