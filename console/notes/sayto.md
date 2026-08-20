# `sayto` / `sayto_idx`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, retrieved 2026-08-02); verified against `src/chat.cpp:1999-2040` (sayto/sayto_idx CCMD implementations).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Send a private message to a specific player by name or player index. The server itself can be targeted with a magic constant.

## Syntax

- `sayto <player_name_or_magic> <message>`
- `sayto_idx <player_index_or_magic> <message>`

## Magic constants for server

Both commands support a magic value to address the server (the server itself as the recipient):

- `sayto "Server" "message text"` — sends to the server
- `sayto_idx -1 "message text"` — sends to the server

Using either form when the issuing client **is** the server produces an error: "The server can't send private messages to itself."

## Variant

`sayto` takes player names; `sayto_idx` takes a player index from the `playerinfo` command's listing.

## Engine-family divergence

`sayto`/`sayto_idx` are confirmed absent from UZDoom's source entirely — no `CCMD`/`CVAR`
declaration and no bare mention of either name anywhere in the tree. This isn't a documentation
gap; UZDoom's netcode has no private/whisper-message channel for these commands to address.
Invoking either under UZDoom — from the console, a config file, or ACS's `ConsoleCommand()` — hits
the console dispatcher's command lookup, then its cvar-name fallback, and when neither matches
prints `Unknown command "sayto"` (or `"sayto_idx"`) to console/log and does nothing else: a visible
failure at the console, but easy to miss if triggered from an unattended context like a server
startup script or `autoexec.cfg` line nobody is watching.

As a result, UZDoom has no console-driven way to send a private message to a single player by name
or index, or to address the server itself via the magic `"Server"`/`-1` constants this file
documents — the entire private-messaging mechanism simply does not run.
