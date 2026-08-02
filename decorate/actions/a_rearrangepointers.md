# `A_RearrangePointers` (actor pointer reassignment)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_RearrangePointers` (retrieved 2026-08-01, oldid=50165) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:203-263`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_RearrangePointers)` in `src/thingdef/thingdef_codeptr.cpp`.

Reassigns the calling actor's `target`, `master`, and `tracer` pointers to any of the actor's current pointers or to `NULL`, with optional safeguards against infinite pointer chains.

## Signature

```
void A_RearrangePointers(int target, int master, int tracer, int flags = 0)
```

## Parameters

### `target` (int — AAPTR value)

The new value for the calling actor's `target` field. Must be one of the `AAPTR_*` constants (see "Pointer values" below). The actor's original `target` is fetched *before* any modifications, so all three parameters see the pre-modification state.

### `master` (int — AAPTR value)

The new value for the calling actor's `master` field. See `target` for fetch-order semantics.

### `tracer` (int — AAPTR value)

The new value for the calling actor's `tracer` field. See `target` for fetch-order semantics. Note that unlike `target` and `master`, no loop-verification functions are called on `tracer` changes, because the engine never follows a `tracer` chain.

### `flags` (int, optional)

Bitfield controlling loop-safeguard behavior. Flags are combined using `|`. Default is 0 (safeguards enabled).

## Pointer values

These constants (AAPTR_*) control what each pointer field is set to. All are fetched from the actor's current pointers *before* any modifications, so the fetch order does not matter and independent rearrangements are possible (e.g., assigning the same source pointer to multiple fields).

- **`AAPTR_DEFAULT` (0)** — No change. The corresponding field (target/master/tracer) is left unchanged.

- **`AAPTR_NULL` (0x1)** — Set to `NULL` (no actor).

- **`AAPTR_TARGET` (0x2)** — Set to the actor's current `target` (if any; otherwise `NULL`).

- **`AAPTR_MASTER` (0x4)** — Set to the actor's current `master` (if any; otherwise `NULL`).

- **`AAPTR_TRACER` (0x8)** — Set to the actor's current `tracer` (if any; otherwise `NULL`).

**Important note:** The semantics of `target`/`master`/`tracer` vary by actor type. For example, in missiles, `target` points to the owner; in regular monsters, `target` points to the current enemy. Always verify actor-type semantics before assuming pointer meanings.

## Safeguards and flags

By default, `A_RearrangePointers` prevents **infinite pointer chains** by nullifying assignments that would create circular references:

- **For `target`**: An assignment is nullified (target set to `NULL`) if the actor being assigned is a missile and the assignment would create an infinite loop in the target chain (e.g., A → B → A). Checked by `VerifyTargetChain()` in the Zandronum source (`src/actorptrselect.cpp`).

- **For `master`**: An assignment is nullified if it would create an infinite loop in the master chain (checked for all actors, not just missiles). Checked by `VerifyMasterChain()`.

- **For `tracer`**: No verification is performed. The engine does not traverse tracer chains, so infinite loops are not a concern.

The following flags allow disabling these safeguards:

- **`PTROP_UNSAFETARGET` (1)** — Disable loop-checking for `target` assignments. Allows missiles to form infinite target chains (e.g., A → B → A).

- **`PTROP_UNSAFEMASTER` (2)** — Disable loop-checking for `master` assignments. Allows any actor to form infinite master chains.

- **`PTROP_NOSAFEGUARDS` (3)** — Equivalent to `PTROP_UNSAFETARGET | PTROP_UNSAFEMASTER`. Disables all safeguards.

**Caution:** Infinite pointer chains can cause engine hangs or crashes if code attempts to traverse them. Only disable safeguards if you fully understand the actor relationships you are creating and can guarantee external code will never traverse the chains.

## Caveat: A_ClearTarget

Setting `target` to `AAPTR_NULL` using `A_RearrangePointers` *only* sets the `target` field to `NULL`. It does **not** perform the additional cleanup that `A_ClearTarget` does (e.g., clearing related targeting fields or triggering related state changes). If you need full target clearing, use `A_ClearTarget` instead.

## Example (Zandronum DECORATE)

```
ACTOR AmnesiacImp : DoomImp
{
  States
  {
  See:
    TROO A 0 A_Jump(252, 2)
    TROO A 0 A_RearrangePointers(AAPTR_NULL, AAPTR_NULL, AAPTR_DEFAULT)
    TROO AABBCCDD 3 A_Chase
    Loop
  }
}
```

This imp has a 4/256 chance per state to "forget" its current target and master, while leaving its tracer unchanged. On the 4-in-256 chance, it jumps to the second `TROO A 0` line and clears both pointers. Otherwise, it skips to the normal chase sequence.

## See also

- `A_ClearTarget` — Full target cleanup (more thorough than just nullifying the `target` field).
- `A_TransferPointer` — Copy a pointer from one actor to another.
- Actor pointers concept: `target`, `master`, `tracer` fields and their meanings.
