# The `CMPGNINF` lump

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki `CMPGNINF` (https://wiki.zandronum.com/w/index.php?title=CMPGNINF&oldid=1679,
retrieved 2026-09-09) + verified against the Zandronum source's `src/campaign.cpp`
(`CAMPAIGN_ParseCampaignInfo`, `campaign_ParseCampaignInfoLump`, `CAMPAIGN_AllowCampaign`,
`CAMPAIGN_GetCampaignInfo`) and its use sites in `src/g_level.cpp`'s `G_DoLoadLevel` and
`src/g_mapinfo.cpp`'s MAPINFO parser.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0
(NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's
own license terms, see [LICENSE](../../LICENSE) §3.

`CMPGNINF` declares single-player campaign settings per map: frag/point/time/win/wave limits, a
forced game mode and dmflags/compatflags set, and a bot roster to spawn in. **It is live-parsed at
startup unconditionally, and its main use is gated to single-player, but it is not fully inert on
a networked game either.** `CAMPAIGN_AllowCampaign()` (`src/campaign.cpp:180`) returns false
whenever the game is a hosted server (`NETSTATE_SERVER`) or a joined client
(`NETWORK_InClientMode()`, which also covers watching a client-side demo), and `G_DoLoadLevel`
only applies the full set of limits, forced dmflags/compatflags/game mode, and bot roster when
`CAMPAIGN_AllowCampaign()` is true (`src/g_level.cpp:1234`), so that half of `CMPGNINF` genuinely
never runs on a networked game.

But `G_DoLoadLevel` has a second, separate `CMPGNINF` lookup that
runs specifically `if ( NETWORK_GetState( ) == NETSTATE_SERVER )` (`src/g_level.cpp:1615`): a
dedicated server still consults the matching block's `wavelimit` for an Invasion map (gated by
`sv_usemapsettingswavelimit`) and `possessionholdtime` for a Possession/Team Possession map (gated
by `sv_usemapsettingspossessionholdtime`), both cvars defaulting to enabled. And a MAPINFO `gamemode`
option is checked against `CMPGNINF`'s own `gamemode` key for that map at MAPINFO parse time,
unconditionally, on every game role (`src/g_mapinfo.cpp:1239`); a mismatch is a fatal MAPINFO parse
error even on a server that will never enter "in campaign" state. That cross-check, and the MAPINFO
`gamemode` key itself, were added after 3.2.1 (`7aa633182`); a 3.2.1 engine has neither. So: campaign progression itself
(limits/flags/game-mode-forcing/bot-roster/team-assignment as one unit, plus the `CAMPAIGN_InCampaign()`-gated
behavior elsewhere in the engine) is single-player-only, but two narrower `CMPGNINF` values escape
that gate on a server, and the `gamemode` key is cross-checked at parse time regardless of role.

## Grammar: anonymous `{ }` blocks, `key = value` pairs

Like `ANCRINFO`, `CMPGNINF` is a sequence of anonymous `{ }`-delimited blocks parsed by the same
Skulltag-era hand-rolled scanner (down to the same stale `pszBotInfo` comment). Tokens between
blocks (including a file's very first tokens, before any `{`) are silently skipped rather than
rejected; inside a block, each `key = value` triple is read positionally, and a missing `=` after
a key is a fatal `I_Error`.

```text
{
    mapname = MAP01
    fraglimit = 20
    gamemode = deathmatch
    bot[0] = SomeBot
}
```

**Unlike `ANCRINFO`, an unrecognized key here is fatal.** `ANCRINFO` treats every key besides `name`
as a valid, open-ended event mapping; `CMPGNINF` checks each key against a fixed list of 19 names
plus the two indexed families below, and calls `I_Error( "...Unknown CMPGNINF property..." )`
(`src/campaign.cpp:500`) on anything else. A typo in a `CMPGNINF` key is a hard parse failure, not
a silently-accepted mapping.

Key and value tokens are each capped at 31 characters plus a null terminator (`char szKey[32]`,
`char szValue[32]` in `campaign_ParseCampaignInfoLump`). A longer token is silently truncated, not
rejected.

## The 19 keys

Every block resets all fields to defaults first, so a block only needs to state the keys it wants
to override; anything omitted keeps that block's default, not the previous block's value.

| Key | Meaning | Default if omitted |
|---|---|---|
| `mapname` | The map this block applies to. Copied into an 8-character buffer (`strncpy(...,8)`), matching the classic map-lump name length limit; a longer value is truncated. | empty (block never matches any map) |
| `fraglimit` | Forced `fraglimit` cvar value for this map. | `0` |
| `timelimit` | Forced `timelimit` cvar value (parsed as a float). | `0.0` |
| `pointlimit` | Forced `pointlimit` cvar value. | `0` |
| `duellimit` | Forced `duellimit` cvar value. | `0` |
| `winlimit` | Forced `winlimit` cvar value. | `0` |
| `wavelimit` | Forced `wavelimit` cvar value. | `0` |
| `gamemode` | Forces the current game mode for this map. One of `cooperative`, `survival`, `invasion`, `deathmatch`, `teamplay`, `duel`, `terminator`, `lastmanstanding`, `teamlms`, `possession`, `teampossession`, `teamgame`, `ctf`, `oneflagctf`, `skulltag`, `domination`. Any other value is a fatal `I_Error`. | `deathmatch` |
| `dmflags` | Forced `dmflags` cvar value. | sentinel `-1`: cvar left untouched |
| `dmflags2` | Forced `dmflags2` cvar value. | sentinel `-1`: cvar left untouched |
| `compatflags` | Forced `compatflags` cvar value. | sentinel `-1`: cvar left untouched |
| `compatflags2` | Forced `compatflags2` cvar value. | sentinel `-1`: cvar left untouched |
| `zadmflags` | Forced `zadmflags` cvar value. | sentinel `-1`: cvar left untouched |
| `zacompatflags` | Forced `zacompatflags` cvar value. | sentinel `-1`: cvar left untouched |
| `playerteam` | Name of the team the console player is placed on, if the active game mode has players-on-teams. An unrecognized team name is a fatal `I_Error` at map load. | empty (no forced team) |
| `mustwinallduels` | Accepts `"true"`/`"false"` or a numeric boolean. In duel mode, whether the player must win every duel to advance. | `true` |
| `possessionholdtime` | Overrides `sv_possessionholdtime` for Possession/Team Possession maps, but only when greater than `0` and only when `sv_usemapsettingspossessionholdtime` is enabled. | `0` (no override) |
| `instagib` | Accepts `"true"`/`"false"` or a numeric boolean. Forces the `instagib` cvar. | `false` |
| `buckshot` | Accepts `"true"`/`"false"` or a numeric boolean. Forces the `buckshot` cvar. | `false` |

**A key detail the limit/boolean fields and the flag fields disagree on:** the six limit keys
(`fraglimit`/`timelimit`/`pointlimit`/`duellimit`/`winlimit`/`wavelimit`) plus `instagib` and
`buckshot` are always force-set on entering a campaign map, so omitting one *disables* that limit
(sets it to `0`, or `false` for the two booleans) rather than leaving whatever value was previously
in effect. The six flag keys (`dmflags`/`dmflags2`/`compatflags`/`compatflags2`/`zadmflags`/
`zacompatflags`) use a `-1` sentinel instead, and are only force-set when the block actually
specifies a value; omitting one of these leaves the corresponding cvar exactly as it already was.

## The `bot<N>`/`botteam<N>` indexed families

Two more key families are matched by prefix rather than by exact name, each carrying a bracketed
numeric index: `bot[N]` and `botteam[N]`, where `N` is any integer from `0` up to `MAXPLAYERS - 1`
(64 on this engine). `campaign_ParseBracketIndex` (`src/campaign.cpp:257`) extracts the index
between `[` and `]`; a missing `[`, a missing `]`, or an out-of-range index is a fatal `I_Error`.

- `bot[N] = "BotName"` sets slot `N`'s bot name (a `BOTINFO` bot's config name, not a lump name),
  for example `bot[0] = SomeBot`. The value uses the same 31-character token cap as every other
  value in this lump; nothing shortens it further.
- `botteam[N] = "TeamName"` sets slot `N`'s team, consulted only when the active game mode has
  players on teams.

At map load, `G_DoLoadLevel` walks every slot and calls `BOTSPAWN_AddToTable` for each one that has
a name (and, in a team game, whose team is actually in use), building the roster of bots to spawn
for that map; any bots already present are removed first (`BOTS_RemoveAllBots`). The indices don't
need to be contiguous or ordered, since each is looked up independently by number. One parser quirk
worth knowing: the `botteam` prefix is checked before the plain `bot` prefix, so any misspelled key
that merely starts with `bot` (e.g. `bots0`) is still routed into `campaign_ParseBracketIndex` and
fails with its `Expected '['` error rather than the generic "Unknown CMPGNINF property" one.

## Loading: cumulative within one lump, but the last lump found wins wholesale

**This is the opposite of `ANCRINFO`'s cumulative-across-WADs loading, and it looks like a bug in
the engine, not a deliberate design choice.** `CAMPAIGN_ParseCampaignInfo` does scan every loaded
archive for a lump named `CMPGNINF` (`Wads.FindLump` loop) and calls `campaign_ParseCampaignInfoLump`
once per lump found, the same shape `ANCRINFO` uses. But at the top of
`campaign_ParseCampaignInfoLump`, before parsing that lump's own blocks, this loop runs
(`src/campaign.cpp:288-290`):

```cpp
pInfo = g_pCampaignInfoRoot;
while ( pInfo != NULL )
	pInfo = pInfo->pNextInfo;
```

This walks to the end of the existing global list and discards the result: the loop condition is
`pInfo != NULL`, so it always exits with `pInfo == NULL`, whatever the list already contained.
Immediately after, the very first block parsed from this lump hits `if ( pInfo == NULL )` and does
`g_pCampaignInfoRoot = pInfo`, overwriting the global list's head with a brand-new node. So parsing
a second `CMPGNINF` lump doesn't append to whatever a previously-parsed lump built: it replaces the
entire list, silently discarding (and leaking, since nothing frees the orphaned chain) every entry
the earlier lump declared. Within a single `CMPGNINF` lump, later blocks correctly chain onto
`pInfo->pNextInfo` and accumulate as expected; it's only the boundary between separate lumps where
the list is clobbered rather than extended.

**Net effect: only the last-found `CMPGNINF` lump's blocks exist at all** by the time anything
queries campaign info. `CAMPAIGN_GetCampaignInfo` (`src/campaign.cpp:146`) then walks that surviving
list and keeps the *last* entry whose `mapname` matches (case-insensitively, first 8 characters), so
within that one surviving lump, a later block for the same map still overrides an earlier block's
settings outright rather than merging field-by-field. But an entire earlier-loaded WAD's `CMPGNINF`
contributes nothing once a later WAD's `CMPGNINF` has been parsed, even for maps the later lump
never mentions.

## Wiki/engine divergence

The Zandronum Wiki states that `CMPGNINF` "is required to create Invasion maps." This is
overstated. Invasion maps do not require a `CMPGNINF` block: the engine will run an Invasion map
without one and use whatever `wavelimit` cvar is currently set (default `0`). A `CMPGNINF` block
for an Invasion map only takes effect if `sv_usemapsettingswavelimit` is enabled (which it is by
default), at which point it overrides the cvar with the block's `wavelimit` value. The block is
optional, not required.

## Engine-family divergence

UZDoom/GZDoom-family engines do not parse `CMPGNINF` and have no single-player campaign subsystem
of this shape (`CAMPAIGNINFO_s`, `CAMPAIGN_AllowCampaign`, the bot-roster/limit/flag override
machinery) to port it to.
