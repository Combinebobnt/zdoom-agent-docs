# `A_DeQueueCorpse` (remove actor from corpse queue)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_DeQueueCorpse` (retrieved 2026-08-01, oldid=32299) + verified against the Zandronum source's `src/g_shared/a_action.cpp:455`.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_DeQueueCorpse)` in `src/g_shared/a_action.cpp` — callable from any actor's state table.

Removes the calling actor from the engine's corpse queue. Queued corpses are limited by the `sv_corpsequeuesize` console variable (default: 64) — when this limit is reached, the oldest corpse in the queue is destroyed to make room for a new one. This action is typically used in a resurrection/raise state to prevent a resurrecting corpse from occupying a queue slot.

## Signature

```
void A_DeQueueCorpse()
```

## Parameters

None.

## Behavior

When called, this action searches the active corpse queue for an entry pointing to the calling actor and removes it. If found, the queue slot is freed; if the actor was never queued, the function silently does nothing and returns.

**Critical implementation detail:** The queue system manages corpse cleanup asymmetrically. When an actor is queued via `A_QueueCorpse`, it is stored in a `DCorpsePointer` object. When `A_DeQueueCorpse` is called, it finds that pointer and nullifies the `Corpse` reference *before* destroying the queue entry — this prevents the corpse actor itself from being destroyed. In contrast, when the queue reaches capacity, the oldest entry is destroyed *with* the corpse reference still set, which destroys the corpse actor itself. This asymmetry is why the action exists: it allows a resurrecting monster to free its queue slot without being destroyed.

## Typical usage

Place this action in a monster's `Raise` state or any other state where resurrection is about to occur, before the actor transitions back to its normal `Spawn` or `See` state:

```
Raise:
    MONS A 0 A_DeQueueCorpse;
    MONS ABCD 5 A_Raise;
    MONS A 0 A_Look;
    Goto Spawn;
```

## The corpse queue mechanism

The `sv_corpsequeuesize` cvar is a server-replicated integer (`CUSTOM_CVAR`, default 64). When it is greater than 0, actors can be added to the queue via `A_QueueCorpse`. The queue operates as a first-in-first-out list managed by thinker objects. If an actor calls `A_QueueCorpse` multiple times without calling `A_DeQueueCorpse`, each call adds a new queue entry — a single `A_DeQueueCorpse` only removes the first match found.

## Network behavior and client-side caveat

The implementation does not include explicit network guards. Whether corpse queue operations affect both server and client behavior, or are server-authoritative only, is unverified — state code execution is client-side, but the corpse queue's own replication has not been traced through the full server/client boundary.

## Related actions

- **`A_QueueCorpse`** — Adds the calling actor to the corpse queue. The two actions form a queue-management pair: queue on death, dequeue on resurrection.

## See also

- [`sv_corpsequeuesize`](../../console/inventory/cvars.md) — the cvar controlling the queue's maximum size.
