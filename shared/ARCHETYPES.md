# Doc archetypes

Every section (`acs/`, `decorate/`, `zscript/`, `mapinfo/`, `gldefs/`, `sbarinfo/`, `cvarinfo/`,
`console/`, `sprites/`, and any lump-format section added later) is built from three archetypes.
Assigning a knowledge area to an archetype — rather than inventing a bespoke layout per section —
is what keeps nine sections maintainable as one system. A section's own `AGENTS.md` says which of
its directories map to which archetype; this file is the schema each archetype follows, shared
everywhere. See `shared/AUTHORING.md` for the rules (tiers, engine scope, licensing, project-
agnosticism) that apply to content in every archetype below.

## Archetype 1: Callable

**Used by:** ACS/BCS functions (`acs/functions/`, `acs/families/`), DECORATE action functions
(`decorate/actions/`, `decorate/families/`), ZScript classes/methods (`zscript/classes/`,
`zscript/families/`).

One file per callable (lowercase filename), or a family file grouping several callables — see
`shared/AUTHORING.md`'s "Family/group files" for the three grouping rationales and when each
applies. Header block goes directly under the H1, one field per line, in this order:

```markdown
# `bool CheckFlag(int tid, str flag)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @fbad53bff5 (2026-08-08); Zandronum 3.2.1 @28f736fb3 (2026-07-28)
**Provenance:** ZDoom Wiki `CheckFlag` (retrieved 2026-07-29, oldid=44244) + verified against
the Zandronum source's `src/p_acs.cpp:6802-6810`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation
License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (index -75; dispatched as `ACSF_CheckFlag`).

Checks whether an actor with a given TID has a specified actor flag set.

## Parameters
...
```

- `Applies to:` - where the feature exists. Comma-separated `<engine>=<value>`; engine is one of
  UZDoom/GZDoom/Zandronum/zt-bcc/acc; value is `yes`, `no`, or `unknown` and nothing else. Both
  `UZDoom=` and `Zandronum=` are required. There is deliberately no `partial`: "exists on both but
  behaves differently" is `yes` plus an `## Engine-family divergence` section. Free prose is
  allowed after an em-dash. An entry that genuinely isn't a property of any engine (a compiler
  codegen bug, say) uses `N/A — <reason>` instead of the pairs.
- `Verified against:` - whose source was actually read, and at what revision. Semicolon-separated
  `<engine> <version> @<sha> (<YYYY-MM-DD>)`, or the literal `none` for an entry that read no
  engine at all. Never retro-updated when a checkout advances. Naming only one engine here (say,
  Zandronum) while `Applies to:` says both exist is legal and common — it means only that engine's
  source was actually read for this entry.

`tools/lint_docs.py` hard-errors on a file carrying only half the pair, and on the legacy
single-field `**Engine:**` form the UZDoom retarget's Phase 5 sweep fully retired (completed
2026-08-17) — don't add one. Stamp a real version, SHA and date from a checkout you actually read;
don't invent a SHA to look verified.

- The H1 is the signature (or, for a family file, the topic name — see the section's own
  convention for family H1s).
- `Bucket:` is per-section — it names where in the engine/compiler source this callable's real
  behavior lives, so a future reader searching only one file doesn't wrongly conclude a callable
  is undocumented in the engine. Each section's `AGENTS.md` defines its own bucket table (e.g.
  ACS's compiler-builtin / action-special / extension-function split by `zcommon.bcs` index sign;
  DECORATE's `DEFINE_ACTION_FUNCTION` file-and-line; ZScript's owning class/struct).
  `**Wiki license:**`, if present (any entry whose `Provenance:` cites a wiki — see
  `shared/AUTHORING.md`'s "Wiki provenance"), goes immediately after `Provenance:`.
  `**Source excerpt:**`, if present, goes immediately after `Bucket:`.
- A family file carries the same header block once, covering every member, then one `## \`<full
  signature>\`` H2 per member — this is what a section's `lookup.py` resolution keys off, and why
  `INDEX.md` links to the family file as a whole rather than to a per-member anchor. The one
  file-level `Tier:`/`Applies to:`/`Verified against:`/`Provenance:`/`Wiki license:`
  must sit directly under the H1, before
  the first `## ` heading — `tools/lint_docs.py`'s `STRICT_HEADER_POSITION` check only looks at
  that leading run, so nothing below the first `## ` counts toward it. `Provenance:` composes by
  listing every member's wiki page with its own `oldid=` (see `acs/families/cvar.md`/`inventory.md`
  for the pattern), not a summary sentence. A member's own `## ` section may **additionally** carry
  its own `**Provenance:**` (a per-member citation or source-only sub-note) and, when a member's
  verified tier genuinely differs from the file-level claim, its own `**Tier:**` — both are
  established, lint-compatible practice (`check_wiki_provenance`/`check_wiki_license` already union
  over every `Provenance:` field in the file, not just the header block's), not a duplicate of the
  file-level field. Keep the file's own rationale/intro prose paragraph after the header block, not
  before it — a paragraph between the H1 and the block also fails
  `STRICT_HEADER_POSITION` (the block must be the first non-blank content under the H1).
- `Tier:` C entries don't get a standalone file at all — they're a flat line in the section
  `INDEX.md`'s "not yet documented" block (auto-generated where a generator exists, e.g. ACS's,
  hand-added otherwise).

## Archetype 2: Table-of-entries

**Used by:** DECORATE actor flags and properties, MAPINFO/GLDEFS/SBARINFO/CVARINFO keys, console
cvars and ccmds — anywhere the underlying engine table is too large (hundreds to low thousands of
entries) for one file per entry to be practical, and most entries don't individually earn a file
under the Authoring rule.

Split into two directories per section:

**`<section>/inventory/<table>.md` — generated, complete, never hand-edited row-by-row.** Written
and refreshed only by `tools/gen_inventory.py`. Carries a header stating this:

```markdown
# DECORATE actor flags

**Generated:** by `tools/gen_inventory.py decorate-flags` — do not hand-edit rows; add a
`notes/` file and update this row's `Notes`/`Tier` cell only through the generator's
preserve-by-key merge (see below). Extraction reads the Zandronum source as its base
(confirmed present for every row); UZDoom presence is a name cross-reference only (the `UZD`
column), not independently behavior-verified.
**Tier:** per row (defaults to C until a `notes/` file promotes it).

| Flag | Table | Class | Field | Zan | UZD | Tier | Notes |
|---|---|---|---|---|---|---|---|
| SOLID | ActorFlags | AActor | flags | yes | yes | C | |
| FRIENDLY | ActorFlags | AActor | flags | yes | yes | A | [notes](../notes/friendly.md) |
| QUARTERGRAVITY | ActorFlags | AActor | flags | dep | — | C | deprecated |
```

Archetype 2's inventory files carry no file-level `Applies to:`/`Verified against:` pair — the
per-row `Zan`/`UZD` columns already state per-engine presence, and the `**Generated:**` field's
own prose states what was cross-referenced against what (see the real files for the exact
wording, which varies by extractor).

- One row per entry; columns are extractor-specific but always include a per-engine
  presence/value column (`yes`/`dep`/`—`/a concrete value) and a `Tier` column defaulting to `C`.
- **Regeneration preserves `Tier` and `Notes` by name key** and reports added/removed/changed
  entries — the generalized form of the contract ACS's `INDEX.md` already states for its
  auto-generated tier-C block ("replace only lines carrying `, auto-generated`"). A hand-promoted
  `Tier` cell or `Notes` link never gets silently clobbered by a re-run.
- Never hand-edit a row. If an entry earns more than its inventory row, write a `notes/` file (see
  below) and update only that entry's `Tier`/`Notes` cell — or better, let the next generator run
  pick up the change from the `notes/` directory's presence, if the section's generator supports
  that (see the section's own `AGENTS.md`).

**`<section>/notes/<entry>.md` — curated, only for entries that earn it.** Same header block and
Authoring-rule bar as archetype 1:

```markdown
# `FRIENDLY` (actor flag)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-28)
**Provenance:** ...

Prose that earns its cost per the Authoring rule — parameter/argument semantics, interaction with
other flags, failure modes, fork-specific caveats.
```

## Archetype 3: Concept

**Used by:** `<section>/concepts/<topic>.md` for knowledge specific to one section (script types,
the DECORATE state-machine model, ZScript VM/scope semantics, sprite-naming conventions), and
`shared/concepts/<topic>.md` for anything that genuinely spans sections (e.g. Zandronum/GZDoom-
family divergence patterns, lump load order across formats).

Same header-block position and fields as archetype 1, no signature H1 — just a topic title:

```markdown
# Script types

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @fbad53bff5 (2026-08-08); Zandronum 3.2.1 @28f736fb3 (2026-07-28)
**Provenance:** ...

Prose.
```

A concept page still has to earn its cost per the Authoring rule (not a restatement of something
obvious from the language/format spec) and still gets verified against source where the claim is
checkable. A section's crash-and-bug checklist (where one exists) is a concept file that indexes
findings living in that section's other files rather than duplicating them — see
`acs/concepts/crash-and-bug-checklist.md` for the pattern, and note it is deliberately
per-section: `decorate/` and `zscript/` get their own when they have findings to index, rather
than one shared checklist mixing languages.
