# DECORATE expressions

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `DECORATE_expressions` (retrieved 2026-07-31, oldid=55359) + verified against Zandronum source (`src/thingdef/thingdef_exp.cpp`, `src/thingdef/thingdef_expression.cpp`, `src/thingdef/thingdef_function.cpp`).

Numeric expressions can be used as parameters to action functions and other dynamic contexts in DECORATE (e.g., in `A_SetHealth(health + 50)`, `A_CustomMissile(..., random(0, 360))`). Expressions combine literals, variables, operators, and function calls following standard operator precedence. **Note:** Expressions may not be used as static values in the `Default` block — that context requires compile-time constants only (see [`constants.md`](constants.md) for `const`/`enum`/user variables in actor definitions).

## Precedence and operators

Operators follow C-like precedence, highest to lowest (within the same level, left-to-right):

1. Unary: unary minus/plus (`-x`, `+x`), unary logical not (`!x`), unary bitwise complement (`~x`)
2. Multiplicative: `*`, `/`, `%` (modulo)
3. Additive: `+`, `-` (binary)
4. Shift: `<<`, `>>`, `>>>` (unsigned right shift)
5. Bitwise: AND (`&`), XOR (`^`), OR (`|`)
6. Relational: `<`, `>`, `<=`, `>=`
7. Equality: `==`, `!=`
8. Logical AND: `&&`
9. Logical OR: `||`
10. Ternary conditional: `? :`

All operators work on numeric types (int and float); bitwise operators truncate to integers. Floating-point and integer operands are coerced as needed, following C rules (explicit cast not required).

## Literals and identifiers

- **Numeric literals:** integers (e.g., `42`, `-100`) and floats (e.g., `3.14`, `0.5`)
- **Boolean literals:** `true` (1) and `false` (0)
- **Actor member variables:** any variable accessible on the calling actor — both the predefined member variables listed below and user-defined variables/arrays (e.g., `user_count`, `user_array[3]`)
- **Class constants:** `const` and `enum` defined in the actor class or globally
- **Map args:** `args[0]` through `args[4]` (the thing's special arguments in the map editor)

## Actor variables accessible in expressions

The following actor member variables can be read and, where noted, written in expressions:

**Position and velocity:**
- `x`, `y`, `z` — actor position
- `velx` (alias `momx`), `vely` (alias `momy`), `velz` (alias `momz`) — velocity components
- `ceilingz`, `floorz` — absolute Z coordinates of ceiling and floor at the actor's XY position (portal- and 3D-floor-aware)

**Orientation:**
- `angle` — facing angle in degrees
- `pitch` — pitch in degrees
- *Note: `roll`, `VisibleStartAngle`, `VisibleEndAngle`, `VisibleStartPitch`, `VisibleEndPitch` are not accessible in Zandronum DECORATE*

**Physical properties:**
- `health` — current health
- `height`, `radius` — collision box dimensions
- `mass` — actor mass
- `scaleX`, `scaleY` — visual scale factors
- `damage` — projectile damage value (**deprecated** in newer syntax — prefer dedicated action functions)

**Actor state:**
- `alpha` — opacity (1.0 = opaque, 0.0 = invisible)
- `accuracy` — accuracy rating
- `stamina` — stamina value
- `reactiontime` — reaction time in tics
- `meleerange` — melee attack range

**Special values:**
- `tid` — thing ID
- `TIDtoHate` — TID of the actor to hate (see `Thing_Hate`)
- `waterlevel` — submersion level in water (0–3; see [`creating-monsters.md`](creating-monsters.md) for the meaning of each)
- `special`, `special1`, `special2` — map special and auxiliary values
- `score` — score value

*Note: The wiki's ZScript-era reference lists `pos`, `vel` with component access (e.g., `pos.x`, `vel.z`) — Zandronum DECORATE does not support that syntax (dot-member access is disabled). Use the flat variable names (`x`/`y`/`z`, `velx`/`vely`/`velz`) instead. Similarly, `threshold`, `defthreshold`, `waterdepth`, `roll`, and `species` are not accessible in Zandronum DECORATE.*

## Built-in functions

**Random number generation:**

- `random(min, max)` — returns a random integer in `[min, max]` inclusive
- `frandom(min, max)` — returns a random floating-point value in `[min, max]`
- `random2(mask)` — returns a value in `[-mask, +mask]` using the formula `(random() & mask) - (random() & mask)`. If no mask is given, defaults to 255. Mask should be one less than a power of 2 (e.g., 1, 3, 7, 15, 31, 63, 127) for useful distributions.

All three accept an optional **identifier** for RNG isolation (e.g., `random[myspawner](0, 10)`), used to keep certain random calls from affecting the outcomes of others — useful in multiplayer to maintain desync-free behavior when mixing synchronized and clientside code. Without an identifier, calls share the global RNG state. *The wiki's discussion of UI-scope vs. play-scope and clientside RNG (`crandom`, etc.) applies to ZScript only and does not apply to Zandronum DECORATE.*

**Warning on integer vs. floating-point:** Do not pass float bounds to `random()` or int bounds to `frandom()` — the truncation behavior is counterintuitive. For example, `random(0.0, 0.5)` always returns 0 (both bounds truncate to 0 before the draw); `frandom(0.0, 1.0)` cast to int truncates before the comparison, not after. Use matching types: `random(0, 5)` and `frandom(0.0, 5.0)`.

**Mathematical:**

- `abs(x)` — absolute value
- `sqrt(x)` — square root
- `sin(x)`, `cos(x)` — sine and cosine of x in degrees

*The wiki lists additional math functions (`exp`, `log`, `log10`, `ceil`, `floor`, `round`, `min`, `max`, `clamp`, `tan`, `acos`, `asin`, `atan`, `cosh`, `sinh`, `tanh`, `atan2`, `VectorAngle`) and a second set of random functions (`randompick`, `frandompick`, `crandom`, etc.) — these are not supported in Zandronum DECORATE; they are GZDoom/ZScript extensions.*

**Type checking and pointer comparison:**

- `checkclass(class, [pointer], [match_superclass])` — checks whether the actor at `pointer` (default: self) is an instance of `class`. If `match_superclass` is true, also matches subclasses of `class`.
- `ispointerequal(pointer1, pointer2)` — returns true if both pointers reference the same actor

Actor pointers in expressions use the numeric form: `AAPTR_DEFAULT` (0 = self), `AAPTR_TARGET` (1 = self.target), `AAPTR_MASTER` (2 = self.master), `AAPTR_TRACER` (3 = self.tracer), etc.

**ACS function calls:**

- `ACS_NamedExecuteWithResult(scriptname, [arg1, arg2, arg3, arg4])` — calls an ACS script by name and returns its result
- `CallACS(scriptname, [arg1, arg2, arg3, arg4])` — alias for `ACS_NamedExecuteWithResult`

These are routed to the map's ACS behavior lump and are synchronized across the network in multiplayer.

## Array access

Actor variables that are arrays (e.g., `args`, `user_myarray`) can be indexed with `[n]`, e.g., `args[2]`, `user_myarray[0]`.

## Examples

```
// Health that scales with difficulty
health = 100 * (2 - skill / 4)

// Angle within a 90-degree arc
angle = random(self.angle - 45, self.angle + 45)

// Projectile damage with variance
damage = (random(0, 3) + 1) * base_damage

// Check actor class and act accordingly
checkclass(DoomImp, AAPTR_TARGET, true) ? 10 : 20  // return 10 for Imps or subclasses, else 20

// Call ACS script and branch on result
ACS_NamedExecuteWithResult("CheckObjective", args[0], args[1]) == 1
```

## See also

- [`constants.md`](constants.md) — `const`/`enum` declarations and user variables in actor definitions
- [`state-machine.md`](state-machine.md) — expression use in state-duration parameters (duration cannot be an expression in Zandronum DECORATE; see that file for details)
- [`creating-monsters.md`](creating-monsters.md) — actor properties and flags used with expressions
