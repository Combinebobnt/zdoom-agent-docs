# `A_Chase` (monster pursuit and attack decision)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_Chase` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_Chase&oldid=54054) + verified against the Zandronum source's `src/p_enemy.cpp:3049-3067` and the shared `A_DoChase` implementation (`src/p_enemy.cpp:2438-2868`); parameter defaults and state-argument parsing from `wadsrc/static/actors/actor.txt:77`, `src/thingdef/thingdef_parse.cpp:124-146` and `src/thingdef/thingdef_states.cpp:353-397`; `CHF_RESURRECT` from `P_CheckForResurrection` (`src/p_enemy.cpp:2878-3032`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_Chase)` in `src/p_enemy.cpp`.

The core monster chase-and-attack action: handles target acquisition, decision-making between melee and ranged attacks, and pathing. Like any action, it runs once each time a state carrying it is entered (e.g., `MONS ABCD 4 A_Chase;` runs once per 4 tics), not every game tic.

## Signature

```text
A_Chase(state melee = "*", state missile = "none", int flags = 0)
```

This is the Zandronum declaration's shape (`wadsrc/static/actors/actor.txt:77`). `"*"` is a sentinel that is only legal as a declared default: writing `"*"` in a call is a parse error ("Invalid state name '*'"). UZDoom declares different defaults; see "Engine-family divergence: omitted melee/missile arguments do fall back on UZDoom" below.

## Parameters

On Zandronum, how `A_Chase` behaves depends first on whether the `melee` argument was written at all:

- **Bare `A_Chase` (no argument list):** `melee` keeps the `"*"` sentinel, and `A_Chase` takes the "old default" path. It attacks with the actor's own `MeleeState`/`MissileState` (the `Melee`/`Missile` labels), plays the active sound, and applies the game's default nightmare-speed setting. `flags` is ignored on this path. Write it without parentheses: the parser has no empty-argument path for this action, so `A_Chase()` is not a valid spelling of the bare call.
- **Any explicit `melee` argument:** the explicit path. Each state argument is resolved as given, and `flags` applies. An omitted `missile` here is the declared `"none"`, meaning **no missile attacks**. `A_Chase("Melee")` therefore silences the actor's ranged attack; write `A_Chase("Melee", "Missile")` to keep both.

### `melee` (state label, optional)

The state to jump to when the actor decides to perform a melee attack. State arguments must be quoted strings (or an integer jump offset). `""`, `"None"` or `0` mean no melee attacks; an unquoted `NULL` is not a string constant and fails to parse. A quoted label the actor doesn't have prints `Jump target '<label>' not found in <class>` to the console when evaluated and then counts as "no melee state".

**Note on defaults:** The wiki describes a `'_a_chase_default'` sentinel value used in ZScript. Zandronum's DECORATE has its own sentinel instead (`"*"` as the declared default of `melee` only), with the behavior described above.

### `missile` (state label, optional)

The state to jump to when the actor decides to perform a ranged attack. Same argument rules as `melee`. When `melee` is given explicitly and `missile` is omitted, `missile` defaults to `"none"` (no missile attacks). Only the bare `A_Chase` call falls back to the actor's own `MissileState`.

### `flags` (int, optional)

Bitfield controlling chase behavior, combined using `|`. Only honored when `melee` is passed explicitly (see above). Only 5 flags are defined in Zandronum (the wiki lists additional ones that **do not exist in Zandronum**; see "Flags listed in the wiki but NOT present in Zandronum" below).

#### Flags defined in Zandronum

- `CHF_FASTCHASE` (1) — Enables Hexen-style strafe-around-target movement (used by "player bosses"). Within 640 map units of the target, each call has a 100/256 chance to start a 3-call strafe perpendicular to the target, driven by velocity. That velocity movement **ignores `MaxDropOffHeight`, potentially walking off cliffs or into pits** from which it cannot escape (the `NODROPOFF` actor flag prevents this; it is an actor flag, not an A_Chase flag). Normal walking is suspended while a strafe is in progress. The strafe logic runs only on the server (skipped in client mode).

- `CHF_NOPLAYACTIVE` (2) — Disables active-sound playback during chase (the sound normally plays with a 3/256 chance per call).

- `CHF_NIGHTMAREFAST` (4) — When `G_SkillProperty(SKILLP_FastMonsters)` is true (e.g. Nightmare), halves the current state's remaining tics if they are above 3, never going below 3. It does not change the actor's `Speed`; the actor just cycles through its chase frames faster.

- `CHF_RESURRECT` (8) — Before chasing, checks for a raisable corpse just ahead in the actor's movement direction. If one is found, the corpse is revived (plays `vile/raise`, takes the reviver's friendliness), the actor enters its own `Heal` state if it defines one (otherwise it stays in its current state), and this `A_Chase` call ends without chasing. Unlike `A_VileChase`, there is no fallback to the Arch-Vile's `Heal` state. Server-side only: on clients the check always fails and the chase proceeds.

- `CHF_DONTMOVE` (16) — Actor will not move toward the target. Walking, strafing, friendly wandering and the post-attack direction change are skipped (the move counter still counts down), but attack decisions still proceed normally.

#### Flags listed in the wiki but **NOT present in Zandronum**

The following flags appear in the ZDoom wiki but are **not defined in Zandronum's `wadsrc/static/actors/constants.txt`**. Using one of these names is an unknown-identifier error that aborts loading, not a silently ignored value:

- `CHF_NORANDOMTURN`
- `CHF_NODIRECTIONTURN`
- `CHF_NOPOSTATTACKTURN`
- `CHF_STOPIFBLOCKED`
- `CHF_DONTIDLE`
- `CHF_DONTTURN`

If you are targeting Zandronum, do not use these; they are ZDoom/GZDoom-family additions not present in Zandronum. If the exact behavior they provide is needed, it may require a custom action function or a design workaround.

## Engine-family divergence: wiki-only flags are real and functional in UZDoom

The "Flags listed in the wiki but NOT present in Zandronum" list above is Zandronum-specific. All six of those flags (`CHF_NORANDOMTURN`, `CHF_NODIRECTIONTURN`, `CHF_NOPOSTATTACKTURN`, `CHF_STOPIFBLOCKED`, `CHF_DONTIDLE`, `CHF_DONTTURN`) are defined and functional on UZDoom, confirmed against the `EChaseFlags` enum (`wadsrc/static/zscript/constants.zs:153-168`) and their use in `A_DoChase` (`src/playsim/p_enemy.cpp`):

- `CHF_NORANDOMTURN` (32) — skips the `movecount`-expired random chase-direction reroll.
- `CHF_NODIRECTIONTURN` (64) — skips the per-tic turn-toward-movement-direction step.
- `CHF_NOPOSTATTACKTURN` (128) and `CHF_STOPIFBLOCKED` (256) — alter the post-attack `P_NewChaseDir`/movecount-reset behavior (the "do not attack twice in a row" step).
- `CHF_DONTIDLE` (512) — makes non-friendly actors fall back to `A_Wander` instead of `SetIdle()` when no target is found, the same as friendly actors already do.
- `CHF_DONTTURN` — a combo constant (`CHF_NORANDOMTURN | CHF_NOPOSTATTACKTURN | CHF_STOPIFBLOCKED`), not an independent bit.

UZDoom also defines one further flag this file doesn't mention at all (it isn't in either the "Flags defined in Zandronum" or the "listed in the wiki but not present" lists above): `CHF_DONTLOOKALLAROUND` (1024), which suppresses all-around target-reacquisition checks (passed as the second argument to `P_LookForPlayers`) in both the initial and unseen-target reacquisition steps.

If targeting Zandronum only, the existing "do not use these" guidance above still holds; if targeting UZDoom, all of the flags above are usable.

## Engine-family divergence: omitted melee/missile arguments do fall back on UZDoom

The "Parameters" section above describes Zandronum's fallback, which keys on the `melee` argument alone. On UZDoom the fallback is keyed differently: `A_Chase`'s native declaration (`wadsrc/static/zscript/actors/actor.zs:1287`) really does default both parameters to the `'_a_chase_default'` state-label sentinel, and `A_ChaseNative` (`src/playsim/p_enemy.cpp:2933-2951`) checks whether *either* resolved name still equals that sentinel. If both `melee` and `missile` are left at their defaults — a bare `A_Chase;` or `A_Chase();` — it takes the "old default A_Chase" branch and automatically uses `self->MeleeState`/`self->MissileState`. Passing an explicit `NULL` (or any other explicit value) for either parameter takes it out of the sentinel branch, and both parameters are then resolved via `StateLabels.GetState()` instead — matching the "NULL means no attack of that kind" behavior already documented above.

Zandronum's own DECORATE binding (`src/p_enemy.cpp:3049-3067`, already cited in this file's Provenance) differs in shape: it gates the same "old default" fallback on the `melee` parameter's sentinel (`(FState*)-1`) alone, not on either parameter the way UZDoom's does.

## Decision flow (Zandronum)

When called, A_Chase performs these steps *in order* (simplified):

1. **Guards**: Returns at once if the actor is in a Strife conversation (`MF5_INCONVERSATION`). Otherwise sets `MF_INCHASE`, returning early if it was already set (see "Re-entry protection" below).

2. **Bookkeeping**: Resets stealth-monster fade direction (`visdir`) and counts down `reactiontime`.

3. **Early target checks**: Drops an invisible (`RF_INVISIBLE`) target unless it is the `goal`. In client mode, forces `target` and `goal` to `NULL`. Counts down `threshold` (or zeroes it when the target is missing or dead).

4. **Nightmare mode**: If nightmare-fast applies and `G_SkillProperty(SKILLP_FastMonsters)` is true, halves the state's `tics` when above 3 (minimum 3).

5. **Facing**: Turns 45 degrees toward the movement direction (or faces the target while `strafecount` is set).

6. **Target sanity checks**: Drops a dead, friendly or spectating target (unless it is the `goal`). A friendly monster without a target has an 80/256 chance to target whoever last attacked its player.

7. **Target reacquisition** (if no target or target not shootable):
   - A target that is only temporarily unshootable (`NONSHOOTABLE`) is remembered in `lastenemy` and `threshold` is reset to 0.
   - Calls `P_LookForPlayers`. If it finds a new target (other than the goal), the call ends here.
   - If still no target and not in client mode, friendly monsters call `A_Wander` (unless `CHF_DONTMOVE`); others go idle via `SetIdle()`. Either way the call ends.

8. **Post-attack pause**: If `MF_JUSTATTACKED` is set, clears it, picks a new chase direction (unless the actor is fast, `CHF_DONTMOVE` is set, or in client mode) and ends the call. This is the "do not attack twice in a row" rule.

9. **Patrol/goal handling** (if the target is the goal, or `MF5_CHASEGOAL` is set and there is a goal):
   - Checks melee range to the goal.
   - If reached, executes any `PatrolSpecial` actors sharing the goal's TID, moves on to the next patrol point, and ends the call.
   - If not reached and the target is the goal, skips the attack decisions.

10. **Strafe behavior** (if `CHF_FASTCHASE` set and not `CHF_DONTMOVE`, server-side only): see `CHF_FASTCHASE` above.

11. **Attack decisions** (a frightened actor, or one targeting a player with the frightening cheat, only gets here on a 43/256 roll):
    - **Melee check**: If `melee` resolves to a state and `CheckMeleeRange()` returns true, plays the `AttackSound` and jumps to the melee state.
    - **Missile check**: If `missile` resolves to a state, the move counter has run out (or the actor is fast), and `P_CheckMissileRange()` returns true, jumps to the missile state and sets `MF_JUSTATTACKED`. `P_CheckMissileRange()` itself is where `MF_JUSTHIT` gets consumed and cleared, as a fast-path "attack right back" that skips the normal missile-range roll — see [Damage retaliation: what writes a monster's `target` during gameplay](../../shared/concepts/monster-target-retaliation.md) for what sets that flag and the damage-retaliation write path it's part of.

12. **Unseen target reacquisition** (only in multiplayer or when the actor has `TIDtoHate`, with `threshold` at 0, not in client mode, not in invasion, and the target out of sight): calls `P_LookForPlayers` again, ending the call if that yields a different target.

13. **Movement** (unless `CHF_DONTMOVE` or mid-strafe):
    - On the server, calls `P_NewChaseDir()` when the move counter runs out or `P_Move()` fails (obstacle in the way). In client mode, just calls `P_Move()`.
    - Respects `CANTLEAVEFLOORPIC` (reverts the move if the floor texture changed).

14. **Active sound** (3/256 chance per call, unless `CHF_NOPLAYACTIVE`): calls `PlayActiveSound()`.

15. **Cleanup**: Clears the `MF_INCHASE` flag.

## Related functions

- **`A_FastChase`**: Equivalent to `A_Chase` with `CHF_FASTCHASE | CHF_NIGHTMAREFAST` using the actor's own `MeleeState`/`MissileState`. It always strafes (the strafe part runs only on the server) and always applies the nightmare speed-up.

- **`A_VileChase`**: Checks for a revivable corpse first, falling back to the Arch-Vile's `Heal` state when the actor has none of its own, then chases with the actor's own `MeleeState`/`MissileState` and the game's default nightmare-speed setting. This is the Arch-Vile's default chase behavior. It is not quite `A_Chase("Melee", "Missile", CHF_RESURRECT)`, which has no Arch-Vile fallback.

- **`A_ExtChase` (legacy)**: A parameterized predecessor to the modern `A_Chase(state, state, int)` form; now largely superseded. Signature: `A_ExtChase(bool domelee, bool domissile, bool playactive = true, bool nightmarefast = false)` — simpler boolean parameters instead of flags, but less flexible.

## Special notes

### Re-entry protection

A_Chase jumps by calling `SetState()` directly, and `SetState()` runs the new state's action immediately, while `MF_INCHASE` is still set. So an `A_Chase` in the first frame of the melee/missile state is a no-op when that state was entered from `A_Chase`; it cannot recurse. Zero-tic state loops are a separate hazard: `SetState()` keeps advancing through zero-tic states, so a loop made only of zero-tic states hangs the game. Only clients in client mode break out, after 10000 steps, with a console warning.

### Network behavior (Zandronum multiplayer)

- Movement and attack decisions are **server-authoritative**. Clients receive position/state updates from the server and replay animations, but do not make AI decisions.
- In client mode, `target` and `goal` are forced to `NULL` before the main decision loop.
- In client mode, `P_NewChaseDir`, the `CHF_FASTCHASE` strafe, `CHF_RESURRECT` and target reacquisition (`P_LookForPlayers` always returns false there) are skipped. Clients still call `P_Move` along the current direction until the server changes it.
- Certain state changes and position updates are broadcast to clients via `SERVERCOMMANDS_*` calls.

### Performance characteristics

A_Chase conditionally calls several expensive operations:
- `P_CheckSight` (line-of-sight trace) — for the unseen-target check (multiplayer or `TIDtoHate` only, with `threshold` at 0), and inside `P_CheckMissileRange` and `P_LookForPlayers`.
- `P_LookForPlayers` (broad target search) — only when target is missing or out of sight.
- `P_CheckMissileRange` (distance + line-of-sight check for missiles) — only when considering a missile attack.
- `P_Move` + `P_NewChaseDir` (pathfinding) — once per call, but skipped if `CHF_DONTMOVE` set or already strafing.

**Most calls are gated on specific conditions**, so A_Chase's actual cost varies widely depending on actor state and target presence. Stock Doom monsters call it every 2 to 4 tics (e.g. the Demon's 2-tic and the Zombieman's 4-tic `See` frames).

## Engine-family divergence: chase movement uses P_SmartMove, not plain P_Move

The "Movement" decision-flow step and the "Performance characteristics" section above both name `P_Move()` as the function `A_Chase` calls to advance the actor each tic — accurate for Zandronum's `A_DoChase` (`src/p_enemy.cpp`). UZDoom's `A_DoChase` (`src/playsim/p_enemy.cpp:2687`) calls `P_SmartMove()` instead, an MBF21-derived wrapper (`src/playsim/p_enemy.cpp:723`) that calls `P_Move()` internally but adds two extra behaviors gated on compatibility/actor flags with no Zandronum equivalent: staying on a lift the actor's target is also riding (`MF8_STAYONLIFT` / `COMPATF2_STAYONLIFT`), and steering away from damaging floor hazards or crushing ceilings (`MF8_AVOIDHAZARDS` / `COMPATF2_AVOID_HAZARDS`). Neither behavior is reachable unless the relevant flag or compatibility option is set, so a default-configured actor moves the same either way, but a UZDoom actor or map opting into either flag will see chase movement Zandronum has no equivalent for.

## Engine-family divergence: no client/server authority split in UZDoom

The "Network behavior (Zandronum multiplayer)" section above, and the "Server-side only" qualifiers on the `CHF_FASTCHASE` and `CHF_RESURRECT` flags earlier in this file, describe Zandronum's client/server authoritative model. UZDoom's `A_DoChase` (`src/playsim/p_enemy.cpp:2365-2717`) has no equivalent split: there is no `NETWORK_InClientMode()`-style check anywhere in the function, nor anywhere in UZDoom's source tree at all (GZDoom-family netcode does not use Zandronum's server-authoritative AI model), no forced-`NULL` of `target`/`goal` in a "client mode," and no `SERVERCOMMANDS_*`-style broadcast of state changes. `A_Chase` and its variants run identically on every machine in a UZDoom multiplayer session; the flags' "server-side only" qualifiers and the network-behavior bullets above do not apply.

## Open questions and untraced details

- Exact behavior of `P_NewChaseDir` direction-selection algorithm (used to pick a new chase direction when movement fails).
- Exact behavior of `P_Move` internal collision handling and how it interacts with the `CANTLEAVEFLOORPIC` check.

## Example (Zandronum DECORATE)

```text
actor Scurymonster
{
    Monster
    Height 20
    Radius 16
    Speed 10

    States
    {
    Spawn:
        MONS A 10 A_Look
        Loop
    See:
        MONS ABCD 4 A_Chase("Melee", "Missile")
        Loop
    Melee:
        MONS F 5 A_CustomMeleeAttack(5)
        Goto See
    Missile:
        MONS E 5 A_CustomMissile("SomeProjectile")
        Goto See
    Pain:
        MONS G 2
        Goto See
    Death:
        MONS H 5
        MONS I 5 A_NoBlocking
        MONS J -1
        Stop
    }
}
```

(Note: the wiki's example uses the ZScript class syntax `class Scurymonster : Actor {}` and calls `A_SpawnProjectile("Cowmissile")`, which does not exist in Zandronum's DECORATE. The above is the equivalent DECORATE form, using `A_CustomMissile`.)
