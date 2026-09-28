# `PlayerPawn`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** ZDoom Wiki "Classes:PlayerPawn" (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=Classes%3APlayerPawn&oldid=54208) + verified against the Zandronum source's `src/d_player.h:89-180` (native class definition), `src/thingdef/thingdef_data.cpp` (PlayerPawnFlags table), `src/thingdef/thingdef_properties.cpp` (Player.* properties), and `src/p_user.cpp:979-998` (AddInventory voodoo doll handling). Corrections backed by Zandronum `src/thingdef/thingdef.cpp:142-147` + `src/dobjtype.cpp:209-224,273-283` (duplicate class name), `wadsrc/static/actors/` player class headers (hierarchy), `src/p_mobj.cpp:3378-3379`, `src/p_enemy.cpp:3571`, `src/p_pspr.cpp:978-981,1139`, `src/p_user.cpp:2375,2942`, `src/g_shared/a_morph.cpp:100-108,141-144,181-183` (NOMORPHLIMITATIONS), `src/thingdef/thingdef_properties.cpp:2836-2846` + `src/r_data/sprites.cpp:1363-1400` (MaxSkinSizeFactor), `src/p_mobj.cpp:5746-5763,6058-6060` + `src/p_acs.cpp:5242,5284-5287` (ENTER scripts per start), `src/cooperative.cpp:63-65,150-214`, `src/p_interaction.cpp:1174-1180,1474-1476,1572-1573,800-803`, `src/g_shared/a_pickups.cpp:1107-1137` (online co-op voodoo dolls).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Native C++ base class in Zandronum (`class APlayerPawn : public AActor`, `src/d_player.h:89`); ZScript class in UZDoom (`class PlayerPawn : Actor`, `wadsrc/static/zscript/actors/player/player.zs:35` — no native `APlayerPawn` C++ class exists there at all; `APlayerPawn` only survives as the native-function group name in `DEFINE_ACTION_FUNCTION_NATIVE(APlayerPawn, ...)` bindings for the handful of methods still implemented in C++, e.g. `src/playsim/p_user.cpp:1229`). See "Engine-family divergence: native vs. ZScript implementation" below.

`PlayerPawn` is the engine's built-in base class for all player characters — native C++ on Zandronum, an ordinary ZScript class on UZDoom (see "Engine-family divergence: native vs. ZScript implementation" below). A modder never instantiates this class directly in DECORATE — instead, they inherit from it or from a shipped subclass like `DoomPlayer` to define a custom player character. **Note: this class already exists in the engine; never define a new `ACTOR PlayerPawn` in DECORATE.** Neither engine rejects it outright by default. On Zandronum it is not a parse error: the engine prints a red "Tried to register class 'PlayerPawn' more than once." console message and registers a second, plain `Actor`-derived class under the same name, which later name lookups find ahead of the native one. On UZDoom the ZScript-declared `PlayerPawn` is registered before any DECORATE lump is parsed, and the DECORATE parser warns that the class was defined more than once and renames the new class (a hard error only with `strictdecorate`; `src/scripting/decorate/thingdef_parse.cpp`). For how to define a new player class by inheriting from `PlayerPawn` or `DoomPlayer`, setting `Player.*` properties, and registering it via MAPINFO, see [`../concepts/creating-player-classes.md`](../concepts/creating-player-classes.md).

## Class hierarchy

`AActor` → `APlayerPawn` → shipped subclasses:

- `PlayerChunk` (native `APlayerChunk`; used internally for player gibs/corpses during player death sequences)
- `DoomPlayer` (the Doom/Doom II player character), with `ChexPlayer` (the Chex Quest player character) inheriting from it
- `HereticPlayer` (the Heretic player character)
- `FighterPlayer`, `ClericPlayer`, `MagePlayer` (the three Hexen player classes)
- `StrifePlayer` (the Strife player character)
- `ChickenPlayer`, `PigPlayer` (the Heretic/Hexen morph classes)
- Custom user-defined subclasses (inheriting from `PlayerPawn` directly, or from any of the above)

## Engine-family divergence: native vs. ZScript implementation

Zandronum's `PlayerPawn` is a native C++ class (`class APlayerPawn : public AActor`, `src/d_player.h:89`) — its behavior lives in `.cpp` files, and DECORATE only configures it via `Player.*` properties/flags registered on top.

UZDoom's `PlayerPawn` is a pure ZScript class (`class PlayerPawn : Actor`, `wadsrc/static/zscript/actors/player/player.zs:35`) with no distinct native C++ counterpart. `Tick`, `Die`, `AddInventory`, and most of the class's other behavior are plain ZScript method overrides in that file and its `extend class PlayerPawn` blocks (`player_morph.zs`, `player_cheat.zs`, `player_inventory.zs`). `APlayerPawn` still appears in UZDoom's C++ source, but only as the native-function group name for the handful of methods still implemented in C++ and exposed to the ZScript class via `DEFINE_ACTION_FUNCTION_NATIVE(APlayerPawn, ...)` (e.g. crouch-sprite setup in `src/playsim/p_user.cpp:1229`, weapon-button checks in `src/playsim/p_pspr.cpp:742`) — there is no `class APlayerPawn : public AActor` declaration anywhere in UZDoom's source.

Worth keeping for future porting work: a Zandronum-side `PlayerPawn` behavior change means editing `src/p_user.cpp`/`src/d_player.h`; the equivalent UZDoom change is almost always a ZScript edit in `player.zs` or one of its `extend class` siblings, not a C++ recompile.

## Shipped DECORATE properties and flags

`PlayerPawn` exposes a set of **`Player.*` properties** for configuring player class appearance and mechanics (e.g., `Player.DisplayName`, `Player.ViewHeight`, `Player.JumpZ`, `Player.ColorRange`, `Player.StartItem`). See [`../concepts/creating-player-classes.md`](../concepts/creating-player-classes.md) for the complete property list and their semantics; that document is the canonical reference for player-class configuration and should be read before writing a custom player class.

`PlayerPawn` also exposes four **actor flags** (`+PLAYERPAWN.*`, or their internal `PPF_*` constants) specific to player-class behavior:

- `+PLAYERPAWN.NOTHRUSTWHENINVUL` — When set, the player is not pushed backward by attacks while invulnerable.
- `+PLAYERPAWN.CANSUPERMORPH` — When set on a morphed player class, being remorphed into this class grants a Tome of Power / powerup, reproducing the Heretic super-chicken effect. Not normally used outside of morph attacks.
- `+PLAYERPAWN.CROUCHABLEMORPH` — When set, the morphed player can crouch. By default, morphed players cannot crouch.
- `+PLAYERPAWN.NOMORPHLIMITATIONS` — When set, removes the restrictions normally imposed on morphed players. A morphed player with it plays land/grunt and pain sounds, can switch weapons, is affected by speed powerups and gets view bob, and keeps velocity, pitch and the class's own score icon across the morph.

**Fork divergence (wiki vs. Zandronum):** The ZDoom wiki lists two additional flags (`PLAYERPAWN.WEAPONLEVEL2ENDED` and `PLAYERPAWN.MAKEFOOTSTEPS`) that do not exist in Zandronum's `PlayerPawnFlags` table — they were added later in GZDoom-family development and have no Zandronum equivalent.

Both flags are confirmed present in UZDoom's `PlayerPawn` `flagdef` block (`wadsrc/static/zscript/actors/player/player.zs:112` and `:114`). The reverse also happens: Zandronum's `+PLAYERPAWN.NOMORPHLIMITATIONS` (`DEFINE_FLAG(PPF, NOMORPHLIMITATIONS, APlayerPawn, PlayerFlags)`, `src/thingdef/thingdef_data.cpp:395`) has no UZDoom equivalent at all — it isn't in UZDoom's `PlayerPawn` `flagdef` block, and no other flag or `MRF_*` morph-style flag reproduces its specific effects (lifting the morphed player's restrictions on land and pain sounds, weapon switching, speed powerups and view bob). See "Engine-family divergence: property and flag inventory" below.

## Voodoo dolls

A **voodoo doll** is a vanilla Doom effect (also supported by ZDoom-family engines) where multiple player spawns for the same player number are placed in a map editor, causing multiple `PlayerPawn` actors to be created and bound to the same `PlayerInfo` struct (the engine's per-player state, tracking health, inventory, current weapon, etc.). Each spawn rebinds the player to the actor just spawned, so the player controls the last `PlayerPawn` spawned (the start that comes last in the map's thing list); the earlier ones become voodoo dolls. They exist on the map but do not respond to player input. Zandronum's online co-op handles dolls differently; see "Zandronum-specific: voodoo dolls in online co-op" below.

### Voodoo doll mechanics

A voodoo doll is identified at runtime by checking whether its player-info pointer's `mo` (main object) field points to a different actor than itself: a `PlayerPawn` instance is a voodoo doll if `player != NULL && player->mo != this`. This identity check is the core of the voodoo doll engine behavior:

- **Inventory operations forward to the real player.** When a voodoo doll receives an inventory item (via `A_GiveInventory`, item pickup, etc.), the `AddInventory` method detects this and forwards the item to the real player's `PlayerPawn` instead — identical on both engines: Zandronum's `AddInventory` (`src/p_user.cpp:979-986`) and UZDoom's `PlayerPawn::AddInventory` override (`wadsrc/static/zscript/actors/player/player_inventory.zs:148-156`) both gate on the same `player.mo != self` check before forwarding. This prevents duplication of items across multiple doll instances.
- **Damage and health are shared.** All voodoo dolls of a single player are bound to the same `PlayerInfo`, so damage taken by any doll is reflected in the shared health value and affects all, and a doll's death kills the real player. This is the default on both engines, and on Zandronum it holds offline and for dolls bound to their player (see the online co-op section below for the default online case). UZDoom/GZDoom-family adds an optional opt-out; see "Engine-family divergence: `compat_voodoozombies`" below.
- **The real player's movement and actions are independent from dolls.** The real player's sprite, animation state, and weapon state are controlled by user input. Voodoo dolls remain static (or move via map effects, ACS scripts, or other non-input-driven mechanics).

### DECORATE and scripting concerns

When writing a custom player class or player-related ACS/DECORATE behavior:

- **`ENTER` scripts start once per player start, not once per player.** When a map has several starts for the same player, each start's spawn starts the map's `ENTER` scripts again, with the pawn just spawned as activator, so initialization code (weapon selection, inventory setup, etc.) runs once for every doll as well as for the real player. This applies offline on both engines; Zandronum's online co-op spawns dolls through a separate path (see below). `RESPAWN` scripts are not affected, since a respawn spawns only the one pawn. Guard `ENTER` initialization in ACS by checking the activator, e.g. `if (ClassifyActor(0) & ACTOR_VOODOODOLL) terminate;`.
- **Inventory forwarding is unidirectional for dolls.** A voodoo doll cannot be given inventory directly; items given to it are forwarded to the real player. However, the real player's inventory changes are not automatically synchronized back to the doll's visual representation. Dolls are not gameplay-relevant except as collision objects or targets for ACS/map effects.
- **Voodoo dolls are typically used for map tricks or legacy vanilla Doom effects,** not intentional gameplay mechanics. Modern modding should avoid relying on them.

## Engine-family divergence: `compat_voodoozombies` (voodoo zombies)

UZDoom/GZDoom-family engines add an optional compatibility flag, `COMPATF2_VOODOO_ZOMBIES` (CVAR `compat_voodoozombies`, also bundled into `compatmode 2`'s strict-vanilla preset — `src/d_main.cpp:830-837`), with no Zandronum equivalent. When set, a voodoo doll's death no longer forces the real player to die — normally, killing any doll kills the bound `PlayerInfo` too (`wadsrc/static/zscript/actors/player/player.zs:834-837`) — letting the real player's health diverge from a doll's and survive independently as a "voodoo zombie" (`PF_VOODOO_ZOMBIE`, tracked in `PlayerThink`, `wadsrc/static/zscript/actors/player/player.zs:1686-1689`). It is off by default; a mapper or modder has to opt in via the compat flag or MAPINFO's `compatmode`.

Worth keeping: this is a genuine behavioral option, not just a naming difference — a map or mod relying on "killing a voodoo doll always kills the real player" (the default, and Zandronum's only behavior for a doll bound to its player) needs to know this assumption can be turned off on UZDoom.

## Zandronum-specific: voodoo dolls in online co-op

On a server or in offline multiplayer emulation (anything but plain single player), Zandronum spawns voodoo dolls itself instead of through the map's normal player spawns, and by default does not bind them to their player at all:

- **Dolls exist only in cooperative modes** with `sv_coopspawnvoodoodolls` on (default on). Other online game modes spawn none. Every start of a player except the last becomes a doll.
- **They are server-side only.** A doll gets no net ID, so on a server clients never see it and no per-actor update is ever sent for it.
- **With `sv_coopunassignedvoodoodolls` on (the default), dolls are "unassigned":** they are bound to a dummy player slot that never has a body, not to any real player. `sv_coopunassignedvoodoodollsfornplayers` limits them to the first N player numbers (default all). Consequences:
  - An unassigned doll takes no damage and cannot kill anyone. Damage with both a source and an inflictor still thrusts it (so it can be pushed into line triggers); other damage does nothing.
  - Inventory given to it is not forwarded to any player, because the dummy player has no real pawn to forward to.
  - On the server, an item the doll touches is given to every in-game, non-spectating player, then removed (or hidden for respawn). Weapons and keys picked up this way are remembered and handed to players who join later.
- **With `sv_coopunassignedvoodoodolls` off,** dolls are bound to their player as offline, with shared health, doll death killing the player and inventory forwarding as described above.

## Engine-family divergence: property and flag inventory

**Player.* properties not in Zandronum** (present in ZDoom/GZDoom-family engines; confirmed present in UZDoom's `PlayerPawn` property list, `wadsrc/static/zscript/actors/player/player.zs:104-107` and `:103`):
- `Player.FlyBob` — bob multiplier for flight (GZDoom-era feature)
- `Player.ViewBob` and `Player.ViewBobSpeed` — camera bob multipliers (GZDoom-era additions)
- `Player.TeleportFreezeTime` — duration of post-teleport immobility (GZDoom-era feature)
- `Player.WaterClimbSpeed` — speed while climbing walls underwater (GZDoom-era feature)

**Zandronum-specific additions** (confirmed absent from UZDoom's source — no match anywhere in `wadsrc/`/`src/`):
- `Player.MaxSkinSizeFactor <width>, <height>` — the largest a skin's sprites may be relative to the class's hitbox (width factor times twice the radius, height factor times the height; `PlayerPawn` defaults to `3.44, 1.68`). A larger skin is downsized with a red console message; a factor of 0 disables the check (Zandronum multiplayer feature)
- `+PLAYERPAWN.NOMORPHLIMITATIONS` — removes the restrictions normally imposed on morphed players (land and pain sounds, weapon switching, speed-powerup effects, view bob); no UZDoom equivalent flag or mechanism found

**PlayerPawn flags not in Zandronum** (present in ZDoom/GZDoom-family engines; confirmed present in UZDoom's `PlayerPawn` `flagdef` block, `wadsrc/static/zscript/actors/player/player.zs:112,114`):
- `PLAYERPAWN.WEAPONLEVEL2ENDED` — signals powered-up weapon expiration (internal flag, GZDoom-era)
- `PLAYERPAWN.MAKEFOOTSTEPS` — enables footstep sound effects (GZDoom-era)
