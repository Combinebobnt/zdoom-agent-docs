# `void A_SetTranslucent(float alpha [, int style])`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_SetTranslucent` (retrieved 2026-08-01, oldid=46825) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:2974-2996`.
**Bucket:** action function (defined on `AActor`).

Sets an actor's alpha value and render style mode.

## Parameters

- **alpha**: float between 0.0 (fully transparent) and 1.0 (fully opaque), specifying the actor's visibility. Clamped to this range if out of bounds.
- **style** (optional): int specifying the translucency blend mode. Defaults to 0 (normal translucency) per the DECORATE declaration `actor.txt:225`. 
  - **0**: Normal translucency blending (opaque at alpha 1.0).
  - **1**: Additive blending.
  - **2**: Fuzz effect (post-blur distortion; alpha value is ignored).
  - **Other values**: Silently default to additive blending (mode 1 behavior) — the function treats any value outside `{0, 2}` as additive, not as an error.

## Notes

- **Wiki divergence — A_SetRenderStyle supersession claim does not apply to Zandronum.** The ZDoom Wiki states this function "has been superseded by A_SetRenderStyle." A_SetRenderStyle does not exist in Zandronum's codebase and never did; this advice applies only to GZDoom/UZDoom-family engines. Zandronum modders should continue using A_SetTranslucent.
- **Engine-specific constants unavailable.** Zandronum does not define `STYLE_*` enum constants for the mode parameter — modders must pass raw integers (0, 1, 2), not names like `STYLE_Add`. The GZDoom family added this enum late in development.
- **Network-aware.** In multiplayer, alpha and RenderStyle changes are replicated to clients via `SERVERCOMMANDS_SetThingProperty` (Zandronum 3.2.1+). This function executes server-side only; calls on clients return immediately unless the actor has `+CLIENTSIDEONLY`.
- **Parameter-index note for reviewers of the C++ source.** The underlying `DEFINE_ACTION_FUNCTION_PARAMS` macro uses `ACTION_PARAM_INT(mode, 1)` — the second argument is the parameter *index* (1 = second parameter), not the default value. The actual default (0) comes from the DECORATE declaration in `actor.txt:225`, not the C++ code.

## See also

- [A_FadeIn](a_fadein.md), [A_FadeOut](a_fadeout.md), [A_FadeTo](a_fadeto.md) — related translucency animations.
- [Creating projectiles](../concepts/creating-projectiles.md) — projectile properties and render-style usage in projectile definitions.
