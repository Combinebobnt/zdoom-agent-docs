# Thing_Stop

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** ZDoom Wiki `Thing_Stop` page (Thing_Stop - ZDoom Wiki.html, https://zdoom.org/w/index.php?title=Thing_Stop&oldid=38935 saved 2026-07-29), verified against the Zandronum source's `src/p_lnspec.cpp:1617-1654` and `src/sv_commands.cpp:1646-1649`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

**Action special, index 19.** Positive index in `zcommon.bcs`'s `special` table; behavior at `p_lnspec.cpp:1617` `FUNC(LS_Thing_Stop)`.

**Signature:** `int Thing_Stop(int tid)`

Stops the specified actor's current movement by zeroing its velocity vectors. 

## Parameters

- `tid` — thing tag. `0` means the activator (the actor that activated the script). Non-zero finds all actors with that TID via `TActorIterator` and stops every match. If `tid=0` and there is no activator (e.g., an OPEN script called with no activator, or an unbound script call), the function returns `0` and does nothing.

## Return value

Returns `1` if at least one actor was stopped, `0` otherwise (no activator when `tid=0`, or no actors matching the given `tid`).

## Behavior notes

This function zeroes the actor's full 3D velocity (`velx`, `vely`, `velz` on Zandronum) and, for players, also the player's own separate velocity. That player-side velocity is 2D only (Zandronum `player->velx`/`player->vely`), so there is no player `velz` to clear. A player's vertical velocity is still zeroed through its actor.

**Wiki divergence:** The ZDoom wiki claims this sets "acceleration and speed to 0". The implementation sets velocity only — it does not touch any acceleration field (`DECORATE` `Speed` property, internal acceleration state, etc.). As a result, the actor is free to re-accelerate on the next game tick. This is why the wiki's own example pairs `Thing_Stop` with `SetPlayerProperty(0, 1, PROP_TOTALLYFROZEN)` to prevent the player from moving afterward — `Thing_Stop` alone does not freeze an actor in place, only halts its current motion.

## Zandronum netcode

On a server (`NETSTATE_SERVER`), the function sends `SERVERCOMMANDS_MoveThingExact` to replicate the velocity change to all clients. The replication scope differs by actor type:

- **Non-player actors:** position **and** velocity are synced (`CM_X|CM_Y|CM_Z|CM_VELX|CM_VELY|CM_VELZ`).
- **Player actors:** only velocity is synced (`CM_VELX|CM_VELY|CM_VELZ`). Position is deliberately not resynced.

Offline, and on the server itself, the velocity change is applied locally; only the broadcast is gated on `NETSTATE_SERVER`. An actor with no net ID (e.g. a `SERVERSIDEONLY` actor) gets no update, because `SERVERCOMMANDS_MoveThingExact` returns early for it (`sv_commands.cpp:1648-1649`).
