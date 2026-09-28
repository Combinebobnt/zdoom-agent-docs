# `+CLIENTSIDEONLY` (actor flag)

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki `DECORATE` (https://wiki.zandronum.com/w/index.php?title=DECORATE&oldid=2445, retrieved 2026-09-22) + verified against the Zandronum source at the Zandronum 3.3-alpha @bdd0f7beb checkout: `src/actor.h:467-470`, `src/p_mobj.cpp:6187-6199` (`P_SpawnMapThing`), `src/thingdef/thingdef_codeptr.cpp:105-124` (`NETWORK_ShouldActorNotBeSpawned`) and its callers, `src/p_acs.cpp:4193-4212` (`DLevelScript::DoSpawn`), `src/sv_main.cpp:5653-5668` (`SERVER_DestroyActorIfClientsidedOnly`), `src/network.cpp:1598-1605` (`NETWORK_IsActorClientHandled`), `src/g_game.cpp:3428-3442` (`GAME_ResetMap`).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_FLAG(NETFL, CLIENTSIDEONLY, AActor, NetworkFlags)` in `src/thingdef/thingdef_data.cpp:281` (bit `NETFL_CLIENTSIDEONLY` = `0x10`, `src/actor.h:470`).

Marks an actor as existing only on clients. The server never keeps a copy; each client spawns and
simulates its own, unsynchronized with the other clients. The engine's own comment on the bit
(`src/actor.h:467-469`) says to use it only on actors that don't affect the game apart from
visuals.

## How the spawn paths treat it (Zandronum)

There are three distinct paths, and they don't all work the same way:

- **Map things.** `P_SpawnMapThing` returns without spawning on the server for a
  `CLIENTSIDEONLY` type (`src/p_mobj.cpp:6195-6199`). Clients, which normally skip map things and
  wait for the server, spawn this one themselves (`src/p_mobj.cpp:6187-6193`).
- **Action-function spawns.** `A_CustomMissile`, `A_FireCustomMissile`, `A_SpawnItem`,
  `A_SpawnItemEx` and `A_SpawnDebris` all consult `NETWORK_ShouldActorNotBeSpawned`
  (`thingdef_codeptr.cpp:1175`, `:1762`, `:2554`, `:2648`, `:3232`). The spawn counts as
  client-side if the spawned type has this flag, if the **spawner** has it, or (for
  `A_SpawnItemEx`) if `SIXF_CLIENTSIDE` is passed (`:111-114`). A client-side spawn is skipped on
  the server and performed by each client whose copy of the spawner runs that state; a
  non-client-side spawn is skipped on clients (`:116-122`). So a normal, server-synced monster can
  spawn a `CLIENTSIDEONLY` effect, and the server never sees it. Anything a client spawns this way
  gets the flag set on the new actor (for example `:2579` in `A_SpawnItem`).
- **ACS `Spawn`/`SpawnSpot` and the `summon` cheat.** These paths do run on the server. It spawns
  the actor, sends the spawn to clients, then destroys its own copy through
  `SERVER_DestroyActorIfClientsidedOnly` (`src/p_acs.cpp:4206`; `src/sv_main.cpp:6925`, `:6973`;
  helper at `src/sv_main.cpp:5653-5668`). A client that runs a `CLIENTSIDE` ACS script's spawn
  marks the result `CLIENTSIDEONLY` (`src/p_acs.cpp:4209-4212`). This behavior landed in commit
  `c4f241990`, which is an ancestor of 3.2.1.

## Consequences

- **Client-run action functions.** `NETWORK_IsActorClientHandled` is true for a
  `CLIENTSIDEONLY` actor (`src/network.cpp:1604`). Many action functions return early on clients
  unless the actor is client-handled, among them `A_FadeOut`, `A_FadeIn`, `A_SetScale`,
  `A_ChangeVelocity`, `A_Warp`, `A_RadiusGive` and the `ACS_Named*` family (for example
  `thingdef_codeptr.cpp:3050`). For this flag they run locally on each client.
- **No server copy to query.** Since the server holds no copy (or destroys it straight away), no
  server-side logic, such as a server ACS script or another actor's pointer, can find it.
- **Map reset.** On a client, `GAME_ResetMap` destroys every `CLIENTSIDEONLY` actor that wasn't
  spawned by the map (`src/g_game.cpp:3428-3442`).

## Wiki/engine divergence

The wiki says "If spawned serverside, the server will merely tell clients to spawn it." That is
accurate only for the third path above (ACS spawns and `summon`). For map things and action-function
spawns, the server does not spawn the actor at all and sends nothing. Each client spawns its own.

## Engine-family divergence

UZDoom has no client/server actor split. It registers the name as
`DEFINE_DUMMY_FLAG(CLIENTSIDEONLY, false)` (UZDoom source `src/scripting/thingdef_data.cpp:458`).
A dummy entry has no storage offset, so the DECORATE parser hands it to the deprecated-flag handler
(`src/scripting/decorate/thingdef_parse.cpp:460-462`), and that handler's default case does
nothing (`src/scripting/thingdef_properties.cpp:343`). The `false` argument means it isn't even
marked deprecated. `+CLIENTSIDEONLY` therefore parses silently on UZDoom and has no effect. The
actor is an ordinary actor.

## See also

- [`+SERVERSIDEONLY`](serversideonly.md), [`+ALLOWCLIENTSPAWN`](allowclientspawn.md),
  [`+NONETID`](nonetid.md): the other Zandronum network flags.
- [Jump functions and network synchronization](../concepts/network-jump-synchronization.md): RNG
  behavior of `CLIENTSIDEONLY` actors in `A_Jump`-family actions.
- [Client-side scripting](../../acs/concepts/clientside-scripting.md): the ACS-side counterpart.
