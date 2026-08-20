# Palette translations (`CreateTranslation`)

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-05)
**Provenance:** read from the Zandronum source's `src/p_acs.cpp` (`PCD_STARTTRANSLATION`/`PCD_TRANSLATIONRANGE1..3`/`PCD_ENDTRANSLATION` cases), the UZDoom source's `src/playsim/p_acs.cpp` (`PCD_TRANSLATIONRANGE4`/`5`) and `src/common/engine/palettecontainer.cpp` (`FRemapTable::AddColourisation`/`AddTint`), the zt-bcc/bcc compiler source (`src/parse/stmt.c` `read_paltrans`, `src/codegen/stmt.c` `visit_paltrans`), and the original `acc` compiler's `parse.c` (`LeadingCreateTranslation`, read only — never quoted, see `../../shared/AUTHORING.md`). No wiki page involved. 2026-08-05.

`CreateTranslation` looks like an ordinary ACS function call and is not one. It's a
**dedicated statement** in both compilers' grammars, with its own multi-clause syntax and no
entry in any special/`ACSF` table — which is why it can't be declared with `special`, can't be
used as an expression, and compiles to a *sequence* of pcodes rather than one. This page covers
the clause syntax, what each clause kind actually does at the engine level, the operand units
(which differ per clause kind and are the main trap), and the bytecode shape.

## Source form

```text
CreateTranslation ( <slot> [ , <clause> ]... ) ;

<clause>  ::= <begin> : <end> = <replacement>
<replacement> ::= <pal1> : <pal2>                        // palette-index range
                | [ r,g,b ] : [ r,g,b ]                  // RGB range
                | % [ r,g,b ] : [ r,g,b ]                // desaturated range
                | # [ r,g,b ]                            // colourisation
                | @ <amount> [ r,g,b ]                   // tint
```

Every operand is a full expression, not a literal — none of these clauses is restricted to
constants, and non-constant operands compile the same way (see "Bytecode shape" below). The
statement is a statement: it needs its trailing `;`, and it can't appear in expression position.

Case: `bcc`/`zt-bcc` is case-sensitive and spells the keyword `createtranslation`; `acc`
lowercases every identifier before keyword lookup, so any casing parses there. **Lowercase is
the only spelling that works under both.**

A zero-clause `CreateTranslation(n);` is legal and meaningful, not a degenerate no-op: it resets
slot `n` to the identity translation (the engine's `MakeIdentity()`), which is how a script
clears a slot it set earlier.

## Slot numbering

The first argument is a **1-based** level-scripted translation slot. The engine ignores the
whole statement's effect when it's outside `1..MAX_ACS_TRANSLATIONS` — silently, with no error
and no return value to test (the statement has no result at all), so an out-of-range slot is
invisible at runtime. The slot number is what a `Thing_SetTranslation`-style consumer refers to
later; nothing about the translation is addressable by any other handle.

## Clause kinds and their units

The five clause kinds differ in operand count *and* operand units. Getting the units wrong is
the main hazard here, because nothing in the syntax distinguishes them:

| Syntax | Engine effect | Operand units |
|---|---|---|
| `b:e = p1:p2` | remap palette indices `b..e` onto `p1..p2` | plain palette indices (0-255) |
| `b:e = [r,g,b]:[r,g,b]` | remap `b..e` onto a gradient between two RGB colours | plain 0-255 channel values |
| `b:e = %[r,g,b]:[r,g,b]` | desaturate `b..e` and remap onto a gradient | **fixed point** — the engine reads these six as `fixed_t` and converts to doubles |
| `b:e = #[r,g,b]` | colourise (multiply the greyscale luminance of `b..e` by an RGB colour) | plain 0-255 channel values |
| `b:e = @a[r,g,b]` | tint `b..e` toward an RGB colour by `a` | `r,g,b` plain 0-255; **`a` is a 0-100 PERCENT integer** (the engine does `amount * 0.01f`), *not* fixed point and not 0-255 |

Two of these are easy to get backwards:

- The `%` (desaturation) clause is the **only** one whose colour operands are fixed point.
  `%[0.0,0.0,0.0]:[1.5,1.0,0.5]` is the intended spelling; writing `%[0,0,0]:[255,255,255]`
  there compiles fine and means something wildly different (255.0 rather than ~1.0).
- The `@` (tint) clause's *amount* is a percentage even though the clause sits right next to the
  fixed-point `%` one. `@50[255,0,0]` is a half-strength red tint; `@0.5[...]` compiles to
  `32768`, i.e. a 32768% tint.

The `@` clause has a **parsing quirk** in both compilers: `@amount[r,g,b]`'s `[` is ambiguous
with an array subscript on `amount`, and both resolve it by refusing to parse a subscript in
that position at all. To use a subscripted value as the amount, parenthesize it —
`@(amounts[i])[255,0,0]`. A bare `@amounts[i][255,0,0]` is a syntax error, not a subscript.

## Engine-family divergence

`CreateTranslation` compiles under both compilers with all five clause kinds. The **engine**
support is narrower:

- Zandronum implements `PCD_TRANSLATIONRANGE1`/`2`/`3` only. Its interpreter has **no case at
  all** for `4`/`5` — a `#` or `@` clause compiles cleanly and then does nothing there (it falls
  through the pcode switch), so this is a silent no-op, not a script error.
- GZDoom-family engines (verified on UZDoom) implement all five.

So `#`/`@` are a portability trap specifically: the compiler is not the gate, the engine is, and
the failure mode is silence.

Zandronum additionally mirrors every applied translation to clients when running as a server
(each range op has its own `SERVERCOMMANDS_CreateTranslation`-family call, plus a
stored-for-late-joiners list) — relevant if you're wondering whether a scripted translation
survives a client connecting after the script ran. It does.

## Bytecode shape

One `CreateTranslation` statement compiles to a **run** of pcodes, not one:

```text
<push slot>              PCD_STARTTRANSLATION      (pops 1)
<push clause operands>   PCD_TRANSLATIONRANGE1..5  (pops 4/8/8/5/6 — see below)
...                      (one such group per clause, in source order)
                         PCD_ENDTRANSLATION        (pops 0)
```

Operands are pushed left-to-right in source order, always starting with `begin` then `end`:

| Pcode | Clause | Pops | Push order |
|---|---|---|---|
| `PCD_TRANSLATIONRANGE1` | `b:e = p1:p2` | 4 | `b, e, p1, p2` |
| `PCD_TRANSLATIONRANGE2` | `b:e = [..]:[..]` | 8 | `b, e, r1, g1, b1, r2, g2, b2` |
| `PCD_TRANSLATIONRANGE3` | `b:e = %[..]:[..]` | 8 | `b, e, r1, g1, b1, r2, g2, b2` |
| `PCD_TRANSLATIONRANGE4` | `b:e = #[..]` | 5 | `b, e, r, g, b` |
| `PCD_TRANSLATIONRANGE5` | `b:e = @a[..]` | 6 | `b, e, a, r, g, b` |

Both compilers emit exactly this, in this order — `acc` and `zt-bcc`/`bcc` agree pcode-for-pcode
here, so a translation statement's bytecode doesn't identify which compiler produced it.

Three consequences worth knowing if you're reading or generating bytecode rather than source:

- **The whole run is straight-line and branch-free.** None of the three pcodes is a jump or a
  jump target, so a `CreateTranslation` never spans a basic-block boundary; a `START` without a
  matching `END` in the same block means the input is malformed.
- **The "translation under construction" is a local of the interpreter's own `RunScript` call**,
  set by `PCD_STARTTRANSLATION` and cleared by `PCD_ENDTRANSLATION` — so it does not survive the
  script yielding (a `Delay`, a `ScriptWait`) and is not shared between scripts. A range pcode
  with no active translation is a silent no-op, not an error: every range case is guarded by a
  null check. Splitting one `CreateTranslation` across a delay isn't expressible in source
  anyway, but it's worth knowing the state isn't durable.
- **A `%` clause is indistinguishable from an RGB clause in the pushed values alone**; only the
  pcode number carries the fixed-vs-int distinction. Two clauses that push identical constants
  can mean completely different colours.

## See also

- [Units and encodings](units-and-encodings.md) — what "fixed point" means for the `%` clause's
  operands.
- [ACSe/ACSE compiled object format](acse-object-format.md) — the surrounding bytecode container.
