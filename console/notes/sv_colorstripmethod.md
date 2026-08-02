# `sv_colorstripmethod`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02), enum values verified against raw wiki HTML.

Controls how color codes in server messages are displayed in the server console and logfile. This does not affect color codes sent to players in-game (client-side chat rendering is unaffected).

## Value modes

| Value | Behavior |
|-------|----------|
| 0 | Strips the color codes from messages. The `\cX` markers are removed, leaving plain text. |
| 1 | Allows color codes to pass through. The `\cX` markers are preserved and may be interpreted by a console/terminal that supports them. |
| 2 | Leaves the raw `\c<x>` format in messages (literal backslash-c-character). Useful for debugging color-code problems or for log parsing that needs to see which codes were used. |

Default is 0 (strip color codes).

## Log parsing and debugging

When building tools that parse server logfiles:
- Value 0: color codes are already stripped, so no further processing needed.
- Value 2: raw format is preserved, allowing tools to reconstruct the original colored text or detect color-code sequences for special handling.

## Network and storage

This is a local server-side setting for console/log display, not replicated to clients. Marked `0` in the flags column (no special replication).

## Related cvars

- **`sv_markchatlines`** — adds 'CHAT' tags to chat messages in the server console; works independently of color-strip behavior.
- **`sv_logfiletimestamp`** — adds timestamps to logfile lines; orthogonal to color-code handling.
