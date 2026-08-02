# `void A_PlaySoundEx(sound whattoplay, coerce name slot [, bool looping [, int attenuation]])`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_PlaySoundEx` (retrieved 2026-08-01, oldid=47286) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:536` and `wadsrc/static/actors/actor.txt:202`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS` on `AActor` (`src/thingdef/thingdef_codeptr.cpp:536`).

Plays a sound from the calling actor on a named channel. This is an older interface; **use `A_PlaySound` for new code**, which offers a volume parameter and clearer attenuation semantics. A_PlaySoundEx is not deprecated in Zandronum (unlike GZDoom/ZDoom upstream, which prefer `A_StartSound` — not available in Zandronum).

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
- **Attenuation encoding differs.** A_PlaySound accepts float attenuation values (`ATTN_NONE`, `ATTN_NORM`, `ATTN_IDLE`, `ATTN_STATIC` constants); A_PlaySoundEx converts an integer to one of four fixed float values.

## Looping behavior

Same as A_PlaySound: two distinct code paths based on the `looping` parameter. If `looping=true`, the function guards against re-triggering by checking `S_IsActorPlayingSomething`. Looping channels persist per-actor and re-synchronize to clients joining mid-game.

## Network behavior

**Server-side only in multiplayer, with replication to clients**, except for actors flagged `+CLIENTSIDEONLY` (cosmetic sounds run locally on each client). Server maintains per-actor looping-channel state for client sync on join.

## Implementation note

A potential issue: in the `!looping` branch, the code tests `channel & CHAN_LOOP` (bit 8) on a name-table index clamped to `[NAME_Auto, NAME_SoundSlot7]` — meaningless as a loop flag. This appears to be unadapted copy-paste from `A_PlaySound` where `channel` is an int bitmask. Behavior matches intention (sound does not loop), but the bitwise test is vestigial — **this aspect is flagged for future tracing, not fully verified**.

## See also

- `A_PlaySound` — the preferred newer interface with volume parameter and cleaner channel semantics.
- `A_StopSoundEx` — stops a sound on a named channel.
- `A_StopSound` — stops a sound on a numbered channel.
