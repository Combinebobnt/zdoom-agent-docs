# sbarinfo/ — SBARINFO keys and commands

SBARINFO semantics for UZDoom/GZDoom-family (primary) and Zandronum where they diverge. **Read
`../shared/AUTHORING.md` and `../shared/ARCHETYPES.md` first.**

If the `zdoom-docs-lookup` subagent is registered, prefer delegating a lookup question to it
instead of reading this tree by hand — see the root [`AGENTS.md`](../AGENTS.md)'s "Subagents"
section.

## Layout

- `INDEX.md` — this section's router.
- `inventory/<block>.md` — generated tables of SBARINFO keys/commands, grouped by block
  (`statusbar`, `mugshot`, per-condition draw commands). Archetype 2, generated half. No
  generator exists yet.
- `notes/<key-name>.md` — curated prose. Archetype 2, curated half.
- `concepts/<topic>.md` — cross-block knowledge (the fullscreen/status-bar draw-command model,
  mugshot state naming conventions). Archetype 3.

## Where SBARINFO parsing lives

Zandronum: `src/g_shared/sbarinfo.cpp` (`SBarInfo::Load`, `SBarInfo::ParseSBarInfo`,
`SBarInfo::ParseMugShotBlock`) plus per-command implementations in
`src/g_shared/sbarinfo_commands.cpp`. UZDoom: `src/g_statusbar/sbarinfo.cpp`.

## Status

Scaffolded, no content yet. Tier-B prose source once picked up: `sources.local.md`'s `udb` key →
`Build/Scripting/ZDoom_SBARINFO.cfg`.
