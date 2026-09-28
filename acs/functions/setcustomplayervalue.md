# `int SetCustomPlayerValue(str data, int player, raw value)`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** `SetCustomPlayerValue - Zandronum Wiki.html` (wiki `https://wiki.zandronum.com/w/index.php?title=SetCustomPlayerValue&oldid=2264`, a stub page), verified against the Zandronum source's `src/p_acs.cpp:8176-8225` (2026-08-18); `src/scoreboard.cpp:723-738` (`PlayerData::SetValue`) and `src/cmdlib.cpp:105-112` (`ncopystring`).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** Extension function (index -156; `GetCustomPlayerValue` at -157, `ResetCustomDataToDefault` at -158)

## What it actually does

`data` looks up a `PlayerData*` in `gameinfo.CustomPlayerData` — the per-mod custom scoreboard columns declared with `addcustomdata` in a MAPINFO `GameInfo` block (the same system documented for [GetCustomPlayerValue](getcustomplayervalue.md)). The function writes `value` to the custom column for the given player, branching on the column's declared `DATATYPE_*` and converting the incoming `raw` argument appropriately.

If either the column doesn't exist or `player` fails `PLAYER_IsValidPlayer()`, the call returns `0` — this covers both "field doesn't exist" and "player doesn't exist" as one shared failure path.

- **`player` validity is `playeringame[player]` only** — `PLAYER_IsValidPlayer()` does **not** exclude spectators. A spectating player's custom value can be set and read normally.
- `player` is compared as an unsigned index internally, so a negative `player` silently fails closed to the same `0` return rather than erroring.

## Parameter conversion depends on the column's declared data type

The `raw` signature type hides that the incoming `value` parameter is interpreted by a type-specific branch — the same "one raw slot, several real types" pattern documented for [GetCustomPlayerValue](getcustomplayervalue.md):

| Column data type | How `value` is interpreted |
|---|---|
| `DATATYPE_INT` | Stored as-is (plain `int`). |
| `DATATYPE_BOOL` | Converted to bool: any non-zero becomes `1`, zero becomes `0`. |
| `DATATYPE_FLOAT` | **Converted from fixed-point to float using `FIXED2FLOAT(value)`** — the incoming ACS `raw` argument must already be fixed-point. Passing `1` sets the column to `~0.0000153` (1/65536), not `1.0`; to set the column to exactly `1.0`, pass `65536`. This is the inverse of `GetCustomPlayerValue`, which returns a `DATATYPE_FLOAT` column as fixed-point. |
| `DATATYPE_COLOR` | Stored as raw `PalEntry` int (packed color). |
| `DATATYPE_STRING` | Looked up in the global ACS string table via `FBehavior::StaticLookupString(value)`, then stored as a copied C string. `value` must be a string handle: a string literal or the result of a string-producing call such as `StrParam`. An empty string or an invalid handle (which looks up as NULL) clears the column to an empty value, and the call still returns `1`. |
| `DATATYPE_TEXTURE` | `value` is a string handle naming the texture. The name is looked up the same way, then passed to `TexMan.FindTexture()` and stored as a `FTexture*`. **Note: an unknown texture name (or an invalid handle) is stored as NULL, but the function still returns `1`. A successful return does not guarantee the texture name was valid.** |

None of this — the fixed-point float case or the two string-handle cases — is mentioned on the (stub) wiki page. Passing the right type for each case is required to avoid corruption or silent failures.

## Return value

Returns `1` if the field and player both exist and the write succeeded (including the `DATATYPE_TEXTURE` case where the texture name was invalid, and the case where the new value equals the stored one, which `PlayerData::SetValue` skips as a no-op). Returns `0` if:

- The `data` key isn't found in `gameinfo.CustomPlayerData`.
- `player` fails the `PLAYER_IsValidPlayer()` check.
- The column's declared type is not one of the six cases above (an internal `default:` case in the type switch).

## Networking

The call runs wherever the script runs: offline and on a server it changes the local copy. When the stored value actually changes on a server, `PlayerData::SetValue` sends `SERVERCOMMANDS_SetCustomPlayerValue` to clients, with the value serialized as a string (no field-width truncation). A call from a `CLIENTSIDE` script changes only that client's copy and tells nobody.

## See also

- `GetCustomPlayerValue` (-157) — the reader counterpart; same key lookup and same per-type branch on the way out (returns are already decoded to the appropriate type, unlike the setter's raw-type hiding).
- `ResetCustomDataToDefault` (-158) — resets one player's (or, with `player < 0`, all players') value for a given `data` key back to the column's declared default.

## Engine-family divergence

`SetCustomPlayerValue` is bound as ACSF (CALLFUNC) index 156 — inside the 100–199 range UZDoom's own ACSF enum reserves for Zandronum's extensions and implements none of (confirmed via the comment block in UZDoom's `src/playsim/p_acs.cpp:4824-4832`, which explicitly lists Zandronum-specific indices and says "these must be skipped"). UZDoom's `CallFunction` dispatcher is a plain `switch` over the ACSF index with `default: break;` falling through to `return 0` — no error, no log line. A Zandronum-compiled object calling `SetCustomPlayerValue` under UZDoom silently gets `0` back, and the write never happens. A set-then-get round trip over this pair reads back `0`, with nothing logged to flag that neither call ran. The setter's own return value is the one signal: on Zandronum it returns `1` only when the write ran, so a `1` proves it ran. A `0` stays ambiguous (skipped under UZDoom, or a bad column or player on Zandronum). The getter has no such signal, since its `0` can't be told from a real zero. See [Zandronum/UZDoom compatibility](../concepts/zandronum-uzdoom-compat.md) for the general mechanism.
