# ZScript structs: semantics and native vs. scripted

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki `Structs` (retrieved 2026-08-03, https://zdoom.org/w/index.php?title=Structs&oldid=55083) + verified against the
UZDoom source's `src/common/scripting/frontend/zcc_compile.cpp:2459-2463` (return type handling)
and `zcc_compile.cpp:2670-2675` (parameter handling); re-verified 2026-08-03 against UZDoom
5.0.0-pre (commit fbad53bff5) after upstream pull — no behavioral drift found (the cited logic is
byte-identical between commits, only shifted by unrelated insertions earlier in the file; corrected
line range: `zcc_compile.cpp:2459-2463`), but this pass also corrected a pre-existing, mis-verified
claim about the `out` modifier (see below) that predates this re-verification and was not caused by
the upstream pull.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

Structs in ZScript are data containers defined at module scope and instantiated in actors/classes.
They behave similarly to C++ structs: they can hold member variables of any type, nested enums,
and member functions.

## Pass-by-reference semantics

Structs (distinct from the built-in vector/quaternion types) are always passed and returned as
pointers, not as values. A function parameter of struct type receives a pointer, and a function
return type of struct type is automatically wrapped as a pointer. **This is structural, not
optional** — the compiler transparently converts struct parameters and return values to pointer
form (see the UZDoom source's `src/common/scripting/frontend/zcc_compile.cpp:2459-2463` for
return types).

**Correction (2026-08-03): the `out` modifier has no effect on a struct parameter's mutability.**
For struct-typed parameters (and dynarray/map parameters, which share the same pointer-wrapping
path), the pointer-construction call at `zcc_compile.cpp:2673` is written to take a second,
const-controlling argument based on whether the parameter is `out` — but that argument is
commented out in the actual call, so it always defaults to non-const regardless of `out`. A plain
(non-`out`) struct parameter therefore receives an equally writable pointer as an `out` one, and
its fields can be mutated inside the function body either way; this is confirmed independently by
the field-write-permission check in `codegen.cpp:7647-7648`, which gates writability on the pointer's
const flag — always false for both cases here. This diverges from the source's own inline comment
one line above the call, which describes the intended-but-unimplemented behavior ("unless marked
'out' that pointer must be readonly"): no code path in `CompileFunction` actually sets read-only-ness
based on `out` for struct/dynarray/map parameters (grepping the function for `ZCC_Out` finds no
other use). This has been true since `out` parameters were introduced and is not new drift from the
UZDoom source's most recent commit range. `out` does still matter for parameters of register-backed
types (`int`, `float`, etc.), where it sets `VARF_Out` and affects both calling convention and a
caller-side check that the passed argument is itself a modifiable value — that branch is unaffected
by this correction.

## Native structs vs. scripted structs

**Scripted structs** are user-defined structs declared in your script: they are value types
instantiated locally (e.g., `MyStruct s;`). The struct's data is stack-allocated, and the struct
itself is passed/returned by pointer to other functions.

**Native structs** are built-in structs exposed from the engine (e.g., `NetworkCommand`, `WorldEvent`,
`RenderEvent` from the ZScript standard library, or `Console`, `CVar`, `LevelLocals` from the native
struct inventory). These **cannot be instantiated** — you cannot declare a local variable of a native
struct type. You can only hold references to them, typically through class members or function
parameters (see the UZDoom source's `src/common/scripting/frontend/zcc_compile.cpp:2292`).

## Limitations

Structs cannot generally be used as the element type of dynamic arrays; use a class instead if an
array of many instances is needed. This is a structural VM constraint, not a syntactic one; the
compiler forbids array type declarations whose element type isn't register-backed, with one narrow,
user-visible exception: the native `TRS` struct (used for actor bone transforms, exposed as
`Array<TRS> frameData` on `Actor`) is special-cased to allow `Array<TRS>`. A small number of other
native, engine-internal array declarations are also carved out, but those aren't reachable from
user script code.

## Wiki/engine divergence: return-by-value and pass-by-reference

The saved ZDoom Wiki page states "Structs currently cannot be returned, nor can they be passed
normally. They must be passed by reference." This is more restrictive than the actual UZDoom
behavior: structs *can* be returned and passed, and they are automatically converted to pointer
form rather than requiring manual reference syntax. The practical effect is similar (pass-by-reference
semantics), but the mechanism is automatic pointer wrapping at compile time.
