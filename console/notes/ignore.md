# `ignore` / `ignore_idx`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, retrieved 2026-08-02); verified against `src/chat.cpp:1288-1350` (CHAT_ExecuteIgnoreCmd implementation).

Ignore a player's chat messages (or voice, for the `voice_ignore` variant). Both commands support blocking for a specified duration or indefinitely.

## Syntax

- `ignore <player_name> [duration_minutes] [reason]`
- `ignore_idx <player_index> [duration_minutes] [reason]`

## Duration semantics

The **duration is in minutes**, and may be omitted to block indefinitely. Duration omission is the default when the third and later arguments are not specified. For example:

- `ignore "PlayerName"` — blocks indefinitely
- `ignore "PlayerName" 30` — blocks for 30 minutes
- `ignore "PlayerName" 0` — blocks indefinitely (zero duration maps to indefinite, per the same semantics as omission)
- `ignore_idx 5 5` — blocks player at index 5 for 5 minutes

Server consoles may optionally append a reason string, which clients cannot: `ignore "PlayerName" 10 "Spamming chat"` (server only).

## Variants

- `voice_ignore` / `voice_ignore_idx` — same syntax, but blocks voice chat instead of text messages.
- `unignore` / `unignore_idx` — reverses either text or voice ignoring for the named/indexed player.
