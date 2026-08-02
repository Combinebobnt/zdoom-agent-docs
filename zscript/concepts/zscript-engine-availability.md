# ZScript engine availability: absent from Zandronum, present in UZDoom/GZDoom-family

**Tier:** A
**Engine:** Zandronum 3.2.1/3.3-alpha (confirmed absent); UZDoom 4.15pre (confirmed present)
**Provenance:** Source-verified directly against both local checkouts (no wiki intake needed —
this is a structural fact about which files exist, not a behavior claim a wiki page would
describe).

**ZScript does not exist in Zandronum at all, in any form — not a stripped-down or partial
implementation, a genuinely absent subsystem.** This is the single most important fact for an
agent routed to this section: before answering any ZScript question in a Zandronum-targeting
project, first check whether the project can even use ZScript (it can't, on Zandronum).

## What's actually missing

Verified by direct inspection of the local Zandronum checkout (`~/source/zandronum` per
`sources.local.md`'s `zandronum` key):

- No `src/scripting/` directory (or equivalent) at all.
- Zero occurrences of `zcc_parser`, `ZCC_`, or `VMFunction` anywhere in `src/`.
- `src/thingdef/` is the *only* actor-scripting parser in the codebase, and it is DECORATE-only —
  the same subsystem `../../decorate/CLAUDE.md` documents, with no ZScript layer above or beside
  it.
- Structurally, this isn't a feature that was removed or disabled — it's a feature that was never
  added, because this fork's own `version.h` (`ZDOOMVERSIONSTR "2.8pre-441-g458e1b1"`) pins its
  ZDoom baseline to a point that predates ZScript's introduction upstream entirely. Zandronum
  forked before ZScript existed and has continued to receive DECORATE-era backports since, not
  ZScript-era ones.

## Where ZScript does exist locally

The UZDoom checkout (`sources.local.md`'s `uzdoom` key, a GZDoom-family fork at `4.15pre`) has a
complete ZScript implementation:

- `src/common/scripting/frontend/zcc_parser.cpp` (and the generated `zcc-parse.lemon` grammar)
- `src/common/scripting/backend/vmbuilder.cpp`, `src/common/scripting/vm/vmexec.cpp`
- A real ZScript standard-library corpus at `wadsrc/static/zscript/` (`actors/`, `engine/`, `ui/`,
  `constants.zs`, `doombase.zs`, `events.zs`, `mapdata.zs`, and more) — **GPL-3.0 licensed** per
  its own `zscript_license.txt`; see `../../shared/AUTHORING.md`'s "Quoting engine/compiler source
  verbatim" before citing anything from it (paraphrase only, never a verbatim excerpt).

Every ZScript doc in this section is necessarily verified against UZDoom (or, once/if a checkout
exists, GZDoom proper), never Zandronum — see `../../shared/AUTHORING.md`'s "Engine scope" for why
a doc's `Engine:` field must say so explicitly rather than leaving it ambiguous.

## Practical implication for a mixed-engine mod project

A project currently shipping on Zandronum has no migration path to ZScript short of porting to a
GZDoom-family engine entirely — there is no partial-adoption or compatibility-shim option, since
the parser and VM simply aren't compiled into the Zandronum binary. If a user asks about adding
ZScript to a Zandronum project, this is a "not possible on this engine" answer, not a "here's how"
one.

## See also

- [`decorate/CLAUDE.md`](../../decorate/CLAUDE.md) for the DECORATE-only actor-scripting layer
  Zandronum uses instead.
- `../../shared/AUTHORING.md`'s "Engine scope" for the general multi-engine handling rules this
  fact is the most extreme instance of.
