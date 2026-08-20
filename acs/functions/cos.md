# `fixed Cos(fixed angle)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `Cos - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`https://zdoom.org/w/index.php?title=Cos&oldid=35793`) + source-verified against the Zandronum source (`p_acs.cpp:12241-12243`,
`tables.h:48-70`) and the zt-bcc source's `src/builtin.c:103`. The wiki's core "cosine of a
fixed-point turn-fraction angle" description holds; the wiki's own `int`-typed signature is
wrong per the compiler's builtin table (see "Wiki divergence" above); the wraparound behavior and
the shared-table/`Sin` relationship are this doc's source-verified additions, not on the wiki
page.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin (not an action special or extension function — no `zcommon.bcs`
`special`-table entry; the p-code is wired straight into the compiler).
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Returns the cosine of `angle`, where `angle` is a **fixed-point fraction of a full turn** —
`0.0` to `1.0` spans `0`–`360` degrees, not the plain `int` the ZDoom wiki declares
it as (see "Wiki/engine divergence" below). Compiler builtin (`g_funcs[]` entry `"cos"`, `"f;f"` —
both the argument and return are typed `fixed`, the zt-bcc source's `src/builtin.c:103`),
implementation in `case PCD_COS:` (the Zandronum source's `src/p_acs.cpp:12241-12243`):

```cpp
case PCD_COS:
	STACK(1) = finecosine[angle_t(STACK(1)<<16)>>ANGLETOFINESHIFT];
	break;
```

- **Unit conversion.** The fixed-point `angle` argument (already a 16.16 value where `1.0` ==
  `65536` raw) is shifted left another 16 bits, reinterpreting it as a full 32-bit BAM
  (`angle_t`, where a complete turn is `0x100000000` wrapping mod 2^32), then shifted right by
  `ANGLETOFINESHIFT` (19, `tables.h:53`) to index an 8192-entry (`FINEANGLES`, `tables.h:49`)
  lookup table spanning one full turn. This is the same convention `GetActorAngle`/
  `SetActorAngle` use, so `Cos(GetActorAngle(0))` needs no extra scaling — consistent with the
  wiki's own example (`cos(angle + 0.25)`, a quarter-turn offset), even though the wiki's
  declared signature types the parameter `int`.
- **Out-of-range angles wrap for free.** Because the shift-and-cast to `angle_t` is unsigned
  32-bit arithmetic, a negative `angle` or one `>= 1.0` wraps to its equivalent in-circle angle
  automatically — there is no need to normalize into `[0.0, 1.0)` before calling. Not mentioned
  on the wiki.
- **Return range and implementation sharing.** Return is fixed-point in `[-1.0, 1.0]`. `Cos` is
  not a separate computation from `Sin` — `finecosine[x]` is defined as `finesine[x +
  FINEANGLES/4]` (`tables.h:63-70`), i.e. cosine reuses the sine table with a quarter-turn phase
  shift on the index. `Sin`/`Cos` are exact mirrors of each other with a fixed `+0.25` angle
  offset baked into the lookup, not independently-verified math.

## Wiki/engine divergence

The ZDoom wiki declares `fixed Cos(int angle)` — typing `angle` as plain
`int` — while its own prose calls it "the fixed point angle value" and its example passes fixed
literals (`angle + 0.25`). The compiler's actual builtin table types **both** the argument and
the return as `fixed` (`"f;f"`, `builtin.c:103`), not `int`/`fixed`. This looks like a stale
convention from old vanilla-ACS docs (before `fixed` existed as a distinct declared type) rather
than a Zandronum-specific gap — `PCD_COS`/`PCD_SIN` are base ACS p-codes with no Zandronum-only
behavior, so this mistyped-wiki-signature issue likely also holds for current upstream ZDoom, not
just Zandronum. Trust the compiler's `"f;f"` signature (and `zt-bcc`'s own `zcommon.bcs`/type
checking, which will flag a plain-int call site) over the wiki's declared parameter type.

## Engine-family divergence: table precision

UZDoom's `PCD_COS`/`PCD_SIN` (same p-code dispatch as Zandronum, in the UZDoom source's
`src/playsim/p_acs.cpp`) route through a `DAngle::Cos()`/`Sin()` helper (the UZDoom source's
`src/common/utility/vectors.h`) into a table-based fast-trig implementation (the UZDoom source's
`src/common/thirdparty/math/fastsin.cpp`) that agrees with everything documented above at the
contract level — the same 16.16-fraction-of-a-turn unit conversion (`65536` raw == a full turn,
same scale factor as Zandronum's `angle_t` shift), the same free wraparound for an out-of-range
input angle (the degrees-to-BAM conversion casts through an unsigned integer, wrapping mod 2^32
the same way Zandronum's `angle_t` cast does), and the same fixed-point `[-1.0, 1.0]` return
range. The underlying table lookup itself is not identical, though:

- Both engines size their base table at 8192 entries spanning one full turn (Zandronum's
  `FINEANGLES`; UZDoom's fast-trig `TBLPERIOD`), so the coarse resolution matches.
- Zandronum's table lookup returns a table entry directly — the input angle is truncated to the
  nearest of the 8192 slots with no interpolation, so its output is a step function of the input.
- UZDoom's fast-trig implementation linearly interpolates between the two adjacent table entries
  (using the angle's low bits below the table-index shift as an interpolation fraction), and
  reaches `Cos()` via quadrant-symmetry reflection into a quarter-turn helper rather than by
  literally indexing a precomputed cosine table offset by a quarter turn the way Zandronum's
  `finecosine[x] == finesine[x + FINEANGLES/4]` does.

Practically: for the same fixed-point input angle, the two engines' `Cos()`/`Sin()` can return
slightly different fixed-point values — UZDoom's interpolated result sits closer to the
mathematically exact cosine, while Zandronum's un-interpolated table lookup has a quantization
step (up to roughly the curve's local slope times 1/8192 of a turn — largest, tens of low-order
fixed-point units, near the steepest part of the curve around the quarter-turn points).
Gameplay-facing math (movement vectors, aim angles) won't notice; code that compares a `Cos()`
result for exact equality across engines, or replays a previously-recorded value verbatim, can.
Not on the wiki, which predates both this port and either engine's table internals.
