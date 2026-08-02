# `State A_MonsterRefire(int chance, statelabel label)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_MonsterRefire` (retrieved 2026-08-01, oldid=53989) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:4933-4956`.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_MonsterRefire)` — applies to any monster or actor with a state table.

Checks whether a monster should abort its attack sequence and transition to a different state. This function is commonly used to give monsters a chance to lose sight of their target and stop attacking, or to break off an attack if the target is dead or no longer visible.

## Parameters

- **`int chance`** — Probability (in the 0–255 range) that the actor will **continue attacking** if its target is dead or out of sight. Higher values = higher chance to persist. For example, `chance=128` gives a 50% chance to continue attacking when conditions would normally abort.
- **`statelabel label`** — Name of the state sequence to jump to if the attack is aborted (typically `"See"` to return to idle searching, or `"Spawn"` to return to spawning state).

## Behavior

1. Calls `A_FaceTarget` to adjust the monster's angle toward its target.
2. Checks a random probability: if a random value 0–255 is **less than** `chance`, the function returns without jumping (the actor continues its current state sequence, typically looping back to attack again).
3. If the probability check does not cause an early return, the function jumps to `label` if **any** of these conditions are true:
   - No target exists (target pointer is null).
   - The monster hit an ally (checked via `P_HitFriend()`).
   - The target is dead (`target->health <= 0`).
   - The monster cannot see the target (line-of-sight check via `P_CheckSight()` with flags `SF_SEEPASTBLOCKEVERYTHING|SF_SEEPASTSHOOTABLELINES`).

## Network behavior

- **Server-side only** in multiplayer: the function returns early if called in client mode on a non-client-handled actor. When a jump is triggered, the server sends a client update to ensure state synchronization across the network.

## Usage note

This function differs from `A_FaceTarget` + `A_JumpIf` in that it pairs the target facing with a unified check for multiple abort conditions. Common specializations include `A_CPosRefire`, `A_CrusaderRefire`, `A_SpidRefire`, and `A_SentinelRefire`, which use preset `chance` values and always jump to `"See"` rather than accepting parameters.

## Example

```decorate
Class SuperZombie : ZombieMan
{
	States
	{
	Missile:
		POSS E 10 A_FaceTarget;
	MissileLoop:
		POSS FE 2 Bright A_PosAttack;
		POSS F 1 A_MonsterRefire(128, "See");  // 50% chance to abort if target is out of sight
		loop;
	}
}
```

In this example, the monster attacks twice per loop iteration. On the third state line, `A_MonsterRefire(128, "See")` gives a 50% chance to either continue the attack loop or jump back to the `"See"` state (idle searching) if the target is dead, out of sight, or an ally.
