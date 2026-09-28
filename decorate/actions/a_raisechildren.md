# `void A_RaiseChildren()`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki `A_RaiseChildren` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_RaiseChildren&oldid=53237) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:4852-4868` and `src/p_things.cpp:527-566`; raise eligibility from `src/p_mobj.cpp:7849-7868` and `src/p_interaction.cpp:513-518`; `SXF_SETMASTER` gating from `src/thingdef/thingdef_codeptr.cpp:2400-2454`; the no-parentheses parse error from `src/thingdef/thingdef_states.cpp:432-440`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_RaiseChildren)` in `src/thingdef/thingdef_codeptr.cpp`.

Resurrects all actors whose master pointer is set to the calling actor, typically creatures spawned by the calling actor. Zandronum version takes **no parameters** — the `flags` parameter and `RF_*` constants described in the ZDoom Wiki do not exist in Zandronum.

## Signature

```text
void A_RaiseChildren()
```

## Behavior

When called, this action:

1. **Iterates all actors in the current map** using a global thinker iterator.
2. **Identifies children** by checking if `mo->master == self` (the actor's master pointer equals the calling actor).
3. **Attempts to resurrect each child** by calling `P_Thing_Raise(mo)`, which:
   - Looks up the child's `Raise` state through its raise-eligibility check (see "Resurrection failure conditions" below). A child that is still alive, still playing its death animation, or has no `Raise` state is skipped with no effect.
   - Zeroes the child's horizontal velocity, temporarily makes it solid, and restores its height and radius to their default values.
   - **Checks if there is room** for the resurrected actor at its current position using `P_CheckPosition`. If not enough room, its original flags, height and radius are restored, the child remains dead, and no further processing occurs for that actor.
   - Plays the "vile/raise" sound effect.
   - Calls `Revive()` to restore the actor to life.
   - Sets the actor to its `Raise` state.
4. **Continues iterating** through all remaining actors; multiple children can be resurrected in one call.

## Child relationship and scope

A child's master relationship is typically established via `A_SpawnItemEx(..., SXF_SETMASTER)`, which sets the spawned actor's `master` pointer to the spawner. If the spawner is a missile, the master becomes the actor that fired it instead (the engine walks up the missile's `target` chain). The `A_RaiseChildren` action then uses that relationship to identify and resurrect victims.

The two engines differ on when `SXF_SETMASTER` takes effect. On UZDoom it always sets the pointer. On Zandronum it only does so when the spawned actor is a monster (`ISMONSTER`) and the spawner (or the missile's shooter) is also a monster; a non-monster spawner, or a spawned non-monster, gets no master from this flag, so `A_RaiseChildren` will not see it as a child.

**Important limitation:** Actors spawned with `A_SpawnProjectile` (UZDoom) or its Zandronum counterpart `A_CustomMissile` are **not affected** by `A_RaiseChildren`. Neither action sets the `master` pointer, and neither was designed to spawn creatures targeted by this action. Only use `A_SpawnItemEx` with the `SXF_SETMASTER` flag if you intend to later resurrect spawned actors via `A_RaiseChildren`.

## Resurrection failure conditions

### Not eligible to be raised

`P_Thing_Raise` returns without effect, and the child stays as it is, unless all of the following hold:

- The child is a corpse (`MF_CORPSE` set). A living child is never affected.
- Its current state has an infinite duration (it has finished its death animation), or that state is explicitly marked as raisable (`CanRaise`).
- It is not a player pawn.
- It has a `Raise` state. Many actors do not define one and therefore cannot be resurrected.

This is not an error; it is a silent condition.

### No room to raise

If the child's default height and radius would overlap another actor or solid geometry at its current position, `P_CheckPosition` fails and the resurrection is aborted. The child remains dead and at its current location. **This check is unconditional in Zandronum** — there is no parameter to skip it (unlike the ZDoom Wiki's `RF_NOCHECKPOSITION` flag, which does not exist in Zandronum).

## Zandronum difference from ZDoom Wiki

**The ZDoom Wiki describes a more complex version** of `A_RaiseChildren` with an optional `int flags` parameter supporting two flags:

- `RF_TRANSFERFRIENDLINESS` — described as making resurrected actors change their affiliation to match the caller's.
- `RF_NOCHECKPOSITION` — described as skipping the position-availability check.

**Neither parameter nor flag constants exist in Zandronum 3.2.1.** The Zandronum version is a no-argument action that always performs the position check and does not modify affiliations — it resurrects the child as-is.

If you port DECORATE code from upstream ZDoom/GZDoom to Zandronum, do not attempt to pass flags to `A_RaiseChildren`. Zandronum's DECORATE parser rejects any opening parenthesis after a zero-argument action function with a hard "You cannot pass parameters to ..." parse error, not a silent no-op. That includes empty parentheses: on Zandronum write the call bare, as `A_RaiseChildren`, not `A_RaiseChildren()` (see [state-machine.md](../concepts/state-machine.md)).

## Monster-only resurrection

The ZDoom Wiki states: "Raise and damage functions only work with monsters." For raising, that is looser than the source. Resurrection is gated on the `MF_CORPSE` flag (see "Not eligible to be raised" above), not on `ISMONSTER` directly. At death, an actor gets `MF_CORPSE` if it is a monster, has a `Raise` state, or is a player pawn, unless it has `DONTCORPSE`. So a non-monster actor with a `Raise` state can be resurrected once it dies, though this is an uncommon configuration, and a `DONTCORPSE` monster never can.

## Engine-family divergence: flags parameter

**UZDoom implements the wiki-documented `flags` parameter**, unlike Zandronum: `A_RaiseChildren(int flags = 0)` (declared native in `wadsrc/static/zscript/actors/actor.zs`, backed by `DEFINE_ACTION_FUNCTION(AActor, A_RaiseChildren)` in `src/playsim/p_actionfunctions.cpp`). The parameter the previous section says "does not exist" is a Zandronum-only limitation — on UZDoom it exists and behaves as the wiki describes, routed through the shared `P_Thing_Raise` helper (`src/playsim/p_things.cpp`) also used by `A_RaiseMaster`, `A_RaiseSiblings`, `A_RaiseSelf`, and ZScript's `RaiseActor`:

- **`RF_TRANSFERFRIENDLINESS`** (1) makes the resurrected child copy the raiser's allegiance via `CopyFriendliness`, instead of retaining whatever affiliation it had before death.
- **`RF_NOCHECKPOSITION`** (2) skips the `P_CheckPosition` room check documented above as unconditional on Zandronum — with this flag set, UZDoom raises the child even if its restored height/radius would overlap something.

Both constants have the same values in `src/playsim/p_local.h`'s native enum and their ZScript mirror in `wadsrc/static/zscript/constants.zs`. With the default `flags = 0`, UZDoom's behavior matches what's documented above for Zandronum: unconditional position check, no friendliness transfer.

UZDoom's `P_Thing_Raise` also gates every resurrection behind a `P_CanResurrect(raiser, thing)` check that calls each actor class's overridable `virtual bool CanResurrect(Actor other, bool passive)` hook (default implementation just returns `true`, `wadsrc/static/zscript/actors/actor.zs`) — a ZScript-only extension point with no Zandronum equivalent. It's a no-op unless a mod overrides `CanResurrect`, but a mod that does can silently veto a resurrection `A_RaiseChildren` would otherwise perform.

## Zandronum-specific: network behavior

**Zandronum multiplayer:** This action is handled by the server. The iteration and resurrection calls are resolved server-side; affected clients receive state-change updates (resurrection animations) from the server via `SERVERCOMMANDS_SetThingState`.

**UZDoom has no equivalent split.** UZDoom/GZDoom-family engines have no server-authoritative/client-prediction distinction for action-function execution at all — `A_RaiseChildren`'s implementation (and the shared `P_Thing_Raise` helper it routes through) contains no `NETWORK_InClientMode`-style check or `SERVERCOMMANDS_*`-style replication call anywhere in the call chain. It simply runs the full iterate-and-raise loop wherever it's invoked.

## Related actions

- **`A_RaiseMaster`** — resurrects the calling actor's own master instead of its children.
- **`A_RaiseSiblings`** — resurrects all other actors that share the same master.
- **`A_SpawnItemEx`** — the typical way to spawn actors as children (with `SXF_SETMASTER` to establish the master relationship).
- **`A_KillChildren`** — destroys all children instead of resurrecting them.
- **`A_DamageChildren`** — damages all children by a fixed amount.
- **`A_RemoveChildren`** — removes (without death animation) the caller's dead children, or all of them if its `removeall` argument is true.
