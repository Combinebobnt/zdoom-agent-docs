# `A_FadeTo`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_FadeTo` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_FadeTo&oldid=44214) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3097-3158`, `src/p_mobj.cpp:586` (action runs on state entry), `src/p_mobj.cpp:619-632` (`HideOrDestroyIfSafe`) and `src/thingdef/thingdef_states.cpp:230-232` (a stray `;` on a state line is a parse error).
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

The amount by which to adjust the actor's alpha on each call. The action runs once each time its state is entered, not once per tic of the state's duration.

**Default:** `0.1` (matches the wiki's default; verified against Zandronum's native declaration `action native A_FadeTo(float target, float amount = 0.1, bool remove = false)` in `wadsrc/static/actors/actor.txt`).

**Units:** fixed-point. The function subtracts `amount` when `alpha > target` and adds it when `alpha < target`, so a positive `amount` moves `alpha` toward `target`. The sign is not normalized: a negative `amount` moves `alpha` *away* from `target` and never reaches it.

**Behavior:** An explicit `0` is used as-is. Unlike `A_FadeIn`/`A_FadeOut`, `A_FadeTo` does not substitute its default for a zero `amount`, so `alpha` never moves (see "Zero amount" below).

### `remove` (bool, optional)

Controls whether the actor is destroyed once its alpha reaches the target value.

- `false` (default): The actor is **not** destroyed when it reaches the target alpha. **This differs from the wiki's default of `true`.**
- `true`: The actor is removed from the map when `alpha == target` after the step. On Zandronum this goes through `HideOrDestroyIfSafe`, so in a game mode with map resets a level-spawned actor is hidden rather than destroyed. For player bodies (actors where `player != NULL` and `player->mo == self`), removal is blocked and a warning is printed instead (on every such call). **A_FadeTo will not delete a player body still attached to a player**.

## Behavior notes

- **No alpha clamping in Zandronum**: Unlike the wiki's description of the `FTF_CLAMP` flag (a GZDoom-family feature), Zandronum has no automatic clamping. Alpha values can exceed the `[0.0, 1.0]` range if `target` is set outside it, and the rendering engine will clamp visually during display.

- **Convergence and overshooting**: The function prevents overshooting the target. If `alpha` approaches `target` and the next step of `amount` would overshoot, `alpha` is set exactly to `target` instead. This lands `alpha` exactly on `target`, which is what lets the `remove` equality test fire.

- **Called once per state entry, not every game tic**: The action runs once when its state is entered; the state then holds for its duration. `PUFF A 4 A_FadeTo(0.5, 0.1)` steps alpha once, then waits 4 tics. To fade faster, loop through a shorter state (e.g., `PUFF A 1 A_FadeTo(...)`) or use a larger `amount` value.

- **Network synchronization (multiplayer)**: On Zandronum clients skip `A_FadeTo` for server-controlled actors and receive the result from the server instead. It sends `SERVERCOMMANDS_SetThingProperty()` for the alpha only when the alpha changed, and for the render style only when the render-style flags changed (the call clears `STYLEF_Alpha1`, so an actor that still had it set gets a render-style update). A removal also sends `SERVERCOMMANDS_DestroyThing()`. Client-handled actors (client-side-only or with no network ID) run the action locally on the client instead.

- **Zero amount**: With `amount` explicitly `0`, `alpha` never changes, though `STYLEF_Alpha1` is still cleared. With `remove = true`, the removal then fires only if `alpha` already equals `target`.

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

UZDoom's actual declared signature (in `wadsrc/static/zscript/actors/actor.zs`: a `double` target, a `double` amount defaulting to 0.1, and an `int` flags defaulting to 0) confirms that the "new signature" described in the Wiki/engine divergence section above is UZDoom's real implementation, not just a wiki description of a hypothetical variant. UZDoom's `A_FadeTo` (`src/playsim/p_actionfunctions.cpp`) takes an `int flags` parameter using `FTF_REMOVE` (bit 0) and `FTF_CLAMP` (bit 1), not Zandronum's boolean `remove` parameter, and internally represents `target`/`amount` as native `double` rather than fixed-point.

- **Alpha clamping**: UZDoom supports `FTF_CLAMP`; when set, alpha is clamped into `[0.0, 1.0]` after the fade step. Zandronum has no equivalent flag or clamping logic (as already noted above for the wiki's description of this feature).
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
        SPID A 0 A_FadeTo(0.5, 0.1)  // Step 0.1 toward 50% opacity each loop (every 3 tics)
        SPID A 3
        Loop

    Vanish:
        SPID A 0 A_FadeTo(0.0, 0.05)  // Step 0.05 toward fully transparent each loop (every 2 tics)
        SPID A 2
        Loop

    Pain:
        SPID I 0 A_FadeTo(1.0, 0.2)   // One step of 0.2 back toward fully opaque per pain
        SPID I 10 A_Pain
        Goto Spawn
    }
}
```

State lines take no trailing `;`. On Zandronum a stray `;` is read as the next state's sprite name and aborts loading with "Sprite names must be exactly 4 characters".

In this example:
- The `Spawn` loop fades the spider down to 50% opacity over about five passes, then holds it there.
- The `Vanish` label (reached only by an explicit jump) fades it to fully transparent.
- Each `Pain` entry raises opacity by a single 0.2 step (capped at 1.0); returning to `Spawn` then fades it back toward 50%.

## Related actions

- **`A_FadeIn`**: Increases alpha by a fixed step per call, toward full opacity.
- **`A_FadeOut`**: Decreases alpha to full transparency over multiple calls, with automatic removal option.
