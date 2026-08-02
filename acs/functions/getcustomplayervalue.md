# GetCustomPlayerValue

**Tier:** A
**Engine:** Zandronum 3.2.1 — the whole custom-column/custom-player-value feature (originally added as `GetCustomColumnValue` in commit `b3d065026`, later renamed to `GetCustomPlayerValue` in `1115642c3`) was checked via `git merge-base --is-ancestor <commit> 28f736fb3` (the 3.2.1 version-bump commit) and both predate it, so this is confirmed present in 3.2.1, not a post-3.2.1 addition.
**Provenance:** `GetCustomPlayerValue - Zandronum Wiki.html` (wiki `oldid=2282`, a stub page), verified against the Zandronum source's `src/p_acs.cpp` 2026-07-29.
**Bucket:** Extension function (index -157; `SetCustomPlayerValue` at -156, `ResetCustomDataToDefault` at -158)

```
raw GetCustomPlayerValue(str data, int player)
```

## What it actually does

`data` looks up a `PlayerData*` in `gameinfo.CustomPlayerData` — the per-mod custom scoreboard
columns declared with `addcustomdata` in a MAPINFO `GameInfo` block (this is what the wiki means
by "as defined in the GameInfo definition"; a mod that never uses `addcustomdata` has no valid
`data` strings to pass here at all). If the key isn't found, or `player` fails
`PLAYER_IsValidPlayer()`, the call returns `0` — this covers both "field doesn't exist" and
"player doesn't exist" as one shared failure path, matching the wiki's "returns 0 otherwise", but:

- **`player` validity is `playeringame[player]` only** — `PLAYER_IsValidPlayer()` does **not**
  exclude spectators (unlike `PlayerCount`/`PlayerInGame`, both already documented in this repo
  as spectator-excluding). A spectating player's custom value still reads back normally here.
- `player` is compared as an unsigned index internally, so a negative `player` silently fails
  closed to the same `0` return rather than erroring — indistinguishable from "field not found"
  or "value is legitimately 0".

## Return value depends on the column's declared data type

The raw wiki signature (`raw` return) hides that the actual value returned is decoded by a
`GetPlayerValue()` helper (`p_acs.cpp:1896`) that branches on the custom column's `DATATYPE_*`,
the same "one raw slot, several real types" pattern already documented for
[GetActorProperty](getactorproperty.md):

| Column data type | What `GetCustomPlayerValue` actually returns |
|---|---|
| `DATATYPE_INT` | plain `int` |
| `DATATYPE_BOOL` | `0`/`1` |
| `DATATYPE_FLOAT` | **fixed-point** (`FLOAT2FIXED`) — not a plain int, must be treated as `fixed` in BCS despite the `raw` declared type |
| `DATATYPE_COLOR` | raw `PalEntry` int (packed color) |
| `DATATYPE_STRING` | a **global ACS string-table handle** (`GlobalACSStrings.AddString(...)`), not printable as an int |
| `DATATYPE_TEXTURE` | also a string-table handle, holding the texture's *name* (or `""` if the stored `FTexture*` is `NULL`) |

None of this — the fixed-point float case or the two string-handle cases — is mentioned on the
(stub) wiki page. Treating the result as `str` for `DATATYPE_STRING`/`DATATYPE_TEXTURE` fields,
`fixed` for `DATATYPE_FLOAT`, and plain `int` otherwise is required to get a sane value out.

## See also

- `SetCustomPlayerValue` (-156) — the writer counterpart; same key lookup and same per-type
  branch on the way in (`args[2]` is read as int/bool/fixed/string depending on the column's
  declared type).
- `ResetCustomDataToDefault` (-158) — resets one player's (or, with `player < 0`, all players')
  value for a given `data` key back to the column's declared default.
