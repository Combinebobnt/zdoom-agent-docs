# Shared authoring rules

**This file is the one copy of every rule that applies across all sections** (`acs/`,
`decorate/`, `zscript/`, `mapinfo/`, `gldefs/`, `sbarinfo/`, `cvarinfo/`, `console/`, `sprites/`,
and any lump-format section added later). Every section's own `AGENTS.md` points here instead of
restating these rules — the original repo split `maintainer/PROCESS_INTAKE_FILE.md` out of
`maintainer/CLAUDE.md` for the same reason ("so there's only one copy to keep in sync"); the same
logic applies with more force across nine sections than it did across one. A section's `AGENTS.md`
only covers what's specific to that section: its own layout, its own engine-source buckets or
inventory extractor, its own worked examples.

See `shared/ARCHETYPES.md` for the three doc schemas (Callable / Table-of-entries / Concept) this
file's rules apply to, and the root `AGENTS.md` for how to find the right section.

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

**UZDoom is the primary target.** A six-phase retarget (approved 2026-08-08) moved it there from
Zandronum; the marking pass that makes the claim honest tree-wide has landed. Behavior
re-verification against UZDoom source has not — see `maintainer/TODO.md`'s "Retarget primary
engine: Zandronum -> UZDoom" entry (maintainer-only) for live phase status before trusting any
doc's UZDoom-side *behavior* claim specifically. Zandronum stays **co-equal and fully verified**,
not grandfathered — the consuming projects still ship on it.

**State the engine claim as this pair — the only legal form.**

```markdown
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @fbad53bff5 (2026-08-08); Zandronum 3.2.1 @28f736fb3 (2026-07-28)
```

`Applies to:` says where the feature exists; `Verified against:` says whose source was actually
read and at what revision, and — the stamp-what-you-read rule — names only engines whose source
you personally read for this entry, at the version/SHA/date of the checkout you read it from,
never retro-updated when that checkout later advances. `shared/ARCHETYPES.md` has the exact
grammar; `tools/lint_docs.py` hard-errors on a file carrying only half the pair.

**The legacy single-field `**Engine:**` form is retired.** The two fields came apart from it
because a single prose field could not express "exists on both engines, but only Zandronum's
behavior was checked" — the honest state of most of this tree, and still the right shape to stamp
when a re-verification pass only actually reads one engine's source (see `**Verified against:**`
above). The UZDoom retarget's Phase 5 sweep (completed 2026-08-17) re-verified every file off the
legacy field; `tools/lint_docs.py` now hard-errors on any `**Engine:**` field, new or old. The
tiny residual set in `maintainer/deferred_set.txt` (3 files, regenerated by
`maintainer/tools/stamp_applies_to.py`, never hand-edited) already carries the modern pair too —
that file now just tracks entries the tooling's own bookkeeping still calls "deferred" for
narrower reasons (see the script's own comments), not files still on the legacy field.

**Settled 2026-08-14 (Phase 3, step 3.1): stamp new UZDoom claims as `UZDoom 5.0.0-pre`, not
`4.15pre`.** The tree had split 40 files on the older `4.15pre` against 88 already on `5.0.0-pre`
before this was written down — `5.0.0-pre` is both the majority form already in use and the
`trunk` checkout's actual current `VERSIONSTR` (see the caveats below). A file's *existing*
`4.15pre` stamp is a real historical claim, not an error, and is not worth mass-rewriting for its
own sake — this only governs what a new stamp writes.

**UZDoom/GZDoom-family engines are documented in full; Zandronum is documented where UZDoom's
ZScript-first codebase doesn't apply** — most importantly ZScript itself, which does not exist in
Zandronum at all (its DECORATE-only codebase traces to a ZDoom `2.8pre-441` baseline that predates
ZScript's introduction upstream). A Zandronum-only doc's engine claim says so explicitly
(`**Applies to:** UZDoom=no, Zandronum=yes` plus a divergence section — see below) rather than
leaving the field to imply portability it doesn't have.

Do not assume a doc verified for one engine holds for another, even within the same knowledge
area — DECORATE/MAPINFO/GLDEFS/SBARINFO/CVARINFO all diverge between Zandronum and the
GZDoom family, not just ZScript. A project retargeting engines should treat every doc tagged for
its old engine as unverified until re-checked, not as still-good.

**Canonical divergence-heading forms**, required on any file whose engine claim says `UZDoom=no`
(`tools/lint_docs.py` enforces the co-occurrence; see "Divergence headings" below for what belongs
in each): `## Engine-family divergence`, optionally suffixed (`: <topic>`), for engine-vs-engine
behavior differences; `## Zandronum-specific: <topic>`, always suffixed, for behavior that exists
only on Zandronum and needs its own name rather than a generic "divergence" label; `## Wiki/engine
divergence`, optionally suffixed, for the distinct case of a wiki page describing behavior the
actually-verified engine source doesn't match — see "Wiki provenance" below for why that is a
different axis from engine-vs-engine and must never be collapsed into it.

Five caveats worth knowing before trusting or adding an engine claim, in order of how directly
they bear on the primary engine:

- **The local UZDoom checkout is behind its own upstream and is a GZDoom-family fork, not GZDoom
  itself.** It tracks `origin/trunk` but sits commits behind, and its own behavior can diverge from
  mainline GZDoom in ways not yet catalogued here. Treat `UZDoom 5.0.0-pre` as exactly that — a
  claim about UZDoom's `trunk` checkout, not a stand-in for "GZDoom" or "the ZDoom family"
  generally — until a claim has actually been cross-checked against a GZDoom checkout too.
- **The playtested binary can be ahead of the `trunk` checkout.** `trunk`'s `src/version.h` reports
  a static `VERSIONSTR` (`"5.0.0-pre"` as of the `trunk` checkout stamped 2026-08-13
  @`5a9b0ec511`) that never advances to match tagged release-candidate builds, because those are
  cut from a separate `5.0` stabilization branch (confirmed: `5.0.0-rc.1` @`7b8bea8098`,
  2026-07-28, and `5.0.0-rc.2` @`2c6ed9be22`, 2026-08-11 — neither reachable from `trunk`'s current
  HEAD). A claim verified by reading the `trunk` checkout is not automatically verified against
  whatever `5.0`-branch rc build is actually installed and played; if a claim's behavior looks
  version-sensitive, check the `5.0` branch's tag history rather than assuming trunk-checkout
  behavior transfers.
- **Wiki-sourced material can describe a feature-ahead engine — now mostly a Zandronum-side
  caveat.** The ZDoom Wiki describes upstream ZDoom/GZDoom-family behavior, which is UZDoom's own
  lineage — so for the primary engine, a wiki claim's *existence* usually does hold, though its
  *behavior* still needs a source check against UZDoom's own divergences. The gap is now mostly
  on the Zandronum side: a ZDoom-wiki DECORATE/MAPINFO/GLDEFS page can legitimately describe a
  flag, property, or key that doesn't exist in Zandronum, or whose Zandronum behavior differs from
  what the wiki (describing the feature-ahead GZDoom-family lineage) says.
- **The 3.2.1-target vs. 3.3-alpha-checkout gap, secondary-engine only.** The Zandronum source used
  to verify claims against "Zandronum 3.2.1" is a `master` HEAD checkout whose own `version.h`
  reports `3.3-alpha` — a development snapshot *ahead of* the 3.2.1 target, used only because it's
  the best available local source to read. This rarely matters (core engine behavior is stable
  across minor versions), but if a claim in this tree ever turns out not to hold on an actual 3.2.1
  client, the version gap is the first place to look. When a function/flag/key's name suggests a
  recent addition, check its introducing commit's ancestry against the 3.2.1 version-bump commit
  (`28f736fb3`, "changed the version string to 3.2.1") before stamping a Zandronum 3.2.1 claim —
  see `acs/concepts/event-scripts.md` for a worked example of a feature that exists in the
  `3.3-alpha` checkout but postdates 3.2.1.
- **The local Zandronum working tree is not pristine.** It carries an applied ZandronumMCP
  integration patch — several modified tracked files including `src/p_acs.cpp` (+170 lines
  relative to upstream) plus untracked `src/mcp_*.cpp` files. Since claims are verified by reading
  that checkout, a cited `p_acs.cpp` line number may be shifted relative to a clean 3.2.1/3.3-alpha
  checkout elsewhere. `git diff` the relevant file in the local checkout before quoting a line
  number or adding a `**Source excerpt:**` block sourced from it, and don't assume line numbers
  cited here transfer to a different Zandronum checkout unmodified.

**An engine claim isn't always a version claim — a compiler-only finding uses `N/A`.** A tier-A/B
entry whose subject is genuinely engine-independent (e.g. a `zt-bcc` code-generation bug that
produces identical corrupt bytecode regardless of which engine eventually runs it — see
`acs/concepts/string-concat-operator-variable-bug.md`) still carries the field(s), but as
`**Applies to:** N/A — <one line saying why>` together with `**Verified against:** none` rather
than a version. This is different from the tier-C
carve-out above (no field at all): tier-C omits it because no behavior has been read yet; `N/A`
says behavior *was* read and verified, just not against any one engine's version. `Applies to:`
otherwise requires both a `UZDoom=` and a `Zandronum=` key, and an engine-independent entry can't
honestly assert either — `N/A` is how it says so without widening the yes/no/unknown value set.
Don't leave the field out and rely on prose to explain its absence — `tools/lint_docs.py`'s
`STRICT_HEADER_POSITION` check requires the field to literally be present in the header block.

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

Every tier-A/B file/row also carries an engine claim field/column — `Applies to:`/`Verified
against:` (see "Engine scope" above). Tier-C entries don't need one — they're derived from a
compiler/engine table's existence, not from reading behavior, so there's no version claim being
made yet.

Tier-A entries require a wiki-sourced starting point produced by the maintainer-side intake
pipeline — see `maintainer/CLAUDE.md` if that directory exists in your checkout, and note the
intake pipeline is per-section-aware (`maintainer/_intake/<section>/`). **Tier-B and tier-C
entries don't require it** — anyone can add one straight from engine/compiler source.

## Writing a tier-B/C entry

1. **Pick a target** — a section's "not yet documented" list, or an entry missing entirely. Skim
   the section's `INDEX.md` first to confirm it isn't already documented under a different name.
2. **Classify its engine-source bucket** — see the section's own `AGENTS.md` for what buckets
   exist there (e.g. ACS's compiler-builtin/action-special/extension-function split, or
   DECORATE's owning-class-and-flags-word split) — and read the real implementation.
3. **Apply the Authoring rule** (below): only write a file if it earns its cost over a one-line
   grep. Tier B needs prose from a secondary source verified against fork source; tier C is
   signature/name/type only and doesn't need source verification or an engine claim.
4. **Stamp `Tier:`, `Provenance:`, and (for A/B) `Applies to:`/`Verified against:`** directly
   under the file's H1 (see `shared/ARCHETYPES.md` for the exact block), and add the section
   `INDEX.md` line.
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

**The primary engine is the one you may never quote.** UZDoom/GZDoom-family source, ZScript stdlib
included, is GPL-3.0 with no excerpt escape hatch (see below) — the *opposite* of the permissive
Zandronum/zt-bcc-bcc path this section leads with next. Under the old Zandronum-primary framing
that ordering matched the common case; it no longer does. Read the GPL-3.0 rule near the end of
this section first if you're about to quote anything from the primary engine's source.

Citing a function/struct name and file:line (encouraged throughout this tree) is not the same as
reproducing its body in a fenced code block — the latter is a literal copy of someone else's
copyrighted source, not a citation, and this repo's `LICENSE` has to account for every file that
does it. If you quote a real function body, `case` block, struct, or enum verbatim from
engine/compiler source (as opposed to a usage example in ACS/BCS/DECORATE/ZScript, which is fine
and unaffected by this rule):

- Add a `**Source excerpt:**` field to the file, immediately after its `Bucket:` field (per
  `shared/ARCHETYPES.md` and `lint_docs.py`'s `HEADER_FIELDS`, which are authoritative on order),
  stating which project the excerpt came from and pointing at the
  matching `LICENSE` section — e.g. `**Source excerpt:** This file quotes Zandronum engine source
  verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.` (path depth
  varies by section; `§4` for zt-bcc/bcc compiler source).
- Do this for **Zandronum or zt-bcc/bcc source only** — see below for why `acc` and GPL-3.0
  sources are different. Both Zandronum and zt-bcc/bcc are permissively licensed and
  redistributing a short excerpt with notice is fine; `LICENSE` §3/§4 already carry the standing
  notice and source pointer this requires.
- If you're only restating what code *does*, write that in prose instead and skip the field
  entirely — simpler, and keeps the file lighter per the Authoring rule above.

**A fence's tag places it in one of three tiers, with asymmetric consequences.** This is what
`lint_docs.py`'s `check_source_excerpt_and_gpl` actually does with the tag, not a courtesy label:

| Tier | Tags | What the tag does |
|---|---|---|
| **Exemption** | `acs`, `bcs`, `decorate`, `zscript` | Removes the fence from the C++ heuristic's reach — tagging a block ` ```acs `, ` ```decorate `, or ` ```zscript ` is you asserting it's a usage example in that language. So a DECORATE example containing `Goto Super::Missile`, or a ZScript one calling `Console.Printf`, should carry its language tag rather than being left bare. |
| **Assertion** | `c`, `cpp`, `c++`, `cc`, `cxx`, `h`, `hpp` | *You* asserting the block is C/C++ engine or compiler source. `lint_docs.py` enforces that assertion as a **hard error**: any file with such a fence and no `Source excerpt:` field fails lint, full stop — this is not a heuristic guess that can be wrong. If the block is really a usage example, tag it `acs`/`decorate`/`zscript` instead; if it's a restatement of what code does, drop the fence and write prose. |
| **Neutral** | ` ```text `, `mapinfo`, `markdown`, anything else outside the other two tiers | The heuristic still scans it, no hard error either way. This is the safe default for a block that is not an assertion in either direction — tagging it ` ```text ` does not weaken detection at all compared to leaving it bare. |

Two things a tag does **not** do, in any tier: it never substitutes for the `Source excerpt:` field
when the block really is engine source, and it never makes a GPL-3.0 excerpt legal.

**Every fence must carry a tag — an empty tag is itself a hard error.** `lint_docs.py` no longer
accepts a bare ` ``` ` with nothing after it: pick the tier the fence actually belongs to, and use
` ```text ` when it's not an assertion in either direction. This is regression prevention, not new
detection — an untagged fence was never outside the heuristic's reach, so the rule doesn't catch
anything the neutral tier wouldn't already have caught. What it buys is that a future untagged fence
can't silently drift back into existence unnoticed.

**The exemption tier's own cost.** An `acs`/`decorate`/`zscript` tag no longer silences everything:
`lint_docs.py` also rescans exemption-tagged fences for a narrower, exemption-safe token subset
(`EXEMPT_RESCAN_TOKENS` — things like `TArray`, `case ACSF_`, `AActor` that cannot appear in
hand-written ACS/DECORATE/ZScript at all) and warns if one turns up. A strong engine-source token in
a fence tagged as a usage example means one of the two is wrong: retag it, add a `Source excerpt:`
field, or paraphrase it.

**Lint now does partial enforcement of the GPL-3.0 ZScript rule, but not full coverage — do not
rely on it alone.** `GPL_ZSCRIPT_RES` scans for ZScript-shaped GPL signals (an `SPDX-License-
Identifier: GPL` header, or ZScript's own `native`/`readonly<...>`/`deprecated(...)`/`version(...)`
declaration syntax), on top of the older C++-VM-internals check (`DEFINE_FIELD(`,
`IMPLEMENT_CLASS(`, `VMValue`), which the ZScript standard library — written in ZScript, not C++ —
never trips. Measured against all 294 files of UZDoom's stdlib: a header-inclusive paste is caught
294/294; a snippet paste with the header stripped is caught 55/294 (19%). That's a real, if partial,
reduction in an already-partial signal — the rule below is still a rule you have to follow, not one
the linter fully enforces for you.

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

## Wiki provenance

Two rules apply to any entry whose `Provenance:` cites a wiki page. Both are licensing rules
first and authoring rules second - see `LICENSE` §2 for the terms they exist to satisfy.

**Never derive one file from both wikis.** The ZDoom Wiki is GFDL 1.2 (with no "or any later
version" clause) and the Zandronum Wiki is CC BY-NC-SA 4.0. Those are mutually incompatible
copyleft licenses: a file drawing on both could not satisfy either, and no `LICENSE` section can
rescue it. If one topic genuinely needs material from both, split it into two files, each citing
only its own wiki, and cross-link them. `tools/lint_docs.py` treats a `Provenance:` field naming
both wikis as a hard error, the same way it treats a GPL-3.0 excerpt.

**Record an `oldid=`, not just a page title.** Every wiki-citing `Provenance:` field must carry
the page's `oldid=` revision number - the wiki's page history is what supplies the principal-author
list and change history that GFDL 1.2 §4 and CC BY-NC-SA 4.0's attribution terms expect, and a
bare page title doesn't get a reader there. A page URL without a revision is no better: it
resolves to whatever the page says today, not to what the entry was actually built from. See
`shared/ARCHETYPES.md`'s header-block example for the canonical form.

`tools/lint_docs.py` enforces this per field, and enforces the both-wikis rule above as a union
across all of them. Both look at every `Provenance:` field in a file, not just the header block's
- a `families/*.md` carries one per member function, and a rule that only read the first would
inspect one of the seven in `acs/families/lump-io.md`.

**Carry a `**Wiki license:**` field naming the wiki's license.** `LICENSE` §2 asks a file derived
from a wiki page to carry a per-file pointer to the license that page is published under, so a
copy of the file taken on its own still names its terms - mirrors the `**Source excerpt:**`
field's job for a verbatim engine/compiler excerpt (§3/§4). Goes immediately after the
`Provenance:` field it derives from (the first one that cites a wiki, if a file carries more than
one - see `shared/ARCHETYPES.md`'s header-block example for the canonical form and wording):

    **Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation
    License 1.2 — see [LICENSE](../../LICENSE) §2.

    **Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0
    (NonCommercial) — see [LICENSE](../../LICENSE) §2.

`tools/lint_docs.py` requires exactly one such field on any file whose `Provenance:` cites a wiki,
naming the license matching the wiki cited and linking `LICENSE` §2, and forbids the field on a
file that cites no wiki.

Consequences of these rules, plus one adjacent rule, worth knowing:

- **Re-stamping an existing entry is an intake re-run, not a metadata edit.** A fresh fetch yields
  today's revision, so the entry has to be re-verified against it and dated accordingly, never
  backdated to the original retrieval. See `maintainer/PROCESS_INTAKE_FILE.md`'s "When the target
  file already exists" for what that obligates.
- **Mentioning a wiki without citing one still trips the check** if the sentence names a wiki and
  the field has no `oldid=`. A tier-B entry recording that no wiki page exists should say so in
  the body prose rather than in `Provenance:`, and keep the field to what it was actually built
  from (e.g. `**Provenance:** written from `src/p_acs.cpp:1234-1250`; no wiki page covers this.`). There's no lint check for this - distinguishing a new entry from that legacy cohort
mechanically would take a baseline file this tree deliberately doesn't keep.
- **Shedding a wiki citation (`LICENSE` §1's "rewritten from scratch" carve-out) is a clean-room
  rewrite, not a metadata edit.** It means rewriting the entry from engine/compiler source alone,
  without reference to the wiki text, and only then dropping the wiki citation from
  `Provenance:` - freeing the file from the source wiki's license terms. No procedure for this is
  defined yet; if one is ever needed (e.g. to lift the NonCommercial restriction from a specific
  file), design it deliberately first rather than improvising per-file.

## Version control

This repo is a single git repo (aside from the gitignored, independently-versioned `maintainer/`
directory — see its own `CLAUDE.md`). Remind the user to commit when a meaningful chunk of work is
done and nothing is staged/committed yet. Never run destructive git operations (`reset --hard`,
`clean`, `checkout --` over uncommitted changes, `push --force`, etc.) without explicit user
approval first. Never write a machine-specific filesystem path into a commit message or doc file
(see the Authoring rule above) — this repo is cloned onto machines you don't control.
