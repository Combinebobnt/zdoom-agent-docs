# BaseStatusBar and StatusBarCore

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki `Classes:BaseStatusBar` (retrieved 2026-08-03, https://zdoom.org/w/index.php?title=Classes%3ABaseStatusBar&oldid=55287) + verified against UZDoom source at `wadsrc/static/zscript/ui/statusbar/statusbar.zs` and `wadsrc/static/zscript/engine/ui/statusbar/statusbarcore.zs`; re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — no behavioral drift found.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

The base class for all HUD implementations in ZScript. Despite its name, `BaseStatusBar` handles drawing both status-bar-style HUDs (covering the bottom of the screen) and fullscreen HUDs (covering the entire screen). It does not handle GZDoom's alternate HUD (see the wiki's AltHUD page for that).

## StatusBarCore vs. BaseStatusBar

`StatusBarCore` is a separate engine-provided class containing most of the drawing functions and constants. In UZDoom, `StatusBarCore` exists primarily to share code with the Raze engine and serves as the base for `BaseStatusBar` — you can access static methods and constants through either `StatusBarCore.` or `BaseStatusBar.` or the global `statusbar` pointer. In practice, they form one logical unit for documentation purposes.

## Accessing the HUD from gameplay code

The global variable `statusbar` holds a pointer to the current HUD instance. This allows:

- **Event handlers:** Use `RenderOverlay()` or `RenderUnderlay()` virtual methods in an `EventHandler` to access HUD drawing functions via the `statusbar` global.
- **Play-scope interaction:** Use an `EventHandler` with an `InterfaceProcess` override to interact with the HUD from play scope (the scope where actors and scripts run).

## Virtual resolution and coordinate system

`BaseStatusBar` maintains a virtual resolution separate from the actual screen resolution. This allows HUDs to scale consistently across different monitor sizes:

- `HorizontalResolution` and `VerticalResolution` define the virtual canvas size (default 320×200 if unset).
- `BeginStatusBar()` creates a virtual canvas for status-bar-style HUDs, covering a designated strip on screen.
- `BeginHUD()` creates a virtual canvas for fullscreen HUDs, covering the entire screen.
- `defaultScale` provides a scale vector for fitting the virtual resolution to the actual window without fractional steps.

When `fullscreenOffsets` is true, drawing coordinates are relative to the actual window resolution instead. The `drawOffset` field allows HUDs to apply global offsets to all drawing operations.

## Registration via MAPINFO

To use a custom HUD, register it in the `GameInfo` block of a MAPINFO lump:

```text
GameInfo
{
  StatusBarClass = "MyCustomHUD"      // replaces the base HUD
  AltHUDClass = "MyCustomAltHUD"      // replaces the alternate HUD
}
```

## Virtual methods to override

The following virtual methods can be overridden in a custom HUD class:

- `Init()` — called when the HUD is first created; use this to set up additional functionality.
- `Tick()` — called every tic; use for frame-independent game-logic updates.
- `Draw(int state, double TicFrac)` — called every frame with a fractional tic offset; use for rendering. The `state` parameter is one of the `EHudState` enum values (HUD_StatusBar, HUD_Fullscreen, HUD_None, HUD_AltHud, in that declaration order).
- `ScreenSizeChanged()` — called when the screen size or aspect ratio changes; use to adapt the HUD layout.
- `ReceivedWeapon(Weapon weapon)` — called when a weapon is picked up for the first time.
- `SetMugShotState(String state_name, bool wait_till_done, bool reset)` — sets the state of the status bar's mug shot (player face graphic).
- `AttachToPlayer(PlayerInfo player)` — attaches the HUD to a specific player.
- `NewGame()` — called when the status bar object is created; the native call site is `G_InitNew` (via `ST_CreateStatusBar`). **Verified correction:** despite the name, this also fires when loading a saved game — `G_DoLoadGame` calls `G_InitNew` the same as a genuine new-game start, and `NewGame()` is invoked unconditionally with no check of the `savegamerestore` flag, so there is no "skip on load" gate in current UZDoom source.
- `ShowPop(int popnum)` — shows a popup box (used in Strife for character portraits).
- `MustDrawLog(int state)` — return true to draw the log instead of a popup.
- `ProcessNotify(EPrintLevel level, String outline)` — called when the console receives a notification; return true to suppress default behavior.
- `ProcessMidPrint(Font font, String msg, bool bold)` — called when printing a HUD message; return true to suppress default behavior.
- `FlushNotify()` — called when console notifications are cleared.
- `DrawChat(String text)` — called to draw a chat message; return true to suppress default behavior.
- `DrawPaused(int player)` — called to draw pause graphics; return true to suppress default behavior.
- `GetProtrusion(double scaleratio)` — return the height (in HUD pixels) that HUD graphics extend above the status bar, used for automap text positioning.
- `DrawMyPos()` — called every frame when the `idmypos` cheat is active.
- `DrawAutomapHUD(double ticFrac)` — called every frame the automap is active.
- `DrawPowerups()` — called every frame to draw power-up icons.

## Key fields

- `RelTop` — height of the status bar in pixels (virtual resolution units).
- `HorizontalResolution`, `VerticalResolution` — virtual canvas size (default 320×200).
- `Centering` (unused in current UZDoom).
- `FixedOrigin` (unused in current UZDoom).
- `CompleteBorder` — if true, the background image is drawn behind the entire status bar; if false, only at the edges.
- `CrosshairSize` — scalar for the crosshair size; only has effect if the `crosshairgrow` cvar is true.
- `Displacement` — size difference between scaled and unscaled status bar as a fraction of `RelTop`.
- `CPlayer` — the `PlayerInfo` for the player being viewed (can change in multiplayer when swapping views).
- `ShowLog` — controls display of subtitles and log text (mainly used in Strife).
- `defaultScale` — x/y scale factors for fitting the virtual resolution to the window.
- `artiflashTick` — frame counter for the flash effect when an item is used (Heretic/Hexen).
- `itemflashFade` — alpha value for the item-use flash (Strife).
- `Alpha` — overall alpha (opacity) of the entire HUD.
- `drawOffset` — x/y offsets applied to all subsequent drawing operations.
- `fullscreenOffsets` — if true, use window resolution instead of virtual resolution for drawing coordinates.

## Drawing functions

`StatusBarCore` provides numerous drawing functions; the most common are:

- `DrawTexture(TextureID, Vector2 pos, ...)` — draws a texture by ID.
- `DrawImage(String textureName, Vector2 pos, ...)` — draws a texture by name.
- `DrawImageRotated(String textureName, Vector2 pos, double angle, ...)` — draws a rotated texture.
- `DrawString(HUDFont font, String text, Vector2 pos, ...)` — draws text. Note: the UZDoom signature includes two additional trailing parameters absent from some wiki versions (`int pt` and `ERenderStyle style`).
- `DrawBar(String foreground, String background, double curval, double maxval, Vector2 pos, int border, int vertical, int flags, double alpha)` — draws a bar (health, ammo, etc.).
- `DrawInventoryBar(InventoryBarState, Vector2 pos, int numfields, ...)` — draws the player's inventory bar.
- `DrawHexenArmor(int type, String image, Vector2 pos, ...)` — draws Hexen-style armor.
- `DrawShader(int which, Vector2 pos, Vector2 size, ...)` — draws a shader effect.
- `Fill(Color col, double x, double y, double w, double h, ...)` — fills a rectangle with a solid color.
- `SetClipRect(double x, double y, double w, double h, ...)` — creates a clipping mask for subsequent drawing.
- `ClearClipRect()` — clears the clipping mask.

## Wiki/engine divergence

This page was verified against UZDoom source. The source includes `DrawTextureRotated` as a paired function with `DrawImageRotated`; some wiki versions list only `DrawImageRotated`. The `DrawString` signature in UZDoom includes two optional trailing parameters (`int pt = 0` and `ERenderStyle style = STYLE_Translucent`) not universally documented. The wiki marks `RefreshBackground()` and `DrawCrosshair()` as "development version only," but in UZDoom they are standard protected native members with no version restriction. If cross-checking against GZDoom or a different GZDoom-family fork, note that behavior may diverge.

## See also

- `HUDFont` — font wrapper for HUD text rendering.
- `InventoryBarState` — struct holding inventory bar configuration.
- `HUDMessageBase` — base class for HUD messages (pop-ups, log text).
- Event handlers and `EventHandler` class (for dispatching HUD updates from play scope or other event handlers).
