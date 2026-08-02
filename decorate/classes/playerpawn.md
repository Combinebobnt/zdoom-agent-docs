# `PlayerPawn`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki "Classes:PlayerPawn" (retrieved 2026-08-01, oldid=54208) + verified against the Zandronum source's `src/d_player.h:89-180` (native class definition), `src/thingdef/thingdef_data.cpp` (PlayerPawnFlags table), `src/thingdef/thingdef_properties.cpp` (Player.* properties), and `src/p_user.cpp:979-998` (AddInventory voodoo doll handling).
**Bucket:** Native C++ base class. `class APlayerPawn : public AActor`, `src/d_player.h:89`.

`PlayerPawn` is the engine-native base class for all player characters. A modder never instantiates this class directly in DECORATE — instead, they inherit from it or from a shipped subclass like `DoomPlayer` to define a custom player character. **Note: this class already exists in the engine; attempting to define a new `ACTOR PlayerPawn` in DECORATE will cause a parse error.** For how to define a new player class by inheriting from `PlayerPawn` or `DoomPlayer`, setting `Player.*` properties, and registering it via MAPINFO, see [`../concepts/creating-player-classes.md`](../concepts/creating-player-classes.md).

## Class hierarchy

`AActor` → `APlayerPawn` → shipped subclasses:

- `APlayerChunk` (used internally for player gibs/corpses during player death sequences)
- `DoomPlayer` (the Doom/Doom II player character)
- `HereticPlayer` (the Heretic player character)
- `HexenFighter`, `HexenCleric`, `HexenMage` (the three Hexen player classes)
- `StrifePlayer` (the Strife player character)
- `ChexPlayer` (the Chex Quest player character)
- Custom user-defined subclasses (inheriting from `PlayerPawn` directly, or from any of the above)

## Shipped DECORATE properties and flags

`PlayerPawn` exposes a set of **`Player.*` properties** for configuring player class appearance and mechanics (e.g., `Player.DisplayName`, `Player.ViewHeight`, `Player.JumpZ`, `Player.ColorRange`, `Player.StartItem`). See [`../concepts/creating-player-classes.md`](../concepts/creating-player-classes.md) for the complete property list and their semantics; that document is the canonical reference for player-class configuration and should be read before writing a custom player class.

`PlayerPawn` also exposes four **actor flags** (`+PLAYERPAWN.*`, or their internal `PPF_*` constants) specific to player-class behavior:

- `+PLAYERPAWN.NOTHRUSTWHENINVUL` — When set, the player is not pushed backward by attacks while invulnerable.
- `+PLAYERPAWN.CANSUPERMORPH` — When set on a morphed player class, being remorphed into this class grants a Tome of Power / powerup, reproducing the Heretic super-chicken effect. Not normally used outside of morph attacks.
- `+PLAYERPAWN.CROUCHABLEMORPH` — When set, the morphed player can crouch. By default, morphed players cannot crouch.
- `+PLAYERPAWN.NOMORPHLIMITATIONS` — When set, removes several restrictions normally imposed on morphed players, such as disabling land/footstep sounds, weapon switching, or speed powerup effects.

**Fork divergence (wiki vs. Zandronum):** The ZDoom wiki lists two additional flags (`PLAYERPAWN.WEAPONLEVEL2ENDED` and `PLAYERPAWN.MAKEFOOTSTEPS`) that do not exist in Zandronum's `PlayerPawnFlags` table — they were added later in GZDoom-family development and have no Zandronum equivalent.

## Voodoo dolls

A **voodoo doll** is a vanilla Doom effect (also supported by ZDoom-family engines) where multiple player spawns for the same player number are placed in a map editor, causing multiple `PlayerPawn` actors to be created and bound to the same `PlayerInfo` struct (the engine's per-player state, tracking health, inventory, current weapon, etc.). The player can only directly control the first `PlayerPawn` actor spawned; additional spawns become voodoo dolls — they exist on the map but do not respond to player input.

### Voodoo doll mechanics

A voodoo doll is identified at runtime by checking whether its player-info pointer's `mo` (main object) field points to a different actor than itself: a `PlayerPawn` instance is a voodoo doll if `player != NULL && player->mo != this`. This identity check is the core of the voodoo doll engine behavior:

- **Inventory operations forward to the real player.** When a voodoo doll receives an inventory item (via `A_GiveInventory`, item pickup, etc.), the `AddInventory` method (in `src/p_user.cpp:979-986`) detects this and forwards the item to the real player's `PlayerPawn` instead. This prevents duplication of items across multiple doll instances.
- **Damage and health are shared.** All voodoo dolls of a single player are bound to the same `PlayerInfo`, so damage taken by any doll is reflected in the shared health value and affects all.
- **The real player's movement and actions are independent from dolls.** The real player's sprite, animation state, and weapon state are controlled by user input. Voodoo dolls remain static (or move via map effects, ACS scripts, or other non-input-driven mechanics).

### DECORATE and scripting concerns

When writing a custom player class or player-related ACS/DECORATE behavior:

- **Multiple `PlayerPawn` instances for one player will all execute per-map scripts.** If a map contains multiple player spawns for the same player and a DECORATE actor definition or ACS script uses an event like `ENTER` or `RESPAWN` to initialize player state (weapon selection, inventory setup, etc.), the code will run once per voodoo doll. This can cause unintended duplication. A common solution is to guard initialization code with a check: in ACS, use `Thing_Count(THING_PlayerPawn, TID)` or similar; in DECORATE, avoid startup-only code or check via a custom flag.
- **Inventory forwarding is unidirectional for dolls.** A voodoo doll cannot be given inventory directly; items given to it are forwarded to the real player. However, the real player's inventory changes are not automatically synchronized back to the doll's visual representation. Dolls are not gameplay-relevant except as collision objects or targets for ACS/map effects.
- **Voodoo dolls are typically used for map tricks or legacy vanilla Doom effects,** not intentional gameplay mechanics. Modern modding should avoid relying on them.

## Fork divergence summary

**Player.* properties not in Zandronum** (present in ZDoom/GZDoom-family engines):
- `Player.FlyBob` — bob multiplier for flight (GZDoom-era feature)
- `Player.ViewBob` and `Player.ViewBobSpeed` — camera bob multipliers (GZDoom-era additions)
- `Player.TeleportFreezeTime` — duration of post-teleport immobility (GZDoom-era feature)
- `Player.WaterClimbSpeed` — speed while climbing walls underwater (GZDoom-era feature)

**Zandronum-specific additions:**
- `Player.MaxSkinSizeFactor` — scale multiplier for a player skin's sprite size (Zandronum multiplayer feature)

**PlayerPawn flags not in Zandronum** (present in ZDoom/GZDoom-family engines):
- `PLAYERPAWN.WEAPONLEVEL2ENDED` — signals powered-up weapon expiration (internal flag, GZDoom-era)
- `PLAYERPAWN.MAKEFOOTSTEPS` — enables footstep sound effects (GZDoom-era)
