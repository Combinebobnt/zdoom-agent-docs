# Teleport_NoStop

**Tier:** A
**Engine:** Zandronum 3.2.1 (feature predates the fork; verified against the `3.3-alpha` local checkout).
**Provenance:** `Teleport_NoStop - ZDoom Wiki.html` (`https://zdoom.org/wiki/Teleport_NoStop`), verified 2026-07-29 against the Zandronum source's `src/p_teleport.cpp`, `p_lnspec.cpp`, and `p_spec.h`.
**Bucket:** Action special, index 154 in `zcommon.bcs`'s `special` table.

`int Teleport_NoStop(int tid, int sectortag [, int nofog])`

## Signature in this toolchain

`Teleport_NoStop(int,int;int):int` — in `zt-bcc`'s BCS signature, the third argument `nofog` is optional (after the `;`), defaulting to `0` if omitted.

## Parameters

- `tid` — TID of a teleport destination actor (usually a `TeleportDest` or `TeleportDest2`). If `tid=0` and `sectortag != 0`, the search falls back to finding any `TeleportDest` in a sector with matching `sectortag`. If both are zero, teleportation fails (returns `false`).
- `sectortag` — sector tag to restrict the `tid` destination search. If non-zero, only teleport destinations whose sector's tag matches are considered. When `tid != 0` and `sectortag != 0`, a destination must satisfy both conditions; if none are found, a compatibility fallback searches for untagged `MapSpot` or non-solid actors with matching `tid`. When `tid == 0` and `sectortag != 0`, the search uses "old Doom behavior" and returns the first `TeleportDest` found in any sector with matching tag (from lowest-numbered sector first).
- `nofog` — if non-zero, suppresses teleport fog spawning at the **departure** location only. Fog still spawns at the destination location. To suppress both, use `Teleport_NoFog` instead.

## Return value

Per `p_lnspec.cpp:891-895` and `p_teleport.cpp:345-449`:

- **Successful teleport:** returns `true`.
- **Activator is NULL:** returns `false` (e.g., in `OPEN` scripts with no activator). Test with `ActivatorTID()` if unsure.
- **Activator has `MF2_NOTELEPORT` flag set:** returns `false` without searching for a destination.
- **Destination not found (bad `tid`, bad `sectortag`, or both zero):** returns `false`.
- **Destination found but occupied/blocked:** returns `false`. The teleport move is validated with `P_TeleportMove` before spawning fog; if movement fails, the function returns `false` without side effects.
- **Called from a line's back side** (action special on a line, hit from behind): returns `false`. Only valid when called from the line's front side.

## Special behavior notes

- **Momentum preservation is not world-space-invariant:** "without losing momentum" means the actor's velocity magnitude and direction *relative to its new facing* are preserved. Specifically: the actor takes the destination spot's angle (line 180 in `p_teleport.cpp`), and then its velocity vector is rotated by the angle change. If the spot points North and the actor was moving East relative to its old facing, it will move East relative to its new facing. The speed (distance per tic) stays constant. This behavior is produced by the `haltVelocity=false` parameter passed to the underlying `P_Teleport` function (line 894), whereas the base `Teleport` special uses `haltVelocity=true` and zeroes velocity on arrival.

- **Fog spawning is asymmetric:** spawn behavior depends on three conditions:
  - Destination fog always spawns (controlled by `fog=true` in the engine call, not exposed to ACS).
  - Departure fog is controlled by the `nofog` argument (0 = spawn, non-zero = suppress).
  - **Exception: if the activator is a spectator, both fogs are suppressed** (line 188-191 in `p_teleport.cpp`), regardless of the `nofog` argument.

- **Teleport fog has side effects beyond visual:** it resets the player's field of vision (FOV zoom) and reaction time (freeze) only when `haltVelocity` is true — since this special has `haltVelocity=false`, the FOV zoom (line 212) and reaction-time freeze (line 217) do not occur. Non-player actors are unaffected by these client-side effects.

- **Zandronum netcode replication:** on the server, teleportation is broadcast to all clients via `SERVERCOMMANDS_TeleportThing(thing, sourceFog, useFog, ...)` (line 241 in `p_teleport.cpp`), and the server adjusts player reaction timing to account for network latency (lines 244-245). This differs from ZDoom, where no netcode notification is sent.

- **Specifier-allowed special (Zandronum multiplayer):** `Teleport_NoStop` is explicitly listed in `GAMEMODE_IsSpectatorAllowedSpecial()` (gamemode.cpp:1132) alongside `Teleport`, `Teleport_NoFog`, and `Teleport_Line`, confirming it is callable by spectators without special restrictions. This is a Zandronum-native carve-out not documented on the ZDoom wiki.

## Contrast with related teleport functions

- **vs. `Teleport` (index 154):** only difference is `haltVelocity`. `Teleport` zeroes velocity on arrival; `Teleport_NoStop` preserves and rotates it.
- **vs. `Teleport_NoFog` (index 155):** that function has no `nofog` parameter and instead takes a `useang` (angle preservation) and `keepheight` parameter. Parameters and behavior are unrelated despite the similar name.
- **vs. `TeleportOther` and `TeleportGroup`:** those are separate functions for teleporting other actors by TID or groups. `Teleport_NoStop` always teleports the activator.
