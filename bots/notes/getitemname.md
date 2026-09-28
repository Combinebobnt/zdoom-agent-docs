# GetItemName

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** written from the Zandronum source's `src/botcommands.cpp` (`botcmd_GetItemName` and the other `RETURNVAL_STRING` handlers). No wiki page covers this command. Net-ID validation: `botcmd_GetItemName`'s `unsigned short` cast (`botcommands.cpp:1695`) and `botcmd_ValidateItemNetID`'s 65536 bound (`botcommands.cpp:843`).

## Engine-family divergence

`GetItemName` is a bot command, not an ACS/BCS function — it lives in Zandronum's bot-command
dispatcher (`botcommands.cpp`), which UZDoom/GZDoom-family engines don't have at all. There is no
UZDoom counterpart to diverge from; see `../AGENTS.md`.

Returns the DECORATE class name (`TypeName`) of the item actor identified by the given net ID
(same net-ID argument convention as `GetDistanceToItem`/`GetPathingCostToItem`/`IsItemVisible`/
`SetGoal`). The pushed value is cast to `unsigned short` before `botcmd_ValidateItemNetID` checks
it against 65536, so that check's fatal `I_Error` can never fire: an out-of-range value silently
wraps modulo 65536 and is looked up as whatever ID it lands on. Returns an
empty string, not an error, if the net ID doesn't currently resolve to any actor (e.g. the item was
picked up or removed between the ID being obtained and this call).

## The `BOTCMD_RETURNSTRING_SIZE` cap fails silently, not by truncating

Every `RETURNVAL_STRING` command shares one 256-byte buffer, `g_szReturnString`
(`BOTCMD_RETURNSTRING_SIZE`, `botcommands.h:69`). `GetItemName` is representative of how most of
them handle a source string at or past that cap: `if ( strlen(source) < BOTCMD_RETURNSTRING_SIZE )
copy else g_szReturnString[0] = 0;` — a too-long source produces a **silent empty string**, not a
truncated one and not an error. This exact pattern (verified individually, not assumed from
`GetItemName` alone) is shared by `GetCurrentWeapon`, `GetWeaponFromItem`, `GetFavoriteWeapon`, and
`GetPlayerName` — all read live class/weapon/player names that could theoretically reach 256
characters (a very long custom actor class or player name), and all fail the same way.

**`GetLastChatString` is the one exception**: it reads from `g_szLastChatString`, which is itself
capped to 255 characters (plus null terminator) at the point it's captured
(`BOTCMD_SetLastChatString`'s `strncpy(..., 255)`), so its `< BOTCMD_RETURNSTRING_SIZE` check can
never fail. `GetLastChatPlayer` looks like the same case but isn't: its source,
`g_LastChatPlayer`, is a plain `FString` assigned with no length cap at all
(`BOTCMD_SetLastChatPlayer( const char *pszString ) { g_LastChatPlayer = pszString; }`, called from
`chat.cpp` with a player's userinfo name) — it shares the same silent-empty-string exposure as
`GetItemName`/`GetPlayerName`/the weapon getters, just bounded in practice by whatever caps a
player's own name length elsewhere, not by anything in this code path.

## Related

- `IsItemVisible`, `GetDistanceToItem`, `GetPathingCostToItem`, `SetGoal` — the other net-ID-taking
  item commands; all take the net ID through the same `unsigned short` cast, so all wrap an
  out-of-range value the same way instead of erroring.
