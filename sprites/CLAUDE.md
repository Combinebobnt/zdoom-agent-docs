# sprites/ — sprite naming/rotation conventions

Sprite lump naming, rotation-letter conventions, and how DECORATE state definitions resolve a
frame letter to an actual sprite lump. **Read `../shared/AUTHORING.md` and
`../shared/ARCHETYPES.md` first.**

If the `zdoom-docs-lookup` subagent is registered, prefer delegating a lookup question to it
instead of reading this tree by hand — see the root [`CLAUDE.md`](../CLAUDE.md)'s "Subagents"
section.

## Layout

- `INDEX.md` — this section's router.
- `concepts/<topic>.md` — the only archetype this section currently uses. There's no natural
  "callable" or large flat table here — sprite naming is a fixed convention (4-letter name + frame
  letter + rotation digit, optionally mirrored), not an engine-side table of named entries the way
  flags/cvars are. Archetype 3.

If a genuinely table-shaped need shows up later (e.g. a full inventory of every sprite-related
DECORATE property), add an `inventory/`/`notes/` split then rather than guessing at one now.

## Status

Scaffolded, no content yet.
