# `void A_PlaySoundEx(sound whattoplay, coerce name slot [, bool looping [, int attenuation]])`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_PlaySoundEx` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_PlaySoundEx&oldid=47286) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:536` and `wadsrc/static/actors/actor.txt:202`; deprecation comment `src/thingdef/thingdef_codeptr.cpp:521-524`; loop bookkeeping `src/thingdef/thingdef_codeptr.cpp:572-595`, `src/namedef.h:51-58`, `src/s_sound.h:265`, `src/sv_main.cpp:4437-4465` and `src/sv_main.cpp:2997-2999`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS` on `AActor` (`src/thingdef/thingdef_codeptr.cpp:536`).

Plays a sound from the calling actor on a named channel. This is an older interface; **use `A_PlaySound` for new code**, which offers a volume parameter and clearer attenuation semantics. On Zandronum, calling A_PlaySoundEx never produces a deprecation warning. Its own source still calls it deprecated in favor of extending `A_PlaySound` (the comment above `A_PlayWeaponSound`, `src/thingdef/thingdef_codeptr.cpp:521-524`). GZDoom/ZDoom upstream prefer `A_StartSound` — not available in Zandronum.

## Parameters

- **whattoplay** — a sound identifier (e.g., `"weapons/pistol"`). No default (required).
- **slot** — the sound channel name. Accepts channel names or strings coerced to names. Valid channels (in order):
  - `Auto` (0)
  - `Weapon` (1)
  - `Voice` (2)
  - `Item` (3)
  - `Body` (4)
  - `SoundSlot5` (5)
  - `SoundSlot6` (6)
  - `SoundSlot7` (7)
  - Out-of-range names silently clamp to `Auto`.
- **looping** — controls whether the sound repeats. Default: `false`.
- **attenuation** — distance-based volume fading control. Default: `0`. Maps as:

| Value | Behavior |
|---|---|
| -1 | Drops off rapidly with distance (`ATTN_STATIC` in source) |
| 0 | Plays as normal, using sound's close_dist/clipping_dist (`ATTN_NORM` in source) |
| 1 | Plays at full volume everywhere in the level |
| 2 | Plays at full volume everywhere in the level; **no surround-sound distinction in Zandronum** (both 1 and 2 map to `ATTN_NONE` in source) |
| out-of-range | Silently treated as 0 (`ATTN_NORM`) |

## Key differences from A_PlaySound

- **No volume control.** Both internal `S_Sound` calls pass hardcoded volume `1.0`. Use `A_PlaySound` if you need dynamic volume.
- **Channel parameter is a name, not an int.** A_PlaySoundEx accepts named channel identifiers; A_PlaySound accepts integer channel values with optional bitwise flags.
- **Attenuation encoding differs.** A_PlaySound accepts float attenuation values (`ATTN_NONE`, `ATTN_NORM`, `ATTN_IDLE`, `ATTN_STATIC` constants); A_PlaySoundEx converts an integer to one of three fixed float values (1 and 2 both become `ATTN_NONE`).

## Looping behavior

Same as A_PlaySound: two distinct code paths based on the `looping` parameter. If `looping=true`, the function guards against re-triggering by checking `S_IsActorPlayingSomething`. Looping channels persist per-actor and re-synchronize to clients joining mid-game.

## Network behavior

**Server-side only in multiplayer, with replication to clients**, except for actors flagged `+CLIENTSIDEONLY` (cosmetic sounds run locally on each client). Server maintains per-actor looping-channel state for client sync on join.

## Implementation note

The `!looping` branch's server bookkeeping (`src/thingdef/thingdef_codeptr.cpp:572-575`) was copied from `A_PlaySound`, where `channel` is an int bitmask, but here `channel` is still the raw name index. `NAME_Auto` through `NAME_SoundSlot7` are name indexes 34-41 (`src/namedef.h:51-58`, counting from `None` = 0), and none of them has bit 256 (`CHAN_LOOP`, `src/s_sound.h:265`) set. So the `channel & CHAN_LOOP` early-return test never fires, and the following `SERVER_UpdateLoopingChannels` call always removes a record. It passes the raw name index, not `int(channel) - NAME_Auto` as the looping branch does (line 595). `SERVER_UpdateLoopingChannels` keys on `channel & 7` (`src/sv_main.cpp:4437-4465`), so a non-looping call on slot N removes the server's looping record for channel `(N + 2) & 7` (e.g. `Auto` removes `Voice`'s, `SoundSlot7` removes `Weapon`'s), and leaves slot N's own record alone. The sound itself plays on the correct channel (line 578), and `looping` still decides whether it loops. What goes wrong is the list the server replays to a client joining mid-game (`src/sv_main.cpp:2997-2999`): that client can be sent a stale loop, or miss one that is still playing.

## Engine-family divergence: deprecated in favor of A_StartSound

UZDoom's declaration (`wadsrc/static/zscript/actors/actor.zs:1315`) carries a formal `deprecated("2.3", "Use A_StartSound() instead")` attribute — a stronger claim than the intro prose's "prefer" framing above, which describes upstream style guidance rather than UZDoom's own declaration site. In practice the warning is narrower than the attribute alone suggests: `FxVMFunctionCall::CheckAccessibility` (`src/common/scripting/backend/codegen.cpp:9761-9790`) only emits the "Accessing deprecated function" warning when the *calling* code's compiled `VersionInfo` is `>= 2.3`; DECORATE action-function calls compile at a fixed `MakeVersion(0,0)` (`src/scripting/decorate/thingdef_exp.cpp:70`), which is below that threshold, so a DECORATE state table calling `A_PlaySoundEx` gets no warning at all — only ZScript code compiled at version 2.3+ sees it. Also note `A_PlaySound` itself is deprecated on UZDoom too, since version 4.3 in favor of `A_StartSound` (same file, line 1306) — so on UZDoom the "use `A_PlaySound` for new code" advice in the intro above is itself superseded; `A_StartSound` (line 1307, no deprecation attribute) is the actual current replacement.

## Engine-family divergence: no vestigial bitwise loop test

UZDoom's `A_PlaySoundEx` (`src/playsim/p_actionfunctions.cpp:680`) does not carry the vestigial `channel & CHAN_LOOP` test described in the Implementation note above — `looping` is a genuine `PARAM_BOOL` read directly, and loop state is passed explicitly as the `CHANF_LOOP` flag argument to `S_Sound`, not tested from channel bits. There is no equivalent artifact on this engine, though observable behavior (looping controlled correctly by the `looping` parameter) is the same on both.

## Engine-family divergence: no client/server authority split

UZDoom's `S_Sound(AActor*, ...)` (`src/sound/s_doomsound.cpp:537`) has no server/client gate at all — it calls straight through to the local sound engine (`soundEngine->StartSound`/`S_SoundPitchActor`) with no `NETWORK_InClientMode`/`SERVERCOMMANDS_*`-style check and no per-actor looping-channel replication state. The "Server-side only in multiplayer, with replication to clients" mechanism described above, including the join-sync of looping-channel state, does not exist on UZDoom — the sound plays locally on whichever instance runs the action, every time. `CLIENTSIDEONLY` is registered in UZDoom's actor-flag table only as `DEFINE_DUMMY_FLAG(CLIENTSIDEONLY, false)` (`src/scripting/thingdef_data.cpp:458`) — the flag is accepted for DECORATE compatibility but has no effect, consistent with there being no client/server distinction for it to gate.

## See also

- `A_PlaySound` — the preferred newer interface with volume parameter and cleaner channel semantics.
- `A_StopSoundEx` — stops a sound on a named channel.
- `A_StopSound` — stops a sound on a numbered channel.
