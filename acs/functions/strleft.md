# `StrLeft`

**Bucket:** Extension function (`zcommon.bcs`: `-65:StrLeft(str,int):str`) — `ACSF_StrLeft` in
the Zandronum source's `src/p_acs.cpp`'s `EACSFunctions` enum (declared right before `ACSF_StrRight`,
which shares the identical `case` block).

**Tier:** A. **Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD —
see "Engine scope" in `../../shared/AUTHORING.md`).

**Provenance:** `StrLeft - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=StrLeft&oldid=37592`), verified against
the Zandronum source's `src/p_acs.cpp:6640-6659` (`case ACSF_StrLeft: case ACSF_StrRight:`) on
2026-07-29.

## Signature

```
str StrLeft(str string, int length);
```

Both parameters are mandatory in this fork's `zcommon.bcs` declaration — there is no
zero-argument or one-argument overload to worry about.

## Behavior

`StrLeft` and `StrRight` are the *same* engine `case` block (`funcIndex == ACSF_StrLeft ?  ... :
...` is the only branch between them) — whatever is true of one's edge-case handling is
mechanically true of the other's:

- **Invalid or null string handle** (`FBehavior::StaticLookupString` returns `NULL`) **or an
  already-empty string** → returns a freshly-interned empty string (`""`), matching the wiki's
  "If string does not exist, an empty string is returned."
- **`length >= string length`** → returns the entire string unchanged, matching the wiki's
  "If string is shorter than length characters, the entire string is returned." (Implemented as
  `oldlen < newlen` clamping `newlen` down to `oldlen`.)
- **`length` negative — undocumented on the wiki, and not a safe no-op or error.** The engine reads
  `length` into a `size_t` (`size_t newlen = args[1];`) with no sign check first. `args[]` is a
  signed 32-bit `SDWORD`, so a negative `length` sign-extends and then gets reinterpreted as a huge
  unsigned value on the assignment to `size_t`. That huge value immediately trips the
  "`oldlen < newlen`" shorter-than-requested clamp, so `newlen` collapses back down to `oldlen` —
  in practice, **any negative `length` behaves exactly like "return the whole string,"** the same
  as passing a `length` larger than the string. It is not treated as "0 characters" and does not
  error.
- **`length == 0`** → returns `""` (the normal, non-clamped path: `oldlen < 0` is false since
  `oldlen` is unsigned and the string is non-empty, so `newlen` stays `0`).

## See also

[`StrRight`](strright.md) — the literal same `case` block as `StrLeft`, with the substring
anchored at the other end (`oldstr + oldlen - newlen` instead of `oldstr`) and the identical
negative-`length` quirk above. [`StrMid`](strmid.md) is a related but separate extension
function. A future `families/*.md` consolidating `StrLeft`/`StrRight`/`StrMid`/`StrCpy`/
`StrParam` would be reasonable, but per this batch's instructions no family file was created
here — see the final report for that recommendation.
