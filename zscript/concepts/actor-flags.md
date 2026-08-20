# ZScript actor flags

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki "ZScript actor flags" (retrieved 2026-08-02, https://zdoom.org/w/index.php?title=ZScript_actor_flags&oldid=54700) + verified against UZDoom 4.15pre source's `wadsrc/static/zscript/actors/actor.zs` and `wadsrc/static/zscript/actors/inventory/inventory.zs`; re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — no behavioral drift found.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

ZScript exposes the actor flag table that DECORATE defines, but uses a distinct syntax for reading and writing flags in code. The underlying engine flag table is identical across both languages — the difference is purely syntactic and scoped to the ZScript language layer.

## Flag access in Default blocks

Within a `Default` block (actor property declarations), ZScript flags work identically to DECORATE:

```text
Default
{
  Projectile;
  Damage 20;
  -NOGRAVITY  // clear the flag
  +BOUNCEONFLOORS  // set the flag
}
```

Semicolons after flags are optional. The `+` and `-` syntax sets and clears flags respectively, same as DECORATE.

## Flag access in code

Within functions and methods, flags are accessed as **boolean fields** with a `b` prefix. To set or read a flag, prepend `b` to its name (in PascalCase, uppercase in the flag table becomes uppercase in the field name):

```text
virtual override BeginPlay()
{
  bSOLID = true;  // set SOLID flag
  bINVULNERABLE = false;  // clear INVULNERABLE flag
  
  if (bFRIENDLY)  // check FRIENDLY flag
  {
    // ...
  }
}
```

Any flag from the DECORATE table can be read or written this way — the field is synthesized at the ZScript VM level from the underlying engine flag word. Flags may be assigned any expression that evaluates to `true` or `false`.

## Special flags: NOSECTOR and NOBLOCKMAP

**NOSECTOR** and **NOBLOCKMAP** cannot be changed via direct boolean field assignment from mod code — they are marked read-only/internal-access at the engine level. (They aren't the only flags marked this way, but they're the two whose engine bookkeeping — sector and blockmap link management — needs synchronization beyond a simple bit-flip, so they're the ones with a dedicated setter function.) Changing them requires the `A_ChangeLinkFlags(int blockmap = FLAG_NO_CHANGE, int sector = FLAG_NO_CHANGE)` function, which unlinks the actor from the world, applies the requested flag changes, then relinks it:

```text
A_ChangeLinkFlags(blockmap: true, sector: true);  // set both NOBLOCKMAP and NOSECTOR
```

Pass `true`/`1` to set the corresponding flag or `false`/`0` to clear it; omitting a parameter (or passing `FLAG_NO_CHANGE`, `-1`) leaves that flag unchanged. The parameters are named `blockmap` and `sector` (matching the flag they control minus the `NO` prefix), not the flag names themselves.

## Custom flags

ZScript allows defining custom actor flags beyond those in the standard DECORATE table. Custom flags are declared with the `flagdef` keyword inside a class body:

```text
flagdef <FlagName>: <IntegerVariable>, <BitPosition>
```

- `<FlagName>`: The flag's name (as used in code and Default blocks).
- `<IntegerVariable>`: An `int` class member variable that holds the flag bits. The variable is the "container"; multiple `flagdef` declarations can use the same container, each at a different bit position.
- `<BitPosition>`: An integer from 0 to 31. Internally, the flag is computed as `1 << <BitPosition>` (bit 0 is value 1, bit 1 is value 2, bit 2 is value 4, etc.).

Example (a mod-defined class with its own custom flags):

```text
private int MyFlags;

flagdef Shielded: MyFlags, 0;
flagdef Berserk: MyFlags, 1;
```

Custom flags are then used in code like standard flags:

```text
bShielded = true;
if (bBerserk) { ... }
```

The standard library's own `Inventory` class uses this same mechanism internally: it holds several dozen custom flags (`Quiet`, `Autoactivate`, `Undroppable`, and others) packed into one private 4-byte container, one bit position per flag.

### Accessing custom flags from subclasses

When setting a custom flag in a class that did not define it, the fully-qualified name must be used:

```text
+MyBaseClass.Shielded  // in Default block
```

(In this case, `MyBaseClass` is the class that defined the `MyFlags` variable and the `Shielded` flagdef.)

In code, custom flags are accessed by the flag name alone (no class prefix); the compiler resolves which container holds the bits:

```text
bShielded = true;  // no "MyBaseClass." prefix needed
```

For the defining class itself, either the full name or just the flag name works in Default blocks.

### Avoiding direct container modification

While custom flag containers are ordinary integer variables, they should not be modified directly:

```text
MyFlags = 0;  // bad — bypasses flag semantics
```

Instead, always use the boolean field syntax to set and clear individual flags. Direct modification can cause unintended side effects, particularly if other subsystems are tracking flag state or if the engine has assumptions about which bits mean what.

## Relationship to DECORATE flags

The standard actor flags (SOLID, FRIENDLY, NOGRAVITY, INVULNERABLE, etc.) are identical to the DECORATE table. A complete list is documented at `../../decorate/inventory/actor-flags.md` — those same flags are accessible here in ZScript via the `b<FlagName>` boolean-field syntax. There is no separate ZScript flag table; the underlying engine flag words are shared.

## See also

- DECORATE: `../../decorate/inventory/actor-flags.md` — the flag table itself (names, which engine, presence in UZDoom vs. Zandronum).
- `A_ChangeLinkFlags` action function — required for changing NOSECTOR and NOBLOCKMAP.
- ZScript language reference — virtual method overrides, class hierarchy.
