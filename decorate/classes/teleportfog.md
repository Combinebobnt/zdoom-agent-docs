# `TeleportFog`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `Classes:TeleportFog` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=Classes%3ATeleportFog&oldid=48907) + verified against Zandronum source (`src/g_shared/a_sharedglobal.h:85`, `src/p_teleport.cpp:49`, `wadsrc/static/actors/shared/teleport.txt`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** native C++ class in Zandronum (`class ATeleportFog : public AActor` in `src/g_shared/a_sharedglobal.h:85`; also declared in DECORATE as `ACTOR TeleportFog native` in `wadsrc/static/actors/shared/teleport.txt`); ordinary ZScript class in UZDoom (`class TeleportFog : Actor` in `wadsrc/static/zscript/actors/shared/teleport.zs:20`, no native backing beyond what `Actor` itself provides — though the fog-spawning *mechanism* used throughout the engine is native, see "Engine-family divergence: customizable teleport fog is live on UZDoom" below).

Special effect actor spawned when an actor teleports or undergoes morphing/unmorphing. The fog is spawned at the actor's location with the actor set as the fog's target pointer (during teleportation only; see "Target pointer behavior" below).

## Appearance and flags

- **Flags:** `+NOBLOCKMAP`, `+NOTELEPORT`, `+NOGRAVITY` — passes through solid geometry, cannot be teleported, unaffected by gravity. Confirmed identical on UZDoom's `TeleportFog` (`wadsrc/static/zscript/actors/shared/teleport.zs:24-26`), which additionally sets `+ZDOOMTRANS` (see "Differences from ZDoom Wiki" below).
- **Render style:** `Add` (additive blending, typical for flash effects).
- **State sequences:** Sprite varies by game type — `Spawn` state (TFOG frames) for Doom, `Raven` state (TELE frames) for Heretic/Hexen, `Strife` state (TFOG frames) for Strife. Selection happens in `PostBeginPlay()` based on `gameinfo.gametype`. Confirmed identical on UZDoom (`teleport.zs:30-63`) — same three state labels and frame sequences, with `PostBeginPlay()` calling `SetStateLabel()` (the ZScript idiom) instead of DECORATE's implicit state jump.

## Behavior

### Sound

Plays `misc/teleport` sound at full volume on the `CHAN_BODY` channel when `PostBeginPlay()` executes. Confirmed identical on UZDoom (`A_StartSound("misc/teleport", CHAN_BODY)` at `teleport.zs:48`).

### Target pointer behavior — wiki divergence

**During regular teleportation:** The fog's `target` pointer is set to the teleporting actor. This enables manipulating the teleporting actor via actor pointers.

**During morphing and unmorphing:** The fog is spawned but the `target` pointer is **not set**. This contradicts the ZDoom Wiki's claim that "This includes when an actor (un)morphs." Actor pointer manipulation is not available when the fog comes from morphing effects.

## Engine-family divergence: target pointer *is* set on morph fog on UZDoom

The "not set" behavior above is Zandronum-specific, not a ZDoom-family-wide fact — UZDoom's morph/unmorph implementations explicitly assign the spawned fog's `target` pointer, which means the ZDoom Wiki's original claim (called false above, for Zandronum) actually holds true on the primary engine:

- Player morph (`wadsrc/static/zscript/actors/player/player_morph.zs:223-228`): `Actor fog = Spawn(enterFlash, ...); if (fog) fog.Target = morphed;`
- Player unmorph (`player_morph.zs:379-384`): `fog.Target = alt;` (the actor returning to its original body).
- Monster morph (`wadsrc/static/zscript/actors/morph.zs:239-244`): `fog.Target = morphed;`
- Monster unmorph (`morph.zs:338-343`): `fog.Target = alt;`

By contrast, Zandronum's `src/g_shared/a_morph.cpp` spawns the same fog actors (`Spawn(enter_flash ?: RUNTIME_CLASS(ATeleportFog), ...)` at line 122 and line 510) with no equivalent `->target` assignment anywhere in either function — the only `->target` writes in the file are unrelated (`morphed->target = actor->target` at line 92 and `actor->target = beast->target` at line 550, both copying the *morphing actor's own* target pointer during the morph transfer, not touching the fog). So this file's "wiki divergence" framing above is accurate only for Zandronum: on UZDoom, actor-pointer manipulation via the fog's `target` **is** available for morph/unmorph fog, exactly as the wiki originally described.

### Spawn height

- **Non-missile actors:** fog spawns at `actor.z + TELEFOGHEIGHT` (where `TELEFOGHEIGHT` is typically 32 map units).
- **Missile actors** (`MF_MISSILE` flag): fog spawns at exact actor Z coordinate, with no height offset.

### Spectators — Zandronum-specific

In multiplayer, actors marked as spectators do not spawn any fog, even if they would normally create it during teleportation. This is Zandronum-specific netplay behavior — independently confirmed here by reading UZDoom's `P_Teleport` (`src/playsim/p_teleport.cpp:81-255`, the code that calls this class's fog-spawn logic for the base line-special teleports): it has no spectator/`bSpectating`-equivalent check anywhere in its fog-spawning branches, matching the same finding already documented in `acs/functions/teleportother.md` and `acs/functions/teleport_nostop.md` for those specials' own fog spawning (see those files for the full spectator-fog analysis rather than repeating it here).

## Spawn contexts

### Player/actor teleportation (P_Teleport in src/p_teleport.cpp)

- **Source fog** (old position): spawned if `sourceFog` parameter is true.
- **Destination fog** (new position): spawned if `useFog` parameter is true.
- **When:** triggered by linedef special 70 (Teleport) and related specials, or via ACS function calls to `Teleport()` or `TeleportOther()`.
- **On UZDoom:** the equivalent code path is `P_Teleport` in the UZDoom source's `src/playsim/p_teleport.cpp:81-255`, which takes a `flags` bitfield (`TELF_SOURCEFOG`/`TELF_DESTFOG`) instead of separate `sourceFog`/`useFog` booleans, and spawns fog by calling this class's own `P_SpawnTeleportFog` helper (see "Engine-family divergence: customizable teleport fog is live on UZDoom" below) rather than hardcoding `Spawn<ATeleportFog>` the way Zandronum's `P_Teleport` does.

### Action function A_Teleport (src/thingdef/thingdef_codeptr.cpp:5221)

Teleports an actor to a random spot of a specified type. Accepts optional `FogType` parameter to customize or disable the fog:
- If `FogType` is specified, a fog of that type is spawned at the *previous* actor position only (not destination), with `ALLOW_REPLACE` honored.
- If `FogType` is omitted or null, no fog is spawned.
- **Note:** Unlike regular teleportation, `A_Teleport` does not spawn a destination fog — only a source fog at the point of origin.
- **On UZDoom:** this is reversed. `A_Teleport`'s `fogtype` parameter defaults to `"TeleportFog"` (not null), and with default `flags=0` neither `TF_NOSRCFOG` nor `TF_NODESTFOG` is set — so a bare `A_Teleport()` call spawns fog at *both* the source and destination by default, the opposite of the Zandronum-only behavior described above. See `decorate/actions/a_teleport.md`'s "Engine-family divergence: fog spawning, state-jump gating, and network authority" section for the full analysis of that reversal; the `TF_USEACTORFOG` flag mentioned there (routing through this class's own customizable-fog fields instead of the literal `fogtype` class) is covered from this file's angle in "Engine-family divergence: customizable teleport fog is live on UZDoom" below.

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

## Engine-family divergence: customizable teleport fog is live on UZDoom

The "not active yet" comment above is Zandronum-specific — a function with the identical comment and a similar signature shape exists in the UZDoom source's `src/playsim/p_teleport.cpp:38-61` (`void P_SpawnTeleportFog(AActor *mobj, const DVector3 &pos, bool beforeTele, bool setTarget)`), but there it is fully wired up, not dead code:

- Every `AActor` on UZDoom carries `TeleFogSourceType`/`TeleFogDestType` fields (`src/playsim/actor.h:1373-1374`), both defaulting to `"TeleportFog"` in the base `Actor` class's `Default` block (`wadsrc/static/zscript/actors/actor.zs:534-535`).
- `P_SpawnTeleportFog` spawns `mobj->TeleFogSourceType` or `mobj->TeleFogDestType` (whichever `beforeTele` selects) at `pos`, offset by `TELEFOGHEIGHT` unless `mobj` is a missile, and sets the spawned fog's `target` to `mobj` when `setTarget` is true — and it spawns nothing when the selected field resolves to no class. This single function is the actual implementation backing the base `Teleport`/`Teleport_NoStop`/`TeleportOther` line specials' fog spawning on UZDoom (called from `P_Teleport` at `p_teleport.cpp:204,212`), not an unused alternate path sitting next to the real one.
- `A_Teleport`'s `TF_USEACTORFOG` flag (absent from Zandronum's implementation — see `decorate/actions/a_teleport.md`) routes through this same function instead of the literal `fogtype` class parameter (`src/playsim/p_actionfunctions.cpp:3241-3264`).
- Two action functions, `A_SetTeleFog(class oldpos, class newpos)` and `A_SwapTeleFog()` (`src/playsim/p_actionfunctions.cpp:4482-4509`), plus two ACS extension functions, `SetActorTeleFog(tid, telefogsrc, telefogdest)` and `SwapActorTeleFog(tid)` (`ACSF_SetActorTeleFog`/`ACSF_SwapActorTeleFog`, index 86/87, `src/playsim/p_acs.cpp:5183-5240`), let a mod read or write these fields at runtime.

This is a per-actor customizable fog-class system with no Zandronum counterpart at all — grepping the Zandronum source's `p_acs.cpp` and `actor.h` for `TeleFog` turns up nothing. Practically: a mod targeting UZDoom can give one actor class a different source-teleport fog than its destination fog (or suppress one entirely), all without touching `TeleportFog` itself or any individual `A_Teleport`/`Teleport` call site — the customization axis Zandronum's identical-looking dead code never actually delivered.

## Differences from ZDoom Wiki

- **ZDoom Wiki includes `+ZDOOMTRANS` flag** in the ZScript definition; Zandronum's DECORATE version omits this, as it is a GZDoom-family-specific feature. Confirmed directly against UZDoom's own `teleport.zs` source (not just inferred from the wiki) — UZDoom's `TeleportFog` does carry `+ZDOOMTRANS` (see "Appearance and flags" above).
- **Wiki states target pointer is set on morph** — verified false in Zandronum (see "Target pointer behavior" section), but verified **true** on UZDoom (see "Engine-family divergence: target pointer *is* set on morph fog on UZDoom" above). The wiki's claim was accurate for its own (ZDoom-family) subject all along; it's Zandronum specifically that diverges from it.
