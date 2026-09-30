# Retrieving LANGUAGE strings: `$LABEL` and its consumers

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/common/engine/stringtable.cpp` and `.h` (`CheckString`, `GetString`, `localize`), `src/common/scripting/interface/stringformat.cpp` (`LocalizeString`, behind ZScript `StringTable.Localize`), `src/common/2d/v_drawtext.cpp` (`DrawText`), `src/common/engine/i_interface.cpp` (`language` cvar), `src/d_main.cpp` (`System_LanguageChanged`), `src/gamedata/g_mapinfo.cpp` (`LookupLevelName`, `ParseLookupName`, map and cluster parsing), `src/g_hub.cpp`, `src/g_level.cpp`, `src/intermission/intermission.cpp` and `intermission_parse.cpp`, `src/playsim/p_interaction.cpp` (`ClientObituary`), `src/playsim/p_mobj.cpp` (`GetTag`), `src/playsim/a_pickups.cpp` (`PrintPickupMessage`), `src/gamedata/a_keys.cpp` (`P_CheckKeys`), `src/playsim/p_actionfunctions.cpp` (`A_Print`, `A_PrintBold`, `A_Log`), `src/scripting/vmthunks.cpp` (`Console.MidPrint`), `src/playsim/p_acs.cpp` (`PCD_PRINTLOCALIZED`, `APROP_NameTag`), `src/g_statusbar/sbarinfo_commands.cpp` (`DrawString`), `src/sound/s_doomsound.cpp`, `src/gamedata/g_skill.cpp`, `wadsrc/static/zscript/engine/ui/menu/listmenuitems.zs` and `optionmenuitems.zs`, `wadsrc/static/zscript/actors/inventory/inv_misc.zs`; and the Zandronum source's `src/stringtable.cpp` (`operator()`, `operator[]`, `LoadStrings`), `src/doomstat.cpp` (`language` cvar), `src/g_mapinfo.cpp` (`LookupLevelName`, `ParseLookupName`, `ParseEpisodeInfo`, map and cluster parsing), `src/g_hub.cpp`, `src/intermission/intermission.cpp` and `intermission_parse.cpp`, `src/p_interaction.cpp` (`ClientObituary`), `src/p_mobj.cpp` (`GetTag`), `src/g_shared/a_pickups.cpp` (`PrintPickupMessage`), `src/g_shared/a_keys.cpp` (`P_CheckKeys`), `src/g_shared/a_puzzleitems.cpp`, `src/thingdef/thingdef_codeptr.cpp` (`A_Print`, `A_PrintBold`, `A_Log`), `src/p_acs.cpp` (`PCD_PRINTLOCALIZED`, `PCD_ENDPRINT`, `PCD_ENDHUDMESSAGE`, `APROP_NameTag`), `src/cl_main.cpp` (`client_DoInventoryPickup`, the client obituary call), `src/sv_commands.cpp` (`SERVERCOMMANDS_DoInventoryPickup`), `src/g_shared/sbarinfo_commands.cpp`, `src/menu/listmenu.cpp`, `src/menu/optionmenu.cpp`, `src/s_sound.cpp`, `src/g_skill.cpp`, `src/medal.cpp`, `src/scoreboard.cpp`, `src/scoreboard_margin.cpp` and `src/zstring.cpp`. No wiki page was used.

This page is the consumer side of LANGUAGE: which lumps and script APIs look a label up, what
form they want it in, when they do it, and what the player sees if the label does not exist. The
lump's own grammar, the `[code]` sections and which of several same-named strings wins are in
[The LANGUAGE lump](language-lump.md).

## The two lookup primitives

Every consumer below ends in one of two engine calls, and which one it uses decides its
missing-label behavior:

- **Lookup-or-label.** UZDoom `GStrings.GetString` (`src/common/engine/stringtable.cpp:1040-1087`)
  and Zandronum `GStrings(...)`, i.e. `operator()` (`src/stringtable.cpp:352-356`), return the
  string, or **the label itself** when it is missing. The label is returned as passed, which
  means **without** the `$`: a missing `$MY_TEXT` displays as `MY_TEXT`.
- **Lookup-or-null.** UZDoom `GStrings.CheckString` (`stringtable.cpp:957-990`) and Zandronum
  `GStrings[...]`, i.e. `operator[]` (`src/stringtable.cpp:325-348`), return null when the label
  is missing, and the consumer picks its own fallback.

Labels are case-insensitive on both engines. Most consumers only look a string up when its
**first character** is `$`, then pass everything after it as the label. The exceptions are ACS
`l:` and MAPINFO's `lookup` keyword, which take a bare label with no `$`.

## Consumer table

"Draw time" means the lookup runs every time the text is drawn, so it follows a language change
immediately. "Event time" means it runs once when the message is produced (a pickup, a death, a
failed lock). "Parse time" means the lookup runs once while the defining lump is read and the
result is stored, so a later language change never reaches it.

| Consumer | Form accepted | When resolved | Missing label shows | UZDoom | Zandronum |
|---|---|---|---|---|---|
| MAPINFO `map` level name | `map MAP01 lookup "LABEL"` or `map MAP01 "$LABEL"` | Level start, and again on a `language` change; also at each intermission and map-list print | Bare label | `src/gamedata/g_mapinfo.cpp:2233-2246`, `LookupLevelName` `:334-380` | `src/g_mapinfo.cpp:1640-1653`, `LookupLevelName` `:315-360` |
| MAPINFO cluster `EnterText` / `ExitText` | `lookup, "LABEL"` or `"$LABEL"` | When the text screen starts | Bare label | `src/gamedata/g_mapinfo.cpp:632-666`, `:842-870`; `src/intermission/intermission_parse.cpp:899-906`, `src/intermission/intermission.cpp:390` | `src/g_mapinfo.cpp:617-651`, `:724-736`; `src/intermission/intermission_parse.cpp:851-858`, `src/intermission/intermission.cpp:297` |
| MAPINFO cluster `Name` | Parsed as a lookup, but never looked up (see below) | Never | Bare label, always | `src/g_hub.cpp:122`, `src/g_level.cpp:2616` | `src/g_hub.cpp:135` |
| MAPINFO `intermission` TextScreen `Text` | `"$LABEL"`, see "Engine-family divergence" | When the text screen starts | UZDoom: bare label. Zandronum: never found, bare label | `src/intermission/intermission_parse.cpp:373-377` | `src/intermission/intermission_parse.cpp:310-319` |
| MAPINFO `intermission` `Background` | `"$LABEL"` naming a graphic | When the screen starts | UZDoom: the label is used as the graphic name. **Zandronum: crash** (null pointer read) | `src/intermission/intermission.cpp:166-168` | `src/intermission/intermission.cpp:110-114` |
| MAPINFO `intermission` Cast `CastName` | `"$LABEL"` | Draw time | Bare label | `src/intermission/intermission.cpp:752` | `src/intermission/intermission.cpp:583` |
| MAPINFO episode `name`, skill `Name` | `"$LABEL"` (no `lookup` form for episodes) | Draw time | Bare label | menu items, `src/gamedata/g_skill.cpp:501` | `src/menu/listmenu.cpp:521`, `src/g_skill.cpp:411` |
| MAPINFO / SNDINFO music name | `"$LABEL"`, whose text gets a `D_` prefix | Each time that music starts | The literal `$LABEL` is used as the music name, so nothing plays | `src/sound/s_doomsound.cpp:141-151` | `src/s_sound.cpp:2608-2618` |
| LOCKDEFS `Message` / `RemoteMessage` | `"$LABEL"` | Event time (each failed use) | Bare label | `src/gamedata/a_keys.cpp:220-230` | `src/g_shared/a_keys.cpp:175-185`, `:453-458` |
| DECORATE `Obituary` / `HitObituary` | `"$LABEL"` | Event time (each player death) | Falls back to a default obituary, never the label (see "Engine-family divergence") | `src/playsim/p_interaction.cpp:273-296` | `src/p_interaction.cpp:385-393` |
| DECORATE `Tag` | `"$LABEL"` | Each read of the tag (HUD, ACS, menus) | Bare label | `src/playsim/p_mobj.cpp:8625-8645` | `src/p_mobj.cpp:7938-7960` |
| DECORATE `Inventory.PickupMessage` (and `Health.LowMessage`, which feeds it) | `"$LABEL"` | Event time (each pickup) | Bare label | `src/playsim/a_pickups.cpp:46-59` | `src/g_shared/a_pickups.cpp:1068-1078`; online, `src/cl_main.cpp:7883-7890` |
| DECORATE `PuzzleItem.FailMessage` | `"$LABEL"` | Event time | UZDoom: bare label. Zandronum: the stock `TXT_USEPUZZLEFAILED` text | `wadsrc/static/zscript/actors/inventory/inv_misc.zs:165-167`, `src/scripting/vmthunks.cpp:2769-2778` | `src/g_shared/a_puzzleitems.cpp:52-53` |
| DECORATE `A_Print`, `A_PrintBold`, `A_Log` | `"$LABEL"` as the whole text argument | Each call | Bare label | `src/playsim/p_actionfunctions.cpp:1280`, `:1318`, `:1347` | `src/thingdef/thingdef_codeptr.cpp:2865`, `:2922`, `:2949` |
| MENUDEF item and title text, KEYCONF `addkeysection` / `addmenukey` titles | `"$LABEL"` | Draw time | Bare label | `wadsrc/static/zscript/engine/ui/menu/listmenuitems.zs:171`, `optionmenuitems.zs:77` | `src/menu/listmenu.cpp:418`, `:521`; `src/menu/optionmenu.cpp:405`, `:518` |
| SBARINFO `DrawString` with a quoted constant | `"$LABEL"` | UZDoom: every status bar tick. Zandronum: parse time | UZDoom: bare label. Zandronum: empty string | `src/g_statusbar/sbarinfo_commands.cpp:912-913` | `src/g_shared/sbarinfo_commands.cpp:843-848` |
| ACS `l:` cast in `Print`, `PrintBold`, `HudMessage`, `Log`, `StrParam` | **Bare label**, no `$` | When the print buffer is built, on the machine running the script | Bare label | `src/playsim/p_acs.cpp:8571-8582` | `src/p_acs.cpp:10735-10746` |
| ACS `s:` cast, and HUD message text generally | Never looked up | n/a | `s:"$LABEL"` prints `$LABEL` literally | same file, no lookup on `s:` | same file, no lookup on `s:` |
| ACS `GetActorProperty(tid, APROP_NameTag)` | Returns the resolved `Tag` | On the machine running the script | Bare label | `src/playsim/p_acs.cpp:4457` | `src/p_acs.cpp:5011` |
| ZScript `StringTable.Localize(s, prefixed = true)` | `"$LABEL"`; with `prefixed` false, the whole string is the label | Each call | Bare label; a string without `$`, or a lone `$`, comes back unchanged | `src/common/scripting/interface/stringformat.cpp:273-281` | no ZScript |
| ZScript `Screen.DrawText` | `"$LABEL"`, localized by default; `DTA_Localize, false` turns it off | Draw time | Bare label | `src/common/2d/v_drawtext.cpp:756-761` | no ZScript |
| Zandronum MEDALDEF `text`, SCORINFO column `DisplayName` / `ShortName`, boolean column `TrueText` / `FalseText` | `"$LABEL"` | Parse time | Bare label | no such lumps | `src/medal.cpp:222`, `src/scoreboard.cpp:908`, `:1988` |
| Zandronum SCORINFO margin `drawstring` text | `"$LABEL"` | Each margin refresh | Bare label | no such lumps | `src/scoreboard_margin.cpp:838-853`, `:1068-1074` |

Examples of the three label forms:

```mapinfo
map MAP01 lookup "MYMOD_MAP01"      // bare label after the lookup keyword
{
    next = "MAP02"
}
map MAP02 "$MYMOD_MAP02"            // $-prefixed shorthand
{
}
cluster 1
{
    exittext = lookup, "MYMOD_C1TEXT"   // note the comma after lookup
}
```

```decorate
actor MyKeyCard : Key
{
    Inventory.PickupMessage "$MYMOD_GOTKEY"
    Tag "$MYMOD_KEYTAG"
}
```

```acs
Print(l:"MYMOD_GREETING", s:" ", n:0);   // l: takes the label with no $
Print(s:"$MYMOD_GREETING");              // prints the text $MYMOD_GREETING, no lookup
```

```zscript
String greet = StringTable.Localize("$MYMOD_GREETING");
String same  = StringTable.Localize("MYMOD_GREETING", false);
```

### Level names strip their own map-number prefix

After a successful level-name lookup, both engines search the looked-up text for a prefix built
from the map's lump name and drop everything up to and including its first occurrence. For an
`ExMy` map the prefix is the lump name itself (`E1M1: `). For a `MAPxx` or `LEVELxx` map it is
only the number with the leading zeros gone (`1: ` for `MAP01`). Other lump names strip nothing.
So the stock-style string `"level 1: entryway"` for `MAP01` shows as `entryway`, and so would
`"MAP01: entryway"`, because it contains `1: ` too. The search is not anchored to the start, so
avoid `<n>: ` elsewhere in a level name's text (UZDoom `src/gamedata/g_mapinfo.cpp:348-374`,
Zandronum `src/g_mapinfo.cpp:328-356`). A missing label skips the stripping and shows the bare
label.

### Cluster `Name` is never translated

Both engines' cluster parsers set one flag for a `lookup`/`$` cluster name, while every consumer
(the hub intermission title, and UZDoom's `Level.GetClusterName()`) tests a different flag that
nothing sets. The label is shown as written, without the `$`. See
[the cluster block](../../mapinfo/concepts/cluster-block.md) for the full account.

## When a language change takes effect

- **Both engines refresh the current level's name** when the `language` cvar changes (UZDoom
  `src/d_main.cpp:3133-3142`, called from `src/common/engine/i_interface.cpp:94-99`; Zandronum
  `src/doomstat.cpp:63-68`).
- **Draw-time consumers** (menus, `CastName`, episode and skill names, UZDoom's SBARINFO
  `DrawString` and `Screen.DrawText`) switch on the next frame.
- **Event-time consumers** (pickups, obituaries, lock and puzzle messages, `A_Print`, ACS `l:`)
  use the new language for the next message. A message already on screen or in the console
  keeps its text, and so does a `StrParam` result built earlier.
- **Parse-time consumers** keep the language that was active when their lump was read:
  Zandronum's SBARINFO `DrawString` constants, MEDALDEF `text` and SCORINFO column names and
  boolean texts. SCORINFO margin `drawstring` text follows the change at the next margin refresh.
- On non-Windows Zandronum the cvar does not change the language at all; see
  [The LANGUAGE lump](language-lump.md#the-players-language).

## Engine-family divergence

**Obituary fallbacks** differ, and neither shows a missing obituary label:

- Zandronum looks the `$` label up with the null-returning form and, on a miss, prints
  `OB_DEFAULT` (`src/p_interaction.cpp:385-393`).
- UZDoom first checks for LANGUAGE labels named `Obituary_<Class>_<damagetype>` and then
  `Obituary_<Class>` (the attacker's class name), which take priority over the actor's
  `Obituary`/`HitObituary` property. After the property, a miss tries `DEFHITOB_<Class>` (melee
  only), then `DEFOB_<Class>`, then `OB_DEFAULT` (`src/playsim/p_interaction.cpp:247-256`,
  `:273-296`). UZDoom also picks the **dying player's** gender variant of the string, not the
  local player's.

**MAPINFO `intermission` TextScreen `Text`.** UZDoom treats `Text = "$LABEL"` as a lookup only
when it is a single string. With several comma-separated strings, a `$` in the first is kept as
literal text (`src/intermission/intermission_parse.cpp:373-377`). Zandronum appends a newline
after every string, including a single one, and later looks up everything after the `$`
(`src/intermission/intermission_parse.cpp:310-319`, `src/intermission/intermission.cpp:297`).
The label it searches for therefore ends in a newline and never matches, so the screen shows the
label text. Observed live (2026-09-29, local test builds, probe map): `Text = "$TESTLBL"` showed
the bare word `TESTLBL` on Zandronum and the LANGUAGE string on UZDoom, while ACS `l:"TESTLBL"`
resolved on both. Cluster `EnterText`/`ExitText` do not
have this problem on either engine, because they build the `$` string without a newline. For
portable intermission text, put the text in a cluster or use a literal string.

**MAPINFO `intermission` `Background = "$LABEL"`** on Zandronum reads through the null result of
a failed lookup and crashes if the label is missing (`src/intermission/intermission.cpp:110-114`).
UZDoom falls back to using the label as the graphic name (`src/intermission/intermission.cpp:166-168`).
Both observed live: Zandronum crashed as the screen started (SIGSEGV in
`DIntermissionScreen::Init`, `intermission.cpp:114`); UZDoom showed a black screen.

**SBARINFO `DrawString` constants** are resolved once at parse time on Zandronum, with the
null-returning lookup, so a missing label draws nothing and a language change is not picked up
(`src/g_shared/sbarinfo_commands.cpp:843-848`; a null assigned to the stored string gives an empty
string, `src/zstring.cpp:216-224`). UZDoom resolves the stored text on every status bar tick
(`src/g_statusbar/sbarinfo_commands.cpp:912-913`).

**Puzzle item fail message.** A missing `$` label falls back to the stock `TXT_USEPUZZLEFAILED`
text on Zandronum (`src/g_shared/a_puzzleitems.cpp:52-53`) but prints the bare label on UZDoom,
which only substitutes the stock text through the class default (`inv_misc.zs:137`, `:167`).

**UZDoom-only consumer behavior:**

- **Missing-label warning.** With `developer` nonzero, UZDoom prints `Translation not found
  '<label>'` once per label, for lookups that go through `GetString` only
  (`src/common/engine/stringtable.cpp:1044-1083`). Consumers that use `CheckString` (level names,
  obituaries, music) stay silent. Zandronum never warns.
- **Implicit level-name and cluster-text lookups.** A plain (non-`$`) level name whose first line
  matches, case-insensitively, the default-table string labelled with the map's lump name (for
  example `MAP01`) is turned into a lookup of that label. Cluster `EnterText`/`ExitText` do the
  same against `CLUSTERENTER<n>`/`CLUSTEREXIT<n>` (`src/gamedata/g_mapinfo.cpp:846-870`,
  `:2251-2256`). This lets stock IWAD text follow the player's language; it is not a feature to
  rely on in new content.
- **`$$` redirects** (see [The LANGUAGE lump](language-lump.md#engine-family-divergence)) are
  followed inside `CheckString`, so every consumer above follows them. A redirect whose target is
  missing counts as a missing label: `GetString` consumers show the label **originally**
  requested. There is no loop guard (`src/common/engine/stringtable.cpp:982-983`), so two strings
  redirecting to each other recurse without limit.
- **ZScript** `StringTable.Localize`, `Screen.DrawText`'s default localization, and
  `Console.MidPrint`'s `$` handling have no Zandronum counterpart, since Zandronum has no ZScript.

## Zandronum-specific: which machine's copy is used

LANGUAGE is not part of Zandronum's connect-time lump check, so a client's strings can differ from
the server's (see [The LANGUAGE lump](language-lump.md#zandronum-specific-which-machines-copy-is-used)).
Whether a player sees their own translation depends on where the lookup runs.

**Resolved on the server, sent to clients as finished text** (what the client receives was
resolved with the server's strings):

- ACS `l:` in a server-side script. `Print`/`PrintBold` send the built text
  (`src/p_acs.cpp:10962-10969`), and `HudMessage` does the same (`src/p_acs.cpp:11032-11050`).
  The same goes for a `StrParam` result and `GetActorProperty(..., APROP_NameTag)` in a
  server-side script.
- LOCKDEFS fail messages: the server resolves the `$` label and sends the text to the player who
  tried the lock (`src/g_shared/a_keys.cpp:453-458`).
- `PuzzleItem.FailMessage` (`src/g_shared/a_puzzleitems.cpp:52-63`).
- `A_Print`: the server resolves the text, then sends it to the player as a HUD message
  (`src/thingdef/thingdef_codeptr.cpp:2865-2893`).

**Resolved on each client, against its own table and language:**

- Pickup messages. The server sends the **unresolved** `PickupMessage` string, `$` included
  (`src/g_shared/a_pickups.cpp:1121`, `:1184`; `src/sv_commands.cpp:4114-4122`), and the
  client looks it up (`src/cl_main.cpp:7883-7890`).
- Obituaries. Clients run the obituary code themselves from the server's death notice
  (`src/cl_main.cpp:4224`); the server runs it only for its own console
  (`src/p_interaction.cpp:940-945`).
- Level names, menus, SBARINFO, intermission and cluster text, and ACS `l:` in a clientside
  script.

A server on a non-Windows host always resolves the first group with its `enu`/`default` strings,
so online those messages never follow a player's language. Only the second group does. For ACS
text that should be translated per player, print from a clientside script.

UZDoom has no split of this kind in the code read here: `PrintPickupMessage`, `A_Print` and lock
messages resolve their text on the machine that draws them, after a local-view check
(`src/playsim/a_pickups.cpp:49`, `src/playsim/p_actionfunctions.cpp:1281`,
`src/gamedata/a_keys.cpp:503-507`).

## See also

- [The LANGUAGE lump](language-lump.md): grammar, language codes, which string wins, override
  order.
- [CSV LANGUAGE format](csv-format.md) (UZDoom only).
- [`StrParam`](../../acs/functions/strparam.md) and [`HudMessage`](../../acs/functions/hudmessage.md)
  for the ACS print casts, including `l:`.
- [The LOCKDEFS lump](../../lockdefs/concepts/lockdefs-lump.md) for lock messages.
- [MAPINFO index](../../mapinfo/INDEX.md), especially
  [map blocks](../../mapinfo/concepts/map-block-and-inheritance.md),
  [cluster blocks](../../mapinfo/concepts/cluster-block.md) and
  [intermission blocks](../../mapinfo/concepts/intermission-block.md).
- [DECORATE index](../../decorate/INDEX.md) and [KEYCONF index](../../keyconf/INDEX.md).
- [MEDALDEF](../../zandronum-lumps/concepts/medaldef.md) and
  [SCORINFO](../../zandronum-lumps/concepts/scorinfo.md) (Zandronum only).
