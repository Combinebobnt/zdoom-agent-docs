# `raw GetSkinProperty(int skin, str property[, bool checkType, int index])`

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the Zandronum source's `src/p_acs.cpp:5549` (`EACSFunctions` enum entry), `:8833-8851` (dispatch case), `:1896-1927` (`GetPlayerValue`); `src/r_data/sprites.h:79-84` (`FPlayerSkin` property fields); `src/r_data/sprites.cpp:764-820` (custom-key parsing in `R_InitSkins`), `:850-864` and `:1268-1269` (skin-to-class binding), `:1075-1093` (`R_CreateSkin` defaults), `:1099-1163` (`R_InitSkinPropertyMap`), `:1272-1423` (scale downsizing, then the property-map pass); `src/scoreboard_enums.h:92-110` (`DATATYPE_e`); `src/d_main.cpp:2492-2497` (skins directory autoload); and zt-bcc's `lib/zcommon.bcs:1299-1305` (`SPROP_TYPE_*`) and `:1812` (declaration).
**Bucket:** extension function (index -184; dispatched as `ASCF_GetSkinProperty`, with the `ASCF_` misspelling. A grep for `case ACSF_GetSkinProperty` finds nothing).

Reads one named property of a player skin by skin index: either a built-in field the engine fills in for every skin, or a free-form custom key from the skin's `SKININFO`/`S_SKIN` block. With `checkType` set it returns the property's data type instead of its value. This entry is written from engine and compiler source only, not derived from any wiki page. Neither the UltimateDoomBuilder `Zandronum_ACS.cfg` nor SLADE's language files describe it.

## Parameters

zt-bcc declares all four parameters as `raw` with the last two optional (`GetSkinProperty(raw, raw; raw, raw):raw`); the types in the H1 are what the engine actually reads each one as.

- `skin`: skin index, the same numbering `GetPlayerSkin()` returns. Read as unsigned, so a negative value is out of range and fails like any other bad index.
- `property`: property name string. Looked up as an `FName`, so the match is case-insensitive (`"XScale"` and `"xscale"` are the same property).
- `checkType` (optional, default `false`): any nonzero value makes the call return the property's type code (see below) instead of its value.
- `index` (optional, default `0`): which value to read when the property holds several (a comma-separated custom key, or a name collision; see below). Read as unsigned, so negative values fail.

The engine gates the optional arguments on the actual argument count, so omitting them is exactly the same as passing `false` and `0`.

## Return value

With `checkType` false, the stored value is converted by the same helper `GetCustomPlayerValue()` uses:

| Stored type | Returned as |
|---|---|
| int | the integer as-is |
| bool | `1` or `0` |
| float | fixed-point (`xscale` of 1.0 returns `65536`) |
| string | an ACS string |

With `checkType` true, the return is one of zt-bcc's `SPROP_TYPE_*` constants, which map one-to-one onto the engine's `DATATYPE_e` values: `SPROP_TYPE_UNKNOWN` (0), `SPROP_TYPE_INT` (1), `SPROP_TYPE_BOOL` (2), `SPROP_TYPE_FLOAT` (3), `SPROP_TYPE_STRING` (4). The engine enum also has color (5) and texture (6) types with no zt-bcc constant, but no skin property is ever stored as either.

## Failure behavior

Three conditions fail, and all three look the same: a skin index at or past the end of the skin list, a property name the skin doesn't have, or an `index` at or past the property's value count. The call then returns `0`, or `SPROP_TYPE_UNKNOWN` (also `0`) when `checkType` is set. Nothing is printed.

That `0` can't be told apart from a real integer `0`, a `false` bool or a `0.0` float, and for a string property it is not an empty string: it is ACS string handle 0, which looks up string 0 of the first loaded ACS module. When a property may be missing, call once with `checkType` set and treat `SPROP_TYPE_UNKNOWN` as "absent" before reading the value.

## Built-in properties

The engine fills these in for every skin once, at startup, after all skins are parsed:

| Property | Type | Value | Present |
|---|---|---|---|
| `name` | string | the skin's name (after any duplicate-name rename to `skin<N>`) | always |
| `sprite` | string | 4-character sprite name | always |
| `crouchsprite` | string | 4-character crouch sprite name | only if the skin has its own crouch sprite |
| `face` | string | 3-character status-bar face prefix | only if one is set |
| `gender` | int | 0 male, 1 female, 2 neuter | always |
| `xscale`, `yscale` | float | horizontal/vertical scale | always |
| `game` | string | `"doom"`, `"heretic"` or `"strife"` | always |
| `class` | string | the bound player class's `Player.DisplayName` | always, in practice |
| `classactor` | string | the bound player class's actor class name | always, in practice |
| `revealed` | bool | whether the skin is revealed in the skin menu | always |
| `cheat` | bool | whether the skin is a cheat skin | always |
| `color` | string | the skin's `color` key, verbatim (stored in a 16-byte buffer) | only if the key was given |

Notes on specific properties:

- **Property names are not SKININFO key names.** The `scale` key becomes two properties, `xscale` and `yscale`. The `hidden` key becomes `revealed`, and with the inverted sense documented in [the SKININFO lump](../../zandronum-lumps/concepts/skininfo.md): `hidden = true` stores `revealed` as true.
- **`xscale`/`yscale` are the final scale.** The engine shrinks a skin whose sprites exceed the size limits before it builds the property table, so these report the downsized scale, not the declared one.
- **`game` is the declared key, defaulting to `"doom"`.** A skin that never sets `game`, and every base skin, reports `"doom"` even when the running game is Heretic or Strife.
- **`revealed` is a startup snapshot.** Selecting a hidden skin reveals it at runtime (`src/d_netinfo.cpp:1414-1422`), but the property keeps the value it had when the table was built.
- **`class`/`classactor` name one class.** Every skin that survives loading is bound to at least one player class, so both are present in practice. A skin usable by several player classes records only the last matching class in player-class order.

## Base skins

Indices below the number of player classes are each class's reserved `"Base"` skin. Their `name` is `"Base"`, `class`/`classactor` name that player class, `sprite`/`xscale`/`yscale` come from the class defaults, `face` is the class's face prefix (or `STF` when the class sets none), `game` is `"doom"` and `revealed` is true. They carry no custom properties, since they are not parsed from a lump.

## Custom properties

Any `SKININFO`/`S_SKIN` key the parser doesn't recognize (not a general key, not a `*`-prefixed or legacy sound key) is stored as a custom property under its own name. Each value is auto-typed: integer-looking text becomes an int, float-looking text a float, `true`/`false` (case-insensitive) a bool, and anything else, including `yes`/`no`, stays a string.

A custom key can hold several values separated by commas (`tags = 1, 2, 3`); each is typed separately and stored in order, and `index` selects one. There is no call that returns the count, so probe with `checkType` until it returns `SPROP_TYPE_UNKNOWN`:

```acs
int count = 0;
while (GetSkinProperty(skin, "tags", true, count) != SPROP_TYPE_UNKNOWN)
    count++;
```

**Name collisions shift the built-in value to index 1.** Custom keys are stored while the lump is parsed; the built-in properties are appended afterwards. A lump key that is not a parser key but matches a built-in property name (`xscale`, `yscale`, `revealed` or `classactor`) therefore puts the custom value at index 0 and the engine's own value at index 1. Keys the parser does recognize (`name`, `sprite`, `class`, `cheat`, `color` and so on) never collide this way.

## Client/server behavior

The call only reads the local skin table. It sends nothing over the network and behaves the same in a `CLIENTSIDE` script as on the server. The skin table itself is built per machine at startup, though, and each machine also autoloads the files in its own `skins` directory (`src/d_main.cpp:2492-2497`). A client with extra skins installed can have a different skin list from the server, so a skin index obtained on one side (for example from `GetPlayerSkin()` on the server) is not guaranteed to name the same skin, or exist at all, on the other.

## Zandronum-specific: absence from UZDoom

This function exists only in Zandronum. The UZDoom source has no `GetSkinProperty` in its ACS function enum or special table, and no per-skin property table to back one.

## See also

- `GetPlayerSkin()`: get a player's skin index, the input this function takes.
- `SetPlayerSkin()`: set a player's ACS skin override.
- [The SKININFO lump](../../zandronum-lumps/concepts/skininfo.md): the keys that feed the built-in and custom properties.
