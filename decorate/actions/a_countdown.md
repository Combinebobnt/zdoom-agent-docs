# `void A_Countdown()`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_Countdown` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_Countdown&oldid=47867) + verified against the Zandronum source's `src/g_strife/a_strifestuff.cpp:621-637`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_Countdown)` in `src/g_strife/a_strifestuff.cpp` — callable from any actor's state table (defined on `AActor`).

Decrements the calling actor's `ReactionTime` property once per call. When `ReactionTime` reaches 0 or below, explodes and destroys the calling actor.

## Signature

```text
void A_Countdown()
```

## Parameters

None.

## Behavior

When called, this action decrements the `reactiontime` field by 1. If the result is 0 or less:

1. Calls `P_ExplodeMissile()` to explode the actor (creating an explosion effect at its current position).
2. Clears the `MF_SKULLFLY` flag from the actor.

If `reactiontime` is still above 0 after the decrement, the actor continues normally until the next call to `A_Countdown`.

## Intended usage

This function is **intended for use with missile-type actors** — projectiles with the `+MISSILE` flag. The wiki explicitly warns that using it with other actor types is considered "undefined behavior" and may produce unwanted side effects. The typical usage pattern is to set the `ReactionTime` property to the desired lifetime in tics, then call `A_Countdown` every frame in the `Spawn` state to count down to zero.

## Example

A missile that follows its target (`A_Tracer`) for 25 tics, then explodes:

```text
actor RevenantTracer2 : RevenantTracer
{
    ReactionTime 25

    States
    {
    Spawn:
        FATB AB 2 Bright A_Tracer
        FATB A 0 A_Countdown
        Loop
    }
}
```

In this example, each loop advances two frames with `A_Tracer` (4 tics total), then calls `A_Countdown` once. Since `ReactionTime` starts at 25 and decrements once per loop, the missile will loop roughly 25 times before exploding.

## Network behavior

**Zandronum multiplayer:** The server handles this action exclusively. On network clients, the action returns without effect if the actor is not marked as client-side-only. After the explosion occurs on the server, the destruction is synchronized to all clients via the normal actor-death replication.

## Engine-family divergence: Network behavior

**UZDoom has no client/server authority split for this action.** UZDoom's implementation (`wadsrc/static/zscript/actors/strife/strifefunctions.zs`) is a plain ZScript `extend class Actor` method with no network-mode check at all — it decrements `reactiontime` and calls `ExplodeMissile()` unconditionally on whichever peer runs it, every time. This mirrors the finding across this cohort: UZDoom's source tree has no client/server authority split anywhere (no `NETWORK_InClientMode`/`SERVERCOMMANDS_*` equivalents), unlike Zandronum's server-authoritative model described above.

## Related actions and properties

- **`ReactionTime`** — the property decremented by this action. Can be set in the actor definition or modified at runtime via `A_SetReactionTime` or similar.
- **`A_CountdownArg`** — a more general version that counts down an arbitrary `args[n]` field instead of `ReactionTime`.
