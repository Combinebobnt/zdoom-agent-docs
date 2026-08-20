# Creating player classes

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki "Creating new player classes" (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=Creating_new_player_classes&oldid=52200), verified against the Zandronum source's DECORATE actor definition examples (`wadsrc/static/actors/doom/doomplayer.txt`), `Player.*` property definitions (`src/thingdef/thingdef_properties.cpp:2254-2836`), MAPINFO parser (`src/gi.cpp:330-331`), KEYCONF command definitions (`src/p_user.cpp:233-241`), and multiplayer player-class selection mechanism (`src/d_netinfo.cpp`, `src/menu/multiplayermenu.cpp`, `src/menu/menudef.cpp:1164-1257`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

Player classes allow a game to define multiple player character variants (different sprites, stats, weapon sets, appearance) selectable by the player, either at new-game startup (single-player) or when joining a game (multiplayer). This page covers the DECORATE/ZScript-side mechanisms — actor definition and property configuration — shared across both UZDoom and Zandronum, with special attention to the multiplayer workflow that the wiki's single-player focus omits.

## Defining a player class in DECORATE

A player class is defined by creating a new DECORATE actor inheriting from `PlayerPawn` or a subclass like `DoomPlayer` (the shipped Doom player character; defined in `wadsrc/static/actors/doom/doomplayer.txt` on Zandronum or in `wadsrc/static/zscript/actors/doom/doomplayer.zs` on UZDoom):

```text
actor MyCustomPlayer : DoomPlayer
{
  Health 120
  Player.DisplayName "Custom Marine"
  Player.ColorRange 128, 143
  Player.StartItem "Pistol"
  States
  {
  ...
  }
}
```

Any actor inheriting from `PlayerPawn` is a valid player class. The choice of which parent class to inherit from is a matter of code reuse and customization level:

- **Inheriting from `DoomPlayer`** — Reuses all the Doom player's sprites, weapon slots, sounds, and mechanics. Best for minor variants (palette swaps, tweaked health/speed).
- **Inheriting from a different shipped player class** (e.g. `HereticPlayer`, `HexenFighter`) — Reuses a different game's player base.
- **Inheriting from the bare `PlayerPawn`** class directly — Requires explicitly defining all required properties, sounds, weapon slots, and states. Only necessary if none of the shipped bases are suitable.

## Configuring the player class: `Player.*` properties

Beyond the basic actor properties (`Health`, `Radius`, `Height`, `Speed`, etc.), player classes use a set of DECORATE properties prefixed `Player.` to configure character-specific behavior and appearance. The most commonly used are:

**Display and identity:**
- **`Player.DisplayName "<string>"`** — The name shown in the player-class selection menu(s) and player-setup interface. The display name is looked up by string matching, so it must be unique across all defined player classes (Zandronum searches `PlayerClasses.Type->Meta.GetMetaString(APMETA_DisplayName)`, `src/d_netinfo.cpp:323`). Required; a player class without a display name will be rejected during setup (`src/p_user.cpp:204`).
- **`Player.ColorRange <first>, <last>`** — Defines a range of palette indices to use for player color (palette swap). This is used by the player-color selection menu and the `Color` userinfo field. The first index is the start of the color range; the last index is the end (inclusive). Example: `Player.ColorRange 112, 127` uses a 16-color range starting at index 112.
- **`Player.Colorset <index>, "<name>", <start>, <end>, <representative-color>`** — Predefined color translations by name, allowing the player-setup menu to offer discrete color choices by name (e.g., "Red", "Blue", "Green") instead of a continuous palette range. Optional extra palette ranges can be added as additional `<range-start>, <range-end>, <color-start>, <color-end>` tuples. Not required if using `Player.ColorRange` alone.

**Gameplay mechanics:**
- **`Player.StartItem "<itemtype>"` or `Player.StartItem "<itemtype>", <amount>`** — Adds an item (weapon, ammo, powerup) to the player's initial inventory on spawn. Can be repeated; multiple `Player.StartItem` lines stack. Example: `Player.StartItem "Pistol"` starts with a pistol; `Player.StartItem "Clip", 50` starts with 50 bullets.
- **`Player.WeaponSlot <slot>, <weapon1>, <weapon2>, ...`** — Assigns weapons to inventory slots (0–9) for quick access. Example: `Player.WeaponSlot 1, Fist, Chainsaw` puts the Fist and Chainsaw in slot 1.
- **`Player.ViewHeight <units>`** — The camera height when standing. Defaults to 41 units; humanoid players typically use 41–56.
- **`Player.MaxHealth <hitpoints>`** — The maximum health the player can reach with powerups (not the `Health` property, which is the initial health). If not set, defaults to 100 (or a compatibility-mode dependent value in DEHACKED compatibility mode).
- **`Player.JumpZ <units>`** — Jump force; higher values allow higher jumps (only used if jumping is enabled via server flags or MAPINFO).

**Audio and miscellaneous:**
- **`Player.SoundClass "<classname>"`** — The sound class used for player damage sounds, footsteps, etc. (e.g., `"marine"`, `"baby"`). Must match one of the sound classes defined in `SNDINFO` lump. Not directly visible to the player but affects audio playback.
- **`Player.CrouchSprite "<spriteletter>"`** — The sprite prefix to use while crouching (e.g., `"PLYC"` for the crouching Doom player). Only relevant if the `+CROUCHING` actor flag is enabled.
- **`Player.SpawnClass "<className>"`** — If set, causes this player to spawn a morphing spawner of the specified actor type instead of the player itself at level start. Rarely used.

For the complete list of `Player.*` properties, see the Zandronum source `src/thingdef/thingdef_properties.cpp:2254-2836`.

## Making the player class available: MAPINFO configuration

Once a player class is defined in DECORATE, the game must be told to include it in the available player-class list. This is done via the `GameInfo` section of a MAPINFO lump:

```text
GameInfo
{
  PlayerClasses = "MyCustomPlayer", "DoomPlayer"
}
```

The `PlayerClasses` key accepts a comma-separated list of actor class names. The order in the list determines the order they appear in the player-class selection menu. Examples:

- `PlayerClasses = "DoomPlayer"` — Single player class; no selection menu appears (the player is automatically assigned this class).
- `PlayerClasses = "MyClass1", "MyClass2", "DoomPlayer"` — Three player classes; a selection menu appears at new-game startup or on multiplayer join.

The `PlayerClasses` key lives in the **`GameInfo` block of the MAPINFO lump**, not in any specific map's `Map` block — it is a global game-configuration setting, not per-map.

**MAPINFO parsing:** The key is registered as `playerclasses` (case-insensitive) in the MAPINFO parser's `GameInfo` keyword table (`src/gi.cpp:331`). Both `playerclasses` and the deprecated `addplayerclasses` keyword are accepted; the parser converts them to entries in the `gameinfo.PlayerClasses` string array, which is read at startup by `SetupPlayerClasses()` (`src/p_user.cpp:212`).

**Shipped default:** The Doom game definition (`wadsrc/static/mapinfo/doomcommon.txt`) sets `playerclasses = "DoomPlayer"` as the default; Heretic, Hexen, and Strife define their own respective defaults in their MAPINFO files.

## Hiding a player class from menus: the `+NOMENU` flag

A player class can be defined and included in `PlayerClasses` but hidden from the player-class selection menu by setting the `+NOMENU` actor flag (equivalent to `MF6_NOMENU` in C++ source, `src/actor.h:329`):

```text
actor HiddenClass : DoomPlayer
{
  +NOMENU
  ...
}
```

When `+NOMENU` is set, the class is technically available but does not appear in any player-class selection menu. It can only be assigned via console commands (e.g., `set playerclass <classname>`) or programmatically. This is useful for special modes, debug classes, or classes that should only be selectable in specific game configurations.

The shipped code checks this flag and applies the `PCF_NOMENU` per-class flag when setting up the player-class list (`src/p_user.cpp:224-226`).

## Deprecated: KEYCONF-based class setup (backward compatibility)

Older ZDoom versions (predating MAPINFO's `PlayerClasses` key) used console commands in KEYCONF to manage player classes:

```text
clearplayerclasses
addplayerclass DoomPlayer
addplayerclass MyCustomPlayer
```

These commands (`clearplayerclasses`, `addplayerclass`) are still supported in Zandronum for backward compatibility and work only when parsing KEYCONF (`src/p_user.cpp:233-262`). **The MAPINFO approach is preferred** and is the method all shipped game definitions use; the KEYCONF method is deprecated in the sense that no new projects should rely on it, though it is not removed from the engine.

## Single-player vs. multiplayer player-class selection

Both UZDoom and Zandronum implement player-class selection differently in single-player vs. multiplayer contexts:

**Single-player (new-game menu):** When starting a new game in single-player:
1. After choosing "New Game" from the main menu.
2. If there are 2 or more player classes defined, a player-class selection menu appears.
3. The player selects a class, then proceeds to the skill-level selection.
4. The selected class is used for the level (until restarted or changed via console).

**Multiplayer (userinfo-based):** In multiplayer games:
- Player class is stored as a **`playerclass` userinfo cvar** — a network-synchronized player property like `name`, `skin`, or `color`, not selected during a new-game flow. On Zandronum, this is registered at `src/d_netinfo.cpp:90`; on UZDoom, at `src/d_netinfo.cpp:60`.
- The player class takes effect **at spawn/respawn time**: when the player joins the server or respawns, the server looks up the player's `CurrentPlayerClass` from userinfo and spawns the corresponding `PlayerPawn` actor.
- The class **remains in effect for the duration of the game or until explicitly changed** via the player-setup menu, console command, or explicit userinfo update. **Mid-game class switching is possible** if the player changes their `playerclass` userinfo during play; the change takes effect at the next respawn (though the exact code path from menu selection or console command to the spawn-side consumer remains incompletely traced in both engines).
- A **multiplayer "join game" menu** offers a class selector when the player is about to join, allowing class selection as part of the join process.

This design allows multiplayer servers to enforce player-class restrictions, track which classes are in use, and handle dynamic class changes as part of the player-state synchronization protocol.

## Engine-family divergence

**DECORATE vs. ZScript:** Zandronum uses DECORATE syntax for player-class definition (`wadsrc/static/actors/...`). UZDoom, beginning with its ZScript integration, defines the shipped player classes in ZScript (`wadsrc/static/zscript/actors/...`). The underlying `Player.*` property names and behavior are identical across both languages; the difference is syntactic (DECORATE `property` declarations in UZDoom's ZScript vs. DECORATE keyword blocks in Zandronum). Custom player classes in UZDoom can still be defined in DECORATE and will parse correctly alongside ZScript classes.

## Open questions (unverified in this checkout — don't guess past these)

- **How exactly is a class changed mid-game in multiplayer?** The code path from menu selection or console `set playerclass` to the next respawn with the new class is not fully traced in either engine. Specifically: does the new class take effect immediately if the player is already alive, or only on the next respawn? Is there a server-side throttle or validation of class changes during active play?
- **Does the shipped class-selection menu support `+NOMENU` classes?** Both engines check the `PCF_NOMENU` flag and exclude such classes from the menu, but whether this flag is separately settable in DECORATE (beyond automatically inheriting from the actor's `MF6_NOMENU` flag) is not verified.
- **Zandronum-fork-specific class-handling cvars?** This checkout has `sv_forcerandomclass` and `gameinfo.norandomplayerclass` visible. There may be other server-side cvars affecting class selection or availability that aren't documented here.
