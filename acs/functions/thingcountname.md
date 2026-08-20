# `int ThingCountName(str classname, int tid)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `ThingCountName - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`https://zdoom.org/w/index.php?title=ThingCountName&oldid=26428`) + source-verified against the Zandronum source (`p_acs.cpp:10526-10529` for the
builtin dispatch, `DLevelScript::ThingCount` at `p_acs.cpp:3894-3988` for the actual counting
logic) and `zt-bcc/src/builtin.c:142,290`. The wiki's dead-monster-exclusion and
tid-zero-means-ignore-tid claims both hold exactly against Zandronum's source. Everything else in
this doc (inventory-ownership exclusion, DECORATE-replacement counting, the two Zandronum-only
`[AK]`/`[RK]` exclusions for hidden actors and spectating players, and the silent-0-on-bad-class-
name failure mode) is this doc's source-verified addition, not present on the wiki page — this is
exactly the kind of fork-specific/deeper-than-wiki behavior the ZDoom-wiki intake caveat in
`../../shared/AUTHORING.md` warns to check for.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin. `ThingCountName(classname, tid)` is sugar for
`ThingCount`'s string-lookup path with `tag` hardcoded to `-1` (no sector-tag filter) — see
`DLevelScript::ThingCount` at `p_acs.cpp:3894-3988`. `ThingCountNameSector` (`PCD_THINGCOUNTNAMESECTOR`,
`p_acs.cpp:10531-10534`) is the same worker with a real `tag` argument instead of `-1`; that's a
separate builtin, not covered here.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Counts live actors of a given DECORATE class name, optionally restricted to a TID. Compiler
builtin (`PCD_THINGCOUNTNAME` in `zt-bcc/src/builtin.c`), implemented at
the Zandronum source's `src/p_acs.cpp:10526-10529`, which just forwards into the shared `ThingCount`
worker:

```cpp
case PCD_THINGCOUNTNAME:
    STACK(2) = ThingCount (-1, STACK(2), STACK(1), -1);
    sp--;
    break;
```

- **Class name resolution can silently return 0, not error.** `stringid` is looked up via
  `FBehavior::StaticLookupString`; if that fails (bad string index), or if `PClass::FindClass
  (type_name)` doesn't find a class, or the class exists but has no `ActorInfo`, `ThingCount`
  returns `0` immediately (`p_acs.cpp:3907-3917`) — a typo'd class name is indistinguishable from
  "zero currently exist," with no log/warning either way.
- **`tid == 0` really does mean "ignore TID, count all of that class,"** confirming the wiki's
  claim: the `tid` parameter only gates which iterator is used
  (`if (tid) { FActorIterator... } else { TThinkerIterator<AActor>... }`, `p_acs.cpp:3924-3975`);
  a `0` takes the `TThinkerIterator` branch, which walks every actor with no TID filtering.
- **Dead monsters are excluded** via `actor->health > 0` in both iterator branches, matching the
  wiki. This applies to *any* class counted this way, not just monsters — `ThingCountName` can
  count non-monster actor classes too (the wiki's monster framing is because that's the common
  use case, not a restriction the engine enforces).
- **Inventory items held by an actor are excluded**: `!actor->IsKindOf(RUNTIME_CLASS(AInventory))
  || static_cast<AInventory *>(actor)->Owner == NULL` — an `AInventory`-derived class sitting on
  the ground counts, but one currently held by a player/monster does not. Not mentioned on the
  wiki page at all.
- **DECORATE replacements are also counted**, via a `goto do_count` retry with
  `kind->GetReplacement()` if it differs from `kind` (`p_acs.cpp:3976-3986`). Counting
  `"DoomImp"` when a mod replaces Imps with a custom actor will include both the original class
  (if any remain) and the replacement class in one call. Not mentioned on the wiki.
- **Two Zandronum-specific exclusions absent from vanilla ZDoom and from the wiki page** (this
  page is a ZDoom wiki page — see intake caveats in `../../shared/AUTHORING.md` — and both of these are
  fork additions per their `// [tag]` comments):
  - `// [AK] Don't count actors hidden by HideOrDestroyIfSafe()` — actors with
    `STFL_HIDDEN_INSTEAD_OF_DESTROYED` set are skipped (`p_acs.cpp:3931-3932, 3957-3958`).
  - `// [RK] Don't count players who left the game by spectating or dead spectators` — a
    `player_t` with `bSpectating` or `bDeadSpectator` is skipped even if it otherwise matches
    (`p_acs.cpp:3934-3936, 3960-3962`). Relevant if counting a player-controlled class (e.g. a
    possession/morph mechanic) in a multiplayer mod — spectators won't inflate the count.
- **`tag` is always `-1` for this builtin** (no sector filter) — the `actor->Sector->tag == tag ||
  tag == -1` check in `ThingCount` always takes the `tag == -1` branch here, so every matching
  actor counts regardless of what sector it's in. Only `ThingCountNameSector` passes a real tag.

**Example** (from the wiki, verified consistent with the source above — a `tid` of `0` counts
every instance of the class map-wide, ignoring TID):

```text
// Map has: Imp(tid 5) x2, Imp(tid 5), Imp(tid 0), Baron(tid 5) x2, Baron(tid 4), Baron(tid 0),
// Demon(tid 5), Demon(tid 4), Demon(tid 0)
ThingCountName("DoomImp", 0)     // 3  (tid 0 == "ignore tid", counts all Imps)
ThingCountName("BaronOfHell", 0) // 4
ThingCountName("Demon", 0)       // 3
ThingCountName("DoomImp", 5)     // 2  (only the two tid-5 Imps)
ThingCountName("Demon", 4)       // 1
ThingCountName("DoomImp", 4)     // 0  (no tid-4 Imps)
```

**Returns:** `int` — count of matching, currently-alive actors. `0` on an unrecognized class name
(no error), not just on a genuine zero count.

**See also:** [`IsTidUsed`](istidused.md) for a cheaper existence-only check; `ThingCount` (by
spawnable-type ID rather than class name string) and `ThingCountNameSector`/`ThingCountSector`
(same worker with a sector-tag filter) share this implementation but aren't documented here.
