# ZScript load order and compile sequence

**Tier:** B
**Engine:** UZDoom 4.15pre / GZDoom-family — does not exist in Zandronum
**Provenance:** ZDoom Wiki `ZScript` (retrieved 2026-07-31, oldid=54245) + verified against the UZDoom source's `src/scripting/thingdef.cpp:422-475`.

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

- **Absolute paths:** `#include "Folder/File.zs"` — resolved relative to the mod's namespace.
- **Relative paths:** 
  - `#include "./File.zs"` — includes from the same directory as the current file.
  - `#include "../Folder/File.zs"` — includes from parent directories, repeating `../` to traverse up the hierarchy.

The include path resolver (`ResolveIncludePath` in the UZDoom source) handles these natively.

## File naming and conflict risk

**Unverified:** The wiki page warns about a risk of files like `ZScript/Const.txt` in a mod conflicting with the engine's own `ZScript/Const.txt` entries. The mechanism for this conflict (and how to mitigate it with a mod-specific namespace folder) is not yet verified against the local engine source.

## See also

- [`zscript-engine-availability.md`](zscript-engine-availability.md) — why ZScript is completely absent from Zandronum.
