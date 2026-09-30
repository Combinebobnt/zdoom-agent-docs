# ACC, its include files, and declaring engine functions it doesn't know yet

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Compiler:** ACC 1.60 built from the ACC checkout at `bdb9bc4`; zt-bcc 0.10.0-alpha-8, library
files identical to the zt-bcc checkout at `d2d7da3`.
**Provenance:** written from the ACC source (`parse.c` `OuterSpecialDef` at 1171,
`LeadingLineSpecial` at 1602, `LeadingFunction` at 1762, `ExprLineSpecial` at 3741; `symbol.c`
`SY_InsertGlobalUnique` at 394; `token.c` `CheckForLineSpecial`; the four shipped `.acs` headers),
read only and never quoted. zt-bcc: `src/parse/dec.c` (`p_read_special_list` at 2437,
`read_special` at 2453 and its helpers), `src/semantic/dec.c:2044`, `src/codegen/expr.c`
(`visit_aspec_call` at 1596, `visit_ext_call` at 1658), `lib/zcommon.bcs`, `lib/zcommon.acs`.
UZDoom: `src/playsim/p_acs.cpp` (`MIN_ARG_COUNT` at 5368, `CallFunction`'s `default` at 6874,
`PCD_LSPEC*` from 7141, `PCD_CALLFUNC` at 7289), `src/playsim/p_lnspec.cpp` (`LineSpecials[]` at
3545, `P_ExecuteSpecial` bounds check at 3955). Zandronum: `src/p_acs.cpp` (`CallFunction` at
5899, its `default` at 9059, `PCD_CALLFUNC` at 9461, `ACSF_AddBot`/`ACSF_RemoveBot` at
8540/8583), `src/p_lnspec.cpp` (`LineSpecials[256]` at 3598, `P_ExecuteSpecial` at 3923).
Every compiler-behavior claim below was also confirmed by test compiles with both compilers
(2026-09-28).

ACC is the original ACS compiler: written by Raven Software in 1995 for Hexen, then extended and
maintained by the ZDoom project (the current upstream is ZDoom's `acc` repository, version 1.60).
Both UZDoom and Zandronum load its output. This tree's own compiler target is zt-bcc (`bcc`), a
separate ACS-superset compiler; ACC matters when a project still builds with it, when reading
old sources, and when a function exists in the engine but not in ACC's shipped headers. ACC's
source is **not open source** (1999 Raven EULA, never relicensed), so everything below describes
its behavior in prose; the examples use made-up names. See `../../shared/AUTHORING.md`'s
"Never quote `acc` source verbatim".

## The four include files

A normal ACC script starts with `#include "zcommon.acs"`. That file is only an umbrella: it
includes the other three, and holds nothing else except a commented-out `#nowadauthor` toggle.

| File | Holds |
|---|---|
| `zcommon.acs` | Umbrella include for the three below. |
| `zspecial.acs` | One big `special` declaration: every action special and extension function ACC knows, with its number and argument count. This is the file the rest of this page is about. |
| `zdefs.acs` | `#define` constants (`TRUE`/`FALSE`, `LINE_FRONT`, `SKILL_*`, `APROP_*`, and so on). |
| `zwvars.acs` | An empty placeholder, meant for a project's own `world` variable declarations. |

Nothing about these names is known to the compiler itself: a function is callable in ACC only
because `zspecial.acs` declared it. The compiler's own built-in functions (`Delay`, `Random`,
`ThingCount` and friends) are separate and need no header.

## How ACC relates to zt-bcc

- zt-bcc's `lib/zcommon.bcs` says in its own header comment that its declarations are based on
  ACC's `zdefs.acs` and `zspecial.acs`. It is one `#library` file holding both roles: constants
  as `enum`s and the function table as a typed `special` list.
- zt-bcc ships **no** `zspecial.acs`, `zdefs.acs` or `zwvars.acs`. Its `lib/zcommon.acs` is a
  short shim that `#import`s `zcommon.bcs`. So `#include "zcommon.acs"` compiles under both
  compilers, but resolves to different headers with different contents.
- zt-bcc's table is the more current one. For example, Zandronum's `AddBot` (-168) and
  `RemoveBot` (-169) are declared there, but ACC's `zspecial.acs` at `bdb9bc4` stops at -167 in
  Zandronum's reserved range. Both functions predate Zandronum 3.2.1 (the introducing commit is an
  ancestor of the 3.2.1 version bump), so a 3.2.1 project on ACC has to declare them itself. See
  [AddBot](../functions/addbot.md) and [RemoveBot](../functions/removebot.md) for their
  semantics.
- ACC's `zspecial.acs` also carries entries added for other ports (Eternity, ZDaemon, GZDoom-only
  specials), and support for those varies per engine. Being declared there proves nothing about
  whether a given engine runs it; check the engine source.

## Declaring a function ACC doesn't know yet

This is the topic of the Zandronum wiki page "Adding New ACS Functions to ACC". The mechanism is
the same `special` statement `zspecial.acs` itself uses, and it can appear in any source file at
top level:

```acs
#include "zcommon.acs"

// Made-up names and numbers, for syntax only.
special
    -9001:MyEngineQuery(1, 3),
     300:MyNewLineAction(2),
    -9002:MyNoArgFunc(0);
```

- **Shape.** The keyword `special`, then a comma-separated list of `number:Name(args)` entries,
  ended by one semicolon.
- **The sign of the number picks the bucket** (the same split as `acs/AGENTS.md`'s bucket table).
  A positive number is an **action special** (a line special index, compiled to the `LSPEC*`
  pcodes). A negative number is an **extension function** (compiled to `PCD_CALLFUNC` with the
  magnitude as the function index). A leading minus sign is the only difference.
- **Argument count.** One number means exactly that many arguments. Two numbers, `(min, max)`,
  allow any count in that range, for functions with optional trailing arguments. ACC has no types
  in this form: every argument and return value is a plain int.
- **Names are case-insensitive.** ACC lowercases identifiers.
- **Where to get the real number and count.** Never guess either. The quickest reliable source is
  zt-bcc's `lib/zcommon.bcs`, which already tracks the newer engine additions. Take the number from
  the mainline entry, never from the table's `// Q-Zandronum` section: some negative numbers are
  declared twice there under different names (`-168` is both `AddBot` and a Q-Zandronum-only
  function), as `acs/AGENTS.md` explains. Then confirm the name against the engine's `case` using
  that file's bucket table. The minimum count is whatever the
  engine's `case` body reads unconditionally, not what the wiki example happens to pass.

Two ways to apply it:

1. **Your own `special` block after the include** (recommended). The declaration stays in your
   project and survives an ACC update.
2. **Edit `zspecial.acs`.** Works, but the edit is lost when ACC's headers are replaced, and it
   silently changes every project sharing that include directory.

### ACC traps, all confirmed by test compile

- **You cannot redeclare a name `zspecial.acs` already declares.** Once a name is declared, ACC's
  tokenizer treats it as a special, so a second declaration fails with the misleading "Invalid
  identifier." error rather than a redefinition error. To fix a wrong shipped declaration you must
  edit `zspecial.acs` itself, or declare the function under a different name.
- **Declarations do not travel through `#import`.** ACC skips every `special` statement while
  reading an imported library. A library that declares a function can call it, but a script that
  `#import`s the library cannot, and fails with "used but not defined". Put the declaration in a
  small include file of its own and `#include` it from every module that calls the function.
- **An optional-argument function cannot be called with empty parentheses as a statement.** With
  a `(0, N)` declaration, a bare `MyFunc();` statement is a "Syntax error in expression." The
  same call in expression position (say, assigned to a variable) compiles fine. This is why
  Zandronum's `RemoveBot` treats an empty string as "no argument": ACC users pass `""` instead.
- **The bare name, without parentheses, is an expression yielding the declared signed number**
  (`-9001` for `MyEngineQuery` above), not a call.
- **ACC does not reject an action special declared with more than five arguments.** The engine's
  line specials take at most five. A call passing six non-constant arguments compiles silently
  into the wrong pcode (the `LSPEC` opcode family has no six-argument slot), producing corrupt
  bytecode. zt-bcc rejects the same declaration outright.
- A zero-argument action special `(0)` numbered up to 255 compiles as a one-argument call passing
  `0`, since the base pcode set has no zero-argument form. Don't declare one above 255 in ACC: that
  path doesn't push a full five arguments.

## Getting the count or the index wrong

ACC checks every call only against **your** declaration. It has no idea what the engine really
expects, so a wrong declaration fails in one of these ways:

**Maximum too low.** A correct call with all its arguments is a compile error ("Incorrect number
of arguments." or "Incorrect number of special arguments."). Loud and easy to fix.

**Minimum too low, extension function.** A call that omits a required argument compiles, and the
engine receives a smaller argument count than the function needs:

- **UZDoom** guards most of its extension functions with a minimum-count check. The call returns `0`,
  and the console prints a line naming the function index, the count passed and the count
  needed. A map with `compat_noacsargcheck` set turns that guard off; see
  [PickActor](../functions/pickactor.md) for the flag.
- **Zandronum** has no general guard. Many `case` bodies read their arguments by position
  without checking the count, so a missing argument is read from whatever value was left in the interpreter
  stack buffer above the current top. The call runs with garbage for that argument, silently.

**Minimum too low or count short, action special.** Missing arguments arrive as `0`: both
compilers pad statement and expression calls, and the engine always passes five. Extra arguments
beyond what a special uses are ignored. So a count mistake on an action special usually means a
wrong-but-quiet `0`, not a crash.

**Wrong index.** Both engines dispatch purely by number, with no name check:

- A wrong negative number calls whichever extension function owns that index, with your
  arguments. If no function owns it, both engines' dispatchers fall through to a silent `return
  0`, with no log line.
- A wrong positive number runs a different line special. Unassigned slots in both engines' tables
  are a no-op, and a number past the table's end returns `0` silently.
- Any action special numbered above 255 compiles (in both ACC and zt-bcc) to `PCD_LSPEC5EX`,
  which Zandronum does not implement: opcode 381 is a different instruction there. See
  [Zandronum-vs-UZDoom ACS bytecode compatibility](zandronum-uzdoom-compat.md) for what that
  does to a script.
- An extension function number in UZDoom's skipped 100-199 range (Zandronum's reserved range)
  returns `0` silently on UZDoom. The same page covers that.

In every silent case the script keeps running with a `0` result, which often looks plausible.
When a newly declared function "does nothing", check the number and count against the engine
before debugging anything else.

## The zt-bcc equivalent

zt-bcc reads the same `special` statement, anywhere a declaration is allowed, with a richer
parameter list:

```bcs
// Made-up names and numbers, for syntax only.
special
    -9001:MyEngineQuery(int; int, str):int,
     300:MyNewLineAction(int, int),
    -9002:MyCountedQuery(1, 3);
```

- **Typed parameters.** Each parameter is a type (`int`, `fixed`, `bool`, `str`, `raw`). A
  semicolon splits required parameters (before it) from optional ones (after it), replacing
  ACC's `(min, max)` pair.
- **Return type** follows a colon after the closing parenthesis. Leaving it out gives `raw`, not
  `void`.
- **ACC's numeric form still works.** `(N)` or `(min, max)` is accepted, with every parameter
  treated as `raw`.
- A positive-number entry may carry a trailing `:0`, meaning linedef-only and not callable from a
  script. `acs/AGENTS.md` covers this and the other table-parsing quirks.

Behavior differences from ACC, confirmed by test compile:

- **An `int`-for-`str` mismatch is only caught inside a `strict namespace`.** There it is a
  compile error; in a plain ACS-style file the same call compiles.
- **Redeclaring an existing name is a clear error** ("duplicate object name"), naming where the
  original is.
- **An action special with more than five parameters is a hard error** at declaration.
- **Declarations do travel through `#import`.** That is how `zcommon.bcs` itself works, since it
  is imported rather than included.
- Codegen matches ACC where it matters: an extension function call passes the actual argument
  count, so omitted optional arguments reach the engine as a smaller count. Trailing constant-zero
  arguments to an action special may be dropped from the call, since the engine fills them with
  `0` anyway.

The wrong-count and wrong-index consequences above are engine-side, so they are identical
whichever compiler produced the call.
