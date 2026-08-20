# acs/ — ACS/BCS function docs

ACS/BCS engine function semantics for UZDoom/GZDoom-family (primary target) and Zandronum where
they diverge — see `../shared/AUTHORING.md`'s "Engine scope" — plus, via the `zt-bcc` compiler
fork, Zandronum's BCS superset (structs, enums, namespaces, strong types, pointers, and more on
top of base ACS; whether/how UZDoom's own ACS compiler supports BCS syntax hasn't been traced in
this tree — don't assume either way). **Read `../shared/AUTHORING.md` and
`../shared/ARCHETYPES.md` first** — this file only covers what's specific to ACS: the
engine-source bucket table, this section's layout, and the ACS-only tier-A intake quirks. Tiers,
the `Applies to:`/`Verified against:` engine-claim fields, licensing, and the Authoring rule are
defined once, there, for every section.

If the `zdoom-docs-lookup` subagent is registered, prefer delegating a lookup question to it
instead of reading this tree by hand — see the root [`AGENTS.md`](../AGENTS.md)'s "Subagents"
section.

## Layout

- `INDEX.md` — this section's router. Name → file path + one hook-shaped line. Read this first
  when routed here; everything else is read on demand.
- `functions/<name>.md` — one file per function (lowercase filename). Archetype 1 (Callable).
- `families/<topic>.md` — used instead of per-function files when grouping is warranted — see
  `../shared/AUTHORING.md`'s "Family/group files" for the three rationales this tree actually
  uses (e.g. `lump-io.md` is a mandatory sequence; `cvar.md` is shared implementation;
  `zdoom-math-stubs.md` is a shared root cause). Archetype 1.
- `concepts/<topic>.md` — general ACS/BCS knowledge not tied to one function's signature: script
  types, the client/server execution model, event scripts, language-level definitions. Archetype
  3. `concepts/crash-and-bug-checklist.md` is the ACS-specific crash/bug review index — read it
  before/during an ACS code review.

## The engine-source buckets

A function's semantics live in one of three places, depending on which table it's listed in. The
"How to recognize it" column is compiler-side (zt-bcc, Zandronum-only — UZDoom's own ACS compiler
hasn't been traced for an equivalent classification signal); both engines' "Where the behavior
lives" columns use the identical `case PCD_<NAME>:`/`FUNC(LS_<Name>)`/`case ACSF_<Name>:` shapes
`tools/engine_matrix.py`'s `BUCKET_PATHS` already keys off for staleness checks:

| Bucket | How to recognize it (zt-bcc) | Where the behavior lives (Zandronum) | Where the behavior lives (UZDoom) |
|---|---|---|---|
| Compiler builtin | Name appears in `zt-bcc/src/builtin.c`'s `g_funcs[]` | `src/p_acs.cpp`, `case PCD_<UPPERCASE_NAME>:` | `src/playsim/p_acs.cpp`, `case PCD_<UPPERCASE_NAME>:` |
| Action special | **Positive** index in `zcommon.bcs`'s `special` table | `src/p_lnspec.cpp`, `FUNC(LS_<Name>)` — usually has a `// Name (param, param, ...)` comment right after | `src/playsim/p_lnspec.cpp`, `FUNC(LS_<Name>)` |
| Extension function | **Negative** index in `zcommon.bcs`'s `special` table | `src/p_acs.cpp`, `case ACSF_<Name>:` | `src/playsim/p_acs.cpp`, `case ACSF_<Name>:` |

UZDoom's own index<->name declaration table (the engine-side analog of zt-bcc's compiler-side
`zcommon.bcs` `special` table) is `src/playsim/actionspecials.h`'s `DEFINE_SPECIAL(Name, Index,
min, normal, max)` list — confirmed present and structurally equivalent, just a different file
layout (`src/playsim/` vs. bare `src/`) than Zandronum's.

Always record which bucket a function is in — without it, a future session searching only
`p_acs.cpp` will wrongly conclude an action special is undocumented in the engine.

Two `zcommon.bcs` `special`-table parsing quirks worth knowing before trusting a signature pulled
from it: a declaration with **no return type at all** compiles to `raw`, not `void` (confirmed
against `zt-bcc/src/parse/dec.c`'s `read_special`, which defaults `return_spec = SPEC_RAW`) — e.g.
`Line_SetHealth`/`Sector_SetHealth`; and a positive-index entry with a trailing **`:0`** is
compiler-declared but not script-callable at all (linedef-only). Separately, a handful of negative
indices are declared **twice with two different names** in the same table — mainline Zandronum's
real function under one name, plus a same-numbered but otherwise-unrelated Q-Zandronum-only
addition under another (e.g. `-144` is both `ExecuteClientScript` and `SetEffectActor`; ten such
collisions exist, all in the file's `// Q-Zandronum` section). Since the engine dispatches purely
by that shared numeric index, calling the Q-Zandronum-only name on zt-bcc's `bcc` build would
silently invoke the *other* name's mainline implementation with mismatched arguments — worth a
closer look (and likely a `concepts/crash-and-bug-checklist.md` entry) before anyone tier-A/B's
one of those names.

## How tier-A entries are made

Tier-A entries are wiki-enriched: they start from a saved Zandronum/ZDoom wiki page (dropped into
`maintainer/_intake/acs/`) and get verified against fork source. See `maintainer/CLAUDE.md` if you
have that directory locally, and `../shared/AUTHORING.md`'s "Locating the engine/compiler source"
for why this tree never fetches the wikis directly.

## Writing a tier-B/C entry for ACS

Follow `../shared/AUTHORING.md`'s "Writing a tier-B/C entry" using the bucket table above for step
2. Tier B needs prose from something like the UltimateDoomBuilder `Zandronum_ACS.cfg` /
`ZDoom_ACS.cfg` files, verified against fork source.

## Generating the "Signature-only (tier C)" list

`INDEX.md`'s `### Signature-only (tier C)` block is generated by `python3 tools/gen_inventory.py
acs-signatures` from `zt-bcc`'s `special` table (`lib/zcommon.bcs`) and compiler-builtin table
(`src/builtin.c`'s `g_funcs[]`), cross-referenced against **both** engines' tables for presence —
Zandronum's `actionspecials.h`/`EACSFunctions`, and UZDoom's `src/playsim/actionspecials.h`/
`src/playsim/p_acs.cpp`'s `EACSFunctions` (the same UZDoom-side files the bucket table above
already names). A cross-referenced bullet carries a `Zan: yes/no, UZD: yes/no` pair, mirroring
DECORATE's inventory `Zan`/`UZD` columns — but see `INDEX.md`'s own note paragraph at the top of
the block before treating this as symmetric with those tables: the candidate universe is
`zt-bcc`-only (a UZDoom-only special/ACSF can never appear here), a compiler builtin only gets
the pair when it resolves to exactly one engine opcode (positional zt-bcc `g_deds[]` matching,
not name matching — several builtins are aliases of a differently-named opcode), and the pair is
explicitly **not** an `Applies to:`/`Verified against:` engine claim, just a name cross-reference.
Regenerating replaces only lines carrying `, auto-generated`; `CreateTranslation` is hand-added
there (a compiler keyword with no table entry, not caught by the generator) and survives a
regeneration.

While scoping the UZDoom cross-reference, also fixed a pre-existing bug in the Zandronum side:
`_acsf_names()` matched `ACSF_` only, silently skipping three of Zandronum's own `EACSFunctions`
entries that its `[TRSR]` Domination additions misspell `ASCF_` (`GetControlPointInfo`,
`SetControlPointInfo`, `GetSkinProperty` — `src/p_acs.cpp:5547-5549`), which had been printing a
false `not in this engine's ACSF enum` note for `SetControlPointInfo`. The same typo was already
found and fixed in `engine_matrix.py`'s `_ACSF_ENTRY_RE` on 2026-08-14 (see that file's comment)
but never ported to this generator until now — the two tools' extractors should be re-checked for
this kind of drift if either is touched again.
