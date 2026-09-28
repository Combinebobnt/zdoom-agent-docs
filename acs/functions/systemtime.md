# `int SystemTime()`

**Tier:** A.
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** wiki page `SystemTime - Zandronum Wiki.html` (`_intake/`, retrieved 2026-07-29, `https://wiki.zandronum.com/w/index.php?title=SystemTime&oldid=1339`) + source-verified against `p_acs.cpp:115-179` (CVAR/CCMD), `p_acs.cpp:5791-5797` (`SetCVar` mod-cvar gate), `c_cvars.cpp:195-199` (`CVAR_NOSETBYACS` under `ConsoleCommand`) and `p_acs.cpp:7373-7375` (`ACSF_SystemTime` case). Wiki page is a Zandronum-specific-feature page (confirmed: "This article documents a Zandronum-specific ACS feature") and its description matched the fork source exactly — no discrepancy found. Zandronum-native feature added in commit `f614049b4` ("Added ACS date and time functions SystemTime, GetTimeProperty and Strftime...", 2015-08-30), confirmed via `git merge-base --is-ancestor f614049b4 28f736fb3` (the 3.2.1 version-bump commit) to predate the 3.2.1 target — safe to stamp as verified for 3.2.1, not just the checked-out `3.3-alpha` snapshot.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
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
  the script. In a networked game that is the server for ordinary scripts, and each client's own
  machine for `CLIENTSIDE` scripts. The value is never synced between them.
- **Overridable per machine via the `acstimestamp` CVAR** (`p_acs.cpp:115`,
  `CVAR(Int, acstimestamp, 0, CVAR_ARCHIVE | CVAR_NOSETBYACS)`). If non-zero, `SystemTime()`
  returns this value verbatim instead of the real clock. The cvar has no `CVAR_SERVERINFO`, so a
  server's override doesn't reach clients; a client's own `acstimestamp` drives its `CLIENTSIDE`
  scripts. `CVAR_ARCHIVE` means an override is saved to the ini and survives a restart.
  **ACS itself cannot set or clear this override.** `SetCVar` refuses it because it isn't a mod
  cvar (`p_acs.cpp:5791-5797`), `ConsoleCommand()` can't set a `CVAR_NOSETBYACS` cvar
  (`c_cvars.cpp:195-199`), and the `acstime` command returns early when run from
  `ConsoleCommand()` (`p_acs.cpp:119-120`). Only a human/server operator can set it, either by
  setting `acstimestamp` directly or via the `acstime` console command (`p_acs.cpp:117-179`, a
  `CCMD`, not an ACS-callable function):
  - `acstime` (no args) — prints whether an override is active and what it is.
  - `acstime yyyy-mm-dd [hh:mm]` — sets the override to that local date/time (midnight if time
    omitted), via `mktime()`. The fields are read with `sscanf`'s `%i`, which treats a leading
    `0` as octal, so zero-padded `08`/`09` misparse. A month `08`/`09` fails with "Could not read
    that date.". A day `08`/`09` silently becomes day 0 (the previous month's last day) at hour 8
    or 9. An hour `08`/`09` becomes hour 0 and the minutes are dropped; a minute `08`/`09` becomes 0. Write `2026-9-8 8:30`
    instead.
  - `acstime clear` — clears the override (`acstimestamp = 0`), reverting `SystemTime()` to real
    time.
  - This matches the wiki's "The acstime console command can override the result of this
    function" claim exactly — confirmed by source, not just trusted.
- **Year-2038 problem confirmed real in Zandronum:** the value is stored and returned as ACS's
  32-bit signed `int` (both `acstimestamp` and the cast `(int) time(NULL)`), so it wraps once the
  Unix timestamp exceeds `INT_MAX` (2038-01-19 03:14:07 UTC) — matches the wiki's caveat.
- No documented failure mode — always returns a value (real time or override), never a sentinel
  error value.

**Example — log the current Unix timestamp:**

```text
int now = SystemTime();
Log(s: "Current timestamp: ", i: now);
```

**See also:** `GetTimeProperty` (breaks a timestamp like this one into calendar fields) and
`Strftime` (formats a timestamp into a string) — both take a timestamp of this same shape as
input. (Per this batch's family-collision guard, this file does not create or edit a shared
`families/*.md` — flagging here that `SystemTime`/`GetTimeProperty`/`Strftime` plausibly belong
together as a time-handling family for a future consolidation pass.)

## Engine-family divergence

`SystemTime` is bound as ACSF (CALLFUNC) index 127 — inside the 100–199 range UZDoom's own ACSF
enum reserves for Zandronum's extensions and implements none of (confirmed via
`tools/engine_matrix.py SystemTime`, bin `zandronum-only-silent`). UZDoom's `CallFunction`
dispatcher is a plain `switch` over the ACSF index with `default: break;` falling through to
`return 0` — no error, no log line, execution just continues. A Zandronum-compiled object calling
`SystemTime()` under UZDoom silently gets `0` back in place of the real Unix timestamp. See
[Zandronum/UZDoom compatibility](../concepts/zandronum-uzdoom-compat.md) for the general mechanism
— this function is one of the confirmed instances it names directly.

As an absolute value `0` is not a plausible-looking timestamp — it decodes to 1970-01-01 00:00:00
UTC, decades away from any real wall-clock read, so a script that logs or displays the raw value
is likely to look obviously broken rather than subtly wrong. The more dangerous case is a caller
that only ever consumes *deltas* between two `SystemTime()` calls (a cooldown timer, an elapsed-
time check, a rate limit): both calls return the same `0`, so the delta is exactly `0` every time,
with no error and no out-of-range value to notice. Timing logic that expects the delta to
eventually cross a threshold simply never fires on UZDoom, silently, instead of crashing or
producing a visibly wrong number.
