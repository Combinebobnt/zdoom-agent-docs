# ACS libraries (`#library`, `#include`, `#import`, `LOADACS`)

**Tier:** B — spot-checked against fork source (the Zandronum source's `src/p_acs.cpp`, the zt-bcc source's `src/parse/library.c`, `src/codegen/chunk.c`), not an exhaustive trace of bcc's full namespace/import semantics (BCS's `using`/namespace-qualified imports go well beyond what this file covers).
**Engine:** Zandronum 3.2.1 (mechanism verified in the `master`/`3.3-alpha` checkout at the Zandronum source; nothing found here is gated behind a post-3.2.1 commit).
**Provenance:** `_intake/Libraries - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=Libraries&oldid=42547`), verified 2026-07-29.
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

## Where the wiki is unverified or wrong for this fork

- **Cross-module number/name conflict resolution ("the one loaded last is used (Verification
  needed))" is backwards here — first-loaded wins, not last.** Both numbered and named script
  lookup *across modules* funnel through `FBehavior::StaticFindScript(script, module)`
  (`p_acs.cpp:3173`), which does a **linear scan over `StaticModules` in load order and returns
  the *first* match**:
  ```
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
  flags this specific claim as unverified; this fork's source resolves that: it's first-match,
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

## See also

- [Named script execution](../families/script-execution.md) — the `Acs_NamedExecute*` family that
  actually triggers the `StaticFindScript` resolution documented above.
- [Script types](script-types.md) — `LOADACS`-loaded libraries really do run their own
  `ENTER`/`OPEN` scripts on every map, confirming the wiki's note: `FBehavior::StaticStartTypedScripts`
  loops over every entry in `StaticModules` with no library/non-library distinction
  (`p_acs.cpp:3378-3381`, `StaticModules[i]->StartTypedScripts(type, ...)`), so a library module
  gets its typed scripts started exactly like the map's own `BEHAVIOR` would.
