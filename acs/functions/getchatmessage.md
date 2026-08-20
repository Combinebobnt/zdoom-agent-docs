# `str GetChatMessage(int player, int offset [, bool keepcolorcodes])`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-18)
**Provenance:** wiki page `GetChatMessage - Zandronum Wiki.html` (retrieved 2026-08-18, https://wiki.zandronum.com/w/index.php?title=GetChatMessage&oldid=2281) + verified against the Zandronum source's `src/p_acs.cpp:5775-5795`, `src/chat.cpp:922-930`, and `src/networkshared.h:560-602`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (index -148, dispatched as `ACSF_GetChatMessage`).

---

## Description

Retrieves a previously received public chat message from a player or server. Each player slot and the server maintain a rolling buffer of up to 5 public chat messages (in FIFO order); private messages sent via `sayto` or `sayto_idx` are never stored and are not retrievable.

## Parameters

- **`player`**: Player slot number whose chat message to retrieve (0-63 for players, MAXPLAYERS for the server's RCON). Any negative value (e.g., `-1`) retrieves from the server instead. Does not validate the player slot; an out-of-range nonnegative value silently returns an empty string.

- **`offset`**: Which message from the player's rolling buffer to retrieve. `0` retrieves the most recently received message; `4` retrieves the oldest message still stored in memory (since the buffer holds only 5 messages). Values outside `0-4` are silently clamped to the nearest valid index: an offset of `5` or higher returns the oldest message (same as `4`), and an offset less than `0` (after clamping to `0`) returns the newest message.

- **`keepcolorcodes`**: If `true`, color codes in the message are preserved. If `false` (the default when omitted), color codes are removed from the message before returning. Optional; defaults to `false`.

## Return value

Returns the chat message as a string. If fewer than `offset + 1` messages have been stored (e.g., `offset=3` when only 2 messages exist), the unfilled buffer slots return an empty string `""`.

**Silent failure cases** (all return empty string):
1. Nonzero `player` does not exist (player never connected, disconnected, or invalid slot number).
2. The player has not sent messages; the requested `offset` exceeds the number of stored messages.
3. Negative `player` is used and the server has sent no messages (e.g., via RCON).

### Behavior details

**Message retrieval order:** Messages are stored in FIFO order (oldest pushed out when a 6th message arrives). Within the 5-slot rolling buffer:
- `offset=0` → newest message
- `offset=1` → second newest
- `offset=4` → oldest message still in the buffer

**Color code handling:** When `keepcolorcodes=true`, Zandronum's native color code format (e.g., `\c[Z]`, `\c-`) is preserved verbatim in the return value. When `keepcolorcodes=false`, `V_RemoveColorCodes()` is called to strip all color codes.

**Server messages via RCON:** When `player=-1` (or any negative value), the function retrieves RCON messages sent by the server console. The server has its own 5-message buffer, separate from all players.

**Out-of-range offsets:** The offset argument is silently clamped to `0-4` before lookup. No error is raised; clamping is entirely silent. This means `offset=-1` becomes `offset=0` (newest), and `offset=100` becomes `offset=4` (oldest).

**Private message exclusion:** Messages sent via `sayto` or `sayto_idx` are **never** added to the buffer, even on the receiving end. Only public chat messages (via `say` or `sayteam` and variants handled as public) are stored and retrievable via this function.

---

## Zandronum-specific: no UZDoom equivalent

This function does not exist in UZDoom, GZDoom, or any ZDoom-family engine variant. It is a Zandronum-only ACS extension tied to Zandronum's `GAMEEVENT_CHAT` event script type (also Zandronum-only). If you need chat-message handling for a portable (non-Zandronum) codebase, this functionality has no alternative in other engines.

---

## String comparison caveat

The returned string is a pooled ACS string (allocated via `GlobalACSStrings.AddString()`), never a compiled string literal. Direct comparison with a literal (`GetChatMessage(player, offset) == "hello"`) will **always** return `false` regardless of matching text — the two strings live in permanently disjoint index ranges by construction. Use `StrCmp()` or `StrIcmp()` for safe equality checks, or convert one side explicitly using `StrParam("%s", literal)`.

---

## Code references

- **Engine implementation:** the Zandronum source's `src/p_acs.cpp:5775-5795` (the case block)
- **Chat buffer storage:** the Zandronum source's `src/chat.cpp:922-930` (`CHAT_GetChatMessage` wrapper) and `src/networkshared.h:560-602` (RingBuffer template class)
- **Exclusion of private messages:** the Zandronum source's `src/sv_main.cpp` (chat message dispatch, showing `CHATMODE_PRIVATE_SEND` never calls `CHAT_AddChatMessage`)
- **Declaration:** the zt-bcc source's `lib/zcommon.bcs:1778`
