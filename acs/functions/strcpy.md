# `strcpy`

**Bucket:** none of the three — like [`restart`](restart.md), this is a **compiler
keyword/expression**, not a callable function. `StrCpy`/`strcpy` never appears in
`zt-bcc/src/builtin.c`'s `g_funcs[]` or `zcommon.bcs`'s `special` table. It's tokenized as
`TK_STRCPY` (`zt-bcc/src/parse/token/user.c:134`) and parsed by a dedicated grammar production
(`strcpy: strcpy <strcpy-call>`, `doc/grammar.txt:783-790`), sharing its call-syntax parser with
`memcpy` (`read_strcpy`/`read_strcpy_call`, `zt-bcc/src/parse/expr.c:1090-1105`). BCS lowercases
identifiers during tokenizing, so `StrCpy`/`strcpy`/`STRCPY` all compile identically (same
case-insensitivity as [`Random`](random.md)) — the wiki's `StrCpy` capitalization is just the
ZDoom-side house style, not a distinct spelling `bcc` recognizes.

**Tier:** A. **Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD —
see "Engine scope" in `../../shared/AUTHORING.md`).

**Provenance:** `StrCpy - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=StrCpy&oldid=37279`), verified against
the Zandronum source's `src/p_acs.cpp` (`PCD_STRCPYTO*CHRANGE`, lines 12893-12980) and
the zt-bcc source's `src` on 2026-07-29. The wiki's signature and top-level return-value description
are accurate for this fork, but it omits several storage-class-dependent edge cases only visible
in the interpreter source — see below.

## Syntax

```
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

## See also

[`memcpy`](https://zdoom.org/wiki/Memcpy) shares `strcpy`'s call-syntax parser and grammar
production one-for-one (`read_strcpy_call`) but copies whole arrays/structs instead of
string-into-`int`-array — not documented here since it wasn't in this batch's intake.
