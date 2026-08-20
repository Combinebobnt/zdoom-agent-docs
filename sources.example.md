# Local source checkout paths

This repo cites the engine/compiler source it verifies claims against (e.g. `src/p_acs.cpp:123`),
but never assumes a fixed absolute location for the actual checkouts — that differs per machine
and per project.

Copy this file to `sources.local.md` (already gitignored — never commit your real paths) and fill
in the absolute path to each checkout you have locally. Leave a path blank to skip it; an agent
that needs a source you haven't configured will say so and ask, rather than guess.

| Key | What it is | Your local path |
|---|---|---|
| `uzdoom` | UZDoom engine C++ source — the primary engine target across this tree (see `shared/AUTHORING.md`'s "Engine scope"); a GZDoom-family fork, and the local ZScript source of record (`zscript/`). **GPL-3.0** — read freely, never quote verbatim (see `shared/AUTHORING.md`) | |
| `gzdoom` | GZDoom engine C++ source proper — not currently checked out anywhere in this project's environment; UZDoom is used as the nearest available GZDoom-family stand-in. Also **GPL-3.0**, same quoting restriction as `uzdoom` | |
| `zandronum` | Zandronum engine C++ source — co-equal and fully verified secondary engine target (the version consuming projects currently ship on); used for DECORATE/MAPINFO/etc. divergence from UZDoom | |
| `zt-bcc` | zt-bcc/bcc — an ACS-superset compiler; this tree's current compiler target | |
| `zt-bcc.wiki` | zt-bcc's wiki (BCS language reference: Grammar, Declarations, Types, Functions, ...) | |
| `acc` | The original ACC compiler — an alternative to zt-bcc/bcc serving the same role (compiling ACS source), relevant when a question is about base-ACS behavior rather than a BCS-specific extension. **Not open source** (restrictive 1999 Raven Software EULA, never relicensed under GPL like Heretic/Hexen were) — read it to understand behavior and describe that behavior in your own words, but never copy any of its code into a doc file's fenced block. See `shared/AUTHORING.md`'s "Never quote `acc` source verbatim." | |
| `udb` | UltimateDoomBuilder — not an engine, but its `Build/Scripting/*.cfg` files are a first-party-adjacent tier-B prose source for nearly every lump format (DECORATE, MAPINFO, CVARINFO, SBARINFO, GLDEFS, ZSCRIPT, MENUDEF, KEYCONF, and more), verified against fork source same as any other tier-B entry | |
| `slade` | SLADE — likewise not an engine; its `dist/res/config/languages/*.txt` files are a secondary tier-B prose source, useful as a cross-check against UDB's `.cfg` files | |

This table isn't a fixed list — add a row for any other compiler or engine fork your project
actually uses (another ACS-superset compiler, a different ZDoom-family engine, etc.) so an agent
knows where to look for it.

If nothing is configured for a given key, an agent falls back to checking for a same-named sibling
directory in this repo's parent folder (`../zandronum`, `../zt-bcc`, etc.), and if that also comes
up empty, it'll tell you it needs the source rather than proceeding on a guess.
