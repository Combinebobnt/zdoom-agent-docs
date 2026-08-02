# `int GetTimeProperty(int timestamp, int which [, bool utc])`

**Tier:** A.
**Engine:** Zandronum 3.2.1 (confirmed predates the 3.2.1 version-bump commit).
**Provenance:** wiki page `GetTimeProperty - Zandronum Wiki.html` (`_intake/`, retrieved 2026-07-29, `oldid=1775`) + source-verified against `p_acs.cpp:7378-7401`, `zt-bcc/lib/zcommon.bcs:1219-1227,1761`, and version-gated against `f614049b4`/`28f736fb3` per shared/AUTHORING.md's "Engine scope" section.
**Bucket:** extension function.

Localizes a Unix timestamp (as returned by `SystemTime()`) into calendar/clock fields and returns
one requested field. Extension function (`ACSF_GetTimeProperty`, index `-128` in
the zt-bcc source's `lib/zcommon.bcs:1761`), implementation in `DLevelScript::CallFunction`'s
`case ACSF_GetTimeProperty:` (the Zandronum source's `src/p_acs.cpp:7378-7401`).

Added together with `SystemTime`/`Strftime` in commit `f614049b4` ("Added ACS date and time
functions SystemTime, GetTimeProperty and Strftime...", 2015-08-30), which is an ancestor of the
3.2.1 version-bump commit `28f736fb3` (confirmed via `git merge-base --is-ancestor
f614049b4 28f736fb3`, verified true) — so this function predates and is present in Zandronum
3.2.1, not a post-3.2.1 addition from the `master`/`3.3-alpha` checkout.

## Parameters

- `timestamp` — a Unix timestamp (seconds since epoch), typically from `SystemTime()` or a
  stored/previously-fetched value. Internally cast straight to `time_t` (`p_acs.cpp:7392`,
  `time_t timer = args[0];`) with no clamping — unlike `Strftime`, which clamps a negative
  timestamp to `0` before use (`p_acs.cpp:7413-7414`). `GetTimeProperty` has no such clamp, so a
  negative `timestamp` is passed straight to `localtime`/`gmtime` and its result depends on the
  C library's handling of pre-epoch times.
- `which` — one of the `TM_*` constants below, selecting which calendar field to return. Any
  value outside the six documented cases silently falls through to `return 0;`
  (`p_acs.cpp:7401`) — indistinguishable from a genuinely-zero field (e.g. `TM_SECOND` at
  `:00`, or `TM_MONTH` in January).
- `utc` — optional (`argCount >= 3 ? !!args[2] : false`, `p_acs.cpp:7393`), defaults to `false`.
  `false`/omitted uses `localtime` (the **server or client machine's local timezone**), `true`
  uses `gmtime` (UTC). This is a real clientside/netcode caveat: if this is evaluated on both
  server and clients (e.g. a `CLIENTSIDE` script) with `utc` false, machines in different
  timezones will localize the same `timestamp` to different wall-clock fields — pass `utc: true`
  for anything that must agree across machines.

### `TM_*` constants (the zt-bcc source's `lib/zcommon.bcs:1219-1227`, matches the engine's local
`enum` at `p_acs.cpp:7380-7388` field-for-field)

| Constant | Value | Engine field | Range |
|---|---|---|---|
| `TM_SECOND` | 0 | `tm_sec` | 0-59 (rarely 60/61 on a leap second, per libc) |
| `TM_MINUTE` | 1 | `tm_min` | 0-59 |
| `TM_HOUR` | 2 | `tm_hour` | 0-23 |
| `TM_DAY` | 3 | `tm_mday` | 1-31 |
| `TM_MONTH` | 4 | `tm_mon` | 0-11 (0 = January) |
| `TM_YEAR` | 5 | `1900 + tm_year` (`p_acs.cpp:7398`) | full 4-digit year, already offset — do not add 1900 yourself |
| `TM_WEEKDAY` | 6 | `tm_wday` | 0-6 (0 = Sunday) |

The wiki's stated `TM_YEAR` range of `[1901, 2038]` is just the practical range for a 32-bit
signed Unix timestamp (the "year 2038 problem" also called out on the wiki page), not a hard
limit enforced by this function — it is exactly `1900 + tm_year` with no clamping.

## Return value

The requested calendar field as a plain `int` (not fixed-point). Returns `0` if `which` doesn't
match any `TM_*` case — same caveat as `GetActorProperty`'s unmatched-property fallthrough:
indistinguishable from a real zero value.

## Example

```
script 1 OPEN
{
    if (GetTimeProperty(SystemTime(), TM_WEEKDAY) == 4 && GetTimeProperty(SystemTime(), TM_DAY) == 20)
        PrintBold(s:"Happy Thursday the 20th!");
}
```

## See also

`SystemTime` (produces the `timestamp` input) and `Strftime` (formats a timestamp as a string
instead of extracting one field) — related but documented in their own files per this intake
batch's collision guard; not merged into a shared family file here even though the three are
closely related. A future pass may want to consolidate `SystemTime`/`GetTimeProperty`/`Strftime`
into `families/time.md` since none is very useful without `SystemTime` supplying the timestamp.
