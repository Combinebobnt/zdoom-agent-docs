# ZDoom math-function stubs (`Floor`/`Round`/`Ceil`) — dead in this fork

**Tier:** A (for the negative finding — confirmed dead, not a signature-only stub).
**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`; the gap is an absent enum member, not a version-gated `#ifdef`, so it predates any specific backport and isn't a 3.2.1-vs-3.3-alpha version question).
**Provenance:** wiki pages `Floor (ACS function) - ZDoom Wiki.html` (`oldid=54852`), `Round - ZDoom Wiki.html` (`oldid=48046`), `Ceil - ZDoom Wiki.html` (`oldid=48045`) (all retrieved 2026-07-29, `_intake/processed/`) + source-verified against the Zandronum source's `src/p_acs.cpp:5360-5459` (`EACSFunctions` enum gap), `:9058-9064` (`default: break;` / `return 0;`), `:9459-9469` (`PCD_CALLFUNC` dispatch), and the zt-bcc source's `lib/zcommon.bcs:1838-1840` (`ZDoom_Floor`/`ZDoom_Round`/`ZDoom_Ceil` declarations). Wiki/fork divergence (functions declared, never implemented) recorded above rather than silently trusted.
**Bucket:** extension function (negative index in `zcommon.bcs`'s `special` table), dispatched through `DLevelScript::CallFunction`'s `switch(funcIndex)` (the Zandronum source's `src/p_acs.cpp:5899`).

`ZDoom_Floor(fixed):fixed` (-207), `ZDoom_Round(fixed):fixed` (-208), and
`ZDoom_Ceil(fixed):fixed` (-209) — declared consecutively in `zt-bcc/lib/zcommon.bcs:1838-1840`
as extension functions, but **none of them do anything in this engine build**. One family file
instead of three per-function files because all three share one root cause discovered by reading
them together (the same missing enum range), not three independent findings.

## The gap

The engine's own `EACSFunctions` enum (`p_acs.cpp:5360-5459`) is what gives ACSF numbers their
names and, in turn, their `case` labels in the switch below it. That enum jumps straight from
`ACSF_GetActorFloorTexture = 204` to a comment block and then `ACSF_ResetMap = 100` (Zandronum's
own numbering resuming after a Skulltag reset) — **numbers 205-209 are never named at all.**
Since the switch matches on enum names, there is no `case` for 205 (`GetActorFloorTerrain`), 206
(`StrArg`), 207 (`ZDoom_Floor`), 208 (`ZDoom_Round`), or 209 (`ZDoom_Ceil`) anywhere in
`p_acs.cpp` (confirmed by grep — zero matches for any of those names). Every one of the three
falls through to the switch's `default: break;`, and the function ends with a bare `return 0;`
(`p_acs.cpp:9058-9064`).

**Practical effect: calling any of `ZDoom_Floor(x)` / `ZDoom_Round(x)` / `ZDoom_Ceil(x)`
compiles cleanly and always returns `0`, regardless of `x` — silently, with no compiler warning
and no runtime error.** 205 (`GetActorFloorTerrain`) and 206 (`StrArg`) sit in the same dead
range but weren't part of this wiki-intake batch and aren't otherwise verified here — flagging
their presence in the gap without claiming full documentation of them.

**`Sin`/`Cos`/`Sqrt` are NOT in this bucket and are unaffected** — those are real compiler
builtins (`PCD_SIN`/`PCD_COS`/`PCD_SQRT`, `zt-bcc/src/builtin.c`), a completely different
dispatch path from the ACSF extension-function switch. Don't generalize this finding to them.

## Wiki/fork divergence

Each wiki page (`Floor (ACS function)`, `Round`, `Ceil` — all "ZDoom Wiki") describes real
upstream ZDoom/GZDoom behavior: `Floor` rounds to the lowest whole number, `Round` to the
nearest, `Ceil` to the highest, all returned as `fixed`. `Ceil`'s wiki page additionally notes it
became a *native* (engine-side) function in GZDoom 2.4.0+ — **that native backport never landed
in Zandronum.** This is a genuine ZDoom-ahead-of-Zandronum feature gap, not a wiki error.

The wiki's bare name `Floor`/`Round`/`Ceil` also doesn't compile as-is with `zt-bcc`:
`zt-bcc/lib/zcommon.bcs` only declares the `ZDoom_`-prefixed names (grepped the whole `zt-bcc`
tree for a bare `\bFloor\b` in any `.bcs` file — zero hits outside the unrelated `Floor_*`
sector-mover action-special family). The callable name in `zt-bcc` is `ZDoom_Floor`, not
`Floor` (and likewise for the other two).

## What to use instead

None of these have a working native replacement in this fork; use the wiki's own bit-trick
fallbacks, which are plain bitwise expressions with no engine call and so aren't subject to this
gap:

```
function fixed FloorFixed (fixed value)
{
    return value & 0xFFFF0000; // round fixed value down to next whole number
}

function fixed RoundFixed (fixed value)
{
    return (value + 32768) & 0xFFFF0000; // round fixed value to nearest whole number
}

function fixed CeilFixed (fixed value)
{
    return (value + 65535) & 0xFFFF0000; // round fixed value up to next whole number
}
```

For flooring toward zero specifically (not true mathematical floor), casting/assigning a `fixed`
to an `int` also works: BCS integer conversion truncates via a raw `>> 16`, which is equivalent
to `floor()` for non-negative values only — it diverges from true floor by one for negative
non-integers (truncation rounds toward zero, floor rounds toward negative infinity).
