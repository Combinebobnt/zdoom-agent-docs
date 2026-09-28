# `ignore` / `ignore_idx`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** Zandronum Wiki `Console commands` (https://wiki.zandronum.com/w/index.php?title=Console_commands&oldid=2437, retrieved 2026-08-02); verified against `src/chat.cpp:1288-1368` (CHAT_ExecuteIgnoreCmd implementation), `src/chat.cpp:1262-1282` (CHAT_IgnorePlayer), `src/chat.cpp:1400-1445` (CHAT_ExecuteUnignoreCmd), `src/chat.cpp:2057-2079` and `src/voicechat.cpp:252-270` (the CCMD declarations); server mute path `src/sv_commands.cpp:1419-1431`, `src/cl_main.cpp:5137-5143`, `src/chat.cpp:1542-1546`; client IP rule `src/sv_main.cpp:5743-5777`.
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

A negative or non-numeric duration is also indefinite, as is one too large to convert to tics.

A reason string is only meaningful from the server console: `ignore "PlayerName" 10 "Spamming chat"`. Only the server's usage text advertises `[reason]`. A client may type a fourth argument, but it is stored locally, never sent to the server and never shown, so it has no visible effect.

Run from the server console, `ignore` is a server-side mute. The target's client is told it is muted (with the duration and reason) and stops sending chat, printing a "muted" notice instead. Run on a client, it hides the target's messages locally and also tells the server, which remembers the ignore against the target's IP address.

With no arguments, the command lists the players currently ignored (with minutes remaining), or prints its usage if there are none.

Calling any of these commands through ACS `ConsoleCommand()` does nothing on Zandronum: the command returns immediately, with no message.

## Variants

- `voice_ignore` / `voice_ignore_idx` — same syntax, but blocks voice chat instead of text messages.
- `unignore` / `unignore_idx` — reverses a text-chat ignore for the named/indexed player.
- `voice_unignore` / `voice_unignore_idx` — reverses a voice ignore.

## Engine-family divergence

None of `ignore`/`ignore_idx`/`voice_ignore`/`voice_ignore_idx`/`unignore`/`unignore_idx` exist in
UZDoom at all — confirmed absent from the engine's source (no matching `CCMD` declaration, and no
bare mention of any of these names anywhere in the tree), not merely undocumented.

Invoking any of them under UZDoom — from the console or a config file —
prints `Unknown command "<name>"` to the console/log and does nothing else: visible if a player or
admin is watching the console at the time, easy to miss if triggered from an unattended context
such as an `autoexec.cfg` line. As a result, UZDoom has no per-player mechanism at all for a client
to silence another player's chat or voice — the capability these commands provide simply doesn't
exist there, so a player who wants to block harassment has no equivalent to fall back on.
