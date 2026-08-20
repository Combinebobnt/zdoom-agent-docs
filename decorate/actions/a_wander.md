# `void A_Wander([int flags])`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_Wander` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_Wander&oldid=49317) + verified against Zandronum source's `src/p_enemy.cpp:2297`, `wadsrc/static/actors/constants.txt`, and `src/thingdef/thingdef_data.cpp`; UZDoom source's `src/playsim/p_enemy.cpp:2251`, `src/scripting/thingdef_data.cpp:328`, and `wadsrc/static/zscript/constants.zs:160+`
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** action function defined on `AActor` (Zandronum: `src/p_enemy.cpp:2297`; UZDoom: `src/playsim/p_enemy.cpp:2251`)

Makes an actor wander around aimlessly. Unlike `A_Chase`, calling this function will not cause the actor to play active sounds, attack players, or pursue any target.

## Engine-family divergence

**Zandronum:** This action takes no parameters — the signature is `void A_Wander()` only.

**GZDoom-family (UZDoom/GZDoom):** This action accepts an optional `int flags` parameter controlling movement behavior via `CHF_*` flags (see Parameters below). The wiki page describes the GZDoom-family version.

## Parameters

These parameters only apply to **GZDoom-family engines (UZDoom/GZDoom)**, not Zandronum.

**Zandronum:** This action takes no parameters. The flags described below do not exist in Zandronum's DECORATE (not exported in `wadsrc/static/actors/constants.txt`) and cannot be passed. See `A_Chase` for the cross-reference: `A_Chase` in Zandronum knows only 5 `CHF_*` flags (`CHF_FASTCHASE`, `CHF_NOPLAYACTIVE`, `CHF_NIGHTMAREFAST`, `CHF_RESURRECT`, `CHF_DONTMOVE`), whereas the four flags below are GZDoom-family extensions. The wiki page describes the GZDoom-family version.

**GZDoom-family parameters:**

- `flags` — Optional. Flags controlling movement behavior, combined using the bitwise OR operator (`|`):
  - `CHF_NORANDOMTURN` — The actor will not attempt to change direction at random intervals during movement. Direction changes only occur when the actor encounters an obstacle.
  - `CHF_NODIRECTIONTURN` — The actor will not rotate to face its movement direction.
  - `CHF_STOPIFBLOCKED` — When an obstacle blocks the actor's path, it will stop moving but may still rotate to face the blocking obstacle.
  - `CHF_DONTTURN` — Convenience flag equivalent to `CHF_NORANDOMTURN | CHF_STOPIFBLOCKED`, combining the two turn-suppression flags.

## Wiki/engine divergence: CHF_DONTTURN composition

UZDoom's `constants.zs` (`wadsrc/static/zscript/constants.zs`) defines `CHF_DONTTURN` as `CHF_NORANDOMTURN | CHF_NOPOSTATTACKTURN | CHF_STOPIFBLOCKED` (three flags, value `416`), not the two-flag `CHF_NORANDOMTURN | CHF_STOPIFBLOCKED` (value `288`) the Parameters section above states. The extra bit, `CHF_NOPOSTATTACKTURN`, does not change `A_Wander`'s own behavior — `A_Wander` (`src/playsim/p_enemy.cpp:2251`) only ever tests `CHF_NODIRECTIONTURN`, `CHF_NORANDOMTURN`, and `CHF_STOPIFBLOCKED`; `CHF_NOPOSTATTACKTURN` is meaningful only to `A_Chase`. So passing `CHF_DONTTURN` to `A_Wander` produces the same practical effect the Parameters section describes, even though the constant's actual composition is one flag wider than stated there.

## Special cases

### STANDSTILL flag

Calling this action when the actor has the `+STANDSTILL` flag set has no effect — the function returns immediately without wandering. This flag exists in both Zandronum and GZDoom-family engines.

### Friendly monsters

The default behavior for friendly monsters is to follow the player rather than wander (this is handled by whatever code sets the actor's `movedir`, typically `A_Look` or similar target-acquisition calls, not by `A_Wander` itself).

**GZDoom-family (UZDoom/GZDoom):** To make friendly monsters actually wander instead, the actor must have the `+DONTFOLLOWPLAYERS` flag set (MF8_DONTFOLLOWPLAYERS in the engine source).

**Zandronum:** The `DONTFOLLOWPLAYERS` flag does not exist in the engine. The wiki's advice to use this flag to override friendly-monster behavior has no Zandronum equivalent. There is no per-action flag or DECORATE property to disable player-following for friendly monsters in Zandronum; they will follow the player as set by target-acquisition code.

### Conversation blocking

In Zandronum, if an actor has the `MF5_INCONVERSATION` flag set, calling this action has no effect (returns immediately).

## See also

- `A_Chase` — Similar action for pursuing a target, supports more extensive behavior flags
- `A_Look` — Check for enemies/players while wandering (typically called in alternating state frames alongside `A_Wander`)
