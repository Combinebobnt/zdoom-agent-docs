# Old-style `ACS\0` compiled object format (the original Hexen-era `BEHAVIOR` layout)

**Tier:** B — reverse-engineered from real compiled `BEHAVIOR` lumps and cross-read against
Zandronum's own `ACS_Old` load path (`src/p_acs.cpp`, `src/p_acs.h`), then empirically validated
by writing a decoder and running it over a 57-object corpus of shipped Hexen-family `BEHAVIOR`
lumps. Not sourced from a wiki page — this is below source-code level.
**Applies to:** UZDoom=yes, Zandronum=yes — the layout itself is fixed by the 1995-era compiler and
has not changed since; both engines still load it, and their old-format readers are the same code
apart from the string-lookup difference recorded below.
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3
(2026-08-16)
**Provenance:** Established while scoping old-format support for an ACS decompiler. Validation:
every one of 939 script bodies across all 57 objects disassembled to an exact instruction
boundary with zero drift and zero unrecognized opcodes, and the recovered statements were
confirmed against genuine period ACS source for one map plus against an independent 1995
decompiler (`DEACC` 1.1) run over the entire corpus.

## Why this matters

This is the format that predates the chunked `ACSe`/`ACSE` objects described in
[ACSe/ACSE compiled object format](acse-object-format.md) — the one Hexen itself shipped, and the
one a modern `acc` still emits when asked for Hexen-compatible pcode. A decoder written only
against `ACSe` will reject or silently misread it. It is also, structurally, far *simpler* than
`ACSe`: no chunks at all.

Do not confuse the two on magic bytes alone. **Both formats begin with the literal bytes
`ACS\0`.** In a modern object those bytes are a backward-compatibility wrapper and the real format
tag lives just before the trailing dummy directory (see the `ACSe` doc's header section). In a
genuinely old object there is no such tag — the bytes mean what they say.

**Discriminating the two:** read `dirofs` (the 4-byte LE int at offset 4); if `dirofs >= 24`, look
at the 4 bytes at `dirofs-4`. If those are `ACSe` or `ACSE`, it's a modern object wearing a legacy
hat. Otherwise — or if `dirofs` is below that threshold — it's a real old-style object. This is
exactly the test the engine performs (`p_acs.cpp:2408-2423`) before deciding whether to keep
`Format = ACS_Old`; the `dirofs >= 6*4` guard is part of the condition, not an afterthought, and
skipping it means reading a "pretag" out of a region the engine would never have consulted.

## Layout

Four fixed regions. No chunk directory, no chunk tags, nothing optional.

```text
0x00   char[4]   "ACS\0"        magic; byte 3 is a real NUL, not 'E'/'e'
0x04   uint32    dirofs         absolute offset of the directory
0x08   ...       pcode          starts here, always; the first script's address is always 8
       ...       string DATA    NUL-terminated, packed after the last pcode byte

dirofs + 0                      uint32 script_count
dirofs + 4                      script_count * 12 bytes, each:
                                    uint32 number
                                    uint32 address
                                    uint32 argcount
dirofs + 4 + 12*script_count    uint32 string_count
                                string_count * uint32 offsets (ABSOLUTE, from file start)
```

The string offset table is the last thing in the file — `dirofs + 4 + 12*script_count + 4 +
4*string_count` equals the lump length exactly, with no trailing padding (held for all 57 objects
measured).

The 12-byte script record matches the engine's own struct field-for-field (`p_acs.h:303-308`,
`ScriptPtr2`: `Number`, `Address`, `ArgCount`, all `DWORD`). The string-table base is computed by
the engine as `dirofs + script_count*12 + 4` (`p_acs.cpp:2434-2435`), and a string is looked up as
"element 0 of the table is the count, element `1+index` is an absolute offset from the start of
the lump" (`p_acs.cpp:3339-3344`).

### Script number and type share one field

There is no separate type byte. The single `number` field encodes both:

```text
script_number = number % 1000
script_type   = number / 1000        (0 = closed/ordinary, 1 = OPEN, ...)
```

This is precisely what the engine does when loading the directory (`p_acs.cpp:2866-2867`). It is
the historical reason ACS script numbers are conventionally capped at 999.

### Gotcha: pcode does not run to `dirofs`

String *bytes* live between the end of the pcode and `dirofs`. The end of the code section is
therefore:

```text
code_end = min(dirofs, min(string_offsets))
```

not `dirofs`. A decoder that assumes `dirofs` will happily disassemble packed C strings as pcode
and produce garbage (or a bogus decode error) at the tail of the last script. There is no marker,
padding, or alignment gap separating the two regions — the last instruction's final byte is
immediately followed by the first string's first byte.

## Instruction encoding

Every opcode and every operand is a plain 4-byte little-endian int. That is the same encoding the
engine uses for the uncompressed `ACSE` format — there is **no** compact encoding here: no
240-value opcode escape, no per-opcode byte/int operand-width rules, none of the packing that
makes `ACSe` decoding fiddly.

Consequences for a decoder that already handles `ACSE`: the instruction reader needs no changes at
all, only the header parser does.

## What this format does not have

Absent entirely, because the language of the era had none of it:

- **No user-defined functions.** No `FUNC`/`FNAM` equivalent, no `PCD_CALL`, no call stack.
- **No arrays** of any storage class. No `ARAY`/`AINI`/`ATAG` equivalent.
- **No named scripts.** Scripts are numbers only.
- **No libraries or imports.** A `BEHAVIOR` lump is self-contained.
- **No exported map-variable names.** Map variables are addressed purely as opcode operands
  (`PCD_PUSHMAPVAR` etc.), so a decompiler must synthesize declarations from observed usage; the
  engine likewise just points all map-var slots at a flat store (`p_acs.cpp:2453-2459`).
- **No script flags.** No `NET`/`CLIENTSIDE` equivalent — those are `ACSe`-era chunk data.
- **No encrypted string table.** Strings are stored plainly.

## Gotcha: string arguments carry no type marker

`PCD_TAGSTRING` — the opcode that marks a pushed value as a string-table index in `ACSe` objects
(see the sibling doc's section on it) — **does not appear in this format at all**. A string
argument compiles to an ordinary push of the table index, byte-identical to pushing an integer.

For example, a three-argument sound call whose middle argument is a string literal compiles to
three plain pushes followed by the sound opcode; nothing in the bytecode distinguishes the string
index from the surrounding numbers.

This matters for anything reconstructing source: the only way to know an operand is a string is to
know, per opcode, which parameter positions are string-typed. Opcodes observed taking a string
index this way include the thing/sector/ambient sound family and the line-texture setter. Opcodes
that pop a string by definition (the print family) are unaffected — they were already
self-describing.

## Gotcha: script numbers are not unique

Old compilers did not enforce script-number uniqueness *across different script types*, so one
lump can legitimately contain both an ordinary `script N` and a `script N OPEN`. The engine knows
this and works around it explicitly at load time, warning and reordering so the closed variant
sorts first (`p_acs.cpp:2930-2949`, whose own comment states the compiler never enforced
uniqueness). Two independent occurrences were found in the corpus measured for this doc.

Anything that re-emits recovered source must handle this — modern compilers reject a duplicate
script number outright.

## Gotcha: `delay` is one tic longer in this format

The engine adds one tic to every `PCD_DELAY`/`PCD_DELAYDIRECT` when the format is `ACS_Old` **and**
the game is Hexen (`p_acs.cpp:10475`, `10484`, `10493`) — a compatibility shim for the original
game's own timing. See [`delay`](../functions/delay.md).

This is invisible if you recompile recovered source back to the same format, but it means source
recovered from an old-format lump and retargeted to a modern `ACSe` object runs every delay one
tic shorter than the original did.

## Gotcha (format-independent): `PCD_SUSPEND` is resumable, not a terminator

Worth stating alongside the above because old-format code uses `suspend` far more freely than
modern code does, but it is **not** specific to this format.

`PCD_SUSPEND` sets the script's state to suspended and breaks out of the interpreter loop with the
program counter already advanced past the opcode (`p_acs.cpp:9262-9264`). When the script is later
resumed it continues at the **following instruction**. So, for control-flow analysis:

- `terminate` ends the script — control does not continue.
- `restart` redirects control to the script's entry point — control does not fall through.
- `suspend` **does** fall through to the next instruction, just not immediately.

Treating `suspend` as a hard terminator (as is tempting, since all three "stop the interpreter
loop" in the same place) makes every instruction after a mid-body `suspend` look unreachable, and
a reachability-based decoder will silently discard real code. This was found live: one script in
the corpus measured for this doc lost ten statements that way.

## Engine-family divergence: UZDoom's Hexen string-localization hook

Every claim above was re-verified against UZDoom's own old-format reader and holds unchanged there:
the magic dispatch on byte 3 (`0` / `'E'` / `'e'`), the `dirofs >= 6*4` plus pretag-at-`dirofs-4`
discriminator, the 12-byte `Number`/`Address`/`ArgCount` script record, the `number % 1000` /
`number / 1000` split, the `dirofs + script_count*12 + 4` string-table base and its "element 0 is
the count, element `1+index` is an absolute offset from the start of the lump" lookup, the flat
map-var store, the duplicate-script-number warning and closed-first reorder, the extra `delay` tic
under Hexen, and `PCD_SUSPEND`'s resumability. The file:line citations elsewhere in this doc are
into the Zandronum tree; UZDoom holds the same code at `src/playsim/p_acs.cpp` and
`src/playsim/p_acs.h`.

**One real behavioral difference, and it is on the string table.** A UZDoom behavior module carries
a per-module "should localize" flag, set at load time only when *all* of: the level was loaded with
the Hexen-compatibility MAPINFO flag, the gametype is Hexen, the object is the map's own embedded
`BEHAVIOR` lump rather than a separately loaded ACS library, and the archive containing that map is
literally `HEXEN.WAD` or `HEXDD.WAD`. When the flag is set, an old-format string lookup made *for a
print operation* first synthesizes a language-table key from the map name, the string index, and an
uppercased, punctuation-stripped five-character prefix of the string's own bytes, and returns the
translated string if the string table has an entry under that key; only on a miss does it fall back
to the raw lump bytes. Zandronum's old-format lookup has no such path and always returns the lump
bytes.

Consequences if you care about what an old-format lump actually says:

- On UZDoom, what a shipped Hexen/Hexen:DD script *prints* is not necessarily the byte content of
  the lump's string table, so a decoder's recovered text and the engine's on-screen text can
  legitimately disagree for those two IWADs without either being wrong. Nothing else is affected:
  user content in old format, and every non-print use of a string index (see the string-argument
  gotcha above), read the raw bytes on both engines.
- Both engines run the same in-place escape-sequence pass over the old-format string table at load,
  the same one applied to an `ACSe` object's `STRL` chunk, so backslash escapes stored literally in
  the lump are resolved before any lookup. "No encrypted string table" above still holds — this is
  escape processing, not decryption — but the in-memory table is not a byte-for-byte image of the
  lump's, and its offsets have been byte-swapped in place on a big-endian host.

## Producing test material

A modern `acc` can still emit this format — its `-h` option is documented as producing pcode
compatible with Hexen and old ZDooms, and the result is a genuine `ACS\0` object with the layout
above. Useful for generating small, known-input fixtures without needing shipped game lumps.

**This is an `acc`-only capability — the zt-bcc/bcc compiler fork cannot produce this format at
all.** Its object writer emits `ACSe` or `ACSE` unconditionally (with the `ACS\0` compatibility
header and trailing dummy directory the sibling doc describes), and it exposes no output-format
option. Do not reach for `bcc -h` by analogy: in zt-bcc `-h` prints the compiler's own help text,
not Hexen-compatible pcode.

Two caveats found by testing `acc`:

- The Hexen-era `const:` argument tag that period sources use is rejected by modern `acc`; write
  fixtures without it.
- Old and modern compilers lower control flow differently, and `-h` reproduces the *old* shapes —
  loops come out top-tested (`cond; branch-out; body; jump-back`) rather than the bottom-tested
  form modern compilers emit, and a `switch` pushes its value, jumps forward past every case body
  to a case-test chain placed at the end, then discards the value if nothing matched. Any pattern
  matcher tuned on modern output will not recognize either shape.

## Tooling note

A period MS-DOS decompiler for this format, `DEACC` 1.1 (1995), exists and still runs under
DOSBox. It resolves string arguments and reconstructs `while`/`switch` structure correctly, which
makes it a usable independent oracle when validating a new decoder against this format — the
cross-check behind this doc's own validation claim.
