# `void A_Die(name damagetype = "none")`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_Die` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_Die&oldid=54643) + verified against Zandronum source's `src/p_enemy.cpp:3614` and `wadsrc/static/actors/actor.txt`; `+SPECTRAL`, dead-actor and buddha handling at `src/p_interaction.cpp:1182-1211` and `:1586-1590`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** action function on `AActor` (callable from any actor's state table).

Kills the calling actor if it is not already dead, setting its health value to 0 and transitioning it to its Death state. This has only an effect if the actor has the `MF_SHOOTABLE` or `MF6_VULNERABLE` flag set. Optionally, a damage type can be provided.

Internally, this calls `P_DamageMobj` with both the inflictor and source pointers set to null, and passes the `DMG_FORCED` flag (which bypasses invulnerability checks but does not bypass the SHOOTABLE/VULNERABLE gate). The damage amount is the actor's current health value. If the actor is already dead (health ≤ 0), `P_DamageMobj` returns early without effect, except that a frozen `ICECORPSE` corpse is shattered.

On Zandronum, `DMG_FORCED` does not skip the `+SPECTRAL` check, so a `+SPECTRAL` actor is never killed by `A_Die` (the null inflictor fails that check). UZDoom's `DMG_FORCED` does skip it. Also on Zandronum, a player with the buddha cheat is left at 1 health instead of dying.

## Parameters

- `damagetype` — the damage type to use for the death, as a name/string. Defaults to `"none"`. Controls which death state is entered (e.g., `Death.Fire` for damage type `Fire`).

## Network behavior

On a Zandronum client (and during client-side demo playback), this action is a no-op. The game server handles actor death exclusively. So online, a `+CLIENTSIDEONLY` actor calling `A_Die` on a client will never actually die, since the action returns without calling `P_DamageMobj`. Offline, the action is not in client mode and kills it normally.

## Engine-family divergence: no client/server authority split

UZDoom's source tree has no `NETWORK_InClientMode`/`SERVERCOMMANDS_*`-style client-authority mechanism anywhere at all (unlike Zandronum's split-mode netcode). `A_Die` (`wadsrc/static/zscript/actors/actor.zs`) is a one-line wrapper that unconditionally calls `DamageMobj(null, null, health, damagetype, DMG_FORCED)` — there is no client-mode early return, so the action always runs to completion regardless of network role. `CLIENTSIDEONLY` itself is registered in UZDoom only as a recognized-but-inert `DEFINE_DUMMY_FLAG` (`src/scripting/thingdef_data.cpp`) — it compiles but has no runtime effect, so the doc's Zandronum-specific claim that a `+CLIENTSIDEONLY` actor "will never actually die" does not apply to UZDoom.

## Examples

Simple death in a DECORATE state:

```decorate
ACTOR ShortLivedImp : DoomImp
{
  States
  {
  Spawn:
    TROO A 35
    TROO H 2 A_Die
    Stop
  }
}
```

Using a specific damage type (enters `Death.Fire` if the actor defines it):

```decorate
ACTOR BurningImp : DoomImp
{
  States
  {
  Spawn:
    TROO A 35
    TROO H 2 A_Die("Fire")
    Stop
  }
}
```

## Wiki/engine divergence: quote style and ZScript-only example

The ZDoom Wiki's documented signature uses single quotes (`damagetype = 'none'`); Zandronum's DECORATE definition in `wadsrc/static/actors/actor.txt` uses double quotes. The wiki page also includes a ZScript-only example (with anonymous action blocks and `ResolveState`) — see `concepts/state-machine.md` for why those features are unavailable in Zandronum DECORATE.

## See also

- `DamageMobj` (C++ engine function; called by `A_Die` internally)
- `Death` state (the target state entered after `A_Die` kills an actor)
