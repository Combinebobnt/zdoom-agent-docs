# `VisibleToPlayerClass <classname> [, <classname> ...]` (actor property)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-22); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki `DECORATE` (https://wiki.zandronum.com/w/index.php?title=DECORATE&oldid=2445, retrieved 2026-09-22) + verified against the Zandronum source at the 3.3-alpha checkout (line numbers below are at bdd0f7beb): `src/thingdef/thingdef_properties.cpp:79-96` and `:1402-1411`, `src/info.h:276`, `src/thingdef/thingdef.cpp:149-152` and `:290-320` (`FinishThingdef`), `src/p_mobj.cpp:1283-1315` (`AActor::IsVisibleToPlayer`), `src/r_things.cpp:531-535`, `src/gl/scene/gl_sprite.cpp:509`, `src/gl/dynlights/gl_dynlight1.cpp:192`; and the UZDoom source's `src/scripting/thingdef_properties.cpp:1151-1160`, `src/playsim/p_mobj.cpp:1458-1491`, `src/gamedata/info.h:259,276`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_PROPERTY(visibletoplayerclass, Ssssssssssssssssssss, Actor)` in `src/thingdef/thingdef_properties.cpp:1402`, stored as a class list on the actor's `FActorInfo` (`src/info.h:276`), not on each actor instance.

Hides an actor from the local view unless the viewed player's class is one of the listed classes
or a subclass of one. It only affects drawing, not gameplay.

## Arguments (Zandronum)

- **Up to 20 class names.** The parameter spec `Ssssssssssssssssssss` is one required string
  plus 19 optional ones, so the wiki's single `classname` can be a list of up to 20.
- **Resolved at load time** through the `FindClassTentative` helper with `PlayerPawn` as the
  required ancestor (`thingdef_properties.cpp:79-96`, `:1409`):
  - An empty string is skipped (`:1408`), and `"none"` adds a null entry that never matches.
  - A name that exists but doesn't inherit from `PlayerPawn` is a fatal error ("does not inherit
    from PlayerPawn").
  - A name that is never defined anywhere fails at the end of DECORATE loading with "Class ...
    referenced but not defined" and a fatal error (`src/thingdef/thingdef.cpp:304`, `:320`).
- **Replaces, doesn't append.** Using the property clears the list first (`:1404`). A subclass
  inherits its parent's list unless it sets its own (`src/thingdef/thingdef.cpp:152`).

## Behavior (Zandronum)

- `AActor::IsVisibleToPlayer` (`src/p_mobj.cpp:1283-1315`) looks at the player the local
  **camera** is attached to. If the list is non-empty, the actor is drawn only when that player's
  pawn `IsDescendantOf` one of the listed classes (`:1297-1311`). Matching is by inheritance, not
  exact name: listing `DoomPlayer` also covers every class derived from it.
- If the camera isn't a player (or the player has no pawn), the class check is skipped and the
  actor is drawn.
- The team check for [`VisibleToTeam`](visibletoteam.md) runs first in the same function; an actor
  must pass both.
- **Rendering only, traced.** `IsVisibleToPlayer` is the list's only reader, and it is only
  called by the software sprite projector (`src/r_things.cpp:531-535`), the GL sprite path
  (`src/gl/scene/gl_sprite.cpp:509`) and GL dynamic lights attached to the actor
  (`src/gl/dynlights/gl_dynlight1.cpp:192`). A hidden actor still collides, can be picked up or
  used by any class, and runs its states.

## Example

```decorate
ACTOR ScoutPlayer : DoomPlayer
{
    Player.DisplayName "Scout"
}

ACTOR MedicPlayer : PlayerPawn
{
    Player.DisplayName "Medic"
}

// Drawn only for DoomPlayer and its subclasses (ScoutPlayer included), and for MedicPlayer.
ACTOR MarineHint
{
    +NOBLOCKMAP
    +NOGRAVITY
    VisibleToPlayerClass "DoomPlayer", "MedicPlayer"
    States
    {
    Spawn:
        BON1 A -1
        Stop
    }
}
```

## Wiki/engine divergence

The wiki describes a single class ("only visible for a certain class"). The source accepts up to
20, and a listed class also covers its subclasses.

## Engine-family divergence

UZDoom has the property with the same 20-string parameter spec, the same clear-then-fill list, and
the same per-class storage (UZDoom source `src/scripting/thingdef_properties.cpp:1151-1160`,
`src/gamedata/info.h:259`, inheritance copy at `:276`). Its visibility test in
`src/playsim/p_mobj.cpp:1458-1491` uses the same inheritance match against the camera's player, and
also shows the actor when the camera isn't a player. Two differences:

- **Looser name check.** UZDoom resolves each name with `Actor` as the required ancestor rather
  than `PlayerPawn` (`thingdef_properties.cpp:1158`). Naming a non-player class is not an error
  there; the entry only matches if the viewed pawn descends from it.
- **Team check.** The `VisibleToTeam` test that runs first in the same function behaves
  differently on UZDoom; see [`VisibleToTeam`](visibletoteam.md)'s divergence section.

## See also

- [`VisibleToTeam`](visibletoteam.md): the per-team counterpart.
- [`LimitedToTeam`](limitedtoteam.md): restricts a player class to a team.
- [Creating player classes](../concepts/creating-player-classes.md).
