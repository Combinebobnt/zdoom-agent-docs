# Actor definition syntax

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** ZDoom Wiki "DECORATE format specifications" (retrieved 2026-07-31,
https://zdoom.org/w/index.php?title=DECORATE_format_specifications&oldid=52163), verified against the Zandronum source's top-level actor-header parser
(`src/thingdef/thingdef_parse.cpp:1018-1118`, `ParseActorHeader`), `CreateNewActor`
(`src/thingdef/thingdef.cpp:80-172`), the DECORATE error-count abort (`src/thingdef/thingdef.cpp:349-360`),
spawn replacement call sites (`src/p_mobj.cpp:6119`, `src/p_mobj.cpp:5501`,
`src/thingdef/thingdef_codeptr.cpp:2150`, `src/p_acs.cpp:1287`) and the `#include` handler
(`src/thingdef/thingdef_parse.cpp:1239-1258`, `src/sc_man.cpp:156-164`, `src/w_wad.cpp:542-565`). Per
`../../shared/AUTHORING.md`'s engine-scope caveats, the local checkout used to verify this is a
`master` HEAD reporting `3.3-alpha`, not a pristine 3.2.1 checkout.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

This page covers the actor-declaration line and the overall lump structure a `States{}` block (see
`state-machine.md`) sits inside — not the state machine itself.

## Grammar

```text
actor classname [: parentclassname] [replaces replaceclassname] [doomednum] [native]
{
  properties
  flags
  states
}
```

- **`classname`**: the identifier the actor is spawned/referenced by. The wiki recommends keeping
  it a plain identifier (alphanumeric plus underscore, not digit-first) for portability, though
  the engine accepts a wider range of values.
- **`: parentclassname`** (optional): the class this actor inherits from. See `inheritance.md`.
  Defaults to `Actor` if omitted. The parser accepts the colon as a separate token
  (`actor Foo : Bar`) or fused onto a name (`actor Foo:Bar`, `actor Foo: Bar`, `actor Foo :Bar`).
  `ParseActorHeader` splits the class-name token on an embedded `:`. If the class name has none,
  it checks whether the next token starts with `:`. A colon with nothing after it makes the parser
  read the parent name from the following token, so all these spacing styles parse identically.
- **`replaces replaceclassname`** (optional): spawns of `replaceclassname` produce this actor
  instead. This operates above the doomednum table and doesn't require a duplicate doomednum.
  Replacement applies to every spawn that allows it, not only map things: map-placed things
  (`p_mobj.cpp:6119`), projectiles, `A_SpawnItem`-style spawns, ACS `Spawn`, puffs and fog all
  honor it. It does **not** apply to inventory given directly (ACS `GiveInventory`,
  `A_GiveInventory`, cheats: these spawn the item with replacement disabled,
  `thingdef_codeptr.cpp:2150`, `p_acs.cpp:1287`), and it does not apply to a custom player class
  (the player pawn is spawned with replacement disabled, `p_mobj.cpp:5501`; player classes are
  handled through a separate mechanism). A class cannot list itself as its own replacement. The
  parser reports "Cannot replace class X with itself" as a counted error, and loading aborts once
  parsing finishes (see doomednum below).
- **doomednum** (optional, bare integer): the map-editor thing number. It must fall in
  **`[-1, 32767]`** (`thingdef_parse.cpp:1083`). A value outside that range is not silently
  clamped: the parser prints "DoomEdNum must be in the range [-1,32767]" and counts an error.
  Parsing continues, but after all DECORATE lumps are read, any counted error aborts startup with
  "N errors while parsing DECORATE scripts" (`thingdef.cpp:357-359`). A doomednum of `0` is stored
  as no editor number, the same as `-1` or omitting it (`thingdef_parse.cpp:1100`).
- **`native`** (optional keyword, undocumented on the wiki page): an engine-internal keyword used
  by the engine's own bundled actor definitions, not something a mod author can use. See
  "Engine-family divergence" below for what each engine does with it.
- The actor name/parent/replaces tokens are parsed in the scanner's default (non-C) mode. Only
  **after** those are consumed does the parser call `sc.SetCMode(true)` for the remainder of the
  definition (doomednum, properties, flags, states). The source's stated reason is that C mode
  disallows periods, so reading the header in non-C mode lets actor and parent names contain a
  period while the body is tokenized as C.

## Comments and includes

- Both C-style comment forms are supported anywhere in a DECORATE lump: `//` to end of line, and
  `/* ... */` block comments. (Some external editing tools use a `//$`-prefixed comment convention
  for their own metadata; that's a tooling convention, not a DECORATE language feature.)
- `#include "path/to/lump"` pulls in another DECORATE lump's contents, and may appear anywhere
  **outside** an actor definition. It is only recognized at the top level of a lump
  (`thingdef_parse.cpp:1239-1258`); inside an actor's braces it is a fatal parse error. A common project layout keeps a single root `decorate.txt`/`DECORATE` lump that does
  nothing but `#include` every actor file under an `actors/` subfolder, which also lets the
  includes fix a precise load order for actors that reference each other.
- The path is a full path from the archive root, matched case-insensitively. It is not relative
  to the including lump. A name of 8 characters or fewer containing no `.` or `/` falls back to a
  plain lump-name lookup (`w_wad.cpp:542-565`). A missing target is a fatal startup error, "Could
  not find script lump '...'" (`sc_man.cpp:156-164`).
- When the including lump comes from the engine's own resource file, the engine refuses to let a
  mod file supply the included lump ("File ... is overriding core lump ..."). Includes from a mod's
  own lumps never hit this check.
- On Zandronum, every included lump is also marked for network authentication
  (`thingdef_parse.cpp:1255`).

## Engine-family divergence

The `native` keyword fails in both engines when a mod uses it, with different errors. On
Zandronum, it tells `CreateNewActor` (`thingdef.cpp:80-172`) to attach the definition to an
existing compiled-in C++ class of the same name. A name with no such class is a counted error
("Unknown native class '...'"). A class the engine's bundled definitions already set up is also an
error ("Redefinition of internal class '...'"), as is a parent that doesn't match the native
class's parent. Each of these aborts startup once parsing finishes. On UZDoom, the DECORATE parser
still recognizes the `native` token after the doomednum, but only to reject it with a script error
("Cannot define native classes in DECORATE"). Native class declarations live in ZScript there
instead, not in DECORATE. A DECORATE lump that uses `native` (deliberately or by copying an
engine-internal example) fails to load on both engines.
