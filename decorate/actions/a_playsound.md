# `void A_PlaySound(sound whattoplay [, int slot [, float volume [, bool looping [, float attenuation]]]])`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_PlaySound` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_PlaySound&oldid=54524) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:445` and `wadsrc/static/actors/actor.txt:197`; volume cap and attenuation handling from `src/s_sound.cpp:954`, `src/sv_commands.cpp:3678`, `src/s_sound.cpp:1183`, `src/sound/fmodsound.cpp:2665` and `wadsrc/static/sndinfo.txt:51`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS` on `AActor` (`src/thingdef/thingdef_codeptr.cpp:445`).

Plays a sound from the calling actor with parameters controlling channel, volume, looping behavior, and attenuation (distance fading).

**Note: Engine-family divergence.** The ZDoom wiki describes a GZDoom-family version with 7 parameters including `local` and `pitch` at the end. Zandronum's implementation has only 5 parameters; passing extra arguments is a fatal DECORATE parse error at load time. The wiki also documents `A_StartSound` as the recommended non-deprecated alternative, but `A_StartSound` does not exist in Zandronum — `A_PlaySound` is the current production interface here.

## Parameters

- **whattoplay** — a sound identifier (e.g., `"weapons/pistol"`). Default: `"weapons/pistol"`.
- **slot** — the sound channel/slot and optional flags. Default: `CHAN_BODY` (4). Zandronum defines:
  - Named channels: `CHAN_AUTO` (0), `CHAN_WEAPON` (1), `CHAN_VOICE` (2), `CHAN_ITEM` (3), `CHAN_BODY` (4), `CHAN_5` (5), `CHAN_6` (6), `CHAN_7` (7).
  - Channel-modifier flags (OR-able): `CHAN_LISTENERZ` (8), `CHAN_MAYBE_LOCAL` (16), `CHAN_UI` (32), `CHAN_NOPAUSE` (64).
  - Note: `CHAN_LOOP` (256) exists in C++ but is not exposed as a named DECORATE constant; pass the numeric literal if needed (rare — see Looping behavior below).
- **volume** — amplitude. Default: 1.0. It is multiplied by the sound's SNDINFO volume and the result is capped at 1.0, so values above 1.0 only matter when the sound's SNDINFO volume is below 1.0. A result of 0 or less plays nothing. In multiplayer the server sends at most 2.0 to clients.
- **looping** — controls whether the sound repeats. Default: false. See Looping behavior section below for important interactions with the `slot` parameter.
- **attenuation** — distance-based volume fading. Default: `ATTN_NORM`. Zandronum defines:
  - `ATTN_NONE` (0.0) — full volume everywhere on the map, regardless of listener distance.
  - `ATTN_NORM` (1.0) — default; the sound's SNDINFO `$rolloff` range, or the global default (Doom's stock SNDINFO sets 200 to 1200 units).
  - `ATTN_IDLE` (1.001) — effectively the same as `ATTN_NORM`. The engine has no special case for it; it is just a distance scale of 1.001.
  - `ATTN_STATIC` (3.0) — rapid fade. Listener distance is multiplied by 3 before the rolloff is applied, so with Doom's default 200 to 1200 rolloff the sound goes silent at 400 units.
  - Any other positive value works the same way, as a multiplier on listener distance (further multiplied by the sound's SNDINFO `$attenuation`).

## Looping behavior

The `looping` parameter and the `CHAN_LOOP` (256) flag interact in two distinct paths:

- **`looping=false` (default):** The `slot` value is passed to the sound system unchanged, so the sound plays once unless the `CHAN_LOOP` flag (256) is OR-ed into `slot`, in which case it loops. On a server, a `CHAN_LOOP` call returns early if the server's looping-channel list already records that same sound on that channel; otherwise the list entry for that channel is updated (a call without `CHAN_LOOP` removes it).
- **`looping=true`:** The sound loops indefinitely. The function guards against re-triggering: if that actor is already playing that same sound-id on that channel (checked via `S_IsActorPlayingSomething`), the call returns early. On a server, it also returns early if the looping-channel list already records that same sound on that channel. If the call proceeds, `CHAN_LOOP` is internally added to the channel when passed to the sound system, and the server tracks this as an active looping channel for synchronization to newly joined clients.

In both paths, starting a sound on a channel (other than `CHAN_AUTO`, which picks a free one) stops whatever that actor was already playing on it, looping or not. `A_StopSound` stops it explicitly.

## Network behavior

**Server-side only in multiplayer, with replication to clients.** If the calling actor's `+CLIENTSIDEONLY` flag is not set, the function returns immediately on the client side; the server alone handles the call (it plays no audio itself) and broadcasts the sound to all clients via `SERVERCOMMANDS_SoundActor`. For actors flagged `+CLIENTSIDEONLY`, the function runs on each client's local copy of that actor (cosmetic-only sounds). The server maintains a per-actor list of active looping channels (per `SERVER_UpdateLoopingChannels`) so that looping sounds re-synchronize to clients that join mid-game.

## Zandronum-specific: network-authoritative sound replication

The server-side-only/replication model described in "Network behavior" above does not exist on
UZDoom. UZDoom's `A_PlaySound` (`src/sound/s_doomsound.cpp:643`) is a thin parameter-remapping
wrapper: it folds `looping` into the `CHANF_LOOP|CHANF_NOSTOP` channel flags and `local` into
`CHANF_LOCAL`, then calls straight into `A_StartSound` → `S_PlaySoundPitch`
(`src/sound/s_doomsound.cpp:608`), which plays (or, if `CHANF_LOCAL` is set, conditionally plays
only for the calling client via `AActor::CheckLocalView`) without any server/client branch, any
equivalent of `SERVERCOMMANDS_SoundActor`, or a `SERVER_UpdateLoopingChannels`-style resync list.
The `+CLIENTSIDEONLY` flag itself is a no-op on UZDoom — `src/scripting/thingdef_data.cpp:458`
registers it as a dummy flag, parsed for DECORATE compatibility but
without effect. This matches a pattern seen across most of this cohort: UZDoom has no
client/server network-authority split anywhere in its source tree.

## Engine-family divergence: parameter count, deprecation, and channel constant

UZDoom's native declaration (`wadsrc/static/zscript/actors/actor.zs:1306`) carries the full
7-parameter signature the ZDoom wiki describes (`whattoplay`, `slot`, `volume`, `looping`,
`attenuation`, `local`, `pitch`) — confirming, on the primary engine itself rather than by wiki
inference, that the "Note: Engine-family divergence" paragraph above describes a real UZDoom/
Zandronum split rather than just a wiki-vs-Zandronum one. UZDoom's declaration is also marked
deprecated since 4.3 in favor of `A_StartSound`, and unlike Zandronum, `A_StartSound` genuinely
exists on UZDoom (`wadsrc/static/zscript/actors/actor.zs:1307`) as the current recommended
interface — `A_PlaySound` is a legacy call-through, not the production interface, on this engine.
Separately, UZDoom exposes `CHAN_LOOP` (256) as a named constant in the global `ESoundFlags` enum
(`wadsrc/static/zscript/engine/base.zs:41`), usable directly in DECORATE/ZScript source, unlike
Zandronum where the same numeric value has no named constant.

## See also

- `A_StopSound` — stop a sound on a specific channel.
- `A_PlaySoundEx` — an older interface taking a different parameter structure and type (sound + name-type channel + bool looping + int attenuation_raw) — see `src/thingdef/thingdef_codeptr.cpp:536`.
