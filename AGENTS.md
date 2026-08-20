# zdoom-agent-docs

**This folder is first-party, not vendored.** It is a hand/agent-maintained documentation tree
covering the ZDoom-family Doom-engine modding surface — ACS/BCS, DECORATE, ZScript, and the
smaller lump formats (MAPINFO, GLDEFS, SBARINFO, CVARINFO, console cvars/cmds, sprites, and
more) — created for and edited by AI agents working across Zandronum and GZDoom-family mod
projects. Unlike a vendored/foreign upstream checkout (an engine or compiler fork you'd treat
conservatively and leave to its own conventions), you should freely create, edit, and correct
files here.

**This file is a router, not a rulebook.** It exists so an agent asking about one knowledge area
never has to load another's index. Every rule that applies across sections (tiers, the `Engine:`
field, licensing, the Authoring rule, project-agnosticism) lives in exactly one place —
`shared/AUTHORING.md` — read that before writing anything, and `shared/ARCHETYPES.md` for the
three doc schemas every section is built from.

## Subagents — prefer these if registered

This tree ships two ready-made Agent-tool subagent definitions:

- **`zdoom-docs-lookup`** (retrieval, read-only, `model: haiku`, canonical copy in this repo's own
  `agents/`) — answers ACS/BCS/DECORATE/ZScript/lump-format questions by walking this tree itself,
  following the same routing this file describes. If it's registered, delegate a lookup question
  to it directly instead of working through the "Where to go" table and section `INDEX.md`s by
  hand.
- **`zdoom-docs-intake`** (processing, `model: haiku`, canonical copy at
  `maintainer/agents/zdoom-docs-intake.md` — moved out of this public repo since the agent is
  inert without that directory) — turns one saved wiki page under
  `maintainer/_intake/<section>/` into a verified doc file. Only relevant if you have the
  maintainer-only `maintainer/` directory locally — see `maintainer/CLAUDE.md`'s "Wiki intake
  pipeline" if so.

Before doing either job by hand, check whether the corresponding subagent is registered with the
Agent tool — commonly once at `~/.claude/agents/` (applies to every project on that machine) or
copied into the calling project's own `.claude/agents/`. If neither is registered, each
definition's canonical copy above is the source: register it yourself (copy or symlink into a
`.claude/agents/` directory, project- or user-level) or paste its contents into a generic
subagent's prompt as a one-off. Every section's own `AGENTS.md` repeats a one-line pointer back to
this section, since an
agent can land directly in a subdirectory without reading this file first.

## Where to go

| If you need... | Go to |
|---|---|
| An ACS/BCS function's semantics, script types, or other BCS language questions | [acs/INDEX.md](acs/INDEX.md) |
| A DECORATE action function, actor flag, or actor property | [decorate/INDEX.md](decorate/INDEX.md) |
| ZScript classes, methods, or VM/scope semantics — **UZDoom/GZDoom-family only, does not exist in Zandronum** | [zscript/INDEX.md](zscript/INDEX.md) |
| A MAPINFO key | [mapinfo/INDEX.md](mapinfo/INDEX.md) |
| A GLDEFS key | [gldefs/INDEX.md](gldefs/INDEX.md) |
| An SBARINFO key/command | [sbarinfo/INDEX.md](sbarinfo/INDEX.md) |
| A CVARINFO declaration | [cvarinfo/INDEX.md](cvarinfo/INDEX.md) |
| A console cvar or console command (CCMD) | [console/INDEX.md](console/INDEX.md) |
| Sprite naming/rotation conventions | [sprites/INDEX.md](sprites/INDEX.md) |
| Authoring rules, tiers, engine scope, or licensing | [shared/AUTHORING.md](shared/AUTHORING.md) |
| The doc schemas (Callable / Table-of-entries / Concept) | [shared/ARCHETYPES.md](shared/ARCHETYPES.md) |
| A knowledge area not listed above | [INDEX.md](INDEX.md)'s "Not yet covered" section — check there before assuming it's simply missing |

`INDEX.md` in this same directory is the full top-level map (every section, its coverage stats,
and what isn't covered yet) — read it if the table above doesn't resolve your question, but don't
read a *section's* `INDEX.md` speculatively; go straight to the one you need.

## Engine scope, in brief

**UZDoom is the primary target** (current: UZDoom 5.0.0-pre). Zandronum stays co-equal and fully
verified, not grandfathered — the consuming projects still ship on it. ZScript and some
DECORATE/MAPINFO/GLDEFS/SBARINFO/CVARINFO behavior only exists on UZDoom/GZDoom-family engines;
some Zandronum-side behavior has no UZDoom counterpart either — every doc's engine claim says
which, stated as an `Applies to:`/`Verified against:` pair (the legacy single-field `Engine:` form
is retired tree-wide, and a new one is a hard `tools/lint_docs.py` error). `shared/AUTHORING.md`
is authoritative on the exact grammar — see its "Engine scope" for the full detail, including
known gaps between the local checkouts and their own upstreams, and `maintainer/TODO.md`
(maintainer-only) for live retarget phase status. Don't assume a doc verified for one engine holds
for another.

## Wiki access

**Don't try to fetch the Zandronum or ZDoom wikis yourself** — neither is machine-fetchable (an
Anubis proof-of-work challenge on the Zandronum wiki, empty replies from `zdoom.org/wiki`). This
applies to every knowledge area in this tree, not just ACS. If a wiki page would genuinely help
and isn't covered here yet, say so explicitly, or write a tier-B/C entry instead (see
`shared/AUTHORING.md`) — that doesn't require wiki access. If the user wants to feed a page into
the maintainer-side intake pipeline, that's `maintainer/CLAUDE.md`'s job, not something to
hand-roll — see that file if it exists in your checkout (maintainer-only, gitignored, absence is
normal for anyone who isn't the repo maintainer).

## Open work

Open work that isn't a coverage gap (for "this format has no section yet", see `INDEX.md`'s "Not
yet covered" table instead) lives at `maintainer/TODO.md` — maintainer-only, gitignored,
same as `maintainer/CLAUDE.md`; absence is normal for anyone who isn't the repo maintainer. There
is no public-facing equivalent of this file.

## Version control

This repo is a single git repo, tracked locally (see `shared/AUTHORING.md`'s "Version control" for
the destructive-operations rule). `maintainer/`, if present, is a separate nested git repo with its
own rules — don't run `git clean -xdff` here without checking it first.
