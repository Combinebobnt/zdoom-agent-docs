# `A_CountdownArg` (countdown with state change)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_CountdownArg` (retrieved 2026-08-01, oldid=42322) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3615-3640`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_CountdownArg)` in `src/thingdef/thingdef_codeptr.cpp`.

Decrements one of an actor's argument counters and destroys or state-changes the actor when the countdown reaches zero. Replaces the simpler `A_Countdown` (which operates on the `reactiontime` field instead of an arg and is Strife-specific).

## Signature

```
void A_CountdownArg(int arg[, str state])
```

## Parameters

### `arg` (int)

Zero-based index into the actor's `args[5]` array. Valid range is 0–4. **Out-of-range values (negative or >= 5) cause the function to return immediately without decrementing anything** — a silent no-op.

### `state` (str, optional)

State label to transition the actor to when the countdown completes, or `NULL`/omitted for default behavior. The actual meaning depends on the destruction path (see below) — this parameter **is only used when the actor neither has the MISSILE flag nor the SHOOTABLE flag** (neither condition is `NULL`).

Default: "Death" — the actor's `Death` state, if defined. If the `Death` state is not defined and this parameter is omitted, the actor is simply removed/hidden by calling `SetState(NULL)`.

## Countdown mechanics

The countdown uses C post-decrement (`args[cnt]--`), which evaluates the argument's value **before** decrementing it:

- **Starting with `args[cnt] = N` (where N ≥ 0)**: the first N calls evaluate `args[cnt]` as N, N-1, ..., 1 respectively, each time returning without destruction. After the N-th call, `args[cnt]` = 0.
- **On call N+1**: `args[cnt]` evaluates to 0, the destruction branch executes, and `args[cnt]` becomes **-1**.
- **On any subsequent call**: `args[cnt]` is now -1, the condition `!(-1)` is false, and nothing happens. **Destruction never re-triggers** unless external code resets the arg.

**Important:** Setting an arg to N requires **N+1 calls to A_CountdownArg** to trigger destruction, not N. The wiki's phrase "counts one of the actor's args down until it reaches 0" understates this by one call.

## Destruction branch (when countdown triggers)

When the countdown reaches 0, one of three paths executes, checked **in this order**:

### 1. MISSILE flag (has highest priority)

If the actor has the `+MISSILE` flag, the function calls `P_ExplodeMissile(self, NULL, NULL)`:

- The missile enters its own `Death` state (or `XDeath`/`Crash` if those are reached first in the impact-state cascade).
- The `state` parameter is **silently ignored**.
- Splash damage (if any) depends on the missile's `Death` state actions and properties, not on `A_CountdownArg` itself.

### 2. SHOOTABLE flag (checked if MISSILE is not set)

If the actor has the `+SHOOTABLE` flag (but not MISSILE), the function calls:

```
P_DamageMobj(self, NULL, NULL, self->health, NAME_None, DMG_FORCED)
```

- Deals damage equal to the actor's current health (usually killing it instantly).
- **`DMG_FORCED`** bypasses armor/damage-reduction modifiers, invulnerability frames, dormancy checks, and skill-specific damage scaling — guaranteeing the actor dies regardless of resistances.
- **No kill credit**: the inflictor is `NULL`, so there is no attacker to credit, no obituary message, and (in multiplayer) no frag counter increment.
- The `state` parameter is **silently ignored**.
- If the actor survives this damage call (rare, e.g., if a custom property prevents death), the function returns without further state changes; `args[cnt]` is now -1, so the countdown never fires again without being reset.

### 3. Neither flag set (default)

If the actor has neither MISSILE nor SHOOTABLE, the function changes the actor's state:

- If `state` is provided and resolves to a valid state label, transition to that state.
- If `state` is omitted or `NULL`, attempt to find the actor's own `Death` state and transition to it.
- If no valid `Death` state is found, call `SetState(NULL)`, which **hides or destroys the actor** depending on map-reset game modes (returns false; the actor is no longer active).

**Note on the SHOOTABLE check:** An actor with both MISSILE and SHOOTABLE flags takes the MISSILE path (calls `P_ExplodeMissile`), **not** the SHOOTABLE path. This is rarely applicable in practice — missiles are not typically marked SHOOTABLE.

## Special notes

### Collision with map-placed arguments

The `args[5]` array is shared with map things' special arguments (set via the map editor). If a map-placed actor instance uses arg 0 for its own purposes (common in some maps), calling `A_CountdownArg(0, ...)` will interfere with and eventually destroy the argument that the map editor assigned. Choose an unused arg (often 1, 2, 3, or 4) if the map thing's editor-set args matter.

### Post-countdown state (-1 arg)

Once `args[cnt]` reaches -1, it stays there unless external code resets it. A subsequent call to `A_CountdownArg` on the same arg **will never re-trigger** the destruction branch — you must set the arg back to 0 or higher to restart the countdown.

### Network behavior (Zandronum multiplayer)

No special network logic — the countdown and state changes are decided server-side. Clients receive state updates from the server. The `P_ExplodeMissile` and `P_DamageMobj` calls broadcast their effects via `SERVERCOMMANDS_*` as usual.

### Difference from A_Countdown

`A_Countdown` (a Strife-specific action in `src/g_strife/a_strifestuff.cpp`) operates on the actor's `reactiontime` field, not an arg, and has special network handling plus a `MF_SKULLFLY` flag-clear side-effect. It is a different action with a different use case; do not confuse them.

## Example (Zandronum DECORATE)

```
actor TimedDispenser : Actor
{
    Default
    {
        Health 100;
        Radius 16;
        Height 32;
    }

    States
    {
    Spawn:
        DISP A 10
        {
            A_SpawnItemEx("Ammo", random(-16, 16), random(-16, 16), 32);
            A_CountdownArg(0);  // Decrement args[0] each tic
        }
        Loop;
    Death:
        DISP B 5 A_Scream;
        DISP C 5;
        DISP D 5 A_NoBlocking;
        Stop;
    }
}
```

A map editor would set the dispenser's arg 0 to, say, 60 (tics / 10 = 6 seconds per state frame). On the 61st state-action call (after ~6.1 seconds, depending on how frequently the state loops), arg 0 reaches 0, and if the dispenser has neither MISSILE nor SHOOTABLE, the actor transitions to `Death` (or is removed if no Death state exists).

## Open questions

- Exact behavior if an actor is in the SHOOTABLE destruction path but a custom actor property/flag prevents the `P_DamageMobj` call from killing it — whether the `args[cnt]` decrement still occurs (-1), or whether it remains at 0 and re-triggers next call.
