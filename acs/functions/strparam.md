# `StrParam` / `strparam`

**Bucket:** none of the three — like [`strcpy`](strcpy.md), this is a **compiler builtin
keyword**, not a `zcommon.bcs`-declared function or action special. `strparam` never appears in
`zcommon.bcs`'s `special` table (positive or negative index) and it is not a normal
`g_funcs[]` entry either in the sense of taking ordinary parentheses arguments — it's one of the
five names in `zt-bcc/src/builtin.c`'s dedicated **"Format functions" block** (`builtin.c:167-174`:
`print`, `printbold`, `hudmessage`, `hudmessagebold`, `log`, `strparam`), the same family that
implements `Print`/`Log`/`HudMessage`'s `s:`/`d:`/`c:`/etc. format-item call syntax. The tier-C
stub's signature (`str StrParam()`, zero args) reflects exactly this: `g_funcs[]`'s format string
for `strparam` is just `"s"` (return type `str`, no parenthesized parameter list — `builtin.c:174`,
consumed by `setup_return_type`, `builtin.c:404-435`, which maps `'s'` to `SPEC_STR`). The actual
arguments are **format items**, parsed by a completely separate grammar path
(`peek_format_cast`/`read_format_item_list`, `zt-bcc/src/parse/expr.c:901-931,949-1035`) that
every call expression checks for before falling back to ordinary comma-separated arguments — this
is why the auto-generated scaffolder saw "zero args" for a function whose whole point is taking
arguments: it read `g_funcs[]`'s post-return-type parameter string, which is genuinely empty for
`strparam`, and had no way to see the format-item grammar bolted on separately.

**Tier:** A. **Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD —
see "Engine scope" in `../../shared/AUTHORING.md`).

**Provenance:** `StrParam - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=StrParam&oldid=45949`), verified against
the Zandronum source's `src/p_acs.cpp` (`PCD_SAVESTRING`, line 12884, and the `ACSStringPool`
implementation, lines 396-560+) and the zt-bcc source's `src` on 2026-07-29.

## Syntax

```
str s = StrParam( <format-item-list> );
```

`<format-item-list>` is a comma-separated list of `<cast>:<expr>` items, exactly the same syntax
`Print`/`Log`/`HudMessage` use — `s:` (string), `d:` (decimal/int), `c:` (char), `f:` (fixed),
`x:` (hex), `b:` (binary), `k:` (key-bind name), `l:` (localized string), `n:` (class/name
lookup), `i:` (raw), `a:` (array) — full list in `read_format_cast`,
`zt-bcc/src/parse/expr.c:1003-1031`. Because `strparam` shares its parser with the other four
format functions, any cast usable in `Print`/`Log` is usable in `StrParam` too (this includes
casts the wiki page itself doesn't enumerate, e.g. `k:`/`n:`/`a:`/`i:`/`b:` — the wiki only shows
`s:` in its example).

Unlike `HudMessage`, which takes a required (and optional) plain-argument tail after a `;`
following the format-item list, `strparam`'s `g_funcs[]` entry has no post-semicolon parameter
string at all — there is no trailing non-format argument list for `StrParam`, just the format
items.

## Return value and behavior

Compiles to the same sequence of `PCD_PRINTSTRING`/`PCD_PRINTNUMBER`/etc. opcodes that
`Print`/`Log` use to accumulate a `FString` "work" buffer from the format items, but terminates
with **`PCD_SAVESTRING`** instead of `PCD_ENDPRINT`/`PCD_ENDLOG` (`p_acs.cpp:12884-12891`):

```cpp
case PCD_SAVESTRING:
    const int str = GlobalACSStrings.AddString(work);
    PushToStack(str);
    STRINGBUILDER_FINISH(work);
    break;
```

- The return value is a **string-table index** into `GlobalACSStrings`, the same global dynamic
  string pool used by `PCD_TAGSTRING` and every other "on the fly" string producer — not a
  library-local or per-call-frame handle. This matches the wiki's "return value is the string
  table index of the new string."
- **Interning:** `ACSStringPool::AddString` (`p_acs.cpp:474-498`) hashes the built string and
  checks for an existing identical entry (`FindString`) before inserting a new one — **identical
  content always returns the identical string ID**, it does not allocate a fresh slot per call.
  Calling `StrParam(s:"hangar", s:"key")` twice yields the same integer both times.
- **Lifetime — this is where the wiki's caveat is stale for this fork.** The wiki page (as
  written, oldid 45949) frames the 1-tic-lifetime behavior as the historical default and treats
  the "lasts indefinitely" fix as a footnote ("As of revision r4295..."). The Zandronum source's
  own in-source comment block directly above `ACSStringPool` (`p_acs.cpp:396-434`) states plainly
  that this fork **already has the post-r4295 persistent-string pool**: *"Strings returned by
  strparam last indefinitely. No longer do they disappear at the end of the tic they were
  generated."* Garbage collection is reference-counted against the ACS stack, all running
  scripts' locals, map/world/global variables, and an explicit lock count — a `StrParam` result
  is safe to store in a `world`/`global` variable and read back on a later tic or after a map
  change (library strings likewise no longer need every library loaded in the same order). On
  Zandronum 3.2.1 the wiki's "only exists for 1 tic, a delay will nullify it" opening sentence and
  the accompanying example's pre-r4295 comments (`"but its contents are only valid until this
  tick ends..."`, `"no keyObject here on pre-r4295"`) do **not** apply — treat the whole example
  as demonstrating syntax only, not this fork's actual string lifetime.
- **Multiplayer/demo-sync warning is real and still applies.** The wiki's warning about
  indeterminate results (e.g. a format item whose value can differ between clients feeding into
  something that affects the playsim) is a general ACS determinism concern, not something this
  fork's persistent string pool changes — `l:`/`k:`/`n:` casts in particular can format
  differently per client (localization, keybind name, actor class display name), so a
  `StrParam` result built from one of those casts is still unsafe to feed into anything that
  must stay in sync (RNG seeding, spawning, geometry changes). Safe uses (HUD display, chat text)
  are unaffected.
- **Related open question, not re-verified here:** `INDEX.md`'s note on
  `../concepts/clientside-scripting.md` flags as *unverified* whether a `StrParam`-produced string
  ID survives being passed as an `ACS_ExecuteAlways` argument from server to client. Since the
  string pool this doc describes is genuinely global engine state (not per-script or
  per-side), a stale/foreign ID would only be a problem if client and server ever have
  divergent pool contents (e.g. a client hasn't yet executed the same `StrParam` call and so
  never inserted that entry) — plausible but not traced in this pass; that concept doc's
  "unverified" tag should stay until someone checks it specifically.

## See also

`Print`/`Log`/`HudMessage` (not yet documented in this tree) share the exact same format-item
grammar and opcode sequence up to the terminator opcode — a future doc for any of them should
cross-reference this one rather than re-deriving the cast-type table.

**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.
