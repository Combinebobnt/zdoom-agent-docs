# `+BUMPSPECIAL` (actor flag)

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-22); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** engine source only. Zandronum, re-read and re-cited at the 3.3-alpha checkout @bdd0f7beb: `src/actor.h:312,375,607-619`, `src/thingdef/thingdef_data.cpp:219`, `src/p_map.cpp:1014-1025` (the commented-out modern block), `:1340-1383` (`PIT_CheckThing`'s live bump block), `:7087-7141` (`P_ActivateThingSpecial`), `src/p_mobj.cpp:4435-4456` (standing on top). UZDoom: `src/playsim/actor.h:328`, `src/scripting/thingdef_data.cpp:254`, `src/playsim/p_map.cpp:1472-1509` (`PIT_CheckThing`), `:7233-7288` (`P_ActivateThingSpecial`), `src/playsim/p_mobj.cpp:5009-5025` (standing on top).
**Bucket:** `DEFINE_FLAG(MF6, BUMPSPECIAL, AActor, flags6)` on both engines (`MF6_BUMPSPECIAL` = `0x20`).

Runs the actor's own `special` (with its `args[0..4]`) when another actor collides with it. It
started as a Skulltag flag. ZDoom later adopted it with a different trigger model, and Zandronum
kept Skulltag's version for sideways bumps. So the two engines disagree on who can trigger it,
how often, and whether `activationtype` applies.

There are two trigger paths on each engine: bumping into the actor sideways (`PIT_CheckThing`),
and standing on top of it (the z-movement code in `AActor::Tick`, reached only when the mover has
`+PASSMOBJ` or `+SPECIAL`). They only differ on the sideways path.

## Standing on top (both engines)

Near-identical code on both. The special fires every tic the mover rests on the actor, rate-limited by
`lastbump` to once per second (`TICRATE` tics). The mover must be a player, or a monster when
`activationtype` has `THINGSPEC_MonsterTrigger`, or a missile when it has
`THINGSPEC_MissileTrigger`. The call goes through `P_ActivateThingSpecial`, so every
`activationtype` bit applies: who the activator is (`ThingActs`/`TriggerActs`), target swaps,
`ClearSpecial`, and the `Activate`/`Deactivate`/`Switch` state toggling. The one-second cooldown
only starts when `P_ActivateThingSpecial` reports success. The one code difference: UZDoom skips
the call while a player's movement is only being predicted, and Zandronum has that guard
commented out. Whether a Zandronum client then runs the special itself wasn't traced.

## Sideways bump on UZDoom

The same model as standing on top: player (or monster/missile per `activationtype`), one-second
`lastbump` cooldown, dispatched through `P_ActivateThingSpecial`. The actor doesn't need
`+SOLID`: any of `+SOLID`, `+SPECIAL`, `+SHOOTABLE` or `+TOUCHY` gets it past `PIT_CheckThing`'s early
"can't hit" filter, and the bump check itself tests neither actor's solidity. It is skipped while
a player's movement is only being predicted. An overridden `CanCollideWith` returning false also
suppresses it.

## Sideways bump on Zandronum: the older Skulltag form

Zandronum has the modern block above in its source, but commented out with the note that it
"keeps Skulltag's BUMPSPECIAL implementation for now" (`p_map.cpp:1014-1025`). The live code
at the end of `PIT_CheckThing` (`:1358-1383`) behaves differently:

- **Both actors must be solid.** The bumped actor needs `+SOLID` and no `+NOCLIP`. The bumper
  needs `+SOLID` or `+BLOCKEDBYSOLIDACTORS`. A non-solid `BUMPSPECIAL` actor never fires from a
  sideways bump (only from standing on top).
- **Any such bumper triggers it**, not only players. A walking monster fires the special with no
  `activationtype` bit needed. Ordinary missiles aren't solid, so they don't.
- **No cooldown.** `lastbump` is neither checked nor set. The special fires on every movement
  check that touches the actor, so a player pushing against it fires it about once per tic.
  Make the special idempotent, or have the script it runs guard against re-entry.
- **`activationtype` is ignored.** The special is called directly with the bumper as activator
  and no line. `ThingActs`, target swapping, `ClearSpecial` and the `Activate`/`Deactivate`/
  `Switch` toggling don't happen.
- **Server/offline only.** The block is skipped in client mode.

The same block also handles Skulltag score pillars before running the special. See
[`+SCOREPILLAR`](scorepillar.md).

## Engine-family divergence

Only the sideways path differs, as described above. A map or mod that relies on the UZDoom
behavior (a monster-proof trigger, a once-per-second rate limit, `THINGSPEC_Switch` toggling, a
shootable but non-solid trigger actor) behaves differently on Zandronum when the actor is bumped from the side,
and the reverse holds for a Zandronum mod that relies on monsters triggering it.

## See also

- [`SwitchableDecoration`](../classes/switchabledecoration.md): how the `Activate`/`Deactivate`
  bits gate `P_ActivateThingSpecial`.
- [Team items](../families/team-items.md): score pillars, the main Zandronum consumer.
