# `State A_MonsterRefire(int chance, statelabel label)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_MonsterRefire` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_MonsterRefire&oldid=53989) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:4933-4956`, `DoJump` (`thingdef_codeptr.cpp:695-753`), and the hardcoded refire functions (`src/g_doom/a_possessed.cpp:138-163`, `src/g_doom/a_spidermaster.cpp:14-39`, `src/g_strife/a_sentinel.cpp:89-113`, `src/g_strife/a_crusader.cpp:100-116`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_MonsterRefire)` (`src/thingdef/thingdef_codeptr.cpp:4933`) — applies to any monster or actor with a state table.

Checks whether a monster should abort its attack sequence and transition to a different state. This function is commonly used to give monsters a chance to lose sight of their target and stop attacking, or to break off an attack if the target is dead or no longer visible.

## Parameters

- **`int chance`** — Probability (in the 0–255 range) that the actor will **continue attacking** if its target is dead or out of sight. Higher values = higher chance to persist. For example, `chance=128` gives a 50% chance to continue attacking when conditions would normally abort.
- **`statelabel label`** — Name of the state sequence to jump to if the attack is aborted (typically `"See"` to go back to chasing, or `"Spawn"` to return to the idle state).

## Behavior

1. Calls `A_FaceTarget` to adjust the monster's angle toward its target.
2. Checks a random probability: if a random value 0–255 is **less than** `chance`, the function returns without jumping (the actor continues its current state sequence, typically looping back to attack again).
3. If the probability check does not cause an early return, the function jumps to `label` if **any** of these conditions are true:
   - No target exists (target pointer is null).
   - The monster hit an ally (checked via `P_HitFriend()`).
   - The target is dead (`target->health <= 0`).
   - The monster cannot see the target (line-of-sight check via `P_CheckSight()` with flags `SF_SEEPASTBLOCKEVERYTHING|SF_SEEPASTSHOOTABLELINES`).

## Network behavior

- **Server-side only** in multiplayer: the function returns before doing anything (including `A_FaceTarget`) when called in client mode on an actor that isn't client-handled.
- The jump passes `CLIENTUPDATE_FRAME`. When it fires from the actor's own state on the server, clients are sent the new frame (`SERVERCOMMANDS_SetThingFrame`), since clients don't know the monster's target and can't run the checks themselves. A jump taken inside a CustomInventory state chain sends nothing.

## Zandronum-specific: server-authoritative execution

UZDoom has no client/server authority split for this function at all. UZDoom's implementation (`src/playsim/p_actionfunctions.cpp`, `DEFINE_ACTION_FUNCTION(AActor, A_MonsterRefire)`) has no equivalent of Zandronum's `NETWORK_InClientModeAndActorNotClientHandled()` early-return guard, and no `CLIENTUPDATE_FRAME`-style update is sent when the state jump fires. UZDoom runs the full sequence — `A_FaceTarget`, the `pr_monsterrefire()` probability check, then the target/ally/health/sight checks — unconditionally on whichever side calls it, with no per-client/per-server distinction. The "Network behavior" section above describes Zandronum-only behavior; UZDoom performs no equivalent synchronization step because it has no server-authoritative/client-prediction split for actor state to synchronize in the first place.

## Usage note

This function differs from `A_FaceTarget` + `A_JumpIf` in that it pairs the target facing with a unified check for multiple abort conditions. `A_CPosRefire` and `A_SpidRefire` are hardcoded near-equivalents with a fixed chance (40 and 10) that always jump to the actor's See state. `A_SentinelRefire` is similar but adds a second random abort roll and a missile/melee-range check. `A_CrusaderRefire` has no probability roll, no friend check and no target facing: it only jumps to See when the target is missing, dead or out of sight.

## Example

```decorate
Actor SuperZombie : ZombieMan
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

In this example, the monster attacks twice per loop iteration. On the third state line, `A_MonsterRefire(128, "See")` gives a 50% chance to either continue the attack loop or jump back to the `"See"` state (chasing) if there is no target, the target is dead or out of sight, or a friendly actor is in the line of fire.
