# TeleportOther

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** ZDoom Wiki (verified against Zandronum fork implementation, 2026-07-29, https://zdoom.org/w/index.php?title=TeleportOther&oldid=44556)
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

## Signature

```text
int TeleportOther(int other_tid, int dest_tid, int fog)
```

Action special with index 76. All three parameters are mandatory (no optional parameters per BCS syntax).

## Parameters

- **`other_tid`** — The TID of the actor(s) to teleport. If `0`, the function does nothing and returns `0`.
- **`dest_tid`** — The TID of the destination marker. Must be a `TeleportDest` or `TeleportDest2` actor class; a plain mapspot or unrelated actor with this TID will **not** be recognized. If `0` or no destination is found, the function returns `0`.
- **`fog`** — Control of teleport effects. Any nonzero value (not just `1`) enables fog spawning at source and destination, plus velocity halt (see Behavior below). `0` disables fog and preserves velocity.

## Return Value

Returns `1` (true) if at least one actor was successfully teleported, or `0` (false) otherwise.

## Behavior

Teleports all actors with the specified `other_tid` to the location of the destination `TeleportDest`. Unlike `Teleport` and `Teleport_NoFog` (which act on the activator), `TeleportOther` acts on any actor(s) matching a TID.

**Multiple actors:** If multiple actors share the same `other_tid`, all of them are teleported to the same destination.

**Destination class requirement:** The destination is found via `NActorIterator(NAME_TeleportDest, dest_tid)` — only actors of class `TeleportDest` or its subclasses (e.g. `TeleportDest2`) are recognized. A plain mapspot with the destination TID will silently fail. **This is a fork/wiki divergence** — the wiki describes the parameter generically as "TID of the map spot" without specifying the class constraint.

**Height handling:** If the destination is a `TeleportDest2`, the teleported actor lands at the destination's z-coordinate. Otherwise, actors land at `ONFLOORZ` (floor height of the destination sector).

**Velocity and fog interaction:**
- **If `fog=0` (no fog):** Velocity is preserved unchanged. Actor angle is preserved.
- **If `fog` is nonzero:** Velocity is halted to zero. Actor angle is set to the destination's angle. Teleport fog effects appear at source and destination.

**No valid targets:** Returns `0` (false) if `other_tid` is `0`, `dest_tid` is `0`, or no actors match either TID.

## Activator, Spectators, Server-Side

No inherent `tid=0` activator fallback — `other_tid=0` simply does nothing.

Teleporting spectators disables both source and destination fog effects (intended behavior, not documented on wiki).

In multiplayer, teleportation is server-authoritative; clients receive `SERVERCOMMANDS_TeleportThing` updates.

## Engine-family divergence: spectators and network authority

The spectator-fog rule and the server-authoritative network model described above are Zandronum-specific and do not exist in UZDoom. UZDoom's teleport path (the UZDoom source's `src/playsim/p_teleport.cpp:81-255`, `EV_TeleportOther`/`P_Teleport`) has no `bSpectating`-equivalent player flag anywhere in the file, so there is no spectator case that suppresses fog. UZDoom also has no `SERVERCOMMANDS_TeleportThing`/`NETWORK_GetState()`-style client-server authority split (the Zandronum source's `src/p_teleport.cpp:187-192, 631-640` gates fog on `bSpectating` and pushes a `SERVERCOMMANDS_TeleportThing` update when acting as a server) — GZDoom-family netcode has no equivalent construct in this file.

UZDoom does gate fog spawning on a different, unrelated condition: a `predicting` flag (`thing->player && (thing->player->cheats & CF_PREDICTING)`, the UZDoom source's `src/playsim/p_teleport.cpp:83, 202-208`) suppresses fog spawning during client-side prediction of an unlagged move, not for spectators specifically. This is a distinct client-prediction mechanism, not a UZDoom analogue of the spectator rule.

Everything else in this file (the destination-class fallback chain, the velocity/fog/angle interaction driven by `TELF_KEEPORIENTATION`/`TELF_DESTFOG`/`TELF_SOURCEFOG`, and the `TeleportDest2`-vs-`ONFLOORZ` height rule) was confirmed identical in UZDoom's `EV_TeleportOther`/`P_Teleport`/`SelectTeleDest` (the UZDoom source's `src/playsim/p_teleport.cpp:274-343, 651-668`).
