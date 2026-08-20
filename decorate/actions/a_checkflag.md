# `void A_CheckFlag(string flagname, state label, int check_pointer = AAPTR_DEFAULT)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_CheckFlag` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_CheckFlag&oldid=54541) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:4752-4769`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `src/thingdef/thingdef_codeptr.cpp:4752` (`DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_CheckFlag)`).

Checks whether an actor (specified by actor pointer) has a given actor flag set, and jumps to a target state if the flag is set. Called on any actor; the actor being checked defaults to the calling actor if not specified.

## Signature

```decorate
void A_CheckFlag (string flagname, state label [, int check_pointer])
```

## Parameters

- **`flagname`** — the name of the flag to check, as a string. Case-insensitive. Supports dot notation for actor-class-specific flags (e.g., `"FRIENDLY"` or `"weapon.nohitscanscan"`), resolved via the same `FindFlag` function as `A_ChangeFlag`. See `A_ChangeFlag` for the full `FindFlag` semantics.
- **`label`** — the state to jump to if the flag is set on the target actor. If a state label (e.g., `"Death"`, `"DeathFade"`), the name is resolved in the calling actor's derived class's state table (virtual resolution). If the flag is not set, no jump occurs — execution continues to the next action or frame in the current state.
- **`check_pointer`** (optional) — the actor on which to perform the flag check, specified as an actor pointer. Default is `AAPTR_DEFAULT`, which refers to the calling actor itself. Other common pointers are `AAPTR_TARGET`, `AAPTR_MASTER`, `AAPTR_TRACER` (see `actorptrselect.h` in the Zandronum source for the full enum of selectors).

## Engine-family divergence

**UZDoom deprecates `A_CheckFlag`.** In UZDoom's ZScript stdlib (`wadsrc/static/zscript/actors/checks.zs`), the action is declared with `deprecated("2.3", "Use a combination of direct flag access and SetStateLabel()")`, so calling it from DECORATE or ZScript on UZDoom emits a compile-time deprecation warning recommending direct flag-field access plus `SetStateLabel()` instead. It remains fully functional and behaves identically to the description below: the ZScript wrapper calls a private native `CheckFlag()` (`src/playsim/p_actionfunctions.cpp`, `DEFINE_ACTION_FUNCTION(AActor, CheckFlag)`) that resolves the pointer via `COPY_AAPTR` and, on a non-null result, routes through the same `CheckActorFlag()`/`FindFlag()`/`CheckDeprecatedFlags()` machinery described here, with the same "Unknown flag" error message and the same silent no-jump behavior on a null pointer. Zandronum carries no such deprecation notice; `A_CheckFlag` remains its standard, non-deprecated flag-check action.

## Behavior

**Flag state check:** If the target actor (resolved via `check_pointer`) has the flag set, the function jumps to the specified state. The check uses `CheckActorFlag()` to find the flag definition and test whether the bit is set.

**Null pointer path:** If `check_pointer` resolves to `NULL` or an invalid pointer (e.g., `AAPTR_MASTER` on an actor with no master), the function returns immediately **without jumping**. The behavior is indistinguishable from "flag is clear" — no jump occurs, execution continues to the next action in the state.

**Unknown flag name:** If `flagname` does not match any flag in the engine's flag table, `FindFlag()` returns `NULL`, the flag check fails, and no jump occurs. **Additionally, the engine prints an error message `Unknown flag 'X' in 'ClassName'` to the console every tic the state runs**, because the `CheckActorFlag(owner, flagname)` overload defaults `printerror` to `true`. This can lead to console spam if an actor loops in a state that performs the check with a typo'd flag name; use caution when testing.

**Deprecated flags:** If the flag name refers to a deprecated flag (where `structoffset == -1` in the flag definition), the check routes through `CheckDeprecatedFlags()` instead of a direct bit test, applying any special deprecation handling the engine defines for that flag.

**Dot notation:** Actor-class-specific flags can be checked using dot notation (e.g., `"weapon.nohitscanscan"`), which allows checking flags on actors of different classes without switching the context. This works identically to `A_ChangeFlag`'s dot-notation support.

## Zandronum-specific: network handling

Unlike `A_ChangeFlag` (which broadcasts state changes to clients via `SERVERCOMMANDS_SetThingFlags`) or `A_CheckSight` (which branches on `NETWORK_InClientMode()` and broadcasts the jump decision), **`A_CheckFlag` performs no explicit network handling**. The source comment notes that clients already mirror actor flag state; the function checks this state without synchronization overhead. Because it is a read-only check, no client-side inconsistency guard is present. The jump decision is made identically on both server and client (assuming their flag state is synchronized), and no `CLIENTUPDATE_FRAME` flag is passed to the underlying `ACTION_JUMP` macro.

## Related functions

- `A_ChangeFlag` — changes an actor flag to a given value. Useful for setting flags on one actor before checking them on another.
- `A_CheckSight` — jumps if no player can see the calling actor, using line-of-sight rather than flag checks.
- `A_CheckSightOrRange` — jumps if an actor is both out of sight and beyond range.

## Examples

This imp will be frightened if its master is frightened, copying the master's `FRIGHTENED` flag state:

```decorate
ACTOR CowardImp : DoomImp
{
  States
  {
  See:
    TROO A 0 A_CheckFlag("FRIGHTENED", "RunAway", AAPTR_MASTER)
    TROO AABBCCDD 3 A_Chase
    Loop
  RunAway:
    TROO A 0 A_ChangeFlag("FRIGHTENED", TRUE)
    Goto See+2
  }  
}
```

This projectile enters a slow "trailing" state if its tracer (target) is marked as friendlier to the player:

```decorate
ACTOR MyTracingProjectile : Projectile
{
  States
  {
  Spawn:
    MISL A 4
    MISL B 4 A_CheckFlag("FRIENDLY", "Trail", AAPTR_TRACER)
    Loop
  Trail:
    MISL A 2 A_Tracer2
    Loop
  }
}
```
