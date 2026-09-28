# `A_PlayWeaponSound`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_PlayWeaponSound` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_PlayWeaponSound&oldid=47751) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:528-534`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Action function on `AActor` (`DEFINE_ACTION_FUNCTION_PARAMS` in `src/thingdef/thingdef_codeptr.cpp`).
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Plays the specified sound using the weapon sound channel. **This function is deprecated.** The Zandronum source comment above it says it was deprecated in favor of the extended `A_PlaySound` (which takes a channel argument) and `A_StopSound`.

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

This hardcodes the channel to `CHAN_WEAPON`, volume to `1.0`, and attenuation to `ATTN_NORM`. The source comment above it says this group of functions dates from before DECORATE had constants at all (so no `CHAN_*` names to pass) and when the sound interface was less flexible. It is preserved for backwards compatibility but should not be used in new code.

## Engine-family divergence: additional `fullvol` parameter

UZDoom implements `A_PlayWeaponSound` as a ZScript wrapper (`wadsrc/static/zscript/actors/actor.zs`) around `A_StartSound`, rather than the direct `S_Sound` call Zandronum's C++ uses, and its signature carries a second parameter Zandronum's version doesn't have at all: `A_PlayWeaponSound(sound whattoplay, bool fullvol = false)`.

With `fullvol` left at its default (`false`), the call still resolves to `CHAN_WEAPON`, volume `1.0`, attenuation `ATTN_NORM` — identical to Zandronum's fully-hardcoded behavior. Passing `fullvol = true` switches the attenuation to `ATTN_NONE` (the sound plays at full volume regardless of distance from the listener), a mode Zandronum's version cannot produce through this function at all, since its implementation hardcodes `ATTN_NORM` with no parameter to override it.

UZDoom's deprecation message also differs in what it recommends: it points to `A_StartSound(<sound>, CHAN_WEAPON)` specifically, rather than Zandronum's source comment, which only says the function was deprecated in favor of extending `A_PlaySound` and `A_StopSound`.

## See also

- `A_PlaySound` — play a sound with full control over channel, volume, and attenuation.
- `A_StopSound` — stop a sound on a specified channel.
