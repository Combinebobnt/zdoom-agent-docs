# `int ThingCount(int type, int tid)`

Counts live actors matching a spawn-number type and/or a TID. Compiler builtin (`PCD_THINGCOUNT`
/ `PCD_THINGCOUNTDIRECT` in `zt-bcc/src/builtin.c`), implemented by `DLevelScript::ThingCount` at
the Zandronum source's `src/p_acs.cpp:3894-3988`, dispatched from `p_acs.cpp:10516-10522`.

**Bucket:** compiler builtin.

- **`type`** — a DECORATE spawn number (`P_GetSpawnableType`), e.g. `T_IMP`. If `type == 0`
  (`T_NONE`), the type filter is dropped entirely (`kind = NULL`) and every actor holding `tid` is
  counted regardless of class — this is the wiki's documented behavior and it holds. If `type` is
  positive but not a registered spawn number, `P_GetSpawnableType` returns `NULL` and the function
  returns `0` immediately, without iterating anything.
- **`tid`** — if nonzero, iterates only actors with that TID (`FActorIterator`); if `0`, iterates
  every actor on the map (`TThinkerIterator<AActor>`) and filters by `type` instead — also matches
  the wiki.
- **Dead monsters are never counted** — every candidate must have `actor->health > 0`. Confirmed
  at `p_acs.cpp:3929` and `:3955`. This is the same `health > 0` gate that `functions/istidused.md`
  contrasts itself against (`IsTidUsed` has no such check).
- **Decorate replacements are counted transitively** — after the first pass, if
  `kind->GetReplacement()` differs from `kind`, the function re-runs the entire count
  (`goto do_count`) with the replacement class substituted in. In practice this means a spawn
  number whose actor has a DECORATE `replaces` in effect gets counted under the replacement, not
  silently dropped.
- **The underlying C++ function takes two more parameters the base `ThingCount` PCD never
  exposes**: `stringid` (a string-table index, used by `ThingCountName` for actors with no spawn
  ID) and `tag` (a sector tag, used by `ThingCountSector`/`ThingCountNameSector`). `PCD_THINGCOUNT`
  always calls it with `stringid = -1, tag = -1` — i.e. base `ThingCount` never filters by sector.

## Zandronum-specific exclusions not on the ZDoom wiki page

This page (`ThingCount - ZDoom Wiki.html`, upstream ZDoom) describes only the type/TID/health
semantics above. Reading the fork's actual loop body turned up three more exclusions, all applied
unconditionally regardless of `type`/`tid`, none mentioned on the wiki:

- **Actors hidden via `HideOrDestroyIfSafe()`** (`STFL_HIDDEN_INSTEAD_OF_DESTROYED` flag) are
  skipped — comment-tagged `[AK]` in the source, i.e. a Zandronum-side addition over base ZDoom.
- **Spectating or dead-spectator players are skipped** — comment-tagged `[RK]`. Multiplayer-only
  and Zandronum-specific: a player actor that would otherwise match `type`/`tid` (e.g. counting
  `T_NONE` against a TID assigned to players) is excluded while spectating.
- **Items currently sitting in another actor's inventory are skipped** — checked via
  `IsKindOf(RUNTIME_CLASS(AInventory))` and `Owner == NULL`. Not fork-tagged in the comments (may
  be shared with upstream ZDoom), but absent from this wiki page's description, so recorded here
  since it changes counts for inventory-item spawn numbers.

None of these contradict the wiki's examples (which only use monsters, never touch multiplayer
spectating or inventory items), but they mean a mod counting players or pickups by TID/type will
see lower numbers than the wiki's simple model predicts.

**Returns:** `int` — the number of matching, currently-alive, non-hidden, non-spectating,
not-in-inventory actors. `0` if `type` doesn't resolve to a spawnable class.

**See also:** [`functions/istidused.md`](istidused.md) — cheaper existence-only check when you
don't need an exact count and don't care whether the actor is alive.

**Provenance:** wiki page `ThingCount - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`oldid=35771`) + source-verified against the Zandronum source (`p_acs.cpp:3894-3988`,
`:10516-10522`, `P_GetSpawnableType` at `p_things.cpp:624`) and `zt-bcc/src/builtin.c:38,186`.
The wiki's type/TID/health-based semantics all hold exactly; the hidden-actor, spectator, and
inventory-ownership exclusions are this doc's source-verified additions (not mentioned on the wiki
page), consistent with this being a ZDoom-wiki page describing an upstream ZDoom function that the
fork has since extended for multiplayer. **Engine:** Zandronum 3.2.1 (verified against
the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.
