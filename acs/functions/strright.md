# `StrRight`

**Bucket:** Extension function (`zcommon.bcs`: `-66:StrRight(str,int):str`) — `ACSF_StrRight` in
the Zandronum source's `src/p_acs.cpp`'s `EACSFunctions` enum (declared right after `ACSF_StrLeft`,
which shares the identical `case` block).

**Tier:** A. **Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD —
see "Engine scope" in `../../shared/AUTHORING.md`).

**Provenance:** `StrRight - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=StrRight&oldid=37593`), verified against
the Zandronum source's `src/p_acs.cpp:6640-6659` (`case ACSF_StrLeft: case ACSF_StrRight:`) on
2026-07-29.

## Signature

```
str StrRight(str string, int length);
```

Both parameters are mandatory in this fork's `zcommon.bcs` declaration — there is no
zero-argument or one-argument overload to worry about.

## Behavior

`StrRight` and `StrLeft` (index `-65`) are the *literal same* engine `case` block — the only
branch between them is a single ternary picking which end of the string to slice
(`funcIndex == ACSF_StrLeft ? oldstr : oldstr + oldlen - newlen`, `p_acs.cpp:6656`). Every
edge-case in the shared clamp/lookup logic applies identically to both:

- **Invalid or null string handle** (`FBehavior::StaticLookupString` returns `NULL`) **or an
  already-empty string** → returns a freshly-interned empty string (`""`), matching the wiki's
  "If string does not exist, an empty string is returned."
- **`length >= string length`** → returns the entire string unchanged, matching the wiki's
  "If string is shorter than length characters, the entire string is returned." (Implemented as
  `oldlen < newlen` clamping `newlen` down to `oldlen`; when this clamp fires, `StrRight`'s
  `oldstr + oldlen - newlen` collapses to `oldstr + 0`, i.e. the same full string `StrLeft` would
  return — both functions become indistinguishable from plain string-copy in this case.)
- **`length` negative — undocumented on the wiki, and not a safe no-op or error.** The engine reads
  `length` into a `size_t` (`size_t newlen = args[1];`) with no sign check first. `args[]` is a
  signed 32-bit `SDWORD`, so a negative `length` sign-extends and then gets reinterpreted as a huge
  unsigned value on the assignment to `size_t`. That huge value immediately trips the
  "`oldlen < newlen`" shorter-than-requested clamp, so `newlen` collapses back down to `oldlen` —
  in practice, **any negative `length` behaves exactly like "return the whole string,"** the same
  as passing a `length` larger than the string. It is not treated as "0 characters" and does not
  error.
- **`length == 0`** → returns `""` (the normal, non-clamped path: `oldlen < 0` is false since
  `oldlen` is unsigned and the string is non-empty, so `newlen` stays `0`; `oldstr + oldlen - 0`
  points at the string's own terminating NUL, and an `FString` of length 0 from that pointer is
  empty).

No other wiki/fork divergence found beyond the above — the wiki's stated signature and the two
documented clamp behaviors (empty-on-missing-string, full-string-on-too-long) are otherwise
accurate for this fork.

## See also

[`StrLeft`](strleft.md) — the mirror-image function sharing this exact `case` block; anything
verified here about the shared clamp/negative-length/lookup behavior is mechanically true of
`StrLeft` too, and vice versa. [`StrMid`](https://zdoom.org/wiki/StrMid) is a related but
separately-implemented `case` block, not covered here. A future `families/*.md` consolidating
`StrLeft`/`StrRight`/`StrMid`/`StrCpy`/`StrParam` would be reasonable — see this file's final
report for that recommendation; no family file was created here per this batch's instructions.

**Note for the coordinator:** `functions/strleft.md` (written by a sibling agent in this same
batch) already documents `StrRight`'s behavior inline and states "`StrRight` — not written up
separately". This file now exists anyway per this task's explicit instructions. The two files'
descriptions of the shared `case` block are consistent with each other (same clamp/negative-length
findings), but `strleft.md`'s closing note claiming StrRight has no separate writeup is now stale
and should be reconciled (either drop that line from `strleft.md`, or fold both into a
`families/string-slicing.md` and delete the redundant per-function detail) — left to whoever
integrates `INDEX.md`.
