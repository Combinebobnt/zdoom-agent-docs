# ZScript data types

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki "ZScript data types" (retrieved 2026-08-03, https://zdoom.org/w/index.php?title=ZScript_data_types&oldid=55475) + verified against the UZDoom source's `src/common/scripting/core/types.cpp`, `src/common/scripting/backend/codegen.cpp`, and `wadsrc/static/zscript/constants.zs`. The local UZDoom checkout is confirmed at version 5.0.0-pre; re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — one behavioral change found (int-to-`TextureID` cast, see `TextureID` section) plus one pre-existing doc inaccuracy corrected (`Sum()` description; see Verification notes). Everything else re-checked (vector/quat methods, swizzle accessors, `double.equal_epsilon`, the vectors/quats-in-dynamic-arrays restriction) matched with no drift.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

ZScript introduces a variety of primitive and container data types available within classes, structs, and functions. This document covers the primitive scalar type system, vector types, and related value types; see `classes/array.md` and `classes/associative-maps.md` for container types, and `concepts/function-pointers.md` for function references.

## Arithmetic types

### `bool`

Boolean value; `true` or `false`. Non-zero numeric values convert to `true` when assigned to a bool variable.

### `int`

32-bit signed integer. Supports constants:
- `int.min` — the lowest representable value (−2,147,483,648).
- `int.max` — the highest representable value (2,147,483,647).

### `uint`

32-bit unsigned integer (cannot be negative). Supports constants:
- `uint.max` — the highest representable value (4,294,967,295).

### `double`

64-bit IEEE 754 floating-point number. Supports:
- `double.NaN` — "not a number", used to invalidate a double; never equals anything, including itself.
- `double.max` — the largest representable value.
- `double.epsilon` — the smallest representable difference between distinct doubles.
- `double.equal_epsilon` — equivalent to 1/65536 (approximately 1.526e−5), matching the precision of Doom's 16.16 fixed-point format; useful for fixed-point-originated values.

For the `~==` (approximately-equal) operator, see `concepts/operators.md`, which documents it in detail with the exact tolerance value and type-specific behavior (including case-insensitive string comparison).

## Vector types

ZScript provides vector types with compile-time fixed dimensions. All vector types support length/normalization methods:
- `double Length()` — returns the Euclidean magnitude.
- `double LengthSquared()` — returns the magnitude squared (more efficient; avoids sqrt).
- `double Sum()` — returns the sum of the **absolute values** of all components (e.g. `(3, -4).Sum()` is `7`, not `-1`), not a plain algebraic sum. Source-verified: the codegen emits `FLOP_ABS` on each component before adding (`FxVectorBuiltin::Emit`, `NAME_Sum` case, `src/common/scripting/backend/codegen.cpp`). This detail is easy to miss and is not obvious from the method name.
- `Vector# Unit()` — returns a unit vector (magnitude 1) in the same direction. If the source vector has zero length, returns a vector with every component set to NaN.
- `double Angle()` — returns the angle formed by the XY components as a global angle in the range [−180, 180]. Equivalent to `atan2(vec.y, vec.x)`. Available on all vector types (the W component of Vector4/FVector4 is ignored).

### `Vector2` and `Vector3`

- **Vector2:** two-component vector with `.x` and `.y` members.
- **Vector3:** three-component vector with `.x`, `.y`, and `.z` members. Supports `PlusZ(double offset)` — returns a new Vector3 with z offset by the given amount.

### `Vector4`

Four-component vector with `.x`, `.y`, `.z`, and `.w` members. Also supports swizzle accessors:
- `.xyz` returns a `Vector3` containing the X, Y, Z components.
- `.xy` returns a `Vector2` containing the X, Y components.

Note: **Vectors currently cannot be stored in dynamic arrays.**

## Quaternion type

### `Quat`

A quaternion for representing rotations and orientations. Supports the same methods as vectors: `Length()`, `LengthSquared()`, `Unit()`, plus rotation-specific operations `Conjugate()` and `Inverse()`. Like vectors, quats **currently cannot be stored in dynamic arrays**.

## Member-variable-only types

The following types are valid only as class/struct member variables and are automatically converted to broader types when used inside functions:

- **`int8`, `int16`** — narrow signed integers, 8-bit and 16-bit respectively. Convert to/from `int` in function scope.
- **`uint8`, `uint16`** — narrow unsigned integers, 8-bit and 16-bit respectively. Convert to/from `uint` in function scope.
- **`float`** — 32-bit single-precision floating-point number. Converts to/from `double` in function scope.
- **`FVector2`, `FVector3`, `FVector4`** — single-precision vector types. Convert to/from their double-precision equivalents (`Vector2`/`Vector3`/`Vector4`) in function scope.
- **`FQuat`** — single-precision quaternion. Converts to/from `Quat` in function scope.

**Important:** `FVector*` types do not interoperate with double-precision `Vector*` types for dot/cross products — operations between `FVector3` and `Vector3` will not compile.

## String and Name types

### `String`

Case-sensitive text strings, enclosed in double quotes: `"MyString"`. Supports relational operators and `~==` for case-insensitive comparison. Strings can be directly converted to/from `name` types.

### `Name`

Case-insensitive text strings, enclosed in single quotes: `'myname'`. When a string is converted to a name, the result is lowercased (e.g., `name x = "MyString"` assigns `'mystring'`). Supports relational operators but not string formatting.

## Special value types

### `Sound`

Represents a sound name as defined in SNDINFO. ZScript cannot read audio file names directly; only sounds exposed to SNDINFO can be used in audio functions like `A_StartSound`. Invalid sound names (attempting to cast a string/name that isn't a valid SNDINFO nicename to a `Sound` type) result in an empty `Sound` value (`""`).

### `StateLabel`

Represents the name of a state sequence label, enclosed in double quotes: `"MyStateLabel"`. These are **not** strings and cannot be converted to/from strings. However, a string can be converted to a `StateLabel` via `FindStateByString()`. A special case:
- `null` means "no state" and should be used when a jump function should not jump.
- `"Null"` (the string literal `"Null"`) is an actual state label defined in the base Actor class that destroys the actor after 1 tic — use it when the actor should be destroyed.

### `Color`

Represents a color with 4 components: alpha (a), red (r), green (g), blue (b), each in the range 0−255. Can be defined as:
- A named color string: `color c = "red";`
- ARGB function: `color c = color(255, 255, 0, 0);` for opaque pure red
- RGB function (alpha defaults to 255): `color c = color(255, 0, 0);` for opaque red
- Hexadecimal: `0xFFFF0000` (ARGB) or `0xFF0000` (RGB)
- Hex string: `"FF0000"` (RGB, converted internally)

**Important caveat:** Reading certain actor color properties (like `bloodcolor`) requires masking off the alpha channel — `(bloodcolor & 0xffffff)` — before the value can be used correctly in some contexts.

### `TextureID`

The integer ID of a texture. All graphics have TextureIDs, not just map textures. Can be obtained and managed via the `TexMan` struct's methods.

**Changed in this re-verification (2026-08-03, commit fbad53bff5):** an integer-typed expression can now be used anywhere a `TextureID` is expected — source-verified via a new branch added to `FxTypeCast::Resolve` (`src/common/scripting/backend/codegen.cpp`) that accepts any integer expression when the target type is `TextureID`; absent at the prior verification commit 515ea869f4. This mirrors the int-to-`SpriteID` conversion that already existed. Two details confirmed by reading the surrounding code: the branch doesn't check the cast's explicit/implicit flag, so this applies to plain assignment and argument-passing (`TextureID t = 5;`), not just an explicit cast expression; and unlike the adjacent null-to-`TextureID` conversion (gated on `ctx.Version >= 4.14.1`), this new branch carries no ZScript `version` gate, so it applies regardless of a mod's declared version directive.

### `SpriteID`

The integer ID of a sprite, with specific constraints:
- Only images in the `/sprites/` subfolder of a PK3 (or between S_START/S_END markers in a WAD) following sprite naming rules generate SpriteIDs.
- SpriteIDs are only generated for sprites explicitly referenced in the `States` block of some actor class in the loaded archives.
- A SpriteID contains only the 4-character sprite name (e.g., `"BAL1"`) — not the frame letter or rotation number. Frame information is stored separately (actors have a `sprite` field holding the SpriteID and a separate `frame` field holding the frame letter as a 0-indexed integer).
- **SpriteIDs cannot be directly converted to TextureIDs** — they lack the full texture information. Use `GetSpriteTexture()` to obtain the TextureID for a sprite used in a specific actor's state.

To obtain a SpriteID from a sprite name, use `GetSpriteIndex("NAME")` where the sprite must be defined in some loaded actor's states.

### `Class types`

`class<ClassName>` holds a reference to a class name and can be passed to functions expecting a class argument. If an invalid class name is assigned, the engine throws an error at assignment time.

Example:
```zscript
class<Actor> projectile = 'RocketProjectile';
if (CountInv('GrenadeAmmo')) {
    projectile = 'GrenadeProjectile';
}
A_FireProjectile(projectile);
```

## Verification notes

**Source-verified in UZDoom source:**
- Vector4/FVector4/Quat/FQuat type registration and existence.
- Vector methods: `Length()`, `LengthSquared()`, `Unit()`, `PlusZ()`, `Angle()`, `Sum()` (confirmed `Sum()` sums absolute values per-component via `FLOP_ABS`, not a plain sum — this was true at both the original verification commit and the current one, so it's a doc correction, not a behavioral change from the upstream pull).
- Quaternion methods: `Conjugate()`, `Inverse()`.
- `double.equal_epsilon` constant (in active use in `wadsrc/static/zscript/constants.zs`).
- Vector4/FVector4 swizzle accessors (`.xyz`, `.xy`).
- Quat does **not** expose `Sum()`/`Angle()` (only `Length()`, `LengthSquared()`, `Unit()`, `Conjugate()`, `Inverse()` are dispatched for quaternions in `FxMemberFunctionCall::Resolve`) — confirms the doc's Quat method list above is complete as written, not an omission.
- The "vectors/quats cannot be stored in dynamic arrays" restriction, **corrected during this re-verification pass (2026-08-15) — the previous note's stated mechanism was wrong**: the actual gate is in `src/common/scripting/frontend/zcc_compile.cpp`'s `DetermineType()` (`AST_DynArrayType` case), which rejects an element type unless `GetRegType() != REGT_NIL && GetRegCount() <= 1`, with one hand-coded exception for the internal `TRS` struct (a translation/rotation/scaling struct used for animation-frame arrays, `Array<TRS>` in `actors/actor.zs`): `zcc_compile.cpp` special-cases `TypeName == "TRS"` to bypass the gate outright, and `types.cpp`'s `NewDynArray()` has its own matching special case (a dedicated `DynArray_TRS` backing type) that makes the bypassed call actually resolve. Vector2/Vector3/Vector4/FVector2/FVector3/FVector4/Quat/FQuat all **explicitly set `RegType = REGT_FLOAT`** in `types.cpp` — contrary to what this note previously claimed, they are not left at the `REGT_NIL` default — but they set `RegCount` to 2, 3, 4, or 4 (vs. the base `PType` default of 1), so they fail on the `GetRegCount() > 1` half of the check, not a `REGT_NIL` half. `types.cpp`'s `NewDynArray()` backing-type switch (`REGT_INT`/`REGT_FLOAT`/`REGT_STRING`/`REGT_POINTER` cases, `default:` errors) is downstream of this gate and is never reached for a plain vector/quat type at all — it's real code, just not the code that actually blocks vectors. The end-user-facing conclusion (vectors/quats cannot be stored in dynamic arrays) is unchanged and still correct; only the previously-documented reasoning was wrong. `zcc_compile.cpp`, `types.cpp`, and `actors/actor.zs` are all unchanged between the last-cited commit and current HEAD (`5a9b0ec511`), so this was a pre-existing documentation error, not new drift.
- Int-to-`TextureID` cast — new as of commit fbad53bff5 (was absent at the 515ea869f4 verification baseline); see the `TextureID` section above.

**Wiki-trusted, not independently verified in local source:**
- Arithmetic constants (`int.min`/`max`, `uint.max`, `double.max`/`NaN`/`epsilon`).
- Member-variable-only type conversion behavior in function scope.
- SpriteID generation rules and limitations.
- The `bloodcolor & 0xffffff` mask requirement.
- StateLabel's `"Null"` state behavior (actor destruction).

## Not yet documented from the intake page

This file deliberately omits:
- **Declaration modifiers** (unsafe, sealed, internal, native, readonly, meta, transient, const access/scope modifiers) — these are orthogonal to types and belong in their own `concepts/declaration-modifiers.md`.
- **Linked lists** — documented separately (Inv, GetDropItems, psprites iteration).
- **Structs and State types** — outside this document's scope.
- **Constants** (untyped const declaration) — brief mention in wiki but merits separate coverage.

## See also

- [Function pointers](function-pointers.md) for `Function<...>` type and indirect function calls.
- [Dynamic arrays](../classes/array.md) and [Associative maps](../classes/associative-maps.md) for container types.
- [Operators](operators.md) for `~==` and other operator semantics.
- [Object scopes and versions](object-scopes-and-versions.md) for scope keywords and version directives.
- [ZScript engine availability](zscript-engine-availability.md) — this entire document applies only to UZDoom/GZDoom-family engines, not Zandronum.
