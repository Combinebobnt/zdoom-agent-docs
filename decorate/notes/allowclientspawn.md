# `+ALLOWCLIENTSPAWN` (actor flag)

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki `DECORATE` (https://wiki.zandronum.com/w/index.php?title=DECORATE&oldid=2445, retrieved 2026-09-22) + verified against the Zandronum source at the 3.3-alpha checkout: `src/actor.h:457-459`, `src/p_mobj.cpp:6187-6193` (`P_SpawnMapThing`), `src/p_mobj.cpp:5054-5063` (net ID assignment), `src/sv_main.cpp:2791-2808` (`SERVER_SendFullUpdate`), `src/g_game.cpp:3445-3450` (`GAME_ResetMap`), `src/p_mobj.cpp:5724-5735` (`P_SpawnPlayer` telefog). These are the flag's only readers.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_FLAG(NETFL, ALLOWCLIENTSPAWN, AActor, NetworkFlags)` in `src/thingdef/thingdef_data.cpp:280` (bit `NETFL_ALLOWCLIENTSPAWN` = `0x02`, `src/actor.h:459`).

Lets clients spawn a map-placed copy of the actor themselves at map load, instead of waiting for
the server to tell them about it. The server spawns its own copy as usual. The two copies are not
linked.

## How it works (Zandronum)

- **Map things only.** Clients normally skip every map thing and wait for the server. They make an
  exception for `ALLOWCLIENTSPAWN` (and `CLIENTSIDEONLY`) types (`src/p_mobj.cpp:6187-6193`). No
  other spawn path reads the flag, which matches the wiki's "only works for things on the map
  startup".
- **The server still spawns it.** Unlike `CLIENTSIDEONLY`, the server does not skip the type. Its
  copy gets a net ID like any other actor (`src/p_mobj.cpp:5054-5063`). The client's own copy is
  spawned in client mode, so its `NetID` is 0 (same lines). Nothing ties one to the other.
- **Skipped in join updates.** `SERVER_SendFullUpdate` doesn't send `ALLOWCLIENTSPAWN` actors to a
  joining client, on the assumption that the client already spawned them from the map
  (`src/sv_main.cpp:2801-2808`).
- **Map reset.** On a client, `GAME_ResetMap` restores the `args` of every map-spawned
  `ALLOWCLIENTSPAWN` actor. The source comment says these actors are "supposed to stay untouched"
  and that some mods change them anyway, notably for dynamic-light tricks
  (`src/g_game.cpp:3445-3450`).

## Gotchas

- **Treat the actor as static.** Because the server's copy and each client's copy are unlinked,
  server-side changes to the actor (state, position, args, removal) have no defined path to the
  client's copy. The engine's own telefog use confirms the pattern: when the server gives the
  player-spawn telefog this flag, it also frees the fog's net ID. The comment explains that
  otherwise the server would think it could notify clients about changes to the fog
  (`src/p_mobj.cpp:5724-5735`).
- **Late joiners miss mid-game spawns.** The join-update skip has no check for `STFL_LEVELSPAWNED`.
  If an actor of this type is spawned mid-game, currently connected clients get the normal spawn
  message, but a client joining later never receives it (`src/sv_main.cpp:2801-2808`).

## Engine-family divergence

UZDoom has no client/server actor split. It registers the name as
`DEFINE_DUMMY_FLAG(ALLOWCLIENTSPAWN, false)` (UZDoom source `src/scripting/thingdef_data.cpp:457`).
A dummy entry has no storage offset, so the DECORATE parser hands it to the deprecated-flag handler
(`src/scripting/decorate/thingdef_parse.cpp:460-462`), whose default case does nothing
(`src/scripting/thingdef_properties.cpp:343`). `+ALLOWCLIENTSPAWN` parses silently on UZDoom and
has no effect.

## See also

- [`+CLIENTSIDEONLY`](clientsideonly.md): the server skips the actor entirely.
- [`+SERVERSIDEONLY`](serversideonly.md): clients never get the actor.
- [`+NONETID`](nonetid.md): an actor spawned without a net ID.
