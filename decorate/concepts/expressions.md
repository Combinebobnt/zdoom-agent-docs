# DECORATE expressions

**Tier:** A (original content below); B (the "Correction" sentence in the intro, added from
direct source reading with no wiki starting point — see `constants.md` for the full finding)
**Applies to:** UZDoom=yes, Zandronum=yes — UZDoom's DECORATE expression parser supports a wider
built-in function set than Zandronum's, see "Engine-family divergence" below; the expression
language and grammar described in this file otherwise apply to both
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** ZDoom Wiki `DECORATE_expressions` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=DECORATE_expressions&oldid=55359) + verified against Zandronum source (`src/thingdef/thingdef_exp.cpp`, `src/thingdef/thingdef_expression.cpp`, `src/thingdef/thingdef_function.cpp`). The intro's tier-B correction is verified against `src/thingdef/thingdef_parse.cpp:649-651` and `:1261-1265` (see `constants.md`'s Provenance for the same citation). Pointer constants, readable variables, `random2`/`frandom` ranges and `ACS_NamedExecuteWithResult` behavior re-verified against `wadsrc/static/actors/constants.txt:245-249`, `wadsrc/static/actors/actor.txt:33-64`, `src/actor.h:984`, `src/m_random.h:68-72`, `src/thingdef/thingdef_expression.cpp:1742-1766` and `:2313-2347`, `src/p_lnspec.cpp:1833-1851`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

Numeric expressions can be used as parameters to action functions and other dynamic contexts in DECORATE (e.g., in `A_SetAngle(angle + 45)`, `A_CustomMissile(..., random(0, 360))`). Expressions combine literals, variables, operators, and function calls following standard operator precedence. **Note:** Expressions may not be used as actor property values (the property section ZScript calls the `Default` block), with one exception: `Damage`, the only `'X'`-type property, accepts an expression in parentheses. **Correction (source-verified, tier B):** a plain `'I'`/`'F'`-typed property value in the `Default` block is not "a compile-time constant expression" in the sense of accepting a named `const`/`enum` symbol either — it is parsed by `sc.MustGetNumber()`/`sc.MustGetFloat()`, which only ever reads a bare numeric literal token and never consults the symbol table `const`/`enum` names are registered in. A same-named `const int`/`enum` that resolves fine as an action-function argument one line later will fail to compile as a plain property value. See [`constants.md`](constants.md#named-constants-are-not-accepted-as-plain-property-values-verified) for the full trace and the distinction from `'X'`-type (expression-in-parens) properties, where a named constant does resolve.

## Precedence and operators

Operators follow C-like precedence, highest to lowest (within the same level, left-to-right):

1. Unary: unary minus/plus (`-x`, `+x`), unary logical not (`!x`), unary bitwise complement (`~x`)
2. Multiplicative: `*`, `/`, `%` (modulo)
3. Additive: `+`, `-` (binary)
4. Shift: `<<`, `>>`, `>>>` (unsigned right shift)
5. Relational: `<`, `>`, `<=`, `>=`
6. Equality: `==`, `!=`
7. Bitwise AND: `&`
8. Bitwise XOR: `^`
9. Bitwise OR: `|`
10. Logical AND: `&&`
11. Logical OR: `||`
12. Ternary conditional: `? :`

All operators work on numeric types (int and float); bitwise operators truncate to integers. Floating-point and integer operands are coerced as needed, following C rules (explicit cast not required).

## Literals and identifiers

- **Numeric literals:** integers (e.g., `42`, `-100`) and floats (e.g., `3.14`, `0.5`)
- **Boolean literals:** `true` (1) and `false` (0)
- **Actor member variables:** any variable accessible on the calling actor — both the predefined member variables listed below and user-defined variables/arrays (e.g., `user_count`, `user_array[3]`; on Zandronum user variables are `int` only)
- **Class constants:** `const` and `enum` defined in the actor class or globally
- **Map args:** `args[0]` through `args[4]` (the thing's special arguments in the map editor)

## Actor variables accessible in expressions

The following actor member variables can be read and, where noted, written in expressions. This list applies to Zandronum; UZDoom's GZDoom-derived `AActor` class carries the same variables with some semantic differences (e.g. angles/pitches as doubles rather than fixed-point, and position components as explicit doubles). A full type/range comparison for UZDoom has not been traced here — see the engine source if precision/range matters to your DECORATE code.

**Position and velocity:**
- `x`, `y`, `z` — actor position
- `velx` (alias `momx`), `vely` (alias `momy`), `velz` (alias `momz`) — velocity components
- `ceilingz`, `floorz` — absolute Z of the lowest ceiling and highest floor among the sectors the actor's bounding box touches (3D-floor-aware)

**Orientation:**
- `angle` — facing angle in degrees, read in the range [0, 360)
- `pitch` — pitch in degrees. Zandronum stores pitch as a signed value but declares it unsigned for expressions, so a negative pitch reads as 360 minus its magnitude (e.g. -10 reads as 350)
- *Note: `roll`, `VisibleStartAngle`, `VisibleEndAngle`, `VisibleStartPitch`, `VisibleEndPitch` are not accessible in Zandronum DECORATE*

**Physical properties:**
- `health` — current health
- `height`, `radius` — collision box dimensions
- `mass` — actor mass
- `scaleX`, `scaleY` — visual scale factors
- `damage` — the stored `Damage` property value. When `Damage` was given as a parenthesized expression, this holds an encoded expression reference rather than a damage number

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
- `special` — the actor's map special
- `score` — score value

*Note: The wiki's ZScript-era reference lists `pos`, `vel` with component access (e.g., `pos.x`, `vel.z`) — neither Zandronum nor UZDoom DECORATE supports that syntax (dot-member access is disabled via preprocessor guard in both engines). Use the flat variable names (`x`/`y`/`z`, `velx`/`vely`/`velz`) instead. Similarly, `special1`, `special2`, `threshold`, `defthreshold`, `waterdepth`, `roll`, and `species` are not accessible in Zandronum DECORATE (only the variables `actor.txt` declares `native` are readable; any other name is an "Unknown identifier" error that aborts loading).*

## Built-in functions

**Random number generation:**

- `random(min, max)` — returns a random integer in `[min, max]` inclusive
- `frandom(min, max)` — returns a random floating-point value in `[min, max)` (`max` itself is never returned)
- `random2(mask)` — returns a value in `[-mask, +mask]` using the formula `(random() & mask) - (random() & mask)`. On Zandronum each draw is also masked with 255, so the result never leaves `[-255, 255]` even for a larger mask, and `random2()` with no mask behaves as mask 255. Mask should be one less than a power of 2 (e.g., 1, 3, 7, 15, 31, 63, 127) for useful distributions.

All three accept an optional **identifier** for RNG isolation (e.g., `random[myspawner](0, 10)`), used to keep certain random calls from affecting the outcomes of others: the call draws from its own named RNG stream, created on first use. Without an identifier, calls share one expression RNG stream (`EX_Random` on Zandronum). *The wiki's discussion of UI-scope vs. play-scope and clientside RNG (`crandom`, etc.) applies to ZScript only and does not apply to Zandronum DECORATE.*

**Warning on integer vs. floating-point:** Do not pass float bounds to `random()` or int bounds to `frandom()` — the truncation behavior is counterintuitive. For example, `random(0.0, 0.5)` always returns 0 (both bounds truncate to 0 before the draw). An `frandom()` result passed to an integer parameter is truncated toward zero, so `frandom(0.0, 1.0)` there is always 0. Use matching types: `random(0, 5)` and `frandom(0.0, 5.0)`.

**Mathematical:**

- `abs(x)` — absolute value
- `sqrt(x)` — square root
- `sin(x)`, `cos(x)` — sine and cosine of x in degrees (Zandronum uses the engine's fixed-point lookup table, so precision is limited)

*The wiki lists additional math functions (`exp`, `log`, `log10`, `ceil`, `floor`, `round`, `min`, `max`, `clamp`, `tan`, `acos`, `asin`, `atan`, `cosh`, `sinh`, `tanh`, `atan2`, `VectorAngle`) and a second set of random functions (`randompick`, `frandompick`, `crandom`, etc.) — these are not supported in Zandronum DECORATE; they are GZDoom/ZScript extensions.*

**Type checking and pointer comparison:**

- `checkclass(class, [pointer], [match_superclass])` — checks whether the actor at `pointer` (default: self) is an instance of `class`. If `match_superclass` is true, also matches subclasses of `class`. Pass the class name quoted (`"DoomImp"`); a bare `DoomImp` is parsed as an identifier and fails with "Unknown identifier". An unknown class name, or a pointer that selects no actor, returns 0.
- `ispointerequal(pointer1, pointer2)` — returns true if both pointers reference the same actor

Actor pointers are the `AAPTR_*` global constants, usable by name. They are bit flags: `AAPTR_DEFAULT` (0 = self), `AAPTR_NULL` (1), `AAPTR_TARGET` (2), `AAPTR_MASTER` (4), `AAPTR_TRACER` (8), etc.

**ACS function calls:**

- `ACS_NamedExecuteWithResult(scriptname, [arg1, arg2, arg3, arg4])` — calls an ACS script by name and returns its result
- `CallACS(scriptname, [arg1, arg2, arg3, arg4])` — alias for `ACS_NamedExecuteWithResult`

The script is looked up by name in the current map's loaded ACS modules (map and libraries), and the expression's value is what the script sets with `SetResultValue`. On a Zandronum server, a `CLIENTSIDE` script is not run there: the server tells clients to run it and the expression yields 0.

On Zandronum any other action special can also be called by name as a function in an expression; its return value is the expression's value.

## Array access

Actor variables that are arrays (e.g., `args`, `user_myarray`) can be indexed with `[n]`, e.g., `args[2]`, `user_myarray[0]`.

## Examples

Expressions go in action-function arguments inside a state table:

```decorate
ACTOR ExpressionDemo : DoomImp
{
  var int user_shots;
  States
  {
  Missile:
    TROO EF 8 A_FaceTarget
    // Turn by a random amount within a 90-degree arc
    TROO F 0 A_SetAngle(angle + random(-45, 45))
    // Count shots in a user variable
    TROO F 0 A_SetUserVar("user_shots", user_shots + 1)
    // Different attack against imps or their subclasses (class name quoted)
    TROO F 0 A_JumpIf(checkclass("DoomImp", AAPTR_TARGET, true), "ImpTarget")
    // Branch on an ACS script's SetResultValue result
    TROO F 0 A_JumpIf(ACS_NamedExecuteWithResult("CheckObjective", args[0], args[1]) == 1, "ImpTarget")
    TROO G 6 A_TroopAttack
    Goto See
  ImpTarget:
    // Damage with variance
    TROO G 6 A_CustomComboAttack("DoomImpBall", 32, (random(0, 3) + 1) * 3)
    Goto See
  }
}
```

## Engine-family divergence

**Random and math functions:** UZDoom's DECORATE expression parser supports several functions absent from Zandronum DECORATE. Confirmed directly in UZDoom's `src/scripting/decorate/thingdef_exp.cpp`: `min(a, b)`, `max(a, b)`, `clamp(x, lo, hi)`, `atan2(y, x)`, `VectorAngle(x, y)`, and the client-side random variants `crandom`/`cfrandom`/`randompick`/`frandompick`/`crandompick`/`cfrandompick` (available in UZDoom DECORATE itself, not only ZScript as the wiki suggests). The shared core set (`random`/`frandom`/`random2` with optional RNG-isolation identifier `[name]`, `abs`, `sqrt`, `sin`, `cos`, `ACS_NamedExecuteWithResult`/`CallACS`) works identically on both. Extended math functions the wiki lists (`exp`, `log`, `log10`, `ceil`, `floor`, `round`, `tan`, `acos`, `asin`, `atan`, `cosh`, `sinh`, `tanh`) resolve via UZDoom's generic function-lookup mechanism in expressions; their availability in DECORATE specifically is not documented separately here.

**Assignment and mutation operators:** UZDoom's expression parser supports assignment (`=`) and compound-assignment operators (`+=`, `-=`, `*=`, `/=`, `%=`, `<<=`, `>>=`, `>>>=`, `&=`, `^=`, `|=`), and pre/post increment/decrement (`++`, `--`) as operators within expressions. Zandronum's DECORATE expression parser does not support any of these; its expressions are read-only (literals, identifiers, array indexing, the operators listed above, and function calls).

## See also

- [`constants.md`](constants.md) — `const`/`enum` declarations and user variables in actor definitions
- [`state-machine.md`](state-machine.md) — expression use in state-duration parameters (duration cannot be an expression in Zandronum DECORATE; see that file for details)
- [`creating-monsters.md`](creating-monsters.md) — actor properties and flags used with expressions
