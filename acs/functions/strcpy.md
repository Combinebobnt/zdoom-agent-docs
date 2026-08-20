# `strcpy`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes — resolves to `compiler-only` by bare name (`strcpy` is
a compiler keyword/expression, not a callable, see Bucket below), but all four opcodes it compiles
to (`PCD_STRCPYTOMAPCHRANGE`/`PCD_STRCPYTOWORLDCHRANGE`/`PCD_STRCPYTOGLOBALCHRANGE`/
`PCD_STRCPYTOSCRIPTCHRANGE`) are confirmed present on both engines (`tools/engine_matrix.py`, bin
`both` for each), so the keyword is fully portable
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `StrCpy - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=StrCpy&oldid=37279`), verified against
the Zandronum source's `src/p_acs.cpp` (`PCD_STRCPYTO*CHRANGE`, lines 12893-12980) and
the zt-bcc source's `src` on 2026-07-29. The wiki's signature and top-level return-value description
are accurate for Zandronum, but it omits several storage-class-dependent edge cases only visible
in the interpreter source — see below.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** none of the three — like [`restart`](restart.md), this is a **compiler
keyword/expression**, not a callable function. `StrCpy`/`strcpy` never appears in
`zt-bcc/src/builtin.c`'s `g_funcs[]` or `zcommon.bcs`'s `special` table. It's tokenized as
`TK_STRCPY` (`zt-bcc/src/parse/token/user.c:134`) and parsed by a dedicated grammar production
(`strcpy: strcpy <strcpy-call>`, `doc/grammar.txt:783-790`), sharing its call-syntax parser with
`memcpy` (`read_strcpy`/`read_strcpy_call`, `zt-bcc/src/parse/expr.c:1090-1105`). BCS lowercases
identifiers during tokenizing, so `StrCpy`/`strcpy`/`STRCPY` all compile identically (same
case-insensitivity as [`Random`](random.md)) — the wiki's `StrCpy` capitalization is just the
ZDoom-side house style, not a distinct spelling `bcc` recognizes.

The "Bytecode shape" section below was added later (2026-08-05), verified against the same
Zandronum source plus both compilers' codegen (zt-bcc's `src/codegen/expr.c`, `acc`'s `parse.c`)
and live compiles under `acc` 1.59/1.60 — the wiki documents no bytecode-level detail at all.

## Syntax

```text
bool ok = strcpy( destination, source [, source_offset] );
bool ok = strcpy( a: destination_array [, array_offset [, array_length]], source [, source_offset] );
```

- `destination` — a one-dimensional `int` array (any storage class: local, map-scope `static`,
  `world`, or `global`). The bare form (no `a:`) is shorthand for `a: destination` with
  `array_offset=0` and `array_length` unbounded (`INT_MAX`) — per `doc/details.md`'s own note,
  `a:` is only required when you need to supply `array_offset`/`array_length`.
- `source` — a `str` expression to copy from.
- `source_offset` — optional index into `source` to start copying from (this is the wiki's
  `source_index`).

Despite the different-looking grammar (`a:` label, no comma between the array and its
offset/length), the resulting **argument order matches the wiki's shown signature**
`StrCpy(a:destination, source[, source_index])` exactly — this is one of the few ZDoom-wiki
function pages that maps onto BCS syntax essentially unchanged.

## Return value and behavior

Compiles to one of four opcodes chosen by the destination's storage class — `PCD_STRCPYTOMAPCHRANGE`
(map-scope `static` arrays), `PCD_STRCPYTOWORLDCHRANGE`, `PCD_STRCPYTOGLOBALCHRANGE`, or
`PCD_STRCPYTOSCRIPTCHRANGE` (local/function-scope arrays, the `default` case in
`visit_strcpy`, `zt-bcc/src/codegen/expr.c:2454-2500`). All four share one handler in
`p_acs.cpp:12893-12980`:

- **Negative `array_offset` or negative `source_offset`** → returns `false` immediately, writes
  nothing. This matches the wiki's "false ... if a negative source_index was given", but the
  wiki never mentions that a negative *array_offset* triggers the identical early-out.
- **Invalid/stale source string handle** (`FBehavior::StaticLookupString` returns null) →
  treated as "no data, operation already complete" and returns **`true`**, not `false` — same
  silent-substitution pattern documented for [`StrCmp`](strcmp.md)/[`StrLen`](strlen.md). Copying
  from a garbage string handle looks like a trivial success, not a copy failure.
- **`source_offset` larger than the actual source string length** (the skip-`source_offset`-chars
  loop hits the string's own terminating `0` before reaching the requested offset) → also returns
  **`true`** via the same "operation complete" path, not `false`. Only a *negative* offset fails;
  an out-of-range positive one silently succeeds at copying nothing. The wiki's phrasing implies
  only negative values are special-cased, which is correct, but doesn't call out that an
  overrun is a silent no-op/success rather than an error.
- **Normal copy:** characters are copied one at a time up to `array_length` (or until the source's
  terminating `0` is reached, which is never itself written). Return is `true` only if the loop
  stopped because it *reached* the terminator within budget; if `array_length` characters are
  copied and the source still has more (the "next" character isn't `0`), it returns `false` — the
  wiki's "false if the copy ran out of room" is accurate.
- **Destination bounds differ by storage class — not documented on the wiki at all:**
  - **Map-scope arrays** (`PCD_STRCPYTOMAPCHRANGE` → `FBehavior::CopyStringToArray`,
    `p_acs.cpp:3269-3283`) are the only variant that's fully self-consistent: `array_length` is
    silently clamped down to `declared_size - array_offset` if the requested length would
    overrun the array, and an invalid array id or negative offset returns `false`. The reported
    return value always accurately reflects what was actually written.
  - **Local/function-scope arrays** (`PCD_STRCPYTOSCRIPTCHRANGE`) go through
    `ACSLocalArrays::Set()` (`p_acs.h:243-250`), which silently no-ops any write whose
    `arrayentry` falls outside the array's declared size — **but the copy loop itself doesn't
    know that.** It still walks the full source string, still decrements its `array_length`
    budget, and still returns `true` if it reaches the terminator in budget, even though every
    out-of-bounds character along the way was silently dropped instead of written. A `strcpy`
    into a local array with too-small `array_length`/`array_offset` bookkeeping can report
    `true` while having written nothing past the array's real end — the return value is not a
    reliable "everything landed" signal for this storage class the way it is for map arrays.
  - **`world`/`global` arrays** (`PCD_STRCPYTOWORLDCHRANGE`/`PCD_STRCPYTOGLOBALCHRANGE`) write
    straight into `ACS_WorldArrays[a]`/`ACS_GlobalArrays[a]`, which are sparse `TMap<int,int>`
    (`FWorldGlobalArray`, `p_acs.h:69`), not fixed-size buffers — there is no declared capacity
    to overrun, so every index within `array_length` genuinely gets written and the return value
    is as reliable as the map-array case. Only the array *number* `a` is bounds-checked (against
    `NUM_WORLDVARS`/`NUM_GLOBALVARS` via `BoundsCheckingArray`), not the element index.

## Bytecode shape

Relevant if you're reading or generating compiled ACS rather than writing source. All four
opcodes take **six** stack operands and leave **one** result. Verified against both compilers'
codegen (`zt-bcc/src/codegen/expr.c`'s `visit_strcpy`; acc's `ActionOnCharRange`,
`parse.c`, reached from `LeadingStrcpy`) and the interpreter's own `STACK(6)`..`STACK(1)`
comment (`p_acs.cpp:12897-12898`), then re-checked against live compiles of both.

Pushed in this order — deepest (pushed first) at the top:

| depth | operand | value when the source omits it |
| --- | --- | --- |
| `STACK(6)` | destination array **base index** | `0` |
| `STACK(5)` | destination **array number** | always a `PUSHNUMBER` immediate — never an expression |
| `STACK(4)` | destination **array offset** (`array_offset`) | `0` |
| `STACK(3)` | destination **array length** (capacity) | `INT_MAX` (`0x7FFFFFFF`) |
| `STACK(2)` | **source string** handle | — (required) |
| `STACK(1)` | **source offset** (`source_offset`) | `0` |

Net stack effect: pops all six, pushes the `bool` result — the interpreter implements that as
`sp -= 5` with the deepest slot (`Stack[sp-6]`) overwritten in place.

Three things worth knowing that aren't visible from the source syntax:

- **The two destination operands are just added together.** The interpreter computes the write
  index as `STACK(4) + STACK(6)`, with no other use for either. The split exists only because
  the *compiler* has two places to put an index: subscripting a multi-dimensional destination
  (`a:(arr[i], 3, 8)` where `arr` is `[n][width]`) puts the flattened `i * width` in the base
  operand and leaves `array_offset` at 3, while indexing a flat array
  (`a:(arr, i * width + 3, 8)`) puts the whole sum in `array_offset` and leaves the base at 0.
  **Both spellings compile to the same effective write index**, so the operand split carries no
  semantic information — only a hint about how the original source was written. Anything
  reconstructing source from bytecode should treat the two as one summed offset (and
  constant-fold it, since both compilers fold a literal-plus-literal offset into a single
  `PUSHNUMBER`).
- **The array number is always an immediate.** It's a compile-time array id in both compilers
  (`object.index` / `sym->info.array.index`), so a non-constant value in that slot means the
  opcode wasn't produced by a real `strcpy` lowering.
- **The array number's *namespace* differs per opcode**, matching the storage class:
  `PCD_STRCPYTOMAPCHRANGE` indexes the module's own map-array table,
  `WORLD`/`GLOBAL` index the engine-global `ACS_WorldArrays`/`ACS_GlobalArrays`, and
  `SCRIPT` indexes the enclosing script/function's **local** array table — a separate
  per-entry namespace whose sizes live in the object's `SARY`/`FARY` chunks (read by
  `p_acs.cpp`'s `ParseLocalArrayChunk`), not in the module-level array chunk. A local array id
  and a local *scalar* variable id are independent numbers; they collide freely.

The sibling `PCD_PRINT{SCRIPT,MAP,WORLD,GLOBAL}CHRANGE` /
`PCD_PRINT*CHARARRAY` opcodes are the read direction of the same construct and share acc's
parser entirely (`ActionOnCharRange(write)`, one boolean apart) — the `a:` format item inside a
print/log call.

## See also

[`memcpy`](https://zdoom.org/wiki/Memcpy) shares `strcpy`'s call-syntax parser and grammar
production one-for-one (`read_strcpy_call`) but copies whole arrays/structs instead of
string-into-`int`-array — not documented here since it wasn't in this batch's intake.
