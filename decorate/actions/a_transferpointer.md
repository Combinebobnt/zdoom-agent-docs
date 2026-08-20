# `A_TransferPointer(pointer source, pointer recipient, pointer sourcefield, pointer recipientfield[, int flags])`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `A_TransferPointer` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_TransferPointer&oldid=38227) + verified against Zandronum source's `src/thingdef/thingdef_codeptr.cpp:282-307` and `src/actorptrselect.cpp`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
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

```decorate
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

## Engine-family divergence: pointer selector set

The core `A_TransferPointer` algorithm (self-reference check, target/master loop safeguards, `AAPTR_DEFAULT`-as-recipientfield behavior, and the `PTROP_UNSAFETARGET`/`PTROP_UNSAFEMASTER`/`PTROP_NOSAFEGUARDS` flag values of 1/2/3) is identical in UZDoom — same logic, same constants. Only the set of valid `AAPTR_*` selector values differs between the two engines:

- UZDoom defines `AAPTR_GET_LINETARGET`, a general selector (grouped alongside `AAPTR_TARGET`/`AAPTR_MASTER`/`AAPTR_TRACER`/`AAPTR_FRIENDPLAYER`) that Zandronum does not define at all.
- Zandronum defines several netcode/event-script-oriented selectors UZDoom does not have: `AAPTR_PLAYER_GETFLOATYICON`, `AAPTR_PLAYER_GETCAMERA`, and the `AAPTR_DAMAGE_SOURCE`/`AAPTR_DAMAGE_INFLICTOR`/`AAPTR_DAMAGE_TARGET` trio (the latter only meaningful in Zandronum's damage event scripts).

Passing a selector value on the "wrong" engine (e.g. `AAPTR_DAMAGE_SOURCE` on UZDoom) doesn't crash — it simply fails to match any case in the selector-resolution switch and falls through to returning the origin actor itself, the same fallback used for an unrecognized/zero selector.

## Related

- [Actor pointers (concept)](../concepts/actor-pointers.md) — general overview of actor pointer semantics across the engine (if documented).
- `A_CopyFriendliness` — copies hostility/friendliness status along with a pointer reference.
- `A_CheckPointer` — conditional jump on whether an actor pointer is valid.
