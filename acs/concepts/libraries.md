# ACS libraries (`#library`, `#include`, `#import`, `LOADACS`)

**Tier:** B — spot-checked against fork source (the Zandronum source's `src/p_acs.cpp`, the zt-bcc source's `src/parse/library.c`, `src/codegen/chunk.c`), not an exhaustive trace of bcc's full namespace/import semantics (BCS's `using`/namespace-qualified imports go well beyond what this file covers).
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `_intake/Libraries - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=Libraries&oldid=42547`), verified 2026-07-29.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

## What the wiki gets right

- **`#library "NAME"`** marks the compiled lump as a library rather than a normal `BEHAVIOR`,
  and a library lump really is just an `FBehavior` loaded from the ACS-library WAD namespace
  (`ns_acslibrary`), never from `BEHAVIOR` — confirmed at the engine level. **Divergence: `bcc`
  does not actually enforce the wiki's "must be the first statement" rule.** `read_pseudo_dirc`
  threads a `first_object` bool through to `read_library(parse, pos, first_object)` (looks like
  positional enforcement is coming), but `read_library`'s body (`zt-bcc/src/parse/library.c:718-730`)
  never reads that parameter at all — grepped for every use of `first_object` in the file and it's
  passed in twice, read nowhere. **No positional check exists anywhere in `bcc`'s parse path** for
  `#library`'s placement (not independently confirmed by a compile test, only by reading the
  parser); it permits `#library` to repeat as long as every occurrence names the same
  library (`read_library_name` only bails on a *mismatched* name, "library has multiple names"),
  and separately enforces that the name is non-blank and globally unique across the whole
  compile ("duplicate library name"). An imported library missing `#library` entirely is still a
  hard compile error, just not a positional one — `read_imported_lib` bails with *"imported
  library missing #library directive"* if the flag `read_library` sets (`parse->lib->header`)
  never got set by the time the imported file finishes parsing.
- **`#include`** really does get compiled into the including module's own bytecode — it's
  textual inclusion at the compiler level, nothing engine-side ever loads an `#include`d file as
  its own lump. (This is about `#include`'s *linkage* model, distinct from
  [Constants](constants.md)'s finding that `bcc`'s `#define`/`#include` silently degrade to the
  weaker plain-ACS preprocessor form outside an `#if`/`#pragma raw include on` block — the two
  don't contradict each other, just cover different axes of `#include`'s behavior.)
- **`#import "path.acs"`** really is compile-time source-level (the *uncompiled* `.acs`, not the
  compiled lump) and really does result in a runtime cross-lump link: `zt-bcc` parses the
  imported file's namespace/declarations at compile time (`read_imported_lib`) *and* emits a
  `LOAD` chunk into the importing module's compiled output (`src/codegen/chunk.c`'s `do_load()`,
  which walks `library_main->dynamic` — the imported libraries — and `library_main->links`, the
  `#linklibrary`-forced ones) naming the library lumps that must be present and loaded at
  runtime. The engine parses that same `LOAD` chunk in `FBehavior`'s constructor
  (`p_acs.cpp:2667`, `MAKE_ID('L','O','A','D')`), looks each name up in `ns_acslibrary`
  (`Wads.CheckNumForName`), and recursively `StaticLoadModule`s it — matching the wiki's framing
  exactly.
- **`LOADACS`** is real and exactly as described: `FBehavior::StaticLoadDefaultModules`
  (`p_acs.cpp:2028`) scans every `LOADACS` lump, tokenizes it as a plain list of library lump
  names, and `StaticLoadModule`s each one unconditionally for every map — independent of whether
  any map script actually `#import`s it. More generally: a separately compiled library lump only
  becomes visible to a map's own scripts through one of two paths — `LOADACS` (unconditional,
  every map) or a `LOAD` chunk baked into the map's own `BEHAVIOR` by `#import`/`#linklibrary`
  (opt-in, per map-script) — and named-script calls (`Acs_NamedExecute` etc.) then resolve across
  *all* modules loaded by either path, regardless of which one brought a given library in. (Which
  of the two a typical library-lump/map-script split actually uses wasn't
  checked in this pass — not needed for this file, which documents the engine-side mechanism, not
  any particular project's wiring.)
- **Runtime missing-library is a soft failure, not a hard error**: if a `LOAD`-chunk-listed
  library lump can't be found at map-load time, the engine just `Printf`s *"Could not find ACS
  library %s."* and leaves that import slot unresolved (any function call into it silently stays
  unbound rather than crashing anything at load time) — matches the wiki's implicit framing.
  **Divergence from that:** a missing `#import` *source file* at compile time is not a soft
  failure at all — `bcc` hard-errors and bails out of the whole compile. The wiki doesn't
  distinguish these two "library not found" cases (compile-time source-file miss vs. runtime
  lump miss); they have completely different severity in this toolchain.

## Where the wiki is unverified or wrong for Zandronum

- **Cross-module number/name conflict resolution ("the one loaded last is used (Verification
  needed))" is backwards here — first-loaded wins, not last.** Both numbered and named script
  lookup *across modules* funnel through `FBehavior::StaticFindScript(script, module)`
  (`p_acs.cpp:3173`), which does a **linear scan over `StaticModules` in load order and returns
  the *first* match**:
  ```text
  for (DWORD i = 0; i < StaticModules.Size(); ++i) {
      const ScriptPtr *code = StaticModules[i]->FindScript(script);
      if (code != NULL) { module = StaticModules[i]; return code; }
  }
  ```
  (This is distinct from `FindScript`'s own *intra-module* rule a few lines above it — "if the
  preceding script has the same number, return it instead," a duplicate-within-one-module
  concern tied to how the compiler sorts one module's own script table — not chased further
  here.)

  `StaticModules` push order was verified end to end, not just inferred from a doc comment:
  `P_LoadBehavior` (`p_setup.cpp:3454`, called from `p_setup.cpp:4028`) always loads the level's
  own `BEHAVIOR` via `StaticLoadModule` first, and `StaticLoadModule`'s `FBehavior` constructor
  pushes itself onto `StaticModules` (`p_acs.cpp:2350`, `LibraryID = StaticModules.Push(this)
  << LIBRARYID_SHIFT`) *before* it parses its own `LOAD` chunk and recursively
  `StaticLoadModule`s any `#import`/`#linklibrary`-named libraries — so the map's own module
  reserves index 0 before any of its own imports can be pushed. Only afterward, back in
  `p_setup.cpp` (`4028` then `4087` in the same function, i.e. strictly later), does
  `StaticLoadDefaultModules` run the `LOADACS` scan and push those libraries on top. Net effect:
  **the map's own script always wins over any library defining the same script number**, and
  among libraries, whichever one was pushed to `StaticModules` earliest (import/LOADACS scan
  order) wins over one pushed later — the *opposite* of "last loaded wins." The wiki's own page
  flags this specific claim as unverified; the Zandronum engine's source resolves that: it's first-match,
  and the match order is determined by verified `StaticModules` push order, not by declaration
  order within any one file.
- **Cross-library function/map-variable import resolution (the `FNAM`/`MIMP`/`AIMP` chunks bcc
  emits and the engine resolves in `FBehavior`'s constructor, `p_acs.cpp:2694` onward) is a
  separate mechanism from script-number resolution above**, and it is first-match too, but for a
  different reason: it only fires for a symbol the *importing* module itself left unresolved
  (`func->Address == 0 && func->ImportNum == 0`), so only the first library in the importer's own
  `Imports` list that actually defines the symbol gets bound — a second imported library
  defining the same function name is silently never consulted. The wiki doesn't mention this
  path having any conflict behavior at all (it only calls out scripts as conflict-prone).
- **BCS/`bcc`'s `#import` is a much heavier mechanism than the wiki's ACC-era description
  implies.** The wiki frames `#import` as "grab the declared scripts/functions/`#libdefine`
  constants for use, nothing else." `zt-bcc` actually parses the *entire* imported source file
  into its own namespace tree at compile time (`read_imported_lib` → `read_module`, full
  recursive-descent parse, not a declarations-only skim) and layers BCS's namespace/`using`
  visibility rules — plus `private`/`internal` object hiding (`determine_hidden_objects`,
  `is_private_namespace`) — on top. This file does not trace that full system; treat any claim
  about BCS-specific import scoping beyond the plain wiki description as unverified here.
- **`#linklibrary` is a real `bcc`-only pseudo-directive the wiki page never mentions at all** —
  `zt-bcc/src/parse/library.c`'s `read_linklibrary`/`add_library_link`, also settable from the
  command line (`p_create_cmdline_library_links`). It forces a library name into the compiled
  `LOAD` chunk (via `library_main->links`, walked by the same `do_load()` that handles `#import`)
  without doing a compile-time source import at all — i.e. "make the engine load this library
  lump alongside me" without pulling in any of its declarations. Distinct from both `#import`
  (source-level, compile-time-checked, also produces a `LOAD` entry) and `LOADACS` (lump-side,
  unconditional for every map, no per-file opt-in).
- **`#libdefine` is real in `bcc`** (`zt-bcc/src/parse/token/info.c`'s keyword table;
  `library.c`'s directive dispatch routes both `TK_DEFINE` and `TK_LIBDEFINE` to the same
  `read_define`) but this file did not trace far enough to confirm any behavioral difference from
  plain `#define` beyond directive-dispatch identity — don't assume `#libdefine`'s
  library-export semantics are fully verified here, only that the token/keyword exists and is
  accepted.
- Not checked at all in this pass: the wiki's number/name-conflict claim technically covers
  *functions* too ("Functions" is listed as one of the imported element categories) — this file
  only verified the *script*-number case end-to-end. Given the `FNAM`/`MIMP` first-match behavior
  documented above, the same "first, not last" correction likely extends to functions, but that
  wasn't independently traced through a concrete conflicting-function-name scenario.

## `#import`ed macro state is isolated from the importer; `#include`d state is not

**Tier:** C — verified empirically with minimal fixture pairs and `#error` probes, not traced
through `zt-bcc` source. Worth confirming against `src/parse/token/source.c`'s macro-table
handling in a future pass.

- A `-D NAME` given on the `bcc` command line, and even an in-file `#define NAME` placed in the
  *importing* file before its `#import "lib.bcs"` line, are both invisible inside `lib.bcs`: an
  `#ifdef NAME` there evaluates false regardless, confirmed both ways with matching `#error`
  probes. The identical setup using `#include`/an implicit-`.bcs`-extension `#include "lib.h"`
  instead of `#import` propagates the macro correctly — the importer's macro table does not carry
  across an `#import` boundary, but does across an `#include` (pure textual inclusion, expected).
- Separately, a **bare, unguarded `#include` at global scope inside a file reached via `#import`
  is silently a no-op without `#pragma raw include on`** (or an enclosing `#if`/`#ifdef` block) —
  even though the *identical* unguarded global-scope `#include` works with no pragma at all when
  it's in the file `bcc` was invoked on directly (this is [Constants](constants.md)'s "plain ACS
  `#include`, global scope only" fallback form). Confirmed with an `#error` probe inside the
  target file: it did not fire without the pragma immediately preceding the `#include`, and did
  fire with it. Not traced to a source-level cause — plausible reading is that the "plain ACS
  `#include`, no pragma needed" fallback [Constants](constants.md) describes is a property of the
  file `bcc` was invoked on directly, not of files reached transitively via `#import`, but that
  hasn't been confirmed against `source.c`.

Practical consequence for anyone building an ACS/BCS library meant to be a transparent drop-in
replacement for an existing header (shadowing it via file placement or `-i` order, see
[Zandronum/UZDoom compatibility](zandronum-uzdoom-compat.md) for the broader porting context): a
single generated file cannot branch its own content on the *importer's* `-D` flags if any consumer
reaches it via `#import` rather than `#include` — target selection has to happen by which physical
file gets placed/shadowed, not by a macro guard inside a shared, `#import`-reachable file. And any
`#include` added programmatically into such a file needs its own `#pragma raw include on`
immediately before it, unconditionally, regardless of whether the file's own top-level consumers
needed one. Note this only concerns *declarations* (macros, `special` entries, constants) riding
along inside an `#import`-reached file — see the next section for why a real function *body* placed
the same way does not actually work, regardless of macro/pragma handling.

## `#import`ing a real function body always produces an unresolved cross-module reference, named library or not

**Tier:** C — verified empirically by parsing the compiled `.o`'s `FUNC` chunk directly (the
authoritative signal — see the warning below about what does *not* prove this), not traced through
`zt-bcc`/engine source.

An earlier pass at this entry claimed a **bare, unnamed** `#library` (no name at all) behaves
differently from a named one here — that a real function body inside an unnamed `#import`ed file
compiles directly into the importer's own object with a real address, no cross-module reference at
all. **That claim was wrong and has been retracted.** It was based solely on `strings` showing no
library-name text in the output, which does not distinguish "inlined with a real body" from
"emitted as an unresolved stub with no name to even print." Checking the actual `FUNC` chunk
(`argc`/`local_count`/`addr` fields per function, address `0` marking an unresolved import — see
[the ACSe object format](acse-object-format.md) for the chunk layout) shows the true state:

- `#import`ing a file — **named or unnamed**, no difference observed — that declares a real
  function body produces a `FUNC` entry in the *importer's* object with `addr == 0`: an unresolved
  cross-module reference, not an inlined body. Confirmed on both a named (`#library "SOMENAME"`)
  and a bare, unnamed (`#library` with no argument) case, each with a single trivial function
  (`return a + b`-shaped), each showing `addr == 0` for that function in the importer's compiled
  output.
- The named case additionally embeds the library's name as a string in the output (from the
  `LOAD`-chunk mechanism the rest of this file already documents) — something the engine can
  resolve against at runtime via `LOADACS`/an explicit `#import`/`#linklibrary`-driven load. **The
  unnamed case has no name to bind against at all**, so there is no error at compile time (the
  reference is accepted the same way any cross-module reference is) but no evident way for that
  reference to ever resolve at runtime either — this was not tested in-engine, so "does it crash,
  no-op, or Printf a warning like the named-but-lump-missing case" is unconfirmed, only that the
  compiled object never contains a real body for that function regardless.

**Practical consequence:** there is no way to attach a real function *implementation* to an
existing `#import`-reachable header and have it actually execute — not by keeping the header
unnamed, not by any naming choice found so far. A real function body only compiles with a resolved,
nonzero address when it lives in a file reached exclusively via `#include` (pure textual inclusion,
already documented elsewhere on this page as producing no cross-module reference at all). Anyone
needing to add real behavior to something reached by `#import` needs either an explicit
`#include` of the implementation from the *importing* file itself (a real source change at the call
site, however small), or a genuinely separate named library loaded via `LOADACS`/`#linklibrary`
with the runtime-loading cost that implies — not a same-file trick riding along on the header's own
`#import`.

**Verification note for future work on this file:** `strings`-based or exit-status-based checks on
compiled `.o` output cannot distinguish an inlined real function body from an unresolved,
zero-address stub — both compile cleanly, and an unresolved stub's function *name* still appears in
the object's `FNAM` table either way. Only the `FUNC` chunk's per-function address field (or
equivalent structured parsing) tells the two apart.

## File-resolution search order for `#include`/`#import`, and a real-world install caveat

**Tier:** B for the algorithm (read directly from `zt-bcc/src/task.c`'s
`identify_file_relative`); C (environment-specific, not a language fact) for the wrapper caveat.

Given a relative path in `#include`/`#import`, `bcc` searches, in this order, returning the first
match:

1. The directory of the file containing the `#include`/`#import` directive itself (not the
   directory of the file `bcc` was originally invoked on — each nested `#include`/`#import`
   re-anchors to its own containing file).
2. Every `-i`/`-I` directory, **in the order given on the command line**.
3. The compiler's own default library directory (wherever `bcc`'s own binary lives, plus `/lib`).

For `#include "name.h"` specifically (extension `.h`), `bcc` first tries `name.h.bcs` through this
same search, then falls back to the literal `name.h` — so a `name.h.bcs` file can transparently
answer a mod's existing `#include "name.h"` without that mod needing any of its own source
changed, as long as it wins step 1 or step 2 above.

**Caveat that has bitten a real setup:** a `bcc` found on `PATH` is not necessarily the compiler
binary — it can be a thin wrapper script that injects its own `-i <stdlib dir>` ahead of whatever
`-i` a caller supplies (e.g. `exec /path/to/real-binary -i /path/to/stdlib "$@"`). Since step 2
above is order-sensitive and first-match-wins, a caller's own `-i <shadow dir>` appended after such
a wrapper's injected one **never wins** a file that exists in both places — the wrapper's `-i` is
checked first and already satisfies the search. This is invisible from the caller's side: no
error, no warning, just silent resolution to the wrapper's own stdlib copy instead of the shadow.
Two ways around it, both confirmed working: (a) rely only on step 1 (place the shadow file in the
same directory as the file that includes/imports it — this always wins regardless of any wrapper),
or (b) invoke the underlying compiler binary directly, bypassing the wrapper entirely, with the
shadow directory as the *first* `-i` argument. Before trusting a plain `-i`-based shadow/override
strategy in any given environment, check whether `bcc` on `PATH` is a wrapper (`file $(which bcc)`
or read it if it's a script) rather than assuming step 2's ordering is fully caller-controlled.

## See also

- [Named script execution](../families/script-execution.md) — the `Acs_NamedExecute*` family that
  actually triggers the `StaticFindScript` resolution documented above.
- [Script types](script-types.md) — `LOADACS`-loaded libraries really do run their own
  `ENTER`/`OPEN` scripts on every map, confirming the wiki's note: `FBehavior::StaticStartTypedScripts`
  loops over every entry in `StaticModules` with no library/non-library distinction
  (`p_acs.cpp:3378-3381`, `StaticModules[i]->StartTypedScripts(type, ...)`), so a library module
  gets its typed scripts started exactly like the map's own `BEHAVIOR` would.

## Engine-family divergence

The compiler-side half of this page (`bcc`/`zt-bcc` behavior — `#library` placement and
uniqueness, `#import` vs `#include` linkage and macro isolation, `#linklibrary`, `#libdefine`, the
`FUNC`-chunk finding, the `#include`/`#import` file-search order) is engine-independent: it
describes what lands in the compiled object, not what any engine does with it, and is unaffected
by which engine eventually loads that object.

The engine-side half holds on UZDoom too, but **most of the *static* entry points this page cites
have been renamed** by the GZDoom-family refactor, so grepping those specific names in UZDoom finds
nothing — not every symbol, though: `ns_acslibrary` (the load-order namespace, cited above and
below) is unrenamed and greps fine as-is (`FileSys::ns_acslibrary`, `p_acs.cpp:2602` on UZDoom),
and the table below's `StaticModules` row keeps its own member name, just moved to a different
class. Zandronum's file-scope statics on `FBehavior` are instance members of a per-level
`FBehaviorContainer` (reachable as the level's own `Behaviors` object) in UZDoom's
`src/playsim/p_acs.cpp`:

| Zandronum (`src/p_acs.cpp`, `src/p_setup.cpp`) | UZDoom (`src/playsim/p_acs.cpp`, `src/maploader/maploader.cpp`) |
|---|---|
| `FBehavior::StaticFindScript` | `FBehaviorContainer::FindScript` |
| `FBehavior::StaticLoadModule` | `FBehaviorContainer::LoadModule` |
| `FBehavior::StaticLoadDefaultModules` | `FBehaviorContainer::LoadDefaultModules` |
| `FBehavior::StaticStartTypedScripts` | `FBehaviorContainer::StartTypedScripts` |
| `FBehavior::StaticModules` (file-scope static array) | `FBehaviorContainer::StaticModules` (member array, one container per level) |
| `P_LoadBehavior` | `MapLoader::LoadBehavior` |

Confirmed structurally unchanged behind those renames, each read directly in UZDoom source: for
both of the load paths documented above (`LOADACS` and a `LOAD` chunk), library lumps are looked up
only in the ACS-library namespace (`ns_acslibrary`) and the map's own `BEHAVIOR` is loaded from the
map's own lump, never from that namespace; the `LOAD` chunk is parsed
in the module's own initialization and recursively loads each named library; a `LOAD`-listed lump
that can't be found is still a soft failure with the same "could not find ACS library" console
message and an unresolved import slot; `LOADACS` is still scanned across every loaded file and each
listed name loaded unconditionally for every map; cross-module script lookup is still a linear
first-match scan over the module array in push order; the push happens before the module parses its
own `LOAD` chunk, and the map loader still loads the map's own `BEHAVIOR` before running the
`LOADACS` scan — so **the "first loaded wins, and the map's own script beats any library's" result
documented above is the same on UZDoom**; and typed-script startup still loops every module with no
library/non-library distinction. The one thing that does *not* carry over unchanged is the count of
load paths, and with it this page's opening "`ns_acslibrary`, never `BEHAVIOR`" framing — see the
third path immediately below, which is looked up in a different namespace entirely.

**Third load path, UZDoom only: the MAPINFO `loadacs` map key.** The "a library lump only becomes
visible through one of two paths (`LOADACS` or a `LOAD` chunk)" statement above is a Zandronum
fact, not a portable one. UZDoom's MAPINFO map block accepts `loadacs = "LUMPNAME"`
(`src/gamedata/g_mapinfo.cpp`'s map-option table, stored on the level info), and the map loader
loads that lump as an ACS module immediately after the `LOADACS` scan
(`src/maploader/edata.cpp`'s `MapLoader::LoadMapinfoACSLump`, called from
`src/maploader/maploader.cpp`'s level-load sequence). Zandronum has no such map option at all —
its MAPINFO parser has no equivalent key and its level-info struct has no field for one. Four
properties of this path are worth knowing before using it:

- **It is looked up in the *global* lump namespace, not `ns_acslibrary`** — the key's lookup passes
  no namespace, which defaults to global. Those two namespaces are disjoint for this purpose: a
  namespace-qualified request can fall back to a global lump, but a global request never falls back
  into a special namespace. So a `loadacs` key **cannot** reach a library stored the conventional
  way (a pk3's `acs/` folder, or a WAD lump between `A_START`/`A_END`) — it only finds a library
  placed at a pk3's root or as a plain unmarked WAD lump. The reverse is also true: `LOADACS` and
  `LOAD`-chunk lookups can't see a root-level pk3 file that a `loadacs` key can.
- **A missing lump is silently ignored** — no console message at all, unlike both other paths
  (`LOADACS` prints an "autoloaded ACS library" warning, a `LOAD` chunk prints the
  "could not find ACS library" one). A typo'd `loadacs` key produces no diagnostic whatsoever.
- **It is pushed last**, after the map's own `BEHAVIOR`, that module's imports, and every `LOADACS`
  library — so under the first-match rule above it loses every script-number conflict against all
  of them.
- **Unless the same lump was already loaded**, in which case module loading dedupes by lump number
  and returns the existing module: the library keeps whatever earlier index it already had, and a
  `loadacs` key naming an already-`LOADACS`ed lump changes nothing.

**Scoped correction to the `FNAM`/`MIMP`/`AIMP` bullet above, as read in UZDoom source:** the
"only fires for a symbol the importing module left unresolved" guard applies to the **function**
(`FNAM`) loop only. The map-variable (`MIMP`) and array (`AIMP`) loops run inside the same
per-imported-library iteration but bind unconditionally whenever the library has a matching *name
table entry*, overwriting any binding an earlier import already made. (The function path is
stricter in a second way too: it re-checks that the library really defines the function rather than
merely importing it itself; the map-variable and array paths have no equivalent check.) So imported
**map variables and
arrays are last-match, the opposite of imported functions**. Two libraries exporting the same map
variable name resolve to the one listed later in the importing module's own import order, while two
exporting the same function name resolve to the earlier. This was verified in UZDoom for this pass;
the bullet above predates it.
