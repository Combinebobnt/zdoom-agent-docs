# `A_TransferPointer(pointer source, pointer recipient, pointer sourcefield, pointer recipientfield[, int flags])`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_TransferPointer` (retrieved 2026-07-31, oldid=38227) + verified against Zandronum source's `src/thingdef/thingdef_codeptr.cpp:282-307` and `src/actorptrselect.cpp`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_TransferPointer)` — callable from any actor's state table.

Transfers a pointer (target, master, or tracer relationship) from one actor to another, with optional safeguards against creating circular reference chains.

## Parameters

- **`pointer source`** — which actor to read a pointer FROM. Can be the calling actor itself (`AAPTR_DEFAULT`), one of its pointers (`AAPTR_TARGET`, `AAPTR_MASTER`, `AAPTR_TRACER`), or `AAPTR_NULL` (no-op if NULL).
- **`pointer recipient`** — which actor will receive the copied pointer. Resolved the same way as `source`. If NULL, the function returns without modifying anything.
- **`pointer sourcefield`** — which pointer field to copy from the source actor (`AAPTR_TARGET`, `AAPTR_MASTER`, or `AAPTR_TRACER`). Cannot be `AAPTR_DEFAULT` or `AAPTR_NULL` — using an invalid field value silently does nothing.
- **`pointer recipientfield`** — which pointer field of the recipient to overwrite. Can be `AAPTR_TARGET`, `AAPTR_MASTER`, or `AAPTR_TRACER`. **Wiki note:** The ZDoom wiki claims this parameter "cannot be DEFAULT," but Zandronum actually treats `AAPTR_DEFAULT` as "use the same field as `sourcefield`" — if `sourcefield` is `AAPTR_TARGET`, then `AAPTR_DEFAULT` also writes to `AAPTR_TARGET`, etc.
- **`int flags`** (optional, default 0) — bitfield controlling circular-reference safeguards (see below).

## Pointer types

The basic pointer types available in the source/recipient/sourcefield/recipientfield parameters are:

- `AAPTR_DEFAULT` — the calling actor itself (for source/recipient only; has special meaning for recipientfield as noted above).
- `AAPTR_NULL` — no actor (returns from the function if used as recipient; silently does nothing if used as a field).
- `AAPTR_TARGET` — the actor's target pointer.
- `AAPTR_MASTER` — the actor's master pointer.
- `AAPTR_TRACER` — the actor's tracer pointer.

Zandronum also supports additional selectors (`AAPTR_PLAYER_*`, `AAPTR_DAMAGE_*`, etc.) not covered by the ZDoom wiki, but those are not verified here.

## Safety checks

By default, the function prevents two types of circular reference problems:

1. **Target-chain safeguard** — if the recipient's target pointer would form a loop (missile targeting a missile targeting back), the assignment is nulled. Disabled by flag `PTROP_UNSAFETARGET` (value 1).
2. **Master-chain safeguard** — if the recipient's master pointer would form a loop (actor mastering an actor mastering back), the assignment is nulled. Disabled by flag `PTROP_UNSAFEMASTER` (value 2).
3. **Self-reference check** (unconditional, cannot be disabled) — if the transferred pointer would point the recipient to itself, it is always nulled regardless of flags.

## Flags

- **`PTROP_UNSAFETARGET`** (value 1) — disable the target-chain circular-reference check.
- **`PTROP_UNSAFEMASTER`** (value 2) — disable the master-chain circular-reference check.
- **`PTROP_NOSAFEGUARDS`** (value 3, not 4) — **Wiki discrepancy:** The ZDoom wiki states this value as 4 and claims "3 and 4 do the same thing." In Zandronum, `PTROP_NOSAFEGUARDS` equals `PTROP_UNSAFETARGET | PTROP_UNSAFEMASTER` (3), disabling both safeguards. Passing literal 4 (the value of `AAPTR_TRACER`) would not match either bit test and would leave both safeguards active.

## Return value

None — state flow does not branch.

## Examples

```
ACTOR WimpyImp : DoomImp
{
  States
  {
  Missile:
      TNT1 A 0 A_TransferPointer(AAPTR_DEFAULT, AAPTR_MASTER, AAPTR_TARGET, AAPTR_TARGET)
      Goto Super::Missile
  }
}
```

This imp's master acquires the same target as the imp itself. The state then continues to the parent class's Missile state.

## Related

- [Actor pointers (concept)](../concepts/actor-pointers.md) — general overview of actor pointer semantics across the engine (if documented).
- `A_CopyFriendliness` — copies hostility/friendliness status along with a pointer reference.
- `A_CheckPointer` — conditional jump on whether an actor pointer is valid.
