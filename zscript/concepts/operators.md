# ZScript operators

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki `Operators (ZScript)` (retrieved 2026-08-03, https://zdoom.org/w/index.php?title=Operators_%28ZScript%29&oldid=55515) + spot-checked against UZDoom source for operator grammar, division semantics, and approximate-equality tolerance; re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — no behavioral drift found. `zcc-parse.lemon` and `vectors.h`/`vm.h` picked up only license-header/whitespace changes plus a mechanical `VM_EPSILON`→`EQUAL_EPSILON` rename (same `1/65536.` value, now `constexpr` instead of `#define`); the `<=>`/`<>=` version gate (ZScript 4.15.1+) and constant-folded division/modulo/comparison logic in `codegen.cpp` are byte-for-byte unchanged. `NativeRandom`/`NativeFRandom` were reimplemented in the same pull but are unrelated to this doc (no `random()`/`frandom()` content here).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

ZScript operators, in order of precedence (highest to lowest), with their associativity:

| Precedence | Operator | Description | Associativity |
|---|---|---|---|
| 1 | `A::B` | Scope | Left-to-right |
| 2 | `A.B` | Member Access | Left-to-right |
| 2 | `(A)` | Parentheses | Left-to-right |
| 3 | `A++` | Post-increment | Right-to-left |
| 3 | `A--` | Post-decrement | Right-to-left |
| 3 | `++A` | Pre-increment | Right-to-left |
| 3 | `--A` | Pre-decrement | Right-to-left |
| 3 | `+A` | Unary Plus | Right-to-left |
| 3 | `-A` | Unary Minus | Right-to-left |
| 3 | `!A` | Logical Not | Right-to-left |
| 3 | `~A` | Bitwise Not | Right-to-left |
| 4 | `A ** B` | Exponentiation | Left-to-right |
| 5 | `A * B` | Multiplication | Left-to-right |
| 5 | `A / B` | Division | Left-to-right |
| 5 | `A % B` | Modulo | Left-to-right |
| 5 | `A cross B` | Cross Product (vectors) | Left-to-right |
| 5 | `A dot B` | Dot Product (vectors) | Left-to-right |
| 6 | `A - B` | Subtraction | Left-to-right |
| 6 | `A + B` | Addition | Left-to-right |
| 7 | `A << B` | Bitwise Shift Left | Left-to-right |
| 7 | `A >> B` | Bitwise Shift Right | Left-to-right |
| 7 | `A >>> B` | Bitwise Unsigned Shift Right | Left-to-right |
| 8 | `A & B` | Bitwise And | Left-to-right |
| 9 | `A ^ B` | Bitwise Xor | Left-to-right |
| 10 | `A \| B` | Bitwise Or | Left-to-right |
| 11 | `A .. B` | String Concatenation | Left-to-right |
| 12 | `A < B` | Less Than | Left-to-right |
| 12 | `A > B` | Greater Than | Left-to-right |
| 12 | `A <= B` | Less Than or Equal To | Left-to-right |
| 12 | `A >= B` | Greater Than or Equal To | Left-to-right |
| 12 | `A <=> B` | Three-Way Comparison | Left-to-right |
| 12 | `A is B` | Class Inheritance Check | Left-to-right |
| 13 | `A == B` | Equal To | Left-to-right |
| 13 | `A != B` | Not Equal To | Left-to-right |
| 13 | `A ~== B` | Approximately Equal To | Left-to-right |
| 14 | `A && B` | Logical And | Left-to-right |
| 15 | `A \|\| B` | Logical Or | Left-to-right |
| 16 | `C ? A : B` | Ternary Operator | Right-to-left |
| 17 | Assignment operators | See below | Right-to-left |

## ZScript-specific semantics

### Division: integer truncation vs. float result

Integer division truncates toward zero (does not round). If both operands are integers, the result is an integer. To get a floating-point result, at least one operand must be a `double`:

```zscript
int foo = 5 / 2;       // foo = 2 (truncated)
double bar = 5.0 / 2;  // bar = 2.5
double baz = 5 / 2.0;  // baz = 2.5
```

### `~==` (Approximately Equal): tolerance and type behavior

The `~==` operator checks approximate equality using a fixed tolerance of 1/65536.0 (approximately 0.0000152587890625) for floating-point and vector types. For strings, it performs a case-insensitive comparison.

Floating-point numbers should be compared with `~==` rather than `==` because floating-point arithmetic introduces rounding error:

```zscript
double d1 = 5 / 3.0;
double d2 = 1.666666;
if (d1 ~== d2) {
  // True because the difference is within tolerance
}
```

When applied to vectors, `~==` checks each component against the tolerance:

```zscript
Vector3 v1 = (0.0, 0.0, 0.0);
Vector3 v2 = (0.00001, 0.00001, 0.00001);
if (v1 ~== v2) {
  // True because each component difference is within 1/65536.0
}
```

String comparison via `~==` is case-insensitive:

```zscript
string s1 = "Hello";
string s2 = "HELLO";
if (s1 ~== s2) {
  // True
}
if (s1 == s2) {
  // False (case-sensitive)
}
```

### `is` operator: class inheritance

The `is` operator checks whether a class inherits from another class (i.e., whether it is the same class or a subclass):

```zscript
Actor target = // ...
if (target is 'DoomImp') {
  // True if target is a DoomImp or a subclass of DoomImp
}
```

The `is` operator can be used on both class type pointers and actor instance pointers. It does **not** work on class names obtained from `GetClassName()` (which returns a `name`, not a class type).

### `..` operator: string concatenation

The `..` operator appends one value to a string:

```zscript
string result = "Hello " .. "World";
string label = "I am a " .. GetClassName();  // GetClassName() returns a name, cast to string
```

This operator can perform type-to-string casts that `String.Format` does not support — for instance, casting a `SpriteID` to its sprite name:

```zscript
Console.Printf("Current sprite: " .. curstate.sprite);  // prints e.g. "BAL1"
```

### `<=>` and `<>=` operators: three-way comparison

The `<=>` operator (preferred) and `<>=` operator (deprecated in UZDoom 4.15.1+) perform a numeric three-way comparison, returning:
- `-1` if the left operand is less than the right
- `0` if they are equal
- `1` if the left operand is greater than the right

The `<=>` form requires ZScript version 4.15.1 or above in UZDoom.

### Increment/Decrement: pre vs. post return values

Both `++` and `--` have pre- and post- forms:

- **Post-increment/decrement** (`i++`, `i--`): evaluates to the variable's value *before* the operation
- **Pre-increment/decrement** (`++i`, `--i`): evaluates to the variable's value *after* the operation

```zscript
int i = 0;
int a = i++;   // a = 0, i = 1
int b = ++i;   // i = 2, b = 2
```

### Short-circuit evaluation with `&&` and `||`

The `&&` and `||` operators short-circuit: evaluation stops as soon as the result is determined. This is safe for null-checks:

```zscript
if (myPointer != null && myPointer.health > 0) {
  // If myPointer is null, the second condition is never evaluated,
  // so no null-pointer dereference occurs
}
```

## Notes on the precedence table

The precedence table above was verified against the UZDoom source grammar (`src/common/scripting/frontend/zcc-parse.lemon`). The `cross` and `dot` operators (vector operations) are implemented in the grammar but lack detailed documentation in the source — behavior verification was limited to their existence and precedence. The `>>` and `>>>` operators (shift operations) are similarly implemented but lack detailed UZDoom-source documentation; shift semantics follow standard C conventions.
