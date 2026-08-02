# `sayto` / `sayto_idx`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, retrieved 2026-08-02); verified against `src/chat.cpp:1999-2040` (sayto/sayto_idx CCMD implementations).

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
