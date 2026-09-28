# `A_FadeOut`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_FadeOut` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_FadeOut&oldid=45314) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3043-3087`, `wadsrc/static/actors/actor.txt:227-228`, `src/p_mobj.cpp:619-648` (`HideOrDestroyIfSafe`) and `src/network.cpp:1598-1612`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_FadeOut)` in `src/thingdef/thingdef_codeptr.cpp`.

Decreases an actor's alpha (translucency/opacity) by a fixed amount each time it is called. Once alpha reaches 0 or below and `remove` is true, the actor is removed (destroyed, or hidden instead when a map-reset game mode still needs it).

## Signature

```text
A_FadeOut(float reduce = 0.1, bool remove = true)
```

## Parameters

### `reduce` (float, optional)

The amount subtracted from the actor's alpha per call. Alpha runs from 0.0 (invisible) to 1.0 (opaque), so `0.1` subtracts a tenth of full opacity each call.

**Default:** `0.1`. Passing `0` also means `0.1`. From alpha 1.0, the default takes about ten calls to reach 0 (fixed-point rounding can add one).

**Units:** alpha, as a DECORATE float (stored internally as fixed-point, 1.0 = 65536). The subtraction is absolute, not proportional: `0.2` takes 0.2 off the current alpha each call, whatever the current value is.

### `remove` (bool, optional)

Controls whether anything happens once alpha reaches 0 or below.

- `true` (default): When `alpha <= 0` after the subtraction, the actor is removed through `HideOrDestroyIfSafe()`. That destroys it, except in a game mode with map resets (`GMF_MAPRESETS`) for a level-spawned actor on a non-client, where it is hidden instead (unlinked from the world, made dormant and non-solid) so the map reset can restore it. **A_FadeOut will not remove a player body still attached to a player**: when `player` is set and `player->mo == self`, it prints the bold warning "Warning: A_FadeOut may not delete player bodies that are still associated to a player!" and returns.
- `false`: The actor is never removed or hidden by this action. It stays in the world with alpha at or below 0 and keeps losing alpha on each further call.

## Behavior notes

- **No alpha clamping in Zandronum**: Unlike the wiki's description of `FTF_CLAMP`, Zandronum has no flag to prevent alpha from going below 0. Alpha can drop arbitrarily negative; the removal check is simply `alpha <= 0 && remove`.

- **Render style**: every call clears `STYLEF_Alpha1` from the actor's `RenderStyle.Flags`, so a style that forced full opacity starts honoring alpha.

- **Network synchronization (multiplayer)**: On a client, the action does nothing unless the actor is client-handled (`NETFL_CLIENTSIDEONLY` or `NetID == 0`, `src/network.cpp:1598-1612`); client-handled actors run it locally. On a server, for an actor that is not client-handled, each call sends the new alpha via `SERVERCOMMANDS_SetThingProperty(..., APROP_Alpha)`, plus `APROP_RenderStyle` when `STYLEF_Alpha1` was set before the call. When the removal branch runs, the server also sends `SERVERCOMMANDS_DestroyThing` before hiding or destroying the actor.

- **Called once per state entry, not every game tic**: The action runs when its state is entered. A state with duration 4 (e.g., `PUFF A 4 A_FadeOut`) calls it once per 4 tics. To fade faster, use shorter states or a larger `reduce`.

## Wiki/engine divergence: Zandronum's boolean `remove` parameter

The ZDoom wiki describes a parameterized `flags` integer (`FTF_REMOVE`, `FTF_CLAMP`, etc.) as the second parameter, but **Zandronum's version uses a simple boolean `remove` flag instead**. The following wiki features do not exist in Zandronum:

- **`FTF_REMOVE` flag**: Zandronum uses the boolean `remove` parameter; pass `true` for removal (default) or `false` to prevent it.
- **`FTF_CLAMP` flag**: Zandronum has no alpha-clamping behavior; alpha is not prevented from going below 0. If you need clamping, use `A_FadeTo` with a target of 0 instead, which stops at exactly the target.

Zandronum does not define the `FTF_*` constants, so writing `FTF_REMOVE` or `FTF_CLAMP` in Zandronum DECORATE is an unknown-identifier error that aborts startup.

## Engine-family divergence

UZDoom's `A_FadeOut` matches the wiki's flags-based signature rather than Zandronum's boolean one — the divergence above is Zandronum-specific, not a general wiki-vs-engine gap. UZDoom's native signature (`src/playsim/p_actionfunctions.cpp`, `wadsrc/static/zscript/actors/actor.zs:1330`) is:

```text
void A_FadeOut(double reduce = 0.1, int flags = 1)
```

where `flags` is a bitmask of `FTF_REMOVE` (1, the default) and `FTF_CLAMP` (2), not a plain boolean. Passing Zandronum-style `A_FadeOut(0.1, true)` still works in UZDoom (bool-to-int coercion makes `true` equal `1` == `FTF_REMOVE`), but `A_FadeOut(0.1, false)` becomes `flags = 0` (neither remove nor clamp), which is equivalent in effect to Zandronum's `remove = false`.

- **Alpha clamping exists in UZDoom**: unlike Zandronum, passing `FTF_CLAMP` (2) — e.g. `A_FadeOut(0.1, 3)` for remove+clamp — clamps `Alpha` to exactly `0` once it would otherwise go negative, before the removal check runs. This flag is not set by default (`flags = 1` only sets `FTF_REMOVE`), so default behavior still lets alpha go arbitrarily negative like Zandronum, matching this doc's "No alpha clamping" note only when `FTF_CLAMP` is omitted.
- **Player-body protection is silent, not warned**: UZDoom's underlying `P_RemoveThing` (`src/playsim/p_things.cpp:422`) also refuses to destroy a live player's body (`actor->player == NULL || actor != actor->player->mo` gates the `Destroy()` call), but it does so silently — no warning is printed, unlike the Zandronum behavior described above.
- **No client/server authority split**: UZDoom has no client-mode gating or server-command replication anywhere in its source tree (confirmed by search — no `NETWORK_InClientMode`/`SERVERCOMMANDS_*` occurrences at all). `A_FadeOut` runs identically wherever the actor's state ticks; the client-mode skip and `SERVERCOMMANDS_SetThingProperty()`/`SERVERCOMMANDS_DestroyThing` updates described above for Zandronum does not apply to UZDoom.

## Example (Zandronum DECORATE)

```text
actor FadingSmoke
{
    +NOINTERACTION
    RenderStyle Translucent
    Alpha 1.0
    States
    {
    Spawn:
        PUFF AB 2 A_FadeOut(0.1)
        Loop
    }
}
```

Each frame lasts 2 tics, so the smoke loses 0.1 alpha every 2 tics and reaches 0 after about ten calls (about 20 tics). The call that takes alpha to 0 or below removes the actor, which ends the loop.

## Related actions

- **`A_FadeIn`**: Increases alpha, the inverse of A_FadeOut.
- **`A_FadeTo`**: Moves alpha toward a target by a fixed amount per call, stopping exactly at the target. Signature: `A_FadeTo(float target, float amount = 0.1, bool remove = false)`. Note that `remove` defaults to `false` here, unlike `A_FadeOut`, and removal triggers when alpha equals the target, whatever the target is.
