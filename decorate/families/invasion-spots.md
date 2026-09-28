# Invasion spawn spots

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** engine source only. The Zandronum source's `wadsrc/static/actors/shared/sharedmisc.txt:178-215` (DECORATE declarations), `src/invasion.h:78-128` (native class layouts), `src/invasion.cpp` (the whole spot implementation at 136-644, `INVASION_Tick` at 656, `INVASION_StartCountdown` corpse cleanup at 821-910, `INVASION_BeginWave` at 914-1207, `INVASION_UpdateMonsterCount` at 1477, `INVASION_IsMapThingInvasionSpot` at 1514-1531, `invasion_GetNumThingsThisWave` at 1537-1561), `src/actor.h:1163-1164` (spawned-actor back-pointers), `src/g_shared/a_pickups.cpp:1227-1230` (`AInventory::Touch` pickup callback), `src/thingdef/thingdef_properties.cpp:765-790` (`DropItem` property), `src/thingdef/thingdef.cpp:233-246` (drop-item list storage), `src/dobjtype.cpp:307` (class meta inheritance), `src/cooperative.cpp:304-373` and `src/deathmatch.cpp:76-98` (game-mode cvar callbacks), `src/c_cvars.cpp:172-180` (`ForceSet`). Files that differ between 3.2.1 and the local 3.3-alpha checkout were originally read at 3.2.1: `src/p_setup.cpp:4401-4418`, `src/p_mobj.cpp:638-639,5097-5105,5913-5918,7910-7919`, `src/g_game.cpp:2860-3001`. Re-confirmed against the 3.3-alpha HEAD checkout on 2026-09-25; three of the `p_mobj.cpp` cites had shifted at HEAD and were corrected (638->638-639, 5100-5108->5097-5105, 5940-5945->5913-5918); the rest still land on the right code at HEAD. Stock spot counts from `wadsrc/static/actors/{doom,heretic,hexen,strife}/*spawners.txt` and `wadsrc_st/static/actors/skulltagspawners.txt`. UZDoom absence checked in the UZDoom source's `wadsrc/static/zscript` and `src`.
**Bucket:** native C++ classes. `ABaseMonsterInvasionSpot`, `ABasePickupInvasionSpot`, `ABaseWeaponInvasionSpot` declared in `src/invasion.h:78,96,115` (all parented directly on `AActor`); `ACustomMonsterInvasionSpot`, `ACustomPickupInvasionSpot`, `ACustomWeaponInvasionSpot` are file-local classes in `src/invasion.cpp:259,452,595` (each parented on its `Base*` class). DECORATE `native` declarations in `wadsrc/static/actors/shared/sharedmisc.txt:179,187,191,200,205,213`.
**Family rationale:** Shared implementation. Three `Base*` classes carry near-identical per-tick spawn logic driven by one wave controller (`INVASION_BeginWave`), and the three `Custom*` subclasses override only `GetSpawnName()` with the same copy-pasted `DropItem` picker.

Invisible map things that spawn monsters, pickups, or weapons each wave of Zandronum's Invasion game
mode. The engine drives every spot from `INVASION_BeginWave` plus the spot's own `Tick()`; the spot
only decides *what* to spawn through the virtual `GetSpawnName()`. The `Base*` classes return
nothing from it, so a modder always derives from a `Custom*` class and lists candidates with
`DropItem`. Behavior is controlled by the map thing's five `args[]`, so **monster and pickup spots
need Hexen-format or UDMF things**: Doom-format things carry no args, so `args[0]` is 0 and those
spots spawn nothing. Weapon spots ignore `args[0]`, so with all-zero args they still work: the
weapon appears at wave start, every wave (both inferred from the arg handling below, not a separate
code path).

All six classes share the same DECORATE defaults: `+NOBLOCKMAP`, `+NOSECTOR`, `+NOGRAVITY`,
`RenderStyle None`, no states, no doomednum.

## `BaseMonsterInvasionSpot`

Monster spawner. Only kind that counts toward the wave's monster total, supports the boss delay
(`args[2] == 255`), and runs a location check (`P_TestMobjLocation`) on each spawn: a blocked spawn
is destroyed, its kill/item count backed out, and retried next tic. `GetSpawnName()` returns
`NAME_None` (`invasion.cpp:136`). Ticks only in `IS_INPROGRESS` and `IS_BOSSFIGHT`.

## `CustomMonsterInvasionSpot`

`BaseMonsterInvasionSpot` with a `DropItem`-list picker (`invasion.cpp:269-305`). Base class of all
113 stock monster spots.

## `BasePickupInvasionSpot`

Item spawner with pickup-driven respawn (see "Pickup respawn" below). `GetSpawnName()` returns
`NAME_None` (`invasion.cpp:313`). Ticks in `IS_INPROGRESS`, `IS_BOSSFIGHT`, `IS_WAVECOMPLETE`, and
`IS_COUNTDOWN`, so items keep respawning between waves. On `Destroy()` it clears the `pPickupSpot`
back-pointer of every actor it spawned (`invasion.cpp:334-348`).

## `CustomPickupInvasionSpot`

`BasePickupInvasionSpot` with the `DropItem` picker (`invasion.cpp:462-498`). Base class of all 136
stock pickup spots.

## `BaseWeaponInvasionSpot`

One-shot weapon spawner (`invasion.cpp:506-592`). Spawns at most once per qualifying wave, never
respawns after pickup, and clears `MF_DROPPED` on the weapon so it isn't treated as a dropped item.
The code that would destroy the spot after spawning is commented out, so the spot persists and fires
again on the next qualifying wave. Ticks in the same four states as the pickup spot. Not location
checked, and it does not set any back-pointer on the spawned weapon.

## `CustomWeaponInvasionSpot`

`BaseWeaponInvasionSpot` with the `DropItem` picker (`invasion.cpp:605-641`). Base class of all 41
stock weapon spots.

## Map-thing arguments

The comment block at the top of `invasion.cpp:48-55` describes the args, but it is wrong about units:
it calls `args[1]`/`args[2]` tick counts, while every use multiplies them by `TICRATE`, so **both are
whole seconds**. The table is what the code does:

| Arg | Monster spot | Pickup spot | Weapon spot |
|---|---|---|---|
| `args[0]` | Count on the spot's first active wave; scaled up each wave (formula below). 0 = spawns nothing. | Same, pickup scaling factors. Counts spawns (respawns), not simultaneous items. | Ignored. |
| `args[1]` | Seconds between consecutive spawns in a wave. 0 = next spawn on the following tic. | Seconds from pickup to respawn. 0 is treated as 2 seconds. | Ignored. |
| `args[2]` | Delay in seconds from wave start before the first spawn, used when `> 0`. **255** = boss: waits until the monsters left in the wave are only boss monsters, then switches the state to `IS_BOSSFIGHT`. | Delay in seconds, but only honored when **`> 2`**. A value of 1 or 2 spawns immediately. No 255 special case. | Same as pickup: seconds, only when `> 2`. |
| `args[3]` | First wave the spot is active (`wave < args[3]` skips; 0 and 1 both mean wave 1). Scaling restarts from this wave. | Same as monster. | **Exact wave**: if non-zero, spawns only in wave `args[3]`; 0 = every wave. |
| `args[4]` | Per-wave cap on the scaled count; 0 = no cap. | Same as monster. | Ignored. |

**Wave scaling** (`invasion_GetNumThingsThisWave`, `invasion.cpp:1537-1561`): the count is
`args[0] * factor^(n - 1)`, truncated to an integer, where `n` is the wave number counted from the
spot's first wave (`wave - (args[3] - 1)` when `args[3] > 1`). The factor depends on the `gameskill`
cvar value:

| `gameskill` | Monster factor | Pickup factor |
|---|---|---|
| 0, 1 | 1.25 | 2 |
| 2, and any value outside 0-4 | 1.5 | 1.75 |
| 3, 4 | 1.6225 | 1.6225 |

Weapon spots don't scale.

## Map-thing flags

- **Dormant** (`MF2_DORMANT`). The native `Activate`/`Deactivate` overrides only toggle this flag, so
  `Thing_Activate`/`Thing_Deactivate` by TID (and the map thing's dormant flag) work on spots. It is
  **only read in `INVASION_BeginWave`**: a dormant spot is skipped for the whole wave. None of the
  `Tick()` overrides check it, so deactivating a spot mid-wave doesn't stop spawns already scheduled,
  and activating one mid-wave does nothing until the next wave starts. A level-spawned spot that is
  hidden instead of destroyed (`AActor::HideOrDestroyIfSafe`, used in game modes with map resets) is
also made dormant (`p_mobj.cpp:638-639`).
- **Ambush** (`MF_AMBUSH`). Suppresses the teleport fog normally spawned at the spot with each spawn.
- **Angle.** Copied onto every spawned actor.

## How a spot picks its class

`GetSpawnName()` is a native virtual on each `Base*` class, not something DECORATE can override. The
`Base*` versions return `NAME_None`. A DECORATE class inheriting straight from a `Base*` class
therefore passes `None` to `Spawn()`, which calls `I_Error("Attempt to spawn actor of unknown
type ...")` (`p_mobj.cpp:5097-5105`) the first time the spot fires (inferred from those two
code paths; not run).

The three `Custom*` overrides are identical:

- They walk the class's `DropItem` list, count entries whose name isn't `None`, and pick one with
  `M_Random() % count`. The pick is **uniform**: `DropItem`'s probability and amount arguments are
  parsed (`thingdef_properties.cpp:765-790`) but never read here.
- An empty list is a fatal `I_Error("Custom monster invasion spot has no defined monsters!")`. The
  pickup and weapon versions print the same monster wording.
- The list is class metadata (`thingdef.cpp:233-246`), and a derived class copies its parent's
  metadata (`PClass::CreateDerivedClass`, `dobjtype.cpp:307`). A subclass with no `DropItem` lines inherits the parent's list, and
  one that declares any `DropItem` replaces it entirely.
- An unknown class name in the list isn't caught at load. It reaches `Spawn()`, which `I_Error`s at
  the moment that entry happens to be rolled.
- Spawns use `ALLOW_REPLACE`, so a `replaces` on the listed class is honored.

**The picker is re-rolled on every call, and some paths call it more than once.**
`INVASION_BeginWave` calls `GetSpawnName()` on each active monster spot just to compare it against
`"Archvile"` (`invasion.cpp:991`) before separately calling it for the real spawn. For a mixed list,
the Arch-vile counter (replicated to clients; its consumer wasn't traced) can disagree with what spawned. The
pickup spot's `Tick()` and `PickedUp()` also call `GetSpawnName()` again for the ammo test described
below, so for a `CustomPickupInvasionSpot` mixing ammo and non-ammo entries, the ammo test can
examine a different class from the one actually spawned or picked up.

## Pickup respawn

1. At wave start the spot computes its count. If an actor still carrying `MF_SPECIAL` and pointing
   back at this spot (`pPickupSpot`) is resting in the world, the spot doesn't spawn another. This
   check only runs on the immediate-spawn path: with `args[2] > 2` the spot goes straight to its
   delay timer and spawns when it expires, whether or not the old item is still there.
2. After spawning, the spot waits indefinitely (`NextSpawnTick = -1`). It doesn't time out.
3. `AInventory::Touch` calls `pPickupSpot->PickedUp()` after a successful pickup
   (`a_pickups.cpp:1227-1230`). If spawns remain this wave, the next spawn is scheduled `args[1]`
   seconds later (2 seconds if `args[1]` is 0).
4. **Ammo is infinite on a server.** When `NETWORK_GetState() == NETSTATE_SERVER` and the spawn name
   resolves to an `Ammo` descendant, the remaining count isn't decremented and `PickedUp()` always
   reschedules. In offline single-player play ammo spots run out like any other pickup.

Only `Inventory` descendants reach `AInventory::Touch`, so a pickup spot whose list names a
non-inventory class spawns once and never again that wave (inferred from the single call site).

## Monster spots and the wave count

At wave start each active monster spot's count is added to the wave's monsters-left total. A spawn
whose actor doesn't count as a kill (for example a friendly monster) is subtracted again via
`INVASION_UpdateMonsterCount`, so such spots don't hold a wave open. Each spawned monster is tagged
with the current wave and a `pMonsterSpot` back-pointer. The countdown cleanup before the next wave
uses these to destroy corpses from the wave before the one just completed, and any dead monster
not spawned by a spot (`invasion.cpp:848-898`). Still-living hostile monsters are destroyed there too, as a desync guard
for buggy maps.

## Defining a custom spot

Derive from a `Custom*` class, give it a doomednum, and list candidates. The doomednum is what the
map editor places. Set the args on the placed thing.

```decorate
ACTOR MyWeakMonsterSpot : CustomMonsterInvasionSpot 21000
{
	DropItem "ZombieMan"
	DropItem "DoomImp"
}

ACTOR MyHealthSpot : CustomPickupInvasionSpot 21001
{
	DropItem "Stimpack"
	DropItem "Medikit"
}

ACTOR MyWeaponSpot : CustomWeaponInvasionSpot 21002
{
	DropItem "SuperShotgun"
}
```

A monster spot placed with args `4, 2, 0, 3, 10` spawns 4 monsters on wave 3 (its first active
wave), two seconds apart, growing by the skill factor each wave up to a cap of 10.

## Other game modes

Spots aren't removed outside Invasion. They are ordinary actors that also get catalogued as
"invasion starts" when spawned (`p_mobj.cpp:5913-5918`, which unlike the possession and
terminator starts just above it doesn't skip spawning the thing).

**A spot on the map switches the game to Invasion.** Before things are spawned, `P_SetupLevel`
checks whether any map thing resolves (after replacement) to a descendant of one of the three `Base*`
classes, and if `invasion` is off, force-sets it on (`p_setup.cpp:4401-4418` at 3.2.1, done early so
3D floors are handled). The `invasion` cvar callback forces `cooperative` on and `survival` off
(`cooperative.cpp:356-373`). `cooperative` then forces `deathmatch` and `teamgame` off. Afterwards
`GAME_CheckMode` (`g_game.cpp:2860-3001` at 3.2.1) re-derives the mode from the map's starts:

- **Deathmatch starts only:** forces `deathmatch` on, whose callback forces `cooperative` off, whose
  callback forces `invasion` off. The spots stay in the map but do nothing.
- **Team starts only:** forces `teamgame` on. Traced only as far as the branch itself; that
  `invasion` ends up off is inferred by analogy with the deathmatch chain.
- **Player starts only:** forces `deathmatch`/`teamgame` off and sets `invasion` to whether any
  spot was catalogued.
- **Mixed starts:** neither branch applies, so the mode forced during level setup (Invasion)
  stands (inferred from the absence of an override).

Survival cannot coexist with the spots (the `invasion` callback turns it off). When the final mode
isn't Invasion, `INVASION_Tick` returns immediately, the invasion state never leaves
`IS_WAITINGFORPLAYERS`, and every spot's `Tick()` returns before spawning. None of the spot `Tick()`
overrides call the parent `AActor::Tick`, so a spot never runs states or moves in any mode. States
given to a custom spot class have no effect.

## Netcode

Server-authoritative. Every spot `Tick()` and the spawning half of `INVASION_BeginWave` return early
under `NETWORK_InClientMode()`. Each spawned actor and teleport fog is sent to clients with
`SERVERCOMMANDS_SpawnThing`, and the monster count with `SERVERCOMMANDS_SetInvasionNumMonstersLeft`.
Clients never learn which spot spawned a monster (they tag spawned actors with the wave number
instead), so spot-dependent cleanup runs on the server only.

Savegames store each spot's `NextSpawnTick` and `NumLeftThisWave` (`Serialize` at
`invasion.cpp:248,417,585`) but not the monster spot's boss flag. A boss spot loaded mid-wave is
therefore not treated as a boss until the next `INVASION_BeginWave` sets the flag again (inferred
from the serialize list; not tested).

## Stock spots

Roughly 290 stock spots derive from the three `Custom*` classes: `wadsrc/static/actors/doom/doomspawners.txt`
(69), `heretic/hereticspawners.txt` (55), `hexen/hexenspawners.txt` (73),
`strife/strifespawners.txt` (77), all in the always-loaded `zandronum.pk3`, plus 16 in
`wadsrc_st/static/actors/skulltagspawners.txt`, which only exist when `skulltag_actors.pk3` is
loaded (see [Skulltag legacy actor classes](../concepts/skulltag-legacy-classes.md)). Those files
are the reference for which doomednum spawns which `DropItem` list.

## Engine-family divergence

Invasion mode and all six spot classes are Zandronum-only. The UZDoom source (checked at 5.1.0-pre
@98b16b78fc) has no `InvasionSpot` class and no occurrence of "invasion" at all under
`wadsrc/static/zscript` or `src`. A map using these doomednums loads on UZDoom with unknown things
where the spots were, and a mod inheriting from these classes fails to resolve its parent. Porting
a wave system means reimplementing it (in ZScript or ACS) on top of ordinary actors.

## See also

- [GetInvasionWave](../../acs/functions/getinvasionwave.md), [GetInvasionState](../../acs/functions/getinvasionstate.md): read the wave number and `IS_*` state the spots key off.
- [Thing_Activate](../../acs/functions/thing_activate.md), [Thing_Deactivate](../../acs/functions/thing_deactivate.md): toggle a spot's dormancy (takes effect at the next wave).
- `wavelimit`, `sv_invasioncountdowntime`, `sv_usemapsettingswavelimit` rows in [the console cvar inventory](../../console/inventory/cvars.md).
- [Skulltag legacy actor classes](../concepts/skulltag-legacy-classes.md): which stock spots are always available.
- [DropItem](../notes/dropitem.md): how the spot's uniform pick compares with every other reader of the same list.
