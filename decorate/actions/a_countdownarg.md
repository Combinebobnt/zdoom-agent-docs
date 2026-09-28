# `A_CountdownArg` (countdown with state change)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_CountdownArg` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_CountdownArg&oldid=42322) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3615-3640`; corrections backed by `wadsrc/static/actors/actor.txt:262` (declaration), `src/thingdef/thingdef_states.cpp:377-397` (state offsets), `src/thingdef/thingdef_expression.cpp:2740-2757` (runtime label lookup), `src/p_mobj.cpp:1536-1577` (`P_ExplodeMissile`), `src/p_mobj.cpp:513-521` and `619-648` (`SetState(NULL)`, `HideOrDestroyIfSafe`), `src/p_interaction.cpp:1182-1188`, `1259` and `1745-1749` (`P_DamageMobj`), `src/info.h:140-151` (`CallAction`), `src/g_strife/a_strifestuff.cpp:621-637` (`A_Countdown`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_CountdownArg)` in `src/thingdef/thingdef_codeptr.cpp`.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Decrements one of an actor's argument counters and destroys or state-changes the actor when the countdown reaches zero. It is the arg-based counterpart of `A_Countdown`, which counts down the `reactiontime` field instead (see below).

## Signature

```text
void A_CountdownArg(int arg[, state targstate])
```

Zandronum declares it as `action native A_CountdownArg(int argnum, state targstate = "")` in `wadsrc/static/actors/actor.txt:262`.

## Parameters

### `arg` (int)

Zero-based index into the actor's `args[5]` array. Valid range is 0–4. **Out-of-range values (negative or >= 5) cause the function to return immediately without decrementing anything**, a silent no-op.

### `targstate` (state, optional)

State to transition the actor to when the countdown completes. It is **only used when the actor has neither the MISSILE flag nor the SHOOTABLE flag** (see "Destruction branch" below).

On Zandronum it accepts a quoted state label or a non-negative integer offset (`src/thingdef/thingdef_states.cpp:377-397`); offset 0 means "no state", which selects the default below.

Default: none, which falls back to the actor's own `Death` state. If there is no `Death` state either, the actor is removed via `SetState(NULL)` (see path 3).

**Unknown label on Zandronum:** a plain label the actor doesn't have is looked up at runtime, prints `Jump target '<label>' not found in <Class>` to the console, and yields no state, so the `Death` fallback applies (`src/thingdef/thingdef_expression.cpp:2740-2757`). The parameter is evaluated at the top of the function, before the range check and the countdown test, so the message prints on **every** call, not only when the countdown fires.

## Countdown mechanics

The countdown uses C post-decrement (`args[cnt]--`), which evaluates the argument's value **before** decrementing it:

- **Starting with `args[cnt] = N` (where N ≥ 0)**: the first N calls evaluate `args[cnt]` as N, N-1, ..., 1 respectively, each time returning without destruction. After the N-th call, `args[cnt]` = 0.
- **On call N+1**: `args[cnt]` evaluates to 0, the destruction branch executes, and `args[cnt]` becomes **-1**.
- **On any subsequent call**: the arg is negative, so the zero test fails and nothing happens, but the decrement still runs, so the arg keeps falling (-2, -3, ...). **Destruction never re-triggers** unless external code resets the arg.

**Important:** Setting an arg to N requires **N+1 calls to A_CountdownArg** to trigger destruction, not N. The wiki's phrase "counts one of the actor's args down until it reaches 0" understates this by one call.

## Destruction branch (when countdown triggers)

When the countdown reaches 0, one of three paths executes, checked **in this order**:

### 1. MISSILE flag (has highest priority)

If the actor has the `+MISSILE` flag, the function calls `P_ExplodeMissile(self, NULL, NULL)`:

- Because no target is passed, the missile always enters its plain `Death` state. The `Crash`/`XDeath` choice in `P_ExplodeMissile` only applies when a target is given. With no `Death` state it is removed as in path 3.
- With `+EXPLOCOUNT`, `P_ExplodeMissile` returns early until its explosion count is reached. The arg is already negative by then, so this countdown never retries the explosion.
- The `targstate` parameter is **silently ignored**.
- Splash damage (if any) depends on the missile's `Death` state actions and properties, not on `A_CountdownArg` itself.

### 2. SHOOTABLE flag (checked if MISSILE is not set)

If the actor has the `+SHOOTABLE` flag (but not MISSILE), the function calls:

```text
P_DamageMobj (self, NULL, NULL, self->health, NAME_None, DMG_FORCED);
```

- Deals damage equal to the actor's current health (usually killing it instantly).
- **`DMG_FORCED`** skips invulnerability, dormancy, skill damage scaling, damage factors, protection powerups and armor, so resistances don't save the actor.
- **Spectral actors differ by engine.** On Zandronum the `+SPECTRAL` check runs before the `DMG_FORCED` bypass (`src/p_interaction.cpp:1182-1188` vs `1259`), so a spectral shootable actor takes no damage from this call, since there is no spectral inflictor. On UZDoom the spectral check is itself skipped for `DMG_FORCED`, so the actor is damaged normally.
- On Zandronum a player target can still survive via the Buddha cheat, and a damage event script can cancel the damage.
- **No kill credit**: the inflictor and source are both `NULL`, so no attacker is credited.
- The `targstate` parameter is **silently ignored**.
- If the actor survives this damage call, the function returns without further state changes; `args[cnt]` is now -1, so the countdown never fires again without being reset.

### 3. Neither flag set (default)

If the actor has neither MISSILE nor SHOOTABLE, the function changes the actor's state:

- If `targstate` names a state the actor has, transition to that state.
- Otherwise (omitted, offset 0, or an unknown label), use the actor's own `Death` state.
- If there is no `Death` state, `SetState(NULL)` is called and the actor is removed. On Zandronum this goes through `HideOrDestroyIfSafe` (`src/p_mobj.cpp:619-648`): in game modes where the map resets, a level-spawned actor is hidden instead of destroyed (never in client mode); otherwise it is destroyed.

**Note on the SHOOTABLE check:** An actor with both MISSILE and SHOOTABLE flags takes the MISSILE path (calls `P_ExplodeMissile`), **not** the SHOOTABLE path. This is rarely applicable in practice, since missiles are not typically marked SHOOTABLE.

## Special notes

### Collision with map-placed arguments

The `args[5]` array is shared with map things' special arguments (set in the map editor, in Hexen-format or UDMF maps). If a map-placed actor instance uses arg 0 for its own purposes, calling `A_CountdownArg(0, ...)` will count that value down and overwrite it. Choose an unused arg if the map thing's editor-set args matter.

### Post-countdown state (negative arg)

Once `args[cnt]` goes negative, every further call lowers it by one more. A subsequent call to `A_CountdownArg` on the same arg **will never re-trigger** the destruction branch; you must set the arg back to 0 or higher (e.g. with `A_SetArg`) to restart the countdown.

### Network behavior (Zandronum multiplayer)

`A_CountdownArg` has no network code and no client-mode check, and state actions are called without any client filter (`src/info.h:140-151`), so it runs on clients as well as on the server. What reaches clients depends on the path:

- **MISSILE:** the server's `P_ExplodeMissile` sends a `MissileExplode` command (`src/p_mobj.cpp:1564-1577`).
- **SHOOTABLE:** death is decided on the server only; `Die` is skipped in client mode (`src/p_interaction.cpp:1745-1749`).
- **Neither flag:** nothing is sent. A client reaches `targstate`/`Death` only by running the same countdown locally, which depends on its copy of the arg matching the server's. The decrements themselves are never sent.

### Difference from A_Countdown

`A_Countdown` (defined in Strife source, `src/g_strife/a_strifestuff.cpp:621-637`, but declared on `Actor` and callable from any actor) operates on the actor's `reactiontime` field, not an arg. It pre-decrements and fires at `<= 0`, always calls `P_ExplodeMissile` regardless of flags, then clears `MF_SKULLFLY`. On Zandronum it runs on the server only and sends the flag change to clients.

## Example (DECORATE)

```text
actor TimedDispenser
{
    Radius 16
    Height 32
    States
    {
    Spawn:
        DISP A 5 A_SpawnItemEx("Clip", random(-16, 16), random(-16, 16), 32)
        DISP A 5 A_CountdownArg(0)
        Loop
    Death:
        DISP B 5 A_Scream
        DISP C 5
        DISP D -1
        Stop
    }
}
```

A map editor would set the dispenser's arg 0 to, say, 20. The loop is 10 tics long and the countdown runs 5 tics in, so the 21st `A_CountdownArg` call fires about 205 tics (roughly 6 seconds) after spawning. The dispenser has neither MISSILE nor SHOOTABLE, so it transitions to `Death`.
