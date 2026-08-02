# Thing_SetGoal

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki (Thing_SetGoal), verified against Zandronum source, 2026-07-29
**Bucket:** action special 229, `p_lnspec.cpp` `FUNC(LS_Thing_SetGoal)`

**Syntax:** `Thing_SetGoal(tid, goal, delay, chasegoal)`

**Returns:** int (nonzero if any actors matched `tid`, zero otherwise)

## Parameters

- **tid** (int): Thing ID of the monster(s) to send to a patrol point. Only applies to shootable actors (those with the `MF_SHOOTABLE` flag).
- **goal** (int): Thing ID of the destination. Must be a `PatrolPoint` actor. If a non-PatrolPoint actor holds this TID, the goal is silently cleared instead.
- **delay** (int): Delay in seconds before the monster starts moving. Internally converted to tics: `reactiontime = delay * TICRATE`. Only applied if the monster has no current target.
- **chasegoal** (int): Controls whether the monster prefers its goal over any potential target. If zero: walk to target if one exists, only walk to goal if no target. If non-zero: walk to goal instead of target (sets `MF5_CHASEGOAL` flag).

## Behavior

Sets a goal patrol point for one or more monsters, causing them to begin path-following. The function returns a boolean indicating whether any matching actors were found, but this does **not** indicate whether any goals were actually set — only shootable actors receive the goal assignment.

If the monster already has the goal as its current target, that target is cleared; `A_Look` will set it back to the goal if no real enemy comes into view.

Only applies to actors with the `MF_SHOOTABLE` flag set.

## Return value semantics caveat

The return value is true if **any actor matched the TID**, regardless of whether that actor was shootable (and thus actually received the goal). To verify that a goal was set, you must check the actor directly.

## Wiki name vs. source divergence note

The ZDoom Wiki lists the fourth parameter as `dontchasetarget`, but the Zandronum source code names it `chasegoal` (and uses opposite naming convention). The **behavior** matches the source documentation: `chasegoal=0` means "don't ignore targets in favor of goal," while `chasegoal≠0` means "chase goal instead of target." The wiki name can be confusing as it reads like the negation of what it does.

## When tid is 0

The wiki notes that tid=0 can be used as a monster's *thing special* to make the monster walk to a goal on spawn. This is handled at the thing-special call site, not within this function — the engine substitutes the activator's TID. This behavior was not traced in the implementation of `LS_Thing_SetGoal` itself.
