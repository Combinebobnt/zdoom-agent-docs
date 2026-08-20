# `str StrMid(str string, int start, int length)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `StrMid - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`https://zdoom.org/w/index.php?title=StrMid&oldid=37594`) + source-verified against `p_acs.cpp:6661-6683` (`ACSF_StrMid` case) and
`zt-bcc/lib/zcommon.bcs:1696` (index `-67`) on 2026-07-29.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (negative index → `ACSF_StrMid` in `p_acs.cpp`).

Extension function `ACSF_StrMid`, index `-67` in the zt-bcc source's `lib/zcommon.bcs:1696` (listed
as `StrMid(str,int,int):str`). Implementation in the Zandronum source's `src/p_acs.cpp:6661-6683`.

- `string` — the source string.
- `start` — position of the first character of the returned substring.
- `length` — how many characters to return.
- Return value: a new string, `length` characters of `string` starting at `start`. Matches the
  wiki's description for the well-formed/in-range case, and the two documented edge cases also
  check out against the fork's source:
  - **`string` doesn't exist or is empty** (`FBehavior::StaticLookupString` returns `NULL`, or the
    resolved string's first character is `'\0'`) → returns `""` immediately, before `start`/
    `length` are even inspected (`p_acs.cpp:6664-6668`).
  - **`start >= strlen(string)`** → returns `""` (`p_acs.cpp:6673-6676`). This is how the wiki's
    "string is shorter than start characters" case is actually implemented — there's no separate
    length check, just `pos >= oldlen`.
  - **`start + length` overruns the string** → `length` is silently clamped to
    `strlen(string) - start`, returning everything from `start` to the end of the string
    (`p_acs.cpp:6677-6680`). Matches the wiki's "entire substring beginning at start is returned."

- **Not on the wiki: negative `start`/`length` don't error, they wrap via unsigned arithmetic, and
  the two arguments wrap into *different* observable behaviors.** Both `start` and `length` are
  read out of the signed ACS `int` args into `size_t pos`/`size_t newlen` (`p_acs.cpp:6670-6671`)
  — plain narrowing/reinterpretation of a negative `int` as a huge unsigned value, no range check
  or error path for either:
  - A **negative `start`** becomes a huge `pos`, which is always `>= oldlen` (no real string is
    that long), so it hits the "empty string" return path above — same outward result as `start`
    being too large, just for the opposite reason.
  - A **negative `length`** becomes a huge `newlen`. This does *not* hit the same "too long, clamp
    to remainder" branch through the obvious `pos + newlen > oldlen` comparison — `pos + newlen`
    is itself `size_t` arithmetic and overflows/wraps back down when `newlen` is astronomically
    large, which would make the naive `>` comparison **miss** the overrun. The fork's code
    accounts for this with a second condition, `pos + newlen < pos` (`p_acs.cpp:6677`, the
    standard unsigned-overflow-detection idiom: if the sum wrapped below one of its own operands,
    it overflowed) — so the overflow case is still caught and still clamps `newlen` to
    `oldlen - pos`. Net effect: a negative `length` behaves exactly like a `length` large enough to
    reach the end of the string, i.e. "give me the rest of `string` from `start`" — not an error,
    not an empty string, and not the same code path as the negative-`start` case above. Neither
    behavior is mentioned on the wiki, and conflating them (assuming any negative argument just
    produces `""`) would be a plausible but wrong guess from the wiki text alone.

No divergence found in the core three cases the wiki documents; the gap is entirely in the
unsigned-wraparound behavior of negative arguments, which the wiki is silent on.

## See also

[`StrLeft`](https://zdoom.org/wiki/StrLeft)/[`StrRight`](https://zdoom.org/wiki/StrRight) share
the same `oldstr == NULL || *oldstr == '\0'` empty-string short-circuit and the same
length-clamping pattern one case above `ACSF_StrMid` in the same switch
(`p_acs.cpp:6640-6659`) — not documented here since they're being processed as separate intake
files in this batch.
