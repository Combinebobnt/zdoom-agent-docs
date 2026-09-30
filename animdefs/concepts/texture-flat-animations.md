# `texture` and `flat` animation blocks

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/gamedata/textures/animations.cpp` and `animations.h` (`ParseAnim`, `ParseRangeAnim`, `ParsePicAnim`, `ParseFramenum`, `ParseTime`, `AddAnim`, `AddSimpleAnim`, `AddComplexAnim`, `FixAnimations`, `FAnimDef::SetSwitchTime`, `AdvanceFrame`, `UpdateAnimations`, `ResetTimers`, `InitStandaloneAnimation`), `src/common/textures/texturemanager.cpp` (`CheckForTexture`, `AreTexturesCompatible`, `AddTexturesForWad`, `SortTexturesByType`, `SetTranslation`), `src/common/textures/gametexture.cpp`/`gametexture.h` (what `notrim` sets and where it's read), `src/common/utility/cmdlib.cpp` (`IsNum`), `src/common/engine/sc_man.cpp` (`ScriptError`), `src/common/engine/m_random.h`, `src/common/filesystem/source/resourcefile.cpp` (`PostProcessArchive`), `src/p_setup.cpp` (`ClearLevelData`, `P_SetupLevel`), `src/playsim/p_effect.cpp` (`SPF_LOCAL_ANIM`), `src/d_main.cpp` and `wadsrc/static/animdefs.txt`, and the Zandronum source's `src/textures/animations.cpp` and `textures.h` (same parser and update functions, `FAnimDef`), `src/textures/texturemanager.cpp` (same texture-manager functions and the init order), `src/cmdlib.cpp` (`IsNum`), `src/sc_man.cpp` (`ScriptError`), `src/m_random.h`, `src/d_main.cpp` and `wadsrc/static/animdefs.txt`. Keyword names cross-checked against UltimateDoomBuilder's `Build/Scripting/ZDoom_ANIMDEFS.cfg` and SLADE's `z_animdefs` block in `dist/res/config/languages/zdoom.txt`.

A `texture` or `flat` block makes a base texture cycle through frames. This page covers every
keyword inside that block, per engine. The lump's outer grammar (no braces, so a block ends at the
first word its parser doesn't know), load order and redefinition rules are in the section's lump page,
[The ANIMDEFS lump](animdefs-lump.md).

```text
// Portable: forward range that bounces back, oscillate right after the duration
flat MYFLOW1
    range MYFLOW4 tics 5 oscillate

// Portable: explicit frames, a frame number, and a random-length last frame
texture MYSIGN1
    allowdecals
    pic MYSIGN1 tics 6
    pic 2 tics 6              // the texture right after MYSIGN1 in texture order
    pic MYSIGN3 rand 20 60

// UZDoom-only: frames in random order (fatal on Zandronum)
texture optional MYSPARK1
    random
    pic MYSPARK1 tics 3
    pic MYSPARK2 tics 3
    pic MYSPARK3 tics 3
```

## Keywords

`texture` looks the base name up as a wall texture first, `flat` as a flat first. Both fall back to
any other texture kind of that name, including sprites and loose graphics (UZDoom
`animations.cpp:368,382`; Zandronum `animations.cpp:331,343`). The stock `animdefs.txt` in both
engines uses `texture` blocks to animate sprites and menu graphics.

| Keyword | Arguments | Meaning | UZDoom | Zandronum |
|---|---|---|---|---|
| `optional` | none | Must be the word directly after `texture`/`flat`. A missing base then skips the block silently (see below) | yes | yes |
| `range` | `<last frame> <duration>` | Every texture from the base to `<last frame>` in texture order, one duration for all. One per block | yes | yes |
| `pic` | `<frame> <duration>` | One explicit frame. Two or more per block. Can't be mixed with `range` | yes | yes |
| `tics` | `<n>` | Fixed duration. A number, fractions allowed | yes | yes |
| `rand` | `<min> <max>` | Random duration each time the frame is shown | yes | yes |
| `allowdecals` | none | Lets wall decals stick to the base texture (off by default for animated textures) | yes, anywhere in the block | yes, anywhere in the block |
| `oscillate` | none | Play forward, then back, instead of looping | anywhere in the block, `range` or `pic` | only as the word directly after a `range` line's duration |
| `random` | none | Show frames in random order | anywhere in the block | no: fatal |
| `notrim` | none | Turns off border trimming for the base texture when drawn as a sprite | anywhere in the block | no: fatal |

`<frame>` and `<last frame>` are a texture name or a frame number (next section). `<duration>` is
`tics <n>` or `rand <min> <max>`; a frame with neither is fatal (`Must specify a duration for
animation frame`), and a non-number after `tics`/`rand` is fatal too.

UltimateDoomBuilder's config lists `random`, `oscillate` and `optional` but not `notrim`; SLADE
lists all of them. Neither marks `random`/`notrim` as UZDoom-only.

## Frame names and frame numbers

- **A frame word made only of digits and `-` is a frame number**, never a texture name (`IsNum`,
  UZDoom `cmdlib.cpp:412`, Zandronum `cmdlib.cpp:400`). So a texture whose name is all digits
  can't be named as a frame.
- **A frame number counts from the base**: `1` is the base itself, `2` the texture after it in
  texture order, `0` the texture before it (UZDoom `animations.cpp:574-577`, Zandronum
  `animations.cpp:499-502`). It is never checked for existence. A `pic` number that lands outside
  the texture list just shows the base (`SetTranslation` maps an out-of-range target to itself;
  UZDoom `texturemanager.cpp:1558-1568`, Zandronum `animations.cpp:851-861`). A `range` number is
  not bounds-checked before it's used, so keep range numbers inside the base's own block (next
  section).
- **Named frames resolve to the newest texture of that name.** A texture added later sits at the
  head of its hash chain, so a name defined by several files resolves to the last-loaded file's
  (UZDoom `texturemanager.cpp:415-426`, Zandronum `texturemanager.cpp:378-386`).
- **A `pic` animation only animates its base.** Each update points the base texture at the current
  frame's texture. A surface that uses one of the frame textures directly doesn't animate (UZDoom
  `animations.cpp:1174-1177`, Zandronum `animations.cpp:926-929`). Frames can be any textures,
  from any file.

## How a `range` is built

A `range` doesn't list its frames; it takes every texture whose index lies between the base and
the last frame. The index order is the texture manager's list, built one file at a time (UZDoom
`AddTexturesForWad`, `texturemanager.cpp:926-1035`; Zandronum `texturemanager.cpp`'s
`AddTexturesForWad` and `SortTexturesByType`, from line 912). Within one file the textures are
then regrouped by kind, in this order (UZDoom `texturemanager.cpp:1065-1069`, Zandronum
`texturemanager.cpp:932-935`):

1. sprites (including `TEXTURES` `sprite` definitions),
2. patches,
3. wall textures: `TEXTURE1`/`TEXTURE2` entries and `TEXTURES` `walltexture` definitions,
4. flats: flat lumps and `TEXTURES` `flat` definitions,
5. `TX_START`/`textures/` lumps and `TEXTURES` `texture` definitions,
6. other loose graphics, including `TEXTURES` `graphic` definitions.

Inside each kind the order is the order the file added them: lumps first, `TEXTURES` definitions
after them in definition order, entry order in `TEXTURE1` then `TEXTURE2`, lump order between
`F_START`/`F_END` in a WAD. Files in a PK3, ZIP or folder are sorted alphabetically by full path
when the archive is opened (UZDoom `resourcefile.cpp:387`; Zandronum `file_zip.cpp:340`), so a
`flats/` folder runs in alphabetical order. Note that a `TEXTURES` `texture` is not the same kind
as a `TEXTURE1` wall texture, so a range can't span the two.

Consequences, identical on both engines:

- **Both ends must be the same kind and come from the same file.** Otherwise the animation is
  silently not created (`AddSimpleAnim` calls `AreTexturesCompatible`; UZDoom
  `animations.cpp:111`, `texturemanager.cpp:522-545`; Zandronum `animations.cpp:99`,
  `texturemanager.cpp:451-474`). Because names resolve to the newest file (above), a mod that
  replaces only the first texture of a stock range breaks that range: the two ends now live in
  different files.
- **Every texture in the range animates**, each one offset along the cycle, not just the base
  (UZDoom `animations.cpp:1180-1183`, Zandronum `animations.cpp:932-935`).
- **A last frame before the base plays the range backward.** The animation is then stored under
  the lower-numbered end, which is the texture a later redefinition has to name to replace it.
- **A range whose last frame is the base itself** does nothing, with no error (UZDoom
  `animations.cpp:510-513`, Zandronum `animations.cpp:433-436`). On Zandronum a following
  `oscillate` is then fatal (see `oscillate`).
- UZDoom also refuses `range` on long (full-path) texture names; see the lump page's errors table.

## Durations

- **Units: tics in, milliseconds stored.** `tics n` becomes `n x 1000 / 35` milliseconds,
  truncated toward zero (UZDoom `animations.cpp:597-617`, Zandronum `animations.cpp:522-542`). So
  `tics 8` is 228 ms. Fractions are allowed (`tics 2.5` is 71 ms). Negative values aren't
  rejected, and the conversion to an unsigned count is undefined; don't use them.
- **`rand min max`** picks a new duration every time the frame comes up, from `min` inclusive to
  `max` exclusive, in those truncated milliseconds (UZDoom `SetSwitchTime`,
  `animations.cpp:1010-1019`, and `m_random.h:135`; Zandronum `animations.cpp:831-840` and
  `m_random.h:56-60`).
- **`range` has one duration for every frame. `pic` has one per frame.** With `random` or
  `oscillate` on a `pic` animation, the duration used is always the frame being shown.
- **Clock.** Normal animations run on the renderer's millisecond clock, not game tics, and keep
  running while paused (see the lump page's "Timing"). The first update only arms the timer, so the
  first frame gets its full duration. A late update catches up by advancing several frames at once
  (UZDoom `animations.cpp:1162-1172`, Zandronum `animations.cpp:880-924`).
- **UZDoom restarts every animation on each map load.** `P_SetupLevel` clears level data, which
  resets every animation to its first frame and rearms its timer (`p_setup.cpp:304,462`,
  `animations.cpp:1188-1215`). Zandronum never resets them, so the phase carries over between
  maps.
- **UZDoom particles and visual thinkers** with `SPF_LOCAL_ANIM` run their own copy of the
  texture's animation from frame 0, timed on level time in game tics (so it stops while paused)
  rather than the millisecond clock (`p_effect.cpp:389-392,1149-1153`,
  `animations.cpp:1071-1117`).

Two duration hazards, read from the update loop in both engines and observed live on both
(2026-09-29, local test builds of UZDoom 5.1.0-pre and Zandronum 3.3-alpha,
DOOM2.WAD, a probe UDMF map, throwaway config):

- **A zero duration hangs the game.** The loop advances until the next switch time is in the
  future, and a zero duration sets it to the present. A `range` with a zero duration, or a `pic`
  animation whose every frame is zero, never leaves that loop. Anything under `tics 0.035`
  truncates to zero. A single zero-length `pic` frame among nonzero ones is just skipped. Live, a
  two-frame `pic ... tics 0` block hung both engines right after the level started, with no
  error and no crash, whether or not the texture was on screen. The `range` form does the same:
  a two-texture `range <last> tics 0` hung both engines at level start, while the same range
  with `tics 5` animated normally.
- **`rand` with its bounds reversed is not swapped** (unlike switch frames, see
  [Switches](switches.md)). The unsigned subtraction wraps, so the frame waits a random time of up
  to about 49 days: the animation effectively freezes on it. Live, `rand 10 1` on both frames held
  the first frame for 26 s (UZDoom) and 120 s (Zandronum) of unpaused play, while the same block
  with `rand 1 10` changed frame within half a second.

## `oscillate`, `random` and `notrim` in detail

- **`oscillate` on UZDoom** is recorded as a block-level flag and applied after the block ends,
  so it may come before or after the `range`/`pic` lines (`animations.cpp:412-419,483-487`). If the
  range didn't create an animation (missing optional base, one-texture range) it is ignored.
- **`oscillate` on Zandronum** is only looked for inside `ParseRangeAnim`, as the next word after
  the duration, and only after the function's early return for a missing base or a one-texture
  range (`animations.cpp:433-453`). So `oscillate` is fatal on Zandronum in a `pic` block, before
  the `range` line, and also in `texture optional <missing> range <last> tics <n> oscillate`:
  `optional` doesn't protect that line when the base is missing.
- **Backward range plus `oscillate`.** Both engines start it in the "going down" direction at frame
  0, which underflows the 16-bit frame counter. Zandronum therefore plays it as a plain backward
  loop for 65535 steps before it starts bouncing. UZDoom does the same until the first map load,
  whose reset turns it into a normal forward oscillation (`animations.cpp:485,1203-1204`;
  Zandronum `animations.cpp:447,915-921`, `textures.h:88`).
- **`random`** (UZDoom-only) works on `range` and `pic` animations and always changes frame.
  The pick isn't uniform: from any frame but the last two, the next frame is twice as likely as
  the others, and the last frame can only follow the second-to-last (`AdvanceFrame`,
  `animations.cpp:1040-1048`).
  `random` and `oscillate` in one block is fatal (`You cannot use "random" and "oscillate"
  together in a single animation.`).
- **`notrim`** (UZDoom-only) sets the no-trim flag on the base texture only, not its frames
  (`animations.cpp:446-456`). The flag is read only when the hardware renderer sets up a texture's
  sprite data, to stop it trimming transparent borders (`gametexture.cpp:336`). So it matters only
  for a base that is drawn as a sprite. When the base texture is missing, `notrim` is fatal
  whether or not the block is `optional`, and the message names the keyword rather than the
  texture (`NoTrim: notrim is not a sprite`).

## `optional` and missing textures

`optional` only covers a missing **base**. With the base missing, named frames that don't exist
are accepted and the block builds nothing. With the base present, `optional` changes nothing and
every named frame must exist (UZDoom `animations.cpp:376-394,568-587`, Zandronum
`animations.cpp:337-355,493-512`). Two exceptions to "the block builds nothing silently": on
Zandronum a `range ... oscillate` line is still fatal, and on UZDoom `notrim` is still fatal (both
above).

Without `optional`, a missing base prints `ANIMDEFS: Can't find <name>` to the console and the
block is read but discarded. Its named frames must still exist.

## Decals

The base texture refuses decals from the moment the block starts, and `allowdecals` clears that.
After all ANIMDEFS lumps are read, the fix-up pass copies the setting from each `range`
animation's lower-numbered end to every texture in the range (UZDoom `animations.cpp:882-905`,
Zandronum `animations.cpp:686-727`). For a **backward** range the lower end is the last frame,
which copies the base's setting when the `range` line is parsed (UZDoom `animations.cpp:524`,
Zandronum `animations.cpp:440`). So on a backward range, `allowdecals` must come **before** the
`range` line; after it, it has no effect on either engine. A `pic` animation only affects its
base texture's setting.

## Errors

`ScriptError` ends the program with `I_Error` in both engines (UZDoom `sc_man.cpp:1063-1087`, whose
non-fatal mode ANIMDEFS never turns on; Zandronum `sc_man.cpp:888-905`). ANIMDEFS is read at
startup (`TexAnim.Init()`, UZDoom `d_main.cpp:3632`; Zandronum `texturemanager.cpp:1017-1020`), so
every "fatal" below aborts startup with `Script error, "<lump>" line <n>`.

| Condition | UZDoom | Zandronum |
|---|---|---|
| A word the block doesn't know (including `random`/`notrim` on Zandronum) | Ends the block, then fatal `Bad syntax.` as a top-level word | Same |
| `oscillate` anywhere except directly after a `range` duration | Accepted | Fatal, as above |
| `oscillate` after a `range` that built nothing (missing `optional` base, last frame = base) | Ignored | Fatal, as above |
| Base missing, no `optional` | Console `ANIMDEFS: Can't find <name>`, block discarded | Same |
| Named frame missing | Fatal `Unknown texture <name>`, unless `optional` and the base is missing | Same |
| `pic` with `range`, or two `range` lines | Fatal | Same |
| Fewer than two `pic` frames (base present) | Fatal `Animation needs at least 2 frames` | Same |
| No `tics`/`rand` after a frame | Fatal `Must specify a duration for animation frame` | Same |
| `random` with `oscillate` | Fatal | `random` itself is fatal |
| `notrim` with the base missing | Fatal `NoTrim: notrim is not a sprite` | `notrim` itself is fatal |
| `range` ends of different kinds or files, or last frame = base | Silently no animation | Same |
| Zero duration on a `range`, or on every `pic` frame | Update loop never exits: the game hangs (observed with `pic`) | Same |
| `rand` with bounds reversed | Frame stalls for up to about 49 days (observed) | Same |

## Engine-family divergence

- **`oscillate` placement.** UZDoom: anywhere in the block, `range` or `pic`. Zandronum: only as
  the next word after a `range` duration, and fatal there too when the range built nothing. The
  only form that works on both is `range <last> <duration> oscillate` with a base that exists and
  a last frame different from the base.
- **`random` and `notrim`** are UZDoom-only and fatal on Zandronum.
- **Map load.** UZDoom restarts every texture animation at its first frame on each map load;
  Zandronum lets them run on across maps.
- **Backward range with `oscillate`.** Zandronum plays it as a backward loop for 65535 steps;
  UZDoom oscillates normally once a map has loaded.
- **Long texture names.** UZDoom refuses `range` on them; Zandronum has no check (see the lump page).
- **Particles.** Only UZDoom can run a texture's animation per particle or visual thinker
  (`SPF_LOCAL_ANIM`), on game time.

## See also

- [The ANIMDEFS lump](animdefs-lump.md) for the outer grammar, load order, redefinition and the
  lump-wide errors table.
- [Switches](switches.md): switch frames use whole game tics and swap reversed `rand` bounds,
  unlike animation frames.
- [Warps](warps.md) for the other way a texture moves on its own.
- [`../../textures/concepts/textures-lump.md`](../../textures/concepts/textures-lump.md) for
  defining the textures whose order a `range` follows.
- [`../../decaldef/concepts/decaldef-lump.md`](../../decaldef/concepts/decaldef-lump.md) for the
  decals `allowdecals` lets through.
