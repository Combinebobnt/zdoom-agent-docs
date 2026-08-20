# Thing_SetGoal

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-06)
**Provenance:** ZDoom Wiki `Thing_SetGoal` (retrieved 2026-08-06, https://zdoom.org/w/index.php?title=Thing_SetGoal&oldid=49506), re-verified against Zandronum source `src/p_lnspec.cpp:1657-1694`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** action special 229, `p_lnspec.cpp` `FUNC(LS_Thing_SetGoal)`

**Syntax:** `Thing_SetGoal(tid, goal, delay, chasegoal)`

**Returns:** int (nonzero if any actors matched `tid`, zero otherwise)

## Parameters

- **tid** (int): Thing ID of the monster(s) to send to a patrol point. Only applies to shootable actors (those with the `MF_SHOOTABLE` flag).
- **goal** (int): Thing ID of the destination. The engine searches for a `PatrolPoint` actor with this TID (by `NActorIterator(NAME_PatrolPoint, arg1)` in `p_lnspec.cpp:1661`). If no PatrolPoint with that TID exists, or if the TID is invalid, the goal is set to `NULL`, silently clearing any existing goal without warning.
- **delay** (int): Delay in seconds before the monster starts moving. Internally converted to tics: `reactiontime = delay * TICRATE` where `TICRATE = 35` (35 tics per second). Only applied if the monster has no current target (`p_lnspec.cpp:1686-1689`).
- **chasegoal** (int): Controls whether the monster prefers its goal over any potential target. If zero: walk to target if one exists, only walk to goal if no target. If non-zero: walk to goal instead of target (sets `MF5_CHASEGOAL` flag).

## Behavior

Sets a goal patrol point for one or more monsters, causing them to begin path-following. The function returns a boolean indicating whether any matching actors were found, but this does **not** indicate whether any goals were actually set — only shootable actors receive the goal assignment.

If the monster already has the goal as its current target, that target is cleared; `A_Look` will set it back to the goal if no real enemy comes into view.

Only applies to actors with the `MF_SHOOTABLE` flag set.

## Return value semantics caveat

The return value is true if **any actor matched the TID**, regardless of whether that actor was shootable (and thus actually received the goal). To verify that a goal was set, you must check the actor directly.

## Wiki/engine divergence: parameter name

The ZDoom Wiki lists the fourth parameter as `dontchasetarget`, but the engine source (both Zandronum and UZDoom) names it `chasegoal` (and uses opposite naming convention). The **behavior** matches the source documentation: `chasegoal=0` means "don't ignore targets in favor of goal," while `chasegoal≠0` means "chase goal instead of target." The wiki name can be confusing as it reads like the negation of what it does.

## When tid is 0

The ZDoom Wiki documents that tid=0 can be used as a thing special (monster spawn property) to make the monster walk to a goal. This does **not** happen via `LS_Thing_SetGoal`/`Thing_SetGoal()` itself: calling the ACS function with tid=0, or a mapthing's death/`Thing_Activate`-triggered special-arg path (Zandronum `src/p_map.cpp:7133`, UZDoom `src/playsim/p_map.cpp:7274`, both a distinct "run thing's own special" routine unrelated to spawn), still resolves tid=0 through the engine's TID iterator (Zandronum `FActorIterator`, UZDoom `FActorIterator` at `src/playsim/actor.h:1719-1753`), whose `Next()` explicitly returns `NULL` for id==0 (UZDoom `src/playsim/actor.h:1732-1733`), matching zero actors.

Instead, the wiki-documented tid=0 case is implemented by a **dedicated, unrelated hook** in `A_Look`/`A_LookEx` that bypasses `LS_Thing_SetGoal` and the TID iterator entirely: both actions check `self->special == Thing_SetGoal && self->args[0] == 0` (UZDoom `src/playsim/p_enemy.cpp:1922` in `A_Look`, `:2050` in `A_LookEx`; byte-identical in Zandronum `src/p_enemy.cpp:1951`, `:2099`), and if true, resolve `self->args[1]` as the PatrolPoint TID directly, set `self->goal`, clear `self->special` (so the check only fires once), and apply `self->args[2]`/`self->args[3]` as delay/chasegoal — all without going through `LS_Thing_SetGoal`. Practically this means the goal is set the first time the actor's look routine runs (so it depends on the actor's states actually calling `A_Look`/`A_LookEx`, not literally at spawn), and the delay is computed as `self->args[2] * TICRATE + maptime` (offset from the current map time), unlike `LS_Thing_SetGoal`'s own `arg2 * TICRATE` (a plain tic count, only applied if the actor currently has no target). This mechanism works identically on both Zandronum and UZDoom; it is not a fork divergence.
