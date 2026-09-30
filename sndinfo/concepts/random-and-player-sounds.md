# Random, alias, player and pitch commands

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/sound/s_advsound.cpp` (the `SI_Random`,
`SI_Alias`, `SI_Singular`, `SI_PlayerSound*`, `SI_PlayerCompat`, `SI_PlayerAlias`,
`SI_PitchShift*` and `SI_PitchSet` cases, `S_ParsePlayerSoundCommon`, `S_LookupPlayerSound`,
`S_GetSoundClass`, `S_FindSkinnedSound`, `S_CheckIntegrity`), `src/common/audio/sound/s_sound.cpp`
(`StartSound`, `CalcPitch`, `CheckSingular`, `PickReplacement`, `AddRandomSound`),
`src/sound/s_doomsound.cpp` and `src/d_netinfo.cpp`, and the Zandronum source's
`src/s_advsound.cpp`, `src/s_sound.cpp`, `src/p_user.cpp`, `src/d_netinfo.cpp` and
`src/sound/fmodsound.cpp`.

These commands make one logical name stand for other sounds (`$random`, `$alias`), give each
player class and gender its own version of a sound (`$playersound` family), and vary pitch
(`$pitchshift`, `$pitchshiftrange`, `$pitchset`). `$singular` is here because its interaction
with indirection is the thing that bites. Lump grammar and the full command list are in
[the SNDINFO lump](sndinfo-lump.md).

## `$random`

```text
$random <name> { <logicalname> <logicalname> ... }
```

```text
$random monster/mysight { monster/mysight1 monster/mysight2 monster/mysight2 }
```

- `<name>` is created, or redefined if it already existed (any lump it pointed at is dropped).
  The listed names are looked up tentatively, so they may be defined later.
- **Each play picks one entry uniformly at random.** A name listed twice is twice as likely. An
  entry that is itself a `$random` name is resolved again at play time, so lists nest.
- **An entry with no sound behind it silences its share of plays.** An entry mapped to a lump
  that doesn't exist, or never defined at all, is still picked at its normal rate. The pick
  happens before the sound is loaded, and a sound with no lump loads as the empty sound, which
  `StartSound` returns on without playing and without any message at play time (Zandronum `S_StartSound`,
  `s_sound.cpp:974-978`, `:1049-1055`, `S_LoadSound` `:1363-1375`; UZDoom `StartSound`,
  `s_sound.cpp:440-461`, `:512-518`). One bad entry in a four-entry list mutes a quarter of plays,
  which reads as an intermittent sound bug rather than a missing file. See
  [the SNDINFO lump](sndinfo-lump.md) for the missing-lump rule itself.
- **One entry makes it an `$alias`** of that entry. **Zero entries** leave `<name>` defined with
  no sound.
- **Listing `<name>` inside its own list** is caught differently per engine; see the divergence
  section.

## `$alias`

```text
$alias <name> <target>
```

`<name>` plays whatever `<target>` resolves to at play time; `<target>` may be defined later, and
may itself be an alias, a `$random` name or a player sound. Chains are followed until a sound
with a lump is reached.

## What an indirect name takes from its target

When the name being played is an `$alias` or `$random` (or a player sound), each playback property
is taken from a specific point in the resolution chain, not always the one you set it on
(UZDoom `StartSound` in `s_sound.cpp:397-500`, Zandronum `S_StartSound` in `s_sound.cpp:950-1035`):

| Property | Taken from |
|---|---|
| [`$volume`](sound-limits-and-rolloff.md) | **The name played.** A target's `$volume` is ignored when reached through an alias or random name. |
| [`$attenuation`](sound-limits-and-rolloff.md) | **The final sound.** A `$random` name's own `$attenuation` also multiplies in; an `$alias` name's does not. |
| [`$limit`](sound-limits-and-rolloff.md) count and range | The name played, unless it is an `$alias`/`$random` without its own `$limit`, in which case the next name down the chain. |
| [`$rolloff`](sound-limits-and-rolloff.md) | The first name in the chain, starting with the one played, that has a `$rolloff`; else the global `$rolloff *`. |
| `$pitchshift` | The final sound. |
| `$pitchset` (UZDoom) | Same rule as `$limit`. |
| `$singular` | The final sound (see below). |

`$alias` and a multi-entry `$random` both reset the name's limit to "take the target's", so a
`$limit` meant for the alias name itself has to come after the `$alias`/`$random` line.

## `$singular`

```text
$singular <name>
```

A singular sound does not start while another instance of it is already playing anywhere
(the new play is evicted, not queued). The flag is read from the **final** resolved sound, and
the "already playing" test compares against the name each playing channel was **started with**
(`CheckSingular`: UZDoom `s_sound.cpp:799`, Zandronum `s_sound.cpp:1466`). So `$singular` works
only for a sound that is always played by its own name. Put it on a target that is reached
through an `$alias` or `$random` and the flag is found, but the test looks for channels started
under the target's name, never finds the ones started through the alias, and lets every copy
play.

## Player sounds

Player sounds are logical names (by convention starting with `*`, such as `*pain100`, `*death`,
`*jump`) whose actual sound depends on who plays them.

```text
$playersound     <class> <gender> <*name> <lump>
$playersounddup  <class> <gender> <*name> <*existingname>
$playeralias     <class> <gender> <*name> <logicalname>
$playercompat    <class> <gender> <*name> <compatname>
```

```text
$playersound    mymarine male   *jump     DSMYJUMP
$playersound    mymarine female *jump     DSMYFJMP
$playersounddup mymarine male   *land     *jump
$playeralias    mymarine male   *usefail  misc/mynoway
```

- **The first use of `<*name>` reserves it** as a player sound, on any of the four commands
  (`S_ParsePlayerSoundCommon`: UZDoom `s_advsound.cpp:1367`, Zandronum `:1466`). A name already
  defined as an ordinary sound cannot become a player sound, and a reserved name can never be
  redefined by a plain mapping, `$alias` or `$random`; both are fatal errors. A name only
  referenced so far (for example by an earlier `$limit`) can still become a player sound.
- **`<class>`** is a sound-class string, not an actor class. A player plays with its pawn's
  `Player.SoundClass` (default `player`), or with its skin's name when it uses a skin rather than
  a class's own look. A non-player actor playing a `*` sound uses `player`, or `fighter` in
  Hexen. The **first class named by a `$playersound`, `$playersounddup` or `$playeralias`, in
  load order, becomes the default class** used as the fallback below (`$playercompat` does not
  create a class).
- **`<gender>`** is matched against a fixed word list; an unrecognized word means male. The
  lists differ per engine (see divergence).
- `$playersound`: plays `<lump>`, looked up the same way as a mapping. Naming the lump `dsempty`
  marks the entry as deliberately silent, which stops the fallback below from replacing it.
- `$playersounddup`: reuses whatever `<*existingname>` is **at that point in parsing** for the
  same class and gender. `<*existingname>` must already be a player sound, or parsing stops with
  "... is not a player sound".
- `$playeralias`: plays an ordinary logical sound, which may be defined later.
- `$playercompat`: defines the ordinary name `<compatname>` as a link to this class and gender's
  `<*name>`, for code that still plays an old non-star name. A later plain mapping of
  `<compatname>` changes the player sound's target instead of breaking the link.

**Lookup and fallback at play time** (`S_LookupPlayerSound`: UZDoom `:1538`, Zandronum `:1658`):
the entry for the player's sound class and gender is used. If that class is unknown, the default
class is used. If the class has no entries for that gender, the first gender slot that has any is
used. If the chosen entry has no usable lump (and is not a deliberate `dsempty`), the male entry
of the same class is tried, then the default class.

Skins add to the same tables: a skin's `*`-prefixed sound keys only register names SNDINFO has
already reserved with a player-sound command. See
[SKININFO](../../zandronum-lumps/concepts/skininfo.md) for the skin side.

## Pitch variation

```text
$pitchshift      <name> <0-7>
$pitchshiftrange <0-7>
$pitchset        <name> <pitch> [<maxpitch>]     (UZDoom only)
```

- **`$pitchshift`** gives a sound random pitch variation. The number n becomes a mask of
  2^n - 1, and each play adds one random value in `0..mask` and subtracts another, on a scale
  where 128 is normal pitch. So 0 means none, 3 means up to 7/128 either way, and 7 (the clamp)
  up to 127/128. It only takes effect while the `snd_pitched` cvar is on, which defaults to off
  (on for Heretic and Hexen configs). The value is read from the final resolved sound.
- **`$pitchshiftrange`** sets the default mask given to sounds created after this point in
  parsing. It is not reset between SNDINFO lumps, so a value left at the end of one lump carries
  into every later one. Sounds created earlier keep what they had.
- **`$pitchset`** (UZDoom only) sets a fixed pitch multiplier (1.0 is normal), or, with a second
  value different from the first, a uniform random multiplier between the two. It overrides
  `$pitchshift` and works regardless of `snd_pitched`. A pitch passed explicitly by the playing
  code (for example `A_StartSound`'s pitch argument) overrides it. Values of 0 or less mean
  "not set" (UZDoom `CalcPitch`, `s_sound.cpp:368-385`).

## Engine-family divergence

- **`$pitchset`** exists only on UZDoom. On Zandronum it is an unknown command, and its two or
  three arguments are read as logical mappings (see the lump page's gotchas).
- **Self-referencing `$random`.** Zandronum drops an entry equal to the list's own name and
  prints "Definition of random sound '...' refers to itself recursively." UZDoom's in-parser
  version of that check compares against a field that is not yet set, so it never fires; instead
  the post-parse integrity check prints the cycle and disables the whole `$random` name, which
  then plays nothing (`S_CheckIntegrity`, `s_advsound.cpp:320`). Longer cycles through `$alias`
  are also caught there on UZDoom and not at all on Zandronum.
- **Limit and rolloff through a player sound.** When a `*` name resolves to a class entry,
  Zandronum always takes `$limit` and `$rolloff` from that entry. UZDoom applies the general rule
  in the table above: a `*` name is not an alias, so its own limit (the default 2, or a
  `$limit` set on it) applies, and a `$rolloff` set on it wins over the entry's.
- **Gender words.** UZDoom has four gender slots: `male` (and any unrecognized word), `female`,
  `neutral`/`neuter`, and `other`/`object`/`cyborg`. Zandronum has three: `male` (and any
  unrecognized word, including `neutral`), `female`, and `other`/`cyborg`; it also accepts the
  digits `0`, `1`, `2` (`D_GenderToInt` in each engine's `d_netinfo.cpp`). So `other` is a fourth
  slot on UZDoom but the neuter slot on Zandronum, and a `neutral` line silently overwrites the
  male entry on Zandronum.
- **Gender fallback off-by-one (Zandronum).** Zandronum's "first gender with any entries" loop
  increments past the slot it found, so a class whose only entries are in the third (neuter)
  slot is treated as having none and falls back to the default class. UZDoom breaks out
  correctly.
- **Skin sound class (Zandronum).** Zandronum uses a skin's name as the sound class only when the
  `cl_skins` cvar allows skins (and, at 2 or higher, only non-cheat skins), and also applies it to
  a dead player's corpse (`APlayerPawn::GetSoundClass`, `p_user.cpp:1459`).
- **Pitch source (UZDoom).** UZDoom creates a tentatively referenced sound with a zero pitch mask
  and keeps that mask when the name is later mapped to a lump, so a sound first mentioned by a
  property command before its mapping ignores `$pitchshiftrange`. Zandronum gives tentative
  sounds the current default too. Zandronum's `snd_pitched` gate sits in its FMOD sound backend
  (`fmodsound.cpp:78`) and so applies to every pitch change, not only `$pitchshift`.
