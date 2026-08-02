# SBARINFO lump format overview

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `SBARINFO` (retrieved 2026-07-31, oldid=53445) + verified against Zandronum source's `src/g_shared/sbarinfo.cpp`, `src/g_shared/sbarinfo_commands.cpp`, and `src/g_shared/sbar_mugshot.cpp` (3.3-alpha).

SBARINFO is a declarative format for defining custom status bars and mugshot animations in Zandronum. **In Zandronum, SBARINFO is the primary (and only) custom HUD mechanism — it is not deprecated.** The GZDoom-family engines have moved to ZScript-based HUDs; this distinction is critical for Zandronum projects. ZScript does not exist in Zandronum and no `StatusBarClass` MAPINFO key exists.

## Lump semantics

- Multiple SBARINFO lumps are all read and merged (not "only the last"); the Zandronum source (`src/g_shared/sbarinfo.cpp:452-463`) calls `Wads.FindLump` in a loop, processing each found lump.
- Files can be included via `#include "filename"` syntax (identical to DECORATE); the recursive parse call at line 483 handles this.
- Image names must be quoted; names longer than 8 characters require the full `"graphics/longname"` form.
- Empty images (for "off" states in weapon/item indicators) use `""` or `"nullimage"` (except `DrawMugShot`'s default argument).

## Mugshot scripting

Mugshots can be defined independently and used with the default Doom status bar without defining any custom status bar blocks. A mugshot is a scriptable animation with named states; each state contains frame definitions with durations (positive tics, or `-1` for infinite):

- **State names:** `Normal`, `Pain`, `Ouch`, `Rampage`, `Grin`, `Death`, `XDeath`, `God`, `GodAnimated`, plus custom damage-type variants (e.g. `Pain.FireDamage`).
- **Rampage trigger:** In Zandronum, the Rampage state activates when the player holds down a fire button and has a ready weapon for `ST_RAMPAGEDELAY` tics (70 tics per the Zandronum source `src/g_shared/sbar_mugshot.cpp:268-278`). The wiki describes this using ZScript-family terminology (`attackdown` field) which does not apply to Zandronum; the mechanism exists in both but the implementation differs.
- **Flags:** `health` / `health2` / `healthspecial` apply damage type (character suffix determines health level); `directional` picks one of three frames based on damage direction.
- **State-setting:** The ACS function `SetMugShotState(string statename)` (PCD_SETMUGSHOTSTATE, `src/p_acs.cpp:12743`) changes the active mugshot state at runtime.

## Status bar blocks and drawing commands

Top-level configuration commands include `Base`, `Height`, `InterpolateHealth`, `InterpolateArmor`, `CompleteBorder`, `MonospaceFonts`, `LowerHealthCap`, `Resolution`, `StatusBar`, and `CreatePopup`. Drawing commands within a `StatusBar` block include `Alpha`, `AspectRatio`, `DrawBar`, `DrawGem`, `DrawKeyBar`, `DrawImage`, `DrawMugShot`, `DrawNumber`, `DrawSelectedInventory`, `DrawShader`, `DrawString`, `DrawSwitchableImage`, plus conditionals `GameMode`, `PlayerClass`, `PlayerType`, `IsSelected`, `UsesAmmo`, `UsesSecondaryAmmo`, `HasWeaponPiece`, `WeaponAmmo`, `InInventory`, `IfHealth`, and `InventoryBarNotVisible`.

**Wiki-to-Zandronum divergence:** The wiki lists `IfCVarInt`, `IfInvulnerable`, `IfWaterLevel` (not present in Zandronum), and `Else` (parsed as a keyword but not listed in the command table). Zandronum adds multiplayer-specific conditionals `IfSpectator` and `IfSpying` not mentioned on the wiki.

## Coordinate and resolution semantics

The base resolution defaults to 320×200. Commands can use relative centering (e.g. `x, y+center` in fullscreen mode). The `FullScreenOffsets` flag on a `StatusBar` line applies special coordinate handling for fullscreen HUDs.

