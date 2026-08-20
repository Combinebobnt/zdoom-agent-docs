# ZScript load order and compile sequence

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki `ZScript` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=ZScript&oldid=54245) + verified against the UZDoom source's `src/scripting/thingdef.cpp:405-458`; re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — no behavioral drift found. Also checked `src/common/scripting/frontend/zcc_compile.cpp`'s reworked `extend class`/`extend struct` handling (extension bodies are now pre-scanned and always compiled immediately after their target class/struct's own body, instead of being processed inline at their textual position) — that change only affects ordering within a single ZScript compile unit's own class/struct bodies and doesn't touch the ZSCRIPT-vs-DECORATE lump ordering or per-lump error handling this doc describes, so nothing here needed updating.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

## Lump loading

ZScript code is loaded from `ZSCRIPT` lumps in WAD/PK3 files. The engine treats `zscript` as a required file prefix — any file in a `zscript/` directory within a mod's ZIP/PK3 archive or a ZSCRIPT lump in a WAD will be processed. **Note:** The specific mapping of `zscript.txt` file paths within archives to ZSCRIPT lump resolution is not verified in the local UZDoom source; assume this follows GZDoom-family conventions but verify against your target engine if needed.

## Compile order with DECORATE

ZScript and DECORATE can coexist in the same mod, but **ZScript is compiled before DECORATE**. The engine processes ZSCRIPT lumps first (via `ParseScripts()`), then processes DECORATE (via `ParseAllDecorate()`). Consequence:

- **DECORATE classes can inherit from ZScript classes** — the ZScript definitions exist by the time DECORATE compilation starts.
- **ZScript classes cannot inherit from DECORATE classes** — the reverse is not possible at compile time.
- **Runtime spawning is unrestricted in both directions** — a ZScript actor can spawn a DECORATE actor, or vice versa, via engine function calls like `Spawn()` (no compile-time linkage required).

## Error handling asymmetry

**ZScript is strict unconditionally.** If any error occurs while compiling any ZSCRIPT lump, the engine calls `I_Error()` and aborts immediately, preventing compilation of any remaining ZSCRIPT lumps. Warnings are printed but do not halt. The engine's rationale (from the source code) is that later ZSCRIPT lumps are likely to depend on earlier ones, so a partial compile state is unusable.

**DECORATE strictness is user-configurable.** Whether DECORATE compilation errors halt the engine or allow execution depends on the `strictdecorate` console variable — ZScript has no equivalent setting.

## File inclusion

ZScript supports `#include` directives with both absolute and relative paths:

- **Absolute paths:** `#include "Folder/File.zs"` — looked up as a literal full archive path against the entire merged virtual filesystem (every currently-loaded WAD/PK3 together, not scoped to the mod that wrote the `#include`). This lookup ignores ZDoom-family lump namespaces entirely (those apply only to legacy short lump-name lookups); a full-path include is matched purely by its path string.
- **Relative paths:** 
  - `#include "./File.zs"` — includes from the same directory as the current file.
  - `#include "../Folder/File.zs"` — includes from parent directories, repeating `../` to traverse up the hierarchy.

The include path resolver (`ResolveIncludePath` in the UZDoom source) handles the relative-path rewriting; the resulting path is then resolved to a lump via the same full-path filesystem lookup absolute includes use, so both branches converge on one mechanism.

## File naming and conflict risk

Because absolute-path `#include`s resolve by full archive path across the *entire* merged filesystem rather than being scoped to the mod that references them, two loaded mods that happen to ship a file at the same path (e.g. both include `zscript/const.zs`) collide: the lookup returns exactly one match, decided by load order, with the most-recently-loaded matching file winning silently — the other mod's `#include` silently pulls in the wrong file's contents instead of erroring. A mod can avoid this by nesting its ZScript sources under a distinctively-named subfolder (e.g. `zscript/mymodname/...`) instead of reusing generic top-level names.

## See also

- [`zscript-engine-availability.md`](zscript-engine-availability.md) — why ZScript is completely absent from Zandronum.
- [`zscript-class-definitions.md`](zscript-class-definitions.md#class-extension) — "Class extension" section covers what a single `ZSCRIPT` lump's `#include` chain means for `extend class`/`extend struct` resolution, including a 5.0.0-pre regression where an extension whose base isn't found in the same compile unit now fails silently instead of raising the compile-time error it used to.
