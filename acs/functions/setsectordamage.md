# `void SetSectorDamage(int tag, int amount [, str damagetype [, int interval [, int leaky]]])`

**Tier:** A
**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master`/`3.3-alpha` checkout; absence in the newer snapshot implies absence in the older 3.2.1 target — see reasoning above).
**Provenance:** `SetSectorDamage - ZDoom Wiki` (`_intake/SetSectorDamage - ZDoom Wiki.html`, retrieved 2026-07-29, `oldid=44305`). Wiki's signature/parameter defaults are recorded above for reference, but the wiki's described *behavior* does not hold in this fork at all — verified absent against fork source (`p_acs.cpp:5360-5500` `EACSFunctions` enum — no `94`/`ACSF_SetSectorDamage` member exists between explicit `ACSF_Warp=92` and `ACSF_GetActorFloorTexture=204`; `p_acs.cpp:9059-9063` default-case fallthrough; `p_acs.cpp:9461-9473` `PCD_CALLFUNC` doing no funcIndex validation before dispatch) and against `zt-bcc` codegen (`zt-bcc/src/parse/dec.c:2453-2493` confirms the leading `-` in `-94:SetSectorDamage(...)` is consumed as a type-selector flag, not baked into the stored `id` — so the emitted `funcIndex` really is the positive literal `94`, matching the engine-side enum numbering exactly). Empirically confirmed compiling: a script calling `SetSectorDamage(1, 5, "Fire", 32, 0);` built to a `.o` via `bcc` with exit code 0 and no diagnostics. Cross-checked working alternatives `Sector_SetDamage` (`p_lnspec.cpp:2459-2473`) and `SectorDamage` (`functions/sectordamage.md`).
**Bucket:** extension function (by declared table position — but see above; there is no engine side to this bucket for this particular function).

**Does not exist in this fork's engine.** Declared in `zt-bcc/lib/zcommon.bcs:1724` as
`-94:SetSectorDamage(int,int;str,int,int):void` — a negatively-indexed extension function
(`ACSF_SetSectorDamage`, funcIndex `94`) — and it compiles cleanly against that table (confirmed
empirically: a test script calling `SetSectorDamage(1, 5, "Fire", 32, 0);` compiled to a `.o` with
`bcc`, exit code 0). But there is no `ACSF_SetSectorDamage` enumerator, and no `case` for funcIndex
`94`, anywhere in the Zandronum source's `src/p_acs.cpp`'s `EACSFunctions` enum or its `CallFunction`
dispatch `switch` (starts `p_acs.cpp:5899`).

## What actually happens at runtime

`PCD_CALLFUNC` (`p_acs.cpp:9461-9473`) does no bounds/validity check on `funcIndex` before calling
`CallFunction(argCount, funcIndex, ...)` — it just pushes whatever the compiler emitted. Inside
`CallFunction`, the enum sequence jumps straight from `ACSF_CanRaiseActor` (84) to an explicit
`ACSF_Warp = 92` (commented `// [BB] Out of order ZDoom backport`), then to an explicit
`ACSF_GetActorFloorTexture = 204`; nothing in this fork's enum has value `93`-`203`, including
`94`. The `switch`'s only fallback is:

```cpp
default:
    break;
```
(`p_acs.cpp:9059-9060`), after which the function returns `0` (`p_acs.cpp:9063`). So calling
`SetSectorDamage(...)` from a script:

- does **not** crash, error, or print any console message,
- does **not** call `P_SectorDamage`, `Sector_SetDamage`, or touch `sector_t::damage`/`mod` in any
  way,
- silently returns `0` (discarded anyway, since the BCS signature declares `void`),
- and the script continues executing on the very next instruction as if the call were a no-op.

This is a genuine gap, not a version-sensitivity question: the enum gap (`93`-`203` unused except
for the two explicit "out of order backport" values) exists identically in the checked-out
`3.3-alpha` snapshot, and 3.3-alpha is *ahead of* 3.2.1 — a function absent in the newer checkout
cannot have been present in the older 3.2.1 target either, so no git-ancestry check is needed here
(contrast with a function that's *present* in 3.3-alpha but might postdate 3.2.1, which would need
one).

## Working alternatives in this fork

- **`Sector_SetDamage(tag, amount, mod)`** — action special, positive index `214`
  (`zcommon.bcs:1553`), real and implemented: `FUNC(LS_Sector_SetDamage)` (`p_lnspec.cpp:2459-2473`)
  loops every sector matching `tag` and sets `sectors[secnum].damage`/`.mod` directly — i.e. it
  genuinely does set a **persistent** per-sector damage property, which is what `SetSectorDamage`'s
  name and wiki description promise. The catch: `mod` is the old integer damage-type-number format
  (not a string `damagetype`), and there is no `interval`/`leaky` control at all — those two
  knobs from the wiki page have no equivalent anywhere in this fork.
- **`SectorDamage(tag, amount, type, protection_item, flags)`** — compiler builtin
  (`PCD_SECTORDAMAGE`), documented separately at [SectorDamage](sectordamage.md). Different
  shape: a one-shot, call-triggered damage pulse (with full string damage-type and protection-item
  support), not a persistent property setter — it has to be looped by the calling script to
  simulate recurring damage, and doesn't touch `sector_t::damage`/`.mod` at all.

Neither alternative reproduces `SetSectorDamage`'s exact contract (persistent + string damage type
+ configurable interval + leaky-suit probability); `Sector_SetDamage` is persistent but loses the
string type and both timing knobs, `SectorDamage` keeps the string type but is one-shot, not
persistent.

## Parameters (as declared — none of this is exercised by the engine)

- `tag` — sector tag, per the wiki.
- `amount` — damage amount, per the wiki.
- `damagetype` — default `"None"` per the wiki; would need to be an `FName`-lookup damage type if
  it worked at all, matching `SectorDamage`'s `type` param.
- `interval` — tics between damage applications, default `32` per the wiki; no fork equivalent
  (`Sector_SetDamage` has no interval concept, and the sector damage tic-cadence is otherwise
  handled by the base `P_PlayerInSpecialSector` path, not by anything this function would set).
- `leaky` — radiation-suit leak probability (`0`-`256`), default `0` per the wiki; no fork
  equivalent either.

## Not to be confused with

`SectorDamage` (this fork's real, working, differently-shaped compiler builtin) — see its doc's
"Relationship to SetSectorDamage" section, which independently reached the same absence conclusion
via a slightly different trace (checking for a `case ACSF_SetSectorDamage:` by name) before this
file traced the actual funcIndex-94 dispatch path and confirmed the compile-then-no-op behavior
empirically.
