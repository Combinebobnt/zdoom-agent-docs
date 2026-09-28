# `DropItem "<class>" [probability] [amount]`

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-22); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** engine source only. Zandronum: `src/thingdef/thingdef_properties.cpp:761-790`
(parsing), `src/thingdef/thingdef.cpp:233-246` and `src/p_mobj.cpp:7910-7919,8036-8039` (storage),
and every `GetDropItems()` call site: `src/g_shared/a_action.cpp:113-122`, `src/p_enemy.cpp:3471,3513`,
`src/g_shared/a_randomspawner.cpp:76-115`, `src/g_doom/a_bossbrain.cpp:235-262`,
`src/g_shared/a_weapons.cpp:922-927`, `src/p_user.cpp:1667,1746-1753,2095-2104`,
`src/g_shared/st_hud.cpp:620-638`, `src/invasion.cpp:269-305,462-498,605-641`. All Zandronum line
numbers above are at the 3.3-alpha `bdd0f7beb` checkout read for this entry. UZDoom: only the
parse site, `src/scripting/thingdef_properties.cpp:714-743`.
**Bucket:** `DEFINE_PROPERTY(dropitem, S_i_i, Actor)` in `src/thingdef/thingdef_properties.cpp`.

Appends one entry to the class's drop-item list. `probability` defaults to 255 and `amount` to -1
when omitted. Neither is clamped at parse time. The general "monster drops this on death" meaning,
including why 255 and 256 both mean "always", is in
[Creating monsters](../concepts/creating-monsters.md). This note covers what the *other* consumers
of the same list do with the two numbers, because they disagree.

## One list, many readers

The list is class metadata, not a per-actor field. A class with no `DropItem` lines inherits its
parent's list, and one with any `DropItem` line replaces it outright (see
[Invasion spawn spots](../families/invasion-spots.md#how-a-spot-picks-its-class) for the inheritance
trace). `Player.StartItem` writes into the same list with a default amount of 1, so on a
`PlayerPawn` the two properties are one list.

Each line is **prepended** (`di->Next = bag.DropItemList`, on both engines), so the stored list runs
in reverse declaration order: its head is the *last* `DropItem` line. That only matters to readers
that take the head alone (`WeaponGiver`, below).

What each reader does with `probability` and `amount` (Zandronum, read at the 3.3-alpha checkout):

| Reader | `probability` | `amount` |
|---|---|---|
| Death drops (`A_NoBlocking`/`A_Fall`, via `P_DropItem`) | Per-entry roll, dropped if `pr_dropitem() <= probability`. | Passed to `ModifyDropAmount` (`p_enemy.cpp:3408-3453`). Positive sets the amount, except ammo on a skill without `DropAmmoFactor` gets it halved. 0 or -1: ammo gets `Ammo.DropAmount`, else its amount times the skill factor (default 1/2); a weapon's `AmmoGive1/2` are scaled the same way; other items keep their default. |
| Player death weapon drop (`DropItem` on the ready weapon, `p_user.cpp:2095-2104`) | Same `P_DropItem` roll. | Same. |
| [`RandomSpawner`](../classes/randomspawner.md) | One roll *after* the pick; a failed roll spawns nothing. | **Weight** of the entry. -1 is rewritten to 1. |
| Boss-brain cube (`A_SpawnFly`, list on the cube or else its master) | Ignored. | **Weight**, -1 rewritten to 1, same as `RandomSpawner`. |
| `WeaponGiver` pickup | Ignored. | Ignored. Only the head entry (the last-declared line) is used. |
| `PlayerPawn` start items | Ignored. | Starting amount; see `Player.StartItem`. |
| `Custom*InvasionSpot` (Zandronum only) | **Ignored.** | **Ignored.** Pick is uniform over non-`None` entries. |
| Zandronum's `cl_identifymonsters` target HUD | Shown as a percentage when `< 255`; an entry below 0 is hidden. | Not shown. |

## Invasion spots ignore both numbers

A modder used to `RandomSpawner` will write weighted lists for an invasion spot, and they do nothing.
`CustomMonsterInvasionSpot`, `CustomPickupInvasionSpot` and `CustomWeaponInvasionSpot` each count
the entries whose name isn't `None` and take `M_Random() % count`, so every listed class is equally
likely whatever its probability or amount. There is no roll that can make a spot spawn nothing.

To bias an invasion spot, repeat the line: two `DropItem "DoomImp"` lines and one
`DropItem "ZombieMan"` give a 2:1 split (follows from the uniform pick, not tested). There is no
way to make a spot occasionally spawn nothing: neither number helps, and a `None` entry is skipped
by the count. Listing a `RandomSpawner` class instead is not a clean workaround. The spot attaches
its bookkeeping to the spawner actor, not to what the spawner turns into, so a pickup spot's
respawn and a monster spot's wave count and corpse cleanup lose track of the result (inferred from
the back-pointer handling in the family doc; not tested).

The full spot behavior, including the fatal error on an empty list and the re-roll hazards, is in
[Invasion spawn spots](../families/invasion-spots.md).

## Engine-family divergence

UZDoom parses `DropItem` identically (same defaults, same prepend), but has no invasion spots, no
`cl_identifymonsters` HUD, and its other readers were not re-traced for this note. Don't assume the
Zandronum table above holds row for row on UZDoom.
