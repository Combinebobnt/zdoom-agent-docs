# `A_FadeIn(float increase_amount [, ...])`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_FadeIn` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_FadeIn&oldid=44153) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3005-3034`, `src/network.cpp:1598-1612` and `src/thingdef/thingdef_states.cpp:374-430`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `AActor` action function.

Increases the actor's opacity (alpha) by the specified amount each tic. Can be used to slowly fade in an actor or effect.

## Parameters

- `increase_amount` — The amount to increase the actor's alpha per tic. Zandronum converts it to fixed-point, since it stores alpha as a fixed-point number. The value is not range-checked; a negative amount lowers alpha. Default is `0.1` (equivalent to FRACUNIT/10). If `0` is passed, the default is used.

## Behavior

- Unconditionally clears the `STYLEF_Alpha1` bit from the actor's `RenderStyle.Flags` — a side effect beyond merely changing alpha. If this bit was set on entry, the server replicates the render style change to clients in addition to the alpha change.

- **Alpha is not clamped by the action function itself.** If the actor's alpha exceeds `1.0`, it remains unclamped (the renderer or graphics layer may handle excess values, but the action function does not); the code comments "Should this clamp alpha to 1.0?" and chose not to implement clamping.

- **Multiplayer caveat — server-authoritative.** Returns immediately on clients unless the actor is client-handled (the function checks `NETWORK_InClientModeAndActorNotClientHandled(self)` on entry). Client-handled means the actor has the `NETFL_CLIENTSIDEONLY` network flag (DECORATE `+CLIENTSIDEONLY`) or has no network ID (`NetID == 0`) (`src/network.cpp:1598-1612`). A server sends the alpha change, plus the render style when `STYLEF_Alpha1` was set on entry, via `SERVERCOMMANDS_SetThingProperty`, but only if the actor is not client-handled.

## Wiki/engine divergence

The ZDoom Wiki describes `A_FadeIn` as taking an optional second parameter `flags` with `FTF_REMOVE` and `FTF_CLAMP` constants. **Neither of these flag constants nor a second parameter exist in Zandronum.** Passing a second argument is a fatal DECORATE parse error at load time (`Expected ')', got ','.`), since the parser demands `)` after the declared parameters (`src/thingdef/thingdef_states.cpp:374-430`). Zandronum's `A_FadeIn` cannot clamp alpha (the wiki's `FTF_CLAMP`) or remove the actor when alpha reaches 1.0 (the wiki's `FTF_REMOVE`). The closest Zandronum removal behavior is `A_FadeOut`'s `remove` parameter, which removes the actor when it fades out to 0.

## Engine-family divergence: flags parameter matches the wiki

UZDoom's `A_FadeIn` (`src/playsim/p_actionfunctions.cpp`, declared in `wadsrc/static/zscript/actors/actor.zs` with a `double` amount defaulting to `0.1` and an `int` flags parameter defaulting to `0`) is **not** simplified the way Zandronum's is — it carries the full second `flags` parameter the wiki describes, with both `FTF_REMOVE` (`1 << 0`) and `FTF_CLAMP` (`1 << 1`) present and functional (`enum FadeFlags` in `p_actionfunctions.cpp`):

- **`FTF_CLAMP`** — once alpha reaches or exceeds `1.0` (after that tic's increase is applied), it is clamped down to exactly `1.0`. Without this flag, alpha is left unclamped past `1.0`, same as Zandronum's unconditional (non-clamping) behavior.
- **`FTF_REMOVE`** — once alpha reaches or exceeds `1.0`, the actor is destroyed via `P_RemoveThing()`.

The increase-then-threshold-check order is otherwise the same as Zandronum's: add the amount (defaulted to `0.1` if the caller passes `0`) to alpha first, then, if alpha is now at or above `1.0`, apply the flags. One incidental type note: UZDoom declares the amount as `double reduce`, a floating-point value, rather than the fixed-point representation Zandronum uses internally — this doesn't change observable behavior for values in the documented `[0.0, 1.0]` range.

## Engine-family divergence: no client/server authority split

UZDoom's `A_FadeIn` has no `NETWORK_InClientMode`/`SERVERCOMMANDS_*`-style gate at all (confirmed zero occurrences of either in `src/playsim/p_actionfunctions.cpp`, and zero tree-wide in UZDoom's source) — it runs to completion identically on every instance, every tic, with no client-side early return and no server-to-client replication call. The "Multiplayer caveat — server-authoritative" behavior described above does not apply to UZDoom; alpha and render-style changes simply happen locally wherever the action runs.

## See Also

- [`A_FadeOut`](a_fadeout.md) — decreases alpha; supports an optional `remove` parameter to destroy the actor when alpha reaches 0.
- [`A_FadeTo`](a_fadeto.md) — fades to a specific alpha value by a specified increment per tic.
