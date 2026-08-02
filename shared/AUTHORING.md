# Shared authoring rules

**This file is the one copy of every rule that applies across all sections** (`acs/`,
`decorate/`, `zscript/`, `mapinfo/`, `gldefs/`, `sbarinfo/`, `cvarinfo/`, `console/`, `sprites/`,
and any lump-format section added later). Every section's own `CLAUDE.md` points here instead of
restating these rules — the original repo split `maintainer/PROCESS_INTAKE_FILE.md` out of
`maintainer/CLAUDE.md` for the same reason ("so there's only one copy to keep in sync"); the same
logic applies with more force across nine sections than it did across one. A section's `CLAUDE.md`
only covers what's specific to that section: its own layout, its own engine-source buckets or
inventory extractor, its own worked examples.

See `shared/ARCHETYPES.md` for the three doc schemas (Callable / Table-of-entries / Concept) this
file's rules apply to, and the root `CLAUDE.md` for how to find the right section.

## Why this exists

Signatures, flag names, property names, cvar names, and lump keys are all cheaply greppable from
compiler tables or engine source. What's expensive is *semantics* — parameter meaning, valid enum
values, units, failure behavior, fork-specific quirks, which engine actually implements a given
name — which otherwise means re-reading C++ every time the question comes up. This tree caches
that work once, per entry, across every ZDoom-family knowledge area, so it isn't redone per
session and isn't scoped to any single mod project.

## Locating the engine/compiler source

No file in this tree assumes a fixed absolute location for the actual engine/compiler checkouts
it cites — that differs per machine and per project. When you need to read the real source rather
than trust a citation:

1. **Check `sources.local.md` in the repo root** for a configured path (see `sources.example.md`
   for the format and the full key list — engines, compilers, and secondary sources like
   UltimateDoomBuilder/SLADE). Copy the example file yourself if `sources.local.md` doesn't exist
   yet and you know a path to fill in.
2. **If a key isn't configured, check for a same-named sibling directory** next to this repo
   (e.g. `../zandronum`, `../UZDoom`) — a common layout when this tree is checked out alongside
   the engine/compiler repos it documents.
3. **If neither turns up a checkout, don't guess and don't clone one yourself.** Tell the user you
   need the source for `<key>` and ask them to either point `sources.local.md` at a checkout or
   provide the information another way.
4. **Never attempt to fetch the Zandronum or ZDoom wikis directly** (`wiki.zandronum.com`,
   `zdoom.org/wiki`) — both are gated against automated access (an Anubis proof-of-work challenge
   returns HTTP 200 with a challenge page instead of content; the ZDoom wiki returns empty
   replies). This applies to every wiki-sourced knowledge area in this tree, not just ACS — a
   DECORATE, ZScript, or MAPINFO wiki page is exactly as unfetchable. Don't burn a fetch call on
   either; if a wiki page would genuinely help and isn't covered by a local checkout, say so
   explicitly instead of guessing.

## Engine scope

This tree is multi-engine. Every doc file (archetype 1/3) and every inventory row (archetype 2)
carries an **`Engine:`** field/column recording what it was verified against, because "verified"
only means something relative to an engine and a version.

**Zandronum is the primary target** (per the user; this is the version the consuming projects
currently ship against) — current target **Zandronum 3.2.1**. **UZDoom/GZDoom-family engines are
documented where Zandronum doesn't apply** — most importantly ZScript, which does not exist in
Zandronum at all (its DECORATE-only codebase traces to a ZDoom `2.8pre-441` baseline that predates
ZScript's introduction upstream). A ZScript doc's `Engine:` field never says Zandronum; say so
explicitly ("**Engine:** UZDoom 4.15pre / GZDoom-family — does not exist in Zandronum") rather than
leaving the field to imply portability it doesn't have.

Do not assume a doc verified for one engine holds for another, even within the same knowledge
area — DECORATE/MAPINFO/GLDEFS/SBARINFO/CVARINFO all diverge between Zandronum and the
GZDoom family, not just ZScript. A project retargeting engines should treat every doc tagged for
its old engine as unverified until re-checked, not as still-good.

Four caveats worth knowing before trusting or adding an `Engine:` claim:

- **The 3.2.1-target vs. 3.3-alpha-checkout gap.** The Zandronum source used to verify claims
  against "Zandronum 3.2.1" is a `master` HEAD checkout whose own `version.h` reports
  `3.3-alpha` — a development snapshot *ahead of* the 3.2.1 target, used only because it's the
  best available local source to read. This rarely matters (core engine behavior is stable across
  minor versions), but if a claim in this tree ever turns out not to hold on an actual 3.2.1
  client, the version gap is the first place to look. When a function/flag/key's name suggests a
  recent addition, check its introducing commit's ancestry against the 3.2.1 version-bump commit
  (`28f736fb3`, "changed the version string to 3.2.1") before stamping `Engine: Zandronum 3.2.1` —
  see `acs/concepts/event-scripts.md` for a worked example of a feature that exists in the
  `3.3-alpha` checkout but postdates 3.2.1.
- **Wiki-sourced material can describe a feature-ahead engine.** A `... - ZDoom Wiki.html` page
  describes upstream ZDoom, which is feature-ahead of every fork this tree targets — verify a
  claim's *existence* in the actual target engine's source before trusting its *behavior*. This
  generalizes past ACS: a ZDoom-wiki DECORATE/MAPINFO/GLDEFS page can legitimately describe a flag,
  property, or key that doesn't exist in Zandronum, or that exists in GZDoom/UZDoom but not
  Zandronum.
- **The local Zandronum working tree is not pristine.** It carries an applied ZandronumMCP
  integration patch — several modified tracked files including `src/p_acs.cpp` (+170 lines
  relative to upstream) plus untracked `src/mcp_*.cpp` files. Since claims are verified by reading
  that checkout, a cited `p_acs.cpp` line number may be shifted relative to a clean 3.2.1/3.3-alpha
  checkout elsewhere. `git diff` the relevant file in the local checkout before quoting a line
  number or adding a `**Source excerpt:**` block sourced from it, and don't assume line numbers
  cited here transfer to a different Zandronum checkout unmodified.
- **The local UZDoom checkout is behind its own upstream and is a GZDoom-family fork, not GZDoom
  itself.** It tracks `origin/trunk` but sits commits behind, and its own behavior can diverge from
  mainline GZDoom in ways not yet catalogued here. Treat `Engine: UZDoom 4.15pre` as exactly that
  — not a stand-in claim for "GZDoom" or "the ZDoom family" generally — until a claim has actually
  been cross-checked against a GZDoom checkout too.

## Tiers

Every doc file (archetype 1/3) or inventory row's `Tier` cell (archetype 2) is stamped with a
confidence tier:

- **A** — wiki-enriched and verified against fork source. Highest confidence.
- **B** — signature + prose from a secondary source (e.g. the UltimateDoomBuilder or SLADE
  language-definition files), verified against engine source. Good but not wiki-depth. Also used
  for a wiki-sourced concept page whose claims were spot-checked but not exhaustively traced (e.g.
  a claim about network/netcode internals too deep to fully verify in one pass — say so explicitly
  rather than silently calling it tier A).
- **C** — signature/name and type only. No prose yet. For archetype 2, this is the default state
  of every generated row until a `notes/` file promotes it.

Every tier-A/B file/row also carries an `Engine:` field/column (see "Engine scope" above).
Tier-C entries don't need one — they're derived from a compiler/engine table's existence, not
from reading behavior, so there's no version claim being made yet.

Tier-A entries require a wiki-sourced starting point produced by the maintainer-side intake
pipeline — see `maintainer/CLAUDE.md` if that directory exists in your checkout, and note the
intake pipeline is per-section-aware (`maintainer/_intake/<section>/`). **Tier-B and tier-C
entries don't require it** — anyone can add one straight from engine/compiler source.

## Writing a tier-B/C entry

1. **Pick a target** — a section's "not yet documented" list, or an entry missing entirely. Skim
   the section's `INDEX.md` first to confirm it isn't already documented under a different name.
2. **Classify its engine-source bucket** — see the section's own `CLAUDE.md` for what buckets
   exist there (e.g. ACS's compiler-builtin/action-special/extension-function split, or
   DECORATE's owning-class-and-flags-word split) — and read the real implementation.
3. **Apply the Authoring rule** (below): only write a file if it earns its cost over a one-line
   grep. Tier B needs prose from a secondary source verified against fork source; tier C is
   signature/name/type only and doesn't need source verification or an `Engine:` line.
4. **Stamp `Tier:`, `Provenance:`, and (for A/B) `Engine:`** directly under the file's H1 (see
   `shared/ARCHETYPES.md` for the exact block), and add the section `INDEX.md` line.
5. **If you quote engine/compiler source verbatim**, follow "Quoting engine/compiler source
   verbatim" below — this is not the same as an ACS/BCS/ZScript *usage example*, which is fine and
   unaffected.
6. **Run `python3 tools/lint_docs.py`** to catch a missing header field, a dangling `INDEX.md`
   link, or an unlicensed verbatim excerpt before considering the entry done.

## Authoring rule

A doc file must earn its context cost. If everything in it is recoverable from a one-line grep of
the signature/name, don't write the file — list it in the section `INDEX.md`'s flat
"not yet documented" block instead (or leave it as a bare inventory row for archetype 2). A file
should contain at least one of: parameter/argument semantics beyond the type, units (fixed vs int,
tics, map units, angle encoding), failure/error-return behavior, activator/pointer semantics,
netcode/clientside caveats, or known-broken-in-this-fork/this-engine notes.

**Family/group files (archetype 1).** A standalone file per callable is the default; a family
file groups several callables into one when doing so is warranted. In practice this tree uses
three distinct rationales, not just one — record which one applies when writing a new family file
rather than forcing every grouping into the same justification:

- **Mandatory sequence** — the callables can't be used in isolation (e.g. ACS's `lump-io.md`:
  Open/Read/ReadString/GetInfo/Close don't mean anything individually).
- **Shared implementation** — the callables are thin wrappers around the same underlying engine
  code (one `case` block, one static helper, one struct), so the real findings are identical
  across all of them and belong in one file rather than duplicated per-callable.
- **Shared root cause** — grouping happens *after* research, when several independently-looking
  callables turn out to share one underlying bug or missing feature (e.g. all three members are
  broken for the same reason).

Whichever rationale applies, a family/group file's whole point is covering every member — the
low-call-count or seemingly-unused members are exactly the ones nobody has figured out yet, so
document them anyway rather than stopping at the well-understood half.

**Stay project-agnostic.** This tree is shared across every Zandronum/GZDoom-family mod that reads
from it — it isn't owned by whichever project happened to trigger a given finding. Never name a
specific mod/project in a doc file, and never lift an example straight from a project's own code:
a crash found while reviewing one project's spawn logic gets written up as a generic call like
`ThingCount(species, tid)` with placeholder arguments, not as "in \<project\>'s director...". If a
claim only matters because of one project's own design choices (not the engine's or compiler's
behavior), it doesn't belong in this tree at all — flag it to the user instead of writing it here.

**Never write a machine-specific filesystem path into a doc file.** This tree is published and
cloned onto different machines with different local layouts, so an absolute or `~`-rooted path
(e.g. `~/source/zandronum/src/p_acs.cpp`) is dead weight for every reader but the one who wrote it.
Cite a source by name plus a repo-relative path instead — "the Zandronum source's `src/p_acs.cpp:123`",
"the UZDoom source's `src/common/scripting/frontend/zcc_parser.cpp`" — never the local checkout
root. This applies to prose, header fields, and inline shell-command examples alike.

## Quoting engine/compiler source verbatim

Citing a function/struct name and file:line (encouraged throughout this tree) is not the same as
reproducing its body in a fenced code block — the latter is a literal copy of someone else's
copyrighted source, not a citation, and this repo's `LICENSE` has to account for every file that
does it. If you quote a real function body, `case` block, struct, or enum verbatim from
engine/compiler source (as opposed to a usage example in ACS/BCS/DECORATE/ZScript, which is fine
and unaffected by this rule):

- Add a `**Source excerpt:**` field to the file, right after its `Tier:`/`Provenance:`/`Engine:`
  fields, stating which project the excerpt came from and pointing at the matching `LICENSE`
  section — e.g. `**Source excerpt:** This file quotes Zandronum engine source verbatim;
  reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.` (path depth
  varies by section; `§4` for zt-bcc/bcc compiler source).
- Do this for **Zandronum or zt-bcc/bcc source only** — see below for why `acc` and GPL-3.0
  sources are different. Both Zandronum and zt-bcc/bcc are permissively licensed and
  redistributing a short excerpt with notice is fine; `LICENSE` §3/§4 already carry the standing
  notice and source pointer this requires.
- If you're only restating what code *does*, write that in prose instead and skip the field
  entirely — simpler, and keeps the file lighter per the Authoring rule above.

**Never quote `acc` source verbatim.** The original Raven Software `acc` compiler (relevant to
base-ACS-only questions, as an alternative to zt-bcc/bcc) is not open source: its 1999 source
release EULA does not grant permission to redistribute the source or make derivative works, and —
unlike Heretic/Hexen — it was never relicensed under the GPL. Reading `acc` source to understand
base-ACS behavior and describing that behavior in your own words is fine (facts and behavior
aren't copyrightable); copying any of its actual code into a doc file's fenced block is not, and
there is no permissive-license fallback the way there is for Zandronum or zt-bcc/bcc. If `acc`'s
behavior needs a code example, write your own illustrative ACS, or paraphrase the logic in prose.

**Never quote GZDoom/UZDoom engine source or the ZScript standard library verbatim.** Both are
GPL-3.0 (the ZScript stdlib's own `wadsrc/static/zscript/zscript_license.txt` states this
explicitly for everything outside its `engine/` subfolder). Unlike Zandronum/zt-bcc-bcc, there is
no `**Source excerpt:**` escape hatch for GPL-3.0 material — reproducing a real function body,
VM opcode `case` block, or a ZScript class/struct declaration copied straight from the stdlib in a
fenced code block would place the doc file itself under GPL-3.0 obligations this tree's `LICENSE`
doesn't carry. Read this source freely to understand and verify behavior, and describe what it
does in your own prose or your own illustrative ZScript — but never paste it verbatim. This is a
hard rule with no exception, same as the `acc` rule above, for a different reason (license
incompatibility, not lack of a license at all).

## Version control

This repo is a single git repo (aside from the gitignored, independently-versioned `maintainer/`
directory — see its own `CLAUDE.md`). Remind the user to commit when a meaningful chunk of work is
done and nothing is staged/committed yet. Never run destructive git operations (`reset --hard`,
`clean`, `checkout --` over uncommitted changes, `push --force`, etc.) without explicit user
approval first. Never write a machine-specific filesystem path into a commit message or doc file
(see the Authoring rule above) — this repo is cloned onto machines you don't control.
