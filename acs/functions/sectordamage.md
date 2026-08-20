# `void SectorDamage(int tag, int amount, str type, str protection_item, int flags)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `SectorDamage - ZDoom Wiki` (`_intake/SectorDamage - ZDoom Wiki.html`, retrieved 2026-07-29, `https://zdoom.org/w/index.php?title=SectorDamage&oldid=45035`), verified against fork source (`p_acs.cpp:12703-12715`, `p_spec.cpp:714-783`, `p_spec.h:162-165`, `zt-bcc/src/builtin.c:147,295`, `zt-bcc/lib/zcommon.bcs:379-383`). The wiki's signature, parameter semantics, empty-string protection-item behavior, and the "must set PLAYERS/NONPLAYERS" warning all check out. `DAMAGE_NO_ARMOR` does not — see divergence section above.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.

Applies a single, immediate damage pulse to actors currently inside the tagged sector(s) —
fires once per call, not a recurring per-tic effect. Compiler builtin (`zt-bcc/src/builtin.c`
`g_funcs[]` entry `{ "sectordamage", ";iissi" }`, opcode `PCD_SECTORDAMAGE`
(`builtin.c:147,295`)), dispatched in the Zandronum source's `src/p_acs.cpp`, `case
PCD_SECTORDAMAGE:` (line 12703), which unpacks the 5 stack args and calls `P_SectorDamage`
(the Zandronum source's `src/p_spec.cpp:737`), which in turn calls the static helper
`DoSectorDamage` (`p_spec.cpp:714`) once per qualifying actor.

Not to be confused with **`SetSectorDamage`** (`functions/setsectordamage.md`), a separate,
negatively-indexed extension function (`ACSF_SetSectorDamage`, `zcommon.bcs:1724`) that — per the
name — sounds like it configures a sector's *persistent* damage property (the MAPINFO-style
"this sector damages anyone standing in it every N tics" behavior), as opposed to this function's
one-shot, call-triggered pulse. See the "Relationship to SetSectorDamage" note at the bottom —
Zandronum does not actually implement `SetSectorDamage` at all, which is worth knowing before
relying on the pair as a getter/setter-style family.

## Parameters

- `tag` — sector tag to affect; resolved via the standard `P_FindSectorFromTag` tag-chain walk
  (`p_spec.cpp:739`), so it matches every sector with that tag, not just one.
- `amount` — flat damage amount passed straight through to `P_DamageMobj` (no scaling).
- `type` — damage type name (`FName`, looked up via `FBehavior::StaticLookupString`); either a
  builtin ZDoom/Zandronum damage type (`"Fire"`, `"Normal"`, etc.) or any custom type defined on a
  `DECORATE`/`ZScript` damage-type actor. No validation against a known-types list — an unknown
  string just becomes an `FName` with no special resistance/vulnerability behavior tied to it.
- `protection_item` — inventory item class name; an actor carrying it is immune. Passing `""`
  (empty string) means "no protection item" — confirmed in source: the lookup uses
  `FName(text, /*noCreate=*/true)` (`p_acs.cpp:12708`), which for an empty string that isn't
  already a registered class name resolves to `NAME_None`, and `PClass::FindClass(NAME_None)`
  yields `NULL`, so the protection check is skipped entirely. This matches the wiki's description.
- `flags` — bitmask, see below. **At least one of `DAMAGE_PLAYERS`/`DAMAGE_NONPLAYERS` must be
  set or nothing is damaged** — confirmed directly in `DoSectorDamage`'s early-out gating
  (`p_spec.cpp:730-732`), matching the wiki's own warning.

## Flags (`p_spec.h:162-165`, mirrored in `zt-bcc/lib/zcommon.bcs:379-383`)

| Flag | Value | Effect |
|---|---|---|
| `DAMAGE_PLAYERS` | `0x1` | Players in the sector take damage. |
| `DAMAGE_NONPLAYERS` | `0x2` | Shootable non-player actors (`MF_SHOOTABLE`) in the sector take damage. |
| `DAMAGE_IN_AIR` | `0x4` | Without this, an actor is only damaged if it's touching the sector floor or has nonzero `waterlevel` (`p_spec.cpp:723`) — i.e. "on the ground or in the water," per the wiki. With it, height/water is not checked at all. |
| `DAMAGE_SUBCLASSES_PROTECT` | `0x8` | Changes the protection check from "must carry that exact class" to "carries that class *or any subclass of it*" (`actor->FindInventory(protectClass, subclassesProtect)`, `p_spec.cpp:727`). |

**Divergence — `DAMAGE_NO_ARMOR` is broken/nonexistent in Zandronum, contrary to the wiki:**

1. **Not defined in the engine at all.** `p_spec.h:162-165` only defines the four flags above;
   there is no `DAMAGE_NO_ARMOR` constant anywhere in the Zandronum source's `src`.
2. **Not checked by the damage logic either way.** `DoSectorDamage` unconditionally calls
   `P_DamageMobj(actor, NULL, NULL, amount, type)` (`p_spec.cpp:731`) with the damage-flags
   argument omitted (defaults to `0`) — the engine's actual armor-bypass bit, `DMG_NO_ARMOR`
   (`p_local.h:600`, used by `P_DamageMobj`'s own flags parameter), is never set from here. So
   even if a caller could pass some bit through, nothing downstream would act on it — armor
   absorption always applies normally for `SectorDamage`, full stop.
3. **zt-bcc's own constant is malformed on top of that.** `zcommon.bcs:383` defines
   `DAMAGE_NO_ARMOR = 0x16` — decimal 22, i.e. `0b10110`, not a clean single bit. OR'ing it into
   `flags` doesn't just silently no-op: it also sets `DAMAGE_NONPLAYERS` (`0x2`) and
   `DAMAGE_IN_AIR` (`0x4`) as unintended side effects, plus a stray `0x10` bit the engine ignores.
   A script that does `DAMAGE_PLAYERS | DAMAGE_NO_ARMOR` expecting "damage players, ignore their
   armor" will actually get "damage players *and* non-players *and* actors in the air," with
   **no** armor-ignoring effect at all.

**Conclusion: treat `DAMAGE_NO_ARMOR` as unusable in Zandronum — don't pass it.** There is no
working substitute flag in Zandronum's `SectorDamage` for bypassing armor; armor absorption
cannot be disabled through this function.

## Engine-family divergence: `DAMAGE_NO_ARMOR` actually works on UZDoom

Everything above about `DAMAGE_NO_ARMOR` is Zandronum-specific and does **not** carry over to
UZDoom. UZDoom's sector-damage flag header defines a real `DAMAGE_NO_ARMOR` constant with value
`16` (a clean single bit, distinct from the other four flags), and UZDoom's per-actor damage
helper actually consults it: when the bit is set, the damage pulse is sent through with an
armor-bypass flag that the engine's general damage-application code checks before letting a
target's armor absorb any of it. So on UZDoom, setting bit `16` in `SectorDamage`'s `flags`
argument genuinely disables armor absorption for that pulse — the wiki's description of the flag
is accurate there, unlike on Zandronum where the bit is never wired up to anything.

This does **not** make zt-bcc's own `DAMAGE_NO_ARMOR` constant (`zcommon.bcs:383`, decimal `22` /
`0b10110`) safe to use as-is on UZDoom, though. That constant is a compiler-library value shared
across engine targets, not something that changes per engine, and its malformed bit pattern is
unchanged: alongside bit `16` (which now does what it says on UZDoom) it still carries the same
two stray bits documented above, `0x2` and `0x4`. OR'ing zt-bcc's constant into `flags` on UZDoom
will bypass armor as intended, but will also still silently add `DAMAGE_NONPLAYERS` and
`DAMAGE_IN_AIR` to whatever the caller already set — the same unwanted side effects described in
the Zandronum divergence above, just no longer paired with a totally inert armor-bypass bit. A
script that wants armor bypass on UZDoom without those side effects should OR in the literal value
`16` rather than zt-bcc's `DAMAGE_NO_ARMOR` symbol. Since Zandronum has no working armor-bypass bit
at all, there is no flag value that behaves identically on both engines — code relying on this
needs an engine-specific branch (or should avoid depending on armor bypass through `SectorDamage`
entirely) rather than assuming one constant is portable.

Every other aspect of `SectorDamage` checked against UZDoom's implementation matches the
Zandronum-verified behavior described elsewhere in this file: the same one-shot-per-call
semantics, the same tag-chain sector resolution, the same `MF_SHOOTABLE` gate, the same
players/non-players/in-air/protection-item flag semantics (including the empty-string
protection-item no-op), and the same 3D-floor-aware extra pass over attached floor sectors with
its own height-range check.

## Behavior notes

- **One-shot, not continuous.** The wiki's own "Usage" line ("Does the damage only when the
  function is called") is confirmed by the implementation — there's no persistent per-tic hook
  registered; a caller wanting recurring damage must loop and call `SectorDamage` repeatedly
  (exactly as the wiki's own example script does, with `delay(5)` between calls).
- **3D-floor aware.** Beyond the sector's own `thinglist`, `P_SectorDamage` also walks any sectors
  attached to it as 3D floors (`sec->e->XFloor.attached`) and applies the same damage to actors
  touching/above those attached floors, with an extra height-range check
  (`p_spec.cpp:752-780`) — not mentioned by the wiki at all, since 3D floors are a ZDoom-family
  extension the wiki page doesn't call out here.
- **`MF_SHOOTABLE` gate.** Any actor without `MF_SHOOTABLE` (already dead, non-solid decorations,
  etc.) is skipped before the player/non-player check (`p_spec.cpp:715-716`).

## Example (from the wiki, still accurate)

```text
script 1 (int tag)
{
  if (PlayerNumber() < 0)
  {
    PrintBold(s:"Kill the non-players!!!");
    Sector_SetFade(tag, 255, 0, 0);

    while (GetActorProperty(0, APROP_HEALTH) > 0)
    {
      SectorDamage(tag, 100, "Fire", "", DAMAGE_NONPLAYERS | DAMAGE_IN_AIR);
      delay(5);
    }

    Sector_SetFade(tag, 0, 0, 0);
  }
}
```

## Relationship to SetSectorDamage

While researching this function I checked whether `SetSectorDamage` (`ACSF_SetSectorDamage`,
`zcommon.bcs:1724`, index `-94`) is implemented in Zandronum, since the two names strongly suggest
a getter/setter-style pair (`SectorDamage` = "damage it right now" vs. `SetSectorDamage` =
"configure its ongoing damage property"). **It is not implemented in this Zandronum checkout**:
there is no `ACSF_SetSectorDamage` (nor `case ACSF_SetSectorDamage:`) anywhere in
the Zandronum source's `src/p_acs.cpp`, and neighboring entries in the same `zcommon.bcs` index range
(`SetSectorTerrain` at `-95`, `GetMaxInventory` at `-93`) are similarly absent from the engine's
`EACSFunctions` enum and dispatch `switch`. This looks like a block of newer GZDoom-family
extension functions that `zt-bcc` lists (for cross-engine compatibility) but this Zandronum fork
never ported — i.e. calling `SetSectorDamage` from a BCS script would presumably fail to resolve
at the engine level despite compiling cleanly against `zt-bcc`'s table. This is a fork-existence
question, not a behavior question, so I'm flagging it here rather than guessing at
`SetSectorDamage`'s semantics; the sibling doc for that function should verify/state this
independently rather than treat the two as a working pair.
