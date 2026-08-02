# TeleportOther

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki (verified against Zandronum fork implementation, 2026-07-29, https://zdoom.org/w/index.php?title=TeleportOther&oldid=44556)

## Signature

```
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
