# User-defined functions

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-06)
**Provenance:** ZDoom Wiki `Functions` (retrieved 2026-08-06, https://zdoom.org/w/index.php?title=Functions&oldid=53571) for base ACS `function` syntax; cross-checked against the zt-bcc wiki's `Functions.md` (BCS extensions); verified against the zt-bcc source's `src` (parser/semantic/codegen) and the Zandronum source's `src/p_acs.cpp` (VM stack-overflow behavior and function-call guard re-verified 2026-08-06). All compileability claims were confirmed with live `bcc` compiles on 2026-07-29. The "Nested-function call/return bytecode" section was added 2026-08-14 while building nested-function support into an ACS/BCS decompiler (project-agnostic finding, not tied to that project) — verified against `zt-bcc/src/codegen/{expr,dec}.c` and `semantic/dec.c`, and against real `bcc`-compiled bytecode disassembled directly (both the non-recursive and recursive/`RECURSIVE_POSSIBLY` forms, including the emission-order-is-declaration-reverse finding, confirmed by compiling two sibling nested functions and reading their actual compiled addresses).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

## Base ACS syntax (what the ZDoom wiki page actually documents)

```text
function type function_name([type arg1 [, type arg2 [...]]])
{
   // body
   return value;
}
```

- `type` on the return position: use `void` for no return value.
- Every parameter must be typed; an empty parameter list still needs an explicit `void`
  (`function void F(void)`) in plain ACS — see below for how `bcc` relaxes this.
- `return` is optional but the function must ultimately return a value on every path if its
  return type isn't `void`.
- Functions cannot contain latent calls (see "Latent-function restriction" below) — the wiki
  page says this in one line ("you cannot use latent functions (such as Delay) in your
  functions") without saying which functions count as latent or what actually happens if you
  try; both are pinned down below.

This much is unremarkable and matches `bcc` as-is.

## BCS extensions over base ACS (not on the ZDoom wiki page at all)

The ZDoom wiki page is silent on all of the following; they come from `zt-bcc.wiki/Functions.md`
and were independently confirmed to compile with `zt-bcc`:

- **`function` keyword is optional, and so is `void` for an empty parameter list.** All three of
  these compile identically: `function void F(void){}`, `function void F(){}`, `void F(){}`.
- **Parameters can have default arguments** (`void Greet(str who = "Mate")`) — an omitted
  trailing argument at the call site uses the default. This also applies to *builtin* functions:
  `zt-bcc.wiki/Functions.md` notes `MorphActor(0)` now works as a single-arg call even though the
  underlying engine call takes 7 parameters, because the extra 6 have compiler-supplied string
  defaults.
- **A parameter can be unnamed** (`int Sum(int used1, int, int used2)`) — the caller must still
  pass an argument for the unnamed slot, but the function body has no way to reference it. Same
  rule applies to script parameters, not just function parameters.
- **`__FUNCTION__`** is a string-literal magic identifier holding the enclosing function's name
  (lowercased) — but it only resolves *inside a function body*. Confirmed by compile test: calling
  `Print(s: __FUNCTION__)` directly in a script's top-level body (not inside any function) fails
  with `` `__function__` not found `` — it is not a general "current scope" macro, and it is not a
  preprocessor macro either (can't be used in string-literal concatenation).
- **Nested functions**: a function can be declared inside a script body or inside another
  function ("nested function"), to arbitrary depth, and can read/write local variables of every
  enclosing scope (verified: mutating an outer local after defining a nested function that reads
  it, then calling the nested function, observes the mutated value — real capture-by-reference of
  the enclosing scope, not a snapshot). You cannot take a reference to a nested function
  (stated by `zt-bcc.wiki/Functions.md`; not independently re-verified here since it's a negative/
  absence claim that's awkward to compile-test directly — treat as tier-B-strength within this
  otherwise tier-A file).
- **`auto` return type**, valid only for nested functions: the compiler deduces the return type
  from what's actually returned (`auto F(){}` deduces `void`; `auto F(){ return "x"; }` deduces
  `str`).
- **Function literals**: `(auto()) { ...; return x; }()` declares an anonymous nested function
  and calls it in the same expression. Verified: `Print(d: (auto()){ return 42; }())` compiles and
  is usable as an inline expression producing a value.

## Recursion

The compiler statically tracks whether a function might call itself (directly or through a call
chain) and marks it `RECURSIVE_POSSIBLY` (`semantic/expr.c`), which routes it through a different,
slower codegen path in `codegen/dec.c` (dynamic local-variable save/restore instead of static slot
allocation) — this matches `zt-bcc.wiki/Functions.md`'s "might be too much a performance penalty"
framing.

The ZDoom-family ACS VM includes a call-stack-depth guard in function-call handling that prevents
the crash described in the wiki: `p_acs.cpp`'s function-call opcode handling checks, *before*
touching the shared VM stack:

```cpp
if (sp + func->LocalCount + 64 > STACK_SIZE)
{ // 64 is the margin for the function's working space
    Printf ("Out of stack space in %s\n", ScriptPresentation(script).GetChars());
    state = SCRIPT_PleaseRemove;
    break;
}
```

(`STACK_SIZE` is 4096 — one shared stack for both expression evaluation and function calls.) This
guard exists identically in both UZDoom and Zandronum and is not a fork divergence — it's shared
engine-family behavior inherited from a common ZDoom ancestor. Deep or runaway recursion hits this
guard, prints a console message, and removes *just that script instance* (`SCRIPT_PleaseRemove`)
— it does not corrupt engine state or crash the game. The only way to actually hit a hard
crash-equivalent (`I_Error("Out of bounds memory access in ACS VM")` from `BoundsCheckingArray`)
would be an access that bypasses this pre-check entirely, which ordinary recursion doesn't do.

## Nested-function call/return bytecode (compiled ABI)

Not covered by either wiki page — the exact compiled shape of a nested-function call/return,
verified against `zt-bcc` source and confirmed by disassembling real `bcc`-compiled output
(2026-08-14). Useful for anything that has to read or reconstruct compiled ACS/BCS bytecode
(a decompiler, a bytecode-level debugger, a hand-written disassembler) rather than just write
source against the language.

**A nested function has no ACS function index of its own.** It is not a real, separately
addressable function the way a top-level `function` is (no `PCD_CALL`/`PCD_CALLDISCARD` targets
it, and it never appears in the object's FUNC chunk). Its params and locals are instead extra
slots tacked onto the *enclosing* script/function's own local-variable frame, and calling it is a
same-frame jump-and-return, not an ACS-level function call.

**Non-recursive call site** (`codegen/expr.c`'s `call_local_user_func`):

```text
PUSHNUMBER <call-site id>   ; a small int, unique per call SITE (not per callee) within the entry
<argument-pushing code>      ; ordinary expression codegen, one value per parameter
GOTO <callee's prologue address>
<execution resumes here>     ; the callee's result, if any, is left on the stack at this exact address
```

**Non-recursive callee** (`codegen/dec.c`'s `write_one_nestedfunc`):

```text
<prologue>:
    ASSIGNSCRIPTVAR <last param's frame slot>   ; pops args in REVERSE order --
    ...                                          ; the LAST parameter is stored first
    ASSIGNSCRIPTVAR <first param's frame slot>
<body>                                            ; a mid-function `return` compiles to an
                                                   ; ordinary GOTO to <epilogue> below
<epilogue>:
    [PCD_SWAP]                                    ; ONLY emitted if the function returns a value --
                                                   ; swaps the return value above the call-site id
                                                   ; that's still sitting under it on the stack
    PCD_CASEGOTOSORTED <n>, <id0>,<return-point0>, <id1>,<return-point1>, ...
```

The trailing dispatch is **always** a sorted-case table (`PCD_CASEGOTOSORTED`), even for a
function with exactly one call site (`n=1`) — there is no simpler single-target return form. It
dispatches purely on the call-site id pushed at the very start of the call, jumping back into
the *caller's* own code right after that call's `GOTO`.

**Frame-slot allocation.** A nested function's parameters and locals occupy the frame slots
immediately *above* the enclosing entry's own declared locals (`start_index = <enclosing frame
size> + <recursion scratch area, see below> + <slots already claimed by an earlier-declared
sibling>`) — not a separate namespace. This is what makes "a nested function can read/write its
enclosing scope's locals" (see above) mechanically trivial: both live in the exact same frame,
addressed by the exact same `PUSHSCRIPTVAR`/`ASSIGNSCRIPTVAR` opcodes, with no special "outer
scope" addressing mode at all. Multiple sibling nested functions in the same entry stack their
frame slots one after another in the order described below. A nested function cannot declare a
local array or struct variable in its own body (`semantic/dec.c` rejects it outright,
"local array/struct variable declared inside nested function") — only scalars.

**Emission order is the REVERSE of source declaration order.** Semantic analysis *prepends* each
nested function to its enclosing entry's own list as it's encountered (`semantic/dec.c`'s
`s_test_nested_func`: `impl->next_nested = enclosing->nested_funcs; enclosing->nested_funcs =
func;`), and codegen (`write_nested_funcs`) walks that list head-first when emitting the actual
prologue/body/epilogue bytes. So of two sibling nested functions `A` (declared first in source)
and `B` (declared second), `B` is *written* first and ends up at the *lower* compiled address,
while `A` ends up at the *higher* address. This matches the language-level rule above that a
nested function can only call one already declared before it (never one declared later, and
never itself recursively without the compiler's separate recursion handling) — a callee is
always addressable at a *higher* compiled address than its caller's own address, one direct
consequence of the reversal.

**Recursive form** (`RECURSIVE_POSSIBLY`, see "Recursion" above) changes the prologue/epilogue
substantially, adding save/restore code around the plain param-store/dispatch shape above
(`codegen/dec.c:611-706`):

```text
<prologue>:
    ASSIGNSCRIPTVAR <temps-start + 0>            ; stash each incoming arg into a SHARED scratch
    ASSIGNSCRIPTVAR <temps-start + 1>            ; area at the very bottom of the whole nested-
    ...                                            ; function frame region (temps-start), common
                                                     ; to every recursive nested function in the entry
    PUSHSCRIPTVAR <this function's own frame slot 0>   ; save the CURRENT (outer activation's)
    PUSHSCRIPTVAR <this function's own frame slot 1>   ; value of every one of this function's own
    ...                                                  ; frame slots (params AND locals) --
                                                          ; restored at the epilogue
    PUSHSCRIPTVAR <temps-start + 0>              ; interleaved with restoring each stashed arg
    ASSIGNSCRIPTVAR <own frame slot N-1>          ; back from the temp area into the REAL param
    PUSHSCRIPTVAR <temps-start + 1>                ; slot -- reverse order again, one pair per
    ASSIGNSCRIPTVAR <own frame slot N-2>            ; parameter
    ...
<body>
<epilogue>:
    ASSIGNSCRIPTVAR <temps-start>                 ; stash the return value (if any) in the shared
                                                     ; scratch slot too, ONLY if the function
                                                     ; returns a value and has at least one frame slot
    ASSIGNSCRIPTVAR <own frame slot N-1>           ; restore every saved outer-activation value,
    ASSIGNSCRIPTVAR <own frame slot N-2>            ; DESCENDING this time (mirrors the ascending
    ...                                               ; save above)
    PUSHSCRIPTVAR <temps-start>                    ; re-push the stashed return value
    PCD_SWAP
    PCD_CASEGOTOSORTED ...
```

The "shared scratch area" (`temps-start`) is sized to the largest parameter list among every
*recursive* nested function in the entry, and sits directly above the enclosing entry's own
declared locals — non-recursive nested functions' own frame slots (and a recursive function's
own frame slots, above the scratch area) come after it. A recursive nested function with **zero**
parameters and **zero** locals compiles identically to the plain non-recursive form (every
`if (impl->size > 0)`/loop-bound-`0` guard above degenerates to nothing) — recursion only changes
the compiled shape when there's actually a frame slot to save and restore.

## Latent-function restriction

Confirmed as a **hard compile-time error**, not merely a caveat: `semantic/expr.c`'s
`test_call_ded` rejects calling a latent dedicated (compiler-builtin) function whenever
`semantic->func_test` is set (i.e. the call site is lexically inside any function, named or
nested) — one diagnostic if inside a message-building block ("calling a latent function inside a
message-building block"), a different one otherwise ("calling a latent function inside a
function"), both followed by an educational note ("waiting functions like `` `delay` `` can only
be called inside a script"). Verified live:

```text
void BadFunc() { Delay(5); }        // error: calling a latent function inside a function
script "Main" enter {
   void BadNested() { TagWait(1); } // error: calling a latent function inside a function
   BadNested();
}
```

**The exact, closed set of latent dedicated functions in zt-bcc** (grepped from
`zt-bcc/src/builtin.c`'s `g_deds[]` table for the `F_LATENT` flag — the wiki's "such as `Delay`"
undersells how small and enumerable this set is): `Delay`, `TagWait`, `PolyWait`, `ScriptWait`,
`NamedScriptWait` (internally `PCD_SCRIPTWAITNAMED`). All five already have their own per-function
docs in this tree: [Delay](../functions/delay.md), [TagWait](../functions/tagwait.md),
[PolyWait](../functions/polywait.md), [ScriptWait](../functions/scriptwait.md),
[NamedScriptWait](../functions/namedscriptwait.md). Action specials and extension functions are
never latent under this mechanism (the flag only exists on the dedicated/builtin table), and
neither `terminate`/`suspend`/`restart` nor `ACS_(Named)ExecuteWait` are affected by this check —
they're separate mechanisms (see [terminate](../functions/terminate.md),
[suspend](../functions/suspend.md), [restart](../functions/restart.md)).
