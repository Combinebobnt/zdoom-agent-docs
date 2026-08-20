# `void A_PlaySound(sound whattoplay [, int slot [, float volume [, bool looping [, float attenuation]]]])`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `A_PlaySound` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_PlaySound&oldid=54524) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:445` and `wadsrc/static/actors/actor.txt:197`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS` on `AActor` (`src/thingdef/thingdef_codeptr.cpp:445`).

Plays a sound from the calling actor with parameters controlling channel, volume, looping behavior, and attenuation (distance fading).

**Note: Engine-family divergence.** The ZDoom wiki describes a GZDoom-family version with 7 parameters including `local` and `pitch` at the end. Zandronum's implementation has only 5 parameters; passing extra arguments will cause a compile error. The wiki also documents `A_StartSound` as the recommended non-deprecated alternative, but `A_StartSound` does not exist in Zandronum — `A_PlaySound` is the current production interface here.

## Parameters

- **whattoplay** — a sound identifier (e.g., `"weapons/pistol"`). Default: `"weapons/pistol"`.
- **slot** — the sound channel/slot and optional flags. Default: `CHAN_BODY` (4). Zandronum defines:
  - Named channels: `CHAN_AUTO` (0), `CHAN_WEAPON` (1), `CHAN_VOICE` (2), `CHAN_ITEM` (3), `CHAN_BODY` (4), `CHAN_5` (5), `CHAN_6` (6), `CHAN_7` (7).
  - Channel-modifier flags (OR-able): `CHAN_LISTENERZ` (8), `CHAN_MAYBE_LOCAL` (16), `CHAN_UI` (32), `CHAN_NOPAUSE` (64).
  - Note: `CHAN_LOOP` (256) exists in C++ but is not exposed as a named DECORATE constant; pass the numeric literal if needed (rare — see Looping behavior below).
- **volume** — amplitude, typically in the range 0.0–1.0+. Default: 1.0.
- **looping** — controls whether the sound repeats. Default: false. See Looping behavior section below for important interactions with the `slot` parameter.
- **attenuation** — distance-based volume fading. Default: `ATTN_NORM`. Zandronum defines:
  - `ATTN_NONE` (0.0) — full volume everywhere on the map, regardless of listener distance.
  - `ATTN_NORM` (1.0) — default; uses close_dist and clipping_dist from the sound definition.
  - `ATTN_IDLE` (1.001) — Doom's original attenuation curve.
  - `ATTN_STATIC` (3.0) — rapid fade; inaudible beyond ~512 units.

## Looping behavior

The `looping` parameter and the `CHAN_LOOP` (256) flag interact in two distinct paths:

- **`looping=false` (default):** The sound plays once, unless the `CHAN_LOOP` flag (256) is OR-ed into the `slot` parameter. If `CHAN_LOOP` is set and the sound is already looping on that channel (tracked server-side), the call returns early without playing. Otherwise, the sound plays without the loop flag.
- **`looping=true`:** The sound loops indefinitely. The function guards against re-triggering: if that actor is already playing that same sound-id on that channel (checked via `S_IsActorPlayingSomething`), the call returns early. If the call proceeds, `CHAN_LOOP` is internally added to the channel when passed to the sound system, and the server tracks this as an active looping channel for synchronization to newly joined clients.

In both paths, if not looping, the sound can be interrupted by calling `A_PlaySound` again on the same channel with a different sound.

## Network behavior

**Server-side only in multiplayer, with replication to clients.** If the calling actor's `+CLIENTSIDEONLY` flag is not set, the function returns immediately on the client side; the server alone is responsible for playing the sound and broadcasting it to all clients via `SERVERCOMMANDS_SoundActor`. For actors flagged `+CLIENTSIDEONLY`, the function runs on each client's local copy of that actor (cosmetic-only sounds). The server maintains a per-actor list of active looping channels (per `SERVER_UpdateLoopingChannels`) so that looping sounds re-synchronize to clients that join mid-game.

## Zandronum-specific: network-authoritative sound replication

The server-side-only/replication model described in "Network behavior" above does not exist on
UZDoom. UZDoom's `A_PlaySound` (`src/sound/s_doomsound.cpp:643`) is a thin parameter-remapping
wrapper: it folds `looping` into the `CHANF_LOOP|CHANF_NOSTOP` channel flags and `local` into
`CHANF_LOCAL`, then calls straight into `A_StartSound` → `S_PlaySoundPitch`
(`src/sound/s_doomsound.cpp:608`), which plays (or, if `CHANF_LOCAL` is set, conditionally plays
only for the calling client via `AActor::CheckLocalView`) without any server/client branch, any
equivalent of `SERVERCOMMANDS_SoundActor`, or a `SERVER_UpdateLoopingChannels`-style resync list.
The `+CLIENTSIDEONLY` flag itself is a no-op on UZDoom — `src/scripting/thingdef_data.cpp:458`
registers it as `DEFINE_DUMMY_FLAG(CLIENTSIDEONLY, false)`, parsed for DECORATE compatibility but
without effect. This matches a pattern seen across most of this cohort: UZDoom has no
client/server network-authority split anywhere in its source tree.

## Engine-family divergence: parameter count, deprecation, and channel constant

UZDoom's native declaration (`wadsrc/static/zscript/actors/actor.zs:1306`) carries the full
7-parameter signature the ZDoom wiki describes (`whattoplay`, `slot`, `volume`, `looping`,
`attenuation`, `local`, `pitch`) — confirming, on the primary engine itself rather than by wiki
inference, that the "Note: Engine-family divergence" paragraph above describes a real UZDoom/
Zandronum split rather than just a wiki-vs-Zandronum one. UZDoom's declaration is also marked
`deprecated("4.3", "Use A_StartSound() instead")`, and unlike Zandronum, `A_StartSound` genuinely
exists on UZDoom (`wadsrc/static/zscript/actors/actor.zs:1307`) as the current recommended
interface — `A_PlaySound` is a legacy call-through, not the production interface, on this engine.
Separately, UZDoom exposes `CHAN_LOOP` (256) as a named constant in the global `ESoundFlags` enum
(`wadsrc/static/zscript/engine/base.zs:41`), usable directly in DECORATE/ZScript source, unlike
Zandronum where the same numeric value has no named constant.

## See also

- `A_StopSound` — stop a sound on a specific channel.
- `A_PlaySoundEx` — an older interface taking a different parameter structure and type (sound + name-type channel + bool looping + int attenuation_raw) — see `src/thingdef/thingdef_codeptr.cpp:536`.
