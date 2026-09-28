# zandronum-lumps/ — other Zandronum/Skulltag-native lump formats

Nine lump formats unique to the Skulltag/Zandronum lineage, unrelated to each other beyond
sharing that lineage: `ANCRINFO`, `AUTHINFO`, `CMPGNINF`, `GAMEMODE`, `MEDALDEF`, `SCORINFO`,
`SECTINFO`, `SKININFO`, `VOTEINFO`. Plus `TEAMINFO`, the one exception to Zandronum-only (below).
**Read `../shared/AUTHORING.md` and `../shared/ARCHETYPES.md` first.**

**This section is Zandronum-only, except `TEAMINFO`.** None of the nine lumps above is parsed by
any UZDoom/GZDoom-family engine. Every file for them carries `Applies to: UZDoom=no, Zandronum=yes`
and a divergence heading (`## Zandronum-specific: <topic>` or `## Engine-family divergence`) — don't
add a UZDoom-side claim without re-verifying that one exists at all. `TEAMINFO` lives here because
most of its keys are Skulltag-lineage and only do anything on Zandronum, but UZDoom has its own
parser for it, so `concepts/teaminfo.md` is the one file in this section with `UZDoom=yes`.

**`BOTINFO` and the compiled botscript format are NOT here.** Despite being Zandronum-native lumps
from the same wiki category, they live in [`bots/`](../bots/AGENTS.md) — a dedicated section that
predates this one. An agent hunting `BOTINFO` in this directory should find nothing and a pointer,
not silently conclude it's undocumented; see [`bots/AGENTS.md`](../bots/AGENTS.md) and
[`bots/INDEX.md`](../bots/INDEX.md).

If your agent harness has the `zdoom-docs-lookup` subagent registered (adapters for several
harnesses ship in `../agents/`), prefer delegating a lookup question to it instead of reading
this tree by hand — see the root [`AGENTS.md`](../AGENTS.md)'s "Subagents" section.

## Layout

- `INDEX.md` — this section's router.
- `concepts/<lump>.md` — one file per lump, plus `concepts/parsing-model.md` for the three facts
  shared across all nine (cumulative-across-WADs loading, the fixed `d_main.cpp` parse order, and
  the two parser generations' differing error behavior). Archetype 3. None of these nine lumps is
  a table of independently addressable named entries the way a DECORATE flag or a console cvar is,
  so archetype 1/2 doesn't fit any of them — except possibly `SCORINFO`'s ~75-command grammar,
  which is exactly why `inventory/`/`notes/` are registered below without yet being used.
- `inventory/`, `notes/` — registered in `tools/sections.py` (Table-of-entries, archetype 2) but
  deliberately empty for now. `SCORINFO` is the only candidate that plausibly earns a generated
  command table; that call is deferred until its concept page exists (see `notes/README` — no such
  file: this is a placeholder pair, not a partially-built one). Follow `cvarinfo/`'s precedent for
  declaring a Table-of-entries pair before it has any rows, and use its
  `_None yet - no extractor exists yet._` wording in `INDEX.md` rather than inventing new phrasing.

## Where each lump is parsed

Every one of these is unconditionally, live-parsed in the current Zandronum build — no dead lumps
in this set.

| Lump | Parser | Shape |
|---|---|---|
| `ANCRINFO` | `src/announcer.cpp` (`ANNOUNCER_ParseAnnouncerInfo` finds the lump, `announcer_ParseAnnouncerInfoLump` parses it) | anonymous `{ }` blocks, `key = value` |
| `AUTHINFO` | inline in `NETWORK_Construct`, `src/network.cpp` | flat directive list, no blocks |
| `VOTEINFO` | `src/callvote.cpp` | `votetype Name { ... }`, `FScanner` C-mode |
| `SECTINFO` | `src/sectinfo.cpp` | INI-style `[MAPNAME]` sections keyed to MAPINFO levels |
| `SKININFO` | `src/r_data/sprites.cpp` (`R_InitSkins`) — shares its parser with `S_SKIN` | one parser, two dialects |
| `CMPGNINF` | `src/campaign.cpp` | anonymous `{ }` blocks, `key = value` |
| `MEDALDEF` | `src/medal.cpp` | named, re-openable `MedalName { ... }` blocks, `FScanner` default mode |
| `SCORINFO` | `src/scoreboard.cpp`, dispatching into `scoreboard_margin.cpp` | declaration blocks with a deep nested command language, ~8,600 lines of parser |
| `GAMEMODE` | `src/gamemode.cpp` (`GAMEMODE_ParseGameModeInfo`) | named `GameModeName { ... }` blocks, `FScanner` default mode |
| `TEAMINFO` | `src/teaminfo.cpp` (`TEAMINFO_Init`); UZDoom: `src/gamedata/teaminfo.cpp` | `Team Name { ... }` blocks plus `ClearTeams`, `FScanner` default mode |

`ANCRINFO`/`CMPGNINF` share one hand-rolled `key = value` scanner going back to the Skulltag era
(fatal `I_Error` on a bad key, except `ANCRINFO`'s own dialect — see its own file) — both construct
an `FScanner` over the lump but drive it with a manual token-by-token loop rather than using
`FScanner`'s structured facilities, so "hand-rolled" describes the parsing logic, not the absence
of the `FScanner` class. `MEDALDEF`/`SCORINFO`/`VOTEINFO`/`AUTHINFO`/`GAMEMODE` all use `FScanner`'s
structured parsing (`sc.ScriptError`), a distinct, more modern generation from the hand-rolled pair.
**Within that modern generation, only `VOTEINFO` and `SECTINFO` actually run the scanner in C
mode** (`sc.SetCMode(true)`) — `AUTHINFO`, `MEDALDEF`, `SCORINFO`, and `GAMEMODE` are
`FScanner`-based but never call `SetCMode`, so they run the scanner's default classic-Hexen
tokenizer instead. Hand-rolled-vs-structured-`FScanner` and C-mode-vs-default-mode are two
independent axes, not one; see `concepts/parsing-model.md` for the detail, not repeated per-file.
`SKININFO` fits neither generation: `R_InitSkins` is its own hand-rolled `GetString` loop, and a
bad line drops that skin with a message instead of aborting.

## Verifying a claim

Read the real parser (table above) rather than trusting a wiki page's framing — several formats
here parse differently than their surface grammar suggests (see `concepts/ancrinfo.md`'s merge
behavior for the first example). No compiler or secondary tool exists for any of these nine
formats; the engine source is the only ground truth until a wiki page arrives via the maintainer
intake pipeline.
