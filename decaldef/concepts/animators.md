# DECALDEF animators: `fader`, `stretcher`, `slider`, `colorchanger`, `combiner`

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/gamedata/decallib.cpp` (`ParseDecal`'s `animator` case, `ParseFader`, `ParseStretcher`, `ParseSlider`, `ParseColorchanger`, `ParseCombiner`, `FindAnimator`, `ReadScale`, `FDecalTemplate::ApplyToDecal`, and each animator's `CreateThinker`), `src/playsim/mapthinkers/a_decalfx.cpp` and `a_decalfx.h` (`DDecalFader`, `DDecalStretcher`, `DDecalSlider`, `DDecalColorer` and their `Tick`), `src/playsim/a_decals.cpp` (`DImpactDecal::StaticCreate`, `CloneSelf`, `DImpactDecal::Expired`, `SetShade`), `src/p_tick.cpp` (`maptime` advance), `src/common/engine/sc_man.cpp` (`ScriptError`, `ScriptMessage`), `src/common/utility/palette.cpp` (`V_GetColor`) and `wadsrc/static/decaldef.txt`, and the Zandronum source's `src/decallib.cpp` (same parser functions, plus the thinker classes and their `Tick`), `src/g_shared/a_decals.cpp` (`DImpactDecal::StaticCreate`, `CloneSelf`, `DImpactDecal::Destroy`, `SetShade`), `src/p_tick.cpp`, `src/sc_man.cpp`, `src/v_video.cpp` (`V_GetColor`) and `wadsrc/static/decaldef.txt`. Keyword names cross-checked against SLADE's `z_decaldef` block in `dist/res/config/languages/zdoom.txt`.

An **animator** is a named effect that changes a decal over time after it is stamped: fade it
out, rescale it, move it down (or up) the wall, or shift its colour. A decal picks one with
`animator <name>` inside its `decal` block. This page covers each animator block's keywords,
units, defaults and runtime behaviour. The outer grammar, load order and redefinition rules are
in [the DECALDEF lump](decaldef-lump.md); the `decal` block itself is in
[decal definitions](decal-definition.md).

## Shared rules

- **Times are seconds, stored as whole tics.** Every `*Start`/`*Time` value is read as a float,
  multiplied by 35 and truncated to an integer (UZDoom `decallib.cpp:586`, `:591`, `:629`,
  `:634`, `:680`, `:685`, `:729`, `:734`; Zandronum `decallib.cpp:666`, `:671`, `:709`, `:714`,
  `:760`, `:765`, `:810`, `:815`). So `0.5` is 17 tics and anything under 1/35 s is 0. The stock
  `BloodStretcher` and `BloodSlider` in both engines' `wadsrc/static/decaldef.txt` say
  `StretchTime 35` and `SlideTime 35`: that is 35 **seconds** (1225 tics), not one second.
- **`*Start` counts from the moment the decal is created**, not from map start: each thinker
  adds it to the current `maptime` (UZDoom `decallib.cpp:1085`, `:1096`, `:1128`, `:1166`;
  Zandronum `decallib.cpp:1195`, `:1221`, `:1307`, `:1424`).
- **No range checks on times.** A negative value is accepted. A negative `*Start` puts the
  animation partly in the past, so it begins mid-way; a negative `*Time` ends it on its first
  active tic, the same as 0. A `*Time` of 0 jumps straight to the end state at `*Start`; no
  animator divides by the zero duration, because each checks "past the end" first.
- **Every block keyword is optional**, and there's no fixed order. Keywords are
  case-insensitive. A keyword may repeat; the last one wins.
- **Not every block registers an animator.** A `fader` or `colorchanger` always does, even an
  empty one. A `stretcher` registers only if it has `GoalX` or `GoalY` (UZDoom
  `decallib.cpp:615`; Zandronum `decallib.cpp:695`). A `slider` registers only if `DistY` is
  nonzero; `DistX` never counts, on either engine (UZDoom `decallib.cpp:666`; Zandronum
  `decallib.cpp:746`). A `combiner` registers only if it lists at least one member (UZDoom
  `decallib.cpp:770`; Zandronum `decallib.cpp:851`). A block that doesn't register leaves its
  name undefined, so a later `animator` line naming it gets no animation (see "Bad input").
- **Animator names are their own namespace, looked up newest first.** `FindAnimator` walks the
  list backwards (UZDoom `decallib.cpp:1147-1159`; Zandronum `decallib.cpp:1357-1369`), so a
  redefined name resolves to the newest definition above the line that names it. Earlier
  `animator` lines, and earlier combiners, keep a pointer to whatever they found at the time.
- **One set of thinkers per decal, on every spawn path.** Applying a decal's template to a new
  decal creates its animator's thinker(s) (UZDoom `decallib.cpp:984-987`; Zandronum
  `decallib.cpp:1058-1061`). That happens for impact decals, the map-placed `Decal` thing and
  ACS `SpawnDecal`, and again for each piece when a decal spreads across a wall edge
  (`CloneSelf`, UZDoom `a_decals.cpp:630-651`, `:770-790`; Zandronum `a_decals.cpp:553`, `:719`).
  Each piece animates on its own timeline, starting when that piece was made.
- **A `lowerdecal` gets its own animator, not the upper one's.** It's spawned as a separate
  decal from its own template (UZDoom `a_decals.cpp:714-725`; Zandronum `a_decals.cpp:679-688`),
  so a fader on the upper decal removes only the upper decal.
- **Start values are captured when the animation starts**, not when the decal spawns: the
  fader's alpha, the stretcher's scale, the slider's height and the colour changer's colour are
  all read on the thinker's first active tic. Anything that changed them in between (another
  animator, or a spawner-supplied colour) is the starting point.
- **Freezing the level doesn't extend the schedule.** While the level is frozen (the
  time-freeze powerup, for example) every animator thinker skips its update, but `maptime`
  keeps advancing (UZDoom `p_tick.cpp:273`; Zandronum `p_tick.cpp:438`). On unfreeze the
  animation jumps to where it would have been; a fader whose end passed during the freeze
  removes its decal on the first unfrozen tic.

## `fader`

```text
fader <name> { DecayStart <sec> DecayTime <sec> }
```

| Keyword | Argument | Default | Meaning | UZDoom | Zandronum |
|---|---|---|---|---|---|
| `DecayStart` | seconds (float) | 0 | Delay after spawn before fading begins | yes | yes |
| `DecayTime` | seconds (float) | 0 | Length of the fade | yes | yes |

**At runtime** (UZDoom `a_decalfx.cpp:55-83`; Zandronum `decallib.cpp:1162-1189`): on the first
tic at or after `DecayStart` it records the decal's current alpha, then lowers it linearly to 0
over `DecayTime`. It changes alpha only; how visible the fade is depends on the decal's render
style (the stock definitions use faders on `add` and `shade` decals).

**At the end it destroys the decal**, then itself. An impact decal removed this way frees its
`cl_maxdecals` slot on both engines (UZDoom calls `DImpactDecal::Expired`,
`a_decals.cpp:678-681`; Zandronum decrements the count in `DImpactDecal::Destroy`,
`a_decals.cpp:746-748`). An empty `fader Name { }` is valid and removes the decal on its first
tic. The fader is the only animator that removes its decal.

## `stretcher`

```text
stretcher <name> { GoalX <scale> GoalY <scale> StretchStart <sec> StretchTime <sec> }
```

| Keyword | Argument | Default | Meaning | UZDoom | Zandronum |
|---|---|---|---|---|---|
| `GoalX` | scale (float), clamped to 1/256 .. 256 | unset: X not animated | Target horizontal scale | yes | yes |
| `GoalY` | scale (float), clamped to 1/256 .. 256 | unset: Y not animated | Target vertical scale | yes | yes |
| `StretchStart` | seconds (float) | 0 | Delay after spawn before stretching begins | yes | yes |
| `StretchTime` | seconds (float) | 0 | Length of the stretch | yes | yes |

`GoalX`/`GoalY` are **absolute** scales in the same units as the decal's `x-scale`/`y-scale`
(1.0 is the texture's own size), not multipliers of the current scale. They go through the same
clamp as `x-scale` (`ReadScale`: UZDoom `decallib.cpp:1173-1177`; Zandronum
`decallib.cpp:1431-1435`), so `GoalX 0` or a negative value means 1/256, never "leave X alone".
Only omitting the keyword leaves that axis alone.

**At runtime** (UZDoom `a_decalfx.cpp:101-142`; Zandronum `decallib.cpp:1246-1287`): on the first
active tic it records the decal's current scale and interpolates each animated axis linearly to
its goal. **At the end** it sets the goal scale exactly and removes itself; the decal stays at
the new size.

## `slider`

```text
slider <name> { DistY <map units> SlideStart <sec> SlideTime <sec> }
```

| Keyword | Argument | Default | Meaning | UZDoom | Zandronum |
|---|---|---|---|---|---|
| `DistY` | map units (float) | 0 | Vertical distance to move; negative moves down the wall | yes | yes |
| `DistX` | float | n/a | **Unsupported.** Read and discarded with a console line `DistX in slider decal <name> is unsupported` | accepted, ignored | accepted, ignored |
| `SlideStart` | seconds (float) | 0 | Delay after spawn before sliding begins | yes | yes |
| `SlideTime` | seconds (float) | 0 | Length of the slide | yes | yes |

**At runtime** (UZDoom `a_decalfx.cpp:156-185`; Zandronum `decallib.cpp:1315-1344`): on the first
active tic it records the decal's height and adds `DistY` to it linearly over `SlideTime`. **At
the end** it sets the final height exactly and removes itself; the decal stays where it stopped.
There is no horizontal movement: the `DistX` code is commented out in both engines' parser and
thinker, and the `DistX` console line is a plain message, not a script error (UZDoom
`decallib.cpp:687-691`; Zandronum `decallib.cpp:767-772`).

A slider with `DistY 0` (or no `DistY`) registers nothing, whatever `DistX` says.

## `colorchanger`

```text
colorchanger <name> { Color <color> FadeStart <sec> FadeTime <sec> }
```

| Keyword | Argument | Default | Meaning | UZDoom | Zandronum |
|---|---|---|---|---|---|
| `Color` | colour | black (`00 00 00`) | Target shade colour | yes | yes |
| `FadeStart` | seconds (float) | 0 | Delay after spawn before the colour change begins | yes | yes |
| `FadeTime` | seconds (float) | 0 | Length of the colour change | yes | yes |

`Color` takes the same forms as `shade`: a quoted `"rr gg bb"` hex triplet, `#rrggbb`, `#rgb`,
a bare six-digit `rrggbb`, or an X11 colour name (`V_GetColor`: UZDoom `palette.cpp:746`;
Zandronum `v_video.cpp:632`). The stock `ToBlack` changer omits `Color` and relies on the black
default.

**It only works on a `shade` decal.** The thinker removes itself on its first tic unless the
decal's render style has a fixed colour (UZDoom `a_decalfx.cpp:200-203`; Zandronum
`decallib.cpp:1382-1385`), and among the decal keywords only `shade` sets such a style. A decal
whose last style keyword is `solid`, `add`, `translucent`, `fuzzy` or (UZDoom only)
`translatable` gets no colour change and no message.

**At runtime** (UZDoom `a_decalfx.cpp:198-236`; Zandronum `decallib.cpp:1380-1418`): on the first
active tic it records the decal's current shade. If that already equals `Color` it stops.
Otherwise it moves each of red, green and blue linearly toward `Color` over `FadeTime`. For
blood decals that the spawner recolours, the start is the blood colour, not the `shade` value in
DECALDEF. **At the end** it sets `Color` exactly and removes itself; the decal keeps the new
colour.

**Edge case, observed live on both engines:** the end branch doesn't stop the tic
after setting `Color`, so it falls through to the interpolation once more (UZDoom
`a_decalfx.cpp:210-234`; Zandronum `decallib.cpp:1392-1416`). Normally that recomputes exactly
`Color`. But if the level was frozen from inside the fade until past its end, the last step runs
with an elapsed time longer than `FadeTime`, and the decal is left on a colour extrapolated past
the goal instead of on `Color`. Probe (2026-09-29, local test builds, probe map): a `shade "00 00 00"`
decal with `Color "60 60 60" FadeStart 1 FadeTime 1`, frozen with the `freeze` cheat mid-fade for
140 tics, ended on grey 171 (UZDoom) and 161 (Zandronum) instead of 96, and kept that colour.
Unfrozen, the same decal ended on 96 on both. The time-freeze powerup does the same: with
`FadeTime 8`, a `PowerTimeFreezer` given 100 tics after spawn held the decal on grey 21 while
time was frozen, and the fade's end fell inside the freeze. The decal then settled on grey 122 (UZDoom)
and 123 (Zandronum) instead of 96. Unfrozen, it ended on 96.

## `combiner`

```text
combiner <name> { <animator> [<animator> ...] }
```

The body is a list of animator names, nothing else: no weights, no keywords. Each name must
already be defined above (a missing one is fatal, see "Bad input"). A member may be any animator
kind, including another combiner. The same name listed twice runs twice.

**At runtime** (UZDoom `decallib.cpp:1136-1145`; Zandronum `decallib.cpp:1346-1355`), a decal with
a combiner gets one thinker per member, created in list order, each on its own schedule. They
are independent:

- **Two of the same kind fight.** Two stretchers, two sliders or two colour changers on one
  decal each write the same field every tic they're both active; neither combines with the
  other.
- **A fader member ending removes the decal**, and every other member's thinker removes itself
  on its next tic when it finds the decal gone. Put the fader's end after the others' if their
  final state should be visible.

The stock `BloodSmearer` combines `BloodStretcher` (`GoalY 2.0` over 35 seconds) with
`BloodSlider` (`DistY -5` over 35 seconds), giving blood smears a slow downward drip.

## Example

An invented stain that darkens, drips, then fades away (the texture is the mod's own):

```text
colorchanger MyStainDarken
{
    Color     "10 10 10"
    FadeStart 1
    FadeTime  4
}

slider MyStainDrip
{
    DistY     -8
    SlideTime 5
}

fader MyStainFade
{
    DecayStart 10
    DecayTime  3
}

combiner MyStainAnim
{
    MyStainDarken
    MyStainDrip
    MyStainFade
}

decal MyStain
{
    pic MYSTAIN1
    shade "60 30 10"
    animator MyStainAnim
}
```

It slides 8 map units down over the first 5 seconds, darkens from 1 s to 5 s (it can because it
uses `shade`), stays put until 10 s, fades out by 13 s and is then removed.

## Bad input

Every "fatal" here is `FScanner::ScriptError`, which calls `I_Error` and stops startup at once;
there is no error count to reach first (UZDoom `sc_man.cpp:1063-1087`, whose non-fatal mode is
never switched on for DECALDEF; Zandronum `sc_man.cpp:888-905`).

| Condition | UZDoom | Zandronum |
|---|---|---|
| Unknown keyword inside `fader`/`stretcher`/`slider`/`colorchanger` | Fatal: `Unknown fader parameter '...'` (and `stretcher`, `slider`, `color changer` variants) | Same |
| Missing or non-numeric value after a time, goal or distance keyword | Fatal: `SC_GetFloat: Bad numeric constant ...` | Same |
| `combiner` member not defined yet (or its block registered nothing) | Fatal: `Undefined animator ...` | Same |
| Decal's `animator` names an animator not defined yet (or its block registered nothing) | Red console line in script-error format (`Script error, "<lump>" line N: Unable to find animator ...`), but **not fatal**; the decal is defined with no animation (`decallib.cpp:462-469`, `ScriptMessage` at `sc_man.cpp:1096`) | **Silent**; the decal is defined with no animation (`decallib.cpp:557-560`) |
| `stretcher` without `GoalX`/`GoalY`, `slider` with zero `DistY`, empty `combiner` | Silent at the block; the name stays undefined | Same |
| `DistX` in a `slider` | Console line, value ignored | Same |
| `colorchanger` on a decal without `shade` | Silent; no colour change | Same |
| Negative or zero times | Accepted (see "Shared rules") | Same |

## Engine-family divergence

The animator code is the same on both engines apart from number representation (UZDoom uses
floating point for scales, distances and alpha; Zandronum uses 16.16 fixed point), which isn't
visible to a mod. The one behaviour difference:

- **Unknown `animator` name in a decal**: UZDoom prints a red `Unable to find animator` line that
  looks like a script error but doesn't stop loading; Zandronum says nothing. Either way the decal
  loads without animation, so on Zandronum a misspelt animator name is easy to miss.

In Zandronum online play, each machine runs animators from its own DECALDEF copy on its own
timeline; see the lump page's
[which machine's copy is used](decaldef-lump.md#zandronum-specific-which-machines-copy-is-used).

**SLADE** lists every animator block and keyword (`GoalX`, `GoalY`, `StretchStart`,
`StretchTime`, `DecayStart`, `DecayTime`, `DistX`, `DistY`, `SlideStart`, `SlideTime`,
`FadeStart`, `FadeTime`, `Color`), with no gap, but doesn't mark `DistX` as unsupported.

## See also

- [The DECALDEF lump](decaldef-lump.md) for the outer grammar, load order, redefinition and the
  lump-wide error table.
- [Decal definitions](decal-definition.md) for the `decal` block, including `animator`, `shade`
  and the other render-style keywords the fader and colour changer depend on.
- [Decal groups and generators](decalgroups-and-generators.md) for how an actor class picks the
  decal (and so the animator) it leaves.
- [`../../console/notes/cl_maxdecals.md`](../../console/notes/cl_maxdecals.md) for the impact-decal
  limit a fader frees a slot in.
