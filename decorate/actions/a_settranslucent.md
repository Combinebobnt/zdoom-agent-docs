# `void A_SetTranslucent(float alpha [, int style])`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_SetTranslucent` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_SetTranslucent&oldid=46825) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:2974-2996`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
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

## Engine-family divergence: no client/server authority split

UZDoom has no client-mode gate on `A_SetTranslucent` — the function body has no client/server branch, and no `NETWORK_InClientMode`/`SERVERCOMMANDS_*`-style construct exists anywhere in the UZDoom source tree. On Zandronum, the function first checks `NETWORK_InClientModeAndActorNotClientHandled(self)` and returns early on a client for a server-handled actor, then after applying the change explicitly replicates the new alpha and render style to clients via two `SERVERCOMMANDS_SetThingProperty` calls (one for `APROP_RenderStyle`, one for `APROP_Alpha`). On UZDoom, the function just applies the alpha/render-style change directly and unconditionally wherever it's called — there is no server-authoritative gate and nothing to replicate, because UZDoom's multiplayer model has no client/server distinction for actor state to begin with (every instance runs the same simulation). This means the "Network-aware" note above (server-side-only execution, `SERVERCOMMANDS_SetThingProperty` replication, the `+CLIENTSIDEONLY` exception) is Zandronum-specific and does not apply to UZDoom.

UZDoom also stores alpha as a `double` (`PARAM_FLOAT`, clamped via `clamp(alpha, 0., 1.)`) rather than Zandronum's `fixed_t` (`ACTION_PARAM_FIXED`, clamped via `clamp<fixed_t>(alpha, 0, FRACUNIT)`) — an internal representation difference only, with no observable behavioral effect from ACS/DECORATE/ZScript: both accept and clamp the same 0.0-1.0 range.

## See also

- [A_FadeIn](a_fadein.md), [A_FadeOut](a_fadeout.md), [A_FadeTo](a_fadeto.md) — related translucency animations.
- [Creating projectiles](../concepts/creating-projectiles.md) — projectile properties and render-style usage in projectile definitions.
