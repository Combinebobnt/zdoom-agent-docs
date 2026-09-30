# SpawnNums block

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28)
**Provenance:** ZDoom Wiki `MAPINFO/Spawn number definition` (retrieved 2026-09-28, https://zdoom.org/w/index.php?title=MAPINFO/Spawn_number_definition&oldid=44293) + verified against UZDoom source (`src/gamedata/g_mapinfo.cpp:2603-2613`, `src/gamedata/g_doomedmap.cpp:361-457`, `src/gamedata/info.cpp:517-575`, `src/d_main.cpp:3725-3726`, `wadsrc/static/mapinfo/doomcommon.txt:89`) and Zandronum source (`src/g_mapinfo.cpp` top-level keyword dispatch, `src/thingdef/thingdef_properties.cpp:404-409`, `src/info.cpp:170-175`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

## Overview

A `spawnnums` block in MAPINFO maps spawn numbers (used by functions like `Thing_Spawn` and `Thing_SpawnFacing`) to actor classes. This allows modders to reassign or override the numeric spawn-ID assignments without modifying DECORATE or ZScript definitions.

## Syntax

```mapinfo
SpawnNums
{
  <number> = <class>
}
```

- Each line pairs a numeric spawn ID with an actor class name.
- A negative number or a number repeated inside one block prints a script message (the negative case says "must be positive", but `0` passes silently). Neither is fatal: the parser's "N errors encountered" check sits after a loop that only exits by returning on `}`, so it never runs, and the entry is inserted anyway. A later block or lump may reassign a number freely.
- The class name can be any actor type, or `None` to clear a previously-assigned spawn number. An unknown class name is fatal at startup, reported with its file and line.

## Example

```mapinfo
SpawnNums
{
  3001 = BerserkImp
  4489 = GoldenMug
  22594 = GoldenMug
}
```

In this example, spawn number 3001 is mapped to `BerserkImp` and spawn numbers 4489 and 22594 both map to `GoldenMug`.

## Clearing spawn numbers

```mapinfo
SpawnNums
{
  3 = None
  113 = None
}
```

This example clears spawn numbers 3 and 113 (the Baron of Hell and Hell Knight in UZDoom's own Doom table). Clearing prevents those actors from being spawned by spawn functions that identify actors by numeric spawn ID.

Spawn numbers are a separate namespace from editor numbers (`doomednums`): the Imp is editor number 3001 but spawn number 5. UZDoom's own base tables are themselves `spawnnums` blocks in the engine's bundled MAPINFO (`wadsrc/static/mapinfo/doomcommon.txt` for Doom), which is why a PWAD's block can reassign or clear them.

## Interaction with actor-declared SpawnID

DECORATE actors can also declare a spawn ID with the `SpawnID` property. ZScript classes can't (it is a DECORATE-only info property), so a `spawnnums` entry is the only way to give a ZScript class a spawn number. The startup order decides precedence (UZDoom `src/d_main.cpp:3725-3726`):

1. Every `spawnnums` entry from every MAPINFO lump, in load order, is merged into one table, a later entry for the same number replacing an earlier one. That table then becomes the live spawn table. A `None` entry just leaves its number out.
2. Every actor class then registers its own `SpawnID` (only if its `Game` filter matches the current game), **overwriting** any MAPINFO entry for that number.

So an actor-declared `SpawnID` always wins, and `N = None` can only clear a number that came from MAPINFO (including the engine's base table). It can't clear a number an actor claims for itself.

## Engine-family divergence

This feature is **UZDoom/GZDoom-family only**. Zandronum has no `spawnnums` keyword, so the block is an unknown top-level keyword there, which is fatal. Zandronum reads both `MAPINFO` and `ZMAPINFO` with the same parser, so there's no lump name that hides the block from it.

Zandronum assigns spawn IDs only through the actor `SpawnID` property (Zandronum source `src/thingdef/thingdef_properties.cpp:404-409`, registered in `src/info.cpp:170-175`), which it limits to 0-255 (a fatal error outside that range). For a mod targeting both engines, the actor property is the portable form.

## Notes

- Multiple spawn numbers can map to the same actor (as in the example above with `GoldenMug`).
- A `spawnnums` block in an old-format MAPINFO lump is a fatal error. In a lump whose format isn't settled yet, `spawnnums` itself switches it to the new format.
