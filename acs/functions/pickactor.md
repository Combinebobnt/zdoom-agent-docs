# PickActor

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki (https://zdoom.org/w/index.php?title=PickActor&oldid=44255), verified against Zandronum source and TID assignment edge cases documented from engine code.
**Bucket:** Extension function (index -83, `case ACSF_PickActor:` in `p_acs.cpp`)

**Signature:** `int PickActor(int source, fixed angle, fixed pitch, fixed distance, int tid [, int actorMask [, int wallMask [, int flags]]])`

Performs a ray cast from a source actor in a given direction and assigns a TID to the first actor hit (if any). Used to pick targets under a crosshair or in a specific direction.

## Parameters

**source** — TID of the actor the ray originates from, or 0 to use the script's activator. Returns 0 immediately if the actor cannot be found.

**angle** — Direction to look, as a fixed-point fraction of a full turn: 0.0 = east, 0.25 = north, 0.5 = west, 0.75 = south. Wraps at 1.0. Compatible with `GetActorAngle()` output.

**pitch** — Vertical angle to look, as a fixed-point fraction of a full turn: 0.0 = horizontal, 0.25 = down, 0.75 = up. Wraps at 1.0. Compatible with `GetActorPitch()` output; note that `GetActorPitch()` returns a value in the 0.75–0.0–0.25 range for "looking down to level to looking up."

**distance** — Maximum distance in map units to pick actors within.

**tid** — TID to assign to the picked actor. If 0, the function will still pick the actor and return its **existing** TID (if any), but see "Return value" and "TID assignment" below.

**actorMask** — (optional, defaults to `MF_SHOOTABLE`) Actor flags that a target must have to be picked. Raw engine flag bitfield (see the Zandronum source's `src/actor.h` for `MF_*` definitions). Only actors with **all** flags in the mask set will be considered.

**wallMask** — (optional, defaults to `ML_BLOCKEVERYTHING | ML_BLOCKHITSCAN`) Linedef flags that block the ray. Raw engine flag bitfield (see the Zandronum source's `src/doomdef.h` for `ML_*` definitions). The ray stops when it hits a line with **any** flag in the mask set.

**flags** — (optional) Combination of:
- `PICKAF_FORCETID` — Forcibly assign the specified TID, overwriting the actor's existing one. Without this, the function will not change a TID that is already set (see "TID assignment" below).
- `PICKAF_RETURNTID` — Return the picked actor's TID instead of 1. Useful for reading an actor's existing TID.

## Return value

| Case | Return |
|------|--------|
| No actor picked | 0 |
| Actor picked, no flags | 1 |
| Actor picked, `PICKAF_RETURNTID` set | The picked actor's TID |
| Actor picked, TID would not change (see below) | 0 |

## TID assignment

Without `PICKAF_FORCETID`, the function **will not assign a TID if one already exists**, even if the call succeeds. It also **will not assign tid=0** (TID 0 means "no TID" in the engine).

Consequence: `PickActor(..., tid=0, ..., PICKAF_RETURNTID)` returns 0 in two cases: (1) no actor was picked, or (2) an actor was picked but it has no existing TID. The wiki's "Correct usage" section documents a workaround: call `PickActor` twice with the same arguments, first with `tid=0, PICKAF_RETURNTID` to read the existing TID, then with a temporary unique TID and `PICKAF_FORCETID` to reassign it. This avoids the ambiguity because nothing can move between the two calls while a single script is executing.

## Special cases

- **GHOST flag actors:** Actors with the `MF3_GHOST` flag are **skipped** by the ray and will not be picked, regardless of `actorMask`.
- **Same-species check (Zandronum multiplayer note):** In multiplayer, the ray will not pick actors of the same species as the source actor, unless called from a specific netcode context (see `p_map.cpp:4611–4616`, flag `hitSameSpecies`). This behavior is present in Zandronum 3.2.1 and later but is not extensively documented in the wiki.
- **Underargument call:** If called with fewer than 5 arguments, the function returns 0 silently (no crash).
- **Ray origin:** The ray does not originate from the source actor's `(x, y, z)` directly but from a point offset by the actor's eye height (e.g. player attack offset, or 8 map units above the actor's feet for non-players).
