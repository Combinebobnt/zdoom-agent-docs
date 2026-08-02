# `A_FadeIn(float increase_amount [, ...])`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_FadeIn` (retrieved 2026-08-01, oldid=44153) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3005-3034`.
**Bucket:** `AActor` action function.

Increases the actor's opacity (alpha) by the specified amount each tic. Can be used to slowly fade in an actor or effect.

## Parameters

- `increase_amount` — The amount to increase the actor's alpha per tic. Interpreted as a fixed-point value in the range `[0.0, 1.0]` (alpha is internally stored as a fixed-point number). Default is `0.1` (equivalent to FRACUNIT/10). If `0` is passed, the default is used.

## Behavior

- Unconditionally clears the `STYLEF_Alpha1` bit from the actor's `RenderStyle.Flags` — a side effect beyond merely changing alpha. If this bit was set on entry, the server replicates the render style change to clients in addition to the alpha change.

- **Alpha is not clamped by the action function itself.** If the actor's alpha exceeds `1.0`, it remains unclamped (the renderer or graphics layer may handle excess values, but the action function does not); the code comments "Should this clamp alpha to 1.0?" and chose not to implement clamping.

- **Multiplayer caveat — server-authoritative.** Returns immediately on clients unless the actor has `+CLIENTSIDEONLY` (the function checks `NETWORK_InClientModeAndActorNotClientHandled(self)` on entry). Server sends both alpha and render-style changes to clients via `SERVERCOMMANDS_SetThingProperty` only if the actor is not client-handled.

## Divergence from ZDoom Wiki

The ZDoom Wiki describes `A_FadeIn` as taking an optional second parameter `flags` with `FTF_REMOVE` and `FTF_CLAMP` constants. **Neither of these flag constants nor a second parameter exist in Zandronum.** Passing a second argument causes a compile-time argument-count error in Zandronum's DECORATE parser. The wiki's `FTF_CLAMP` flag does not apply (alpha clamping is not supported in Zandronum's A_FadeIn). The wiki's `FTF_REMOVE` flag (which removes the actor when alpha reaches 1.0) is related to `A_FadeOut`'s behavior, not `A_FadeIn`.

## See Also

- [`A_FadeOut`](a_fadeout.md) — decreases alpha; supports an optional `remove` parameter to destroy the actor when alpha reaches 0.
- [`A_FadeTo`](a_fadeto.md) — fades to a specific alpha value by a specified increment per tic.
