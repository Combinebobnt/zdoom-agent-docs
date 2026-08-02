# `A_StopSound(int slot)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_StopSound` (retrieved 2026-01-24, oldid=50324) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:497-517` and `src/s_sound.cpp:1582-1596`.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_StopSound)` — callable from any actor's state table.

Stops the sound currently playing on the specified channel for the calling actor.

## Parameters

- `slot` — the sound channel to stop. Default is `CHAN_VOICE`. This function stops only sounds with an actor source (i.e., sounds played via `A_PlaySound` or other actor-based sound calls with a valid actor pointer). Sounds played locally without an actor source cannot be stopped by this function.

## Implementation

A_StopSound calls the engine's `S_StopSound(self, slot)`, which scans the active sound channels and stops any sound with `SourceType == SOURCE_Actor` matching both the calling actor and the specified channel. In multiplayer, the server is authoritative — clients receive a `SERVERCOMMANDS_StopSound` network message if needed (e.g., when stopping a sound on a CustomInventory item being picked up on a client).

## Engine divergence

The ZDoom Wiki page's prose mentions "calling `A_PlaySound` with `local` set to true" to play source-less sounds. This describes GZDoom/UZDoom behavior — **Zandronum's `A_PlaySound` does not support a `local` parameter**. See [A_PlaySound](a_playsound.md) for Zandronum's actual parameters.

The wiki's "See also" section lists `A_StartSound`, which exists in GZDoom/UZDoom but **not in Zandronum**; use `A_PlaySound` instead.

## Related functions

Not to be confused with:
- **`A_Stop`** — an action that zeroes an actor's velocity; unrelated to sound.
- **`Stop` (state keyword)** — ends the current state sequence; unrelated to `A_StopSound`.
- **`S_StopSound` (engine function)** — the internal C++ function `A_StopSound` calls; not directly callable from DECORATE.
