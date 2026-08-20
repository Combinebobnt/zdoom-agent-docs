# `int ClassifyActor(int tid)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-06)
**Provenance:** ZDoom Wiki `ClassifyActor` (retrieved 2026-08-06, https://zdoom.org/w/index.php?title=ClassifyActor&oldid=35678) + verified against the Zandronum source's `src/p_acs.cpp:5250-5316`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin (dispatched as `PCD_CLASSIFYACTOR`).

Returns a bitfield describing the classification of an actor by its thing ID. Used to test whether an actor is a player, monster, missile, or other entity type, and whether it's currently alive or dead.

## Parameters

- `tid` — The thing ID of the actor to classify. Pass `0` to classify the script's activator.

## Return value

An `int` bitfield where each bit corresponds to a named classification constant defined in `zcommon.bcs`:

- `ACTOR_NONE (0x0)` — No actor with the specified TID was found. **Only returned when `tid` is nonzero**; if `tid == 0` and there is no activator, returns `ACTOR_WORLD` instead.
- `ACTOR_WORLD (0x1)` — The activator is the world rather than an actor. **Only returned when `tid == 0` and the activator is NULL** (e.g., in `OPEN`-type scripts).
- `ACTOR_PLAYER (0x2)` — The actor is a player.
- `ACTOR_BOT (0x4)` — The actor is a bot controlled by the engine. Always paired with `ACTOR_PLAYER` if both are set.
- `ACTOR_VOODOODOLL (0x8)` — The actor is a voodoo doll — an extra copy of a player in the map that has no AI but passes damage taken to the corresponding player. Always paired with `ACTOR_PLAYER` if both are set.
- `ACTOR_MONSTER (0x10)` — The actor is a monster (has the `MF3_ISMONSTER` flag).
- `ACTOR_ALIVE (0x20)` — The actor is currently alive.
- `ACTOR_DEAD (0x40)` — The actor is currently dead.
- `ACTOR_MISSILE (0x80)` — The actor is a missile in flight (has the `MF_MISSILE` flag).
- `ACTOR_GENERIC (0x100)` — The actor is neither a missile nor a monster — typically a decoration, invisible marker, or other non-combat entity.

The return value is a bitfield. Check individual bits using bitwise-AND (`&`):

```text
if (ClassifyActor(tid) & ACTOR_PLAYER) { /* is a player */ }
```

## Classification rules

Classification is mutually exclusive in its primary category:

- If the actor is a player, the result includes `ACTOR_PLAYER` (and optionally `ACTOR_BOT` and/or `ACTOR_VOODOODOLL`).
- Else if the actor is a monster, the result includes `ACTOR_MONSTER`.
- Else if the actor is a missile, the result includes `ACTOR_MISSILE`.
- Else the result includes `ACTOR_GENERIC`.

Players and monsters are also classified as either `ACTOR_ALIVE` or `ACTOR_DEAD`, but never both. Missiles and generic actors receive neither flag — the dead/alive distinction only applies to player/monster types.

## Notes on tid=0

When `tid == 0`, the function tests the script's **activator** (the actor that triggered the script, if any):

- If an activator exists, returns its classification normally.
- If no activator exists (e.g., an `OPEN`-type script with no triggering actor), returns `ACTOR_WORLD` to distinguish it from `ACTOR_NONE`.

## Behavior on TID miss

When `tid` is nonzero and no actor with that TID exists, returns `ACTOR_NONE` (plain `0`). This is indistinguishable from a literal zero-classification, but in practice is only used to detect a missing actor.
