# `int GetAmmoCapacity(str classname)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `GetAmmoCapacity (ACS) - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29, `https://zdoom.org/w/index.php?title=GetAmmoCapacity_%28ACS%29&oldid=49110`) + source-verified against `p_acs.cpp:11814-11841`, `g_shared/a_pickups.h:250` (`AAmmo` field definition + backpack mutation path), `g_shared/a_pickups.cpp:2111-2125` (backpack `MaxAmount` mutation), `zt-bcc/src/builtin.c:131`. Wiki/fork divergence (direct-parent-only `Ammo` check, unheld-ammo fallback to class default, activator-only targeting) and indirection in backpack behavior recorded above rather than silently trusted or omitted. **Not consolidated into a family file with `SetAmmoCapacity`** because the two share the resolution check but diverge materially in the unheld-item behavior (getter returns class default, setter creates the item with `Amount` zeroed); a merged doc would have to caveat nearly every line per-direction.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.

Gets the maximum carry amount of an ammo type on the **activator only**. Compiler builtin
(`PCD_GETAMMOCAPACITY`, the zt-bcc source's `src/builtin.c:131`), implementation in
`DLevelScript::RunScript`'s big switch, the Zandronum source's `src/p_acs.cpp:11814-11841`.

- No `tid`/actor parameter exists at all — this function can only ever query `activator`. **If
  `activator == NULL`** (e.g. called from a script type with no natural activator, or
  `ACS_ExecuteAlways` from a non-actor source), the function returns **`0`** — no error
  (`p_acs.cpp:11839`).
- `classname` — a class name string looked up with `PClass::FindClass`. The check is
  **`type->ParentClass == RUNTIME_CLASS(AAmmo)`** (`p_acs.cpp:11820`) — this requires the class's
  **immediate** parent to be exactly `Ammo`, not merely "somewhere in its ancestry". A class two
  levels deep (e.g. a custom ammo subclassing `ClipAmmo` rather than `Ammo` directly) would fail
  this check and the getter would return `0` rather than the expected value. The wiki's phrasing —
  "Any item from the list Ammo is accepted, as well as derived types from Ammo" — reads as if any
  descendant works; the actual fork behavior is narrower (direct children of `Ammo` only).
  Independently verified against the getter's own source line 11820 (identical check to
  `SetAmmoCapacity`'s line 11849).
- If `classname` doesn't resolve (bad name), or resolves but isn't a direct `Ammo` subclass,
  the function returns **`0`** — no distinction between "not found", "not an ammo type", or "a
  genuine ammo capacity of 0" (the last scenario is theoretically possible if a class's DECORATE
  default `MaxAmount` is set to `0`, though this doesn't occur in the base game).
- **Return behavior differs fundamentally from `SetAmmoCapacity` for unheld ammo:** the getter
  **never returns `0` for a valid ammo class that the activator doesn't currently hold**. Instead,
  it returns the class's DECORATE-defined default `MaxAmount` via `GetDefaultByType(type)`
  (`p_acs.cpp:11829`). This means `GetAmmoCapacity("Clip")` on a player who has never picked up a
  clip returns the Clip class's default `MaxAmount` (200 in stock Doom), not `0`. So unlike the
  setter's activation logic, **this function is not a "does the player hold this ammo" test**.
- **Wiki's backpack behavior is accurate but indirectly achieved:** the wiki states the return is
  "`Inventory.MaxAmount` or, if the player has picked up a backpack, `Ammo.BackpackMaxAmount`."
  This is verified to be correct in spirit but misleading in implementation: the backpack pickup
  itself mutates the ammo's live `MaxAmount` field (not a separate read-path fallback to
  `BackpackMaxAmount`) via `g_shared/a_pickups.cpp:2111-2113` — the getter simply observes the
  mutated value. The distinction matters for implementation clarity (the getter doesn't conditionally
  read `BackpackMaxAmount`, only `MaxAmount`) but doesn't change the observable behavior — after a
  backpack pickup, `MaxAmount` on held items is raised to the backpack cap.

**Example — test whether a player has picked up a backpack (from the wiki, logic verified against
the Zandronum and UZDoom engine forks):**

```text
// Clip's default cap is 200; with backpack it's raised to 400
if (GetAmmoCapacity("Clip") > 200)
{
    // Player has picked up a backpack
}
```
