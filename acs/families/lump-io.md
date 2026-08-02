# Lump I/O family

`LumpOpen`, `LumpRead`, `LumpReadString`, `LumpReadArray`, `LumpGetInfo`, `LumpClose` — a
mandatory-sequence API. A "handle" from `LumpOpen` is required by every other function; none of
them are meaningful in isolation, hence one family file instead of six per-function files.

**Bucket:** all six are extension functions (negative index in `zcommon.bcs`), semantics in
the Zandronum source's `src/p_acs.cpp`, `case ACSF_Lump*:`. Indices: `LumpOpen` -159, `LumpRead`
-160, `LumpReadString` -161, `LumpGetInfo` -166, `LumpClose` -167 (`zcommon.bcs:1789-1795`).
`LumpReadArray` has no *named* entry in `zcommon.bcs` — its four backing engine functions
(`ACSF_LumpReadLocal/Module/Hub/Global`) exist in `p_acs.cpp:8402` and occupy reserved indices
-162 to -165, but `zt-bcc` has no front-end syntax to call them — confirmed uncallable by actual
compile attempts (see its section below).

**Tier:** A for all six — `LumpOpen`/`LumpRead`/`LumpGetInfo`/`LumpClose`/`LumpReadString`/
`LumpReadArray` are all now wiki-derived and source-verified (2026-07-28); `LumpReadArray`'s
"tier A" fact is specifically "verified uncallable from this toolchain," not a usage guide.

**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md` for the version-gap caveat).

---

## `int LumpOpen(str name, int startIndex [, int flags])`

Opens a lump by name and returns a **handle** for use with the other `Lump*` functions.

- `name` — lump name to search for.
- `startIndex` — **mandatory in this toolchain**, despite the wiki listing it as optional. The
  engine (`p_acs.cpp:8257`, `case ACSF_LumpOpen`) does accept a 1-arg call (`argCount > 1` guards
  the read of `args[1]`), but `zcommon.bcs:1789` declares the BCS-visible signature as
  `LumpOpen(str, int; int)` — two mandatory args, one optional — so `bcc` rejects a 1-arg call
  outright (`error: not enough arguments in function call`, confirmed by compiling a test script).
  This is a **compiler-level restriction, not an engine one**: pass a negative value (e.g. `-1`)
  to get the same "first/last match" behavior the wiki describes for omitting it.
  - Semantics when passed: `FindLump(name, &startLump)` where `startLump = startIndex + 1` — i.e.
    **`startIndex` is exclusive**, the search begins at the lump *after* the one you pass
    (confirmed via `FWadCollection::FindLump`, `w_wad.cpp:945`, which scans starting at
    `*lastlump` inclusive). Passing `0` starts the search at lump index 1, not 0 — use `-1` to
    include lump 0. This matches the wiki's own iteration idiom (`startIndex = -1;` then always
    `LumpOpen(name, startIndex + 1)`), it isn't a project-specific gotcha.
  - If `startIndex < 0` (and no `LUMP_OPEN_FULLPATH` flag), falls through to
    `Wads.CheckNumForName(name)` instead — the first/last-loaded match rather than an iteration
    step.
- `flags` *(optional)* — bit 1 (`LUMP_OPEN_FULLPATH = 1`) makes `name` a full path
  (`Wads.CheckNumForFullName`) instead of a bare lump name; overrides `startIndex` iteration when
  set.

**Returns:** the handle (internally, this *is* the lump number) on success, **-1** if not found.

**Gotcha (observed in source, not documented on the wiki):** the handle **is** the lump number —
`LumpGetInfo`/`LumpRead`/etc. all key a map by this same integer. The "already open, don't
re-open" guard in the C++ (`p_acs.cpp:8288`) checks `ACSLumpHandles.CheckKey(args[0])`, but
`args[0]` at that point is the **name argument's string index**, not the resolved lump number —
so the guard can never match in practice, and the reference-count increment on line
`ACSLumpHandles[lumpNum].refCount++` runs on every call. Practical effect: calling `LumpOpen` on
the same lump twice bumps refCount to 2 (each `LumpClose` only decrements by 1), so **every
`LumpOpen` call must be paired with exactly one `LumpClose` call** — don't assume the engine
dedups repeated opens of the same name for you.

**Provenance:** wiki page `LumpOpen - Zandronum Wiki.html` (2026-07-28) + source-verified +
compile-tested (`startIndex` mandatory-arg finding). **Tier:** A.

---

## `raw LumpRead(int handle, int pos [, int type])`

Reads a fixed-size integer/float value from an open lump at a byte offset.

- `handle` — from `LumpOpen`.
- `pos` — byte offset into the lump (absolute seek, `SEEK_SET`).
- `type` *(optional, defaults to `LUMP_READ_UBYTE`)* — one of (all are real BCS constants,
  `zcommon.bcs:1286-1291`):
  - `LUMP_READ_BYTE` — signed 8-bit
  - `LUMP_READ_UBYTE` — unsigned 8-bit (default)
  - `LUMP_READ_SHORT` — signed 16-bit
  - `LUMP_READ_USHORT` — unsigned 16-bit
  - `LUMP_READ_INT` — signed 32-bit
  - `LUMP_READ_FLOAT` — 32-bit float, converted to BCS fixed-point on return

**Returns:** the value read. **0** on either of two failure cases, each printing a console
message: (a) `handle` was never opened via `LumpOpen`, or (b) `type` is not one of the six valid
constants.

**⚠ Wiki example bug:** the wiki's example script calls `LumpRead(startIndex, LUMP_READ_INT, 0)`
— that's `(handle, type, pos)` order. Both the declared signature *and* the actual
`p_acs.cpp:8314-8315` implementation (`lump.Seek(args[1], ...)` then `readType = args[2]`) are
`(handle, pos, type)`. **Do not copy the wiki example's argument order** — use
`LumpRead(handle, pos, type)`.

**Provenance:** wiki page `LumpRead - Zandronum Wiki.html` (2026-07-28) + source-verified.
**Tier:** A.

---

## `str LumpReadString(int handle, int pos [, int maxLen])`

Reads a string starting at `pos` in the lump, up to the end of the lump or `maxLen` bytes,
whichever is shorter.

- `handle` — from `LumpOpen`.
- `pos` — byte offset to start reading from.
- `maxLen` *(optional)* — caps the read length; only takes effect if `0 < maxLen < (lumpLength -
  pos)`.

**Returns:** the string read (null-terminated internally). Empty string `""` if `handle` is
invalid, or if `pos` is at/past the end of the lump (`p_acs.cpp:8367-8377`).

**Wiki says** "stops upon encountering a null terminator or the end of the lump" — true of the
*result*, not the read itself: the engine always reads exactly `len` raw bytes (capped by
`maxLen`/lump end) into a buffer, then hands the whole buffer to `GlobalACSStrings.AddString`,
which is what truncates at the first embedded `\0`. If the lump bytes in range contain no NUL,
you get all `len` bytes back even past what looks like "the string."

**Provenance:** wiki page `LumpReadString - Zandronum Wiki.html` (2026-07-28) + source-verified.
**Tier:** A.

---

## `raw LumpGetInfo(int handle, int infoType)`

Queries metadata about an opened (or even un-opened — see below) lump.

- `handle` — the lump number (from `LumpOpen`, or apparently any raw lump number).
- `infoType` — one of:
  - `LUMP_INFO_SIZE` (0) — lump size in bytes (`Wads.LumpLength`). **Named constant exists**
    (`zcommon.bcs:1295`).
  - `LUMP_INFO_NAME` (1) — full lump name as a string, or `""` if `handle` is out of range.
    **Named constant exists** (`zcommon.bcs:1296`).
  - `LUMP_INFO_NAMESPACE` (2) — the lump's namespace ID (`Wads.GetLumpNamespace`). **No named
    constant in `zcommon.bcs`** — only `LUMP_INFO_SIZE`/`NAME` are defined there; use the literal
    `2`. Same goes for every `LUMP_NAMESPACE_*` return-value constant the wiki lists (`_GLOBAL`,
    `_SPRITES`, `_FLATS`, ... ) — real engine behavior, no BCS-side names to `#include`.
  - `LUMP_INFO_WAD` (3) — index of the WAD/PK3 the lump came from (`Wads.GetWadnumFromLumpnum`).
    Same caveat: literal `3`, no named constant. The wiki suggests pairing this with
    `GetWadInfo`, but that function is **not reachable from this toolchain either** — it's a real
    engine ACSF (`p_acs.cpp:8945`, `ACSF_GetWadInfo`) but, like `LumpReadArray` below, has no
    entry in `zcommon.bcs`, so `bcc` has no name to call it by.

**Returns:** varies by `infoType` (see above). Prints `"LumpGetInfo: unknown info type %u\n"` and
returns 0 for anything else.

**Note:** unlike `LumpRead`/`LumpReadString`, this does **not** check `ACSLumpHandles` at all —
it operates directly on the raw lump number for `SIZE`/`NAMESPACE`/`WAD`, and only bounds-checks
for `NAME`. In practice this means you can call `LumpGetInfo` with a lump number you never passed
through `LumpOpen`. **The wiki's "an index higher than the total number of lumps can crash the
game" warning is corroborated by source**, not just repeated: `SIZE`/`NAMESPACE`/`WAD` all pass
`lumpNum` straight into `Wads.LumpLength`/`GetLumpNamespace`/`GetWadnumFromLumpnum` with no range
check (`p_acs.cpp:8489-8517`) — only the `NAME` branch bounds-checks first.

**Provenance:** wiki page `LumpGetInfo - Zandronum Wiki.html` (2026-07-28) + source-verified.
**Tier:** A.

---

## `void LumpClose(int handle)`

Decrements the handle's reference count; frees it once the count reaches 0.

- `handle` — from `LumpOpen`.

**Returns:** always 0 (return value has no meaning). No-op (returns 0 silently) if `handle` was
never opened.

**Reminder:** because of the `LumpOpen` refcount gotcha above, each `LumpOpen` needs exactly one
matching `LumpClose` — don't assume repeated opens of the same lump share one refcount slot.

**Provenance:** wiki page `LumpClose - Zandronum Wiki.html` (2026-07-28) + source-verified.
**Tier:** A.

---

## `LumpReadArray(int handle, int pos, array arr, int arrayOffset [, int length])` — **not callable from this toolchain**

`zcommon.bcs:1792-1793`'s comment ("a set of 4 functions... built-in to ACC") refers to the
**original ACC compiler**, not `zt-bcc`. The four backing functions are real and fully
implemented on the engine side — `ACSF_LumpReadLocal` / `ACSF_LumpReadModule` /
`ACSF_LumpReadHub` / `ACSF_LumpReadGlobal` (`p_acs.cpp:8402-8487`), one case per array storage
class (local/map array, module/library array, hub-scope world array, global array) — and
`zcommon.bcs` reserves their indices (`-162` to `-165`, between `LumpReadString` at `-161` and
`LumpGetInfo` at `-166`) but **does not name any of them**, and no dispatch logic exists anywhere
in `zt-bcc/src` to pick one based on the array argument's scope.

**Confirmed empirically**, not just by absence of a grep hit: compiling a test script that calls
`LumpReadArray(...)`, or any of the four case names directly (`LumpReadLocal`/`LumpReadModule`/
`LumpReadHub`/`LumpReadGlobal`), against this checkout's `bcc` fails with
`` `lumpreadarray` not found `` (and likewise for each other name) — there is no supported way to
reach these four engine functions from BCS source via this toolchain. Treat this as a hard
"can't use it here," not a documentation gap.

Engine-side semantics (`p_acs.cpp:8402-8487`), recorded for completeness / in case a future
`zt-bcc` adds the front-end sugar:
- `len = Wads.LumpLength(handle) - pos`; returns `0` immediately if `len <= 0`, or if `handle`
  was never opened via `LumpOpen` (prints `"LumpReadArray: Attempted read on non-existent lump
  handle!"`).
- `length` *(optional, arg index 4)* clips `len` down, but **only** if `0 < length < len`.
- `arrayOffset` *(optional, arg index 3, default `0`)* — index into the destination array to
  start writing at.
- **Local/Module arrays additionally clip** `len` to `arraySize - arrayOffset` (can't overrun the
  fixed-size array). **Hub/Global arrays do not get this clip** — the source comment explicitly
  says they "have the entire range of an integer available to them," meaning an oversized
  `length`/`pos` combination against a hub or global array is an out-of-bounds write footgun in
  the engine itself, not just a theoretical one. (Moot while the function stays unreachable from
  `bcc`, but worth knowing if `zt-bcc` ever exposes it.)
- **Returns** the number of bytes actually written (`len` after clipping) — matches the wiki's
  "returns the number of bytes read."

**Provenance:** wiki page `LumpReadArray - Zandronum Wiki.html` (2026-07-28) + source-verified +
compile-tested against `bcc`. **Tier:** A (verified-unreachable is still a
verified fact).

---

## See also (from the wiki's LumpRead page)

`LumpRead` · `LumpReadArray` · `LumpReadString` · `LumpGetInfo` · `LumpClose` — i.e. this exact
family, confirming there's no sixth sibling function being missed.
