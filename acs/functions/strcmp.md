# `int StrCmp(str string1, str string2 [, int maxcomparenum])` / `int StrIcmp(str string1, str string2 [, int maxcomparenum])`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `StrCmp - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`https://zdoom.org/w/index.php?title=StrCmp&oldid=40904`) + source-verified against `p_acs.cpp:6616-6638` (`ACSF_strcmp`/`ACSF_stricmp` case),
`zt-bcc/lib/zcommon.bcs:1691-1692` (indices `-63`/`-64`), and
`src/Linux/platform.h:35-37` (`strnicmp` → `strncasecmp` `#define`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (negative index → `ACSF_strcmp`/`ACSF_stricmp` in `p_acs.cpp`).

Character-by-character string comparison. Extension functions (`ACSF_strcmp`, index `-63`;
`ACSF_stricmp`, index `-64`, both in the zt-bcc source's `lib/zcommon.bcs:1691-1692` as `Strcmp`/
`Stricmp` — BCS is case-insensitive, so `StrCmp`/`StrIcmp` compile identically), shared
implementation in `p_acs.cpp:6616-6638`.

- `string1`/`string2` — the two strings to compare.
- `maxcomparenum` (optional) — if given, only the first `maxcomparenum` characters of each string
  are compared (`strncmp`/`strnicmp`); if omitted, the full strings are compared (`strcmp`/
  `stricmp`). **A negative `maxcomparenum` does not error or truncate to zero-length** — it's read
  into a signed `int` (`p_acs.cpp:6630`) and passed straight through to `strncmp`'s/`strnicmp`'s
  `size_t` count parameter, so it wraps to a huge unsigned value; since `strncmp`/`strncasecmp`
  (Zandronum's Linux `strnicmp` is `#define`d straight to `strncasecmp`,
  `src/Linux/platform.h:36`) also stop early at either string's NUL terminator, the practical
  effect of a negative `maxcomparenum` is an unbounded/full-string comparison, same as omitting it
  — not a documented behavior on the wiki.
- Return value: the raw return of the underlying libc `strcmp`/`strncmp`/`stricmp`/`strnicmp`
  call — `0` if equal (up to `maxcomparenum` chars, if given), a positive value if `string1`'s
  first differing character sorts higher, negative if `string2`'s does. Matches the wiki's
  description exactly. **Only the sign is meaningful** — the magnitude is whatever the libc
  implementation happens to return (commonly the byte-value difference of the first mismatching
  character, but that's a libc-internal detail, not part of the ACS contract); don't compare the
  return value to anything other than `0`, `> 0`, `< 0`.
- `StrIcmp` is the exact same code path as `StrCmp`, just dispatched to the case-insensitive libc
  variants (`stricmp`/`strnicmp`) based on which `ACSF_*` index was called (`p_acs.cpp:6631`,
  `:6635`) — no behavioral difference beyond case-sensitivity.
- **Fork/engine safety net not on the wiki:** both string arguments are resolved via
  `FBehavior::StaticLookupString`; if either resolves to `NULL` (an invalid/out-of-range string
  handle), it's silently substituted with `""` rather than crashing or erroring
  (`p_acs.cpp:6624-6626`, comment: `// Don't crash on invalid strings.`) — an invalid handle acts
  like an empty string, not a failure signal.

No other wiki/fork divergence found — the two-overload signature (with/without `maxcomparenum`)
and comparison semantics match the wiki as described.

**Why this function exists instead of `==`:** `==`/`!=` on `str` is a raw integer comparison of
the string's table index, not its content — safe between two runtime-built (`StrParam`/
concatenation/pool-origin) strings, but **always false/true respectively** when one side is a
compiled literal and the other is pool-origin, regardless of matching text. See
[String literal vs. pool equality](../concepts/string-literal-vs-pool-equality.md) for the full
mechanism. `StrCmp`/`StrIcmp` resolve both sides to actual characters first, so they're correct
across that boundary — use them (`StrCmp(a, b) == 0`) whenever either operand might not be a
literal from the same compiled module as the other.
