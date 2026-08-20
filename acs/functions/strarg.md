# `int StrArg(str string)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** wiki page `StrArg - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`https://zdoom.org/w/index.php?title=StrArg&oldid=46387` — the page itself is minimal, just signature + one-line usage/return, no
parameter/failure detail beyond what's here) + source-verified against
the Zandronum source's `src/p_acs.cpp:5360-5559` (`EACSFunctions` enum) and `:5899-9064`
(`CallFunction` switch and its `default` at `:9059`) + the zt-bcc source's `lib/zcommon.bcs:1837` +
the zt-bcc wiki's `Types.md` for the `int(str)` cast workaround.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function — but see below, it doesn't actually reach engine code.

Extension function (**negative** index -206 in the zt-bcc source's `lib/zcommon.bcs:1837`:
`-206:StrArg(str):int,`). Per the wiki, it converts a string handle into a plain int suitable for
passing as an argument to an action special (e.g. `ACS_NamedExecute`, which takes raw ints, not
`str`).

**Implemented on UZDoom, but via a different encoding than the wiki's description implies.**
`case ACSF_StrArg:` (`src/playsim/p_acs.cpp`) is `return -FName(Level->Behaviors.LookupString(args[0])).GetIndex();`
— it resolves the incoming ACS string constant to its text (`LookupString`), wraps that text in a
**ZDoom-family `FName`** (the engine's global interned-name table, unrelated to ACS's own string
constant table), and returns the negated `FName` index. **Not independently re-verified for this
pass:** whether that negated-`FName`-index encoding is what the specific action specials the wiki
mentions (`ACS_NamedExecute` and similar) actually expect as their raw int argument, or whether
those specials separately re-resolve through the same `FName` machinery — if they instead expect
the same raw ACS string-table index the `int(str)` cast below produces, `StrArg(x)` and `int(x)`
would **not** be interchangeable on UZDoom despite this doc's Zandronum-focused advice below
treating them as equivalent. Flagged as an open question rather than assumed either way.

## Zandronum-specific: unimplemented function (absent from the enum, not just uncased)

the Zandronum source's `src/p_acs.cpp`'s `EACSFunctions` enum (line 5360) is the authoritative list of
extension-function numbers this engine build recognizes. It runs `ACSF_ResetMap = 100` through
`ACSF_CheckAutomap = 189`, then jumps to the out-of-order backport `ACSF_GetActorFloorTexture = 204`
(line 5462), then straight to the ZDaemon-only `ACSF_GetTeamScore = 19620` (line 5557). **There is
no enum member at all for value 205 or 206** — unlike the `SpawnParticle`/`GetMaxInventory` cases
already documented in [families/spawning.md](../families/spawning.md) and
[families/inventory.md](../families/inventory.md) (which *are* named in the enum but have no
`case` in the switch), `ACSF_StrArg` isn't even a symbol here. Calling it at runtime dispatches
through `DLevelScript::CallFunction`'s single big `switch(funcIndex)` (`p_acs.cpp:5902`-`9064`),
which has no `case` matching `206` and falls to the trailing `default: break;` (`p_acs.cpp:9059`),
so the call **silently returns `0`** every time — same failure shape as the other never-backported
ZDoom extension functions in this tree, just with the enum gap making it even more clearly a
"ZDoom is feature-ahead" case than a fork bug.

the zt-bcc source's own toolchain has no compile-time special-casing for `StrArg` either
(`grep -rn StrArg src/` in `zt-bcc` turns up nothing beyond the `zcommon.bcs` declaration) — it's
called through the ordinary `PCD_CALLFUNC` extension-function convention, with no fallback path.

## Why this rarely matters on Zandronum: `int(str)` is a real BCS-level cast, unrelated to this ACSF

BCS already provides a genuine compile-time conversion, `int(str value)`
(the zt-bcc wiki's `Types.md`, "Conversion to `str` type" / cast table), that turns a `str`
value into its underlying int (the string-table index) at zero runtime cost — this is a language
cast handled entirely by `bcc`, not a call into engine code, so it works regardless of whether
`ACSF_StrArg` exists. On Zandronum, anywhere the wiki's `StrArg(x)` idiom would be used to pass a
string as a raw action-special argument, `int(x)` accomplishes the same thing in this toolchain and
does not silently return `0`. **On Zandronum, do not call `StrArg()` expecting it to work — use
`int(str)` cast instead. On UZDoom, `StrArg()` itself works, but see the FName-encoding caveat
above before assuming it's interchangeable with `int(str)` there.**
