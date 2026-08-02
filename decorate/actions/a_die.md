# `void A_Die(name damagetype = "none")`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_Die` (retrieved 2026-08-01, oldid=54643) + verified against Zandronum source's `src/p_enemy.cpp:3614` and `wadsrc/static/actors/actor.txt`.
**Bucket:** action function on `AActor` (callable from any actor's state table).

Kills the calling actor if it is not already dead, setting its health value to 0 and transitioning it to its Death state. This has only an effect if the actor has the `MF_SHOOTABLE` or `MF6_VULNERABLE` flag set. Optionally, a damage type can be provided.

Internally, this calls `P_DamageMobj` with both the inflictor and source pointers set to null, and passes the `DMG_FORCED` flag (which bypasses invulnerability checks but does not bypass the SHOOTABLE/VULNERABLE gate). The damage amount is the actor's current health value; if the actor is already dead (health ≤ 0), the call returns early without effect.

## Parameters

- `damagetype` — the damage type to use for the death, as a name/string. Defaults to `"none"`. Controls which death state is entered (e.g., `Death.Fire` for damage type `Fire`).

## Network behavior

In multiplayer (client mode), this action is a no-op — the game server handles actor death exclusively. A `+CLIENTSIDEONLY` actor calling `A_Die` will never actually die, since the action returns without calling `P_DamageMobj`.

## Examples

Simple death in a DECORATE state:

```decorate
TROO H 2 A_Die;
```

Using a specific damage type:

```decorate
TROO H 2 A_Die("Fire");
```

## Wiki divergences

The ZDoom Wiki's documented signature uses single quotes (`damagetype = 'none'`); Zandronum's DECORATE definition in `wadsrc/static/actors/actor.txt` uses double quotes. The wiki page also includes a ZScript-only example (with anonymous action blocks and `ResolveState`) — see `concepts/state-machine.md` for why those features are unavailable in Zandronum DECORATE.

## See also

- `DamageMobj` (C++ engine function; called by `A_Die` internally)
- `Death` state (the target state entered after `A_Die` kills an actor)
