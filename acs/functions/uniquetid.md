# `int UniqueTid(int tid = 0, int limit = 0)`

**Tier:** A
**Engine:** Zandronum 3.2.1 (checked against the Zandronum source's master/3.3-alpha checkout; `P_FindUniqueTID` logic is old/stable code, no version-gap concerns found).
**Provenance:** `UniqueTID - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=UniqueTID&oldid=40890`), verified against fork source 2026-07-29.
**Bucket:** extension function.

Finds and returns a TID not currently in use by any actor. Extension function (`ACSF_UniqueTID`,
index `-46` in the zt-bcc source's `lib/zcommon.bcs:1674`), implemented in
`P_FindUniqueTID` (the Zandronum source's `src/p_mobj.cpp:3651-3697`), called from
`p_acs.cpp:6358-6359`. Both arguments are optional (zcommon.bcs signature is
`UniqueTid(;int,int):int` — nothing required before the `;`).

- `tid` (default `0`) — has two entirely different modes, selected by whether it's zero:
  - **Non-zero:** linear search. Starting at `tid`, walks upward one TID at a time until it finds
    one not in use (`P_IsTIDUsed`), and returns the first free one. Note the walk only ever
    increases from the given value — passing a negative `tid` starts the linear scan from that
    negative number and counts upward, which is very unlikely to be what a caller wants (TIDs are
    conventionally positive); nothing in the engine rejects a negative `tid`.
  - **Zero (the default, and what you get from a bare `UniqueTid()` call):** random search. Draws
    a random 32-bit value (`pr_uniquetid.GenRand32() & INT_MAX`, always non-negative) and does a
    small linear probe of 5 TIDs from there; repeats with a new random start until a free TID
    turns up or the attempt budget (see `limit`) is exhausted.
- `limit` (default `0`) — attempt budget, meaning depends on which mode `tid` selected:
  - Linear mode: the maximum number of TIDs to check starting from `tid`. `0` means unlimited
    (search all the way to `INT_MAX`). The engine clamps the internal `limit + tid - 1` addition
    to `INT_MAX` if it would overflow, so a huge `limit` can't wrap around.
  - Random mode: the maximum total number of TIDs probed across all the 5-at-a-time random
    attempts (`0` again means unlimited, effectively `INT_MAX`).
  - **Fork-specific gotcha not in the wiki:** the ACSF dispatch clamps a negative `limit` argument
    to `0` before calling into `P_FindUniqueTID`
    (`(argCount > 1 && args[1] >= 0) ? args[1] : 0`, `p_acs.cpp:6359`) — i.e. **a negative limit
    silently becomes "unlimited," not "zero attempts" or an error.** The wiki doesn't mention this
    because it's describing the generic/positive case only.
- **Return value:** the free TID found (always `> 0` in practice, since `0` is treated as "not a
  real TID" throughout — the loop explicitly requires `tid != 0`), or **`0` if the search
  exhausted its `limit` without finding one.** `0` is therefore both "search still unlimited" (as
  an input) and "search failed" (as an output) — don't confuse the two positions.

## Wiki accuracy

The ZDoom wiki page (`UniqueTID`, function name capitalized differently than this fork's BCS name
`UniqueTid` — ACS/BCS identifiers are case-insensitive so this doesn't matter in practice) matches
this fork's actual behavior closely: both modes, the `limit` semantics, and the `0`-on-failure
return are all confirmed correct against `p_mobj.cpp:3651-3697`. The one gap is the negative-`limit`
clamp-to-unlimited behavior above, which the wiki doesn't cover at all (it only documents
`limit` as "if non-zero" / "if zero", not what a negative value does) — this isn't a wiki error so
much as an undocumented-upstream fork/engine implementation detail.

## Practical note

The wiki's own example (`CameraRocket` script) calls `UniqueTID()` with zero arguments to get a
random TID, immediately reassigns it to an actor with `Thing_ChangeTID`, and clears it again with
`Thing_ChangeTID(MissileID, 0)` once done — TIDs found by this function are not reserved by the
call itself, so nothing stops a race between "find a free TID" and "assign it" if other code runs
in between (e.g. across a `Delay` in the same script, or another script running concurrently).
