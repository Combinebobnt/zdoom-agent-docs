# `bool AddBot([str name[, int team]])`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-18)
**Provenance:** Zandronum Wiki `AddBot` (retrieved 2026-08-18, https://wiki.zandronum.com/w/index.php?title=AddBot&oldid=2240) + source-verified against the Zandronum source's `src/p_acs.cpp:8540-8581`, `src/g_level.h:57`, `src/g_mapinfo.cpp:327`, `lib/zcommon.bcs:168`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (index -168; dispatched as `ACSF_AddBot`).

Adds a bot to the game. Returns `1` if the bot was added successfully, or `0` on error.

## Parameters

- **name** (str, optional): The name of the bot to add, as defined in `BOTINFO` lump entries. If omitted or empty, a random bot is added.
- **team** (int, optional): The team to add the bot to. Only valid if `name` is provided and non-empty. If the game mode does not support teams (checked via `GMF_PLAYERSONTEAMS`), passing this parameter returns `0`.

## Return value

Returns `1` if the bot was successfully spawned (the `CSkullBot` constructor was reached and executed).
Returns `0` in any of these error cases:
- No free player slot is available (`MAXPLAYERS` limit reached).
- A `name` was provided but is not recognized as a valid bot name.
- A `team` was provided but the current game mode does not support teams.
- A `team` was provided but the team index is invalid.
- The map has the `nobotnodes` MAPINFO flag set (bots cannot spawn on this map).
- The script is running on a client in network mode (bots can only be added on the server).

## Server-only behavior

Calling `AddBot` from a client in a network game (when `NETWORK_InClientMode()` returns true) is silently ignored and returns `0`. This matches the general pattern that bot management is server-side only.

## Zandronum-specific: bot availability

This function is a Zandronum-only addition and does not exist in UZDoom/GZDoom at all (not exposed as an ACS-callable function; internal bot code is present in UZDoom but uses different entry points not reachable from ACS).

## Wiki/engine divergence

The Zandronum Wiki page lists three failure cases (invalid bot name, invalid team, no bot nodes). The actual source implements six distinct error checks:

1. **Missing name validation (`BOTS_IsValidName`)** — handled via source validation, not mentioned in wiki.
2. **No free player slot** (`freePlayerSlot == MAXPLAYERS`) — checked *before* name/team validation, not documented in wiki. If the player limit is reached, the function fails even if the requested bot name is valid.
3. **Team without game-mode support** — the wiki mentions invalid team, but the actual implementation first checks whether the game mode supports teams at all. If it doesn't, passing a team parameter fails unconditionally.
4. **Client-side execution** — the source silently returns `0` if called from a client in network mode; the wiki does not mention this at all.
5. **Empty-string bot name** — if `name` is an empty string, it is treated the same as omitting the parameter and a random bot is added, but the game mode and team validation still proceeds. The wiki's wording ("If this is unspecified or empty") matches this behavior.
6. **Team parameter without a name** — the team parameter is unreachable if no name (or empty-string name) is provided; the source checks `if (argCount > 1)` nested inside `if (argCount > 0)`. The wiki documentation does not clarify this nesting.

## Potential crash on invalid string index

**Source-verified issue:** At line 8556, `botName = FBehavior::StaticLookupString(args[0])` retrieves a string by index. If `args[0]` is an invalid string index (e.g. a negative number, or an index never registered), `StaticLookupString` can return `NULL`. The next line unconditionally calls `strlen(botName)` without checking for `NULL` first, which would crash the engine with a NULL pointer dereference. This matches the crash pattern documented in `acs/concepts/crash-and-bug-checklist.md` (pattern #2, "NULL `char*` from a getter measured with no guard"). **The script-side mitigation:** validate the string index before calling `AddBot`, or call `StrParam()` to build the bot name from trusted sources rather than passing an unvalidated index.

## Examples

Add a random bot to the game:
```acs
if (AddBot())
  Log("Bot added successfully");
else
  Log("Failed to add bot (server or player limit issue?)");
```

Add a named bot to a specific team (if the game mode supports teams):
```acs
int result = AddBot("Crusher", TEAM_RED);
if (result == 0)
  Log("Failed: invalid bot name, invalid team, or mode doesn't support teams");
```

## See also

- `RemoveBot` — remove a bot by name or player index.
- `BOTINFO` lump — defines available bot names and their properties.
- `nobotnodes` (MAPINFO flag) — disables bot spawning on the map.
