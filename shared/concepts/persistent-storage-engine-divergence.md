# Persistent storage: Zandronum's ACS database has no UZDoom/GZDoom-family equivalent

**Tier:** B — the Zandronum-side half of this comparison is already tier A (see
[acs/families/database.md](../../acs/families/database.md)); the UZDoom-side half is
reverse-engineered directly from engine source, no wiki page covering it.
**Applies to:** UZDoom=yes, Zandronum=yes — the persistence *landscape* this file compares exists
on both engines (CVARINFO-archived cvars and `SavegameManager` both have real UZDoom-side
behavior, documented below); the one piece that is Zandronum-only is the ACS database itself — see
the "Zandronum-specific" section below for that narrower claim.
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** Zandronum side per `acs/families/database.md`'s own provenance. UZDoom side
verified against the UZDoom source's `src/playsim/p_acs.cpp` and `src/d_main.cpp`, and a
tree-wide search for `sqlite`/`database` finding no match outside menu/UI code unrelated to
persistence.

A script asking "how do I persist a value across engine restarts, outside a savegame" gets a very
different answer depending which engine it targets — this is exactly the kind of assumption this
tree exists to catch before it's carried across a fork boundary.

## Zandronum: a real, if unadvertised, SQLite-backed key/value store

Zandronum ships `za_database.cpp`/`.h` — a genuine SQLite-backed namespace/key/value database,
exposed to ACS via the `SetDBEntry`/`GetDBEntry`/`SetDBEntryString`/`GetDBEntryString`/
`IncrementDBEntry`/`GetDBEntryRank`/`GetDBEntries`/`SortDBEntries`/`CountDBResults`/
`GetDBResultKeyString`/`GetDBResultValueString`/`GetDBResultValue`/`FreeDBResults`/
`BeginDBTransaction`/`EndDBTransaction` function family — see
[acs/families/database.md](../../acs/families/database.md) (tier A) for full semantics, including
the crucial catch: **the database defaults to `:memory:`**, so out of the box nothing persists
across a restart despite how the wiki frames it, and ACS has no way to detect this at runtime.

## UZDoom/GZDoom-family: no equivalent at all, not even a degraded one

There is no `za_database`-equivalent anywhere in the UZDoom source — no SQLite dependency, no
`DATABASE_*`-shaped native function family, nothing. Two data points confirm this isn't a naming
difference or something implemented elsewhere:

- `PCD_WRITETOINI`/`PCD_GETFROMINI` still exist as **reserved enum values** in
  `src/playsim/p_acs.cpp` (opcode-numbering compatibility with other ACS-derived engines), but
  there is no `case PCD_WRITETOINI`/`case PCD_GETFROMINI` anywhere in the interpreter's dispatch —
  these opcodes are dead, not merely undocumented.
- ACS's console-command escape hatch — which could otherwise be (ab)used to shell out to some
  other persistence mechanism — is disabled outright on UZDoom/GZDoom-family:
  `PCD_CONSOLECOMMAND`/`PCD_CONSOLECOMMANDDIRECT` (`src/playsim/p_acs.cpp:10371-10374`) print a
  hardcoded red-text console message stating the engine doesn't support running console commands
  from scripts, then no-op instead of executing anything.

## The closest UZDoom/GZDoom-family analogue: CVARINFO-declared archived cvars

A mod-declared `CVARINFO` cvar defaults to `CVAR_MOD|CVAR_ARCHIVE` (`src/d_main.cpp`) — meaning it
is written into the player's config `.ini` and reloaded on next launch, unless the declaration
opts out (a `noarchive`-equivalent keyword; see `../cvarinfo/concepts/declaration-syntax.md` for
the Zandronum-side CVARINFO grammar this tree currently documents — **UZDoom's own CVARINFO
grammar, which differs from Zandronum's in its scope-keyword set, is not yet covered in that
section as of this writing**). From ZScript, this is reachable via the native `CVar` struct (see
[zscript/classes/cvar.md](../../zscript/classes/cvar.md)): `FindCVar`, the `Get*`/`Set*` accessor
pairs, and an explicit `SaveConfig()` to flush to disk immediately rather than waiting for engine
shutdown.

This is meaningfully weaker than Zandronum's database, on every axis that matters for anything
beyond simple settings storage:

| | Zandronum ACS database | UZDoom/GZDoom-family CVARINFO cvars |
|---|---|---|
| Key structure | Namespace + arbitrary string key, created at runtime | One fixed cvar name, declared ahead of time in a CVARINFO lump |
| Value shape | String (with numeric helpers) | Whatever the cvar's declared type is (int/float/bool/string/color) |
| Dynamic keys | Yes — `SetDBEntry(ns, key, ...)` with any runtime-computed key | No — every persisted value needs its own pre-declared cvar |
| Sorted/ranked queries | Yes — `GetDBEntryRank`, `GetDBEntries`/`SortDBEntries` | No |
| Reachable from ACS | Yes (the whole point) | No — only from ZScript (`CVar` struct); ZScript does not exist in Zandronum at all |
| Persists by default | No (`:memory:` unless the server operator configures otherwise) | Yes (`CVAR_ARCHIVE` is the default) |

## No generic file I/O either

Neither engine exposes a scripting-facing "open an arbitrary file and read/write bytes" API to
ACS or ZScript. A tree-wide search of `wadsrc/static/zscript/` for a `FileReader`/`FileWriter`
native class in UZDoom found none — the closest thing ZScript has to file access is the
savegame-specific `SavegameManager.ExtractSaveData()` reading two fixed entries out of a `.zds`
zip (see [zscript/classes/savegamemanager.md](../../zscript/classes/savegamemanager.md)), which is
not a general-purpose file API.

## Zandronum-specific: ACS database availability

This file's central finding, formalized: the `za_database`-backed function family documented in
[acs/families/database.md](../../acs/families/database.md) (itself stamped `Applies to:
UZDoom=no, Zandronum=yes`) exists only on Zandronum and has no counterpart, degraded or otherwise,
anywhere in the UZDoom/GZDoom-family lineage. Re-confirmed directly against the UZDoom source at
commit `5a9b0ec511` (2026-08-13, this file's `Verified against:` checkout):
`PCD_WRITETOINI`/`PCD_GETFROMINI` are still present only as reserved,
unimplemented enum values (`src/playsim/p_acs.cpp:295-296`, no matching `case` anywhere in the
file), and a fresh tree-wide, case-insensitive search for `sqlite`/`database` across the whole
UZDoom checkout (not just `wadsrc/`) turns up nothing persistence-related — the only hits are an
unrelated comment citing SQLite's Lemon parser generator in the ZScript compiler front-end
(`src/common/scripting/frontend/zcc_parser.cpp:291`) and an unrelated comment about anonymous
hardware-stats reporting (`src/d_anonstats.cpp:310`). Neither is a database feature under a
different name. On the ACS-availability axis specifically, `Applies to: UZDoom=no` is `no` in the
strongest sense this tree's vocabulary supports: not merely undocumented, but demonstrably absent
from the dispatch table and the dependency graph alike.

## Practical takeaway

A mod being ported from Zandronum to UZDoom/GZDoom (or vice versa) that relies on the ACS database
for cross-restart persistence (leaderboards, unlocks, per-player stats keyed dynamically) has no
drop-in replacement on the GZDoom-family side — it needs a redesign around either a fixed set of
pre-declared archived cvars (fine for a handful of scalar settings, unworkable for anything
keyed/dynamic) or accepting that the data simply won't survive a restart.
