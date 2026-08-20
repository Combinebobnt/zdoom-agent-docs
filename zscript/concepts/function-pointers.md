# Function pointers

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki `Function pointers` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=Function_pointers&oldid=54363) + verified against the UZDoom source's `src/common/scripting/backend/codegen.cpp` (restrictions, `.call()` mechanics) and `wadsrc/static/zscript/engine/base.zs` (standard-library interface); re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — no behavioral drift found.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

Function pointers in ZScript allow you to store references to functions and call them indirectly. They enable callbacks (different functions with the same type signature), runtime polymorphism without class inheritance, and cross-mod integration patterns.

## Declaring function pointers

A function pointer is declared with the type `Function<scope signature>`, where:
- **scope** is one of `play`, `ui`, or `clearscope` — determines which execution context the pointed function must run in. See the ZScript scope documentation for details on these contexts.
- **signature** is the function's return type followed by its parameter types in parentheses, e.g., `void()` for no parameters/no return, or `double(int, string)` for a function taking an int and string and returning a double.

Example declarations:
```zscript
Function<play void()> myCallback;
Function<clearscope int(Object)> myObjectProcessor;
Function<ui double(double, double)> myUiMath;
```

## Supported and unsupported function types

Function pointers can only point to **static functions and instance methods**. The following function kinds **cannot** be referenced:
- **Action functions** — these are hardcoded into the state machine and don't have first-class callable values.
- **Virtual functions** — the VM doesn't support taking pointers to virtual methods; you must use inheritance and method overrides instead.

The compiler enforces this restriction at compile time: converting an action or virtual function to a function pointer type is rejected with a single shared error, `"virtual/action function pointers are not allowed"` (`src/common/scripting/backend/codegen.cpp`'s `convertRawFunctionToFunctionPointer`), and the same two flags (`VARF_Virtual | VARF_Action`) are checked again when a function-pointer-typed class property resolves its `"Class::Function"` string default (`NativeFunctionPointerCast`).

**Variadic functions** (functions with `...` parameters, e.g. `Console.Printf`) are not independently verified as blocked. No dedicated compile-time check against the vararg flag was found anywhere in the function-pointer assignment or cast paths — the only rejection is the shared virtual/action one above. Whether pointing to a native vararg function actually works (and, if so, what happens to arguments past the fixed parameter list when called through `.call()`) is unverified; treat the "not supported" framing as unconfirmed rather than a documented restriction.

## Assigning function pointers

If the class context is known, you can assign a function by reference:
```zscript
Function<play void()> ref = MyClass.MyMethod;
```

Alternatively, use the `FindFunction()` static method to look up a function by class and name at runtime:
```zscript
Function<void> ref = Object.FindFunction(MyClass, 'MyMethod');
```

The `FindFunction` method is defined on the Object class and takes a class type and a name, returning a generic `Function<void>` that you must cast to the appropriate signature.

## Calling function pointers

Function pointers are invoked using the `.call()` syntax (this is compiler-special-cased, not a real method):
```zscript
result = myFunctionPtr.call(self, arg1, arg2);
```

The first argument must be the appropriate `self` context (the instance or class, depending on whether the function is an instance method or static function). Subsequent arguments match the declared signature.

## Casting function pointers

Function pointer casts follow **covariant return types and contravariant parameter types** — the same variance rules as method override compatibility:

**Covariant returns:** A function pointer can be widened to point to a more general return type:
```zscript
Function<play Actor()> getActor = /* ... */;
Function<play Object()> getObject = (Function<play Object()>)(getActor);  // OK: Actor is-a Object
```

**Contravariant parameters:** A function pointer can be narrowed to accept more specific parameter types:
```zscript
Function<play void(Object)> acceptObject = /* ... */;
Function<play void(Actor)> acceptActor = (Function<play void(Actor)>)(acceptObject);  // OK: Actor is more specific
```

The cast syntax requires two sets of parentheses: `(Function<...>)(value)`.

## Function pointers in properties

Within a class property definition, you can initialize a function pointer field with a reference specified as a string in the format `ClassName::FunctionName`. This is **not** resolved per-instance at object creation: the string is parsed and the function looked up once, at the end of script compilation (`ZCCDoomCompiler::InitDefaultFunctionPointers`, called from `ZCCDoomCompiler::Compile()` after states and functions are compiled), and the resolved pointer is written directly into the class's default field data. Every instance of the class then inherits that already-resolved pointer through the normal default-value-copying mechanism, the same as any other default-initialized field — there is no per-instantiation lookup cost or possibility of late binding:

```zscript
property myFunc: myFuncField;

Default
{
  MyClass.myFunc "SomeClass::SomeMethod";
}
```

## Known limitations and unverified notes

- **Multiple return values via function pointers:** The wiki example shows nested function-pointer signatures returning multiple values (e.g., `Function<...(...)>` pointing to a function that returns a tuple). This syntax appears in the example but is not independently verified against the UZDoom grammar or VM implementation.
- **Returning function-pointer results directly:** The wiki notes a bug (#2210 in the ZDoom tracker) where calling `return functionPointerVar.call(self);` directly doesn't work, requiring intermediate assignment. This specific bug is not independently verified in the local UZDoom source and may be outdated.

## See also

- ZScript scope documentation (`concepts/zscript-scopes.md` — if it exists) for details on `play`, `ui`, and `clearscope`.
- `Object.FindFunction` in the standard library for runtime function lookup.
