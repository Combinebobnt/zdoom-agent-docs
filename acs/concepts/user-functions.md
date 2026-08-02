# User-defined functions

**Tier:** A
**Engine:** Zandronum 3.2.1 (VM stack-overflow behavior below verified against the local `3.3-alpha` checkout per the usual 3.2.1-vs-3.3-alpha engine-scope caveat — see `../../shared/AUTHORING.md`).
**Provenance:** `_intake/Functions - ZDoom Wiki.html` (base ACS `function` syntax), cross-checked against the zt-bcc wiki's `Functions.md` (BCS extensions) and verified against the zt-bcc source's `src` (parser/semantic/codegen) and the Zandronum source's `src/p_acs.cpp` (VM). All compileability claims below were confirmed with live `bcc` compiles on 2026-07-29, not just read from source.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

## Base ACS syntax (what the ZDoom wiki page actually documents)

```
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

**Fork divergence:** the same wiki page also claims "calling a nested function recursively too
many times will eventually crash the game." This does **not hold** for this Zandronum fork.
`p_acs.cpp`'s function-call opcode handling checks, *before* touching the shared VM stack:

```cpp
if (sp + func->LocalCount + 64 > STACK_SIZE)
{ // 64 is the margin for the function's working space
    Printf ("Out of stack space in %s\n", ScriptPresentation(script).GetChars());
    state = SCRIPT_PleaseRemove;
    break;
}
```

(`STACK_SIZE` is 4096 — one shared stack for both expression evaluation and function calls.) Deep
or runaway recursion hits this guard, prints a console message, and removes *just that script
instance* (`SCRIPT_PleaseRemove`) — it does not corrupt engine state or crash the game. The only
way to actually hit a hard crash-equivalent (`I_Error("Out of bounds memory access in ACS VM")`
from `BoundsCheckingArray`) would be an access that bypasses this pre-check entirely, which
ordinary recursion doesn't do. Whether this guard was present in whatever ZDoom version the wiki
author tested against is unknown — record this as a fork-verified correction, not a claim about
upstream ZDoom.

## Latent-function restriction

Confirmed as a **hard compile-time error**, not merely a caveat: `semantic/expr.c`'s
`test_call_ded` rejects calling a latent dedicated (compiler-builtin) function whenever
`semantic->func_test` is set (i.e. the call site is lexically inside any function, named or
nested) — one diagnostic if inside a message-building block ("calling a latent function inside a
message-building block"), a different one otherwise ("calling a latent function inside a
function"), both followed by an educational note ("waiting functions like `` `delay` `` can only
be called inside a script"). Verified live:

```
void BadFunc() { Delay(5); }        // error: calling a latent function inside a function
script "Main" enter {
   void BadNested() { TagWait(1); } // error: calling a latent function inside a function
   BadNested();
}
```

**The exact, closed set of latent dedicated functions in this fork** (grepped from
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
