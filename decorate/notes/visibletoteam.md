# `VisibleToTeam <teamindex>` (actor property)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-22); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki `DECORATE` (https://wiki.zandronum.com/w/index.php?title=DECORATE&oldid=2445, retrieved 2026-09-22) + verified against the Zandronum source at the 3.3-alpha checkout (line numbers below are at bdd0f7beb): `src/thingdef/thingdef_properties.cpp:1393-1397`, `src/actor.h:1011-1012`, `src/p_mobj.cpp:1283-1315` (`AActor::IsVisibleToPlayer`), `src/team.cpp:1553-1572` and `:1674-1690`, `src/r_things.cpp:531-535`, `src/gl/scene/gl_sprite.cpp:509`, `src/gl/dynlights/gl_dynlight1.cpp:192`, `src/teaminfo.h:38`, `wadsrc/static/teaminfo.txt`; and the UZDoom source's `src/scripting/thingdef_properties.cpp:1142-1146`, `src/playsim/p_mobj.cpp:1458-1491`, `src/d_netinfo.cpp:52,475-482`, `src/g_game.cpp:251`, `wadsrc/static/teaminfo.txt`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_PROPERTY(visibletoteam, I, Actor)` in `src/thingdef/thingdef_properties.cpp:1393`, stored in `AActor::VisibleToTeam` (`src/actor.h:1012`).

Hides an actor from the local view of every player not on the given team. Any actor class can use
it. It only affects drawing, not gameplay.

## Value encoding

- `teamindex` is a zero-based index into the loaded `TEAMINFO` teams (its own lump, not a MAPINFO
  block). The property stores it plus one (`thingdef_properties.cpp:1396`), and a stored 0 means
  "visible to everyone" (`src/actor.h:1011`). Leaving the property out gives 0.
- With the stock `TEAMINFO` on both engines, index 0 is **Blue** and 1 is Red.

## Behavior (Zandronum)

- The check is `AActor::IsVisibleToPlayer` (`src/p_mobj.cpp:1283-1315`), which calls
  `TEAM_IsActorVisibleToPlayer` (`src/team.cpp:1674-1690`) for the player the local **camera** is
  attached to. Spectating or spying on another player shows what that player sees. If the camera
  isn't a player, the actor is shown.
- The actor is shown to everyone unless the game mode puts players on teams
  (`GMF_PLAYERSONTEAMS`). Players who aren't on a team see it too. Otherwise the viewed player's
  team must match (`TEAM_CheckTeamRestriction`, `src/team.cpp:1553-1572`).
- **Rendering only, traced.** Apart from savegame serialization, the field's only reader is
  `TEAM_IsActorVisibleToPlayer`, whose only caller is `IsVisibleToPlayer`. That is called only by
  the software sprite projector (`src/r_things.cpp:531-535`), the GL sprite path
  (`src/gl/scene/gl_sprite.cpp:509`) and GL dynamic lights attached to the actor
  (`src/gl/dynlights/gl_dynlight1.cpp:192`). So a hidden actor still collides, can be picked up by
  anyone, makes sounds, and runs its states. Only its sprite and its attached lights are hidden.

## Example

```decorate
// Stock TEAMINFO: index 0 is Blue, 1 is Red.
ACTOR BlueTeamMarker
{
    +NOBLOCKMAP
    +NOGRAVITY
    VisibleToTeam 0
    States
    {
    Spawn:
        BAR1 A -1
        Stop
    }
}
```

## Wiki/engine divergence

- **"255 means not on a team and is set by default."** The default is not 255. An omitted property
  stores 0, which means visible to all. 255 is the engine's "no team" number (`TEAM_None`,
  `src/teaminfo.h:38`), but writing `VisibleToTeam 255` stores 256, which matches no real team. In
  a team mode the actor then shows only to players who aren't on a team.
- The wiki's example is correct: index 1 is the second team, Red in the stock `TEAMINFO`, so
  index 0 is Blue.

## Engine-family divergence

UZDoom has the property with the same plus-one encoding (UZDoom source
`src/scripting/thingdef_properties.cpp:1142-1146`), and it also only feeds rendering and attached
dynamic lights. The visibility test differs (`src/playsim/p_mobj.cpp:1458-1491`):

- **Gate.** UZDoom applies the restriction whenever the `teamplay` cvar is on
  (`src/g_game.cpp:251`), rather than by game-mode flag.
- **Whose team.** UZDoom compares against the console player's own team setting, not the team of
  the player the camera is following. A spectator view of another player doesn't change what is
  shown.
- **Teamless players.** Zandronum's team modes have a real "not on a team" state, and such players
  see every restricted actor. On UZDoom, a player whose team setting is invalid when it changes
  under `teamplay` is put on a random team (`src/d_netinfo.cpp:475-482`), so in practice every
  player is filtered by team. A player still on the "no team" value 255 (the `team` userinfo
  default, `src/d_netinfo.cpp:52`) would not see a restricted actor.
- The stock `TEAMINFO` order starts Blue, Red on both engines, so indices carry over unchanged.

## See also

- [`LimitedToTeam`](limitedtoteam.md): same index encoding, restricts a player class to a team.
- [`VisibleToPlayerClass`](visibletoplayerclass.md): the per-player-class counterpart.
