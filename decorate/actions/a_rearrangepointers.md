# `A_RearrangePointers` (actor pointer reassignment)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_RearrangePointers` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_RearrangePointers&oldid=50165) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:203-263`, `wadsrc/static/actors/actor.txt:316` (signature defaults), `src/actorptrselect.cpp:109-140` and `:142-166` (chain checks), `src/thingdef/thingdef_codeptr.cpp:3915-3920` (`A_ClearTarget`) and `:765-785` (`A_Jump`, for the example).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_RearrangePointers)` in `src/thingdef/thingdef_codeptr.cpp`.

Reassigns the calling actor's `target`, `master`, and `tracer` pointers to any of the actor's current pointers or to `NULL`, with optional safeguards against infinite pointer chains.

## Signature

```text
void A_RearrangePointers(int target, int master = AAPTR_DEFAULT, int tracer = AAPTR_DEFAULT, int flags = 0)
```

Only `target` is required. Omitted `master` and `tracer` default to `AAPTR_DEFAULT`, which leaves that field unchanged.

## Parameters

### `target` (int — AAPTR value)

The new value for the calling actor's `target` field. Must be one of the `AAPTR_*` constants (see "Pointer values" below). The actor's original `target` is fetched *before* any modifications, so all three parameters see the pre-modification state.

### `master` (int — AAPTR value, optional)

The new value for the calling actor's `master` field. See `target` for fetch-order semantics.

### `tracer` (int — AAPTR value, optional)

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

Any other `AAPTR_*` value (the player selectors, `AAPTR_FRIENDPLAYER`, and so on) is ignored and leaves the field unchanged.

**Important note:** The semantics of `target`/`master`/`tracer` vary by actor type. For example, in missiles, `target` points to the owner; in regular monsters, `target` points to the current enemy. Always verify actor-type semantics before assuming pointer meanings.

## Safeguards and flags

By default, `A_RearrangePointers` prevents **infinite pointer chains** by nullifying assignments that would create circular references:

- **For `target`**: The check runs only when the *calling* actor is a missile (it has `MISSILE` now, or its class default has it). It walks the `target` chain only while each next actor is also a missile. If that walk returns to an actor already in the chain (e.g., A → B → A), the caller's `target` is set to `NULL`. A loop passing through a non-missile is not detected. Checked by `VerifyTargetChain()` in the Zandronum source (`src/actorptrselect.cpp`).

- **For `master`**: An assignment is nullified if it would create an infinite loop in the master chain (checked for all actors, not just missiles). Checked by `VerifyMasterChain()`.

- **For `tracer`**: No verification is performed. The engine does not traverse tracer chains, so infinite loops are not a concern.

The following flags allow disabling these safeguards:

- **`PTROP_UNSAFETARGET` (1)** — Disable loop-checking for `target` assignments. Allows missiles to form infinite target chains (e.g., A → B → A).

- **`PTROP_UNSAFEMASTER` (2)** — Disable loop-checking for `master` assignments. Allows any actor to form infinite master chains.

- **`PTROP_NOSAFEGUARDS` (3)** — Equivalent to `PTROP_UNSAFETARGET | PTROP_UNSAFEMASTER`. Disables all safeguards.

**Caution:** Infinite pointer chains can cause engine hangs or crashes if code attempts to traverse them. Only disable safeguards if you fully understand the actor relationships you are creating and can guarantee external code will never traverse the chains.

## Caveat: A_ClearTarget

Setting `target` to `AAPTR_NULL` using `A_RearrangePointers` *only* sets the `target` field to `NULL`. It does **not** perform the additional cleanup that `A_ClearTarget` does, which also sets `LastHeard` and `lastenemy` to `NULL` (it triggers no state change). If you need full target clearing, use `A_ClearTarget` instead.

## Example (Zandronum DECORATE)

```text
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

Each pass through `See` (once per trip around the `Loop`), this imp has a 4/256 chance to "forget" its current target and master, while leaving its tracer unchanged. `A_Jump(252, 2)` jumps 252 times in 256 to offset 2, the `A_Chase` line, skipping the rearrange. In the remaining 4 in 256 it falls through to the `A_RearrangePointers` line and clears both pointers.

## See also

- `A_ClearTarget` — Full target cleanup (more thorough than just nullifying the `target` field).
- `A_TransferPointer` — Copy a pointer from one actor to another.
- Actor pointers concept: `target`, `master`, `tracer` fields and their meanings.
