# The `TEAMINFO` lump

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes — both parse it, but only Zandronum acts on most keys
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-22); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** engine source only. The Zandronum source, read at the `3.3-alpha` checkout
`bdd0f7beb`, with the 3.2.1 commit `28f736fb3` read for the 3.2.1 comparisons: `src/teaminfo.cpp` (`TEAMINFO_Init`
104-130, `TEAMINFO_ParseTeam` 138-247), `src/teaminfo.h`, `src/team.cpp` (`TEAM_Reset` 136,
`TEAM_GetTeamNumberByName` 758, `TEAM_GetTextColor` 810, `TEAM_GetItem` 1010, `TEAM_ShouldUseTeam`
1367, `TEAM_GetTeamFromItem` 1489, `TEAM_GetPlayerStartThingNum` 1694), `src/v_video.cpp`
(`V_GetColor`, `V_GetColorFromString`), `src/p_mobj.cpp:5886` (`P_SpawnMapThing` team starts),
`src/p_setup.cpp:4396`, `src/d_main.cpp:2991-2993`, `src/d_netinfo.cpp:381`,
`src/wi_stuff.cpp:450-456` (`WI_UseMapOrTeamIntermissionAndMusic`), `src/wi_stuff.cpp:521-523,2583-2591`, `src/scoreboard_margin.cpp:1911`, `src/network.cpp`
(base authenticated-lump set), `wadsrc/static/teaminfo.txt`; the HEAD diffs of `teaminfo.cpp`,
`team.cpp` and `wi_stuff.cpp` against 3.2.1 for the version notes. The UZDoom source's
`src/gamedata/teaminfo.cpp`, `src/gamedata/teaminfo.h`, `src/d_main.cpp`,
`wadsrc/static/teaminfo.txt`.

`TEAMINFO` defines the teams used by team game modes: name, player color, text color, and on
Zandronum the team's flag/skull item classes, its player-start thing number, its HUD icons and its
intermission graphics and music. It is the one lump in this section that UZDoom also parses (see
"Engine-family divergence" below). No wiki page has been intaken for it; this file is written from
engine source alone. The team-item side (`FlagItem`/`SkullItem`) is covered in depth in
[`decorate/families/team-items.md`](../../decorate/families/team-items.md) and only summarized here.

## Syntax

```text
ClearTeams

Team "Purple"
{
    PlayerColor "A0 00 C0"
    TextColor "Purple"
    RailColor "C0 40 FF"
    FlagItem "PurpleFlag"
    SkullItem "PurpleSkull"
    PlayerStartThingNumber 5085
    AllowCustomPlayerColor
}

Team "Orange"
{
    // ...same keys; fewer than two teams in total is fatal
}
```

Two top-level commands exist: `ClearTeams` and `Team <name> { ... }`. Anything else at the top
level raises `sc.ScriptError` ("Unknown command"). Inside a block, an unknown key is a separate
`I_FatalError` naming the key and line (`teaminfo.cpp:241`). Both abort startup. The scanner runs in
its default (non-C) mode, and keys are matched with `MatchString`, so key names are
case-insensitive. The team name is read with `MustGetString`, so quoting is only needed for names
containing spaces or special characters.

## Loading: cumulative, and the stock lump already fills every slot

`TEAMINFO_Init` loops over every `TEAMINFO` lump in load order. Each `Team` block pushes a new
entry onto the global `teams` array. Nothing is merged: a second block with an existing team's name
creates a second team, and name lookups (`TEAM_GetTeamNumberByName`, case-insensitive) return the
first. `ClearTeams` empties the array at the point it appears.

After all lumps are read, fewer than 2 teams or more than `MAX_TEAMS` (4) is fatal. The engine's
own `wadsrc/static/teaminfo.txt` starts with `ClearTeams` and defines exactly four teams (Blue, Red,
Green, Gold, in that order). Consequences:

- **A mod cannot add a fifth team.** Four is a compile-time limit.
- **A mod's `TEAMINFO` without `ClearTeams` is always fatal on Zandronum**, since any `Team` block
  appends to the stock four and trips the "Only 4 teams" check. To change even one stock team, start
  with `ClearTeams` and redefine every team you want, in index order.
- Team indices are array positions, so the definition order is what `VisibleToTeam`, ACS team
  numbers, and the `Blue`/`Red`-return script assignment in `TEAM_Reset` (index 0 and 1) key off.

`sv_maxteams` (default 2) is clamped to the loaded team count at the end of `TEAMINFO_Init`, and
`TEAM_CheckIfValid` treats indices at or above `min(teams, sv_maxteams)` as invalid. So with the
default, only the first two teams are usable; a third or fourth team (stock Green and Gold included)
stays invalid until the server raises `sv_maxteams`.

`TEAMINFO_Init` runs at `d_main.cpp:2991`, after `SECTINFO` and immediately before
`FActorInfo::StaticInit` loads DECORATE. So class-name keys can't be validated at parse time; they're
stored as strings and resolved later.

## Keys

| Key | Argument | Used for |
|---|---|---|
| `PlayerColor` | color string | Team player color. Also the spawn-fountain color and the master-server team color. |
| `TextColor` | font color name | Team name/message color. |
| `RailColor` | color string, no names | Default rail color for team members. |
| `Logo` | texture name | Only consumer is SCORINFO's team-logo margin value (`scoreboard_margin.cpp:1911`). |
| `FlagItem` / `SkullItem` | class name | The team's item in flag modes / Skulltag. |
| `PlayerStartThingNumber` | integer | Editor number of this team's player starts. |
| `SmallFlagHUDIcon`, `SmallSkullHUDIcon`, `LargeFlagHUDIcon`, `LargeSkullHUDIcon` | graphic name | HUD/scoreboard icons for the team item. |
| `WinnerPic` / `LoserPic` | graphic name | Intermission victory/defeat graphic. |
| `WinnerTheme` / `LoserTheme` | music name | Intermission victory/defeat music. |
| `AllowCustomPlayerColor` | none | Lets team members keep their own player color. |

Per-key behavior worth knowing:

- **`PlayerColor` vs. `RailColor` accept different syntaxes.** `PlayerColor` goes through
  `V_GetColor`, which first tries the value as an X11 color name (`X11R6RGB` lump), then as a
  literal. `RailColor` calls `V_GetColorFromString` directly, so it only takes the literal forms
  (`"RR GG BB"` or `#RRGGBB`/`#RGB`); a color name there doesn't resolve. How the rail color is
  actually applied (and when it's overridden) is in
  [`decorate/actions/a_railattack.md`](../../decorate/actions/a_railattack.md).
- **`TextColor` is stored wrapped in brackets** (`Blue` becomes `[Blue]`) and parsed as a font-color
  escape every time it's read. An unknown name silently falls back to untranslated on Zandronum.
  **Omitting the key garbles team messages.** `TEAM_GetTextColorName` then returns the bare word
  `Untranslated` (no brackets), and callers splice it straight after a color escape (`\034`). The
  escape parser (`V_ParseFontColor`) reads the single letter `U` as a standard color code (dark
  gray), so the rest prints as literal text, e.g. "ntranslatedPurple team!". This comes from reading
  the source, not a test run. Always set `TextColor`.
- **`PlayerStartThingNumber` is checked before any actor lookup.** `P_SpawnMapThing` tests each map
  thing's editor number against the teams in order, right after the deathmatch start (11) and
  temporary team start (5082) checks. A match registers a team start and spawns nothing. So a number
  that collides with a real actor's editor number swallows every instance of that actor, and if two
  teams share a number only the first gets starts. Team starts are cleared per map (`p_setup.cpp:4396`),
  and in a `TEAMGAME` mode a team with no starts on the current map is skipped by
  `TEAM_ShouldUseTeam`. The stock teams use 5080, 5081, 5083 and 5084.
- **`FlagItem`/`SkullItem` identify the team item by exact class.** `TEAM_GetItem` picks `FlagItem`
  when the game mode has `USEFLAGASTEAMITEM`, else `SkullItem`, and resolves it with
  `PClass::FindClass`; a subclass doesn't count. A missing or misspelled class returns null, with a
  fatal outcome on the first item return. Full detail, including why `replaces` on a stock flag is
  fragile: [`team-items.md`](../../decorate/families/team-items.md).
- **`AllowCustomPlayerColor` takes no argument.** Writing a value after it makes the scanner read
  that value as the next key, which is then fatal as an unknown option. Without the flag, a team
  member's own color setting is overridden (`d_netinfo.cpp:381`).
- **`WinnerPic`/`LoserPic`/`WinnerTheme`/`LoserTheme` only apply to the console player's own team**,
  and only when that player is on a team (`TEAM_SelectCustomStringForPlayer`). An empty key falls
  back to the default. The intermission consults them only in Doom, with `compat_oldintermission`
  off, and when `deathmatch` or `teamgame` is set (`WI_UseMapOrTeamIntermissionAndMusic`). The
  `teamgame` half was added after 3.2.1 (`f9e268ae9`): a 3.2.1 client uses them only in
  `deathmatch`-based modes such as team deathmatch, never in CTF or Skulltag. At 3.2.1 the defaults
  are hardcoded (`WINERPIC`/`LOSERPIC`, `d_stwin`/`d_stlose`); the checkout's `3.3-alpha` HEAD falls
  back to the MAPINFO keys instead, added after 3.2.1 in `95735f243` (see
  [`mapinfo/concepts/zandronum-map-extensions.md`](../../mapinfo/concepts/zandronum-map-extensions.md)).
  At 3.2.1 the theme keys take a plain string. HEAD parses them with MAPINFO's music syntax, which
  adds an optional `:order` track suffix; that form postdates 3.2.1 (also `95735f243`).

The ACS read-side of most of these is
[`GetTeamProperty`](../../acs/functions/getteamproperty.md).

## Zandronum-specific: omitted keys leave garbage, and TEAMINFO isn't authenticated

**Omitted numeric keys are uninitialized.** `TEAMINFO_ParseTeam` builds each team in a local
struct with no constructor for its scalar fields. It explicitly initializes only
`AllowCustomPlayerColor`'s flag (and, at HEAD, the theme track orders). `TEAM_Reset` later zeroes
scores and carrier state but not `PlayerColor`, `RailColor` or `PlayerStartThingNumber`. So a team
block that omits any of those three holds an indeterminate value. Omitting `PlayerStartThingNumber`
is the risky one, since that value is compared against every map thing. This comes from reading the
source, not a test run. Always set all three.

**`TEAMINFO` is not in the network authentication base set.** `NETWORK_Construct`'s always-hashed
lumps include `GAMEMODE`, `MAPINFO`, `VOTEINFO` and `MEDALDEF` but not `TEAMINFO`, so a client with
a different `TEAMINFO` than the server isn't rejected at connect. Add it with `AUTHINFO`'s
`addlump` if that matters (see [`authinfo.md`](authinfo.md)).

## Engine-family divergence

UZDoom has its own parser (`FTeam::ParseTeamInfo`, `src/gamedata/teaminfo.cpp`), a GZDoom-lineage
rewrite rather than Zandronum's Skulltag-era one. It reads the same file shape but differs:

- **Only `PlayerColor`, `TextColor`, `Logo` and `AllowCustomPlayerColor` are kept.** UZDoom has no
  CTF or Skulltag modes. It still accepts every Zandronum key so a shared lump parses: it reads and
  discards `PlayerStartThingNumber` as a number, and `RailColor`, `FlagItem`, `SkullItem`, the four
  HUD icon keys, `WinnerPic`, `LoserPic`, `WinnerTheme` and `LoserTheme` as strings.
- **`Game` is UZDoom-only.** `Game <name>` (or `Any`) restricts a team to matching games. A block
  with no `Game` key is always kept; one whose `Game` keys all name other games is dropped. A shared
  lump using `Game` is fatal on Zandronum (unknown option).
- **Limit is 16 teams, and the stock lump defines 8**, so a UZDoom mod can append teams without
  `ClearTeams`. The same lump is fatal on Zandronum.
- **Errors are all `ScriptError`**, including an unknown key inside a block.
- **Scalars are zero-initialized** by `FTeam`'s constructor, so omitted keys don't leave garbage.
- **An unknown `TextColor` name prints a warning** each time it's resolved, instead of failing
  silently.
- The team list is exposed to ZScript as the global `Teams` array of `FTeam` (name, player/text
  color, logo, `IsValid`, `ChangeTeam`).
