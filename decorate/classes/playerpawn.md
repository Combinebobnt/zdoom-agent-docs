# `PlayerPawn`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki "Classes:PlayerPawn" (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=Classes%3APlayerPawn&oldid=54208) + verified against the Zandronum source's `src/d_player.h:89-180` (native class definition), `src/thingdef/thingdef_data.cpp` (PlayerPawnFlags table), `src/thingdef/thingdef_properties.cpp` (Player.* properties), and `src/p_user.cpp:979-998` (AddInventory voodoo doll handling).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Native C++ base class in Zandronum (`class APlayerPawn : public AActor`, `src/d_player.h:89`); ZScript class in UZDoom (`class PlayerPawn : Actor`, `wadsrc/static/zscript/actors/player/player.zs:35` — no native `APlayerPawn` C++ class exists there at all; `APlayerPawn` only survives as the native-function group name in `DEFINE_ACTION_FUNCTION_NATIVE(APlayerPawn, ...)` bindings for the handful of methods still implemented in C++, e.g. `src/playsim/p_user.cpp:1229`). See "Engine-family divergence: native vs. ZScript implementation" below.

`PlayerPawn` is the engine's built-in base class for all player characters — native C++ on Zandronum, an ordinary ZScript class on UZDoom (see "Engine-family divergence: native vs. ZScript implementation" below). A modder never instantiates this class directly in DECORATE — instead, they inherit from it or from a shipped subclass like `DoomPlayer` to define a custom player character. **Note: this class already exists in the engine; attempting to define a new `ACTOR PlayerPawn` in DECORATE will cause a parse error on both engines** (UZDoom's DECORATE-compatibility parser reports its own "already defined" error — `src/scripting/decorate/thingdef_parse.cpp` — since the ZScript-declared `PlayerPawn` class is registered before any DECORATE lump is parsed). For how to define a new player class by inheriting from `PlayerPawn` or `DoomPlayer`, setting `Player.*` properties, and registering it via MAPINFO, see [`../concepts/creating-player-classes.md`](../concepts/creating-player-classes.md).

## Class hierarchy

`AActor` → `APlayerPawn` → shipped subclasses:

- `APlayerChunk` (used internally for player gibs/corpses during player death sequences)
- `DoomPlayer` (the Doom/Doom II player character)
- `HereticPlayer` (the Heretic player character)
- `HexenFighter`, `HexenCleric`, `HexenMage` (the three Hexen player classes)
- `StrifePlayer` (the Strife player character)
- `ChexPlayer` (the Chex Quest player character)
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
- `+PLAYERPAWN.NOMORPHLIMITATIONS` — When set, removes several restrictions normally imposed on morphed players, such as disabling land/footstep sounds, weapon switching, or speed powerup effects.

**Fork divergence (wiki vs. Zandronum):** The ZDoom wiki lists two additional flags (`PLAYERPAWN.WEAPONLEVEL2ENDED` and `PLAYERPAWN.MAKEFOOTSTEPS`) that do not exist in Zandronum's `PlayerPawnFlags` table — they were added later in GZDoom-family development and have no Zandronum equivalent.

Both flags are confirmed present in UZDoom's `PlayerPawn` `flagdef` block (`wadsrc/static/zscript/actors/player/player.zs:112` and `:114`). The reverse also happens: Zandronum's `+PLAYERPAWN.NOMORPHLIMITATIONS` (`DEFINE_FLAG(PPF, NOMORPHLIMITATIONS, APlayerPawn, PlayerFlags)`, `src/thingdef/thingdef_data.cpp:395`) has no UZDoom equivalent at all — it isn't in UZDoom's `PlayerPawn` `flagdef` block, and no other flag or `MRF_*` morph-style flag reproduces its specific effects (disabling land/footstep sounds, weapon switching, or speed-powerup restrictions while morphed). See "Engine-family divergence: property and flag inventory" below.

## Voodoo dolls

A **voodoo doll** is a vanilla Doom effect (also supported by ZDoom-family engines) where multiple player spawns for the same player number are placed in a map editor, causing multiple `PlayerPawn` actors to be created and bound to the same `PlayerInfo` struct (the engine's per-player state, tracking health, inventory, current weapon, etc.). The player can only directly control the first `PlayerPawn` actor spawned; additional spawns become voodoo dolls — they exist on the map but do not respond to player input.

### Voodoo doll mechanics

A voodoo doll is identified at runtime by checking whether its player-info pointer's `mo` (main object) field points to a different actor than itself: a `PlayerPawn` instance is a voodoo doll if `player != NULL && player->mo != this`. This identity check is the core of the voodoo doll engine behavior:

- **Inventory operations forward to the real player.** When a voodoo doll receives an inventory item (via `A_GiveInventory`, item pickup, etc.), the `AddInventory` method detects this and forwards the item to the real player's `PlayerPawn` instead — identical on both engines: Zandronum's `AddInventory` (`src/p_user.cpp:979-986`) and UZDoom's `PlayerPawn::AddInventory` override (`wadsrc/static/zscript/actors/player/player_inventory.zs:148-156`) both gate on the same `player.mo != self` check before forwarding. This prevents duplication of items across multiple doll instances.
- **Damage and health are shared.** All voodoo dolls of a single player are bound to the same `PlayerInfo`, so damage taken by any doll is reflected in the shared health value and affects all — true on both engines by default. UZDoom/GZDoom-family adds an optional opt-out; see "Engine-family divergence: `compat_voodoozombies`" below.
- **The real player's movement and actions are independent from dolls.** The real player's sprite, animation state, and weapon state are controlled by user input. Voodoo dolls remain static (or move via map effects, ACS scripts, or other non-input-driven mechanics).

### DECORATE and scripting concerns

When writing a custom player class or player-related ACS/DECORATE behavior:

- **Multiple `PlayerPawn` instances for one player will all execute per-map scripts.** If a map contains multiple player spawns for the same player and a DECORATE actor definition or ACS script uses an event like `ENTER` or `RESPAWN` to initialize player state (weapon selection, inventory setup, etc.), the code will run once per voodoo doll. This can cause unintended duplication. A common solution is to guard initialization code with a check: in ACS, use `Thing_Count(THING_PlayerPawn, TID)` or similar; in DECORATE, avoid startup-only code or check via a custom flag.
- **Inventory forwarding is unidirectional for dolls.** A voodoo doll cannot be given inventory directly; items given to it are forwarded to the real player. However, the real player's inventory changes are not automatically synchronized back to the doll's visual representation. Dolls are not gameplay-relevant except as collision objects or targets for ACS/map effects.
- **Voodoo dolls are typically used for map tricks or legacy vanilla Doom effects,** not intentional gameplay mechanics. Modern modding should avoid relying on them.

## Engine-family divergence: `compat_voodoozombies` (voodoo zombies)

UZDoom/GZDoom-family engines add an optional compatibility flag, `COMPATF2_VOODOO_ZOMBIES` (CVAR `compat_voodoozombies`, also bundled into `compatmode 2`'s strict-vanilla preset — `src/d_main.cpp:830-837`), with no Zandronum equivalent. When set, a voodoo doll's death no longer forces the real player to die — normally, killing any doll kills the bound `PlayerInfo` too (`wadsrc/static/zscript/actors/player/player.zs:834-837`) — letting the real player's health diverge from a doll's and survive independently as a "voodoo zombie" (`PF_VOODOO_ZOMBIE`, tracked in `PlayerThink`, `wadsrc/static/zscript/actors/player/player.zs:1686-1689`). It is off by default; a mapper or modder has to opt in via the compat flag or MAPINFO's `compatmode`.

Worth keeping: this is a genuine behavioral option, not just a naming difference — a map or mod relying on "killing a voodoo doll always kills the real player" (the default, and the only behavior Zandronum has) needs to know this assumption can be turned off on UZDoom.

## Engine-family divergence: property and flag inventory

**Player.* properties not in Zandronum** (present in ZDoom/GZDoom-family engines; confirmed present in UZDoom's `PlayerPawn` property list, `wadsrc/static/zscript/actors/player/player.zs:104-107` and `:103`):
- `Player.FlyBob` — bob multiplier for flight (GZDoom-era feature)
- `Player.ViewBob` and `Player.ViewBobSpeed` — camera bob multipliers (GZDoom-era additions)
- `Player.TeleportFreezeTime` — duration of post-teleport immobility (GZDoom-era feature)
- `Player.WaterClimbSpeed` — speed while climbing walls underwater (GZDoom-era feature)

**Zandronum-specific additions** (confirmed absent from UZDoom's source — no match anywhere in `wadsrc/`/`src/`):
- `Player.MaxSkinSizeFactor` — scale multiplier for a player skin's sprite size (Zandronum multiplayer feature)
- `+PLAYERPAWN.NOMORPHLIMITATIONS` — removes several restrictions normally imposed on morphed players (land/footstep sounds, weapon switching, speed-powerup effects); no UZDoom equivalent flag or mechanism found

**PlayerPawn flags not in Zandronum** (present in ZDoom/GZDoom-family engines; confirmed present in UZDoom's `PlayerPawn` `flagdef` block, `wadsrc/static/zscript/actors/player/player.zs:112,114`):
- `PLAYERPAWN.WEAPONLEVEL2ENDED` — signals powered-up weapon expiration (internal flag, GZDoom-era)
- `PLAYERPAWN.MAKEFOOTSTEPS` — enables footstep sound effects (GZDoom-era)
