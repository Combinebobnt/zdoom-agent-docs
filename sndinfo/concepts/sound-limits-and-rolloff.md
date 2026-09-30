# Per-sound playback properties: limits, volume, attenuation, rolloff, rumble

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/sound/s_advsound.cpp` (the `SI_Limit`,
`SI_Volume`, `SI_Attenuation`, `SI_Rolloff`, `SI_RumbleDef` and `SI_Rumble` cases),
`src/common/audio/sound/s_sound.cpp` (`StartSound`, `CheckSoundLimit`, `GetRolloff`),
`src/common/audio/sound/s_soundinternal.h`, `src/common/audio/sound/oalsound.cpp`,
`src/sound/s_doomsound.cpp` and `src/common/engine/m_haptics.cpp`, and the Zandronum source's
`src/s_advsound.cpp`, `src/s_sound.cpp` (`S_StartSound`, `S_CheckSoundLimit`, `S_GetRolloff`)
and `src/sound/fmodsound.cpp`; `wadsrc/static/sndinfo.txt` of each engine checked for the stock
global rolloff.

These commands attach playback properties to an already named sound. Each takes a logical name
that is looked up tentatively, so the property line may come before the mapping that gives the
name a lump. When the name played is an `$alias`, `$random` or player sound, which name in the
chain each property is read from is a separate rule: see
[what an indirect name takes from its target](random-and-player-sounds.md#what-an-indirect-name-takes-from-its-target).

## `$limit`

```text
$limit <name> <count> [<distance>]
```

- **Default for every SNDINFO-defined sound: 2 within 256 map units.** An `$alias` or multi-entry
  `$random` name instead defaults to "use the target's limit".
- `<count>` is clamped to 0 to 255; **0 means unlimited**. `<distance>` is optional and keeps the
  current range when omitted.
- When a sound starts, the engine counts channels already playing the **same resolved sound**
  whose origin is within `<distance>` of the new one. If the count has reached `<count>`, the new
  play is evicted and not heard (`CheckSoundLimit`: UZDoom `s_sound.cpp:828`, Zandronum
  `s_sound.cpp:1495`).
- **Never limited:** unpositioned sounds, sounds whose source is the listener (the local player's
  camera actor), and an actor restarting the same sound on the same channel.

## `$volume`

```text
$volume <name> <volume>
```

A multiplier (default 1.0) applied to the volume the playing code asks for. The product is capped
at 1.0, and a product of 0 or less means the sound is not played at all (UZDoom
`s_sound.cpp:426-429`, Zandronum `s_sound.cpp:953-956`). So values above 1.0 only let a caller's
below-1.0 volume reach full volume sooner; they cannot make a sound louder than full. It is read
from the name that was played, before any `$alias`/`$random` resolution. Callers:
[`A_PlaySound`](../../decorate/actions/a_playsound.md),
[`AmbientSound`](../../acs/functions/ambientsound.md) and the other ACS sound functions document
their own volume ranges against this cap.

## `$attenuation`

```text
$attenuation <name> <multiplier>
```

A multiplier (default 1.0) on the attenuation the playing code asks for (`ATTN_NORM` is 1,
`ATTN_NONE` is 0). The resulting value scales the listener distance before rolloff is applied, so
2.0 makes the sound fade twice as fast and 0 makes it audible at full volume everywhere. It is
read from the final resolved sound; a `$random` name's own value also multiplies in.

## `$rolloff`

```text
$rolloff <name|*> [linear|log|custom] <min distance> <max distance or rolloff factor>
```

```text
$rolloff *            200 1200
$rolloff world/mydrip linear 64 512
```

Sets the distance curve. `*` sets the global default for every sound without its own. The stock
SNDINFO of both engines sets `$rolloff * 200 1200` (Doom and Strife), `custom 0 1600` for
Heretic and `custom 0 2025` for Hexen; the global entry may have a min distance of 0. Without a
type keyword the curve type is left unchanged, which for a fresh sound is the Doom curve.

| Type | Below min | Between min and max | At or beyond max |
|---|---|---|---|
| (none: Doom curve) | full volume | `(10^v - 1) / 9`, where v falls linearly from 1 at min to 0 at max | silent |
| `linear` | full volume | v, linear | silent |
| `log` | full volume | `min / (min + factor * (distance - min))`; the second number is a rolloff factor, not a distance | never silent |
| `custom` | full volume | read from the `SNDCURVE` lump (one byte per step, 127 is full) | silent |

(UZDoom `GetRolloff`, `s_sound.cpp:1293-1324`; Zandronum `S_GetRolloff`, `s_sound.cpp:2211`.)

- The distance fed to the curve is the real distance multiplied by the attenuation above.
- **A min distance of 0 means "no rolloff set"**: that sound falls through to its target's
  rolloff and then to the global one. A sound cannot opt out of the global curve with `0`.
- A falloff range passed explicitly by the playing code overrides SNDINFO's (for example an
  [`AmbientSound` thing's](ambient-sounds.md#the-ambientsound-thing) min/max distance
  arguments).
- An unknown type keyword is a fatal error.

## `$rumbledef` and `$rumble` (UZDoom only)

```text
$rumbledef <id> <tics> <strength A> <strength B> <left trigger> <right trigger>
$rumbledef <newid> <existing id>
$rumble    <logicalname> <id>
```

Game-controller vibration (UZDoom `s_advsound.cpp:1268-1323`, `m_haptics.cpp`).

- **`$rumbledef`** defines a named vibration pattern: a duration in tics (0 or less means
  "never rumbles") and four strengths. When the token after `<id>` is an identifier rather than
  a number, the line instead makes `<newid>` an alias of an existing pattern; aliases are
  resolved after all SNDINFO is parsed, and an alias may not reuse a name that is already a full
  definition.
- **Strength order.** The source comment names the two motor values low-frequency then
  high-frequency, but the parser stores `<strength A>` in the high-frequency field and
  `<strength B>` in the low-frequency field, matching the order of the `rumble` console
  command's test form (`tics high low left right`).
- **`$rumble`** ties a logical sound name to a pattern. When that name is started with the
  rumble hint, the pattern plays. The lookup uses the name that was played; if it has no
  mapping, UZDoom follows its `$alias` chain (and the first entry of a `$random`) a few levels
  deep, then tries the part from `*` onward for a player-class sound.
- **Which plays rumble.** The hint is added automatically, when the `haptics_do_action` cvar is on
  (default), to sounds made by the local player's own actor or its missiles; also to menu and
  some world sounds under the `haptics_do_menus` and `haptics_do_world` cvars. ZScript can force
  or suppress it per call with `CHANF_RUMBLE`/`CHANF_NORUMBLE`.

## Engine-family divergence

- **Limit range scales with attenuation (UZDoom).** UZDoom divides the squared limit range by the
  smaller of the new sound's and the playing channel's attenuation, so a quieter-falling sound
  counts neighbors further away, and a sound played with attenuation 0 counts every instance on
  the map. Zandronum compares plain distance against the range.
- **Rumble** commands exist only on UZDoom. On Zandronum `$rumbledef` and `$rumble` are unknown
  commands, and their arguments are read as logical mappings, which shifts the rest of the lump
  (see the lump page's gotchas). Keep them out of any SNDINFO Zandronum also loads.
- **`custom` curve.** With no `SNDCURVE` lump, both engines use the Doom curve. With one, UZDoom
  returns the table value directly, while Zandronum's FMOD path feeds the table value through the
  Doom-curve formula again (`S_GetRolloff`, `s_sound.cpp:2232-2245`), so the same table is
  quieter at mid distances on Zandronum. The other three types match.
