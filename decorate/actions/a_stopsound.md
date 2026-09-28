# `A_StopSound(int slot)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_StopSound` (retrieved 2026-01-24, https://zdoom.org/w/index.php?title=A_StopSound&oldid=50324) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:497-517` and `src/s_sound.cpp:1582-1596`, plus `src/sv_main.cpp:2997-2999` and `src/sv_main.cpp:4437-4465` (looping-channel list).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_StopSound)` — callable from any actor's state table.

Stops the sound currently playing on the specified channel for the calling actor.

## Parameters

- `slot` — the sound channel to stop. Default is `CHAN_VOICE`. This function stops only sounds with an actor source (i.e., sounds played via `A_PlaySound` or other actor-based sound calls with a valid actor pointer). Sounds played locally without an actor source cannot be stopped by this function.

## Implementation

A_StopSound calls the engine's `S_StopSound(self, slot)`, which scans the active sound channels and stops any sound with `SourceType == SOURCE_Actor` matching both the calling actor and the specified channel. With the `COMPATF_MAGICSILENCE` compatibility flag set, the channel test is skipped and every sound on the calling actor stops.

On Zandronum, an ordinary actor state runs the stop independently on the server and on each client, and no network message is sent. The server also drops that actor/channel from its looping-sound list, which it replays to clients during a full update (`src/sv_main.cpp:2997-2999`), so a later-joining client won't hear the stopped loop. The one exception is a CustomInventory item's state chain running on the actor picking it up (state owner is a CustomInventory other than the caller). There a client skips the stop entirely unless the item is client-side-only (`NETFL_CLIENTSIDEONLY`), and the server sends `SERVERCOMMANDS_StopSound` (actor plus channel) so clients stop it (`src/thingdef/thingdef_codeptr.cpp:502-509`).

## Engine-family divergence

The ZDoom Wiki page's prose mentions "calling `A_PlaySound` with `local` set to true" to play source-less sounds. This describes GZDoom/UZDoom behavior — **Zandronum's `A_PlaySound` does not support a `local` parameter**. See [A_PlaySound](a_playsound.md) for Zandronum's actual parameters.

The wiki's "See also" section lists `A_StartSound`, which exists in GZDoom/UZDoom but **not in Zandronum**; use `A_PlaySound` instead.

**The "Implementation" section's networking claim is Zandronum-specific.** UZDoom has no client/server authority split anywhere in its engine — there is no `SERVERCOMMANDS`-style network command layer at all. On UZDoom, `A_StopSound` resolves entirely through the local sound engine's channel scan (matching source type, source actor, and channel, same as described above); there is no separate network message involved in stopping the sound, unlike Zandronum's CustomInventory case.

## Related functions

Not to be confused with:
- **`A_Stop`** — an action that zeroes an actor's velocity; unrelated to sound.
- **`Stop` (state keyword)** — ends the current state sequence; unrelated to `A_StopSound`.
- **`S_StopSound` (engine function)** — the internal C++ function `A_StopSound` calls; not directly callable from DECORATE.
