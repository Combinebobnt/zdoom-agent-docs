# `int SystemTime()`

**Tier:** A.
**Engine:** Zandronum 3.2.1.
**Provenance:** wiki page `SystemTime - Zandronum Wiki.html` (`_intake/`, retrieved 2026-07-29, `oldid=1339`) + source-verified against `p_acs.cpp:115-176` (CVAR/CCMD) and `p_acs.cpp:7373-7375` (`ACSF_SystemTime` case). Wiki page is a Zandronum-specific-feature page (confirmed: "This article documents a Zandronum-specific ACS feature") and its description matched the fork source exactly — no discrepancy found. Zandronum-native feature added in commit `f614049b4` ("Added ACS date and time functions SystemTime, GetTimeProperty and Strftime...", 2015-08-30), confirmed via `git merge-base --is-ancestor f614049b4 28f736fb3` (the 3.2.1 version-bump commit) to predate the 3.2.1 target — safe to stamp as verified for 3.2.1, not just the checked-out `3.3-alpha` snapshot.
**Bucket:** extension function.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Returns the current time as a Unix timestamp (seconds since 1970-01-01 UTC), as a plain ACS
`int`. Extension function (`ACSF_SystemTime`, index -127 in the zt-bcc source's `lib/zcommon.bcs:1760`),
implementation in `p_acs.cpp:7373-7375`:

```cpp
// [TP] Returns system time unless user decides that system time means something else
case ACSF_SystemTime:
	return acstimestamp != 0 ? acstimestamp : (int) time( NULL );
```

- Takes no arguments.
- Normally returns `(int) time(NULL)` — the real wall-clock system time of the machine running
  the script (the server, in a networked game; see below).
- **Overridable per-server via the `acstimestamp` CVAR** (`p_acs.cpp:115`,
  `CVAR(Int, acstimestamp, 0, CVAR_ARCHIVE | CVAR_NOSETBYACS)`). If non-zero, `SystemTime()`
  returns this value verbatim instead of the real clock. `CVAR_NOSETBYACS` means **ACS itself
  cannot set or clear this override** — only a human/server operator can, via the `acstime`
  console command (`p_acs.cpp:117-176`, a `CCMD`, not an ACS-callable function):
  - `acstime` (no args) — prints whether an override is active and what it is.
  - `acstime yyyy-mm-dd [hh:mm]` — sets the override to that local date/time (midnight if time
    omitted), via `mktime()`.
  - `acstime clear` — clears the override (`acstimestamp = 0`), reverting `SystemTime()` to real
    time.
  - This matches the wiki's "The acstime console command can override the result of this
    function" claim exactly — confirmed by source, not just trusted.
- **Year-2038 problem confirmed real in this fork:** the value is stored and returned as ACS's
  32-bit signed `int` (both `acstimestamp` and the cast `(int) time(NULL)`), so it wraps once the
  Unix timestamp exceeds `INT_MAX` (2038-01-19 03:14:07 UTC) — matches the wiki's caveat.
- No documented failure mode — always returns a value (real time or override), never a sentinel
  error value.

**Example — log the current Unix timestamp:**

```
int now = SystemTime();
Log(s: "Current timestamp: ", i: now);
```

**See also:** `GetTimeProperty` (breaks a timestamp like this one into calendar fields) and
`Strftime` (formats a timestamp into a string) — both take a timestamp of this same shape as
input. (Per this batch's family-collision guard, this file does not create or edit a shared
`families/*.md` — flagging here that `SystemTime`/`GetTimeProperty`/`Strftime` plausibly belong
together as a time-handling family for a future consolidation pass.)
