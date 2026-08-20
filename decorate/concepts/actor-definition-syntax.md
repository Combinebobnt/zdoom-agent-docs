# Actor definition syntax

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-16)
**Provenance:** ZDoom Wiki "DECORATE format specifications" (retrieved 2026-07-31,
https://zdoom.org/w/index.php?title=DECORATE_format_specifications&oldid=52163), verified against the Zandronum source's top-level actor-header parser
(`src/thingdef/thingdef_parse.cpp:1018-1118`, `ParseActorHeader`). Per
`../../shared/AUTHORING.md`'s engine-scope caveats, the local checkout used to verify this is a
`master` HEAD reporting `3.3-alpha`, not a pristine 3.2.1 checkout, though this specific file
isn't touched by the applied ZandronumMCP patch.
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
- **`: parentclassname`** (optional): the class this actor inherits from — see `inheritance.md`.
  Defaults to `Actor` if omitted. The parser accepts either a space (`actor Foo : Bar`) or the
  colon fused directly onto either name as a single token (`actor Foo:Bar` / `actor Foo :Bar`) —
  `ParseActorHeader` explicitly splits on an embedded `:` in either the class-name or
  immediately-following token before falling back to reading a separate token, specifically so
  both spacing styles parse identically.
- **`replaces replaceclassname`** (optional): every *map-spawn* of `replaceclassname` becomes this
  actor instead — this operates above the doomednum table and doesn't require a duplicate
  doomednum. Per the wiki, this does **not** affect an actor created other than by map-spawning
  (e.g. given directly as an inventory item), and does not apply to a custom player class (player
  actors are handled through a separate mechanism). A class cannot list itself as its own
  replacement — the parser rejects `replaces` naming the same class being defined.
- **doomednum** (optional, bare integer): the map-editor thing number. Zandronum specifically
  requires it to fall in **`[-1, 32767]`** (`sc.Number>=-1 && sc.Number<32768`,
  `thingdef_parse.cpp:1083`) — a value outside that range is a script error, not silently clamped.
- **`native`** (optional keyword, undocumented on the wiki page): marks the actor as backed by a
  native (C++-implemented) class rather than a purely DECORATE-defined one. This is an
  engine-internal keyword used by the engine's own bundled actor definitions, not something a mod
  author writes.
- The actor name/parent/replaces tokens are parsed in the scanner's default (non-C) mode; only
  **after** those are consumed does the parser call `sc.SetCMode(true)` for the remainder of the
  definition (properties, flags, states) — this is why a period is legal in some pre-C-mode
  contexts but not case a mod author needs to worry about day to day, just a note on why the
  actor-header line is parsed slightly differently from the body that follows it.

## Comments and includes

- Both C-style comment forms are supported anywhere in a DECORATE lump: `//` to end of line, and
  `/* ... */` block comments. (Some external editing tools use a `//$`-prefixed comment convention
  for their own metadata; that's a tooling convention, not a DECORATE language feature.)
- `#include "path/to/lump"` pulls in another DECORATE lump's contents, and may appear anywhere
  **outside** an actor definition (not inside a `States{}` block or the actor's own braces). A
  common project layout keeps a single root `decorate.txt`/`DECORATE` lump that does nothing but
  `#include` every actor file under an `actors/` subfolder, which also lets the includes fix a
  precise load order for actors that reference each other. This directive's own parsing wasn't
  independently re-traced against Zandronum's source for this page — flagged as unverified below.

## Open questions (unverified in this checkout)

- The exact `#include` directive's parse-time behavior (e.g. path resolution rules, whether a
  missing file is a hard error) wasn't traced against Zandronum's source for this page — only the
  wiki's description is recorded above.

## Engine-family divergence

The `native` keyword behaves differently between the two engines. On Zandronum, it's accepted
silently and marks the actor as backed by a native C++ class — the mechanism the engine's own
bundled actor definitions use internally, not something a mod author is expected to write. On
UZDoom, the DECORATE parser still recognizes the `native` token after the doomednum, but only to
reject it with a script error ("Cannot define native classes in DECORATE") — native class
declarations live in ZScript there instead, not in DECORATE. A DECORATE lump that uses `native`
(deliberately or by copying an engine-internal example) compiles on Zandronum and fails to load on
UZDoom.
