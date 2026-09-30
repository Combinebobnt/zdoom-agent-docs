# Jump functions and network synchronization

**Tier:** B (the `A_Jump`/`A_JumpIf`-specific claims below are tier-A source-verified — see those
files; every other jump function's guard and relay was traced to source for "The general rule"
below, but that section is not wiki-backed).
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** Synthesized from this repo's own verified [`A_Jump`](../actions/a_jump.md) and
[`A_JumpIf`](../actions/a_jumpif.md) findings (both wiki-intake + source-verified, 2026-07-31),
[`../../acs/concepts/clientside-scripting.md`](../../acs/concepts/clientside-scripting.md)'s
verified client/server prediction model, and source checks of `src/thingdef/thingdef_exp.cpp`
(`pr_exrandom`) and the RNG-seed lifecycle (`src/sdl/i_system.cpp`, `src/d_net.cpp`,
`src/d_main.cpp`) done while compiling this file — no claim below goes beyond what's cited.
The server-relay and sibling-gating corrections rest on `src/thingdef/thingdef_codeptr.cpp`
(`DoJump` 695-753, `A_Jump` 765-785, `A_JumpIfCloser`/`A_JumpIfTracerCloser`/`A_JumpIfMasterCloser`
875-906, `DoJumpIfInventory` 913-966, `A_JumpIfTargetInLOS` 4242-4363), `src/cl_main.cpp:5722-5769`
(`client_SetThingFrame`) and `src/sv_commands.cpp:2070-2073`. The Death-state variant under
cause 4 adds `src/p_interaction.cpp:830-836,925` (`AActor::Die`), `src/cl_main.cpp:5342-5356`
(`KillThing`) and `src/p_mobj.cpp:513-521,619-647` (`SetState`, `HideOrDestroyIfSafe`), read
2026-09-29 at the same revision. "The general rule" and the hold-delivery subsection add, read
2026-09-29 at the same revision: every `ACTION_JUMP` call site in `src/thingdef/thingdef_codeptr.cpp`
(line ranges given per function below; none exist outside that file), `A_PlaySound`/`A_PlaySoundEx`
(`:445-459`, `:536-549`), `src/network.cpp:1598-1612` (`NETWORK_IsActorClientHandled`),
`src/sv_commands.cpp:2070-2127` (`SERVERCOMMANDS_SetThingFrame`), `src/sv_main.cpp:5517-5540`
(`SERVER_HandleWeaponStateJump`) and `:6169-6211` (`server_MissingPacket`),
`src/cl_main.cpp:1146-1156,1332-1402,5360-5437` (in-order parsing, `CLIENT_CheckForMissingPackets`,
`SetThingState`), `protocolspec/spec.things.txt`, `src/network/netcommand.cpp:282-288,300-308`
and `src/networkshared.h:72`.

DECORATE's `A_Jump`/`A_JumpIf*` family ticks on both the server and every client, but only the
server's decisions are authoritative for an ordinary (non-`+CLIENTSIDEONLY`) actor. Every
synchronization pitfall below is a different way client-side execution says or does something the
server didn't actually decide.

## Why the client runs these functions at all

Per the client/server model documented in
[`clientside-scripting.md`](../../acs/concepts/clientside-scripting.md): the client predicts and
interpolates locally instead of polling the server every tic, so ordinary state-machine action
functions genuinely execute on both sides. `A_Jump`/`A_JumpIf` are ordinary state actions, so they
tick on the client too. Each function's own network guard (`NETWORK_InClientMode()`, the
`NETWORK_InClientModeAndActorNotClientHandled()` form, or none at all) decides whether that
client-side call is inert or has a side effect, and so does *where* that guard sits relative to
the function's other work.

For a gated jump the client makes no decision of its own. The server tells it about the jump
instead: when the jump's `ACTION_JUMP` call passes `CLIENTUPDATE_FRAME` (as `A_Jump` and `A_JumpIf`
do) and the jump comes from the actor's own state, `DoJump` sends `SERVERCOMMANDS_SetThingFrame`
every time the server takes it (`src/thingdef/thingdef_codeptr.cpp:725-743`), not only when a
client guessed wrong. The client then enters the target state and runs its action
(`client_SetThingFrame`, `src/cl_main.cpp:5722-5769`). Jumps whose `ACTION_JUMP` passes `0` send
nothing; there the client's own evaluation is the only thing that moves it.

## The general rule: the server decides every gated jump, and the client falls through first

On an actor that is not `+CLIENTSIDEONLY`, a gated jump function never jumps on a client. It
returns before `ACTION_JUMP`, so the client's copy carries on to the next state exactly as if the
condition were false. The server decides, and when it jumps from the actor's own state it sends
the jump as `SERVERCOMMANDS_SetThingFrame`. Only `Goto`, `Loop`, `Wait` and plain state-to-state
flow are client-local.

**This includes `A_Jump(256, ...)`.** `A_Jump`'s client-mode guard (`thingdef_codeptr.cpp:772-776`)
comes before its chance test (`:778`), so a 100% `A_Jump` on a networked actor is a server-sent
jump on every client, not a local goto. Use `Goto` for an unconditional branch.

Every `ACTION_JUMP` call in Zandronum's DECORATE lives in `src/thingdef/thingdef_codeptr.cpp`, so
the groups below are complete for this revision. They differ in the guard and in the flags passed
to `ACTION_JUMP`:

- **Guard "client mode and not `+CLIENTSIDEONLY`", relayed.** `A_Jump` (`:765-785`),
  `A_JumpIfHealthLower` (`:792-806`), `A_JumpIfCloser` (`:875-896`, adds a position update),
  `A_JumpIf` (`:3523-3538`), `A_CheckSight` (`:3286-3328`; a `+CLIENTSIDEONLY` caller instead
  tests whether the console player's camera sees it) and `A_Teleport` (`:5221-5281`). An actor
  with no net ID is still inert on the client under this guard, and the server sends it nothing
  (`EnsureActorHasNetID`), so its client copy never takes the jump (see cause 4).
- **Guard `NETWORK_InClientModeAndActorNotClientHandled`, relayed.**
  `A_JumpIfTargetOutsideMeleeRange` (`:815-831`), `A_JumpIfTargetInsideMeleeRange` (`:836-852`),
  `A_CheckLOF` (`:4046-4207`), `A_JumpIfInTargetLOS` (`:4373-4447`), `A_MonsterRefire`
  (`:4933-4954`) and `A_Warp` (`:5556-5691`). "Client-handled" means `+CLIENTSIDEONLY` **or net ID
  0** (`NETWORK_IsActorClientHandled`, `src/network.cpp:1598-1612`). So, unlike the first group,
  an actor with no net ID evaluates these on the client and jumps locally.
- **`DoJumpIfInventory` (`:913-966`): `A_JumpIfInventory` and `A_JumpIfInTargetInventory`
  (`:968-976`).** Gated and relayed like the first group, except in two cases the client handles
  itself: a call from the player's weapon or flash psprite state (flags `0`, no relay), and a call
  on the local console player's own actor, which evaluates its own inventory. For any player
  actor the relay carries `CLIENTUPDATE_SKIPPLAYER`, so it goes to every client except that
  player's (`SVCF_SKIPTHISCLIENT`). For a non-player it adds a position update.
- **No guard, relayed.** `A_JumpIfTargetInLOS` (`:4242-4363`). The source comment at its jump
  (`:4358-4361`) assumes monsters have no target on the client, in which case the client's copy
  returns at the no-target check and waits for the relay (with a position update for a
  non-player). That premise isn't guaranteed: some code paths replicate a target
  (`SERVERCOMMANDS_SetThingTarget` has several call sites), `JLOSF_CHECKMASTER` reads `master`,
  and a player caller aims with `P_AimLineAttack` locally. Whenever the client has the data, it
  evaluates the condition and can jump on its own, and the server's relay still arrives.
  `A_JumpIfTracerCloser`/`A_JumpIfMasterCloser` (`:898-906`) have the same unguarded, relayed
  shape; see the crash-and-bug checklist's replication-bugs section.
- **Flags `0`: client-local, never relayed.** `A_JumpIfArmorType` (`:983-996`), `A_JumpIfNoAmmo`
  (`:1472-1482`), `A_CheckSightOrRange` (`:3374-3400`), `A_CheckRange` (`:3436-3462`),
  `A_CheckFloor` (`:3702-3712`), `A_CheckCeiling` (`:3722-3732`), `A_PlayerSkinCheck`
  (`:3880-3889`), `A_CheckForReload` (`:4553-4577`) and `A_CheckFlag` (`:4752-4767`). None has a
  client-mode guard, so each machine follows its own evaluation and the fall-through rule doesn't
  apply to them.

**How the relay arrives.** `SERVERCOMMANDS_SetThingFrame` (`src/sv_commands.cpp:2070-2127`) sends
`SetThingState` instead when the target is the actor's Melee, Missile, Wound or Pain state and the
jump goes to every client (`:2077-2101`; a `SKIPPLAYER` relay never takes this shortcut). That
is still a server-sent jump: the client's handler calls `SetState` with the action, the same as
`client_SetThingFrame` does (`src/cl_main.cpp:5360-5437`). A jump from a weapon or flash psprite
state goes through `SERVER_HandleWeaponStateJump` instead (see [`A_Jump`](../actions/a_jump.md)'s
"Network considerations"); the same fall-through applies there. A jump inside a
`CustomInventory` state chain (`statecall`) only sets the chain's next state, with no relay; its
client-side behavior isn't traced here.

**What to review.** The client runs everything from the gate to wherever the fall-through leads
until the server's jump lands: zero-tic states always, timed ones depending on latency. Read that
stretch for client-visible effects: `+CLIENTSIDEONLY` spawns (`A_SpawnItemEx` and `A_SpawnItem`
let a `+CLIENTSIDEONLY` type through from a networked caller, see cause 4), the frames and
animation the client shows meanwhile, and any other action that runs unguarded on clients.
**Sounds are not a finding.** `A_PlaySound` (`:445-459`) and `A_PlaySoundEx` (`:536-549`) return
in client mode on a non-`+CLIENTSIDEONLY` actor, because the server plays them and tells clients,
so a fall-through sound is never heard on its own.

None of this applies to UZDoom, which has no client/server split for actors (see "Engine-family
divergence" below).

## Cause 1: RNG rolled before the network gate is checked (verified: `A_JumpIf`)

[`A_JumpIf`](../actions/a_jumpif.md) evaluates its boolean expression *before* checking
`NETWORK_InClientMode()`; [`A_Jump`](../actions/a_jump.md) checks first and only rolls its own RNG
(`pr_cajump`) if the check passes. If `A_JumpIf`'s expression calls
`random()`/`frandom()`/`random2()`, the client burns a roll anyway, even though its own jump gets
discarded. `A_Jump`'s own arguments are also evaluated before its gate (its chance argument is read
at the top of the function), so a `random()` in `A_Jump`'s chance argument burns a roll the same
way. Only the `pr_cajump` rolls sit behind the gate.

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

## Cause 2: the server's jump reaches the client late, and some siblings evaluate locally anyway

The position-, LOS- and inventory-based siblings don't share one network model. Each one's guard
and `ACTION_JUMP` flags are traced under "The general rule" above; for timing, three shapes
matter:

- **Gated, server-relayed** (most of them). The client never evaluates stale data. It falls
  through and stays on that path until the server's frame update arrives, which lags the server's
  jump by the network latency.
- **Ungated, evaluated on the client.** `A_JumpIfTargetInLOS`, `A_JumpIfTracerCloser` and
  `A_JumpIfMasterCloser` have no network guard, and the `NETWORK_InClientModeAndActorNotClientHandled`
  group has none on an actor with no net ID. The client runs them against its own copy of the
  pointers and positions, which can differ from the server's. When the server jumps it still
  sends a frame update if the actor has a net ID.
- **Flags `0`, client on its own.** These send nothing. Each machine follows its own evaluation.

So a condition evaluated at "the same" tic can transiently put server and client in different
states, because the relayed jump arrives late or because an ungated sibling read different local
data. Neither is a bug in one function.

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

`A_JumpIf` on a non-`+CLIENTSIDEONLY` actor never jumps by itself in client mode. It returns before
`ACTION_JUMP` runs (see [`A_JumpIf`](../actions/a_jumpif.md)'s source excerpt), so state
advancement continues to the very next state, exactly as if the condition had evaluated false.
The server's jump does reach the client later as a `SERVERCOMMANDS_SetThingFrame` (see "Why the
client runs these functions at all" above), but only after the network latency. Until it lands,
the client keeps stepping through the not-taken states. Any action functions there (spawning
something, playing a sound, giving inventory) run on the client regardless of what the condition
was testing for. Zero-tic states right after the `A_JumpIf` always run, in the same tic, before any
update could possibly arrive. An actor with no net ID gets no update at all
(`EnsureActorHasNetID`, `src/sv_commands.cpp:2072`), so its client copy never takes the jump.

This is most damaging when the skipped action spawns a `+CLIENTSIDEONLY` actor. `A_SpawnItemEx`
(and `A_SpawnItem`) let a `+CLIENTSIDEONLY` spawn *type* proceed on the client even when the
*spawning* actor isn't `+CLIENTSIDEONLY` — `NETWORK_ShouldActorNotBeSpawned`'s `bSpawnOnClient`
check independently considers `GetDefaultByType(pSpawnType)->NetworkFlags & NETFL_CLIENTSIDEONLY`
(`src/thingdef/thingdef_codeptr.cpp`, the shared spawn-gating helper used by both functions), not
just the caller's own flag. So a server-authoritative actor's `A_JumpIf`-gated `Spawn:` loop that
tries to conditionally show a `+CLIENTSIDEONLY` cosmetic (an overlay icon, a status effect glow, a
UI-only number) based on the actor's own state (velocity, health, distance, anything) will spawn
that cosmetic **on every joined client every pass** when the spawn sits in zero-tic states right
after the gate, because the server's jump that was supposed to skip it always arrives too late.
With longer states in between, the result depends on latency instead. The condition still
evaluates correctly server-side (and in true singleplayer, where the actor is never in client mode
at all). Only clients see the cosmetic ignore its own gate.

**Fix:** don't gate a `+CLIENTSIDEONLY` side effect from the parent's (non-`+CLIENTSIDEONLY`)
`A_JumpIf`. Move the condition into the spawned `+CLIENTSIDEONLY` actor's *own* `Spawn:` state
chain instead — its `A_JumpIf` network-check is on `self` too, and `self` there genuinely is
`+CLIENTSIDEONLY`, so the check's `NETWORK_InClientMode() && (self->NetworkFlags &
NETFL_CLIENTSIDEONLY) == false` gate correctly evaluates false and the jump fires as written on
every machine. Whatever the condition needs to read from the parent (its velocity, a distance, a
flag) has to be handed to the child explicitly at spawn time — e.g. `A_SpawnItemEx`'s `xvel`/`yvel`/
`zvel` parameters, or a `SXF_TRANSFERSPECIAL`/args-based value — since the child cannot read the
parent's fields itself once spawned.

**That fix only works when the child can compute the condition on the client** from data handed
over at spawn (velocity, a distance, a value passed through args). A condition only the server
knows can't move into a clientside actor: a value an ACS script set on the server (a skill-derived
setting in a user variable, say), a server cvar, inventory, health, the target pointer. For those,
keep the gate on the networked parent and use the two-gate shape with a holding fall-through from
the Death-state variant below. That shape isn't specific to `Death`, and its three conditions
apply unchanged.

### The Death-state variant: the client runs the wrong branch, or both

The same thing happens when the gate sits in a `Death` state, where it is harder to hide. For a
non-player actor, the server's `AActor::Die` sends
`SERVERCOMMANDS_KillThing` (`src/p_interaction.cpp:830-836`) before it enters the death state
(`:925`). A player's death goes through `SERVERCOMMANDS_KillPlayer` instead, not traced here. The client's handler sets
health and calls `Die` itself (`ServerCommands::KillThing::Execute`, `src/cl_main.cpp:5342-5356`),
and `Die` enters the death state through `SetState` on the client too, running its 0-tic chain.
The client's `A_JumpIf` is inert, so it falls through and runs the fall-through branch's actions,
spawning any `+CLIENTSIDEONLY` items there. When the server's condition was true, its jump then
arrives as `SERVERCOMMANDS_SetThingFrame`. What the client shows depends on whether its copy is
still alive by then:

- **The fall-through ends in `Stop` within the same tic** (all 0-tic states): the client's `Die`
  destroys its copy inside the kill handler, before the frame update in the same tic is
  processed (see the first condition below). The client shows **only the fall-through branch**,
  which is the wrong one whenever the server jumped.
- **The fall-through outlives the tic** (it runs on into a timed death animation, say): the
  frame update lands, the client enters the jump target and runs that branch too. A "spawn X or Y
  on death" gate shows **both** X and Y on every client whenever the server jumped.

**Fix shape:** put both branches on jump targets and leave nothing in the fall-through.

```decorate
Death:
  TNT1 A 0 A_JumpIf(<condition>, "DeathA")
  TNT1 A 0 A_JumpIf(!(<condition>), "DeathB")
  TNT1 A -1          // holds the client's copy until the server's jump lands
DeathA:
  TNT1 A 0 A_SpawnItemEx("EffectA")
  Stop
DeathB:
  TNT1 A 0 A_SpawnItemEx("EffectB")
  Stop
```

The server takes exactly one jump and sends it. The client runs neither branch on its own and
then runs the one it is sent. Three conditions on this shape:

- **The fall-through must keep the actor alive.** If it ends in `Stop`, the client's copy is
  destroyed at once (`SetState` with no state calls `HideOrDestroyIfSafe`, which destroys in
  client mode, `src/p_mobj.cpp:513-521,619-647`), so the frame update arrives for an actor that is
  gone and neither branch runs there. Use a hold state with `-1` tics, as above. A `Wait` on a
  0-tic state is a same-tic loop, so don't use that instead.
- **No RNG in either condition.** Both are evaluated on the client before the network gate
  (cause 1), and the server evaluates the condition twice, so a random term can also make the
  server take neither jump or roll different values for the two tests.
- **The actor needs a net ID**, or the server's jump never reaches the client (see above).

### Delivery of the server's jump, and how long the hold lasts

A `-1` hold looks like it could strand the client's copy forever if the jump were lost. For a
connected client it can't:

- **The jump is a reliable command.** Neither `SetThingFrame` nor `SetThingState` is marked
  `UnreliableCommand` in `protocolspec/spec.things.txt` (the keyword appears nowhere in that file),
  and `NetCommand::getBufferForClient` puts every command not marked unreliable into the client's
  reliable `PacketBuffer` (`src/network/netcommand.cpp:282-288`).
- **The client parses reliable packets strictly in sequence** (`src/cl_main.cpp:1146-1156`), so
  nothing sent later overtakes the jump. When it sees a gap it sends `CLC_MISSINGPACKET`, and asks
  again every `TICRATE/4` tics until the gap is filled (`CLIENT_CheckForMissingPackets`,
  `:1332-1402`).
- **The server resends from its per-client `SavedPackets` archive**, the last `PACKET_BUFFER_SIZE`
  (2048, `src/networkshared.h:72`) packets it sent that client. If a requested packet is no longer
  there, it kicks the client with "Too many missed packets." (`server_MissingPacket`,
  `src/sv_main.cpp:6169-6211`). The client also disconnects itself once it is 2048 packets behind
  (`src/cl_main.cpp:1350-1356`).

So the hold ends within a resend round trip, or the client leaves the game. It never lasts
indefinitely. One gap: a command broadcast to everyone skips clients that haven't received their
initial full update yet (`SVCF_SKIP_CLIENTS_WITHOUT_FULLUPDATE`, `netcommand.cpp:307-308`), so a
client joining at that moment doesn't get the jump. What its full update sends for the actor
instead isn't traced here.

**A finite hold instead of `-1`.** Holding N tics and then taking a no-effect path bounds the wait
under any delay, but trades one failure for another. If the jump lands after the timeout while the
copy is still alive, the client runs the target branch after the timeout path, a smaller version
of the original double. If the timeout path already ended in `Stop`, the late jump finds nothing
and the client misses the branch. With `-1` the only cost is the copy sitting in the hold state until
the jump lands.

**The jump can arrive before the gate.** A client's copy can enter the state later than the
server's (its timed states run a few tics behind, for example). The jump then lands while the
copy hasn't reached the gate yet. `client_SetThingFrame` calls `SetState` from wherever the copy
is (`src/cl_main.cpp:5761`), so the copy moves straight to the target, runs it, and never reaches
the hold. That is the intended outcome, not a failure case.

## Strategies to avoid these in your own DECORATE

1. **Never put an RNG call inside a condition expression that runs on a non-`+CLIENTSIDEONLY` actor
   before a network gate.** Don't write `A_JumpIf(random(0,255) < N, ...)` directly on a
   server-authoritative actor. If you need "randomly branch, conditioned on some state," split it:
   a pure state check via `A_JumpIf` (no RNG in the expression) landing in a target state that then
   calls `A_Jump` for the probability roll. `A_Jump`'s gate comes before its `pr_cajump` rolls,
   so those only fire once server authority is confirmed. Keep `A_Jump`'s chance argument a
   literal, since an argument expression is evaluated before the gate.
2. **Don't design gameplay/UI logic that trusts what a client's copy of a server-authoritative
   actor's state machine appeared to do.** Gated jumps only show up on the client late, via
   `SERVERCOMMANDS_SetThingFrame`, and ungated or flags-`0` siblings may follow the client's own
   evaluation. Anything that must be authoritative (score, damage, item grants) belongs behind the
   server-side branch.
3. **Keep `+CLIENTSIDEONLY` actors within their contract.** If two players must agree on a
   jump-driven outcome (a shared visual cue, anything gameplay-adjacent), that decision has to be
   made server-side and broadcast — don't reach for `+CLIENTSIDEONLY` plus a random jump and expect
   it to look the same for everyone watching.
4. **Give position/LOS/inventory-gated jumps slack instead of exact-tic dependence.** A mod that
   needs to "look right" the instant a networked value changes should tolerate a tic of visible lag
   on the client rather than assuming the jump fires in perfect lockstep with the server's update.
5. **Never rely on a non-`+CLIENTSIDEONLY` actor's `A_JumpIf` to gate whether a `+CLIENTSIDEONLY`
   cosmetic gets spawned.** The gate is inert on every client, so the "skip" branch's action
   functions run there until the server's frame update arrives, and zero-tic ones always run. Put the condition inside the cosmetic's own state chain,
   passing it whatever parent data it needs at spawn time. If the condition depends on something
   only the server knows (server-set values, cvars, inventory, health, target), keep the gate on
   the parent in the two-gate shape with a `-1` hold instead (see cause 4's Death-state variant).
6. **Don't treat `A_Jump(256, ...)` as a local goto.** On a networked actor it is a gated,
   server-relayed jump like any other, so the client falls through first. Use `Goto` when the
   branch is unconditional.

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
state machines to diverge from in the first place. Neither the general rule (server-decided
jumps, client fall-through, the relay's delivery) nor the four causes documented above, nor the
RNG-desync/`+CLIENTSIDEONLY`-contract reasoning built on them, apply to UZDoom.

## See also

- [`A_Jump`](../actions/a_jump.md) — the correctly-ordered case; full source trace of the RNG-seed
  lifecycle.
- [`A_JumpIf`](../actions/a_jumpif.md) — the network-check-ordering bug in full detail.
- [Crash-and-bug checklist](crash-and-bug-checklist.md) — the terse review-index entry for this
  pattern.
- [`../../acs/concepts/clientside-scripting.md`](../../acs/concepts/clientside-scripting.md) — the
  general client/server prediction model this reasoning is built on.
