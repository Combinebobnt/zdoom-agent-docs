# `void A_QueueCorpse()`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_QueueCorpse` (retrieved 2026-08-01, oldid=32300) + verified against the Zandronum source's `src/g_shared/a_action.cpp:448-451` and UZDoom's `src/playsim/a_action.cpp:94-99`.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_QueueCorpse)` in `src/g_shared/a_action.cpp` — callable from any actor's state table.

Adds the calling actor to the engine's corpse queue, subject to a configurable size limit set by the `sv_corpsequeuesize` console variable (default: 64). When this limit is reached, the oldest corpse in the queue is destroyed to make room. This action is typically placed in a monster's death state to enable persistent corpse cleanup for engines or mods that produce many dead bodies (Hexen uses it extensively for this purpose).

## Signature

```
void A_QueueCorpse()
```

## Parameters

None.

## Behavior

When called, this action checks whether the corpse queue is enabled (`sv_corpsequeuesize > 0`). If disabled, the function silently does nothing and returns; no queue entry is created. If enabled, a new `DCorpsePointer` thinker object is created to track the corpse actor.

**The actual queue management happens in the `DCorpsePointer` constructor**, not in `A_QueueCorpse`'s own body (which is two lines). When a pointer is created:

- If the queue is already at capacity, the **oldest entry is destroyed, which also destroys its corpse actor** (the corpse reference is still set at destruction time).
- A single call to `A_QueueCorpse` evicts at most one corpse to make room — if an actor calls this multiple times, each call adds a new queue entry, and dequeuing a single entry via `A_DeQueueCorpse` removes only the first match found.

The queue itself is a first-in-first-out list of `DCorpsePointer` thinkers. A `Count` field on the oldest (first) entry in the list tracks the total number of corpses currently queued; new entries do not initialize their own count (they inherit it from the rotation of the oldest entry as corpses are queued and evicted).

**Critical asymmetry with overflow:** When an actor calls `A_DeQueueCorpse`, the queue system **nullifies the `Corpse` reference *before* destroying the pointer**, which prevents the actor from being destroyed — this is the entire reason that action exists, for resurrection use cases. In contrast, overflow eviction destroys the corpse actor by keeping the reference set at destruction time. See `A_DeQueueCorpse` for the full details of this mechanism.

## Typical usage

Place this action in the death state of a monster that should participate in corpse queue management:

```
Death:
    MONS A 0 A_QueueCorpse;
    MONS ABCD 5;
    MONS A -1 A_Fall;
    Stop;
```

## The corpse queue mechanism and `sv_corpsequeuesize`

The queue is controlled by the `sv_corpsequeuesize` server cvar, a `CUSTOM_CVAR` with default value 64:

- **`sv_corpsequeuesize > 0`**: the queue is enabled and limited to N corpses. Calling `A_QueueCorpse` adds an actor to the queue; if the queue reaches capacity, the oldest corpse is destroyed.
- **`sv_corpsequeuesize <= 0`**: the queue is disabled. Calls to `A_QueueCorpse` are silent no-ops — no queue entry is created, and no corpse will ever be automatically evicted (all corpses persist indefinitely). This is the behavior referenced in historical commit messages as "setting CVAR to -1 disables corpse queuing completely."
- **Lowering the cvar at runtime** (via console or server script) triggers the `CUSTOM_CVAR` callback, which trims the queue to fit the new size in a `while` loop — a different trimming behavior than the single-eviction-per-call performed when a new corpse is queued normally.

The wiki's description "limited to a specific amount" correctly captures this, though the action's own implementation shows it only checks `> 0`, not a specific numeric limit — the limit check happens at queue-add time inside the `DCorpsePointer` constructor.

## Related actions

- **`A_DeQueueCorpse`** — Removes the calling actor from the corpse queue without destroying it (used for resurrection). The two actions form a queue-management pair: queue on death, dequeue on resurrection.

## Hexen usage

Hexen relies heavily on corpse queuing to prevent dead monster accumulation. The following built-in Hexen actors use `A_QueueCorpse` in their death states:

- Bishop (`bishop.txt:70`)
- Demons (various: `demons.txt:50`, `demons.txt:112`, `demons.txt:129`, `demons.txt:144`, `demons.txt:161`, `demons.txt:178`, and more)

This is the primary use case the wiki refers to: "Hexen uses this to limit the amount of dead items in the game."

## Engine availability

This action is available in both Zandronum and UZDoom/GZDoom-family engines — a portable action across the ZDoom-family.

## See also

- **`A_DeQueueCorpse`** — The complement action for removing an actor from the queue.
- Zandronum console variables (`sv_corpsequeuesize`) for the related cvar documentation (if present).
