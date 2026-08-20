# Thing_Stop

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** ZDoom Wiki `Thing_Stop` page (Thing_Stop - ZDoom Wiki.html, https://zdoom.org/w/index.php?title=Thing_Stop&oldid=38935 saved 2026-07-29), verified against the Zandronum source's `src/p_lnspec.cpp:1617-1654`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

**Action special, index 19.** Positive index in `zcommon.bcs`'s `special` table; behavior at `p_lnspec.cpp:1617` `FUNC(LS_Thing_Stop)`.

**Signature:** `int Thing_Stop(int tid)`

Stops the specified actor's current movement by zeroing its velocity vectors. 

## Parameters

- `tid` — thing tag. `0` means the activator (the actor that activated the script). Non-zero finds all actors with that TID via `TActorIterator` and stops every match. If `tid=0` and there is no activator (e.g., an OPEN script called with no activator, or an unbound script call), the function returns `0` and does nothing.

## Return value

Returns `1` if at least one actor was stopped, `0` otherwise (no activator when `tid=0`, or no actors matching the given `tid`).

## Behavior notes

This function zeroes the actor's velocity fields (`velx`, `vely`, `velz`) and, for players, the player-specific velocity (`player->velx`, `player->vely`). **Note the asymmetry:** player `velz` is *not* cleared.

**Wiki divergence:** The ZDoom wiki claims this sets "acceleration and speed to 0". The implementation sets velocity only — it does not touch any acceleration field (`DECORATE` `Speed` property, internal acceleration state, etc.). As a result, the actor is free to re-accelerate on the next game tick. This is why the wiki's own example pairs `Thing_Stop` with `SetPlayerProperty(0, 1, PROP_TOTALLYFROZEN)` to prevent the player from moving afterward — `Thing_Stop` alone does not freeze an actor in place, only halts its current motion.

## Zandronum netcode

On a server (`NETSTATE_SERVER`), the function sends `SERVERCOMMANDS_MoveThingExact` to replicate the velocity change to all clients. The replication scope differs by actor type:

- **Non-player actors:** position **and** velocity are synced (`CM_X|CM_Y|CM_Z|CM_VELX|CM_VELY|CM_VELZ`).
- **Player actors:** only velocity is synced (`CM_VELX|CM_VELY|CM_VELZ`), position is deliberately not resynced.
