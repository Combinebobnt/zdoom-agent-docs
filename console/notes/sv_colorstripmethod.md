# `sv_colorstripmethod`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02), enum values verified against raw wiki HTML.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

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

## Engine-family divergence

`sv_colorstripmethod` does not exist in UZDoom at all — confirmed absent from the engine's source
(no matching `CVAR`/`CUSTOM_CVAR` declaration, and no bare mention of the name anywhere in the
tree), not merely undocumented.

Setting it under UZDoom — from the console, a config file, or ACS's `ConsoleCommand()` — prints
`Unknown command "sv_colorstripmethod"` to the console/log and does nothing else: visible if
someone's watching the console at the time, easy to miss if triggered from an unattended server
startup script, since the attempted write silently fails to apply and no cvar of this name is ever
created. Consequently a UZDoom server administrator has no cvar-driven control over how `\cX` color
codes appear in the server console/logfile — there is no strip/passthrough/raw-format toggle to
choose from, so any log-parsing tooling built around this cvar's modes has nothing to configure on
UZDoom.
