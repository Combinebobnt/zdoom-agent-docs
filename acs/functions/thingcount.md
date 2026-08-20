# `int ThingCount(int type, int tid)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `ThingCount - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`https://zdoom.org/w/index.php?title=ThingCount&oldid=35771`) + source-verified against the Zandronum source (`p_acs.cpp:3894-3988`,
`:10516-10522`, `P_GetSpawnableType` at `p_things.cpp:624`) and `zt-bcc/src/builtin.c:38,186`.
The wiki's type/TID/health-based semantics all hold exactly; the hidden-actor, spectator, and
inventory-ownership exclusions are this doc's source-verified additions (not mentioned on the wiki
page), consistent with this being a ZDoom-wiki page describing an upstream ZDoom function that the
fork has since extended for multiplayer.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.

Counts live actors matching a spawn-number type and/or a TID. Compiler builtin (`PCD_THINGCOUNT`
/ `PCD_THINGCOUNTDIRECT` in `zt-bcc/src/builtin.c`), implemented by `DLevelScript::ThingCount` at
the Zandronum source's `src/p_acs.cpp:3894-3988`, dispatched from `p_acs.cpp:10516-10522`.

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

## Zandronum-specific: exclusions not on the ZDoom wiki page

This page (`ThingCount - ZDoom Wiki.html`, upstream ZDoom) describes only the type/TID/health
semantics above. Reading the fork's actual loop body turned up three more exclusions, all applied
unconditionally regardless of `type`/`tid`, none mentioned on the wiki:

- **Actors hidden via `HideOrDestroyIfSafe()`** (`STFL_HIDDEN_INSTEAD_OF_DESTROYED` flag) are
  skipped — comment-tagged `[AK]` in the source, i.e. a Zandronum-side addition over base ZDoom.
- **Spectating or dead-spectator players are skipped** — comment-tagged `[RK]`. Multiplayer-only
  and Zandronum-specific: a player actor that would otherwise match `type`/`tid` (e.g. counting
  `T_NONE` against a TID assigned to players) is excluded while spectating.
- **Items currently sitting in another actor's inventory are skipped** — checked via
  `IsKindOf(RUNTIME_CLASS(AInventory))` and `Owner == NULL`. Not fork-tagged in the comments;
  UZDoom-verified as shared ZDoom-family behavior, not Zandronum-specific (see the
  engine-family-divergence note below) — absent from this wiki page's description regardless, so
  recorded here since it changes counts for inventory-item spawn numbers.

None of these contradict the wiki's examples (which only use monsters, never touch multiplayer
spectating or inventory items), but they mean a mod counting players or pickups by TID/type will
see lower numbers than the wiki's simple model predicts.

**UZDoom comparison** (confirmed against `DLevelScript::ThingCount`,
`src/playsim/p_acs.cpp:3638-3717`): the core wiki-documented semantics above (type/tid/health gate,
transitive replacement re-count, `stringid`/`tag` dispatch) hold identically on UZDoom. Of the
three exclusions in this list, the hidden-actor skip and the spectator/dead-spectator skip have no
equivalent in UZDoom's `ThingCount` — confirmed Zandronum-only, consistent with their `[AK]`/`[RK]`
tags above. The inventory-ownership skip does carry over: UZDoom applies it via
`AActor::IsMapActor()` (`src/playsim/p_mobj.cpp:814-818`), `!IsKindOf(NAME_Inventory) || Owner ==
nullptr` — the same condition as Zandronum's inline check, just factored into a shared helper.

**Returns:** `int` — the number of matching, currently-alive, non-hidden, non-spectating,
not-in-inventory actors. `0` if `type` doesn't resolve to a spawnable class.

**See also:** [`functions/istidused.md`](istidused.md) — cheaper existence-only check when you
don't need an exact count and don't care whether the actor is alive.
