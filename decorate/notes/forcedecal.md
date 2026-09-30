# `FORCEDECAL` (actor flag)

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-29); Zandronum 3.3-alpha @bdd0f7beb (2026-09-29)
**Provenance:** written from the UZDoom source's `src/playsim/p_map.cpp:4838-4865` (`P_LineAttack`
decal choice) and `:5570-5585` (`P_RailAttack`), and commit `057b746e58` ("The rail attack only
considered the puff's decal if it had ALWAYSPUFF set", 2019-01-19, an ancestor of the checkout);
the Zandronum source's `src/p_map.cpp:4338-4367` (`P_LineAttack`), `:4983-5007` (`P_RailAttack`)
and `:5055-5063` (the railgun server command), `src/sv_commands.cpp:2966-2978`
(`SERVERCOMMANDS_WeaponRailgun`), `src/cl_main.cpp:6709-6727` (its client handler),
`src/p_map.cpp:5147-5170` (`P_SpawnDecalFromRailAttack`), `src/unlagged.cpp:368-382`
(`UNLAGGED_DrawRailClientside`) and `src/thingdef/thingdef_codeptr.cpp:1961-1965` (`A_RailAttack`
running on the shooter's client); no wiki page was used.
**Bucket:** `DEFINE_FLAG(MF7, FORCEDECAL, AActor, flags7)`: Zandronum
`src/thingdef/thingdef_data.cpp:250`, UZDoom `src/scripting/thingdef_data.cpp:292`.

A puff flag. When a hitscan or rail attack hits a wall, the decal normally comes from the
shooter (its `Decal` property, or for a player the ready weapon's). `FORCEDECAL` on the puff class
makes the puff's own `Decal` win instead. It has no effect unless the puff class has a `Decal`
set.

## Hitscan attacks

Both engines: the puff's decal replaces the shooter's or weapon's only if the puff actor was
actually spawned (UZDoom `p_map.cpp:4845-4850`, Zandronum `p_map.cpp:4341-4349`). If neither the
shooter nor its weapon has a decal, the puff's decal is used anyway, with or without the flag.
So the flag only matters when the weapon or monster already has a `Decal`.

**Zandronum client caveat.** A client that draws its own hitscan decals (see
[`cl_hitscandecalhack`](../../console/notes/cl_hitscandecalhack.md)) spawns no puff unless it
predicts puffs (`cl_clientsidepuffs`). Without a puff, `FORCEDECAL` is ignored there and that
client shows the weapon's decal, while a client that predicts puffs shows the puff's.

## Rail attacks: `ALWAYSPUFF` matters on Zandronum only

For a rail, the flag is the **only** way to get the puff's decal: without it, a rail always uses
the shooter's decal, even when the shooter has none and the puff has one.

- **UZDoom** reads the puff class's defaults, so `FORCEDECAL` plus a puff `Decal` is enough
  (`p_map.cpp:5581-5584`). Before commit `057b746e58` (2019) it also needed `ALWAYSPUFF`.
- **Zandronum** still has the pre-2019 check: it uses the puff's decal only if a puff actor was
  spawned, and a rail spawns one on a wall hit only with `ALWAYSPUFF` (`p_map.cpp:4987`, `:5004`).
  So offline, and in the server's own world, a `FORCEDECAL` rail puff without `ALWAYSPUFF` leaves
  the shooter's decal.

Online, Zandronum is inconsistent without `ALWAYSPUFF`. The server tells other clients to use the
puff's decal whenever the puff class has `FORCEDECAL` and a `Decal`, without checking `ALWAYSPUFF`
(`sv_commands.cpp:2966-2978`). But a shooter with unlagged on draws their own rail locally and is
left out of that command (`p_map.cpp:5060-5062`, `unlagged.cpp:368-382`); their local trace takes
the `ALWAYSPUFF` path above. So without `ALWAYSPUFF` the shooter sees the shooter's decal and
everyone else sees the puff's. Observed live (2026-09-29, local test build, server + 2 clients,
probe map): the shooting client saw the weapon's decal and the other client the puff's. With
`cl_unlagged 0` on the shooter, the shooter saw the puff's decal too, and adding `ALWAYSPUFF`
gave both clients the puff's decal.

**For a rail puff whose decal should show on both engines, set both `FORCEDECAL` and
`ALWAYSPUFF`.** The cost is that the puff actor then really spawns at the wall on every rail hit,
so give it a harmless or invisible spawn state if it shouldn't be seen.
