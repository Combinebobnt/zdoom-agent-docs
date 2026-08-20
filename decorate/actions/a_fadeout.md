# `A_FadeOut`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `A_FadeOut` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_FadeOut&oldid=45314) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3043-3087`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_FadeOut)` in `src/thingdef/thingdef_codeptr.cpp`.

Decreases an actor's alpha (translucency/opacity) by a specified amount each tic it is in a state calling this action. Once alpha reaches 0 or below, the actor is destroyed (or merely hidden, depending on the `remove` parameter).

## Signature

```text
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

## Wiki/engine divergence: Zandronum's boolean `remove` parameter

The ZDoom wiki describes a parameterized `flags` integer (`FTF_REMOVE`, `FTF_CLAMP`, etc.) as the second parameter, but **Zandronum's version uses a simple boolean `remove` flag instead**. The following wiki features do not exist in Zandronum:

- **`FTF_REMOVE` flag**: Zandronum uses the boolean `remove` parameter; pass `true` for removal (default) or `false` to prevent it.
- **`FTF_CLAMP` flag**: Zandronum has no alpha-clamping behavior; alpha is not prevented from going below 0. If you need clamping, apply it in the state logic or use `A_FadeTo` with a target of 0 instead.

## Engine-family divergence

UZDoom's `A_FadeOut` matches the wiki's flags-based signature rather than Zandronum's boolean one — the divergence above is Zandronum-specific, not a general wiki-vs-engine gap. UZDoom's native signature (`src/playsim/p_actionfunctions.cpp`, `wadsrc/static/zscript/actors/actor.zs:1330`) is:

```text
void A_FadeOut(double reduce = 0.1, int flags = 1)
```

where `flags` is a bitmask of `FTF_REMOVE` (1, the default) and `FTF_CLAMP` (2), not a plain boolean. Passing Zandronum-style `A_FadeOut(0.1, true)` still works in UZDoom (bool-to-int coercion makes `true` equal `1` == `FTF_REMOVE`), but `A_FadeOut(0.1, false)` becomes `flags = 0` (neither remove nor clamp), which is equivalent in effect to Zandronum's `remove = false`.

- **Alpha clamping exists in UZDoom**: unlike Zandronum, passing `FTF_CLAMP` (2) — e.g. `A_FadeOut(0.1, 3)` for remove+clamp — clamps `Alpha` to exactly `0` once it would otherwise go negative, before the removal check runs. This flag is not set by default (`flags = 1` only sets `FTF_REMOVE`), so default behavior still lets alpha go arbitrarily negative like Zandronum, matching this doc's "No alpha clamping" note only when `FTF_CLAMP` is omitted.
- **Player-body protection is silent, not warned**: UZDoom's underlying `P_RemoveThing` (`src/playsim/p_things.cpp:422`) also refuses to destroy a live player's body (`actor->player == NULL || actor != actor->player->mo` gates the `Destroy()` call), but it does so silently — no warning is printed, unlike the Zandronum behavior described above.
- **No client/server authority split**: UZDoom has no client-mode gating or server-command replication anywhere in its source tree (confirmed by search — no `NETWORK_InClientMode`/`SERVERCOMMANDS_*` occurrences at all). `A_FadeOut` runs identically wherever the actor's state ticks; the "server-side only, clients receive updates via `SERVERCOMMANDS_SetThingProperty()`" behavior described above for Zandronum does not apply to UZDoom.

## Example (Zandronum DECORATE)

```text
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
