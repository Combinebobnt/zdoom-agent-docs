# `sv_timestampformat`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02), enum values verified against raw wiki HTML.

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

Default is 0 (24-hour HH:MM:SS).

## Enabling timestamps

This cvar only takes effect when `sv_timestamp` is set to true. If `sv_timestamp` is false, no timestamps are added to console output regardless of the format selected.

## Server logfile interaction

When a server logfile is enabled (`sv_logfiletimestamp`), timestamps appear on each line. The format specified by `sv_timestampformat` determines how those times are displayed in the log.

## Network and storage

This is a local server-side setting for console/log display only, not replicated to clients. Marked `0` in the flags (no special replication).

## Related cvars

- **`sv_timestamp`** — enables/disables timestamps in the server console (boolean on/off).
- **`sv_logfiletimestamp`** — enables timestamps in the logfile (boolean on/off).
- **`sv_logfiletimestamp_usedate`** — prepends the date (`YY:MM:DD`) to per-line timestamps.
