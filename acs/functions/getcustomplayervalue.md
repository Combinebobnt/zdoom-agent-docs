# GetCustomPlayerValue

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `GetCustomPlayerValue - Zandronum Wiki.html` (wiki `https://wiki.zandronum.com/w/index.php?title=GetCustomPlayerValue&oldid=2282`, a stub page), verified against the Zandronum source's `src/p_acs.cpp` 2026-07-29.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** Extension function (index -157; `SetCustomPlayerValue` at -156, `ResetCustomDataToDefault` at -158)

```text
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

## Engine-family divergence

`GetCustomPlayerValue` is bound as ACSF (CALLFUNC) index 157 — inside the 100–199 range UZDoom's
own ACSF enum reserves for Zandronum's extensions and implements none of (confirmed via
`tools/engine_matrix.py GetCustomPlayerValue`, bin `zandronum-only-silent`). UZDoom's
`CallFunction` dispatcher is a plain `switch` over the ACSF index with `default: break;` falling
through to `return 0` — no error, no log line, execution just continues. A Zandronum-compiled
object calling `GetCustomPlayerValue` under UZDoom silently gets `0` back in place of whatever the
looked-up column would actually decode to. See
[Zandronum/UZDoom compatibility](../concepts/zandronum-uzdoom-compat.md) for the general mechanism
— this function is one of the confirmed instances it names directly.

That fallback `0` collides with several of this function's own legitimate outcomes, so a UZDoom
caller can't tell "wrong engine" apart from a real answer. Per "What it actually does" above, `0`
is already the shared return for "key not found" and "player invalid" on Zandronum itself, and for
a `DATATYPE_BOOL`/`DATATYPE_INT` column it's also an entirely ordinary stored value — there is no
way to distinguish "this field was never set (or never declared via `addcustomdata`)" from "the
value genuinely is 0" from "this build doesn't implement the call at all". It's worse for the two
string-handle types: per "Return value depends on the column's declared data type" above,
`DATATYPE_STRING`/`DATATYPE_TEXTURE` columns return a global ACS string-table handle, not a raw
int, and `0` is not a valid handle produced by that path — a script that hands the fallback
straight to a string-consuming opcode gets whatever unrelated string an untagged lookup at index 0
resolves to, not the empty string Zandronum's own "key not found" case would produce. The paired
setter, `SetCustomPlayerValue` (CALLFUNC index 156), sits in the same reserved range and fails the
same way: the write silently never happens under UZDoom, so a round-trip set-then-get through this
pair looks like "read back 0" either way, with nothing to flag that neither call actually ran.
