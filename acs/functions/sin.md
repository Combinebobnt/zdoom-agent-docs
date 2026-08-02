# Sin

**Tier:** A
**Engine:** Zandronum 3.2.1 (checked against the Zandronum source's master/3.3-alpha checkout)
**Provenance:** `Sin - ZDoom Wiki.html` (intake, `oldid=35792`), verified against fork source 2026-07-29.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

`fixed Sin(fixed angle)` — **compiler builtin**, not an extension function. Listed in
the zt-bcc source's `src/builtin.c`'s `g_funcs[]` as `{ "sin", "f;f" }` (return fixed, one fixed
param), compiled directly to opcode `PCD_SIN`. Implemented in the Zandronum source's `src/p_acs.cpp`,
`case PCD_SIN:`:

```cpp
case PCD_SIN:
    STACK(1) = finesine[angle_t(STACK(1)<<16)>>ANGLETOFINESHIFT];
    break;
```

Returns the sine of `angle`, where `angle` is the same **fixed-point fraction-of-a-turn** encoding
used by `GetActorAngle`/`VectorAngle`/`Cos` (`0.0`-`1.0` = one full turn, not degrees or radians) —
see [units-and-encodings.md](../concepts/units-and-encodings.md) for that encoding in general, not
re-derived here. The return value uses the same 16.16 fixed-point scale (`FRACUNIT`/`65536` =
`1.0`) for the sine magnitude itself, ranging `-1.0` to `1.0`.

## Wiki says `int angle` — bcc types it correctly as `fixed`

The ZDoom wiki declares the signature as `fixed Sin(int angle)`. As with
[VectorAngle](vectorangle.md), this is imprecise: `builtin.c` types the parameter `f` (fixed), and
`bcc`-compiled calls type-check/coerce accordingly. Pass a genuine fixed-point turn-fraction
(e.g. `GetActorAngle(0) + 0.25`), not a plain small integer — `Sin(1)` means "sine of one full
turn" (`≈0`), not "sine of 1 angle-unit."

## Undocumented: input is quantized to 1/8192 of a turn before lookup

The wiki doesn't mention this, and it's real, verified against the Zandronum source's `src/tables.h`:

- `finesine` has `5*FINEANGLES/4` entries where `FINEANGLES = 8192` (`tables.h:49,58`).
- `ANGLETOFINESHIFT = 19` (`tables.h:53`).
- The engine takes the 16.16 fixed `angle` argument, left-shifts it 16 bits into a 32-bit
  `angle_t` (BAM angle, full turn = `2^32`, silently wrapping — this is what makes the encoding
  periodic: `Sin(1.0) == Sin(0.0)`), then right-shifts by `ANGLETOFINESHIFT` (19) to index the
  table. Net effect on the original fixed value: **right-shift by 3** (`19 - 16`).
- That means only the top 13 bits of the fractional turn actually matter — the input is quantized
  to steps of `8/65536` (`1/8192`) of a full turn (`65536 >> 3 == 8192` table entries per turn)
  before the lookup happens. Two `angle` values less than `1/8192` of a turn apart (`≈0.00012`,
  or about `0.044°`) return the **exact same** sine value, bit for bit — not a rounding
  approximation of a continuous function, a real table quantization step. Not significant for
  typical gameplay-angle use (player/actor angles, HUD math), but relevant if `Sin`/`Cos` are used
  to approximate a smooth curve or chase very small angular deltas.

## Example (from the wiki)

Spawns two Medikits flanking the activator, using `Cos`/`Sin` to offset perpendicular-ish to
facing angle:

```c
script 1 (void)
{
    int x = GetActorX (0);
    int y = GetActorY (0);
    int z = GetActorZ (0) + 32.0;
    int angle = GetActorAngle (0);

    Spawn ("Medikit", x + cos (angle + 0.25) * 32, y + sin (angle + 0.25) * 32, z);
    Spawn ("Medikit", x + cos (angle + 0.75) * 32, y + sin (angle + 0.75) * 32, z);
}
```

(BCS is case-insensitive, so the wiki's lowercase `sin`/`cos` calls compile identically to
`Sin`/`Cos`.)

## See also

- [VectorAngle](vectorangle.md) — sibling compiler builtin using the same fixed-point
  fraction-of-turn angle encoding; same wiki `int`-vs-`fixed` mistyping note.
- [units-and-encodings.md](../concepts/units-and-encodings.md) — fixed-point angle encoding used
  by this function's `angle` parameter.
- `Cos` — same family, quantization, and wiki-mistyping notes apply identically (processed
  separately in this intake batch; not written here).
