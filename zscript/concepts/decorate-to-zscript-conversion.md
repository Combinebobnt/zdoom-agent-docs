# Converting DECORATE code to ZScript

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki "Converting DECORATE code to ZScript" (retrieved 2026-08-03, https://zdoom.org/w/index.php?title=Converting_DECORATE_code_to_ZScript&oldid=54839) + spot-checked against UZDoom engine source; re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — no behavioral drift found (the `ResolveState`/`A_Jump*` wrapper, `PowerupType`'s DECORATE-only "Power" prefix gate, the `A_ChangeFlag`/`A_ChangeLinkFlags`/`A_ChangeCountFlags` deprecation note, the `BeginPlay`/`PostBeginPlay`/`Activate`/`Deactivate` virtual signatures, and the `Super.`/`super.` stdlib casing counts (351/7, unchanged) all checked out; the pull's only touch to a flag-assignment code path was an unrelated fix to chained assignment of legacy `DEPF_*` deprecated flags, not the `b<FlagName> = value` syntax this doc documents)
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

DECORATE and ZScript can coexist in the same mod — converting all DECORATE actors to ZScript is entirely optional. Partial conversion is valid: DECORATE actors can inherit from ZScript actors, but a ZScript actor cannot inherit from a DECORATE actor. This means converting a parent forces converting all ancestors, but children can remain in DECORATE.

## Key syntax and semantic changes

### State resolution: `ResolveState(null)` vs `ResolveState("Null")`

The `state()` cast is replaced by `ResolveState()`. Critically, **there are two different meanings for "no state"**:

- `return ResolveState(null);` — a null jump target is a no-op: it is not treated as a redirect, so the actor's normal state sequence keeps advancing instead of being interrupted. This does not by itself remove the actor.
- `return ResolveState("Null");` — resolves to the actor class's actual `Null` state (a real state, defined on the base `Actor` class, consisting of one tic followed by `Stop`). Reaching the end of a `Stop`-terminated state is what removes the actor — so this does destroy the actor, but only once state advancement reaches that point on a later tic, not instantly.

A common bug when porting old jump-target logic is assuming a null/empty jump target destroys the actor outright and writing `ResolveState(null)` where `ResolveState("Null")` was actually needed to remove it.

### Damage handling: `Damage` becomes `DamageFunction`

In DECORATE, the `Damage` property could hold a fixed integer:
```text
Damage 5
```

In ZScript, if you want to use an expression, you must use `DamageFunction` instead:
```zscript
DamageFunction (random(3, 12));
```

A fixed numeric value still uses `Damage` in both languages; `DamageFunction` is only needed when the damage value is computed.

### Direct flag assignment and scope constraints

ZScript allows direct flag assignment via the `b<FLAGNAME>` syntax:

```zscript
bShootable = true;
bVulnerable = false;
```

However, **this is not a function call** — it must appear in a code block (inside a state action or anonymous/named function). Attempting `A_ChangeFlag("SHOOTABLE", true)` is deprecated; use direct assignment instead. Note that some flags still require dedicated functions, such as `A_ChangeLinkFlags` and `A_ChangeCountFlags`.

### Subclass flag prefixes are now mandatory

In DECORATE, subclass flags were optional:
```text
+ALWAYSPICKUP
```

In ZScript, the flag's subclass prefix is required:
```zscript
+INVENTORY.ALWAYSPICKUP
```

Omitting the prefix causes a compile error.

### Properties must live in `Default { }` blocks; constants must not

In ZScript, actor properties (including flags) must be declared inside a `Default { }` block. Constants must be declared *outside* the block and take no type:

```zscript
class MyActor : Actor
{
    const OffsetX = 1;  // Declared outside Default { }
    
    Default
    {
        Radius 16;      // Properties live here
        Height 56;
    }
    
    States
    {
    // ...
    }
}
```

### Local variables: replacing `A_SetUserVar` and `A_SetUserArray`

DECORATE's `A_SetUserVar` and `A_SetUserArray` still exist in ZScript for backward compatibility, but are deprecated as of `version` 2.3 (the archive's declared ZScript language version, not the engine version) in favor of direct assignment — user variables are directly accessible as regular class fields in ZScript, so the indirection these functions provided is no longer needed. For weapon and CustomInventory actors, use the `invoker.` prefix to access the actor's own variables from within a state action:

```zscript
action void MyFunc()
{
    invoker.CountTracker += frandom(1.28, 2.56);
}
```

State actions are implicitly treated as `action` functions; you only need the keyword if defining a named function outside a state.

### Floating-point type: `double`, not `float`

DECORATE used `float` as a misnomer (these were actually doubles). ZScript makes this explicit: use `double` for all floating-point types. `float` does not exist in ZScript.

### String escaping in quoted strings

Backslashes in quoted strings must be escaped:
```zscript
Inventory.Icon "RPOW\\0";  // Correct — sprite RPOW, frame '\', rotation 0
// Inventory.Icon "RPOW\0";  // Wrong — the unescaped "\0" is read as a string-literal
                              // escape sequence (a NUL byte), not the two characters '\' and '0'
```

### Damagetype definitions moved to MAPINFO

Custom damage types are no longer defined inside actor definitions. Move them to MAPINFO instead.

### PowerupType naming

In DECORATE, `PowerupType MyPower` automatically prepended `Power` to the class name. In ZScript, it does not — the full class name must be used:

```zscript
PowerupType "PowerMyPower";  // Correct
// PowerupType "MyPower";     // Wrong in ZScript
```

## Virtual functions and the actor lifecycle

Several internal engine functions are exposed for override:

- **`BeginPlay`** — Called immediately after the actor is created. Use this for initializing defaults.
- **`PostBeginPlay`** — Called just before the first game tic is processed, after `BeginPlay` completes.
- **`Tick`** — Called every tic while the actor is active. This is how an actor performs over time.
- **`Activate`** — Called when `Thing_Activate` or a similar activation script is executed.
- **`Deactivate`** — Called when `Thing_Deactivate` or a deactivation script is executed (for actors spawned with the `DORMANT` flag).

Virtual functions can be defined with `virtual` or `override`. To call the parent class's implementation, use `Super.FunctionName()`:

```zscript
override void PostBeginPlay()
{
    PerformSomeStuff();
    Super.PostBeginPlay();  // Call the parent's implementation
}
```

**Important:** Calling the parent's implementation is necessary for most internal functions, or the actor will not behave correctly. For example, failing to call `Super.Tick()` breaks the normal tick cycle.

**Note on case:** The ZScript stdlib predominantly uses `Super.` with a capital S (351 documented occurrences vs. 7 lowercase `super.` occurrences in the stdlib). Both forms are accepted by the parser, but `Super.` is the standard convention.

## Scope qualification for states and action functions

States and action functions can optionally be qualified by scope, restricting what function types are allowed to execute within them. The four scopes are `Actor`, `Overlay`, `Weapon`, and `Item`:

```zscript
States(Weapon)
{
    Fire:
        PIST A 1 A_WeaponReady();
        // ...
}

Action(Weapon) void MyWeaponFunc()
{
    // Only weapon-qualified states can use this function.
}
```

## See also

- [`decorate-to-zscript-differences.md`](decorate-to-zscript-differences.md) — narrower focus on actor-definition syntax constraints (property quotation, `DoomEdNum` placement, class naming, multi-return syntax, named-argument ordering).
- [`zscript-engine-availability.md`](zscript-engine-availability.md) — ZScript exists only in UZDoom/GZDoom-family, not Zandronum.
- [`../classes/`](../classes/) — individual ZScript class documentation.
