# DoomEdNums block

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28)
**Provenance:** ZDoom Wiki `MAPINFO/Editor number definition` (retrieved 2026-09-28, https://zdoom.org/w/index.php?title=MAPINFO/Editor_number_definition&oldid=54525) + verified against UZDoom source (`src/gamedata/g_mapinfo.cpp:2591-2602`, `src/gamedata/g_doomedmap.cpp:137-283`, `src/gamedata/info.cpp:556-573`, `src/d_main.cpp:3724-3726`, `src/scripting/thingdef.h:245`, `src/scripting/zscript/zcc_compile_doom.cpp:733-760`, `src/playsim/p_mobj.cpp:6576-6580,6645`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

A `DoomEdNums` block in MAPINFO maps editor thing numbers to actor classes. This feature allows modders to assign editor numbers to custom actors (especially those defined in ZScript), remap existing editor numbers to different actors, disable editor number mappings, and optionally attach action specials and arguments to the thing definition. This block exists only in UZDoom/GZDoom-family engines and has no equivalent in Zandronum.

## Syntax

```mapinfo
DoomEdNums
{
    <number> = <class> [, noskillflags] [, special] [, arg0 [, arg1 [, arg2 [, arg3 [, arg4]]]]]]
}
```

The block begins with the `DoomEdNums` keyword, then contains a list of editor number mappings enclosed in braces. Each mapping begins with an editor number, followed by an `=` sign and a class name or `None`, optionally followed by comma-separated modifiers.

### Parsing notes

- The `DoomEdNums` block is new-format-only; attempting to use it in old-format (Hexen-style) MAPINFO results in a fatal error ("doomednums definitions not supported with old MAPINFO syntax").
- An editor number can be mapped to one class only, but a single class can be assigned multiple editor numbers.
- An already-defined editor number can be mapped to nothing by using `None` instead of a class name, effectively removing that editor number from the editor thing list.
- An editor number can be mapped to a different actor by passing another actor name. Class names are resolved once at startup, after all MAPINFO and actor definitions are loaded: every unknown class is reported with its file and line, then startup aborts with "N unknown actor classes found" (`src/gamedata/g_doomedmap.cpp:253-283`).
- MAPINFO is parsed before actor definitions are registered, and a DECORATE actor that declares an editor number in its header is registered into the editor-number map afterward, overwriting any `DoomEdNums` entry for the same number (see "Conflict resolution with DECORATE" below).
- Repeating an editor number inside one block prints "Editor Number N defined more than once" and the later line wins. It is not fatal: the parser's "N errors encountered in DoomEdNum definition" check sits after a loop that only exits by returning on `}`, so it never runs. The same applies to the invalid-special and wrong-argument-count messages below.
- A class name starting with `$` names a special map-thing type instead of an actor class (the engine's own bundled MAPINFO uses this for things such as player starts); an unrecognized `$` name is a fatal error.

### Special flag values

- There is no range check on the editor number itself.
- **`noskillflags`**: a flag that must appear immediately after the editor number if present. When set, the engine ignores any map-level difficulty settings assigned to the thing and spawns it regardless of the current skill level (UZDoom source `src/playsim/p_mobj.cpp:6644-6648`).
- **Action special and arguments**: if an action special is provided, followed by arguments, the special and all its specified arguments (up to 5) are assigned to the thing at spawn time, and the engine enforces those arguments, preventing any arguments set on the map-placed thing from being used. If `ArgsDefined > 0` is set in the entry (which happens when special/args are parsed), the map's own arguments are discarded and replaced with the MAPINFO values (UZDoom source `src/playsim/p_mobj.cpp:6576-6580`). An unrecognized special name, or an argument count outside the named special's min/max, prints a script message but the entry is still inserted (see the unreachable error check above). A special given by number instead of name skips the argument-count check. A special with no arguments still marks all five arguments as MAPINFO-defined (zeros), so the map thing's own arguments are ignored.

### Special argument case: partial arguments and `+`

A `+` character can appear after any argument value to mark it as the last argument to be parsed, allowing a thing's map-set arguments to add to the MAPINFO-defined ones. For example, `11002 = GreenCard, Autosave, 1, 2, +` means arguments 0 and 1 come from MAPINFO (`1` and `2`), and arguments 2-4 can come from the map's thing definition. When `+` appears, `ArgsDefined` is set to the count of MAPINFO arguments up to that point, and the map's remaining arguments are used afterward (UZDoom source `src/gamedata/g_doomedmap.cpp:223-226`).

## Standard editor numbers

UZDoom's own bundled MAPINFO (`wadsrc/static/mapinfo/*.txt`, e.g. `doomitems.txt`, `heretic.txt`, `hexen.txt`, `strife.txt`, `common.txt`) defines the standard editor numbers as `DoomEdNums` blocks. Custom WADs later in the load order can remap these numbers or add new ones; a later block's entry with the same number silently overwrites the earlier one (no message for a cross-block overwrite, only for a repeat inside one block).

## Examples

### Mapping a custom actor to an editor number

```mapinfo
DoomEdNums
{
    11001 = MarblePillar
}
```

This assigns editor number 11001 to the custom actor `MarblePillar`, making it available in the editor thing palette.

### Mapping an editor number to a different actor (remapping)

```mapinfo
DoomEdNums
{
    2014 = Soulsphere
}
```

This remaps editor number 2014 (which is normally `HealthBonus` in Doom) to the `Soulsphere` actor instead. All map-placed things with editor number 2014 will now spawn `Soulsphere`.

### Disabling an editor number

```mapinfo
DoomEdNums
{
    64 = None
    65 = None
    66 = None
}
```

This disables editor numbers 64, 65, and 66 (Arch-vile, Chaingunner and Revenant in Doom 2). When set to `None`, attempting to place that editor number in a map has no effect; the thing does not spawn.

### Assigning an actor with an action special and arguments

```mapinfo
DoomEdNums
{
    11004 = IceDemon, Thing_Spawn, 0, 25, 0
}
```

This assigns editor number 11004 to `IceDemon` and attaches the `Thing_Spawn` special with arguments 0, 1, and 2 set to `0`, `25`, and `0` respectively. Editor attempts to override these arguments have no effect.

### Using noskillflags to force spawning regardless of skill

```mapinfo
DoomEdNums
{
    11002 = GreenCard, noskillflags, Autosave
}
```

This assigns editor number 11002 to `GreenCard` with the `noskillflags` flag and the `Autosave` special. The `noskillflags` flag ensures the actor spawns even if difficulty settings would normally filter it out, and the `Autosave` special is called when the thing spawns.

## Conflict resolution with DECORATE

When an actor is defined in DECORATE with an editor number (e.g., `ACTOR MyActor : Parent 1234 { ... }`) and a `DoomEdNums` block maps the same editor number to a different actor, the DECORATE-declared editor number wins, regardless of which lump loads first. The startup order is (UZDoom `src/d_main.cpp:3724-3726`):

1. All `DoomEdNums` entries, merged across every MAPINFO lump, become the editor-number map.
2. Every actor class then registers its own header editor number (only if its `Game` filter matches the current game), unconditionally overwriting any MAPINFO entry for that number. Only a DECORATE-vs-DECORATE collision prints a warning ("Editor number N defined twice"), and it isn't fatal.

### ZScript actors and DoomEdNums

ZScript classes can only get an editor number through a `DoomEdNums` block. ZScript's class header has no editor-number slot, and the DECORATE info properties (`SpawnID`, `ConversationID`, `Game`) are rejected in ZScript (the property category comment at UZDoom `src/scripting/thingdef.h:245` says so; the ZScript compiler skips `CAT_INFO` properties in `src/scripting/zscript/zcc_compile_doom.cpp:733-760`).

## Engine-family divergence

### DoomEdNums block: UZDoom-only

Zandronum does not support the `DoomEdNums` block in MAPINFO or ZMAPINFO lumps. Attempting to use it results in a fatal script error: "DoomEdNums: Unknown top level keyword" (Zandronum source `src/g_mapinfo.cpp:1999`), since Zandronum's MAPINFO parser does not recognize the keyword at all.

### Zandronum's alternative: DECORATE actor header editor numbers

Zandronum does not have a `DoomEdNums` block, but editor numbers are still defined in DECORATE. In Zandronum, each actor in DECORATE can declare an editor number directly in its header:

```decorate
ACTOR Soulsphere : Health 2013
{
    // actor properties
}
```

The editor number appears after the parent class name (and after a `replaces` clause, if any). Declaring a number another actor already uses takes it over:

```decorate
ACTOR MyCyberdemon : Cyberdemon 16
{
    // actor properties
}
```

This assigns editor number 16 (the Cyberdemon's) to `MyCyberdemon`. A `replaces Cyberdemon` clause would instead substitute the class everywhere it is spawned, whatever the editor number.

For Zandronum modders, all editor numbers must be declared in DECORATE actor headers; there is no MAPINFO equivalent to the `DoomEdNums` block, and no way to attach a fixed special, fixed arguments, or `noskillflags` to an editor number. Those have to be set per thing in the map.

## Known gaps

The following claims were not independently re-verified and are flagged for future review:

- The full behavior of min/max argument validation for named-string action specials (confirmed present but not exhaustively traced through both parsing and spawning).
