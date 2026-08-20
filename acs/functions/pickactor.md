# PickActor

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** ZDoom Wiki (https://zdoom.org/w/index.php?title=PickActor&oldid=44255), verified against Zandronum source and TID assignment edge cases documented from engine code.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Extension function (index -83, `case ACSF_PickActor:` in `p_acs.cpp`)

**Signature:** `int PickActor(int source, fixed angle, fixed pitch, fixed distance, int tid [, int actorMask [, int wallMask [, int flags]]])`

Performs a ray cast from a source actor in a given direction and assigns a TID to the first actor hit (if any). Used to pick targets under a crosshair or in a specific direction.

## Parameters

**source** — TID of the actor the ray originates from, or 0 to use the script's activator. Returns 0 immediately if the actor cannot be found.

**angle** — Direction to look, as a fixed-point fraction of a full turn: 0.0 = east, 0.25 = north, 0.5 = west, 0.75 = south. Wraps at 1.0. Compatible with `GetActorAngle()` output.

**pitch** — Vertical angle to look, as a fixed-point fraction of a full turn: 0.0 = horizontal, 0.25 = down, 0.75 = up. Wraps at 1.0. Compatible with `GetActorPitch()` output; note that `GetActorPitch()` returns a value in the 0.75–0.0–0.25 range for "looking down to level to looking up."

**distance** — Maximum distance in map units to pick actors within.

**tid** — TID to assign to the picked actor. If 0, the function will still pick the actor and return its **existing** TID (if any), but see "Return value" and "TID assignment" below.

**actorMask** — (optional, defaults to `MF_SHOOTABLE`) Actor flags that a target must have to be picked. Raw engine flag bitfield — `MF_*` definitions live in `src/actor.h` on Zandronum and `src/playsim/actor.h` on UZDoom. Only actors with **all** flags in the mask set will be considered. Confirmed identical default and semantics on both engines (Zandronum `src/p_acs.cpp:6878`; UZDoom `src/playsim/p_acs.cpp:6391`).

**wallMask** — (optional, defaults to `ML_BLOCKEVERYTHING | ML_BLOCKHITSCAN`) Linedef flags that block the ray. Raw engine flag bitfield — `ML_*` definitions live in `src/doomdef.h` on Zandronum and `src/doomdata.h` on UZDoom. The ray stops when it hits a line with **any** flag in the mask set. Confirmed identical default and semantics on both engines (Zandronum `src/p_acs.cpp:6883`; UZDoom `src/playsim/p_acs.cpp:6396`).

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

This assignment logic (the `PICKAF_FORCETID` gate, the "won't assign tid=0" rule, and the `PICKAF_RETURNTID` return value) is byte-for-byte identical between the two engines' `ACSF_PickActor` case bodies (Zandronum `src/p_acs.cpp:6899-6912`; UZDoom `src/playsim/p_acs.cpp:6412-6423`) — only the underlying TID-hash bookkeeping differs (Zandronum manually does `RemoveFromHash()`/`AddToHash()`; UZDoom wraps the same operation in `AActor::SetTID`), which is an implementation detail with no observable difference in ACS.

## Special cases

- **GHOST flag actors:** Actors with the `MF3_GHOST` flag are **skipped** by the ray and will not be picked, regardless of `actorMask`. Confirmed identical on both engines: the trace context `PickActor` builds sets ghost-skipping unconditionally, independent of any weapon/puff flag that would normally gate it for a real attack (Zandronum `TData.hitGhosts = true;`, `src/p_map.cpp:4609`; UZDoom `TData.hitGhosts = true;`, `src/playsim/p_map.cpp:5149`).
- **Same-species actors are *not* filtered (correction):** A prior revision of this doc claimed the ray "will not pick actors of the same species as the source actor" in multiplayer, citing `src/p_map.cpp:4611-4616`. That reading was backwards. Those exact lines show `P_LinePickActor` explicitly forcing `TData.hitSameSpecies = false` — the adjacent comment reads "Explicity set hitSameSpecies to false. We are allowed to pick actors that are the same species" — so the species check `CheckForActor` is capable of applying (`src/p_map.cpp:4161`) never fires for a `PickActor` call. UZDoom does the same thing under a different field name: `TData.MThruSpecies = false;` unconditionally, in its own `P_LinePickActor` (`src/playsim/p_map.cpp:5150`). On both engines, `PickActor` can and will return an actor of the same species as the source; only a real weapon attack's `MF6_MTHRUSPECIES` puff flag ever gates same-species hits, and `PickActor` doesn't go through that path.
- **Underargument call:** If called with fewer than 5 arguments, the function returns 0 silently (no crash) — see "Engine-family divergence: argument-count enforcement" below for a case where UZDoom's behavior can differ from this.
- **Ray origin (correction):** The ray does not originate from the source actor's `(x, y, z)` directly. On both engines the origin is the actor's *vertical center* — half its height above its feet, adjusted for `floorclip` — plus a further offset: 8 map units for a non-player actor, or the player's `AttackZOffset` (scaled by the player's crouch factor) for a player (Zandronum `shootz = t1->z - t1->floorclip + (t1->height >> 1)` then `+= 8*FRACUNIT` or `+= AttackZOffset*crouchfactor`, `src/p_map.cpp:4595-4603`; UZDoom `shootz = t1->Center() - t1->Floorclip + t1->AttackOffset()`, `src/playsim/p_map.cpp:5143`, where `AttackOffset()` returns `8 + offset` for non-players or `(AttackZOffset + offset) * crouchfactor` for players, `src/playsim/actorinlines.h:111-122`). A prior revision of this doc described the non-player case as simply "8 map units above the actor's feet," which drops the half-height term — the real origin is roughly chest-height plus 8, not ankle-height plus 8.

## Zandronum-specific: PickActor bypasses the ally shoot-through dmflag

Zandronum has a deathmatch flag, `zadmflags & ZADF_SHOOT_THROUGH_ALLIES` (settable via `sv_shootthroughallies`), that normally lets a player's hitscan/projectile pass through teammates instead of stopping on them (`PLAYER_CannotAffectAllyWith`, checked in `CheckForActor` at `src/p_map.cpp:4172`). `PickActor`'s trace context sets `TData.bIsLinePick = true` (`src/p_map.cpp:4616`), and the ally check at `src/p_map.cpp:4172` is gated on `!data->bIsLinePick` — so for a `PickActor` call that check is always skipped, regardless of the dmflag's setting. In other words, `PickActor` always stops on (and can pick) an allied actor, even on a server where `ZADF_SHOOT_THROUGH_ALLIES` is enabled for real weapon fire. UZDoom has no equivalent concept at all — `ZADF_SHOOT_THROUGH_ALLIES` and `PLAYER_CannotAffectAllyWith` don't exist in its source tree (confirmed absent by a full-tree search) — so there's nothing to bypass there; UZDoom's `P_LinePickActor` never had an ally pass-through path to begin with.

## Engine-family divergence: argument-count enforcement

Zandronum's `ACSF_PickActor` case unconditionally requires `argCount >= 5`; if not met, the case body is skipped entirely and control falls through to the function's default `return 0;` with no way to disable that check (`if (argCount >= 5) { ... } break;`, `src/p_acs.cpp:6870`, falling through to `src/p_acs.cpp:9059-9063`). UZDoom's equivalent gate is a `MIN_ARG_COUNT(5)` macro that only returns 0 `if (argCount < minCount && !(Level->i_compatflags2 & COMPATF2_NOACSARGCHECK))` (`src/playsim/p_acs.cpp:5368-5374`, used at `:6383`). `COMPATF2_NOACSARGCHECK` is a real, settable UZDoom compatibility flag (`compat_noacsargcheck` in MAPINFO, or `noacsargcheck` in a `compatibility.txt`/COMPATIBILITY lump entry — `src/gamedata/g_mapinfo.cpp:1946`, `src/maploader/compatibility.cpp:167`) that disables ACS argument-count checking tree-wide when set. Zandronum has no equivalent compat flag or setting (confirmed absent from its `COMPATF2_*` enum and tree-wide). Under default compat settings both engines behave identically for an underargument `PickActor` call (silent 0, no crash); a map/mod that explicitly sets `compat_noacsargcheck` on UZDoom instead lets the call proceed and read `args[0]`..`args[4]` past however many arguments were actually supplied, which Zandronum can never do.
