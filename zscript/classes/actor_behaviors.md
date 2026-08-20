# Actor behavior management methods

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki "ZScript actor functions" (retrieved 2026-08-03, https://zdoom.org/w/index.php?title=ZScript_actor_functions&oldid=54768) + verified against UZDoom stdlib declaration in `wadsrc/static/zscript/actors/actor.zs`; re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — no behavioral drift found (the pull's only change to this file was a mechanical license-header rewrite; the `Behavior` class and all six Actor behavior-management methods are byte-for-byte unchanged).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** ZScript stdlib (actor.zs; native method declarations for behavior management).

Behaviors are a plugin-like system allowing modular state/logic management. An `Actor` can have multiple behavior instances attached to it, each running their own virtual methods (Initialize, Reinitialize, Tick, TransferredOwner). This subsection documents the Actor methods for managing behaviors. For the Behavior class itself (which defines the virtual interface and Owner/Level properties), see the ZScript stdlib's `wadsrc/static/zscript/actors/actor.zs`.

## Method signatures

### `clearscope Behavior FindBehavior(class<Behavior> type) const`

Retrieves the first behavior of the specified type attached to this actor, or null if not found.

**Parameters:**
- `type`: The behavior class to search for (exact match; child classes will not match).

**Returns:** The behavior instance if found, or null.

### `bool RemoveBehavior(class<Behavior> type)`

Removes the first behavior of the specified type from this actor.

**Parameters:**
- `type`: The behavior class to remove (exact match; child classes will not be removed).

**Returns:** true if a behavior was removed; false if no behavior of that type was found.

### `Behavior AddBehavior(class<Behavior> type)`

Adds a new behavior of the specified type to this actor, or returns the existing one if already present.

When adding a new behavior:
- Calls the new behavior's `Initialize()` virtual method.

When the behavior already exists:
- Calls the existing behavior's `Reinitialize()` virtual method instead of creating a duplicate.

**Parameters:**
- `type`: The behavior class to add.

**Returns:** The behavior instance (newly created or already existing), or `null` if `type` is abstract or is not actually a `Behavior` subclass, or if the `Initialize()`/`Reinitialize()` call left the behavior in an invalid state (destroyed itself, or reassigned its own `Owner`) — in the latter case the behavior is removed before `null` is returned.

### `void TickBehaviors()`

Calls the `Tick()` virtual method on all behaviors attached to this actor. Any behavior found to be invalid (destroyed, or no longer owned by this actor) when its turn comes up is removed instead of ticked.

This is called automatically from the base `Actor.Tick()`, but only while the actor is not frozen (`isFrozen()` returning true, e.g. during certain time-freeze effects, suppresses the automatic call). It can be manually called from a custom actor `Tick()` override if you want more control over when behaviors update. If an actor has a full `Tick()` override that skips the parent call, call this manually to ensure behaviors receive their tick.

### `void ClearBehaviors(class<Behavior> type = null)`

Removes behaviors from this actor.

**Parameters:**
- `type`: If specified (not null), removes any behavior that **is** this type or a subclass of it (unlike `FindBehavior`/`RemoveBehavior`, which only match the exact class). If null (default), removes all behaviors from the actor unconditionally.

**Behavior cleanup:** When clearing with `type == null`, any remaining behaviors after cleanup are automatically destroyed. This is useful for unconditionally wiping all actor state on actor destruction.

### `void MoveBehaviors(Actor from)`

Transfers all behaviors from another actor to this actor.

**This actor's own existing behaviors are destroyed first** (as if `ClearBehaviors()` had been called on it) before the `from` actor's behaviors are moved in — this is a replace, not a merge. If `from` is this same actor, the call is a no-op (no behaviors are cleared or transferred). If the two actors differ in client-side status (one is a client-side actor and the other is not), the call aborts with a fatal VM error — behaviors cannot be moved between a client-side actor and a world actor.

When a behavior is transferred:
- The behavior's `TransferredOwner(Actor oldOwner)` virtual method is called with the original owner (the `from` actor).
- The transferred behavior's `Owner` property is updated to point to this actor.
- As with `TickBehaviors`, any behavior found invalid at this point (or left invalid by `TransferredOwner()`) is removed instead of transferred.

**Parameters:**
- `from`: The actor whose behaviors to transfer. Its behavior list becomes empty after the call.

## Example usage

```zscript
// Add a behavior to an actor
Behavior b = myActor.AddBehavior(MyCustomBehavior);

// Tick behaviors manually in a custom Tick override
override void Tick() {
  // custom tick logic...
  TickBehaviors(); // manually update all behaviors
  // more custom logic...
}

// Find and remove a behavior
if (myActor.RemoveBehavior(OldBehavior)) {
  // successfully removed
}

// Transfer all behaviors to another actor
// (destinationActor's own existing behaviors are destroyed first, not merged with)
destinationActor.MoveBehaviors(sourceActor);
// sourceActor now has no behaviors

// Clear all behaviors
myActor.ClearBehaviors();
```

## Engine-family divergence

Behaviors are a UZDoom/GZDoom-family ZScript feature and do not exist in Zandronum. This system requires UZDoom 4.15.1 or later (the `version("4.15.1")` qualifier appears on both the Behavior class and these actor methods in the stdlib).
