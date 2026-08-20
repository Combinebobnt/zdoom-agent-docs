# `ignore` / `ignore_idx`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, retrieved 2026-08-02); verified against `src/chat.cpp:1288-1350` (CHAT_ExecuteIgnoreCmd implementation).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

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

## Engine-family divergence

None of `ignore`/`ignore_idx`/`voice_ignore`/`voice_ignore_idx`/`unignore`/`unignore_idx` exist in
UZDoom at all — confirmed absent from the engine's source (no matching `CCMD` declaration, and no
bare mention of any of these names anywhere in the tree), not merely undocumented.

Invoking any of them under UZDoom — from the console, a config file, or ACS's `ConsoleCommand()` —
prints `Unknown command "<name>"` to the console/log and does nothing else: visible if a player or
admin is watching the console at the time, easy to miss if triggered from an unattended context
such as an `autoexec.cfg` line. As a result, UZDoom has no per-player mechanism at all for a client
to silence another player's chat or voice — the capability these commands provide simply doesn't
exist there, so a player who wants to block harassment has no equivalent to fall back on.
