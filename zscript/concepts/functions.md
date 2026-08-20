# ZScript function declarations and modifiers

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki "ZScript functions" (retrieved 2026-08-03, https://zdoom.org/w/index.php?title=ZScript_functions&oldid=54598) + verified against the UZDoom source's `src/common/scripting/frontend/zcc-parse.lemon` (grammar), `src/common/scripting/frontend/zcc_compile.cpp` (semantic checks), `src/common/scripting/backend/vmbuilder.cpp` (register/constant limits), and `src/common/scripting/vm/vm.h` (return limits); re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — no behavioral drift found
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

Functions in ZScript are defined similarly to C++ functions and can be qualified with modifiers controlling their scope, virtuality, and execution context. This page covers function-declaration syntax and modifiers.

## Basic syntax

Functions are declared with an optional return type, name, parameter list, and body:

```zscript
int MyFunction(int param1, int param2)
{
    return param1 + param2;
}

void SideEffectOnly()
{
    // void functions need no return statement
}
```

## Multiple returns

Functions can return multiple values as a tuple by specifying comma-separated return types:

```zscript
int, int, bool MyFunction(int a, int b)
{
    return a, b, true;
}
```

A caller can assign multiple returns in several ways. The assignment uses bracket syntax `[var1, var2, ...]`, matched positionally against the function's return values from left to right. A caller may provide fewer targets than the function returns — but the values dropped are always the trailing (rightmost) ones, since matching starts at the first return value. There's no way to skip an early return value while still capturing a later one; an unwanted early value still needs a variable to receive it (e.g. a throwaway):

```zscript
int x, y;
bool flag;
[x, y, flag] = MyFunction(1, 2);  // Assign all three

// If only the flag is needed (second element doesn't matter):
int throwaway, z;
bool result;
[throwaway, z, result] = MyFunction(3, 4);  // throwaway gets ignored

// Using 'let' for automatic typing:
let [num1, num2, mybool] = MyFunction(5, 6);  // Types inferred from return types
```

**Important constraint:** Each assignment target must be an actual variable of the appropriate type — literal values or complex expressions are not permitted on the left side of the bracket assignment.

## Referencing: `in` and `out` parameters

Parameters can be qualified with `in` or `out` (or both as `in out`) to enable pass-by-reference semantics. This is especially useful for modifying struct instances or large objects that would be expensive to copy:

- **`out`** — the parameter receives a writable reference. The function can modify the argument's contents.
- **`in`** — documented/intended as a read-only reference, but current UZDoom source does not actually enforce this for struct parameters: the compiler always builds a writable pointer for struct-by-reference parameters regardless of the `in`/`out` qualifier, so writes through an `in` parameter currently compile without error (see "Wiki/engine divergence" below).
- **`in out`** (both) — the parameter receives a writable reference for both reading and modification.

```zscript
struct MyData
{
    int value;
    string name;
}

void ModifyData(in out MyData data)
{
    data.value = 42;
    data.name = "modified";
}

void CallIt()
{
    MyData d;
    ModifyData(d);  // d is now modified
}
```

**Struct-specific note:** Structs are always passed as pointers regardless of the `in`/`out` qualifier — the modifier only controls whether the pointer itself permits writes. For details, see [ZScript structs: semantics and native vs. scripted](structs.md).

## Function types

### Static

The `static` modifier marks a function as not belonging to any instance. A static function has no implicit `self` and cannot access instance variables. It must be called via the class or struct name:

```zscript
class MyClass
{
    static void StaticMethod()
    {
        // No access to instance fields
    }
    
    void InstanceMethod()
    {
        MyClass.StaticMethod();  // Call static via class name
    }
}
```

### Action

The `action` modifier is for non-static methods on `Actor` subclasses (or classes inheriting from `StateProvider` — most notably `Weapon` and `CustomInventory`) that will be called directly from a state block. When an action function is invoked from a state, the engine passes three implicit parameters:

- **`invoker`** — the owner of the PSprite/overlay (typically a `Weapon`, `Armor`, or `CustomInventory` for weapon/inventory states). This is the object containing the state being executed.
- **`self`** — the player pawn (the `PlayerPawn` actor).
- **`stateInfo`** — a read-only structure containing metadata about the state (the owning state's index, flags, and duration).

```zscript
class MyWeapon : Weapon
{
    action void FireWeapon()
    {
        // invoker is this Weapon; self is the player pawn; stateInfo describes the state
        invoker.DepleteAmmo(invoker.bAltFire);  // Modifying the weapon itself
        self.DamageMob();  // Modifying the player
    }
}
```

**Important:** When calling an action function from non-state code (e.g., from a regular method), you must call it via the `invoker.` prefix if you want to refer to the invoker actor — `invoker.DepleteAmmo()` not just `DepleteAmmo()`. Action functions cannot be assigned to function pointers (see [Function pointers](function-pointers.md)).

For scope qualifications on action functions (e.g., `action(Weapon)`), see the [Converting DECORATE code to ZScript](decorate-to-zscript-conversion.md) page.

### Virtual and override

The `virtual` modifier allows a method to be overridden in child classes. A child class uses the `override` keyword in place of `virtual` when providing an implementation:

```zscript
class Parent
{
    virtual void MyMethod(int arg1, int arg2 = 0)
    {
        // Default implementation
    }
}

class Child : Parent
{
    override void MyMethod(int arg1, int arg2)
    {
        // Child implementation
        Super.MyMethod(arg1, arg2);  // Call parent's implementation
    }
}
```

**Signature matching:** The override's signature must match the parent's one-to-one, excluding parameter names. This is enforced at compile time.

**Default parameters:** Default parameter values cannot be specified in an override — they must be omitted. If the parent declares defaults, an override that omits those defaulted parameters will have those parameters become inaccessible (the override still compiles and works, but callers cannot invoke it without all arguments):

```zscript
class Parent
{
    virtual void Method(int a, int b = 99)
    {
        // b defaults to 99
    }
}

class Child : Parent
{
    override void Method(int a, int b)
    {
        // Cannot specify "int b = 99" here; it's forbidden
        // But callers can still invoke this with two args
    }
}
```

To invoke the parent's implementation from within an override, use the `Super.` prefix (with capital S, which is the conventional style in the stdlib):

```zscript
override void PostBeginPlay()
{
    PerformCustomSetup();
    Super.PostBeginPlay();  // Call parent; usually necessary for engine behavior
}
```

For a full discussion of virtual functions in the class hierarchy and on actors specifically, see [ZScript class definitions, modifiers, and hierarchy](zscript-class-definitions.md).

## Function limits

ZScript functions are subject to the following per-function constraints:

- **Registers:** 256 registers per type — integer, floating-point, string, and address registers each have their own independent pool of up to 256 (1024 total across all four types combined).
- **Constants:** 32767 integer constants, 32767 floating-point constants, 32767 string constants, and 32767 address constants per function. These limits apply to constant values embedded in bytecode; they are rarely hit in practice due to constant folding and deduplication.
- **Return values:** A single function call can return at most 8 values (via multiple-return syntax).

**Verification note:** Confirmed as an explicit, enforced hard limit (not merely an inference from instruction width): the bytecode emitter's generic operand-encoding path checks each operand index — whether it addresses a register or a per-type constant-table entry — against 32767 once cheaper encodings are exhausted, and aborts with `"Register limit exceeded"` if still over. That check and message are unchanged by the 2025-11-30→2026-08-01 upstream pull.

## Wiki/engine divergence

1. **Error found and corrected in the 2026-08-15 re-verification pass:** the "Multiple returns" section previously stated that "only the rightmost (final) variables must be assigned — earlier ones can be omitted by using a temporary." This had the direction backwards. `FxMultiAssign::Resolve` and `FxMultiAssignDecl::Resolve` (`src/common/scripting/backend/codegen.cpp`) match bracket-assignment targets to a function's return values positionally starting from index 0 (target `i` receives return value `i`), and reject the assignment ("Insufficient returns") if there are more targets than return values. A caller may provide fewer targets than the function returns, but the return values that get silently dropped are always the *trailing* (rightmost) ones — there is no bracket syntax (e.g. a blank slot) for skipping an early return value while still capturing a later one; an unwanted early value must still be captured into a variable such as a throwaway.

2. **Error found and corrected in the 2026-08-15 re-verification pass:** the `in` qualifier's read-only enforcement is not actually implemented in the current UZDoom source for struct parameters. In `zcc_compile.cpp`'s function-parameter handling, struct-by-reference parameters are always wrapped in a pointer via `NewPointer(type)`, whose const-controlling second argument is commented out in source (leaving it at its default of non-const) rather than driven by whether the parameter was declared `out`. `FxStructMember::RequestAddress` (`codegen.cpp`) gates struct-member writability on that same pointer's const flag, so a field write through an `in`-qualified struct parameter currently compiles without error. Source history shows the const-toggle was disabled during a 2017 refactor and never restored — this is a long-standing gap rather than new drift, but it means the qualifier is currently intent-only for structs, not compiler-enforced.

## See also

- [Multiple returns](../concepts/functions.md#multiple-returns) for destructuring patterns.
- [ZScript scope documentation](object-scopes-and-versions.md) for `play`, `ui`, `clearscope`, and virtual scope.
- [Function pointers](function-pointers.md) — function pointers cannot point to action, virtual, or variadic functions.
- [ZScript structs: semantics and native vs. scripted](structs.md) — how struct parameters interact with `in`/`out`.
- [Converting DECORATE code to ZScript](decorate-to-zscript-conversion.md) — action function scope qualifiers and invoker usage patterns.
