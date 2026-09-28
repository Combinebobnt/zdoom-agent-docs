# Parsing model across the nine `zandronum-lumps/` formats

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** written from the Zandronum source's `src/d_main.cpp` (startup parse order) plus a
cross-file check across `src/announcer.cpp`, `src/network.cpp`, `src/callvote.cpp`,
`src/sectinfo.cpp`, `src/campaign.cpp`, `src/r_data/sprites.cpp`, `src/medal.cpp`,
`src/gamemode.cpp`, `src/scoreboard.cpp`, and `src/scoreboard_margin.cpp`. The `SKININFO`
classification rests on `R_InitSkins` in `src/r_data/sprites.cpp` (lines 509-824). No wiki page covers this
cross-format material; it is not itself a lump.

This page collects three facts that hold across all nine lumps in this section (`ANCRINFO`,
`AUTHINFO`, `VOTEINFO`, `SECTINFO`, `CMPGNINF`, `SKININFO`, `MEDALDEF`, `SCORINFO`, `GAMEMODE`), so
each lump's own concept page can cross-reference it instead of restating it. See
`shared/concepts/` for the cross-format lump-load-order page this one narrows to just this
section's nine formats.

## Loading is cumulative across WADs, with one confirmed exception

Every one of the nine scans **every loaded archive** for its lump name (a `Wads.FindLump` loop)
and parses each hit in turn, rather than only reading the last-loaded copy. A mod's own lump adds
to or extends what an earlier-loaded WAD already declared; it does not simply replace it.

**`CMPGNINF` is the one exception, and it looks like an engine bug rather than a deliberate
design choice.** `campaign_ParseCampaignInfoLump` walks to the end of the existing global campaign
list before parsing a newly-found lump's own blocks, but the walk's own loop always leaves it at
`NULL` regardless of what the list already held, and the first new block then overwrites the
list's head with itself. The practical effect: parsing a second `CMPGNINF` lump discards every
entry an earlier-loaded lump's `CMPGNINF` declared, not just the entries for maps the new lump
also mentions. See `concepts/cmpgninf.md`'s "Loading" section for the exact code path. No other
lump in this set shares this defect; treat "cumulative across WADs" as the default and
`CMPGNINF` as the one lump where it doesn't hold.

A narrower per-lump reset also exists and is not the same thing as the `CMPGNINF` exception above:
`SECTINFO` clears one map's own prior data when that map's `[MAPNAME]` section is re-opened
(`concepts/sectinfo.md`), and `MEDALDEF` re-using a medal's name merges into the same object
(`concepts/medaldef.md`) rather than replacing it. Both of those are scoped to a single named
entry re-declared under the same name; `CMPGNINF`'s bug discards unrelated entries wholesale.

## Parse order is fixed

`d_main.cpp` calls the parsers for these lumps in a fixed sequence during startup: `ANCRINFO`
(`ANNOUNCER_ParseAnnouncerInfo`, line 2898), `CMPGNINF` (`CAMPAIGN_ParseCampaignInfo`, line 2902),
`GAMEMODE` (`GAMEMODE_ParseGameModeInfo`, line 2905), `VOTEINFO` (`CALLVOTE_ReadVoteInfo`, line
2913), `SECTINFO` (`SECTINFO_Load`, line 2981), `MEDALDEF` (`MEDAL_Construct`, line 3049), `BOTINFO`
(outside this section, see `bots/`), then `SCORINFO` (`SCOREBOARD_Construct`, line 3085).
`TEAMINFO` (`TEAMINFO_Init`, line 2991), which this page otherwise doesn't cover since UZDoom also
parses it, sits between `SECTINFO` and `MEDALDEF`, just before DECORATE loads; see
`concepts/teaminfo.md`.
`AUTHINFO` is parsed separately, inline inside `NETWORK_Construct` (called from both `cl_main.cpp`
and `sv_main.cpp`, not from this same `d_main.cpp` sequence), and `SKININFO` is parsed inside
`R_InitSkins`, called from sprite initialization rather than this startup sequence either. A mod
relying on one of these lumps referencing state another one sets up (for example, `MEDALDEF`'s
`announcerentry` key naming an `ANCRINFO` event) can rely on `ANCRINFO` having already been parsed
by the time `MEDALDEF` runs, since `ANCRINFO` is earlier in the fixed sequence above.

## Two independent parser-generation axes, not one

An earlier draft of this section's own `AGENTS.md` collapsed parser generation into a single
split ("hand-rolled" vs. "`FScanner` C-mode"). Reading all nine parsers directly shows two
separate axes:

**Axis 1: hand-rolled `key = value` loop vs. structured `FScanner` use.** `ANCRINFO` and
`CMPGNINF` (plus `BOTINFO`, outside this section) all construct an `FScanner` over the lump but
then drive it with a hand-rolled `while`/`if` loop that manually checks each token against literal
`{`, `}`, and `=` characters, rather than using `FScanner`'s own structured token/enum facilities —
going back to the Skulltag era, down to a copy-pasted stale `pszBotInfo` comment present in all
three. A bad key in this generation is a fatal `I_Error` raised directly by the parsing code
(except `ANCRINFO`'s own dialect, which accepts any key besides the one reserved `name`, see
`concepts/ancrinfo.md`).
`SKININFO` belongs to this hand-rolled generation too, through a different lineage: `R_InitSkins`
(`src/r_data/sprites.cpp` line 509, parse loop from line 558, "Bad format" at line 606) is ZDoom's `S_SKIN` parser extended to read
`SKININFO` as well. It builds an `FScanner` and then loops on `GetString`, checking for literal
`{`, `}` and `=` itself, and it carries no `pszBotInfo` comment. Its errors are not fatal at all.
A key not followed by `=` prints "Bad format for skin" and drops that one skin. An unrecognized
key is kept as a custom skin property rather than rejected. The other six (`AUTHINFO`,
`VOTEINFO`, `SECTINFO`, `MEDALDEF`, `SCORINFO`, `GAMEMODE`) all use `FScanner`'s structured parsing (`MustGetString`,
`MustGetEnumName`, `ScriptError`, etc.) instead of a hand-rolled token-by-token loop.

**Axis 2: C-mode vs. default mode, only meaningful within the structured `FScanner` generation.**
Of those six structured-`FScanner` lumps, only **`VOTEINFO`** and **`SECTINFO`** actually call
`FScanner::SetCMode(true)`, switching the scanner into C-like tokenization (recognizing `{`/`}`/
`;`/`,` and C-style operators as their own tokens). `AUTHINFO`, `MEDALDEF`, `SCORINFO`, and
`GAMEMODE` are `FScanner`-based but never call `SetCMode`, so they run the scanner's default
"classic Hexen scanner" tokenizer instead. (The hand-rolled `SKININFO` loop, shared with `S_SKIN`,
never calls `SetCMode` either.) All six structured-`FScanner` lumps share the same fatal error mechanism regardless
of mode: an unrecognized token or key raises `sc.ScriptError`, which routes to `I_Error` the same
as the hand-rolled generation's `I_Error` calls do, and aborts engine startup rather than skipping
just the bad entry or the one lump that contains it.

So "fatal on a bad token" is common to eight of the nine lumps in one form or another (an
`I_Error` call either directly or via `sc.ScriptError`). `SKININFO` is the one exception: its
mistakes cost the affected skin, not engine startup. For the other eight, what differs between the
two axes above is which tokenizer/parsing style produced the token stream in the first place, not
whether a mistake in it is survivable.

## Engine-family divergence: no counterpart outside Zandronum

None of this page's three facts apply to UZDoom/GZDoom-family engines: none of the nine lumps
this page covers exists there at all, so there is no parallel load order, cumulative-loading
behavior, or parser-generation split to compare against.
