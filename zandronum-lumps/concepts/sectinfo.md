# The `SECTINFO` lump

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki `SECTINFO` (retrieved 2026-09-09, https://wiki.zandronum.com/w/index.php?title=SECTINFO&oldid=2132) + Zandronum Wiki `Data:Skulltag SECTINFO` (retrieved 2026-09-09, oldid=1381) + verified against
the Zandronum source's `src/sectinfo.cpp` (`SECTINFO_Load`, `SECTINFO_Parse`, `SECTINFO_ParseNames`,
`SECTINFO_ParseSectors`, `SECTINFO_ParsePoints`, `SECTINFO_GetPlayerLocation`), `src/g_mapinfo.cpp` (`FindLevelInfo`, `FindWadLevelInfo`), and `src/sectinfo.h`. Consumer list
checked against `src/p_acs.cpp` (`ACSF_GetActorSectorLocation`, `ASCF_GetControlPointInfo`,
`ASCF_SetControlPointInfo`, `ACSF_IsPlayerContestingControlPoint`), `src/chat.cpp`,
`src/g_shared/st_hud.cpp`, `src/g_game.cpp` (`GAME_CheckMode`) and `src/domination.cpp`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0
(NonCommercial) — see [LICENSE](../../LICENSE) §2.

`SECTINFO` attaches per-map metadata to sectors: named labels for sector groups (used for a
"where am I standing" display) and, separately, Domination-mode control points. Originally
originating from ZDaemon, Zandronum retained and extended the format. Unlike the other
`key = value`/anonymous-`{ }`-block lumps in this section, it is INI-style: one `[MAPNAME]`
section per map, each holding `key = { ... }` properties. `MAPNAME` is looked up against the
already-parsed MAPINFO level list, not declared fresh here.

Loading is cumulative across every loaded archive, the same as the rest of this lump family:
`SECTINFO_Load` (`src/sectinfo.cpp:98-108`) loops `Wads.FindLump("SECTINFO", ...)` and calls
`SECTINFO_Parse` on each hit. The lump uses a modern `FScanner` parser in C mode
(`sc.SetCMode(true)`, `src/sectinfo.cpp:139`), the same parser generation as `MEDALDEF`/`SCORINFO`/
`VOTEINFO`/`AUTHINFO`: a malformed token raises a fatal `sc.ScriptError`, not the silent-ish
`I_Error` style of the `ANCRINFO`/`CMPGNINF` hand-rolled scanner.

## Section header and map binding

```text
[MAP01]
names = { "Start Room" = { 0-4 } }
```

`[` starts a section; the next token must be an identifier, read as the map name, followed by
`]` (`src/sectinfo.cpp:142-148`). The name is resolved with `FindLevelInfo(name, false)` (the
`false` is `allowdefault`), so an unrecognized map name resolves to a null `level_info_t*` rather
than falling back to a default map. When that happens, the very next property line is fatal: the
parser's fallback branch has no other case and raises `sc.ScriptError("Invalid Syntax")`
(`src/sectinfo.cpp:178-181`). This does not match the comment directly above the `FindLevelInfo`
call in the source, which says an unrecognized map name causes the entry to apply "to the
defaultmap" - that description does not hold for the current `allowdefault=false` call
(`FindLevelInfo`'s own default-fallback path, the one that comment appears to describe, only runs
when `allowdefault` is true; see `src/g_mapinfo.cpp:87-106`). Treat the comment as stale and the
actual behavior (a fatal parse error) as what to expect.

**Reopening a `[MAPNAME]` section clears that map's previously accumulated `SECTINFO` data first**
(`mapinfo->SectorInfo.Clear()`, `src/sectinfo.cpp:150-154`, clearing `Names`, both `Base` arrays,
and `Points`). A later-loaded WAD's `[MAPNAME]` section replaces the earlier one's properties for
that map rather than merging with them, even though the lump as a whole is still loaded
cumulatively across every WAD (a WAD with a `[MAP02]` section does not touch `[MAP01]`'s data from
another WAD).

## Properties

Four keys are recognized inside a `[MAPNAME]` section (`SectInfoProperties`,
`src/sectinfo.cpp:116-124`); anything else is a fatal parse error since `sc.MustMatchString`
requires an exact match.

| Key | Grammar | Read anywhere? |
|---|---|---|
| `names` | `names = { "Label" = { range, range, ... }, ... }` | Yes |
| `base0` | `base0 = { range, range, ... }` | **No, dead** |
| `base1` | `base1 = { range, range, ... }` | **No, dead** |
| `points` | `points = { "Name" = { range, range, ... }, ... }` | Yes |

A "range" in every case above is one `TK_IntConst`, optionally followed by `-` and a second
`TK_IntConst` for an inclusive range; `5-2` and `2-5` are equivalent since the parser swaps the
pair if written in descending order (`src/sectinfo.cpp:209-210`, `248-249`, `291-292`).

### `names`: sector-to-label lookup, not tied to any gamemode

`names` maps sector index ranges to a display string, stored as `SectInfo::Names` (one shared
pointer per sector index, `src/sectinfo.h`). A label starting with `$` is resolved through the
string-table lookup used for localized text (`GStrings`) instead of being used literally
(`src/sectinfo.cpp:193-196`). The engine's own consumer is `SECTINFO_GetPlayerLocation`
(`src/sectinfo.cpp:314-322`), which looks up the calling player's current sector in `Names` and
falls back to a fixed "Unknown Location" string if the sector has no entry (or the map has no
`SECTINFO` at all). That function backs two purely presentational features: the `$location` chat
string substitution (`src/chat.cpp:1712-1716`, which calls it unconditionally, so a map without
`names` substitutes "Unknown Location"), and a line in the scoreboard/HUD overlay shown for
teammates and spectators (`src/g_shared/st_hud.cpp:738-740`, drawn only when
`SectorInfo.Names.Size() > 0`). Neither has any gameplay effect. ACS can also read a label
directly: [`GetActorSectorLocation`](../../acs/functions/getactorsectorlocation.md) with
`point == false` returns the `names` label of an actor's sector, or an empty string
(`src/p_acs.cpp:7987-7993`), so a mod can build its own logic on `names`.

The parser accepts several syntax details the lump grammar description above elides: sector assignment lists may include `//` and `/* */` comments (C mode strips them), commas are optional before a closing `}` (a trailing comma after the last entry is harmless), and map name comparisons are case-insensitive (via `strnicmp` in `FindWadLevelInfo`, which `FindLevelInfo` calls, `src/g_mapinfo.cpp:76`). When two sector-label pairs assign to the same sector index, the last-parsed one overwrites silently with no warning — the fill loop is a plain assignment (`SectorNames[i] = name`, `src/sectinfo.cpp:219`), not a merge or accumulation.

### `base0`/`base1`: parsed, stored, and never read back

`base0` and `base1` parse into `SectInfo::Base[0]` and `Base[1]`, a `bool` flag per sector index
(`src/sectinfo.h`; both are `TArray<bool>`). **A repo-wide search for every place `SectorInfo`'s
`Base` member is touched turns up only three sites, all inside `src/sectinfo.cpp` itself: the
`SectInfo` constructor, `SectInfo::Clear()`, and the two `SECTINFO_ParseSectors` calls that fill
them in from the lump.** No other file in the engine reads `SectorInfo.Base[0]` or `Base[1]` back
out - not the HUD, not `p_acs.cpp`'s extension functions, not any gamemode's own logic. A comment
directly on the `base0` case (`src/sectinfo.cpp:167`) speculates about reversing it for
compatibility with a different engine's red/blue sector convention, which only makes sense if
something once read these values; nothing in the current source does. Declaring `base0`/`base1`
in a `SECTINFO` lump is accepted syntax with no observable effect in this build.

### `points`: Domination-mode control points

`points` declares Domination-mode control points, stored as `SectInfo::Points`, an array of
`DPOINT_s` (`src/sectinfo.h`). Each entry's grammar is a nested block:

```text
points = {
    "Point A" = { 10-14, 20 },
}
```

- The string before `=` becomes the point's display name (`DPOINT_s::name`), with the same
  `$`-prefixed language-lookup rule as `names`' labels (`src/sectinfo.cpp:275-278`).
- The sector list directly follows the `=` and `{`, listing sector indices or ranges that belong
  to that control point, appended into `DPOINT_s::sectors` (`src/sectinfo.cpp:293-298`). There
  is no intervening `sectors` keyword — the parser reads range values directly into the point's
  sector array.

`DPOINT_s` carries three further fields (`owner`, `contesting`, `disabled`) that are never part of
the lump grammar at all - they are runtime-only state the Domination gamemode itself manages
(`src/domination.cpp`), reset at round start and updated as players occupy or leave a point's
sectors (`DPOINT_s::PlayerInsidePoint`, `src/sectinfo.cpp:61-76`).

Unlike `base0`/`base1`, `points` is read from several places: `src/domination.cpp` (the
whole scoring/ownership/contest state machine), `src/sv_main.cpp` (syncing point ownership and
state to a newly joined client, `src/sv_main.cpp:2769-2777`), `src/g_shared/st_hud.cpp` (the
Domination scoreboard widget), `src/g_game.cpp` (`GAME_CheckMode`: on a map with only team starts
and no flags or skulls, a non-empty `Points` force-enables `domination`, `src/g_game.cpp:2959`),
and `src/p_acs.cpp`. The ACS surface is `GetControlPointInfo` (a point's name, owner or disabled
state), `SetControlPointInfo` (owner or disabled state, refused in client mode),
`IsPlayerContestingControlPoint` (whether one player is in the point's `contesting` set, which
holds player numbers, not teams; `src/domination.cpp:141-143`), and `GetActorSectorLocation` with
`point == true` (the index of the point containing an actor's sector), at
`src/p_acs.cpp:7955-8070`. `points` is genuinely live and Domination-specific; `names` is
genuinely live but gamemode-agnostic; `base0`/`base1` are genuinely dead. All four keys live in the
same lump and section grammar, so none of the three claims above generalizes to the other keys.

## A parsing quirk: a range written high-to-low can write past the array it just resized

`SECTINFO_ParseNames` and `SECTINFO_ParseSectors` (the latter backs `base0`/`base1`) both resize
their backing array using `sc.Number` rather than the already-computed, swap-corrected
`range_end`:

```text
if (range_end < range_start)
    swapvalues(range_start, range_end)
if (array.Size() < range_end + 1)
    array.Resize(sc.Number + 1)   // not range_end + 1
for (i = range_start; i <= range_end; i++)
    array[i] = value
```

`sc.Number` still holds whatever the second number in the source text was, before the swap. For a
range written in ascending order (`2-5`) this is the same value as `range_end` and nothing goes
wrong. For a range written in descending order (`5-2`), `range_end` becomes `5` after the swap but
`sc.Number` is still `2`: the array is resized to hold indices `0..2`, then the fill loop writes
indices `3` through `5` into it anyway. `TArray`'s `operator[]` does no bounds checking at all in
either build configuration (plain pointer indexing, `src/tarray.h:126-129`), so this is a genuine
out-of-bounds write, not merely a wrong value. `SECTINFO_ParsePoints`' own range-to-`sectors`
handling computes its resize length from `range_start`/`range_end` directly and does not share
this bug. Practically: write `names` and `base0`/`base1` sector ranges low-to-high to avoid it
(and remember `base0`/`base1` currently have no effect regardless, per the dead-key finding
above).

## Engine-family divergence: no counterpart outside Zandronum

UZDoom/GZDoom-family engines do not parse `SECTINFO`, have no Domination gamemode to read `points`
into, and have no equivalent of the sector-label-lookup feature `names` backs.

## Wiki/engine divergence

The Zandronum Wiki's example format for `points` is correct, though the prose is internally
inconsistent on property naming. The wiki's `points` example shows `"First Point" = { 20 }` (a
direct sector-index list), which matches the actual Zandronum parser behavior (`src/sectinfo.cpp:
267-312`). The wiki's introductory text mentions "name" as the sector-label property, but both
the wiki's own example and the source use `names`; this appears to be a wiki documentation typo,
not an engine quirk.
