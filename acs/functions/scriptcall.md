# `ScriptCall`

**Tier:** B — verified directly against UZDoom source (`src/playsim/p_acs.cpp:5243-5365`, the `DLevelScript::ScriptCall` implementation `case ACSF_ScriptCall` at `:6785` dispatches to), not wiki-derived (the wiki's own extension-function pages don't cover this one at the level of detail below).
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15) — re-confirmed against current source for Phase 5; original read was 2026-08-06, see Provenance
**Provenance:** direct UZDoom source read, 2026-08-06, no wiki page consulted (not present on the pages this tree has ingested).
**Bucket:** extension function, index `-210` (`zcommon.bcs:1842`, `str,str; raw...`,120 total raw slots):int`). Declared in the shared `zcommon.bcs` header both Zandronum's and UZDoom's `zt-bcc` forks compile against, but only **implemented on the UZDoom/GZDoom-family side** — grepped `ACSF_ScriptCall` across the Zandronum source's `p_acs.cpp` and found no match at all. Calling it from a Zandronum build is therefore not a documented no-op here (not independently re-traced this session which `default:` case in Zandronum's own `CallFunc` switch it falls through to) - treat as unverified-but-likely-inert on Zandronum, not as "known safe."

## Syntax

```text
int ScriptCall(str className, str functionName, ... up to ~120 additional args);
```

Calls a **static** ZScript function `functionName` declared on class `className`, marshaling
arguments and the return value between ACS and ZScript types. Despite the declared `:int` return
type, the actual return value's meaning depends on the target function's own return type (see
below) - BCS callers that need a `str`/`bool`/`double` return must declare their own typed alias at
the same `-210` index rather than trust the raw `:int` signature (confirmed real and compiles
clean: a second `special` entry at `-210` with a different name and a different return type
coexists with the stock declaration with no conflict, since these are compile-time-only type
annotations over the same numeric special).

## Target function requirements

**Source:** `p_acs.cpp:5251-5265`

- **Must be `static`.** The implementation checks `func->ImplicitArgs > 0` and aborts (see Failure
  modes below) if the resolved function isn't static - `ImplicitArgs` is nonzero for instance
  methods (implicit `self`) and action functions, zero only for `static`.
- **No visibility/scope keyword requirement.** Resolution is `cls->FindSymbol(funcname, true)` with
  no additional check - ordinary `public`-by-default visibility is sufficient. No `[ClearScope]` or
  similar attribute is required or checked.
- **The class can be any class**, with no inheritance requirement - `PClass::FindClass(clsname)`
  just looks the name up. It does not need to be a `StaticEventHandler`, an `Object` subclass with
  any particular ancestor, etc. (A common pattern is to still make it a `StaticEventHandler` if the
  static functions need to reach persistent instance state - see the next section - but that's a
  design choice, not a `ScriptCall` requirement.)

## Argument and return type marshaling

**Source:** `p_acs.cpp:5268-5361`

Only seven ZScript parameter/return types are supported; every declared parameter (beyond the
first two `str` control arguments) must be one of:

| ZScript type | ACS-side conversion |
|---|---|
| `int` | passed as-is |
| `Color` | passed as-is |
| `bool` | `!!value` |
| `double` | `ACSToDouble(value)` (fixed-point → float) |
| `Name` | ACS string-table lookup, then `FName(...).GetIndex()` |
| `Sound` | ACS string-table lookup, then `S_FindSound(...).index()` |
| `String` | ACS string-table lookup, pointer passed to the VM |

Any other declared parameter type aborts the call (see Failure modes). **Argument count must match
exactly** (with ZScript-side `= default` optional trailing params allowed via `VARF_Optional`) -
there is no varargs bridging; a `ScriptCall` site with too many or too few arguments for the
resolved function's signature aborts rather than silently truncating/padding.

**Special first-parameter case:** if the target function's *first* declared parameter type is
`Actor`, it is NOT filled from the ACS-side argument list at all - it automatically receives the
calling script's activator. The ACS-side argument list then starts filling from the function's
*second* parameter onward.

Return value marshaling (only relevant if the target function has a non-`void` return):

| ZScript return type | Marshaled back as |
|---|---|
| `int` / `bool` / `Color` | raw int |
| `Name` | ACS string-table index via `GlobalACSStrings.AddString(FName(...).GetChars())` |
| `Sound` | ACS string-table index via `GlobalACSStrings.AddString(S_GetSoundName(...))` |
| `double` | `DoubleToACS(d)` |
| `String` | ACS string-table index via `GlobalACSStrings.AddString(d)` - confirmed real, not just declared |
| anything else | silently ignored; call executes as if `void` |

## Failure modes - not graceful

**Source:** `p_acs.cpp:5251-5320`

Every one of these is an `I_Error` - **uncatchable, aborts the whole process**, not a script-level
exception and not a silent no-op:

- Named class doesn't exist: `"ACS call to unknown class in script function %s.%s."`
- Named function doesn't exist on that class: `"ACS call to unknown script function %s.%s."`
- Resolved function isn't `static`: `"ACS call to non-static script function %s.%s."`
- Too many ACS-side arguments for the function's declared parameter list: `"Too many parameters in
  call to %s.%s."`
- Too few (and the missing ones aren't `VARF_Optional`): `"Insufficient parameters in call to
  %s.%s."`
- A declared parameter type outside the seven-type table above: `"Invalid type %s in call to
  %s.%s."`

**Practical consequence for any ACS code that already calls `ScriptCall` against a not-yet-written
ZScript target** (e.g. mid-build during a porting/bridging project): the moment that ACS code
actually *executes* in a running UZDoom instance, the game hard-aborts. An unrecompiled Zandronum
`BEHAVIOR` hitting an unallocated extension-function index elsewhere in this family degrades
gracefully (falls through to a `default: break; return 0;`, `p_acs.cpp:6874-6877`) - `ScriptCall`
itself does not offer that same safety net once the *class* and *function name* strings resolve to
nothing on the ZScript side. A build/install process wiring up a `ScriptCall`-based bridge should
treat the ACS header and the ZScript implementation as one atomic unit, not something that can be
shipped/tested independently.

## Verification note on `-norun`

`uzdoom -norun` ("quits the game early to check for script errors" per `-h`) reliably surfaces
ZScript *compile* errors (exit code `1337`, i.e. `57` mod 256, with `"Script error, ..."` printed
if broken; the same exit code with no such line and a `"script parsing took ... ms"` line if clean)
without needing a real display - confirmed working under `SDL_VIDEODRIVER=dummy`/no GPU. It exits
*before* `OnEngineInitialize`/gameplay code ever runs (`d_main.cpp:3801-3822`, the `norun` early
`return 1337` happens before `C_RunDelayedCommands()` and all later engine bring-up), so it cannot
be used to test `ScriptCall`'s *runtime* behavior (whether a given call actually resolves/executes
correctly) - only whether the ZScript source compiles. A full runtime launch was attempted in the
same sandboxed environment this was verified in and did not reach that point either (hung in a
repeating "Creating window" loop under the SDL dummy driver, regardless of `-host`/`+vid_rendermode
0`/etc.) - runtime `ScriptCall` behavior in this doc is sourced from reading `p_acs.cpp` directly,
not from an observed live call.

## See also

- [Zandronum/UZDoom compatibility](../concepts/zandronum-uzdoom-compat.md)
- [ACS libraries](../concepts/libraries.md) - the `#import`/`#include` mechanics for getting a
  `special` declaration like this one (or a typed alias at the same index) into a BCS translation
  unit in the first place.
