# `str Strftime(int timestamp, str format [, bool utc])`

**Tier:** A.
**Engine:** Zandronum 3.2.1 (confirmed predates the 3.2.1 version-bump commit).
**Provenance:** wiki page `Strftime - Zandronum Wiki.html` (`_intake/`, retrieved 2026-07-29, `oldid=1338`) + source-verified against `p_acs.cpp:7409-7426`, `zt-bcc/lib/zcommon.bcs:1762`, and version-gated against `f614049b4`/`28f736fb3` per shared/AUTHORING.md's "Engine scope" section.
**Bucket:** extension function.

Formats a Unix timestamp (as returned by `SystemTime()`) into a human-readable string, using the
host C library's `strftime()` with the caller-supplied `format` string passed through unmodified.
Extension function (`ACSF_Strftime`, index `-129` in the zt-bcc source's `lib/zcommon.bcs:1762`),
implementation in `DLevelScript::CallFunction`'s `case ACSF_Strftime:`
(the Zandronum source's `src/p_acs.cpp:7409-7426`).

Added together with `SystemTime`/`GetTimeProperty` in commit `f614049b4` ("Added ACS date and
time functions SystemTime, GetTimeProperty and Strftime...", 2015-08-30), which is an ancestor of
the 3.2.1 version-bump commit `28f736fb3` (confirmed via `git merge-base --is-ancestor
f614049b4 28f736fb3`, verified true) — so this function predates and is present in Zandronum
3.2.1, not a post-3.2.1 addition from the `master`/`3.3-alpha` checkout.

## Parameters

- `timestamp` — a Unix timestamp (seconds since epoch), typically from `SystemTime()`. Cast to
  `time_t` and **clamped to `0` if negative** (`p_acs.cpp:7412-7416`,
  `if ( timer < 0 ) timer = 0;`) — unlike `GetTimeProperty`, which passes a negative timestamp
  straight to `localtime`/`gmtime` with no clamp. A negative `timestamp` here silently becomes
  the epoch (1970-01-01) instead of a pre-epoch date or an error.
- `format` — a string of `strftime()` conversion specifiers (`%Y`, `%m`, `%d`, `%B`, `%H`, etc.).
  **The engine does not parse, validate, or rewrite this string in any way** — it is looked up
  with `FBehavior::StaticLookupString` and handed directly to the C library's `strftime()`
  (`p_acs.cpp:7418-7422`). This means the actual set of supported conversion specifiers is
  whatever the build's C runtime implements, not a curated ZDoom/Zandronum-specific list — the
  wiki's "It may contain any supported conversion specifiers" is accurate but vague for exactly
  this reason: "supported" means "supported by libc," which can differ by platform (e.g. `%e`,
  `%G`/`%V`, or locale-dependent specifiers may behave differently across glibc/musl/MSVCRT).
- `utc` — optional (`argCount >= 3 ? !!args[2] : false`, `p_acs.cpp:7419`), defaults to `false`.
  `false`/omitted uses `localtime` (the **server or client machine's local timezone**), `true`
  uses `gmtime` (UTC). Same clientside/netcode caveat as `GetTimeProperty`: with `utc` false, a
  `CLIENTSIDE` script evaluated on machines in different timezones will format the same
  `timestamp` differently — pass `utc: true` for output that must agree across machines.

## Return value

The formatted string as a dynamic ACS string, built from a fixed `char buffer[1024]`
(`p_acs.cpp:7411`). If the underlying `strftime()` call returns `0` — which happens both on
genuine failure (formatted result plus NUL wouldn't fit in 1024 bytes) and on some libcs for a
legitimately-empty result (e.g. an empty `format`) — the buffer is explicitly zeroed
(`p_acs.cpp:7422-7423`) and an empty string `""` is returned either way. Unlike
`GetTimeProperty`'s `0`-return ambiguity (real zero vs. unmatched case), this one has no
practical ambiguity: both failure and legitimate-empty-format produce the same observable `""`.

Per the wiki, and confirmed by the fact that ACS ints are 32-bit and `timestamp` is passed as a
plain ACS `int`, this function (like `SystemTime`) is subject to the year-2038 problem regardless
of the host's own `time_t` width — the timestamp value itself can't represent a UNIX time beyond
`INT32_MAX`.

## Example

```
script 1 (void)
{
    Print (s: Strftime (SystemTime(), "%B %d %Y", true));
}
```

## See also

`SystemTime` (produces the `timestamp` input) and `GetTimeProperty` (extracts a single calendar
field as an int instead of formatting a string) — related but documented in their own files per
this intake batch's collision guard; not merged into a shared family file here even though the
three are closely related. A future pass may want to consolidate
`SystemTime`/`GetTimeProperty`/`Strftime` into `families/time.md` since none is very useful
without `SystemTime` supplying the timestamp.
