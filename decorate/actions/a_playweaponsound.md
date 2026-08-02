# `A_PlayWeaponSound`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_PlayWeaponSound` (retrieved 2026-08-01, oldid=47751) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:528-534`.
**Bucket:** Action function on `AActor` (`DEFINE_ACTION_FUNCTION_PARAMS` in `src/thingdef/thingdef_codeptr.cpp`).

Plays the specified sound using the weapon sound channel. **This function is deprecated** — the Zandronum source code comments recommend using `A_PlaySound` or `A_StopSound` instead for new code.

## Signature

```decorate
void A_PlayWeaponSound (sound whattoplay)
```

## Parameters

**`whattoplay`** (sound lump name)  
The sound to play. The sound is played on the `CHAN_WEAPON` channel with hardcoded volume `1.0` and normal attenuation.

## Behavior

- Plays the specified sound on the weapon sound channel (`CHAN_WEAPON`).
- The channel, volume, and attenuation are hardcoded and cannot be customized — for more control, use `A_PlaySound` instead.
- Sounds played with `A_PlayWeaponSound` do not interfere with sounds played via `A_PlaySound` unless that function explicitly uses `CHAN_WEAPON` as the channel argument.

## Implementation notes

The Zandronum source implements this function as a simple wrapper:

```c
S_Sound (self, CHAN_WEAPON, soundid, 1, ATTN_NORM);
```

This hardcodes the channel to `CHAN_WEAPON`, volume to `1.0`, and attenuation to `ATTN_NORM`. The function was created when DECORATE had no `sound` constants and the sound interface was less flexible. It is preserved for backwards compatibility but should not be used in new code.

**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

## See also

- `A_PlaySound` — play a sound with full control over channel, volume, and attenuation.
- `A_StopSound` — stop a sound on a specified channel.
