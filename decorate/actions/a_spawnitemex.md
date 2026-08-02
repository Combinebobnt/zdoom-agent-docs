# `A_SpawnItemEx` (spawning with position, velocity, and control flags)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_SpawnItemEx` (retrieved 2026-07-31, oldid=52288) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:2591-2710` and `src/thingdef/thingdef_codeptr.cpp:2394-2510` (`InitSpawnedItem` helper). `SXF_TRANSFERAMBUSHFLAG` re-confirmed present and wired (`wadsrc/static/actors/constants.txt:56`, checked in `InitSpawnedItem`) 2026-08-01; `SXF_SETMASTER`/`SXF_TRANSFERPOINTERS`/originator target-override interaction re-traced the same day, resolving the prior "open question" below.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_SpawnItemEx)` in `src/thingdef/thingdef_codeptr.cpp`.

Spawns an actor at specified offsets from the calling actor, with controllable velocity direction and a rich flag set for managing inheritance of properties (translation, pointers, pitch, scale, etc.) and spawning constraints.

## Signature

```
bool A_SpawnItemEx(class<Actor> missile, fixed xofs = 0, fixed yofs = 0, fixed zofs = 0,
                   fixed xvel = 0, fixed yvel = 0, fixed zvel = 0, angle angle = 0,
                   int flags = 0, int failchance = 0, int tid = 0)
```

**Note on types:** Zandronum DECORATE uses fixed-point values (`fixed`) for offsets and velocities, not the `double` type shown in the ZDoom wiki. This affects precision and units — see "Units" below.

## Parameters

### `missile` (class<Actor>)

The actor class to spawn. Required; if null, the action returns false immediately.

### `xofs`, `yofs`, `zofs` (fixed, default 0)

Spawn offset relative to the calling actor. Units are fixed-point (1.0 = `FRACUNIT`). The offset direction is controlled by `flags`:

- **Without `SXF_ABSOLUTEPOSITION`** (default): offsets are **relative to the calling actor's facing angle**. `xofs` is forward/backward (positive forward), `yofs` is right/left (positive right), `zofs` is up/down (positive up).
- **With `SXF_ABSOLUTEPOSITION`**: offsets are **absolute map coordinates** (`xofs` as map X, `yofs` as map Y).

### `xvel`, `yvel`, `zvel` (fixed, default 0)

Initial velocity for the spawned actor. Units are map units per tic (1.0 = `FRACUNIT`). Direction is controlled by `flags`:

- **Without `SXF_ABSOLUTEVELOCITY`** (default): velocities are **relative to the calling actor's facing angle**, following the same orientation as offsets.
- **With `SXF_ABSOLUTEVELOCITY`**: velocities are **absolute map-axis velocities**.

The spawned actor's own `Speed` property can optionally **multiply** these velocities if `SXF_MULTIPLYSPEED` is set.

### `angle` (angle, default 0)

Angle adjustment for the spawned actor:

- **Without `SXF_ABSOLUTEANGLE`** (default): spawned actor's angle = calling actor's angle + `angle` (relative).
- **With `SXF_ABSOLUTEANGLE`**: spawned actor's angle = `angle` (absolute).

Positive angles rotate left, negative angles rotate right (following the engine's angle convention).

### `flags` (int, default 0)

Bitfield controlling spawn behavior, pointer inheritance, and property transfer. Combine multiple flags with `|`. See "Flags" section below.

### `failchance` (int, default 0)

Probability that the spawn will fail, as a raw value out of 256. If `failchance > 0` and `random(0,255) < failchance`, the spawn does not occur and the action returns early (result slot is not updated in this case — behavior depends on the calling state context). Value of 0 means 100% spawn probability; 256 means 0% (never spawn). Note: early return on chance failure means the action's result is **not set**, unlike a successful spawn; the calling state's prior result (or default) remains.

### `tid` (int, default 0)

Thing ID to assign to the spawned actor. If non-zero and the spawn succeeds, the actor is added to the TID hash with this ID. This happens **after** space-check validation (if any). The spawned actor's own actor definition may carry a default TID; Zandronum asserts the actor's TID is 0 before assigning the parameter value — if it isn't, behavior is undefined (assertion failure in debug builds).

## Flags (Zandronum 3.2.1)

**Zandronum defines 19 SXF_* flags.** The wiki lists additional flags; those not listed here **do not exist in Zandronum** and are silently treated as raw integers with no defined behavior if passed.

### Present in Zandronum

- `SXF_TRANSFERTRANSLATION` (1) — Copies the calling actor's `Translation` (color translation) to the spawned actor, provided the spawned actor has `MF2_DONTTRANSLATE` unset. Takes precedence over `SXF_USEBLOODCOLOR` if both are set.

- `SXF_ABSOLUTEPOSITION` (2) — Interprets `xofs` and `yofs` as absolute map coordinates, not relative to the calling actor's angle (see `xofs`/`yofs` above).

- `SXF_ABSOLUTEANGLE` (4) — Interprets `angle` as an absolute angle, not relative to the calling actor's angle (see `angle` above).

- `SXF_ABSOLUTEVELOCITY` (8) — Interprets `xvel`, `yvel`, `zvel` as absolute map-axis velocities, not relative to the calling actor's angle (see `xvel`/`yvel`/`zvel` above).

- `SXF_SETMASTER` (16) — Sets the spawned actor's `master` pointer, making it a "minion". Minions do not attack their master, and both can be affected by functions like `A_DamageMaster` and `A_GiveToChildren`. **Precise conditions (narrower than "monster-based or calling actor is a player"):** this flag only has any effect when (1) the spawned actor is monster-based (`MF3_ISMONSTER`) and survives the space-availability check, **and** (2) the "originator" (see "Originator" below — not necessarily the calling actor itself) is *also* monster-based. In that case `mo->master` is set to the **originator**, not literally the calling actor — if the calling actor is a missile, the originator is whatever non-missile actor is at the end of its `target` chain, so a minion spawned from a projectile gets the projectile's shooter as its master, not the projicting missile. **If the originator is a player instead of a monster, `SXF_SETMASTER` has no effect at all** — that code branch only sets the spawned actor's friendliness and (conditionally) its `target`, never touches `master`; whatever `SXF_TRANSFERPOINTERS` already assigned to `master` (or the class default, `NULL`) is left as-is. Only in the monster-originator case does `SXF_SETMASTER` override a `master` value `SXF_TRANSFERPOINTERS` set earlier in the same call.

- `SXF_NOCHECKPOSITION` (32) — Skips space-availability validation for monster-based spawned actors. Normally, if the spawned actor is a monster (`MF3_ISMONSTER`), Zandronum calls `P_TestMobjLocation` to ensure the spawn point is passable; if the test fails, the actor is destroyed and the action returns false. This flag bypasses that test. Non-monster actors are never space-checked regardless of this flag.

- `SXF_TELEFRAG` (64) — Calls `P_TeleportMove` with `telefrag = true` on the spawned actor's spawn point, potentially killing any actor in the way. Implies `SXF_NOCHECKPOSITION` (the flag is bitwise OR'd into the flags set after telefragging). Only applies to monster-based spawned actors. For non-monsters, the flag is ignored.

- `SXF_CLIENTSIDE` (128) — Marks the spawn as client-side-only in Zandronum multiplayer (documented in the wiki as "Skulltag only: not supported by ZDoom"). The spawn is gated through `NETWORK_ShouldActorNotBeSpawned(self, missile, true)` — if that returns true (server-authoritative spawn restrictions), the action returns without spawning. On successful client-side-only spawn, the actor gets the `NETFL_CLIENTSIDEONLY` flag set.

- `SXF_TRANSFERAMBUSHFLAG` (256) — Copies the `MF_AMBUSH` flag from the calling actor to the spawned actor. Only applies if the spawned actor is monster-based and can have the `MF_AMBUSH` flag set.

- `SXF_TRANSFERPITCH` (512) — Copies the calling actor's `pitch` (vertical aiming angle) to the spawned actor. Does **not** affect the spawned actor's velocity — the velocity is calculated from the `xvel`/`yvel`/`zvel` parameters and the angle, with no pitch component applied. To incorporate pitch into trajectory, manually calculate trajectory offsets; see the wiki's example (involving `cos(pitch)` and `sin(pitch)` math) if you need this behavior.

- `SXF_TRANSFERPOINTERS` (1024) — Copies the calling actor's `target`, `master`, and `tracer` pointers to the spawned actor. This runs early in `InitSpawnedItem`, **before** the monster/originator block, so every later step in that function can still overwrite what this flag set. **Resolved (was an open question in an earlier revision of this file): for a monster-based spawned actor whose originator is a player-type actor with a non-null `player->attacker`, `target` is unconditionally overwritten to that attacker** (`mo->LastHeard = mo->target = attacker;` in `InitSpawnedItem`) — this happens regardless of whether `SXF_TRANSFERPOINTERS` already set `target` to something else, and regardless of whether `SXF_TRANSFERPOINTERS` was even passed at all. There is no flag to suppress this override; a monster spawned by a player-originated call only keeps a `SXF_TRANSFERPOINTERS`-assigned `target` if the player has no current `attacker`. `master` is not affected by this same override (see `SXF_SETMASTER` above for when `master` gets overwritten instead).

- `SXF_USEBLOODCOLOR` (2048) — Uses the calling actor's `BloodColor` as the source of a color translation to apply to the spawned actor, provided the spawned actor can be translated (`MF2_DONTTRANSLATE` unset). If the calling actor has no `BloodColor` defined, no translation is applied. Takes lower precedence than `SXF_TRANSFERTRANSLATION` — if both are set, translation takes precedence.

- `SXF_CLEARCALLERTID` (4096) — If the spawn succeeds (including a successful space check or when space checks are skipped), sets the calling actor's `tid` to 0 and removes it from the TID hash. Does not affect the spawned actor's TID. Note: this runs **after** the spawned actor is validated, so if the spawn fails, the calling actor's TID is unchanged.

- `SXF_MULTIPLYSPEED` (8192) — Multiplies the velocity parameters (`xvel`, `yvel`, `zvel`) by the spawned actor's `Speed` property before applying them. Useful for scaling velocity relative to the actor's defined speed without hand-calculating the multiplier.

- `SXF_TRANSFERSCALE` (16384) — Copies the calling actor's scale factors (`scaleX`, `scaleY`) to the spawned actor.

- `SXF_TRANSFERSPECIAL` (32768) — Copies the calling actor's map special (`special`) and its arguments (`args[0]` through `args[4]`) to the spawned actor. Useful for chaining map specials across spawned actors.

- `SXF_CLEARCALLERSPECIAL` (65536) — If the spawn succeeds, clears the calling actor's `special` and all its `args[]` to 0. Does not affect the spawned actor's special/args.

- `SXF_TRANSFERSTENCILCOL` (131072) — Copies the calling actor's `fillcolor` (stencil/fog color) to the spawned actor. Zandronum-specific; used for colored fog/stencil rendering effects.

### **NOT present in Zandronum** (wiki lists these; they compile as inert integers)

- `SXF_TRANSFERALPHA` — wiki lists this as copying the alpha value.
- `SXF_TRANSFERRENDERSTYLE` — wiki lists this as copying the render style.
- `SXF_SETTARGET`, `SXF_SETTRACER`, `SXF_NOPOINTERS` — wiki lists these as pointer-control variants.
- `SXF_ORIGINATOR` — wiki lists this as explicitly setting the originator.
- `SXF_TRANSFERSPRITEFRAME` — wiki lists this as copying sprite/frame state.
- `SXF_TRANSFERROLL` — wiki lists this as copying roll angle.
- `SXF_ISTARGET`, `SXF_ISMASTER`, `SXF_ISTRACER` — wiki lists these as pointer-setting variants.

These are either GZDoom-family additions or were introduced after Zandronum 3.2.1. **Do not use these in Zandronum DECORATE** — they are silently treated as raw integers and have no effect.

## Return value

**Zandronum-specific note:** The wiki describes a return of two values (a `bool` plus an `Actor` pointer). Zandronum's DECORATE only sets a single boolean result via `ACTION_SET_RESULT(res)`:

- `true` if the spawn succeeded (including successful space validation or when space checks are skipped, and also when the spawn is skipped due to `failchance`).
- `false` if the spawn failed (null missile class, failed space check for a monster actor, or certain network gate checks like `SXF_CLIENTSIDE` being disallowed by the server).

**Important:** A `failchance` early-return (line 2612 of the source) happens **before** `ACTION_SET_RESULT` is called, so the result slot is **not updated** in the case of a chance-based skip. The action's result in this case is whatever the calling state's prior result was (or the actor's default).

To distinguish "spawn succeeded" from "spawn was skipped by chance" in calling DECORATE, you must either:
- Use a separate action before `A_SpawnItemEx` to detect the failure mode directly (e.g., with `A_JumpIf` on an actor variable you set just before the spawn).
- Accept that a chance-skipped spawn leaves the prior result unchanged and structure your state machine accordingly.

## Originator concept

The "originator" is the actor that Zandronum considers the ultimate "spawner" or "shooter" for damage-attribution and pointer-inheritance purposes. Normally, the originator is the calling actor itself. **Exception:** if the calling actor is a missile (`mo->isMissile()`), Zandronum walks the missile's `target` pointer chain until it finds a non-missile actor — that becomes the originator. If the missile has no non-missile target, there is no originator in this context.

The originator is used by `InitSpawnedItem` to:
- Determine which actor to record as the spawned actor's initial `target` for non-missile spawned actors (unless `SXF_TRANSFERPOINTERS` copies the calling actor's target instead).
- Set the spawned actor's friendliness (if it's monster-based and has no explicit pointer flags) via `CopyFriendliness`, when the originator is also monster-based.
- Set the spawned actor's `master` when `SXF_SETMASTER` is set and the originator is monster-based (see that flag's entry above — the master becomes the *originator*, not necessarily the calling actor).
- **Override `target`** to the originator's `player->attacker` when the originator is a player-type actor with a live attacker — unconditionally, independent of any flag (see `SXF_TRANSFERPOINTERS` above).

## Zandronum-specific networking behavior

- **Server-side authority for spawn decision:** The entire spawn is server-authoritative. In client mode, the action returns early (before spawning) if the missile would not be server-allowed (see the `NETWORK_ShouldActorNotBeSpawned` check in the source).

- **Client-side-only actors:** If `SXF_CLIENTSIDE` is set and the spawn succeeds, the actor gets `NETFL_CLIENTSIDEONLY` set. On a dedicated server or listen server, this flag remains set but has no immediate effect (it marks the actor as a visual-only client update).

- **Server broadcast on success:** If spawning on the server and the spawn succeeds:
  - `SERVERCOMMANDS_SpawnThing(mo)` sends the basic spawn to all clients.
  - If the spawned actor's angle is non-zero, `SERVERCOMMANDS_SetThingAngle(mo)` is sent (optimization to avoid zero-angle spam).
  - If the spawned actor received a translation (`SXF_TRANSFERTRANSLATION` or `SXF_USEBLOODCOLOR`), `SERVERCOMMANDS_SetThingTranslation(mo)` is sent.
  - TID assignment (if `tid` parameter is non-zero) is synced separately via `SERVERCOMMANDS_SetThingTID(mo)`.
  - If the spawned actor is a missile or has bounce flags, `SERVERCOMMANDS_SetThingTarget(mo)` syncs the target pointer.
  - If the spawned actor's scale differs from its actor definition default, `SERVERCOMMANDS_UpdateThingScaleNotAtDefault(mo)` is sent.
  - If the spawned actor's `fillcolor` (stencil color) differs from its actor definition default, `SERVERCOMMANDS_SetThingProperty(mo, APROP_StencilColor)` is sent.

- **Monster spawn restrictions:** If `DamageType == NAME_Massacre` on the calling actor and the spawned actor is monster-based, the spawn is skipped entirely (before `ACTION_SET_RESULT` is set). This prevents re-spawning during a player-wipe death.

## Example (Zandronum DECORATE)

```
actor PoisonCloud
{
    // Properties omitted for brevity
    States
    {
    Spawn:
        CLOD A 20 Bright;
        Loop;
    }
}

actor PoisonPod
{
    Default
    {
        Health 20;
        Radius 16;
        Height 20;
        Mass 100;
        Speed 0;
        DeathSound "PoisonPod/Puff";
    }

    States
    {
    Spawn:
        PPOD A 10;
        Loop;
    Death:
        PPOD B 5 A_Scream;
        PPOD C 5 A_Explode(20, 128);
        PPOD D 10 Bright A_SpawnItemEx("PoisonCloud", 0, 0, 28, 0, 0, 0, 0, SXF_TRANSFERPOINTERS);
        Stop;
    }
}
```

## Open questions and untraced details

- Whether the `assert(mo->tid == 0)` before `tid` assignment can ever legitimately fail in map-authoring scenarios (seems to be a defensive check against actors spawning with pre-set TIDs).
