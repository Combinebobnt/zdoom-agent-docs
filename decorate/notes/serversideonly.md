# `+SERVERSIDEONLY` (actor flag)

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki `DECORATE` (https://wiki.zandronum.com/w/index.php?title=DECORATE&oldid=2445, retrieved 2026-09-22) + verified against the Zandronum 3.3-alpha @bdd0f7beb source (line numbers below are at bdd0f7beb): `src/actor.h:472-475`, `src/p_mobj.cpp:386-393` and `:5054-5063` (net ID assignment), `src/p_mobj.cpp:6188-6193` (`P_SpawnMapThing`), `src/sv_commands.cpp` (`EnsureActorHasNetID` 99-112 and the per-command early returns listed below), `src/sv_main.cpp:2791-2794` (`SERVER_SendFullUpdate`).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_FLAG(NETFL, SERVERSIDEONLY, AActor, NetworkFlags)` in `src/thingdef/thingdef_data.cpp:282` (bit `NETFL_SERVERSIDEONLY` = `0x20`, `src/actor.h:475`).

Marks an actor as existing only on the server. Clients are never told about it, so it costs no
network traffic, and clients have no copy of it at all.

## How it works (Zandronum)

The flag works by denying the actor a network ID and then filtering it out of every server-to-client
spawn message:

- **No net ID.** `AActor::StaticSpawn` only assigns a net ID when neither `NONETID` nor
  `SERVERSIDEONLY` is set; otherwise `NetID` is 0 (`src/p_mobj.cpp:5054-5063`). The same check
  runs when a savegame is loaded (`:386-393`).
- **Spawn messages dropped.** With no net ID, `SERVERCOMMANDS_SpawnThing` falls through to the
  ID-less variant (`src/sv_commands.cpp:1441-1445`), and the ID-less variants return early for
  this flag: `SpawnThingNoNetID` (`:1468`), `SpawnThingExactNoNetID` (`:1509`),
  `LevelSpawnThingNoNetID` (`:1550`), `SpawnPuffNoNetID` (`:2331`). `SpawnMissile` and
  `SpawnMissileExact` check the flag directly (`:2824`, `:2858`).
- **Inventory not mirrored.** `GiveInventory`, `TakeInventory` and `GiveWeaponHolder` also return
  early for a flagged item (`src/sv_commands.cpp:3994`, `:4042`, `:4102`). A `SERVERSIDEONLY`
  inventory class never shows up in a client's copy of a player's inventory.
- **Not in join updates.** `SERVER_SendFullUpdate` skips every actor with `NetID` 0
  (`src/sv_main.cpp:2793`), so late joiners don't get it either.
- **Not spawned by clients.** Clients skip map things unless they are `ALLOWCLIENTSPAWN` or
  `CLIENTSIDEONLY` (`src/p_mobj.cpp:6188-6193`), so a map-placed `SERVERSIDEONLY` thing exists
  only on the server.
- **No warning spam.** Every later server command that needs the actor goes through
  `EnsureActorHasNetID`, which returns false for `NetID` 0. It prints the "doesn't have a netID"
  warning under `sv_showwarnings`, except for this flag (`src/sv_commands.cpp:99-112`).

## Gotchas

- **Invisible and non-solid are your job.** Nothing in the engine makes a `SERVERSIDEONLY` actor
  invisible or non-blocking. The comment on the bit (`src/actor.h:472-474`) says to use it only
  on actors that are always invisible and don't block players. A solid one still blocks on the
  server while clients have nothing there to predict against. The wiki gives the same warning.
- **The engine uses it itself.** `RandomSpawner` sets it on itself on the server and frees its net
  ID, since only the spawned result matters to clients (`src/g_shared/a_randomspawner.cpp:60-65`).

## Engine-family divergence

UZDoom has no client/server actor split. It registers the name as
`DEFINE_DUMMY_FLAG(SERVERSIDEONLY, false)` (UZDoom source `src/scripting/thingdef_data.cpp:459`).
A dummy entry has no storage offset, so the DECORATE parser hands it to the deprecated-flag handler
(`src/scripting/decorate/thingdef_parse.cpp:460-462`), whose default case does nothing
(`src/scripting/thingdef_properties.cpp:343`). `+SERVERSIDEONLY` parses silently on UZDoom and has
no effect.

## See also

- [`+CLIENTSIDEONLY`](clientsideonly.md): the opposite, client-only actors.
- [`+NONETID`](nonetid.md): also suppresses the net ID, but the spawn is still sent to clients.
- [`+ALLOWCLIENTSPAWN`](allowclientspawn.md): clients spawn a map thing themselves.
