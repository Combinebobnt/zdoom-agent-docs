# SBARINFO lump format overview

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `SBARINFO` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=SBARINFO&oldid=53445) + verified against Zandronum source's `src/g_shared/sbarinfo.cpp`, `src/g_shared/sbarinfo_commands.cpp`, and `src/g_shared/sbar_mugshot.cpp` (3.3-alpha).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

SBARINFO is a declarative format for defining custom status bars and mugshot animations in Zandronum. **In Zandronum, SBARINFO is the primary (and only) custom HUD mechanism — it is not deprecated.** The GZDoom-family engines have moved to ZScript-based HUDs; this distinction is critical for Zandronum projects. ZScript does not exist in Zandronum and no `StatusBarClass` MAPINFO key exists.

## Lump semantics

- Multiple SBARINFO lumps are all read and merged (not "only the last"); the Zandronum source (`src/g_shared/sbarinfo.cpp:452-463`) calls `Wads.FindLump` in a loop, processing each found lump.
- Files can be included via `#include "filename"` syntax (identical to DECORATE); the recursive parse call at line 483 handles this.
- Image names must be quoted; names longer than 8 characters require the full `"graphics/longname"` form.
- Empty images (for "off" states in weapon/item indicators) use `""` or `"nullimage"` (except `DrawMugShot`'s default argument).

## Mugshot scripting

Mugshots can be defined independently and used with the default Doom status bar without defining any custom status bar blocks. A mugshot is a scriptable animation with named states; each state contains frame definitions with durations (positive tics, or `-1` for infinite):

- **State names:** `Normal`, `Pain`, `Ouch`, `Rampage`, `Grin`, `Death`, `XDeath`, `God`, `GodAnimated`, plus custom damage-type variants (e.g. `Pain.FireDamage`). Zandronum additionally supports a `Quad` state (activated when the player has Quad Damage powerup) that UZDoom does not.
- **Rampage trigger:** The Rampage state activates when the player holds a fire button (checked via the `attackdown` field) and has a ready weapon for `ST_RAMPAGEDELAY` tics (70 tics). Both Zandronum and UZDoom implement this identically via the same `attackdown` check, though the wiki may describe it using ZScript-family terminology.
- **Flags:** `health` / `health2` / `healthspecial` apply damage type (character suffix determines health level); `directional` picks one of three frames based on damage direction.
- **State-setting:** The ACS function `SetMugShotState(string statename)` (PCD_SETMUGSHOTSTATE, `src/p_acs.cpp:12743`) changes the active mugshot state at runtime.

## Status bar blocks and drawing commands

Top-level configuration commands shared by both engines include `Base`, `Height`, `InterpolateHealth`, `InterpolateArmor`, `CompleteBorder`, `MonospaceFonts`, `LowerHealthCap`, `Resolution`, `StatusBar`, and `CreatePopup`; Zandronum adds `appendstatusbar`, and UZDoom adds `protrusion`. Drawing commands within a `StatusBar` block include `Alpha`, `AspectRatio`, `DrawBar`, `DrawGem`, `DrawKeyBar`, `DrawImage`, `DrawMugShot`, `DrawNumber`, `DrawSelectedInventory`, `DrawShader`, `DrawString`, `DrawSwitchableImage`, plus conditionals `GameMode`, `PlayerClass`, `PlayerType`, `IsSelected`, `UsesAmmo`, `UsesSecondaryAmmo`, `HasWeaponPiece`, `WeaponAmmo`, `InInventory`, `IfHealth`, and `InventoryBarNotVisible`.

**Wiki-to-Zandronum divergence:** The wiki lists `IfCVarInt`, `IfInvulnerable`, `IfWaterLevel` — these exist in UZDoom but not in Zandronum — and `Else` (parsed as a keyword in flow-control parsing but not listed as a standalone command). Zandronum adds multiplayer-specific conditionals `IfSpectator` and `IfSpying` not mentioned on the wiki.

## Coordinate and resolution semantics

The base resolution defaults to 320×200. Commands can use relative centering (e.g. `x, y+center` in fullscreen mode). The `FullScreenOffsets` flag on a `StatusBar` line applies special coordinate handling for fullscreen HUDs.

## Engine-family divergence

"GZDoom-family engines have moved to ZScript-based HUDs" (above) describes which mechanism is
*preferred* there, not that SBARINFO stopped existing. The UZDoom source still parses and renders
SBARINFO lumps (`src/g_statusbar/sbarinfo.cpp`, `src/g_statusbar/sbarinfo_commands.cpp`), and the
`gameinfo` block's `statusbar` key still resolves to a status-bar lump file the same way it does on Zandronum. A GZDoom-family engine simply also offers
a second, newer path Zandronum lacks: a ZScript `StatusBarClass` (set via the `statusBarClass`
`gameinfo` key, absent in Zandronum — see [GameInfo block
structure](../../mapinfo/concepts/gameinfo-block.md)) that replaces the built-in status bar with a
custom ZScript class instead of an SBARINFO lump. SBARINFO and a ZScript status bar class are
alternative mechanisms selecting the same slot, not a deprecated format and its replacement — a
PK3 targeting both engines can still ship one SBARINFO lump and have it work everywhere.

### Command and conditional divergences

Beyond the core SBARINFO mechanism, specific commands diverge:

- **Top-level commands:** Zandronum includes `appendstatusbar` (for additive status bar loading), while UZDoom includes `protrusion` (for status bar protrusion effects).
- **Conditional flow-control:** Zandronum includes the multiplayer-specific conditionals `IfSpectator` and `IfSpying` (checking player spectation and spying state), while UZDoom includes `IfCVarInt`, `IfInvulnerable`, and `IfWaterLevel` (checking console variable integers, invulnerability status, and water level respectively).

### Mugshot state divergence

Zandronum includes a `quad` state (activated when the player has the Quad Damage artifact — `PowerQuadDamage` or the terminator artifact powerup) that UZDoom does not. Additionally, in Zandronum, the rampage face state suppresses when the player is spectating; UZDoom does not perform this check, so rampage can display for spectators.
