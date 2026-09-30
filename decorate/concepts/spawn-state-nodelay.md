# The first Spawn state's action and `NoDelay`

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-29); Zandronum 3.3-alpha @bdd0f7beb (2026-09-29)
**Provenance:** Source-derived (no wiki page consulted). Zandronum: `src/p_mobj.cpp`
(`AActor::StaticSpawn`, `AActor::PostBeginPlay`, `AActor::Tick`), `src/actor.h` (`MF7_HANDLENODELAY`),
`src/thingdef/thingdef_states.cpp` (the `NODELAY` keyword). UZDoom: `src/playsim/p_mobj.cpp`
(`ConstructActor`, `AActor::PostBeginPlay`, `AActor::Tick`, `AActor::CheckNoDelay`),
`wadsrc/static/zscript/actors/actor.zs` and `actors/shared/fastprojectile.zs` (paraphrased, GPL-3.0).
Also observed live in a driven Zandronum session (see "Observed" below). The `Goto`-only `Spawn:`
case adds `src/p_states.cpp` (`SetGotoLabel`, `RetargetStates`) and `src/sc_man.cpp`
(`ScriptMessage`) on Zandronum and `src/p_states.cpp` on UZDoom, read 2026-09-29.

**When an actor is spawned, the action on its first `Spawn:` state does not run unless that state
carries the `NoDelay` keyword.** Nothing warns about it: no parse error, no console message. A
first-state action that nothing re-enters is silently dead code.

## Mechanism

1. **Spawn sets the state directly, not through `SetState`.** The engine assigns the actor's
   `SpawnState`, its tics, sprite and frame straight onto the new actor, with a source comment
   saying outright that the spawn state's action routine will not be called, because action
   routines can't run yet. Zandronum: `AActor::StaticSpawn`, `src/p_mobj.cpp:4915-4920`. UZDoom:
   `ConstructActor`, `src/playsim/p_mobj.cpp:5463-5467`.
2. **`PostBeginPlay` arms a one-shot check.** It sets `MF7_HANDLENODELAY` on every new actor.
   Zandronum `src/p_mobj.cpp:5191`; UZDoom `src/playsim/p_mobj.cpp:5802`.
3. **The actor's first `Tick` consumes it.** If the flag is set and the actor isn't dormant, the
   flag is cleared, and only if the current state has `NoDelay` is that state's action run.
   - Zandronum re-enters the state through `SetState` (`AActor::Tick`,
     `src/p_mobj.cpp:4520-4535`). That runs the action and chains through any following 0-tic
     states like a normal transition. A first state with a nonzero duration gets one extra tic so
     it isn't cut short.
   - UZDoom calls the state's action directly from `AActor::CheckNoDelay`
     (`src/playsim/p_mobj.cpp:5171-5195`, called from `AActor::Tick` at line 5108), and only
     changes state if the action itself returned a jump.
   - While the actor is dormant the whole check is skipped and the flag stays set.
4. **Without `NoDelay`, the first state just times out.** Tick decrements its tics and, at zero or
   below, moves to the *next* state with `SetState` (Zandronum `src/p_mobj.cpp:4589`; UZDoom
   `src/playsim/p_mobj.cpp:5118`). A 0-tic first state is left on the first tick, and its own
   action never ran.

## What it breaks

Judge each hit by whether anything ever re-enters the first state:

- **A 0-tic (or any) first state that nothing jumps back to: the action never runs.** Typical
  victims are one-shot setup and pickers:
  - a random picker such as `A_Jump(256, "A", "B", "C")`. The jump never fires, so every instance
    falls through to whatever state follows, and the "random" variety is always the first
    fall-through branch;
  - initialization such as `A_SetUserVar`, `A_SetArg`, `A_SetTranslucent`;
  - a one-shot `A_SpawnItemEx`, `A_PlaySound`, or `ACS_NamedExecute*` call.
- **A first state re-entered by `Loop` or `Goto Spawn`: only its first run is lost.** A looping
  `A_FadeOut`, `A_Look` or trail spawn simply starts one cycle late. Usually harmless, but it is
  still a behavior difference from what the definition reads like.

## Review checklist form

Grep each actor's `Spawn:` label for a first state that has an action and no `NoDelay`. For each
hit, decide whether the action is meant to run on spawn or is dead code (drop it). Either fix
makes a live action run:

- **`NoDelay`** on that first state, as below.
- **A blank 0-tic state ahead of it**, such as `TNT1 A 0` with no action, placed right after
  `Spawn:`. The blank state is what spawn skips, and the first tick's move past it goes through
  `SetState` (Zandronum `src/p_mobj.cpp:502-604`, UZDoom `src/playsim/p_mobj.cpp:852-949`). That
  runs the next state's action and keeps chaining through 0-tic states, so the action fires on
  the first tick, the same timing as `NoDelay`. This is the older idiom and appears widely in
  existing mods. A `Loop` back to `Spawn:` passes through the blank state again, which is
  harmless at 0 tics. A blank state with a nonzero duration also works but delays the action by
  that many tics.

Either fix switches on behavior that has never happened in play, so re-test it rather than
treating the change as cosmetic.

```text
ACTOR Example
{
  States
  {
  Spawn:
    TNT1 A 0 NoDelay A_Jump(256, "Spin1", "Spin2")   // without NoDelay: always Spin1
    // Equivalent: a blank first state, then the action state:
    //   TNT1 A 0
    //   TNT1 A 0 A_Jump(256, "Spin1", "Spin2")
  Spin1:
    XAMP A 4
    Loop
  Spin2:
    XAMP B 4
    Loop
  }
}
```

## A `Spawn:` label that is only a `Goto`

`Spawn:` followed directly by `Goto Death` (or any other `Goto`) makes the target label's first
state the spawn state. The rule above applies to that state unchanged: its action does not run on
spawn. The usual `NoDelay` fix is not available there, because `NoDelay` is accepted only on the
state written immediately after `Spawn:`. A `Spawn:` label with no states of its own is turned
into a pointer to its `Goto` target (`FStateDefinitions::SetGotoLabel` calling `RetargetStates`,
Zandronum `src/p_states.cpp:596-623,758-776`, UZDoom `src/p_states.cpp:696-723,868-880`), so under the
target label the parser's `GetStateLabelIndex(NAME_Spawn) == GetStateCount()` test fails
(Zandronum `src/thingdef/thingdef_states.cpp:284-294`, UZDoom
`src/scripting/decorate/thingdef_states.cpp:261-271`). The keyword is then dropped with a red
`Script error, "<lump>" line <n>: NODELAY may only be used immediately after Spawn:` console line
that does not stop loading (`FScanner::ScriptMessage`, Zandronum `src/sc_man.cpp:914-932`;
UZDoom `src/common/engine/sc_man.cpp:1096-1115`, which also sets `ParseError`, a flag only the
ZScript `ScriptScanner` binding reads, `src/common/scripting/interface/vmnatives.cpp:1876`).

Two fixes:

- **A blank 0-tic first state under the target label**, so the first tick's move past it runs
  the real first state's action through `SetState`, as in the checklist above. Entering that label
  the normal way (for example `Death` on a kill) also passes through the blank state, which is
  harmless at 0 tics.
- **Give `Spawn:` a real state carrying `NoDelay`**, holding the action, then `Goto` the target.

```text
ACTOR Example
{
  States
  {
  Spawn:
    Goto Death
  Death:
    TNT1 A 0                                  // blank: spawn skips this one
    TNT1 A 0 A_SpawnItemEx("SomeEffect")      // now runs on the first tick
    Stop
  }
}
```

## Observed

In a driven Zandronum 3.3-alpha session, 20 spawns each of two actors whose first state was
`<sprite> A 0 A_Jump(256, <five spin labels>)` were read two tics later. Without `NoDelay` all 40
were on the first fall-through label. With `NoDelay` added, each class landed on all five labels
(3/4/5/3/5 and 3/5/4/3/5), and no console message appeared in either run.

## Engine-family divergence

Same rule on both engines: the first `Spawn:` state's action runs on spawn only with `NoDelay`.
Two differences:

- **How the `NoDelay` action runs** (see step 3 above): Zandronum re-enters the state through
  `SetState`, so a 0-tic `NoDelay` state also chains into following 0-tic states that tick.
  UZDoom runs just that action and follows only a jump it returns.
- **UZDoom only: the check lives in `Actor.Tick`.** It is exposed to ZScript as
  `CheckNoDelay()` (declared in `wadsrc/static/zscript/actors/actor.zs`), and
  `FastProjectile`'s own `Tick` override calls it itself. So a ZScript class whose `Tick` override
  never calls `Super.Tick()` has to call `CheckNoDelay()` too, or `NoDelay` stops working for it.
  Zandronum has no ZScript, so this case can't arise there.
