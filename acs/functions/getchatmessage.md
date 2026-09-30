# `str GetChatMessage(int player, int offset [, bool keepcolorcodes])`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-24)
**Provenance:** wiki page `GetChatMessage - Zandronum Wiki.html` (retrieved 2026-08-18, https://wiki.zandronum.com/w/index.php?title=GetChatMessage&oldid=2281) + verified against the Zandronum source's `src/p_acs.cpp:7849-7867`, `src/chat.cpp:919-922`, `src/networkshared.h:560-602`, `src/p_interaction.cpp:3006-3014` (`PLAYER_IsValidPlayer`), `src/chat.cpp:1091-1099,1141-1151` (RCON relay save path), and `src/sv_commands.cpp:220-234,1264-1268,1277-1280` (`SendPrivateMessageToRCONClients`, gated on the receiver or sender being the server).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (index -148, dispatched as `ACSF_GetChatMessage`).

---

## Description

Retrieves a previously received public chat message from a player or server. Each player slot and the server maintain a rolling buffer of up to 5 public chat messages (in FIFO order); private messages sent via `sayto` or `sayto_idx` are never stored and are not retrievable, with one RCON-relay exception (see "Private message exclusion" under Behavior details).

## Parameters

- **`player`**: Player slot number whose chat message to retrieve (0-63). Any negative value (e.g., `-1`) retrieves from the server's own buffer instead, used for RCON messages; `MAXPLAYERS` is only the internal index of that server buffer and is never itself a valid value to pass here. A nonnegative value is validated via `PLAYER_IsValidPlayer()`: a slot with no player currently in the game silently returns an empty string.

- **`offset`**: Which message from the player's rolling buffer to retrieve. `0` retrieves the most recently received message; `4` retrieves the oldest message still stored in memory (since the buffer holds only 5 messages). Values outside `0-4` are silently clamped to the nearest valid index: an offset of `5` or higher returns the oldest message (same as `4`), and an offset less than `0` (after clamping to `0`) returns the newest message.

- **`keepcolorcodes`**: If `true`, color codes in the message are preserved. If `false` (the default when omitted), color codes are removed from the message before returning. Optional; defaults to `false`.

## Return value

Returns the chat message as a string. If fewer than `offset + 1` messages have been stored (e.g., `offset=3` when only 2 messages exist), the unfilled buffer slots return an empty string `""`.

**Silent failure cases** (all return empty string):
1. Nonnegative `player` does not exist (player never connected, disconnected, or invalid slot number).
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

**Private message exclusion:** Messages sent via `sayto` or `sayto_idx` between two players are **never** added to the buffer, even on the receiving end. Only public chat messages (via `say` or `sayteam` and variants handled as public) are stored and retrievable via this function. One exception: a private message sent to or from the server itself is also relayed to every other RCON-privileged client, and that relay does add the message to the RCON client's own local buffer, indexed under the non-server player's slot rather than the RCON client's own slot.

---

## Zandronum-specific: no UZDoom equivalent

This function does not exist in UZDoom, GZDoom, or any ZDoom-family engine variant. It is a Zandronum-only ACS extension tied to Zandronum's `GAMEEVENT_CHAT` event script type (also Zandronum-only). If you need chat-message handling for a portable (non-Zandronum) codebase, this functionality has no alternative in other engines.

---

## String comparison caveat

The returned string is a pooled ACS string (allocated via `GlobalACSStrings.AddString()`), never a compiled string literal. Direct comparison with a literal (`GetChatMessage(player, offset) == "hello"`) is **always** `false` regardless of matching text in a module compiled without `#library`, where the literal is a raw table index and pool indices carry a reserved library-ID tag. Inside a `#library` module the literal is pooled by `PCD_TAGSTRING` and the comparison works (see [String literal vs. pool equality](../concepts/string-literal-vs-pool-equality.md)). Use `StrCmp()` or `StrIcmp()` for safe equality checks, or convert one side explicitly using `StrParam("%s", literal)`.

---

## Code references

- **Engine implementation:** the Zandronum source's `src/p_acs.cpp:7849-7867` (the case block)
- **Chat buffer storage:** the Zandronum source's `src/chat.cpp:919-922` (`CHAT_GetChatMessage` wrapper) and `src/networkshared.h:560-602` (RingBuffer template class)
- **Exclusion of private messages:** the Zandronum source's `src/sv_main.cpp` (chat message dispatch, showing `CHATMODE_PRIVATE_SEND` never calls `CHAT_AddChatMessage`)
- **Player slot validation:** the Zandronum source's `src/p_interaction.cpp:3006-3014` (`PLAYER_IsValidPlayer`). Both an out-of-range slot and an in-range slot with nobody in the game fail this check and yield an empty string.
- **RCON relay exception to private-message exclusion:** the Zandronum source's `src/sv_commands.cpp:220-234` (`SendPrivateMessageToRCONClients`, relays a private message to/from the server to other RCON-privileged clients), `src/sv_commands.cpp:1264-1268,1277-1280` (the call sites, gated on the receiver or sender being the server), and `src/chat.cpp:1091-1099,1141-1151` (the receiving client's save filter, which excludes `CHATMODE_PRIVATE_SEND`/`CHATMODE_PRIVATE_RECEIVE` but not the RCON relay modes).
- **Declaration:** the zt-bcc source's `lib/zcommon.bcs:1778`
