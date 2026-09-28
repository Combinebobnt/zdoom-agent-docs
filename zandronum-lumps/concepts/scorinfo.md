# The `SCORINFO` lump

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** Zandronum Wiki `SCORINFO` (https://wiki.zandronum.com/w/index.php?title=SCORINFO&oldid=1803, retrieved 2026-09-09); verified against Zandronum source's `src/scoreboard.cpp`, `src/scoreboard_margin.cpp`, and `src/scoreboard_enums.h`; custom-data ACS argument order from `src/p_acs.cpp:8176-8255`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0
(NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under
Zandronum's own license terms, see [LICENSE](../../LICENSE) §3.

`SCORINFO` is the scoreboard's own layout and behavior description language: it declares what
columns exist and how they're drawn, how the scoreboard as a whole is styled and sorted, and what
appears in the main header, team/spectator headers, and footer that frame it. Nothing about the
in-game scoreboard's visual structure is hardcoded; all of it is driven by `SCOREBOARD_Construct`
parsing every loaded `SCORINFO` lump (`src/scoreboard.cpp:3877-3979`) before the scoreboard object
is usable at all. This is by a wide margin the largest of the eight lumps in this section: the two
files that implement it together run to roughly 8,150 lines, against low hundreds to low
thousands for its siblings.

This page covers **structure only**: what the top-level blocks are, what the three command
enumerations that drive them govern, and how the format's one real piece of conditional logic
works. It deliberately does not catalog all of the individual commands with per-command semantics.
See the section's `AGENTS.md` for why that's left to future `inventory/`/`notes/` work.

## Flags and properties

Both the `scoreboard` block and column blocks (`column`/`compositecolumn`) support flags and properties declared with `AddFlag FLAGNAME` and `RemoveFlag FLAGNAME` for flags, or `PropertyName = <value>` for properties.

### Scoreboard flags (`SCOREBOARDFLAG_e`, 11 total)

Flags controlling scoreboard-wide appearance and layout behavior:

- `USETEAMTEXTCOLORS` — row text printed in team color (team-based modes only)
- `USEHEADERTEXTCOLORFORBORDERS` — header text color used for border lines. The enum's own
  comments on `LightBorderColor`/`DarkBorderColor` spell it `USEHEADERCOLORFORBORDERS`, which the
  parser rejects.
- `USETEXTUREFORBORDERS` — use specified texture for borders instead of lines
- `SHOWGAPSINROWBACKGROUND` — reveal gaps between columns in row background
- `DONTDRAWBORDERS` — suppress all border drawing
- `DONTSEPARATETEAMS` — single player list, no team headers
- `DONTUSELOCALROWBACKGROUNDCOLOR` — ignore local row background color override
- `DONTSHOWTEAMHEADERS` — suppress team and spectator headers
- `DONTSTRETCHROWHEIGHT` — don't auto-stretch rows to fit tall content
- `SEPARATEDEADSPECTATORS` — sort dead spectators below live players
- `ONLYSHOWLOCALROWBACKGROUND` — only show viewing player's row background

### Column flags (`COLUMNFLAG_e`, 18 total)

Flags controlling per-column visibility and sorting:

- `REVERSEORDER` — sort lowest-to-highest instead of highest-to-lowest
- `INTERMISSIONONLY` — only visible on intermission screen
- `NOINTERMISSION` — hidden on intermission screen
- `SPECTATORSONLY` — visible only for true spectators
- `NOSPECTATORS` — hidden for true spectators
- `NOENEMIES` — hidden for opposing team members
- `OFFLINEONLY` — offline/singleplayer games only
- `ONLINEONLY` — online games only
- `REQUIRESTEAMS` — only in team-supporting game modes
- `FORBIDTEAMS` — disabled in team-supporting game modes
- `REQUIRESLIVES` — only in game modes with lives
- `FORBIDLIVES` — disabled in game modes with lives
- `REQUIRESTEAMITEMS` — only in modes with team items
- `FORBIDTEAMITEMS` — disabled in modes with team items
- `DONTSHOWHEADER` — suppress column header
- `ALWAYSUSESHORTESTWIDTH` — width is the shortest that fits the contents and header, with `Size`
  added as padding. Without this flag a zero `Size` is a fatal parse error.
- `DISABLEIFEMPTY` — disable column when it has no contents
- `SORTWHENDISABLED` — still sort by this column even if disabled

## Native column types

`COLUMNTYPE_e` defines 25 built-in column types. Each has a data type and auto-updated value:

| Type | Data type | Description |
|---|---|---|
| `Name` | string | Player name |
| `Index` | int | Player index number |
| `Time` | int | Minutes played in current game |
| `Ping` | int | Network latency in milliseconds (bots show the string `BOT`) |
| `Frags` | int | Frag count |
| `Points` | int | Point count |
| `Wins` | int | Win count |
| `Kills` | int | Kill count |
| `Deaths` | int | Death count |
| `Secrets` | int | Secrets discovered |
| `Lives` | int | Remaining lives |
| `Damage` | int | Damage dealt: reads the same counter as `Points`, which damage feeds only with `sv_awarddamageinsteadkills` on in a mode where players earn kills |
| `Handicap` | int | Starting health minus the handicap (max armor minus it in (team) LMS); blank when the handicap is 0 |
| `JoinQueue` | int | Join queue position |
| `Vote` | string | Current vote choice |
| `PlayerColor` | color | Player's team/custom color |
| `StatusIcon` | texture | Player status (lagging/talking/chatting/console/menu) |
| `ReadyToGoIcon` | texture | Intermission readiness |
| `PlayerIcon` | texture | Class's `ScoreIcon` property |
| `ArtifactIcon` | texture | Gamemode-specific item (flag/skull/terminator sphere/etc.) |
| `BotSkillIcon` | texture | Bot skill level |
| `ConnectionStrength` | texture | Network connection strength |
| `CountryName` | string | Player's country (full name) |
| `CountryCode` | string | Player's country (alpha-2/3 code) |
| `CountryFlag` | texture | Country flag (16×16 grid in `CTRYFLAG` lump) |

A custom column defined as `Column "MyColumn" { ... }` with a name that doesn't match any native type requires a matching entry in MAPINFO's `GameInfo` block:

```mapinfo
GameInfo
{
	AddCustomData = "MyColumn", "int", 0
}
```

Custom data is per-player, auto-reset on disconnect/new game, and manipulated via three ACS functions, all taking the data name first: [`GetCustomPlayerValue(data, player)`](../../acs/functions/getcustomplayervalue.md), [`SetCustomPlayerValue(data, player, value)`](../../acs/functions/setcustomplayervalue.md), and [`ResetCustomDataToDefault(data, player)`](../../acs/functions/resetcustomdatatodefault.md), where a negative `player` resets every player (`src/p_acs.cpp:8176-8255`).

## Three top-level declaration blocks

`SCOREBOARD_Construct` reads each `SCORINFO` lump as a flat sequence of top-level keywords
(`src/scoreboard.cpp:3893-3973`); any other bare token at that level is a fatal `sc.ScriptError`
("Unknown option '%s'..."). There are exactly three:

- **`scoreboard { ... }`**, configures the single global `Scoreboard` object: fonts, text and
  background colors, border style, spacing, header/row height, and two independently-orderable
  lists (`columnorder`, which columns appear and in what left-to-right order, and `rankorder`,
  which columns are used to sort players top-to-bottom). It also nests the margin declarations
  (`mainheader`, `teamheader`, `spectatorheader`, `footer`), each parsed as its own sub-block
  (`Scoreboard::Parse`, `src/scoreboard.cpp:2675`).
- **`column "Name" { ... }`**, declares or extends one data column. The name is looked up
  against `COLUMNTYPE_e` first; a recognized name (`frags`, `time`, `ping`, ...) yields a native
  column, an unrecognized one falls back to `COLUMNTYPE_CUSTOM` and requires matching
  `gameinfo.CustomPlayerData` to already exist, and a `countryflag` column gets its own subclass.
  Every case shares one grammar and dispatch (`ScoreColumn::Parse`, `src/scoreboard.cpp:848`;
  `ScoreColumn::ParseCommand`, `src/scoreboard.cpp:898`).
- **`compositecolumn "Name" { ... }`**, declares a column that is itself a horizontal grouping of
  other columns (its own `columns`/`addtocolumns`/`removefromcolumns` commands govern the
  sub-column list and order). A composite column can't reuse a native column-type name.

A block re-opening an existing name (by exact column name, case-insensitively via `FName`)
extends the same column object rather than creating a second one. `SCOREBOARD_Construct` looks
the name up first and only allocates a new `ScoreColumn`/`CompositeScoreColumn` if none exists yet
(`src/scoreboard.cpp:3914-3915`, `3921-3928`, `3935-3957`). One inline comment in the source
(`src/scoreboard.cpp:827`) also mentions a `"customcolumn"` block; there is no such keyword in the
actual dispatch: a custom column is just a `column` block whose name doesn't match a native
`COLUMNTYPE_e`, not a separate top-level form.

## The command language: three enum families

Underneath the three block types, `SCORINFO` reads its actual key/value commands through three
enums, all declared together in `src/scoreboard_enums.h:254-425`. Each is resolved with
`FScanner::MustGetEnumName` against its own name prefix, so an unrecognized command name inside a
block is also a fatal parse error, not a silently-ignored key (unlike `ANCRINFO`'s open-ended
key set).

### Column commands: `COLUMNCMD_e` (22 commands)

Read inside a `column`/`compositecolumn` block (`ScoreColumn::ParseCommand`,
`src/scoreboard.cpp:898`, and the composite-specific override at `src/scoreboard.cpp:2278`).
These govern one column's own layout and content: its header text (`displayname`, `shortname`),
sizing and alignment, which game modes/game types/earn types it's restricted to, the controlling
`cvar`, and type-specific commands that only make sense for certain column kinds (`truetext`/
`falsetext` for boolean columns, `scale` for texture columns, `columns`/`addtocolumns`/
`removefromcolumns` for composite columns only). A representative slice, quoted verbatim:

```cpp
// The text that gets drawn in a column's header.
ENUM_ELEMENT( COLUMNCMD_DISPLAYNAME ),
// A shorter or abbreviated version of the display name.
ENUM_ELEMENT( COLUMNCMD_SHORTNAME ),
// How the contents inside the column are aligned (left, center, or right).
ENUM_ELEMENT( COLUMNCMD_ALIGNMENT ),
```

The enum's own trailing sentinel, `NUM_COLUMNCMDS`, is not a real command. It exists purely as
the array-bound marker `EnumToString`-style enums in this codebase always end with. A naive count
of `ENUM_ELEMENT` lines in the block includes it and overstates the real command count by one;
the true figure is 22, not 23.

### Scoreboard commands: `SCOREBOARDCMD_e` (31 commands)

Read inside the top-level `scoreboard` block itself (`Scoreboard::Parse`,
`src/scoreboard.cpp:2675`, `switch` starting `2714`). These govern the scoreboard as a whole
rather than any one column: header/row fonts and text colors, border texture and colors, row and
background opacity, every inter-element spacing value (header-to-rows, between columns, between
rows, column padding), and the two order lists already mentioned above
(`columnorder`/`addtocolumnorder`/`removefromcolumnorder`, `rankorder`/`addtorankorder`/
`removefromrankorder`). Same trailing-sentinel caveat applies (`NUM_SCOREBOARDCMDS`); the real
command count is 31.

### Margin commands: `MARGINCMD_e` (19 commands)

Read inside a `mainheader`/`teamheader`/`spectatorheader`/`footer` block
(`ScoreMargin::Parse`, `src/scoreboard_margin.cpp:2977`, dispatching through
`scoreboard_CreateMarginCommand`, `src/scoreboard_margin.cpp:3481`). These are HUD-drawing
primitives rather than layout properties: `drawstring`/`drawcolor`/`drawtexture` place one element
at a position in the margin, `drawmedals` draws a player's earned medals (and is only legal
inside `mainheader`/`footer`, `src/scoreboard_margin.cpp:3510-3514`), and `multilineblock`/
`rowblock` group several such elements into a block that lays its children out vertically or
horizontally. The remaining 13 of the 19 are the `if*` conditionals covered next. Real command
count is 19, not 20, same trailing-sentinel (`NUM_MARGINCMDS`) caveat as the other two families.

A `mainheader`/`teamheader`/`spectatorheader`/`footer` block can also open with the identifier
`append` before its `{`; this makes the block's commands extend whatever that margin already had
(from an earlier `scoreboard` block in the same or an earlier-loaded lump) instead of replacing it
outright (`ScoreMargin::Parse`, `src/scoreboard_margin.cpp:2977-2990`). Without `append`, a margin
block clears and replaces the margin's prior command list.

## Flow control: the one real conditional-logic surface in this section

Of the eight lumps in this section, `SCORINFO`'s margin grammar is the only one with genuine
conditional branching. Thirteen of `MARGINCMD_e`'s 19 commands are `if`-style flow-control
commands: `ifonlinegame`, `ifintermission`, `ifplayersonteams`, `ifplayershavelives`,
`ifshouldshowrank`, `ifspying`, `ifspectator`, `ifdeadspectator`, `ifplayerhasmedals`,
`ifgamemode`, `ifgametype`, `ifearntype`, and `ifcvar`. All of them share one base class,
`FlowControlBaseCommand` (`src/scoreboard_margin.cpp:2243`), which supplies the actual control
flow: each condition can be chained with `&&`/`||` into short-circuited stacks-of-stacks, an
optional `else { ... }` (or a bare `else if...`-style follow-on condition with no braces) selects
the alternate block, and the condition is **re-evaluated on every refresh**, not once at parse
time (`FlowControlBaseCommand::Refresh`, `src/scoreboard_margin.cpp:2329-2355`), so a scoreboard
skin can, for example, show a different footer line the instant a player becomes a spectator or a
watched cvar's value changes, without a scoreboard reload.

The individual conditions vary in what they test:

- The nine boolean ones (`ifonlinegame`, `ifintermission`, `ifplayersonteams`, `ifplayershavelives`,
  `ifshouldshowrank`, `ifspying`, `ifspectator`, `ifdeadspectator`, `ifplayerhasmedals`) each take
  a single `true` or `false` argument to test the condition or its negation; any other argument is
  read as a number, nonzero meaning `true` (`TrueOrFalseFlowControl`,
  `src/scoreboard_margin.cpp:2425`, parsing at `2471-2483`).
- `ifgamemode` takes a comma-separated list of game mode names and is true if the current mode is
  any of them (`IfGameModeFlowControl`, `src/scoreboard_margin.cpp:2561`).
- `ifgametype` takes a comma-separated list of game type flags (cooperative, deathmatch, teamgame)
  and is true if the current type is any of them (`IfGameOrEarnTypeFlowControl`,
  `src/scoreboard_margin.cpp:2613`).
- `ifearntype` takes a comma-separated list of earn type flags (frags, points, wins, kills) and is
  true if players can earn any of them (`IfGameOrEarnTypeFlowControl`, `src/scoreboard_margin.cpp:2613`).
- `ifcvar` is the most expressive: `ifcvar( <cvar-name> <operator> <value> )` with a full
  comparison-operator set and a value typed to match the cvar (`IfCVarFlowControl`,
  `src/scoreboard_margin.cpp:2679-2764`):

```cpp
if ( sc.CheckToken( TK_Eq ))
	Operator = OPERATOR_EQUAL;
else if ( sc.CheckToken( TK_Neq ))
	Operator = OPERATOR_NOT_EQUAL;
else if ( sc.CheckToken( '>' ))
	Operator = OPERATOR_GREATER;
else if ( sc.CheckToken( TK_Geq ))
	Operator = OPERATOR_GREATER_OR_EQUAL;
else if ( sc.CheckToken( '<' ))
	Operator = OPERATOR_LESS;
else if ( sc.CheckToken( TK_Leq ))
	Operator = OPERATOR_LESS_OR_EQUAL;
```

`multilineblock` and `rowblock` are not conditionals themselves; they're the two block-grouping
commands (`BlockBaseCommand`, `src/scoreboard_margin.cpp:492`, and its `MultiLineBlock`/
`RowBlock` subclasses) that lay a set of child draw/flow-control commands out as a vertical block
of lines or a single horizontal row, respectively. A flow-control command's own `if`/`else`
bodies are themselves ordinary margin-command blocks, so any of these constructs, including
another nested `if`, can appear inside either one.

`SCORINFO` uses the modern `FScanner`-based parser family (`sc.ScriptError` on a bad token
throughout both files), the same generation as `MEDALDEF`/`VOTEINFO`/`AUTHINFO`, rather than the
older Skulltag-era hand-rolled scanner `ANCRINFO`/`CMPGNINF` share. Like `MEDALDEF` and
`AUTHINFO` (and unlike `VOTEINFO`), it never calls `FScanner::SetCMode(true)`, so it runs the
scanner's default classic-Hexen tokenizer rather than genuine C-mode; see
[`concepts/parsing-model.md`](parsing-model.md) for the cross-format detail on what that split
means for error behavior and parser generation axes.

## Wiki/source divergence: scoreboard property and command name spellings

The Zandronum Wiki's documentation of scoreboard properties and column commands uses friendly,
abbreviated names that do not exactly match the enum suffix names the parser expects. For example,
the wiki lists `HeaderColor = "<text color>"` but the parser expects `HeaderTextColor` (matching
the enum `SCOREBOARDCMD_HEADERTEXTCOLOR`). The parser uses `FScanner::MustGetEnumName` with
enum-prefix matching (`src/scoreboard.cpp:2709`), meaning only the exact suffix names (case-insensitive)
are recognized as valid; the wiki's friendly abbreviations will fail to parse. This affects:

- Color properties: the wiki abbreviates all `*TextColor` suffixes as `*Color` (e.g. `HeaderColor`
  instead of `HeaderTextColor`); `LocalRowDemoColor` should be `LocalRowDemoTextColor`
- Game mode/type properties: `GameMode`/`GameType` should be `GameModes`/`GameType` (note singular
  `GameType`)
- Scoreboard flag names: `USETEAMTEXTCOLOR` should be `USETEAMTEXTCOLORS` (plural); flag at
  `src/scoreboard_enums.h:226` is `SCOREBOARDFLAG_USETEAMTEXTCOLORS`
- Column flag that doesn't exist: the wiki lists `CVARMUSTBEZERO` as a flag; nothing by that name
  exists at HEAD. Commit `8306614a9` (before 3.2.1) removed it in favor of the `cvar` command's
  optional value range, `cvar = <name>[, <min>[, <max>]]`, which the CVar's value must fall inside
  for the column to stay active (`src/scoreboard.cpp:985-1040`, checked at `1161`)

The wiki's documentation represents the design intent and is pedagogically useful; the source is
authoritative for actual SCORINFO lump syntax.

## Engine-family divergence: no counterpart outside Zandronum

UZDoom/GZDoom-family engines have no `SCORINFO`-driven scoreboard subsystem; their scoreboard
presentation is handled elsewhere (ZScript-side HUD code) with no equivalent declarative lump
format to port this to.
