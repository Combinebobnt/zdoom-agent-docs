# `A_FadeOut`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_FadeOut` (retrieved 2026-07-31, oldid=45314) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3043-3087`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_FadeOut)` in `src/thingdef/thingdef_codeptr.cpp`.

Decreases an actor's alpha (translucency/opacity) by a specified amount each tic it is in a state calling this action. Once alpha reaches 0 or below, the actor is destroyed (or merely hidden, depending on the `remove` parameter).

## Signature

```
void A_FadeOut(fixed reduce_amount = FRACUNIT/10, bool remove = true)
```

## Parameters

### `reduce_amount` (fixed, optional)

The amount by which to reduce the actor's alpha value per call. Specified as a fixed-point fraction of 1.0 (e.g., `0.1` for a 10% per-tic fade).

**Default:** `FRACUNIT/10` (approximately 0.1), if omitted or set to 0. This results in a ~10-tic fade from full opacity to fully transparent.

**Units:** fixed-point, where `1.0 == FRACUNIT` (65536 in internal fixed-point units). A `reduce_amount` of `0.2` removes 20% of remaining alpha per call; `0.05` removes 5%.

### `remove` (bool, optional)

Controls whether the actor is destroyed once its alpha reaches 0.

- `true` (default): The actor is removed from the map when `alpha <= 0`. For player bodies (actors where `player != NULL` and `player->mo == self`), destruction is blocked and a warning is printed instead — **A_FadeOut will not delete a player body still attached to a player**, to prevent crashes.
- `false`: The actor is **not** destroyed; instead, it is hidden on map reset (via `HideOrDestroyIfSafe()` behavior) but remains in the world. This is typically used for decorative fades where the actor should persist for the map's lifetime.

## Behavior notes

- **No alpha clamping in Zandronum**: Unlike the wiki's description of `FTF_CLAMP`, Zandronum has no flag to prevent alpha from going below 0. Alpha can drop arbitrarily negative; the destruction check is simply `if (alpha <= 0 && remove)`.

- **Network synchronization (multiplayer)**: Server-side only — clients do not execute A_FadeOut, they receive alpha updates from the server via `SERVERCOMMANDS_SetThingProperty()` and update their render accordingly. If an actor's `RenderStyle.Flags` has `STYLEF_Alpha1` set when A_FadeOut is called, this flag is cleared (a render-style change) and the render-style update is also sent to clients.

- **Called once per state tic, not every game tic**: If a state has duration 4 (e.g., `PUFF A 4 A_FadeOut`), the action runs once after 4 game tics elapse, not every tic. To fade faster, use a shorter state duration or a larger `reduce_amount`.

## Zandronum vs. wiki divergence

The ZDoom wiki describes a parameterized `flags` integer (`FTF_REMOVE`, `FTF_CLAMP`, etc.) as the second parameter, but **Zandronum's version uses a simple boolean `remove` flag instead**. The following wiki features do not exist in Zandronum:

- **`FTF_REMOVE` flag**: Zandronum uses the boolean `remove` parameter; pass `true` for removal (default) or `false` to prevent it.
- **`FTF_CLAMP` flag**: Zandronum has no alpha-clamping behavior; alpha is not prevented from going below 0. If you need clamping, apply it in the state logic or use `A_FadeTo` with a target of 0 instead.

## Example (Zandronum DECORATE)

```
actor FadingProjectile : Actor
{
    Default
    {
        RenderStyle "Translucent";
        Alpha 1.0;
    }

    States
    {
    Spawn:
        PUFF AB 2 A_FadeOut(0.1);
        Loop;
    Death:
        PUFF CDEFGH 2 A_FadeOut(0.15);
        Stop;
    }
}
```

This projectile fades out at 10% per tic in Spawn, and 15% per tic in Death. Once fully transparent, the actor is removed.

## Related actions

- **`A_FadeIn`**: Increases alpha, the inverse of A_FadeOut.
- **`A_FadeTo`**: Fades alpha to a specific target value over multiple calls, with fine-grained control. Signature: `A_FadeTo(fixed target, fixed amount, bool remove = true)`.
