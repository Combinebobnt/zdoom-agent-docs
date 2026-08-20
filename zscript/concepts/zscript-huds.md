# ZScript HUDs: design patterns and concepts

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki `ZScript HUDs` (retrieved 2026-08-03, https://zdoom.org/w/index.php?title=ZScript_HUDs&oldid=54285) + spot-checked against UZDoom source (`wadsrc/static/zscript/ui/statusbar/statusbar.zs`, `src/events.cpp`, `src/events.h`); re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — no behavioral drift found. StatusBarClass/AltHUDClass MAPINFO-key handling now independently confirmed in `src/gamedata/gi.cpp`'s `FMapInfoParser::ParseGameInfo()` (case-insensitive `statusbarclass`/`althudclass` keys feeding `gameinfo.statusbarclass`/`gameinfo.althudclass`, consumed by `src/g_statusbar/shared_sbar.cpp` and `shared_hud.cpp` respectively).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

## Overview and scope

This page covers the architectural concepts and implementation patterns for building custom HUDs in ZScript, as distinct from the class reference material in `basestatusbar.md`. ZScript offers a flexible (but more complex) alternative to SBARINFO for creating fully custom HUDs. For the reference documentation of `BaseStatusBar`, `AltHUD`, and related classes, see the class-specific files rather than relying on this concept page.

## Role of related classes

ZScript HUD development involves several classes, each with a distinct role:

- **BaseStatusBar** — the main HUD class all custom status bars inherit from. Handles both status-bar-style HUDs (covering a portion of the screen) and fullscreen HUDs (covering the entire screen). See `classes/basestatusbar.md` for the full virtual-method list and drawing-function reference.
- **AltHUD** — optional class for replacing GZDoom's alternate HUD (the simplified overlay HUD shown with `alt+h`). AltHUD uses global screen coordinates and the `Screen.*` drawing methods, making it less flexible than BaseStatusBar but simpler for minimal overlays. See `classes/basestatusbar.md` for details.
- **HUDFont** — a wrapper for setting up fonts for use with `DrawString()` and related text-drawing functions in BaseStatusBar. Encapsulates font metrics and rendering parameters.
- **InventoryBarState** — encapsulates state for drawing the player's inventory bar (the item selector at the bottom of classic Doom HUDs). Used with `DrawInventoryBar()` in BaseStatusBar.
- **LinearValueInterpolator** and **DynamicValueInterpolator** — utility classes for smoothly animating numeric values between states over time. Useful for health-bar animations, ammo-counter transitions, and other UI effects that shouldn't jump abruptly.

## Virtual resolution and coordinate system

BaseStatusBar uses a virtual resolution (defaulting to 320×200 if not set) that scales to fit the player's actual screen size and aspect ratio. This is critical to understand:

**Never use explicit pixel coordinates** like `(320, 0)` or `(160, 100)` when drawing HUD elements — these values shift depending on the player's monitor resolution and aspect ratio. Instead:

- Familiarize yourself with the `DI_SCREEN*` and `DI_ITEM*` flags, which most BaseStatusBar drawing functions accept.
  - `DI_SCREEN_*` flags place the drawn element's anchor relative to the virtual-resolution screen's corners and edges.
  - `DI_ITEM_*` flags control which point of the drawn image or text (its top/bottom/left/right/center) is aligned to the position coordinate passed into that draw call. This is a general-purpose alignment mechanism used by nearly every drawing function (`DrawTexture`, `DrawImage`, `DrawString`, `DrawBar`, `DrawGem`, ...), not something specific to inventory-bar drawing — `DrawInventoryBar()` is simply one caller among many.
  - These flags handle the coordinate translation automatically, ensuring your HUD scales correctly across all player configurations.
- Alternatively, set `HorizontalResolution` and `VerticalResolution` in your HUD class and use virtual coordinates throughout; the engine handles scaling.

See `classes/basestatusbar.md` for the full list of drawing functions and their flag parameters.

## AltHUD vs. BaseStatusBar: when to use each

- **Use BaseStatusBar** (default) for your main HUD — it offers full drawing-function support, virtual resolution scaling, and integration with the standard HUD lifecycle. This is the recommended path for most custom HUDs.
- **Use AltHUD** if you only need to replace GZDoom's minimal alternate HUD (shown with `alt+h`). AltHUD uses the global `Screen.*` drawing methods and fixed screen coordinates instead of virtual resolution, making it simpler but less flexible. AltHUD is rarely chosen for new projects; BaseStatusBar fullscreen mode is more capable.

## Triggering HUD functions from gameplay events

Gameplay code (actors, scripts) runs in "play scope," while HUDs run in "UI scope." These scopes are isolated — your HUD cannot directly call actor methods, and actors cannot directly call HUD methods. To bridge this gap:

1. **Create an EventHandler** in play scope that detects the gameplay event you care about (e.g., `WorldThingDamaged()`, player death, weapon pickup).
2. **In the event handler, call `EventHandler.SendInterfaceEvent(playernum, eventname, arg1, arg2, arg3)`** to send a message to the UI scope.
   - `playernum` — the player index the event applies to (0 for the console player in singleplayer). **This gates local delivery, not routing:** the native implementation only actually dispatches the event when `playernum` equals *that client's own* `consoleplayer` — every client runs this check independently against its local player index. In multiplayer, calling this once (e.g. from a shared `WorldThingDamaged` handler keyed off the damaged actor's player number) correctly reaches only the affected player's own client and is silently a no-op on every other client, which is normally the desired behavior for a per-player HUD effect.
   - `eventname` — a string identifying the event (e.g., `"HUDEVENT_PlayerDamaged"`).
   - `arg1`, `arg2`, `arg3` — integer arguments passed to the UI scope (stored in the event's `Args[0]`, `Args[1]`, `Args[2]`).
3. **In your custom HUD class, override `InterfaceProcess(ConsoleEvent e)`** — this virtual method is called when an interface event arrives.
   - Check `e.name` to identify which event this is.
   - If it's one you care about, extract the integer arguments from `e.Args[]` and update your HUD state accordingly (e.g., set a timer, cache the damage value for a flash effect).
4. **Later, in `Draw()` or `Tick()`**, use the cached state to render your effect.

**Key implementation detail:** `InterfaceProcess` is a UI-scope method, so you can safely call HUD drawing functions and access `statusbar` (a global pointer to your HUD instance). Use this method to receive play-scope events and update HUD state; use `Draw()` to render based on that state.

Example pattern (pseudocode):

```zscript
// In your custom HUD class:
class MyCustomHUD : BaseStatusBar
{
    int damageFlashTics;    // timer for the damage flash effect
    int lastDamageAmount;   // amount of damage received

    override void Tick()
    {
        Super.Tick();
        if (damageFlashTics > 0)
            damageFlashTics--;
    }

    override void Draw(int state, double ticfrac)
    {
        Super.Draw(state, ticfrac);
        if (state != HUD_None && damageFlashTics > 0)
        {
            // Draw damage effect, fading based on damageFlashTics
            int alpha = (damageFlashTics * 255) / TICRATE;
            DrawCustomDamageFlash(alpha);
        }
    }

    override void InterfaceProcess(ConsoleEvent e)
    {
        Super.InterfaceProcess(e);
        if (e.name ~== "HUDEVENT_PlayerDamaged")
        {
            damageFlashTics = TICRATE;  // 1 second
            lastDamageAmount = e.Args[0];
        }
    }
}

// In your play-scope event handler:
class MyEventHandler : EventHandler
{
    override void WorldThingDamaged(WorldEvent e)
    {
        if (e.thing.player)
        {
            EventHandler.SendInterfaceEvent(
                e.thing.player.mo.PlayerNumber(),
                "HUDEVENT_PlayerDamaged",
                e.damage,
                0,
                0
            );
        }
    }
}
```

## Registration via MAPINFO

See `classes/basestatusbar.md` for documentation of the `GameInfo` block and the `StatusBarClass`/`AltHUDClass` keys used to register your custom HUD in a MAPINFO lump. That class reference covers the registration syntax and the caveat that only the last-loaded mod's HUD definition is active.

## Lifecycle and timing

- **Init()** — called once when the HUD is first created (when entering a level). Use this to set up fonts, initial state, and other one-time setup.
- **Tick()** — called every game tic (35 times per second at normal speed), regardless of framerate. Use for game-logic updates that must happen at fixed intervals.
- **Draw(int state, double TicFrac)** — called every frame for rendering. The `TicFrac` parameter is a fractional tic value normally in `[0.0, 1.0)`, but it is exactly `1.0` when frame interpolation is disabled (`cl_capfps` or `r_NoInterpolate`) — don't assume the exclusive upper bound always holds. The `state` parameter is one of the `EHudState` enum values:
  - `HUD_StatusBar` — drawing the status bar at the bottom of the screen.
  - `HUD_Fullscreen` — drawing a fullscreen HUD (no status bar strip reserved).
  - `HUD_AltHud` — **not** "drawing the alternate HUD": `BaseStatusBar`'s own `Draw()` returns immediately for this state and draws nothing. The alt-HUD's actual visuals come from the separate `AltHud` class's own draw method, called independently by the engine. `HUD_AltHud` exists purely so that a status-bar subclass's `Draw()` override still runs while the alt-HUD is on screen, to let any active popup (the log/keys/status pop-up screens triggered by `ShowPop()`) render on top of it — ordinary HUD content should not be drawn for this state.
  - `HUD_None` — drawing neither (used in some contexts; check `state != HUD_None` before drawing).

## Scope note

The ZDoom wiki's `ZScript HUDs` page does not describe SBARINFO-to-ZScript migration despite the broader title implying it might. That content is not present in this page or other ZScript documentation currently in this tree. (This is a coverage gap, not a wiki/engine behavioral divergence — the wiki and this docs tree agree by both being silent on the topic.)

## Related documentation

- `classes/basestatusbar.md` — BaseStatusBar and StatusBarCore class reference (virtual methods, drawing functions, virtual resolution, MAPINFO registration).
- `classes/eventhandler.md` — EventHandler class reference (event types, dispatch order, scope semantics; covers `SendInterfaceEvent` usage in play scope).
- `concepts/zscript-engine-availability.md` — reminder that ZScript does not exist in Zandronum.
