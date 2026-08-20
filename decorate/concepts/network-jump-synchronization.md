# Jump functions and network synchronization

**Tier:** B (the `A_Jump`/`A_JumpIf`-specific claims below are tier-A source-verified — see those
files; generalizing to other `A_JumpIf*` siblings is architectural reasoning from the confirmed
client/server model, not independently traced per function).
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** Synthesized from this repo's own verified [`A_Jump`](../actions/a_jump.md) and
[`A_JumpIf`](../actions/a_jumpif.md) findings (both wiki-intake + source-verified, 2026-07-31),
[`../../acs/concepts/clientside-scripting.md`](../../acs/concepts/clientside-scripting.md)'s
verified client/server prediction model, and source checks of `src/thingdef/thingdef_exp.cpp`
(`pr_exrandom`) and the RNG-seed lifecycle (`src/sdl/i_system.cpp`, `src/d_net.cpp`,
`src/d_main.cpp`) done while compiling this file — no claim below goes beyond what's cited.

DECORATE's `A_Jump`/`A_JumpIf*` family ticks on both the server and every client, but only the
server's decisions are authoritative for an ordinary (non-`+CLIENTSIDEONLY`) actor. Every
synchronization pitfall below is a different way client-side execution says or does something the
server didn't actually decide.

## Why the client runs these functions at all

Per the client/server model documented in
[`clientside-scripting.md`](../../acs/concepts/clientside-scripting.md): the client predicts and
interpolates locally instead of polling the server every tic, so ordinary state-machine action
functions genuinely execute on both sides for smoothness — the server only needs to correct the
client when a prediction turns out wrong. `A_Jump`/`A_JumpIf` are ordinary state actions, so they
tick on the client too; each function's own `NETWORK_InClientMode()` guard (and, critically,
*where* that guard sits relative to the function's other work) decides whether that client-side
tick is inert or has a side effect.

## Cause 1: RNG rolled before the network gate is checked (verified: `A_JumpIf`)

[`A_JumpIf`](../actions/a_jumpif.md) evaluates its boolean expression *before* checking
`NETWORK_InClientMode()`; [`A_Jump`](../actions/a_jump.md) checks first and only rolls its own RNG
(`pr_cajump`) if the check passes. If `A_JumpIf`'s expression calls
`random()`/`frandom()`/`random2()`, the client burns a roll anyway, even though its own jump gets
discarded.

That roll doesn't come from a stream private to the one actor calling `A_JumpIf` — **`pr_exrandom`
is the single default RNG for every unnamed `random()`/`frandom()`/`random2()` call in every
DECORATE expression across the entire map**, verified in `src/thingdef/thingdef_exp.cpp`
(`FRandom pr_exrandom("EX_Random")` is the fallback used whenever an expression's random call
doesn't name a specific RNG via `random[name](...)`). So one wasted roll shifts every *later*
unnamed-RNG expression evaluated on that client relative to the server or to any other client.

**The actual severity is narrower than "desync" implies.** Zandronum has no RNG-state consistency
check between server and client (no code path compares `FRandom` state over the network), and a
server-authoritative actor's real outcome always arrives via `SERVERCOMMANDS_*` regardless of what
the client's wasted computation produced — so this bug causes no disconnect and no wrong gameplay
outcome for server-authoritative actors. The real, narrower risk: it perturbs the same client's own
`+CLIENTSIDEONLY` actors' (unnamed) `random()`-based cosmetic behavior, since their private draws
are now shifted by an unrelated network event elsewhere on the map — less reproducible, not
gameplay-broken.

## Cause 2: reading networked state before it's caught up (architectural risk, not independently verified per function)

Position-, LOS-, or inventory-based conditions (`A_JumpIfCloser`, `A_JumpIfTargetInLOS`,
`A_JumpIfInventory`, and siblings — not individually source-traced the way `A_Jump`/`A_JumpIf`
were) inherit the predict-and-correct model's core caveat: the client's copy of another actor's
position/inventory/etc. can lag the server's true value by up to one round-trip. A condition
evaluated at "the same" tic on server and client can legitimately produce different results
transiently — not because either side has a bug, but because the client's information is provably
stale by design. Treat this as inherent to the architecture, not a specific function to blame,
until one of these siblings gets its own source-verified writeup.

## Cause 3: `+CLIENTSIDEONLY` actors' RNG is never expected to match across machines (by design, not a bug)

`rngseed` — the per-process value every named `FRandom` (including `pr_cajump`) is (re-)seeded
from — is never transmitted between server and client in live play: each process draws its own
from `I_MakeRNGSeed()` (`/dev/urandom`/`/dev/random`, falling back to `time(NULL)` —
`src/sdl/i_system.cpp`), and the one mechanism that would carry a shared seed across the network —
the legacy `NCMD_SETUP` handshake's `D_ArbitrateNetStart()` — has its only call site commented out
in `D_CheckNetGame` (`src/d_net.cpp`). So a `+CLIENTSIDEONLY` actor's own `A_Jump`/`A_JumpIf`-driven
decisions are guaranteed to diverge from every other machine's copy of "the same" actor. This is
inconsequential exactly as long as the actor honors `NETFL_CLIENTSIDEONLY`'s own contract,
documented at its declaration in `src/actor.h`: "only spawned by the clients... don't affect the
game in any way (visuals aside)." It stops being inconsequential the moment a modder gives a
clientside-only actor's random jump outcome any gameplay weight another player needs to agree on.

## Cause 4: a not-taken branch's own side effects still execute on every client (verified: `A_JumpIf`)

The three causes above are about the jump *decision* diverging or costing an RNG roll. This one is
about ordinary action functions placed in the state range a broken jump was supposed to skip.

`A_JumpIf` on a non-`+CLIENTSIDEONLY` actor never actually jumps in client mode — it returns before
`ACTION_JUMP` runs (see [`A_JumpIf`](../actions/a_jumpif.md)'s source excerpt). "Doesn't jump" means
state advancement simply continues to the very next state, exactly as if the condition had evaluated
false. If the states in between the `A_JumpIf` and its (never-reached-on-client) target contain their
own action functions — spawning something, playing a sound, giving inventory — those actions are not
skipped by the broken jump. They run, on every client, every single time the state machine reaches
that point, regardless of what the condition was actually testing for.

This is most damaging when the skipped action spawns a `+CLIENTSIDEONLY` actor. `A_SpawnItemEx`
(and `A_SpawnItem`) let a `+CLIENTSIDEONLY` spawn *type* proceed on the client even when the
*spawning* actor isn't `+CLIENTSIDEONLY` — `NETWORK_ShouldActorNotBeSpawned`'s `bSpawnOnClient`
check independently considers `GetDefaultByType(pSpawnType)->NetworkFlags & NETFL_CLIENTSIDEONLY`
(`src/thingdef/thingdef_codeptr.cpp`, the shared spawn-gating helper used by both functions), not
just the caller's own flag. So a server-authoritative actor's `A_JumpIf`-gated `Spawn:` loop that
tries to conditionally show a `+CLIENTSIDEONLY` cosmetic (an overlay icon, a status effect glow, a
UI-only number) based on the actor's own state (velocity, health, distance, anything) will show that
cosmetic **unconditionally on every joined client**, for the actor's entire lifetime, because the
gating jump that was supposed to suppress it never fires there. The condition still evaluates
correctly server-side (and in true singleplayer, where the actor is never in client mode at all) —
only clients see the cosmetic ignore its own gate.

**Fix:** don't gate a `+CLIENTSIDEONLY` side effect from the parent's (non-`+CLIENTSIDEONLY`)
`A_JumpIf`. Move the condition into the spawned `+CLIENTSIDEONLY` actor's *own* `Spawn:` state
chain instead — its `A_JumpIf` network-check is on `self` too, and `self` there genuinely is
`+CLIENTSIDEONLY`, so the check's `NETWORK_InClientMode() && (self->NetworkFlags &
NETFL_CLIENTSIDEONLY) == false` gate correctly evaluates false and the jump fires as written on
every machine. Whatever the condition needs to read from the parent (its velocity, a distance, a
flag) has to be handed to the child explicitly at spawn time — e.g. `A_SpawnItemEx`'s `xvel`/`yvel`/
`zvel` parameters, or a `SXF_TRANSFERSPECIAL`/args-based value — since the child cannot read the
parent's fields itself once spawned.

## Strategies to avoid these in your own DECORATE

1. **Never put an RNG call inside a condition expression that runs on a non-`+CLIENTSIDEONLY` actor
   before a network gate.** Don't write `A_JumpIf(random(0,255) < N, ...)` directly on a
   server-authoritative actor. If you need "randomly branch, conditioned on some state," split it:
   a pure state check via `A_JumpIf` (no RNG in the expression) landing in a target state that then
   calls `A_Jump` for the probability roll — `A_Jump`'s own gate is correctly ordered, so the RNG
   only fires once server-authority is already confirmed.
2. **Don't design gameplay/UI logic that trusts a client's own locally-evaluated jump decision for
   a server-authoritative actor as final** — it's a preview the server can still overrule via the
   next `SERVERCOMMANDS_SetThingFrame`. Anything that must be authoritative (score, damage, item
   grants) belongs behind the server-side branch, not inferred from what the client's copy of the
   state machine appeared to do.
3. **Keep `+CLIENTSIDEONLY` actors within their contract.** If two players must agree on a
   jump-driven outcome (a shared visual cue, anything gameplay-adjacent), that decision has to be
   made server-side and broadcast — don't reach for `+CLIENTSIDEONLY` plus a random jump and expect
   it to look the same for everyone watching.
4. **Give position/LOS/inventory-gated jumps slack instead of exact-tic dependence.** A mod that
   needs to "look right" the instant a networked value changes should tolerate a tic of visible lag
   on the client rather than assuming the jump fires in perfect lockstep with the server's update.
5. **Never rely on a non-`+CLIENTSIDEONLY` actor's `A_JumpIf` to gate whether a `+CLIENTSIDEONLY`
   cosmetic gets spawned.** The gate is inert on every client, so the "skip" branch's action
   functions run unconditionally there. Put the condition inside the cosmetic's own state chain,
   passing it whatever parent data it needs at spawn time.

## Engine-family divergence

This entire file is Zandronum-specific. Confirmed directly in UZDoom source: `A_Jump`
(`src/playsim/p_actionfunctions.cpp`) is a plain RNG-gated jump with no network check of any kind —
no `NETWORK_InClientMode`-equivalent guard exists anywhere in the function. `A_JumpIf` isn't even a
native action function in UZDoom; it's a trivial two-line ZScript wrapper
(`wadsrc/static/zscript/actors/checks.zs`) that evaluates its boolean argument and calls
`ResolveState`, again with no network gating. More broadly, `NETWORK_InClientMode`,
`SERVERCOMMANDS_*`, and `NETFL_CLIENTSIDEONLY` — the mechanisms every cause in this file is built
on — don't exist in UZDoom at all; `CLIENTSIDEONLY` is parsed only as a recognized-but-ignored
"dummy flag" (`src/scripting/thingdef_data.cpp`) kept around for DECORATE-source compatibility, not
a functioning network-scope mechanism. This tracks the two engines' fundamentally different
networking models: Zandronum's client-server architecture with per-actor server authority and
client-side prediction/correction (the model this file and
[`clientside-scripting.md`](../../acs/concepts/clientside-scripting.md) document) versus UZDoom's
simpler ZDoom-heritage networking, which has no equivalent client-side prediction layer for actor
state machines to diverge from in the first place. None of the four causes documented above, nor
the RNG-desync/`+CLIENTSIDEONLY`-contract reasoning built on them, apply to UZDoom.

## See also

- [`A_Jump`](../actions/a_jump.md) — the correctly-ordered case; full source trace of the RNG-seed
  lifecycle.
- [`A_JumpIf`](../actions/a_jumpif.md) — the network-check-ordering bug in full detail.
- [Crash-and-bug checklist](crash-and-bug-checklist.md) — the terse review-index entry for this
  pattern.
- [`../../acs/concepts/clientside-scripting.md`](../../acs/concepts/clientside-scripting.md) — the
  general client/server prediction model this reasoning is built on.
