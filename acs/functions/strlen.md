# `int StrLen(str string)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `StrLen - ZDoom Wiki.html` (https://zdoom.org/w/index.php?title=StrLen&oldid=35763), verified against fork source 2026-07-29.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.

Returns the length (character count) of `string`. Compiler builtin (`PCD_STRLEN`,
the zt-bcc source's `src/builtin.c:116`), implementation in `p_acs.cpp:12483-12500`.

- `string` — looked up via `FBehavior::StaticLookupString` (`p_acs.cpp:3318`), which resolves
  both dynamically-built strings (the global string pool, e.g. from `StrParam`) and static
  strings compiled into a loaded library/behavior lump — so this works on any `str` value
  regardless of which of those two sources it came from.
- **Failure behavior (not discoverable from the signature): if `string` doesn't resolve to a
  valid string** — e.g. a stale/out-of-range string handle, or a library-string index whose
  library isn't currently loaded — **`StrLen` returns `0`, not an error**, and the engine prints
  a bold one-time console warning (`"Warning: ACS function strlen called with invalid string
  argument.\n"`, `p_acs.cpp:12492-12497`). The warning is gated on a static `bool` and only ever
  prints once per engine session, so a script calling `StrLen` on a bad handle repeatedly (e.g.
  in a loop) will only warn the first time — don't rely on the console output to catch every
  occurrence during testing.
- Return value is indistinguishable between "valid empty string" (`""`, length `0`) and "invalid
  string handle" (also returns `0`) — if that distinction matters, validate the string handle
  some other way before calling `StrLen`.

## Wiki accuracy note

The ZDoom wiki page's usage note ("all strings in ACS are static... it is not really necessary to
use this function unless...") is generic ZDoom commentary about the string model and isn't
Zandronum-specific; nothing in it or the example script is wrong or fork-divergent. The function's
existence, signature, and normal-path behavior match both UZDoom and Zandronum exactly — the only
material gap is the failure-path behavior above, which the wiki page doesn't mention at all.
