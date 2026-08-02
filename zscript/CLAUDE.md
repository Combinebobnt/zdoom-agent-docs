# zscript/ — ZScript classes, methods, VM/scope semantics

**UZDoom/GZDoom-family only.** ZScript does not exist in Zandronum — see
`concepts/zscript-engine-availability.md` before answering anything here for a Zandronum-targeting
project. **Read `../shared/AUTHORING.md` and `../shared/ARCHETYPES.md` first.**

If the `zdoom-docs-lookup` subagent is registered, prefer delegating a lookup question to it
instead of reading this tree by hand — see the root [`CLAUDE.md`](../CLAUDE.md)'s "Subagents"
section.

## Layout

- `INDEX.md` — this section's router.
- `classes/<name>.md` — one file per documented class/method group (lowercase filename).
  Archetype 1 (Callable).
- `families/<topic>.md` — grouped classes/methods, same three rationales as ACS's/DECORATE's.
  Archetype 1.
- `concepts/<topic>.md` — VM/scope semantics, the class hierarchy, virtual-function override
  rules, differences from DECORATE's state machine. Archetype 3.

This section currently has no `inventory/`/`notes/` split (no Table-of-entries archetype content
yet) — ZScript doesn't have an obvious large flat table the way DECORATE flags/properties or
console cvars do; add one if a genuine table-shaped need shows up (e.g. a full builtin-function
inventory).

## The engine-source buckets

ZScript's engine-source surface, in the UZDoom checkout (`sources.local.md`'s `uzdoom` key):

| What | Where it lives |
|---|---|
| Parser/grammar | `src/common/scripting/frontend/zcc_parser.cpp`, `frontend/zcc-parse.lemon` |
| VM backend | `src/common/scripting/backend/vmbuilder.cpp`, `src/common/scripting/vm/vmexec.cpp` |
| Standard library (the actual class/method definitions most doc entries here describe) | `wadsrc/static/zscript/` — **GPL-3.0**, paraphrase only, never quote verbatim (see `../shared/AUTHORING.md`) |

## Writing a tier-B/C entry for ZScript

Follow `../shared/AUTHORING.md`'s "Writing a tier-B/C entry". Since the stdlib itself is GPL-3.0,
describe class/method behavior in your own prose — reading the `.zs` source to verify behavior is
fine, quoting it in a fenced block is not, ever (no `**Source excerpt:**` exception exists for
this, unlike Zandronum/zt-bcc source).
