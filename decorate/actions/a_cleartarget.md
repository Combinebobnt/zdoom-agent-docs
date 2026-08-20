# `A_ClearTarget` (clear actor targeting fields)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_ClearTarget` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_ClearTarget&oldid=55260) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3915-3920`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_ClearTarget)` in `src/thingdef/thingdef_codeptr.cpp` — callable from any actor's state table.

Clears the calling actor's targeting references: target, sound target, and last target. Commonly used to make a monster "give up" pursuing its target after a period of time, allowing it to return to idle searching behavior.

## Signature

```text
void A_ClearTarget()
```

## Parameters

None.

## Behavior

When called, this action clears three actor fields:

1. **`target`** — The actor's current target, normally acquired via line-of-sight checks or direct damage. Cleared to `NULL`.
2. **`LastHeard`** — The actor's sound target, set when the actor hears a noise (e.g., from a player's weapon or movement). Cleared to `NULL`.
3. **`lastenemy`** — The last enemy encountered, used by some AI logic for recent-threat awareness. Cleared to `NULL`.

After this call, the actor has no targeting pointers active. On the next state tic where an AI action (like `A_Look`) is called, the actor will resume searching for targets from scratch.

## Typical usage

A common pattern is to use `A_ClearTarget` in a "give up" branch to reset monster aggression when a target has been out of range or sight for a set duration:

```text
See:
    MONS ABCD 4 A_Chase("Melee", "Missile");
    MONS A 0 A_SetCounter(0, GetCounter(0) + 1);
    MONS A 0 A_JumpIf(GetCounter(0) >= 20, "Spawn");
    Loop;

Spawn:
    MONS A 0 A_ClearTarget;
    MONS A 10 A_Look;
    Loop;
```

(This example uses ACS-style counter functions, which may not be available in base DECORATE; a simpler approach is to use a looping state with a large duration to naturally give up pursuit without an explicit timer.)

## Network behavior

**Zandronum multiplayer:** In client mode, all three pointer fields are automatically cleared at the start of each tick, so `A_ClearTarget` has no observable effect on clients. Only the server's AI decisions drive the actual chase state; clients receive position and state updates via network replication.

## Engine-family divergence: Network behavior

**UZDoom has no client/server authority split for this action.** UZDoom's implementation (`wadsrc/static/zscript/actors/actor.zs:1169`) is a plain ZScript `A_ClearTarget()` method with no network-mode check at all — it unconditionally sets `target`, `lastheard`, and `lastenemy` to `null` on whichever peer runs it, every time. This mirrors the finding across this cohort: UZDoom's source tree has no client/server authority split anywhere (no `NETWORK_InClientMode`/`SERVERCOMMANDS_*` equivalents), unlike Zandronum's server-authoritative model described above. The three fields cleared are the same in both engines (UZDoom's `lastheard`/`lastenemy` correspond to Zandronum's `LastHeard`/`lastenemy`), so the core clearing behavior is unaffected — only the client-side auto-reclear quirk is Zandronum-specific.

## Related actions

- **`A_Look`** — Searches for targets via sight checks; called after `A_ClearTarget` to resume idle searching.
- **`A_Chase`** — The main monster chase-and-attack action, which uses `target` and may reacquire it if line-of-sight is regained. Calling `A_ClearTarget` before a later `A_Chase` call forces the monster to find a new target on the next chase decision.
- **`A_TakeTarget`** — Steals the target from another actor (opposite semantic to clearing).
