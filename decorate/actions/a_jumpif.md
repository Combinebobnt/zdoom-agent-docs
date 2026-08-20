# `void A_JumpIf(expression, int offset)` / `void A_JumpIf(expression, str "state")`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `A_JumpIf` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_JumpIf&oldid=42392) + verified against the
Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3523-3538` (`DEFINE_ACTION_FUNCTION_PARAMS(AActor,
A_JumpIf)`). Network behavior verified against `src/thingdef/thingdef_codeptr.cpp:695-753` (the `DoJump`
function called by the `ACTION_JUMP` macro) and `src/network.h:118-125` (the `ClientJumpUpdateFlag` enum).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `src/thingdef/thingdef_codeptr.cpp:3523` (`DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_JumpIf)`).
**Source excerpt:** Quotes Zandronum engine source; see [LICENSE](../../LICENSE) §3 for Zandronum's
license terms.

Evaluates a DECORATE expression and, if it evaluates to true, jumps to a specified state offset or
state label. The jump offset can be a numeric literal or an expression.

## Parameters

- **`expression`** — a DECORATE expression. This can include arithmetic, comparisons, actor variables,
  and built-in expression functions like `random()`, `frandom()`, `random2()`, `abs()`, `sqrt()`,
  `sin()`, `cos()`, `checkclass()`, etc. See `concepts/expressions.md` for the full set and validity
  in different contexts.
- **`offset` / `"state"`** — the target state. Either an integer offset (number of states forward from
  the current state) or a string state label. A numeric offset can be a literal or an expression.

## Engine-family divergence: no client/server authority split

UZDoom's `A_JumpIf` (`wadsrc/static/zscript/actors/checks.zs:29-32`) has no client-mode gate at all: the
entire ZScript function body is `return expression? ResolveState(label) : null;` — a pure, unconditional
evaluate-then-jump with no `NETWORK_InClientMode()`/`CLIENTUPDATE_FRAME`/`SERVERCOMMANDS_*`-style
construct anywhere in the UZDoom source tree (confirmed by a tree-wide search: zero occurrences). There is
no `NETFL_CLIENTSIDEONLY`-style split between "network-authoritative" and "client-side-only" actors for
this action, and consequently none of the two "Critical synchronization caveat" consequences described
above apply on UZDoom: the expression's RNG calls (if any) are consumed exactly once, identically on
every machine, and there is no result-slot early-return path to leave stale. `A_JumpIf` is also
implemented directly in ZScript rather than as a native (C++) action function, unlike Zandronum's
`DEFINE_ACTION_FUNCTION_PARAMS` implementation, and its signature is correspondingly different: it
*returns* the target state (`action state A_JumpIf(bool expression, statelabel label)`) rather than
performing the jump as a side effect of a `void`-returning call with an `int`-or-`"state"` union
parameter. That return-based signature is what drives the anonymous-function behavior described below.

## Zandronum network behavior: expression evaluation precedes network check

**Critical synchronization caveat.** Unlike some jump-family actions, `A_JumpIf` evaluates its
expression parameter **before** checking whether the actor is clientsideonly. This has two observable
consequences:

1. **RNG consumption on non-clientside actors in client mode.** If the expression uses `random()`,
   `frandom()`, or `random2()`, those calls consume entries from the expression evaluator's RNG
   (`pr_exrandom`) on both server and client, even though the jump itself is suppressed on the client.
   This causes the RNG state to diverge between server and client, potentially affecting subsequent
   expression evaluations in the same state or nearby actions.

2. **Result slot left untouched on non-clientside actors in client mode.** After the network check,
   `ACTION_SET_RESULT(false)` is not executed for non-clientside actors in client mode (the function
   returns early). Any prior result slot value persists, which can affect branching in subsequent
   `if` statements in DECORATE that key off the action's return value.

Here is the full implementation from the Zandronum source:

```c
DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_JumpIf)
{
	ACTION_PARAM_START(2);
	ACTION_PARAM_BOOL(expression, 0);
	ACTION_PARAM_STATE(jump, 1);

	// [BC] Don't jump here in client mode.
	if ( NETWORK_InClientMode() )
	{
		if (( self->NetworkFlags & NETFL_CLIENTSIDEONLY ) == false )
			return;
	}

	ACTION_SET_RESULT(false);	// Jumps should never set the result for inventory state chains!
	if (expression) ACTION_JUMP(jump, CLIENTUPDATE_FRAME);	// [BC] It's probably not good to do this client-side.
}
```

On the server (or in single-player), if the expression evaluates true, the jump is executed and all
clients are notified of the state change via `SERVERCOMMANDS_SetThingFrame`. On a client for a
non-`NETFL_CLIENTSIDEONLY` actor, the expression is still evaluated (including any side effects), but
the jump is suppressed locally; the server's state-change notification will be received separately. For
a `NETFL_CLIENTSIDEONLY` actor, both the expression and jump happen entirely on the client.

## Comparison with A_Jump

The related `A_Jump` action function checks the network mode **before** consuming RNG, not after. This
means `A_Jump` does not suffer RNG desynchronization on non-clientside actors in client mode, because
the `pr_cajump()` calls are skipped entirely in client mode for non-clientside actors.

## Wiki/engine divergence: anonymous functions not applicable (Zandronum)

The wiki page notes that "Jump functions perform differently inside of anonymous functions." Anonymous
action blocks are a ZScript feature and do not exist in Zandronum's DECORATE implementation; this note
is not applicable. See `concepts/state-machine.md` for Zandronum's limitations relative to ZScript.

## Engine-family divergence: anonymous state-action blocks

Unlike Zandronum, UZDoom does have anonymous state action blocks (ZScript inline `{ }` action blocks
attached directly to a state), and the wiki's caveat about jump functions behaving differently inside
them is real there, via two distinct, independently-verified mechanisms:

1. **A bare call auto-returns; a call inside a `{ }` block does not, unless written explicitly.** When
   a state's action is a single bare call with no braces (e.g. `POSS A 0 A_JumpIf(expression, "Label")`
   — the form used throughout this doc's own examples), the compiler wraps it in an implicit
   `return` (`ZCCCompiler::ConvertAST`, `src/common/scripting/frontend/zcc_compile.cpp:3044-3066`: the
   `AST_ExprFuncCall` branch always adds an `FxReturnStatement`). Inside an explicit multi-statement
   `{ }` action block, no such implicit return is added (the compound-statement branch of the same
   function has that auto-return step commented out) — a bare `A_JumpIf(expression, "Label");`
   statement written as one of several statements in a `{ }` block has its returned state silently
   discarded, and the actor does not jump; the call must be written as `return A_JumpIf(expression,
   "Label");` to take effect. This is the practical form of the wiki's caveat.
2. **A numeric jump-offset argument only compiles inside a state's own action function.** Separately,
   `A_JumpIf(expression, 2)` (a numeric offset rather than a string state label) is only accepted when
   the call is being compiled as part of a state's own action function — bare or inside `{ }`, both
   count — tracked via a per-context state index (`ctx.StateIndex`) that is only valid in that context.
   Calling `A_JumpIf` with a numeric offset from a separately-declared named function is a compile error
   ("State jumps with index can only be used in anonymous state functions.",
   `src/scripting/backend/codegen_doom.cpp:190-195`). String state-label arguments are unaffected by
   this restriction.

## See also

- [DECORATE expressions](../concepts/expressions.md) — the full set of expression operators, built-in
  functions, and actor variables available in state-action parameters.
- `A_Jump` — the probability-based jump function; evaluates its RNG differently (network check first).
- [Creating monsters](../concepts/creating-monsters.md) — actors requiring `See` state with conditional
  branching often use `A_JumpIf` to decide between attack types.
