# ZDoom math functions (`Floor`/`Round`/`Ceil`) — dead on Zandronum, real on UZDoom

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-17)
**Provenance:** wiki pages `Floor (ACS function) - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=Floor_%28ACS_function%29&oldid=54852`), `Round - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=Round&oldid=48046`), `Ceil - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=Ceil&oldid=48045`) (all retrieved 2026-07-29, `_intake/processed/`) + source-verified against the Zandronum source's `src/p_acs.cpp:5360-5459` (`EACSFunctions` enum gap), `:9058-9064` (`default: break;` / `return 0;`), `:9459-9469` (`PCD_CALLFUNC` dispatch); the UZDoom source's `src/playsim/p_acs.cpp` (`EACSFunctions` enum entries `ACSF_Floor`/`ACSF_Round`/`ACSF_Ceil` at 207/208/209, real `case` bodies implementing each); and the zt-bcc source's `lib/zcommon.bcs:1838-1840` (`ZDoom_Floor`/`ZDoom_Round`/`ZDoom_Ceil` declarations, same three indices on both engines). Engine-family divergence (functions declared by the compiler, implemented on one engine but not the other) recorded below rather than silently trusted.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (negative index in `zcommon.bcs`'s `special` table), dispatched through `DLevelScript::CallFunction`'s `switch(funcIndex)` (the Zandronum source's `src/p_acs.cpp:5899`; the UZDoom source's equivalent switch in `src/playsim/p_acs.cpp`).

`ZDoom_Floor(fixed):fixed` (-207), `ZDoom_Round(fixed):fixed` (-208), and
`ZDoom_Ceil(fixed):fixed` (-209) — declared consecutively in `zt-bcc/lib/zcommon.bcs:1838-1840`
as extension functions, at the same three indices in both engines' own `EACSFunctions` enums.
**Zandronum never implements any of the three; UZDoom implements all three with working `case`
bodies.** One family file instead of three per-function files because all three share one root
cause on each engine (the same missing/present enum range), not independent findings.

**Correcting an earlier version of this file, found during the 2026-08-17 UZDoom-retarget audit:**
it previously claimed all three were dead on *both* engines, citing `tools/engine_matrix.py`'s
`compiler-only` classification for UZDoom as independent confirmation. That classification was
itself a bug (see "Tooling note" below) — a case-insensitive name match between `ZDoom_Floor` and
UZDoom's own `Floor` was never attempted, so the tool reported "neither engine implements it" when
UZDoom in fact does, under the un-prefixed name. Reading UZDoom's `p_acs.cpp` directly confirms
real `case ACSF_Floor:`/`ACSF_Ceil:`/`ACSF_Round:` bodies, not stubs. The Zandronum half of the
original finding was correct and is unchanged below.

## The gap, on Zandronum

The engine's own `EACSFunctions` enum (`p_acs.cpp:5360-5459`) is what gives ACSF numbers their
names and, in turn, their `case` labels in the switch below it. That enum jumps straight from
`ACSF_GetActorFloorTexture = 204` to a comment block and then `ACSF_ResetMap = 100` (Zandronum's
own numbering resuming after a Skulltag reset) — **numbers 205-209 are never named at all.**
Since the switch matches on enum names, there is no `case` for 205 (`GetActorFloorTerrain`), 206
(`StrArg`), 207 (`ZDoom_Floor`), 208 (`ZDoom_Round`), or 209 (`ZDoom_Ceil`) anywhere in
`p_acs.cpp` (confirmed by grep — zero matches for any of those names). Every one of the three
falls through to the switch's `default: break;`, and the function ends with a bare `return 0;`
(`p_acs.cpp:9058-9064`).

**Practical effect on Zandronum: calling any of `ZDoom_Floor(x)` / `ZDoom_Round(x)` /
`ZDoom_Ceil(x)` compiles cleanly and always returns `0`, regardless of `x` — silently, with no
compiler warning and no runtime error.** 205 (`GetActorFloorTerrain`) and 206 (`StrArg`) sit in
the same dead range but weren't part of this wiki-intake batch and aren't otherwise verified here
— flagging their presence in the gap without claiming full documentation of them.

**`Sin`/`Cos`/`Sqrt` are NOT in this bucket and are unaffected on either engine** — those are real
compiler builtins (`PCD_SIN`/`PCD_COS`/`PCD_SQRT`, `zt-bcc/src/builtin.c`), a completely different
dispatch path from the ACSF extension-function switch. Don't generalize this finding to them.

## Real and working on UZDoom

UZDoom's `EACSFunctions` enum includes `ACSF_Floor`, `ACSF_Round`, and `ACSF_Ceil` consecutively
at 207/208/209 (anchored from `ACSF_CheckClass = 200`, the same canonical GZDoom-family numbering
zt-bcc's `zcommon.bcs` declares) — no enum gap the way Zandronum has one. `DLevelScript::CallFunction`'s
switch has a real `case` for each: `Floor` rounds a fixed-point value down to the nearest whole
number, `Ceil` rounds up, `Round` rounds to nearest — the same bit-masking approach as the wiki's
own bit-trick fallbacks below, just done engine-side instead of in ACS. Calling any of
`ZDoom_Floor(x)`/`ZDoom_Round(x)`/`ZDoom_Ceil(x)` on UZDoom returns a real, computed result.

## Engine-family divergence

Each wiki page (`Floor (ACS function)`, `Round`, `Ceil` — all "ZDoom Wiki") describes real
upstream ZDoom/GZDoom behavior: `Floor` rounds to the lowest whole number, `Round` to the
nearest, `Ceil` to the highest, all returned as `fixed`. `Ceil`'s wiki page additionally notes it
became a *native* (engine-side) function in GZDoom 2.4.0+ — that native backport landed in UZDoom
(confirmed above) but **never landed in Zandronum.** This is a genuine ZDoom-ahead-of-Zandronum
feature gap, not a wiki error, and it now resolves cleanly under the UZDoom-primary framing: the
wiki's documented behavior is accurate for UZDoom, and Zandronum is the engine that diverges.

The wiki's bare name `Floor`/`Round`/`Ceil` also doesn't compile as-is with `zt-bcc` on either
engine: `zt-bcc/lib/zcommon.bcs` only declares the `ZDoom_`-prefixed names (grepped the whole
`zt-bcc` tree for a bare `\bFloor\b` in any `.bcs` file — zero hits outside the unrelated `Floor_*`
sector-mover action-special family). The callable name in `zt-bcc` is `ZDoom_Floor`, not
`Floor` (and likewise for the other two) — regardless of target engine.

## Tooling note

`tools/engine_matrix.py`'s `classify_all()` previously matched zt-bcc-declared names against each
engine's own ACSF table **by name only** (case-insensitive), with no fallback to check whether the
same numeric slot is implemented under a *different* name. `ZDoom_Floor`/`ZDoom_Round`/`ZDoom_Ceil`
never matched UZDoom's own `Floor`/`Round`/`Ceil` identifiers, so the tool reported `compiler-only`
("neither engine implements it") for all three even though UZDoom's slots 207-209 are real. Fixed
2026-08-17 by adding a numeric-index fallback, scoped to exclude ACSF slots 100-199 (Zandronum's
own private, densely-populated extension block, where a numeric match is coincidental slot reuse,
not a real correspondence — see the fix's own comment in `tools/engine_matrix.py` for the worked
example). Also corrected by the same fix: `Strcasecmp` (-64, genuinely implemented on both engines
as `stricmp`) and `Fs_Excute` (158, a zt-bcc-side typo for the real `FS_Execute`, present on both
engines under the correct spelling).

## What to use instead, on Zandronum

Zandronum has no working native replacement; use the wiki's own bit-trick fallbacks, which are
plain bitwise expressions with no engine call and so aren't subject to the Zandronum gap above.
On UZDoom these fallbacks aren't needed — the real functions work — but they remain correct and
portable if a script needs to run unmodified on both engines:

```text
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
to an `int` also works on both engines: BCS integer conversion truncates via a raw `>> 16`, which
is equivalent to `floor()` for non-negative values only — it diverges from true floor by one for
negative non-integers (truncation rounds toward zero, floor rounds toward negative infinity).
