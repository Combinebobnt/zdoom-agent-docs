# `TeleportFog`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `Classes:TeleportFog` (retrieved 2026-08-01, oldid=48907) + verified against Zandronum source (`src/g_shared/a_sharedglobal.h:85`, `src/p_teleport.cpp:49`, `wadsrc/static/actors/shared/teleport.txt`).
**Bucket:** native C++ class (`class ATeleportFog : public AActor` in `src/g_shared/a_sharedglobal.h:85`); also declared in DECORATE as `ACTOR TeleportFog native` in `wadsrc/static/actors/shared/teleport.txt`.

Special effect actor spawned when an actor teleports or undergoes morphing/unmorphing. The fog is spawned at the actor's location with the actor set as the fog's target pointer (during teleportation only; see "Target pointer behavior" below).

## Appearance and flags

- **Flags:** `+NOBLOCKMAP`, `+NOTELEPORT`, `+NOGRAVITY` — passes through solid geometry, cannot be teleported, unaffected by gravity.
- **Render style:** `Add` (additive blending, typical for flash effects).
- **State sequences:** Sprite varies by game type — `Spawn` state (TFOG frames) for Doom, `Raven` state (TELE frames) for Heretic/Hexen, `Strife` state (TFOG frames) for Strife. Selection happens in `PostBeginPlay()` based on `gameinfo.gametype`.

## Behavior

### Sound

Plays `misc/teleport` sound at full volume on the `CHAN_BODY` channel when `PostBeginPlay()` executes.

### Target pointer behavior — wiki divergence

**During regular teleportation:** The fog's `target` pointer is set to the teleporting actor. This enables manipulating the teleporting actor via actor pointers.

**During morphing and unmorphing:** The fog is spawned but the `target` pointer is **not set**. This contradicts the ZDoom Wiki's claim that "This includes when an actor (un)morphs." Actor pointer manipulation is not available when the fog comes from morphing effects.

### Spawn height

- **Non-missile actors:** fog spawns at `actor.z + TELEFOGHEIGHT` (where `TELEFOGHEIGHT` is typically 32 map units).
- **Missile actors** (`MF_MISSILE` flag): fog spawns at exact actor Z coordinate, with no height offset.

### Spectators — Zandronum-specific

In multiplayer, actors marked as spectators do not spawn any fog, even if they would normally create it during teleportation. This is Zandronum-specific netplay behavior.

## Spawn contexts

### Player/actor teleportation (P_Teleport in src/p_teleport.cpp)

- **Source fog** (old position): spawned if `sourceFog` parameter is true.
- **Destination fog** (new position): spawned if `useFog` parameter is true.
- **When:** triggered by linedef special 70 (Teleport) and related specials, or via ACS function calls to `Teleport()` or `TeleportOther()`.

### Action function A_Teleport (src/thingdef/thingdef_codeptr.cpp:5221)

Teleports an actor to a random spot of a specified type. Accepts optional `FogType` parameter to customize or disable the fog:
- If `FogType` is specified, a fog of that type is spawned at the *previous* actor position only (not destination), with `ALLOW_REPLACE` honored.
- If `FogType` is omitted or null, no fog is spawned.
- **Note:** Unlike regular teleportation, `A_Teleport` does not spawn a destination fog — only a source fog at the point of origin.

### Player morphing (P_MorphPlayer in src/g_shared/a_morph.cpp:122)

- Fog spawned as "enter flash" when a player morphs into a beast form.
- Defaults to `TeleportFog` if no `enter_flash` class is specified in the morph call.
- Target pointer not set (see "Target pointer behavior" section).

### Player unmorphing (P_UndoPlayerMorph in src/g_shared/a_morph.cpp:383)

- Fog spawned as "exit flash" when a player unmorphs back to human form.
- Defaults to the class stored in `player->MorphExitFlash` (usually `TeleportFog`).
- Target pointer not set.
- Spawned at offset angle from unmorphed actor position (20 map units perpendicular to facing angle).

### Monster morphing and unmorphing

- Morphed monsters spawn entrance/exit fog via the same mechanism as players, with defaults to `TeleportFog`.

### Invasion-mode spawning — Zandronum-only (invasion.cpp)

When Invasion mode spawns monsters, items, or weapons at designated spots, temporary fog effects are created via `Spawn<ATeleportFog>(..., ALLOW_REPLACE)` at each spawn point. This is Zandronum-specific multiplayer/mod mode behavior not present on ZDoom Wiki documentation.

### Client-side teleport replication — Zandronum-only (cl_main.cpp)

Clients replicate incoming teleport events (receiving state updates from server) by spawning local fog visuals. Two sites handle player vs. missile-type actors.

## Replaceability

`TeleportFog` is spawned with the `ALLOW_REPLACE` flag, which means:

1. **`ACTOR TeleportFog replaces TeleportFog` in a custom WAD**: A modded `TeleportFog` actor definition will be used instead of the built-in one. This is the intended replacement mechanism.
2. **Redefining `TeleportFog` directly in a WAD causes an error**: The engine detects same-name redefinition and rejects it (enforced by `DECORATE` parser). Use `replaces` instead.
3. **Action function parameter**: The `A_Teleport` action function accepts an optional `FogType` parameter, allowing per-call customization without global replacement.
4. **Morphing customization**: Morph power effects accept `enter_flash` and `exit_flash` class parameters to override the fog type on a per-morph basis.

## Unused infrastructure

The function `P_SpawnTeleportFog(fixed_t x, fixed_t y, fixed_t z, int spawnid)` exists in `src/p_teleport.cpp:80` with a comment "The beginning of customizable teleport fog (not active yet)". It accepts a `spawnid` parameter for per-map fog customization, but **no call sites invoke it** — all teleport fog spawning uses the direct `Spawn<ATeleportFog>(...)` API instead. This path remains implemented but disabled.

## Differences from ZDoom Wiki

- **ZDoom Wiki includes `+ZDOOMTRANS` flag** in the ZScript definition; Zandronum's DECORATE version omits this, as it is a GZDoom-family-specific feature.
- **Wiki states target pointer is set on morph** — verified false in Zandronum (see "Target pointer behavior" section).
