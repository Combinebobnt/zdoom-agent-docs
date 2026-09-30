# `cl_hitscandecalhack` (cvar)

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-29)
**Provenance:** written from the Zandronum source's `src/cl_main.cpp:10034` (declaration),
`src/p_map.cpp:4188-4198`, `:4318-4336`, `:4338-4367`, `:4385-4399`, `:4425-4441`, `:4452-4517` (`P_LineAttack`),
`src/g_doom/a_doomweaps.cpp:112-117`, `:354-359`, `:426-431`, `:603-636` (stock Doom weapons),
`src/thingdef/thingdef_codeptr.cpp:1554-1629` (`A_CustomFireBullets`) and `:1680-1694`
(`A_FireBullets`), `src/sv_commands.cpp:5283` and `:2966-2978` (the server's decal commands), `src/d_netinfo.cpp:103` (`cl_clientsidepuffs`), and
`docs/Skulltag Version History.txt:1282`; no wiki page was used.

A Zandronum client option that lets the client draw bullet decals for its own hitscan shots.
Default `true`, `CVAR_ARCHIVE`, client-side only (no effect on a server or offline).

## Why it exists

The server never sends hitscan (bullet) decals to clients. The only decals it has clients draw
are ACS `SpawnDecal`'s (`sv_commands.cpp:5283`, see
[the spawning family](../../acs/families/spawning.md)) and rail wall hits (the railgun command,
`:2966-2978`). So a client only ever sees a bullet decal it traced itself. With this cvar on, a client that runs a hitscan
firing function doesn't stop at "the server handles weapons" but runs the attack trace locally,
only to place the decals. Damage, puffs (unless predicted, below) and everything else still come
from the server.

## What turning it off skips

With `cl_hitscandecalhack 0`, the client skips:

- **Wall decals from hitscan shots** (`p_map.cpp:4334`), the bullet marks on walls.
- **Blood decals from hitscan hits on actors** (`p_map.cpp:4440`): the blood that `P_TraceBleed`
  sticks to walls behind a hit monster or player (`:4514-4516`). The blood actors themselves,
  including `BloodSplatter` ones, are spawned by the server either way (`:4481-4486`, `:4494`).

If `cl_clientsidepuffs` is also off, the client doesn't trace the attack at all
(`p_map.cpp:4192-4198`). If `cl_clientsidepuffs` is on, the client still traces to spawn its
predicted puffs, then stops before the decal code.

## Which weapons it affects

Player hitscan weapons that fire through `A_CustomFireBullets`, whose client gate is where this
cvar is read for them (`thingdef_codeptr.cpp:1620-1629`):

- The stock Doom pistol, shotgun, super shotgun and chaingun. Zandronum's `A_FirePistol`,
  `A_FireShotgun`, `A_FireShotgun2` and `A_FireCGun` just call `A_CustomFireBullets`
  (`a_doomweaps.cpp:115`, `:357`, `:429`, `:634`); their older bodies, with their own client
  checks, are commented out.
- DECORATE `A_FireBullets` (`thingdef_codeptr.cpp:1693`), so any custom weapon built on it.

Other callers of `P_LineAttack` on a client weren't traced here.

A client-side decal is traced from the client's own copy of the shot, so it need not sit exactly
where the server's shot hit. With `cl_clientsidepuffs` off, the client has no puff actor
either, which changes which decal a `FORCEDECAL` puff gets: see
[`FORCEDECAL`](../../decorate/notes/forcedecal.md).

The code dates from Skulltag (`Skulltag Version History.txt:1282`), well before the 3.2.1 version
bump, so this holds on 3.2.1.

## Engine-family divergence

UZDoom has no such cvar. Its multiplayer runs the whole game on every machine, so each one draws
every hitscan decal itself. The related `cl_maxdecals`, `cl_bloodsplats` and `cl_missiledecals` exist on
both engines; see [`cl_maxdecals`](cl_maxdecals.md).
