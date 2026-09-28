# `LimitedToTeam <teamindex>` (actor property)

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki `DECORATE` (https://wiki.zandronum.com/w/index.php?title=DECORATE&oldid=2445, retrieved 2026-09-22) + verified against the Zandronum source at the 3.3-alpha checkout (line numbers below are at bdd0f7beb): `src/thingdef/thingdef_properties.cpp:1384-1388`, `src/actor.h:1014-1015`, `src/dobjtype.cpp:405-420`, `src/team.cpp:1526-1583` and `:1617-1670`, `src/p_mobj.cpp:5403-5405` and `:5438-5446` (`P_SpawnPlayer`), `src/p_interaction.cpp:2319-2336` (`PLAYER_SetTeam`), `src/g_level.cpp:396-400`, `src/p_acs.cpp:7627-7629` (`ACSF_SetPlayerClass`), `src/menu/optionmenuitems.h:1391-1404`, `src/teaminfo.cpp:104-126`, `src/teaminfo.h:38-40`, `wadsrc/static/teaminfo.txt`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_PROPERTY(limitedtoteam, I, Actor)` in `src/thingdef/thingdef_properties.cpp:1384`, stored in `AActor::LimitedToTeam` (`src/actor.h:1015`).

Restricts a player class to one team. In a game mode where players are on teams, only members of
that team can play the class. It does **not** move anyone onto the team; see "Wiki/engine
divergence" below.

## Value encoding

- `teamindex` is a zero-based index into the loaded `TEAMINFO` teams. The property stores it plus
  one (`thingdef_properties.cpp:1387`), and a stored 0 means "not limited"
  (`src/actor.h:1014`).
- Leaving the property out gives 0, since actor defaults start zeroed (`src/dobjtype.cpp:405-420`).
  There is no way to write "unrestricted" explicitly; see the 255 note below.
- `TEAMINFO` is its own lump, not a MAPINFO block (`src/teaminfo.cpp:104-119`). Teams are indexed
  in the order they are defined, and `ClearTeams` empties the list. At least 2 and at most
  `MAX_TEAMS` (4) teams must exist, or startup fails (`src/teaminfo.cpp:122-126`,
  `src/teaminfo.h:40`).
- With the stock `TEAMINFO` (`wadsrc/static/teaminfo.txt`), index 0 is **Blue**, 1 Red, 2 Green,
  3 Gold.

## Where it is enforced (Zandronum)

Every check goes through `TEAM_CheckTeamRestriction` (`src/team.cpp:1553-1572`). A class counts as
allowed when the game mode doesn't put players on teams (`GMF_PLAYERSONTEAMS`), when the class is
unrestricted, when the player is on "no team", or when the team matches. A player who isn't on a
team is allowed every class (`TEAM_IsActorAllowedForPlayer`, `:1526-1538`). The property is only
ever read from player-class defaults, so it has no effect on other actors.

- **Spawning and team changes.** `TEAM_EnsurePlayerHasValidClass` (`src/team.cpp:1617-1646`) runs
  server-side from `P_SpawnPlayer` (`src/p_mobj.cpp:5403-5405`) and from `PLAYER_SetTeam`
  (`src/p_interaction.cpp:2335-2336`). If the player's chosen class isn't allowed on their team,
  it switches them to the first allowed class in the player-class list (or to random under
  `sv_forcerandomclass`) and respawns them with inventory cleared. If no class is allowed,
  `TEAM_FindValidClassForPlayer` falls back to class 0 (`:1598-1613`).
- **Random class.** Picking the random class while on a team only chooses among classes allowed
  for that team (`TEAM_SelectRandomValidPlayerClass`, `src/team.cpp:1650-1670`; used by
  `src/p_mobj.cpp:5438-5446` and `src/g_level.cpp:396-400`).
- **ACS.** `SetPlayerClass` refuses a class the player's team isn't allowed
  (`src/p_acs.cpp:7627-7629`).
- **Join menu.** The class list in the team-join menu only offers classes allowed for the selected
  team (`src/menu/optionmenuitems.h:1391-1404`).
- **Campaigns.** When a campaign is loaded in single player, the engine switches into a
  single-player "fake multiplayer" state so team restrictions like this one can apply
  (`src/g_level.cpp:1307-1310`).

## Example

```decorate
// Stock TEAMINFO: index 0 is Blue, 1 is Red.
ACTOR BlueMarine : DoomPlayer
{
    Player.DisplayName "Blue Marine"
    LimitedToTeam 0
}

ACTOR RedMarine : DoomPlayer
{
    Player.DisplayName "Red Marine"
    LimitedToTeam 1
}
```

Define new classes rather than redefining `DoomPlayer`. Both classes also need to be in the game's
player-class list for players to pick them.

## Wiki/engine divergence

- **"Forces the Player class to a certain team."** The source restricts the class to the team; it
  never assigns a team. A player on another team who has the class selected is switched to a
  different class, not to the class's team.
- **"255 means not on a team and is set by default."** The default is not 255. An omitted property
  stores 0, which means unrestricted. 255 is the engine's "no team" number (`TEAM_None`,
  `src/teaminfo.h:38`), but writing `LimitedToTeam 255` stores 256, which restricts the class to
  a team index 255 that can't exist. In a team mode that makes the class usable only by players
  who aren't on a team.
- The wiki's own example is correct: index 1 is the second team, Red in the stock `TEAMINFO`, so
  index 0 is Blue.

## Engine-family divergence

UZDoom has no `LimitedToTeam` property. Nothing by that name exists in its source, so a DECORATE
definition using it fails to load with the parser's "unknown actor property" script error (UZDoom
source `src/scripting/decorate/thingdef_parse.cpp:977`). UZDoom does have a `TEAMINFO` lump, but no
per-class team restriction.

## See also

- [`VisibleToTeam`](visibletoteam.md): same index encoding, applied to rendering.
- [`VisibleToPlayerClass`](visibletoplayerclass.md): per-class visibility.
- [Creating player classes](../concepts/creating-player-classes.md).
