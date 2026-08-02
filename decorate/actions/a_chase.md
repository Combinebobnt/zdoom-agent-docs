# `A_Chase` (monster pursuit and attack decision)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_Chase` (retrieved 2026-07-31, oldid=54054) + verified against the Zandronum source's `src/p_enemy.cpp:3049-3067` and the shared `A_DoChase` implementation (`src/p_enemy.cpp:2438-2868`).
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_Chase)` in `src/p_enemy.cpp`.

The core monster chase-and-attack action: handles target acquisition, decision-making between melee and ranged attacks, and pathing. Called once per state tic (e.g., `MONS ABCD 4 A_Chase;` runs once per 4 tics), not every game tic.

## Signature

```
void A_Chase(state melee = NULL, state missile = NULL, int flags = 0)
```

## Parameters

### `melee` (state label, optional)

The state to jump to when the actor decides to perform a melee attack. If `NULL` or omitted, the actor will not initiate melee attacks. The default behavior (called when `melee` is not a valid state) is to jump to the actor's own `MeleeState` (typically the "Melee" state label, if defined).

**Note on defaults:** The wiki describes a `'_a_chase_default'` sentinel value used in ZScript. Zandronum's DECORATE does not support this — pass `NULL` / omit the argument for no melee attacks, or pass an actual state label.

### `missile` (state label, optional)

The state to jump to when the actor decides to perform a ranged attack. If `NULL` or omitted, the actor will not initiate missile attacks. The default behavior (called when `missile` is not a valid state) is to jump to the actor's own `MissileState` (typically the "Missile" state label, if defined).

### `flags` (int, optional)

Bitfield controlling chase behavior. Flags are combined using `|`. Only 5 flags are defined in Zandronum (the wiki lists additional ones that **do not exist in Zandronum**; see "Zandronum-only flags" below).

#### Zandronum-only flags (Zandronum 3.2.1)

- `CHF_FASTCHASE` (1) — Enables Hexen-style strafe-around-target movement (used by "player bosses"). The actor will randomly strafe perpendicular to the target, but **ignores `MaxDropOffHeight` when strafing, potentially walking off cliffs or into pits** from which it cannot escape (mitigated by `NODROPOFF` flag if the actor has it, though this is an actor property, not an A_Chase flag). Server-side only (no effect in client mode).

- `CHF_NOPLAYACTIVE` (2) — Disables active-sound playback during chase (sounds normally play ~1/60 chance per call).

- `CHF_NIGHTMAREFAST` (4) — Actor moves twice as fast on Nightmare difficulty (checked via `G_SkillProperty(SKILLP_FastMonsters)`); reduces tics in the current state accordingly.

- `CHF_RESURRECT` (8) — Actor will enter the "Heal" state (if defined) upon encountering a revivable corpse, like the Arch-Vile. Server-side only.

- `CHF_DONTMOVE` (16) — Actor will not move toward the target. Movement decisions are skipped, but attack decisions still proceed normally.

#### Flags listed in the wiki but **NOT present in Zandronum**

The following flags appear in the ZDoom wiki but are **not exported in Zandronum's `wadsrc/static/actors/constants.txt`** and will be silently treated as raw integer values with no defined behavior if passed:

- `CHF_NORANDOMTURN`
- `CHF_NODIRECTIONTURN`
- `CHF_NOPOSTATTACKTURN`
- `CHF_STOPIFBLOCKED`
- `CHF_DONTIDLE`
- `CHF_DONTTURN`

If you are targeting Zandronum, do not use these; they are likely ZDoom/GZDoom additions not backported to Zandronum 3.2.1. If the exact behavior they provide is needed, it may require a custom action function or a design workaround.

## Decision flow

When called, A_Chase performs these steps *in order* (simplified; actual implementation is more complex):

1. **Recursion guard**: Sets the `MF_INCHASE` flag to prevent infinite recursion if a state jump targets another state that calls `A_Chase` in the same tic. Returns early if already set.

2. **Stealth monster handling**: Updates stealth monster visibility tracking.

3. **Target sanity checks**:
   - Removes invisible targets (unless they are the current `goal`).
   - Removes dead or friendly targets.
   - Clears targets in client mode (network play; only server makes AI decisions).
   - Removes unshootable targets if they were only temporarily unshootable, lowering aggression threshold.

4. **Nightmare mode**: If `CHF_NIGHTMAREFAST` is set and `G_SkillProperty(SKILLP_FastMonsters)` is true, halves the state's `tics` (minimum 3).

5. **Target reacquisition** (if no target or target unshootable):
   - Friendly monsters look for whoever attacked their owner.
   - Calls `P_LookForPlayers` to find a new target via line-of-sight checks.
   - If still no target and not in client mode, friendly monsters call `A_Wander`; others call `SetIdle()` and return.

6. **Patrol/goal handling** (if actor has a `goal` and target is the goal or `MF5_CHASEGOAL` flag is set):
   - Checks melee range to the goal.
   - If reached, executes any `PatrolSpecial` map objects tied to the goal, transitions to the next patrol point, and returns.

7. **Strafe behavior** (if `CHF_FASTCHASE` set and not `CHF_DONTMOVE`, server-side only):
   - Manages random 90-degree strafes perpendicular to target at close range (<`CLASS_BOSS_STRAFE_RANGE`).

8. **Attack decisions** (if `MF_JUSTATTACKED` flag is not set, otherwise defer to next call):
   - **Melee check**: If `melee` is a valid state and `CheckMeleeRange()` returns true, jumps to the melee state.
   - **Missile check**: If `missile` is a valid state and `P_CheckMissileRange()` returns true, jumps to the missile state and sets `MF_JUSTATTACKED`.

9. **Movement** (unless `CHF_DONTMOVE` or already strafing):
   - Calls `P_Move()` with the current chase direction, or `P_NewChaseDir()` if movement fails (obstacle in the way).
   - Respects `CANTLEAVEFLOORPIC` flag (reverts move if floor texture changed).

10. **Unseen target reacquisition** (if target is out of sight and not in client mode):
    - Calls `P_LookForPlayers` again to find a better target.

11. **Active sound** (~3/256 chance per call, if `CHF_NOPLAYACTIVE` not set):
    - Calls `PlayActiveSound()`.

12. **Cleanup**: Clears the `MF_INCHASE` flag.

## Related functions

- **`A_FastChase`**: Equivalent to calling `A_Chase(MeleeState, MissileState, CHF_FASTCHASE | CHF_NIGHTMAREFAST)` — always strafes and always applies nightmare speed boost. Server-side only.

- **`A_VileChase`**: Equivalent to calling `A_Chase(MeleeState, MissileState, CHF_RESURRECT | CHF_NIGHTMAREFAST)` — always checks for revivable corpses and applies nightmare boost. This is the Arch-Vile's default chase behavior.

- **`A_ExtChase` (legacy)**: A parameterized predecessor to the modern `A_Chase(state, state, int)` form; now largely superseded. Signature: `A_ExtChase(bool domelee, bool domissile, bool playactive, bool nightmarefast)` — simpler boolean parameters instead of flags, but less flexible.

## Special notes

### Infinite recursion protection

A_Chase directly calls `SetState()` to jump to the melee/missile state, rather than returning a state pointer. This is intentional and necessary — **do not call A_Chase from within the first tic of an attack state** (e.g., as the first action in a Melee or Missile state), or the same state may re-enter itself in the same tic, exhausting the engine's state-change queue and crashing the game. The `MF_INCHASE` guard prevents this in normal use but is not a complete defense if you jump into an attack state then immediately call A_Chase in the same frame.

### Network behavior (Zandronum multiplayer)

- Movement and attack decisions are **server-authoritative**. Clients receive position/state updates from the server and replay animations, but do not make AI decisions.
- In client mode, `target` and `goal` are forced to `NULL` before the main decision loop.
- Several operations (`P_NewChaseDir`, `P_Move`, `CHF_FASTCHASE` strafe, target reacquisition) are skipped in client mode and performed only on the server.
- Certain state changes and position updates are broadcast to clients via `SERVERCOMMANDS_*` calls.

### Performance characteristics

A_Chase conditionally calls several expensive operations:
- `P_CheckSight` (line-of-sight trace) — only when reacquiring out-of-sight targets.
- `P_LookForPlayers` (broad target search) — only when target is missing or out of sight.
- `P_CheckMissileRange` (distance + line-of-sight check for missiles) — only when considering a missile attack.
- `P_Move` + `P_NewChaseDir` (pathfinding) — once per call, but skipped if `CHF_DONTMOVE` set or already strafing.

**Most calls are gated on specific conditions**, so A_Chase's actual cost varies widely depending on actor state and target presence. Calling it once per 4–8 tics (via state duration) is the intended usage; calling it every tic would incur significant overhead.

## Open questions and untraced details

- Exact behavior of `P_NewChaseDir` direction-selection algorithm (used to pick a new chase direction when movement fails).
- Exact behavior of `P_Move` internal collision handling and how it interacts with the `CANTLEAVEFLOORPIC` check.
- Whether calling `A_Chase` with omitted/NULL melee/missile arguments triggers any fallback to the actor's `MeleeState`/`MissileState` (currently appears to require an explicit state label; wiki implies automatic fallback via sentinel, which Zandronum does not support).

## Example (Zandronum DECORATE)

```
actor Scurymonster : Actor
{
    Default
    {
        Monster;
        Height 20;
        Radius 16;
        Speed 10;
    }

    States
    {
    Spawn:
        MONS A 10 A_Look;
        Loop;
    See:
        MONS ABCD 4 A_Chase("Melee", "Missile");
        Loop;
    Melee:
        MONS F 5 A_CustomMeleeAttack(5);
        Goto See;
    Missile:
        MONS E 5 A_SpawnProjectile("SomeProjectile");
        Goto See;
    Pain:
        MONS G 2;
        Goto See;
    Death:
        MONS H 5;
        MONS I 5 A_NoBlocking;
        MONS J -1;
        Stop;
    }
}
```

(Note: the wiki's example uses the ZScript class syntax `class Scurymonster : Actor {}` and calls `A_SpawnProjectile("Cowmissile")`, which does not exist in Zandronum's DECORATE. The above is the equivalent DECORATE form.)
