# `+NONETID` (actor flag)

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki `DECORATE` (https://wiki.zandronum.com/w/index.php?title=DECORATE&oldid=2445, retrieved 2026-09-22) + verified against the Zandronum source at the 3.3-alpha checkout (line numbers below are at bdd0f7beb): `src/p_mobj.cpp:386-393` and `:5054-5063` (net ID assignment), `src/sv_commands.cpp` (`EnsureActorHasNetID` 99-112, `SERVERCOMMANDS_SpawnThing`/`SpawnThingNoNetID` 1435-1477), `src/cl_main.cpp:5174-5177`, `src/network.cpp:1598-1605`, `src/sv_main.cpp:2791-2794`, `src/p_mobj.cpp:6338-6352` and `:6390-6432` (`P_SpawnPuff`), `:6465-6524` (`P_SpawnPuffForClients`), `src/d_netinfo.cpp:103,115-126`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_FLAG(NETFL, NONETID, AActor, NetworkFlags)` in `src/thingdef/thingdef_data.cpp:279` (bit `NETFL_NONETID` = `0x01`, `src/actor.h:455`).

The actor is spawned without a network ID. The net ID is what the server uses to refer to an actor
in every message after its spawn, so the server can announce the spawn but can't sync anything
about the actor afterward.

## How it works (Zandronum)

- **No net ID.** `AActor::StaticSpawn` skips assignment for `NONETID` (and `SERVERSIDEONLY`)
  actors and leaves `NetID` at 0 (`src/p_mobj.cpp:5054-5063`). The same check runs when a
  savegame is loaded (`:386-393`).
- **The spawn is still sent.** Unlike `SERVERSIDEONLY`, the actor isn't hidden from clients.
  `SERVERCOMMANDS_SpawnThing` sends an ID-less spawn message instead
  (`src/sv_commands.cpp:1441-1445`), and the client spawns its copy with `NetID` 0
  (`src/cl_main.cpp:5174-5177`).
- **Nothing after the spawn is sent.** Server commands that act on an existing actor go through
  `EnsureActorHasNetID`, which returns false for `NetID` 0 (`src/sv_commands.cpp:99-112`;
  48 call sites in that file). With `sv_showwarnings` on, the server prints "doesn't have a netID
  and therefore can't be manipulated online".
- **Clients run it themselves.** An actor with `NetID` 0 counts as client-handled
  (`src/network.cpp:1604`), the same as `CLIENTSIDEONLY`. Action functions that normally return
  early on clients (`A_FadeOut`, `A_SetScale`, `A_ChangeVelocity`, `A_Warp` and others) run on the
  client's copy instead.
- **Late joiners never see it.** `SERVER_SendFullUpdate` skips every actor with `NetID` 0
  (`src/sv_main.cpp:2791-2794`).

## Bullet puffs

Apart from spawning, the only other engine code that reads the flag is client-predicted bullet
puffs:

- A client only predicts a puff locally if the puff type is `NONETID` (`src/p_mobj.cpp:6338-6352`).
- When the server spawns such a puff for a player's attack, it skips sending it to the shooter if
  that player has `cl_clientsidepuffs` on (`src/p_mobj.cpp:6496-6516`). Everyone else still gets
  it.
- That skip only happens on the plain path. A puff that has a `SeeSound` and hit an actor, has an
  `AttackSound`, or is temporary with an obituary gets a net ID from the server despite
  `NONETID`, and is sent to every client including the shooter (`src/p_mobj.cpp:6477-6490`). A puff
  the server put into its `Crash`, `XDeath` or `Melee` state is also sent to every client, without a
  net ID (`src/p_mobj.cpp:6390-6428`, `:6473-6476`).
- `cl_clientsidepuffs` (`src/d_netinfo.cpp:103`) is forced off when unlagged is off
  (`src/d_netinfo.cpp:115-126`).

## Gotchas

- **Fire-and-forget only.** The flag suits actors whose whole behavior plays out from their own
  state machine after spawning: puffs, sparks, short effects. If the server later damages, moves,
  changes the state of, or removes the actor, clients aren't told, and each client's copy just
  keeps running on its own. The wiki's "Only use this if you know what you are doing!" warning is
  about this.

## Engine-family divergence

UZDoom has no client/server actor split. It registers the name as
`DEFINE_DUMMY_FLAG(NONETID, false)` (UZDoom source `src/scripting/thingdef_data.cpp:456`). A dummy
entry has no storage offset, so the DECORATE parser hands it to the deprecated-flag handler
(`src/scripting/decorate/thingdef_parse.cpp:460-462`), whose default case does nothing
(`src/scripting/thingdef_properties.cpp:343`). `+NONETID` parses silently on UZDoom and has no
effect.

## See also

- [`+SERVERSIDEONLY`](serversideonly.md): also leaves the net ID at 0, but the spawn is never sent.
- [`+CLIENTSIDEONLY`](clientsideonly.md): the other way to make an actor client-handled.
- [`+ALLOWCLIENTSPAWN`](allowclientspawn.md): clients spawn a map thing themselves.
