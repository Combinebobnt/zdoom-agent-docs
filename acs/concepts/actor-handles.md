# Holding a handle on an actor that has no unique TID

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-25); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** written from Zandronum `src/dobject.h:291-298` (`GC::ReadBarrier`) and
`src/actor.h:1030`/`:1048`/`:1049` (`target`/`tracer`/`master` declared `TObjPtr<AActor>`), plus
`AActor::Die` in `src/p_interaction.cpp` and `AActor::AddToHash` in `src/p_mobj.cpp` (both cited by
symbol rather than line: they have moved since `28f736fb3`, while the two files cited by line are
byte-identical at it). Every claim here was then read on UZDoom too, not assumed to carry over:
`src/common/objects/dobjgc.h:137` (`GC::ReadBarrier`, behaviourally identical),
`src/playsim/actor.h:1252`/`:1267`/`:1268` (same three fields, as `TObjPtr<AActor*>`),
`src/playsim/p_mobj.cpp:3544` (same tid-0 short-circuit in `AddToHash`), and the same
`if (diestate != NULL) ... else Destroy()` structure in `src/playsim/p_interaction.cpp`. No wiki
page covers this technique.

ACS/BCS can only name an actor by TID, but plenty of actors either share a TID with a whole
population or carry none at all. This page is the general answer to "how do I remember *one
specific* actor across script invocations when I cannot give it a TID of its own": park a pointer
to it on a second actor that *does* have a stable TID, and read it back through a pointer selector.

This is a technique page. The functions it composes are documented separately and are not restated
here: [SetActivator](../functions/setactivator.md), [SetPointer](../functions/setpointer.md),
[Thing_ChangeTid](../functions/thing_changetid.md), [UniqueTid](../functions/uniquetid.md), and
[Actor pointer selectors](actor-pointers.md) for how `AAPTR_*` resolution works at all.

## The addressing problem

Three facts combine into the problem:

- ACS/BCS has no pointer *type* and no `target`/`master`/`tracer` field-access syntax. Every actor
  relationship is resolved at call time from an `AAPTR_*` selector (see
  [Actor pointer selectors](actor-pointers.md)).
- A TID is not an identity. Several actors routinely share one, and the functions that act on a TID
  either pick an arbitrary member or act on all of them.
- Assigning a unique TID is destructive. An actor carries exactly one TID, so tagging it with
  [UniqueTid](../functions/uniquetid.md) overwrites whatever tag it already had, and anything that
  addressed it by the old tag stops finding it.

So "give the actor a unique TID and remember the number" is not available whenever the actor's
existing TID is load-bearing. What *is* available is a second actor's pointer fields, used as
storage.

## The anchor

Spawn one persistent, motionless actor per slot that needs to remember something, give *it* a
stable unique TID, and store the remembered actor in one of its pointer fields. Reading the handle
back is a single hop, after which the activator **is** the remembered actor, so its position,
health and inventory read live:

```acs
// ANCHOR_TID is this slot's own permanent marker, not the remembered actor's.
if (SetActivator(ANCHOR_TID, AAPTR_TRACER)
    && GetActorProperty(0, APROP_Health) > 0)
{
    // the activator is now the remembered actor
}
```

`AAPTR_TRACER` is usually the right field to borrow. `tracer` carries no "this is my enemy"
semantics the way `target` does, nothing in the engine's AI consults it on an inert marker, and
unlike `target`/`master` it has no assignment loop guard to work around (see
[Actor pointer selectors](actor-pointers.md)'s loop-guard section). Use `target` or `master` only
if something else already needs `tracer`.

**Both arms of that `if` are load-bearing**, for reasons that are not interchangeable - see
"Lifetime" below. `SetActivator` also clobbers the activator on failure with no rollback, so
restore it on every path out, not just the success arm.

## Establishing the pointer: the scratch retag

[SetPointer](../functions/setpointer.md) writes **the activator's** own fields. So to point the
anchor at the remembered actor, the anchor has to be the activator, which means the remembered
actor has to be reachable *by TID* for a few instructions. Nothing in ACS sets some *other* actor's
pointer to the activator, so a brief scratch tag is the way in:

```acs
// Runs with the to-be-remembered actor as activator. No yield anywhere in this block.
int old_tid = ActivatorTID();

Thing_ChangeTID(0, SCRATCH_TID);
if (ActivatorTID() != SCRATCH_TID)
{
    return false;   // actor is already being destroyed; the retag silently did nothing
}

bool ok = false;
if (SetActivator(ANCHOR_TID)) { ok = SetPointer(AAPTR_TRACER, SCRATCH_TID); }

if (!SetActivator(SCRATCH_TID))
{
    Thing_ChangeTID(SCRATCH_TID, old_tid);   // restore by TID; activator is gone
    return false;
}
Thing_ChangeTID(0, old_tid);
return ok;
```

Four things about this block are not optional:

- **It must not yield.** ACS is cooperative: a script runs to completion or to its next yield, so
  nothing can observe or steal the scratch TID mid-window. A `Delay`, a `Suspend`, or a nested
  `ACS_Named*` call reintroduces re-entrancy and is the only way to break it.
  [SetActivator](../functions/setactivator.md) documents the same requirement for the
  spawn-then-retag pattern; this is that guarantee applied to an actor that already exists.
- **Confirm the retag rather than assuming it.** `Thing_ChangeTid` silently no-ops on an actor
  already flagged for destruction and still returns true, so its return value proves nothing - read
  `ActivatorTID()` back instead. See [Thing_ChangeTid](../functions/thing_changetid.md).
- **Use a scratch TID reserved for this, not a general-purpose temporary.** A TID that some other
  system retags or removes wholesale will either mis-handle or delete an actor that is transiently
  wearing it.
- **`old_tid == 0` round-trips correctly.** An actor with no TID is common (map-placed and
  script-spawned actors often carry none), and restoring `0` is safe because `AActor::AddToHash`
  short-circuits on tid 0 rather than inserting a bogus hash entry.

The failure path deserves its own note. If the hop back to the scratch TID fails, the activator is
lost *and* `old_tid` may legitimately be `0`, which leaves that actor unaddressable by TID
entirely - every later `GetActorProperty(0, ...)` on it reads `0`. That outcome is not the same as
"the operation failed", and a caller that collapses the two will go on to read properties off the
wrong actor. Distinguish it.

## Lifetime: destroyed is not the same as dead

This is the part the technique actually depends on, and the part that looks redundant and invites
being "simplified" away later.

`target`, `tracer` and `master` are not raw pointers. They are GC-managed handles (`TObjPtr`), and
dereferencing one runs a read barrier that checks whether the referenced object is flagged for
destruction. If it is, the barrier yields null **and writes that null back through the field**, so
the stale handle heals itself in passing. No watchdog script, no generation counter, and no
periodic validity sweep is needed to detect a destroyed actor: the hop simply fails.

What the barrier does *not* do is notice that an actor died. Death and destruction are separate
events:

- An actor that enters a death state is still a live object. `AActor::Die` resolves a death state
  first and only reaches its `Destroy()` call in the `else` arm of `if (diestate != NULL)`, i.e.
  when no death state resolved at all. Anything that does enter one remains a perfectly valid
  object with `health <= 0`.
- So a handle to a corpse **still resolves**. `SetActivator(ANCHOR_TID, AAPTR_TRACER)` succeeds and
  hands you a dead actor.

Hence the two-arm guard: the pointer check catches destruction, the health check catches death, and
neither substitutes for the other. Drop the health check and the handle silently keeps naming a
corpse; drop the null check and you dereference through a field that the barrier has already
nulled. Both failure modes are quiet - the code keeps running and simply acts on the wrong thing.

Note also that `AActor::Die` overwrites the dying actor's own `target` with whatever killed it, so
a corpse's `target` is its killer, not whatever it was chasing (see
[SetActivatorToTarget](../functions/setactivatortotarget.md)). If you borrowed `target` rather than
`tracer` for your anchor, that rewrite does not touch the *anchor's* field - the anchor is not the
one dying - but it does mean a handle read *out of* a dead actor means something different than the
same read a tic earlier. See [Damage retaliation: what writes a monster's `target` during
gameplay](../../shared/concepts/monster-target-retaliation.md) for the full write path this
overwrite is one part of, and what gates it *before* death.

## When the anchor has to move, and when it does not

An anchor that is only ever asked "who are you pointing at" never needs to move. It runs no states,
ticks nothing, and its own coordinates are never read, so parking it anywhere at spawn is fine.

An anchor only needs to physically follow the actor it names when something reads the **anchor's
own** position - drawing a marker on it, measuring distance to it, or using it as a sound origin.
That is when a per-tic `A_Warp` loop (or equivalent) earns its cost, and it is a real cost: a
ticking actor per handle, and a DECORATE class to host the loop.

Deciding which case you are in is worth doing explicitly, because the warping form is the one most
existing examples show, and copying it when nothing reads the anchor's position buys a per-tic
thinker for nothing.

## Hazards

- **Re-pointing is not free on a server.** Establishing a handle retags an actor twice, and a
  successful retag broadcasts to clients on a Zandronum server (see
  [Thing_ChangeTid](../functions/thing_changetid.md)). Refreshing a handle that has not actually
  changed should therefore be a no-op, not a re-establish. Testing "is the anchor already pointing
  at me" with `IsPointerEqual` costs one call and no activator hop - see
  [IsPointerEqual](../functions/ispointerequal.md).
- **The anchor is a real actor and needs a lifecycle.** Something has to remove it when its slot
  goes away, or it leaks. Conversely, destroying and respawning anchors on every change churns
  packets and reintroduces exactly the race a permanent anchor avoids.
- **A cleared handle and a null pointer are different states.** If your code can invalidate a
  handle for its own reasons (the slot's owner died, the logic changed its mind), keep that in a
  separate flag rather than inferring it from the pointer, and test the flag first. Clearing a
  claim without nulling the pointer is a legitimate design, but then the pointer alone no longer
  answers "is this handle live".
- **Do not point an anchor at an actor you must never act on.** The anchor's pointer field is the
  only record of the choice, so whatever filter decides eligibility has to run before the pointer
  is written, not after it is read.
