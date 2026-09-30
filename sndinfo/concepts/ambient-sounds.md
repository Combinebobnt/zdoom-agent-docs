# Ambient sounds: `$ambient` and the `AmbientSound` thing

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/sound/s_advsound.cpp` (`SI_Ambient` case,
`GetTicker`, the `AAmbientSound` native `Tick`/`Activate`/`Deactivate`),
`wadsrc/static/zscript/actors/shared/soundsequence.zs` and `wadsrc/static/mapinfo/common.txt`,
and the Zandronum source's `src/s_advsound.cpp` (`SI_Ambient` case, `AAmbientSound`),
`src/p_mobj.cpp`, `src/cl_main.cpp` and `wadsrc/static/actors/shared/soundsequence.txt`.

`$ambient` defines a numbered ambient-sound slot: which logical sound, how it is positioned, how
often it repeats and how loud it is. Nothing plays until a map places an `AmbientSound` thing
whose first argument names that slot. This is unrelated to the ACS function
[`AmbientSound`](../../acs/functions/ambientsound.md), which plays a one-shot unpositioned sound
from a script.

## Syntax

```text
$ambient <index> <logicalname> [point [<attenuation>] | surround | world] <timing> <volume>

<timing> is one of:
    continuous
    random <min seconds> <max seconds>
    periodic <seconds>
```

```text
$ambient 1 world/wind   world continuous 0.5
$ambient 2 world/drip   point 1.5 random 2.0 6.0 0.8
$ambient 3 world/gong   periodic 10 1.0
```

(UZDoom `s_advsound.cpp:800-889`, Zandronum `s_advsound.cpp:1000-1089`; identical.)

- **`<index>`** is any integer. It is a map key, not an array slot, so indices need not be
  contiguous. A later `$ambient` with the same index, in any SNDINFO lump, replaces the earlier
  definition completely.
- **`<logicalname>`** is looked up tentatively: it may be defined later in the same or another
  SNDINFO lump. If it is never defined, the slot exists but plays nothing.
- **Positioning** (optional, default `world`):
  - `world`: attenuation 0, so the sound is heard at full volume everywhere on the map, like a
    non-positional sound. The word itself may be omitted.
  - `point`: positional, heard from the thing's location. An optional number after it is the
    attenuation multiplier; missing, zero or negative means 1.
  - `surround`: stores attenuation -1.
- **`<timing>`**, with seconds converted to tics at 35 per second and truncated:
  - `continuous`: started once as a looping sound on the thing's `CHAN_BODY` channel.
  - `random <min> <max>`: replayed after an interval drawn uniformly between min and max.
  - `periodic <n>`: replayed every n seconds.
  - Anything else prints "Unknown ambient type (...)" and is consumed as if it were the timing
    word. The slot then behaves as if its period were the sound's own length, replaying it back
    to back without a loop flag.
- **`<volume>`** is clamped to 0.0 to 1.0.

## The `AmbientSound` thing

| Editor number | Class | First argument |
|---|---|---|
| 14065 | `AmbientSound` | set in the map |
| 14067 | `AmbientSoundNoGravity` (same, with `NOGRAVITY`) | set in the map |
| 14001 to 14064 | `AmbientSound` | preset to 1 to 64 (thing number minus 14000) |

The 14001 to 14064 range is the Hexen-format shortcut: the thing type itself picks the slot, and
any args set on the thing are overridden for the first argument.

Arguments:

1. **Ambient index**: the `$ambient` slot to play.
2. **Volume percent**: scales the slot's volume; 0 and 100 both mean unchanged. The product is
   clamped to 1.0, so this can only make a sound louder when the slot's volume is below 1.
3. **Minimum distance** and 4. **maximum distance**: when both are set and min is not greater
   than max, the sound is played with this explicit falloff range instead of the slot's
   attenuation and the sound's [rolloff](sound-limits-and-rolloff.md). Leave both 0 for the
   normal behavior.
5. **Distance multiplier**: if positive, multiplies arguments 3 and 4.

Behavior (UZDoom `AAmbientSound` natives at `s_advsound.cpp:1893-2034`, Zandronum
`AAmbientSound` at `s_advsound.cpp:2152-2325`):

- **It starts active.** The thing activates itself when spawned. A `continuous` slot starts
  playing on the next tic; a `random` or `periodic` slot waits one interval before its first play.
- **Thing activation toggles it.** Deactivating (for example with `Thing_Deactivate`) stops a
  `continuous` sound immediately and stops future repeats of the other types, while letting a
  repeat already playing finish. Reactivating resumes it. Activating an already active thing
  does nothing.
- **An index with no `$ambient` definition destroys the thing** when it activates, silently. A
  defined slot whose logical name was never mapped to a lump keeps the thing alive but plays
  nothing.

## Engine-family divergence

The `$ambient` parser, the argument meanings and the timing math are the same on both engines.
Differences are in the thing's surroundings:

- **Implementation form.** On UZDoom `AmbientSound` is a ZScript class whose `Tick`, `Activate`
  and `Deactivate` are native; editor numbers come from MAPINFO `DoomEdNums` in the engine's
  `mapinfo/common.txt`. On Zandronum it is a native DECORATE actor, and the 14001 to 14064
  remapping is hard-coded in spawn code (`p_mobj.cpp:6092-6096`).
- **Zandronum clients.** A client receives the thing's arguments after it is spawned, so the
  client does not destroy an `AmbientSound` whose slot lookup fails before the arguments arrive;
  it re-runs `BeginPlay` once they are set (`cl_main.cpp:5557-5563`). Ambient sounds are then
  played locally on each client.
- **Blood ambients (Zandronum only).** When Zandronum registers Blood `.SFX` lumps it also
  creates a `continuous` ambient slot for each, keyed by the lump's RFF index number (0 outside
  RFF archives). Those share the `$ambient` numbering, so a Blood slot and a mod's slot with the
  same number replace each other in load order (`S_AddBloodSFX`, `s_advsound.cpp:1409-1440`). UZDoom no longer registers
  Blood sounds.
