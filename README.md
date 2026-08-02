# zdoom-agent-docs

A hand/agent-maintained documentation tree for the ZDoom-family Doom-engine modding surface —
ACS/BCS, DECORATE, ZScript, and lump formats like MAPINFO/GLDEFS/SBARINFO/CVARINFO — targeting
**Zandronum** (primary) and **UZDoom/GZDoom-family** engines (where Zandronum doesn't apply, most
notably ZScript, which doesn't exist in Zandronum at all). It exists to answer one recurring
question cheaply, generalized past its original ACS-only scope: *given a function, flag,
property, key, or cvar name, what does it actually do, and on which engine?*

Names and signatures are trivially greppable from compiler tables or engine source. What's
expensive is *semantics* — parameter meaning, valid enum values, units, failure/error-return
behavior, activator/pointer semantics, and engine-specific netcode or clientside quirks — which
otherwise means re-reading C++ every time the question comes up. This tree caches that work once,
per entry, so it doesn't get redone.

It's project-agnostic: any Zandronum/GZDoom-family mod can read from it, and any contributor can
write back to it. It's built for and consumed by real mod projects but doesn't assume or reference
any one of them by name.

See `CLAUDE.md`'s routing table for the full scope.

## Where to start

- **`CLAUDE.md`** — the router. Routes by knowledge area (ACS, DECORATE, ZScript, MAPINFO, ...) to
  the right section, and to the shared rule files. Read this first.
- **`INDEX.md`** — the full top-level map: every section, its coverage stats, and what's not
  covered yet.
- **`shared/AUTHORING.md`** — every rule that applies across sections: tiers, the `Engine:` field
  and multi-engine handling, licensing (including the GPL-3.0 paraphrase-only rule for
  UZDoom/GZDoom/ZScript source), and the Authoring rule for when an entry earns its own file.
- **`shared/ARCHETYPES.md`** — the three doc schemas every section is built from (Callable /
  Table-of-entries / Concept), with the exact header-block format for each.
- **`agents/`** — ready-made Agent-tool subagent definitions (`zdoom-docs-lookup` for retrieval,
  `zdoom-docs-intake` for wiki-page processing) any consuming project can register. See
  `CLAUDE.md`'s "Subagents" section for how.

## Layout

```
acs/       decorate/   zscript/            -- major sections (Callable + Concept archetypes)
mapinfo/   gldefs/     sbarinfo/  cvarinfo/ -- lump formats  (Table-of-entries + Concept)
console/   sprites/                        -- runtime & assets
shared/    -- AUTHORING.md, ARCHETYPES.md, concepts/ (cross-section only)
tools/     -- sections.py, lint_docs.py, gen_inventory.py, lookup.py
agents/    -- zdoom-docs-lookup.md, zdoom-docs-intake.md (Agent-tool subagent defs)
maintainer/ -- gitignored, maintainer-only wiki-intake pipeline (absent in a plain clone)
```

Each section has its own `INDEX.md` (router for that section) and `CLAUDE.md` (what's specific to
it — its engine-source buckets or inventory extractor, its layout, its worked examples).

## The tier system

Every doc file (or, for a Table-of-entries section, every inventory row) is stamped with a
confidence tier — **A** (wiki-enriched, verified against fork source), **B** (secondary-source
prose, verified against engine source), or **C** (name/signature only, no prose yet). See
`shared/AUTHORING.md`'s "Tiers" for the full definitions and what's required to add each.

Tier-A entries require a wiki-sourced starting point produced by the maintainer-side intake
pipeline (not part of this public repo). **Tier-B and tier-C entries don't** — anyone can add one
straight from engine/compiler source; see `shared/AUTHORING.md`'s "Writing a tier-B/C entry" for
the exact steps, and consider that the most useful way to contribute here.

## Using `tools/lookup.py`

Quick name/signature lookup without opening a full doc file (renamed from the original `sig.py` —
no external consumer referenced the old name):

```
python3 tools/lookup.py CheckFlag                  # ACS, searches every section
python3 tools/lookup.py --section decorate SOLID    # scope to one section
python3 tools/lookup.py GetActorProperty --long     # signature + parameter info
```

Fails loudly with a "did you mean" suggestion for typos — it never silently falls back to
re-deriving an answer from a compiler/engine table this tree hasn't verified yet.

## Setting up local source checkouts

Doc files cite engine/compiler source by relative path (e.g. `src/p_acs.cpp:123`) and never
assume a fixed absolute location, since that differs per machine:

```
cp sources.example.md sources.local.md
```

then fill in the absolute path to whichever checkouts you have locally (Zandronum, UZDoom/GZDoom,
zt-bcc, UltimateDoomBuilder, SLADE, etc. — see the file for the full key list).
`sources.local.md` is gitignored; never commit real local paths. If a key is left blank, an agent
falls back to checking for a same-named sibling directory next to this repo, and if that's also
missing, it'll ask rather than guess.

## Validating changes

After hand-editing any doc file, or regenerating an inventory:

```
python3 tools/lint_docs.py
python3 tools/gen_inventory.py --check   # confirms committed inventories match a fresh extraction
```

`lint_docs.py` checks every section's `INDEX.md` links resolve, every doc file is linked and
carries the required header fields in the right place, generated inventory files aren't
hand-edited, and no file quotes a GPL-3.0 or `acc` source verbatim without the license framework
that allows it.

## Contributing

See `shared/AUTHORING.md` for the full authoring rules — written for an AI agent working in this
tree, but the rules apply the same way to a human contributor. Pull requests adding or correcting
tier-B/C entries from primary engine/compiler source are welcome.

## License

Mixed — see [LICENSE](LICENSE) for the full terms:

1. Original prose and tooling (tier-B/C entries with no wiki provenance, a tier-A entry verified
   straight from source with no wiki provenance at all, `tools/`, `CLAUDE.md` files, this file)
   are MIT-licensed.
2. Tier-A entries are enriched from third-party wikis and carry those wikis' own licenses:
   - ZDoom-Wiki-derived files are GFDL 1.2 (full text at [licenses/GFDL-1.2.txt](licenses/GFDL-1.2.txt))
   - Zandronum-Wiki-derived files are CC BY-NC-SA 4.0 (**NonCommercial**).
3. A number of files quote short verbatim excerpts of Zandronum's own engine source (marked with a
   `**Source excerpt:**` field), reproduced under Zandronum's permissive BSD-style license.
4. A standing category for zt-bcc/bcc compiler source quoted verbatim, under zt-bcc's own MIT
   license.

**UZDoom/GZDoom engine source and the ZScript standard library are GPL-3.0 and are never quoted
verbatim anywhere in this tree** — there is deliberately no license section for them, because
unlike `acc` (no permissive fallback, so still forbidden) there's no excerpt exception being
carved out at all: the rule is paraphrase-only, full stop. See `shared/AUTHORING.md`'s "Quoting
engine/compiler source verbatim" for the reasoning.

A file can fall into more than one of the four numbered categories at once. Check its `Provenance:` and
`**Source excerpt:**` fields before reusing it outside this repo.
