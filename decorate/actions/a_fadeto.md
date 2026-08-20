# `A_FadeTo`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_FadeTo` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_FadeTo&oldid=44214) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3097-3158`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_FadeTo)` in `src/thingdef/thingdef_codeptr.cpp`.

Gradually adjusts an actor's alpha (translucency/opacity) toward a target value. Unlike `A_FadeOut` (which fades to fully transparent) or `A_FadeIn` (which fades to fully opaque), `A_FadeTo` allows fading to any specific alpha value, making it useful for gradual visibility changes, stealth effects, or semi-transparent appearances.

## Signature

```text
void A_FadeTo(fixed target, fixed amount = 0.1, bool remove = false)
```

## Parameters

### `target` (fixed, required)

The alpha value to fade toward, expressed as a fixed-point fraction.

**Units:** fixed-point, where `1.0 == FRACUNIT` (65536 in internal fixed-point units). Valid range: `0.0` (fully transparent) to `1.0` (fully opaque). Values outside this range are permitted but will not be clamped (see "Behavior notes" below).

**Examples:**
- `0.0` — fade to fully transparent
- `0.5` — fade to 50% opacity
- `1.0` — fade to fully opaque

### `amount` (fixed, optional)

The amount by which to adjust the actor's alpha per tic the state is active.

**Default:** `0.1` (matches the wiki's default; verified against Zandronum's native declaration `action native A_FadeTo(float target, float amount = 0.1, bool remove = false)` in `wadsrc/static/actors/actor.txt`).

**Units:** fixed-point. The sign of `amount` is ignored; the function always moves `alpha` *toward* `target` (increasing if `alpha < target`, decreasing if `alpha > target`).

**Behavior:** If `amount` is `0` (explicitly passed), `A_FadeTo` still clamps `alpha` to the exact `target` value on the call where `alpha` equals `target`, so even a zero amount will eventually reach the target in a single call if called while `alpha == target`.

### `remove` (bool, optional)

Controls whether the actor is destroyed once its alpha reaches the target value.

- `false` (default): The actor is **not** destroyed when it reaches the target alpha. **This differs from the wiki's default of `true`.**
- `true`: The actor is removed from the map when `alpha == target`. For player bodies (actors where `player != NULL` and `player->mo == self`), destruction is blocked and a warning is printed instead — **A_FadeTo will not delete a player body still attached to a player**, to prevent crashes.

## Behavior notes

- **No alpha clamping in Zandronum**: Unlike the wiki's description of the `FTF_CLAMP` flag (a GZDoom-family feature), Zandronum has no automatic clamping. Alpha values can exceed the `[0.0, 1.0]` range if `target` is set outside it, and the rendering engine will clamp visually during display.

- **Convergence and overshooting**: The function prevents overshooting the target. If `alpha` approaches `target` and the next step of `amount` would overshoot, `alpha` is set exactly to `target` instead. This ensures precise targeting in a single call.

- **Called once per state tic, not every game tic**: If a state has duration 4 (e.g., `PUFF A 4 A_FadeTo(0.5, 0.1)`), the action runs once after 4 game tics elapse, not every tic. To fade faster, use a shorter state duration (e.g., `PUFF A 1 A_FadeTo(...)`) or a larger `amount` value.

- **Network synchronization (multiplayer)**: Server-side only — clients do not execute `A_FadeTo`, they receive alpha updates from the server via `SERVERCOMMANDS_SetThingProperty()` and update their render accordingly. If an actor's `RenderStyle.Flags` has `STYLEF_Alpha1` set when `A_FadeTo` is called, this flag is cleared (a render-style change) and the render-style update is also sent to clients.

- **Zero amount with non-target alpha**: If `amount` is explicitly passed as `0` and `alpha` is not already equal to `target`, the alpha value will not change on that call. Only when `alpha == target` (whether by prior convergence or by coincidence) will the action do nothing further.

## Wiki/engine divergence

The ZDoom wiki describes two different signatures:

1. **Old signature** (with boolean `remove`): `A_FadeTo(float target, float amount, bool remove)` — this matches Zandronum's implementation.
2. **New signature** (with integer `flags`): `A_FadeTo(float target, float amount, int flags)` — this is the GZDoom-family version, using `FTF_REMOVE` and `FTF_CLAMP` flags.

**Zandronum uses the older boolean version.** The key differences:

- **Parameter 3**: Zandronum takes `bool remove`; GZDoom-family takes `int flags`. The flags `FTF_REMOVE` and `FTF_CLAMP` do not exist in Zandronum.
- **Default for `amount`**: `0.1` in both the wiki and Zandronum — no divergence here.
- **Default for `remove`**: Wiki says `true` (remove by default); Zandronum's default is `false` (do not remove by default).
- **Alpha clamping**: GZDoom-family supports `FTF_CLAMP` to restrict alpha to `[0.0, 1.0]`; Zandronum has no clamping (alpha can exceed this range if `target` is set outside it, but will appear clamped during rendering).

## Engine-family divergence

UZDoom's actual declared signature (`native void A_FadeTo(double target, double amount = 0.1, int flags = 0);` in `wadsrc/static/zscript/actors/actor.zs`) confirms that the "new signature" described in the Wiki/engine divergence section above is UZDoom's real implementation, not just a wiki description of a hypothetical variant. UZDoom's `A_FadeTo` (`src/playsim/p_actionfunctions.cpp`) takes an `int flags` parameter using `FTF_REMOVE` (bit 0) and `FTF_CLAMP` (bit 1), not Zandronum's boolean `remove` parameter, and internally represents `target`/`amount` as native `double` rather than fixed-point.

- **Alpha clamping**: UZDoom supports `FTF_CLAMP`; when set, alpha is clamped into `[0.0, 1.0]` after the fade step via `clamp(self->Alpha, 0., 1.)`. Zandronum has no equivalent flag or clamping logic (as already noted above for the wiki's description of this feature).
- **`remove`/`FTF_REMOVE` default**: UZDoom's native declaration defaults `flags` to `0`, so `FTF_REMOVE` is **not** set by default — matching Zandronum's `remove = false` default, not the wiki's stated default of `true` for the old-style parameter.
- **Player-body protection is silent, not warned, on UZDoom**: Zandronum explicitly checks `self->player && self->player->mo == self` before honoring a remove request and prints a `PRINT_BOLD` warning (`"Warning: A_FadeTo may not delete player bodies that are still associated to a player!"`) when it refuses. UZDoom's removal path instead goes through the shared `P_RemoveThing()` helper (`src/playsim/p_things.cpp`), which applies the same underlying condition (skip removal if `actor->player != NULL && actor == actor->player->mo`) but does so **silently** — no message is printed to console when a live player's body is protected from removal.
- **No client/server authority split on UZDoom**: Zandronum's `A_FadeTo` is server-authoritative — gated by `NETWORK_InClientModeAndActorNotClientHandled()` and followed by `SERVERCOMMANDS_SetThingProperty()`/`SERVERCOMMANDS_DestroyThing()` broadcasts to clients (see "Network synchronization (multiplayer)" above). UZDoom's implementation has no client/server split at all — no `NETWORK_*` gating and no `SERVERCOMMANDS_*` calls anywhere in the function; it simply runs the fade and removal logic directly wherever it's called.

## Example (Zandronum DECORATE)

```text
actor SemiTransparentSpider : SpiderMasterMind
{
    States
    {
    Spawn:
        SPID A 0 A_FadeTo(0.5, 0.1);  // Fade to 50% opacity at 10% per tic
        SPID A 3;
        Loop;
    
    Vanish:
        SPID A 0 A_FadeTo(0.0, 0.05);  // Fade to fully transparent at 5% per tic
        SPID A 2;
        Loop;
    
    Pain:
        SPID I 0 A_FadeTo(1.0, 0.2);   // Rapidly restore to fully opaque at 20% per tic
        SPID I 10 A_Pain;
        Goto Spawn;
    }
}
```

In this example:
- The `Spawn` state fades the spider to 50% opacity (half-transparent).
- The `Vanish` state fades to fully transparent (0% opacity).
- The `Pain` state restores the spider to full opacity (100%) on hit.

## Related actions

- **`A_FadeIn`**: Increases alpha to full opacity over multiple calls.
- **`A_FadeOut`**: Decreases alpha to full transparency over multiple calls, with automatic removal option.
