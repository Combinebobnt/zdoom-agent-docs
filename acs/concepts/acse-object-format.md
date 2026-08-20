# ACSe/ACSE compiled object format (the `.o`/`BEHAVIOR` binary layout)

**Tier:** B — reverse-engineered directly from `acc`/`bcc`'s own writer (zt-bcc's
`src/codegen/chunk.c`, `src/codegen/obj.c`, `src/codegen/pcode.c`) and Zandronum's reader
(`src/p_acs.cpp`), then empirically validated by writing a decoder and running it against real
compiled objects — not sourced from a wiki page (this is below source-code level, not something
the language-reference wiki documents at all).
**Applies to:** UZDoom=yes, Zandronum=yes — Zandronum 3.2.1 / zt-bcc (current `master`). The two
formats described here (`ACSe` compact, `ACSE` uncompressed-enhanced) are what `acc`/`bcc`
actually emit by default; there is also a legacy `ACS\0` "old" format this doc does not cover.
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** Built and validated while decompiling a source-less third-party mod
(`acbots`/"Advanced Coop Bots") for a Zandronum project, using this project's own compiled
`osacs.o`/`BEHAVIOR.o` (source available) as a 100%-verifiable ground truth. Validation: a
disassembler built from the rules below decoded every one of 125+367+347 script/function entry
points across three real objects with zero boundary drift, and (for the two objects with known
source) reconstructed statement-for-statement-correct expressions including exact argument order,
confirmed against the real hand-written source.

## Why this matters

There is no ACSe-format disassembler/decompiler documented anywhere in this tree, and (as far as
this investigation found) no actively-maintained public one either — an old Python 2 tool exists
by reputation but wasn't reachable to check (no network access during this investigation). Every
fact below was derived by reading the compiler's own writer and the engine's own reader side by
side, then cross-checking with a working decoder against real objects. If you're staring at a
compiled `.o`/`BEHAVIOR` lump with no `.acs` source, this is the format underneath it.

## Header and chunk-directory trailer

An object starts `ACS\0` (bytes 0-3) followed by a 4-byte little-endian int at bytes 4-7. What
that int means depends on byte 3:

- **Byte 3 is `'E'` or `'e'`** (a "bare" enhanced object): the int at bytes 4-7 IS the real
  chunk-directory offset, directly.
- **Byte 3 is `0x00`** (the far more common shape — what `acc`/`bcc` actually emit by default,
  `chunk.c:74-151`'s `c_write_chunk_obj`): the int at bytes 4-7 (`dirofs`) points at a trailing
  "dummy directory" stub kept for old-engine backward compatibility (a `while (c_tell() < 32)`
  zero-pad plus a dummy-scripts/dummy-strings area, both usually empty). The REAL structure sits
  immediately **before** that stub:
  - `[dirofs-8 : dirofs-4]` = the real chunk-directory offset (int32 LE)
  - `[dirofs-4 : dirofs]` = `'ACSe'` (compact) or `'ACSE'` (uncompressed enhanced), the format tag

  This exactly mirrors Zandronum's own read path (`p_acs.cpp:2373-2425`): `pretag =
  ((DWORD*)(object+dirofs))[-1]` reads the tag; `Chunks = object +
  ((DWORD*)(object+dirofs))[-2]` reads the real offset. The `ACS\0`+trailer shape exists purely
  so an old engine that doesn't understand `ACSe`/`ACSE` still sees a well-formed (if useless)
  legacy object instead of garbage.

Past the real chunk-directory offset: a flat sequence of `[4-byte ASCII tag][4-byte LE size][size
bytes of body]` chunks, no outer count — walk until you fall off the end of the file (or hit the
zero-size `ALIB` sentinel `chunk.c` always writes last when the library is `importable`).

## Compact (`ACSe`) pcode encoding

This is the encoding that matters for disassembly; `ACSE` (uncompressed) is the same opcode set
with every opcode AND every operand as a plain 4-byte int, no packing at all — trivial by
comparison.

**Opcode**: 1 byte if `< 240`; if `>= 240`, a 2-byte escape: `real_opcode = 240 + ((byte0 - 240) <<
8) + byte1`. Source: `p_acs.cpp`'s interpreter loop, `if (pcd >= 256-16) { pcd = (256-16) +
((pcd-(256-16))<<8) + getbyte(pc); }`; `obj.c`'s `write_opc` mirrors it exactly on the write side.

**Operand width** is the part with no single rule — it's per-opcode, and naively assuming
"compact means everything is a byte" silently misdecodes real objects. Cross-checking `obj.c`'s
`write_arg` (the compiler's write side) against `p_acs.cpp`'s interpreter (the read side) sorts
every opcode into one of four groups:

1. **Always byte, in BOTH `ACSe` and `ACSE` objects** — `PUSHBYTE`/`PUSH2BYTES`.../`PUSH5BYTES`/
   `PUSHBYTES` (this one has a variable-length byte-count-prefixed tail, itself always byte-sized
   regardless of format), `LSPEC1DIRECTB`...`LSPEC5DIRECTB`, `DELAYDIRECTB`, `RANDOMDIRECTB`. The
   interpreter reads these via raw `*(BYTE*)pc` unconditionally, with no format check anywhere in
   their case bodies — format-independent.
2. **`LSPECn`/`LSPECnDIRECT`/`LSPEC5RESULT`**: only the FIRST operand (the action-special number)
   is byte-sized, and only when compact (`obj.c`: `if (opc_args==0 && compress) byte; else int`).
   Any later operand (an `LSPECnDIRECT`'s literal special-call arguments) is always a 4-byte int.
   Interpreter mirrors this via the `NEXTBYTE`/`NEXTSHORT` macros (`fmt==ACS_LittleEnhanced ?
   getbyte(pc) : NEXTWORD`).
3. **The large var/array-access family** — `PUSHSCRIPTVAR`/`PUSHMAPVAR`/`PUSHMAPARRAY`/
   `PUSHWORLDVAR`/.../`ASSIGN*`/`ADD*`/`SUB*`/`MUL*`/`DIV*`/`MOD*`/`INC*`/`DEC*`/`AND*`/`EOR*`/
   `OR*`/`LS*`/`RS*` (both `VAR` and `ARRAY` suffix forms) plus `PUSHFUNCTION`/`CALL`/
   `CALLDISCARD`: every operand these opcodes have is byte-sized ONLY in a compact object, else a
   plain int. Also `NEXTBYTE`-gated on the interpreter side.
4. **`CALLFUNC`**: its own independent rule, two operands with DIFFERENT widths that don't fit
   groups 1-3 — see below.
5. **Everything else** (arithmetic/comparison/logical binary+unary ops, control flow, `CASEGOTO`/
   `CASEGOTOSORTED`, `DUP`/`SWAP`/`DROP`, `TAGSTRING`, print-family, ...): always a plain 4-byte
   int, in both formats. `CASEGOTOSORTED`'s jump table gets 4-byte-aligned before its
   count-and-pairs int32 array regardless of format (the alignment is a no-op in `ACSE` mode,
   where `pc` is already word-aligned by construction).

**`CALLFUNC`** (the ACSF-extension-function call opcode) has its own two-part rule not covered by
any of the above: `argcount` is `NEXTBYTE`-gated (byte when compact, else int), `funcIndex` is
`NEXTSHORT`-gated (2-byte short when compact, else int) — i.e. compact encoding is
`[opcode][argcount:byte][funcIndex:short]`, uncompressed is `[opcode:int][argcount:int]
[funcIndex:int]`.

**`CALLFUNC` always pushes exactly one result value, unconditionally** — this is easy to get
backwards from the extension-function's own declared return type. The interpreter
(`p_acs.cpp:9461-9473`): `int retval = CallFunction(...); sp -= argCount-1; STACK(1) = retval;` —
net effect is pop `argCount`, push 1, regardless of whether the specific ACSF function is declared
`void`. There is no `CALLFUNC`-discard opcode; a `void`-declared extension function called in
statement position gets an explicit `PCD_DROP` right after it in the compiled output instead.
(By contrast, ordinary user-function calls DO have a discard opcode — `CALL` keeps the return
value, `CALLDISCARD` doesn't push it at all, chosen by the compiler at the call site based on
whether the value is used.)

**`CASEGOTO`/`CASEGOTOSORTED` only pop their tested value on a match.** On no-match they fall
through with the value still on the stack (`p_acs.cpp`: `else { pc += 2; }` for `CASEGOTO`, no
`sp--`) — the compiler's own emitted "default" path is responsible for discarding it (usually an
explicit `PCD_DROP`, but not always: one real-world pattern reuses the still-peeked value directly
as the very next instruction's own operand — see "Function-pointer null-check idiom" below).
Anyone hand-decoding a `switch` needs to track this or it looks like a stack-depth bug.

## Chunk formats worth knowing (used to recover names/data, not just code)

- **`SPTR`**: script table, one 8-byte entry per script — `int16 number` (negative =
  named script, see `SNAM` below), `uint8 type` (0=unnamed/CLOSED, 1=OPEN, 2=RESPAWN, 3=DEATH,
  4=ENTER, 5=PICKUP, 6/7/8=BLUE/RED/WHITE-RETURN, then a gap at 9-11, 12=LIGHTNING,
  13=UNLOADING, 14=DISCONNECT, 15=RETURN, 16=EVENT, 17=KILL — cross-checked against Zandronum's
  own `SCRIPT_*` enum, `p_acs.h:338-352`), `uint8 argc`, `int32 addr`.
- **`SFLG`**: sparse `int16 number, int16 flags` pairs, only for scripts with nonzero flags.
  `SCRIPTF_Net=0x1`, `SCRIPTF_ClientSide=0x2` (`p_acs.h:358-360`) — these are flag bits on an
  otherwise normally-typed script, not script types of their own, despite `NET`/`CLIENTSIDE`
  reading like type keywords in source.
- **`SNAM`/`FNAM`**: both the same offset-table shape — `int32 count`, then `count` int32
  byte-offsets (relative to the chunk body start) to NUL-terminated strings. `SNAM` entries are
  indexed by a named script's `SPTR.number`, recovered as `-(number)-1`. `FNAM` entries are in
  `FUNC`-table order and are what a `CALL`/`CALLDISCARD` operand indexes into.
- **`FUNC`**: one 8-byte entry per function, in `FNAM`-parallel order — `uint8 params` (total
  param SLOT count, `c_total_param_size` — 1 slot per scalar param), `uint8 size` (**EXTRA locals
  beyond the param slots**, i.e. `impl->size - params`, NOT a total — confirmed empirically: a
  3-param function with 6 more local variables has `FUNC.size == 6`, not 9; a decompiler that
  subtracts `params` again under-declares locals), `uint8 value` (nonzero = non-void return),
  `uint8` pad, `int32 offset` (0 for an imported/external function, whose `size` is also 0).
- **`ARAY`**: one 8-byte entry per map array — `int32 number`, `int32 size` (element count).
  `AINI` (one chunk per initialized array): `int32 array_number` then a run of `int32` element
  values starting at index 0, with the writer omitting everything from the highest nonzero index
  onward (so a chunk's byte length, not a separate count field, gives you `(size-4)/4` elements —
  zero-fill the rest up to the array's real `ARAY` size).
- **`ATAG`**: per-array element type tags — `uint8 version` (currently always 0), `int32
  array_number`, then one `uint8` per tagged element (0=plain int, 1=string-table index,
  2=function reference), with trailing untagged (implicitly-int) elements omitted from the chunk
  the same way `AINI` omits trailing zeros. This is how a raw `int` element that's "secretly" a
  string handle (or a `PUSHFUNCTION` value stored for later `CALLSTACK` use, see below) gets
  distinguished from an ordinary integer when reading array contents back out.
- **`MEXP`**: exported (non-`private`) map variable AND array names, same offset-table shape as
  `SNAM`/`FNAM` — **but with no index field per entry.** `chunk.c`'s `do_mexp` just walks
  `codegen->vars` in declaration order, skipping hidden ones, and writes names in that order.
  There is no reliable way to map `MEXP[i]` back to the specific var/array *number* that
  `PUSHMAPVAR`/`PUSHMAPARRAY` operands actually encode without assuming declaration order exactly
  matches index-allocation order (plausible, unverified) — treat `MEXP` as "these names exist and
  are exported," not as an index-keyed lookup table.

## Engine-family divergence: the `SPTR` type byte and the `SFLG` flag word

Everything else described above reads the same on both engines — the `ACS\0`-plus-trailer probe,
the flat chunk walk, the opcode escape and all five operand-width groups, `CALLFUNC`'s
one-result-always rule, `CASEGOTO`'s pop-only-on-match, `CALLSTACK`'s calling convention, and
every chunk layout listed here. The script table is the one place the two loaders assign different
meanings to the same bytes:

- **`SFLG` bit `0x0002` is not portable.** Zandronum reads it as `SCRIPTF_ClientSide`. UZDoom has
  no such concept in its ACS flag word — it names that bit `SCRIPTF_Ignored` and documents it as
  meaningless, so a `CLIENTSIDE`-flagged script in an object built for Zandronum loads on UZDoom
  as an ordinary script rather than being rejected or specially handled. Bit `0x0001`
  (`SCRIPTF_Net`) matches on both.
- **`SPTR` type `18` exists only on UZDoom** (`SCRIPT_Reopen`, appended past `17`/`KILL`).
  Zandronum's script-type enum ends at `17`, so a type byte of `18` corresponds to no script type
  it knows. Types `0`-`17`, gap at `9`-`11` included, are identical on both.

Two adjacent facts the `SPTR`/`SFLG` bullets above are best read against — both **identical** on
the two engines, i.e. corrections to those bullets rather than divergences:

- The flag word has a third bit past the two listed: `0x0004`, `SCRIPTF_Busy`, exempting the
  script from the runaway-instruction limit. Present in both engines' enums.
- `SPTR`'s 8-byte entry shape applies only to the `ACS\0`-plus-trailer object shape. In a "bare"
  enhanced object — byte 3 literally `'E'` or `'e'`, the first case under "Header and
  chunk-directory trailer" above — both loaders instead read **12-byte** entries, and not merely
  widened ones: the layout is `int16 number`, `uint16 type`, `int32 addr`, `int32 argc`, with
  address and argument count in the opposite order from the 8-byte form. The selector is the
  object's first four bytes, not the `ACSe`/`ACSE` tag, so a decoder that picks entry width from
  the format tag misparses this shape.

## `PCD_TAGSTRING` vs. an opcode that resolves its own string index

`PCD_TAGSTRING` marks the value on top of the stack as a string-table index (technically:
resolves it into the runtime global string table and rewrites the stack slot with that resolved
handle — `Stack[sp-1] = GlobalACSStrings.AddString(activeBehavior->LookupString(Stack[sp-1]))`).
It shows up after a `PUSHNUMBER`/`PUSHBYTE` whose value is a literal string-table index, e.g.
`GetCvar("some_name")` compiles to `PUSHNUMBER <strtab index>; TAGSTRING; CALLFUNC GetCvar`.

**Not every string consumer requires it, and assuming one does causes a real misdecode.**
`PCD_PRINTSTRING`/`PCD_PRINTLOCALIZED` (the `Log`/`Print`/`HudMessage`-family string-part
opcodes) interpret their popped value as a string-table index directly at the engine level
(`FBehavior::StaticLookupString(STACK(1))`, no tag/resolve step) — a bare `PUSHNUMBER 492;
PRINTSTRING` with no `TAGSTRING` in between is completely normal, valid, compiler-emitted output
for `Log(s:someStringLiteral)`, not truncated or malformed code.

## `PCD_CALLSTACK` (BCS-only function-pointer calls) is not in vanilla ACS

`PCD_CALLSTACK` calls through a function-pointer *value* rather than a compile-time-fixed function
index — it's a BCS extension (`zt-bcc`'s `visit_sample_call`, `src/codegen/expr.c:1830`),
generated only for a call through a `ReturnType function(ParamTypes)? var` reference-to-function
value (`zt-bcc.wiki/Declarations.md`'s "reference-to-function" type). **If an object uses
`PCD_CALLSTACK` at all, it was compiled by a BCS-superset compiler (`bcc`/`zt-bcc`), not vanilla
`acc`** — a useful, cheap discriminator when you don't know what compiled a given `.o` and need to
pick the right recompiler to round-trip it.

Calling convention, from the interpreter (`p_acs.cpp:9484-9498`): the function-pointer value is
`STACK(1)` (the very top) at the moment `CALLSTACK` executes; the callee's actual arguments sit
below it, in the same stack positions a normal `CALL`'s arguments would occupy
(`Stack[sp-func->ArgCount]` onward) — i.e. push the arguments first, then the pointer value last,
then `CALLSTACK`. The compiler's own codegen for a call with arguments doesn't push the pointer
directly where it's needed, though: `visit_sample_call` evaluates the pointer expression, stashes
it into a compiler-allocated scratch script-var, pushes each argument, then reloads the scratch
var and immediately calls — a decompiler reading this pattern needs to recognize
`ASSIGNSCRIPTVAR(tmp); <arg pushes>; PUSHSCRIPTVAR(tmp); CALLSTACK` as one call, not a spurious
assignment plus an unrelated var read. (For a zero-argument call the stash is skipped entirely —
the pointer value is used directly off the top of the stack.)

**Function-pointer null-check idiom.** One real-world pattern combines `CASEGOTO`'s
peek-without-popping-on-no-match behavior (above) with `CALLSTACK` directly: `<push the pointer
value>; CASEGOTO 0, <address of a "null function" safety stub>; CALLSTACK` — if the pointer is
exactly 0 (an invalid/uninitialized function reference), jump to a stub instead of calling through
garbage; otherwise fall through and call the SAME still-on-the-stack peeked value directly,
without any intervening re-push. A decompiler that assumes every `CASEGOTO`'s no-match path is
followed by an explicit `DROP` will misdecode this as a stack underflow.

## Two general things worth stating for anyone building on this

- **A compiled function/script body gets trailing `PCD_TERMINATE` padding appended past its real
  logical end** (observed directly: a minimal one-line function compiles to its real body
  followed by two back-to-back `PCD_TERMINATE` instructions) — for every entry except the last one
  in an object, this padding falls inside the *next* entry's own body and is naturally ignored;
  for the last entry, it's part of that entry's own bounded address range and needs an explicit
  reachability pass (from the entry's own start, following all real control-flow edges) to
  recognize as dead code rather than as further real instructions to decode.
- **`terminate`/`suspend`/`restart` are script-only statement keywords in BCS source** (bare,
  no parens — `zt-bcc.wiki/Grammar.md`'s `script-jump-statement`), a hard compile error inside a
  plain `function` body ("terminate statement outside script") even though `PCD_TERMINATE` itself
  turns up perfectly validly inside compiled function bytecode (e.g. the pattern above, or a
  compiler-synthesized internal helper). There's no function-body source-level equivalent that
  preserves the exact semantics (aborting the *entire calling script chain*, not just the current
  function) — `return`/`return 0` is the closest legal approximation, not a faithful one.
