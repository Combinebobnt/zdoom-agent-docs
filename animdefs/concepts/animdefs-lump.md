# The `ANIMDEFS` lump

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** ZDoom Wiki `ANIMDEFS` (https://zdoom.org/w/index.php?title=ANIMDEFS&oldid=54722, retrieved 2026-09-28) + verified against the UZDoom source's `src/gamedata/textures/animations.cpp` and `animations.h` (`FTextureAnimator::Init`, `InitAnimated`, `InitAnimDefs`, `ParseAnim`, `ParseRangeAnim`, `ParsePicAnim`, `ParseFramenum`, `ParseTime`, `ParseWarp`, `ParseCanvasTexture`, `ParseCameraTexture`, `ParseFireTexture`, `ParseAnimatedDoor`, `FindAnimatedDoor`, `AddAnim`, `FixAnimations`, `UpdateAnimations`), `src/gamedata/textures/anim_switches.cpp` (`InitSwitchList`, `ProcessSwitchDef`, `ParseSwitchDef`, `AddSwitchPair`, `FindSwitch`), `src/d_main.cpp` (the `UpdateAnimations` call and its clock) and `wadsrc/static/animdefs.txt`, and the Zandronum source's `src/textures/animations.cpp`, `src/textures/anim_switches.cpp` and `src/textures/texturemanager.cpp` (same functions and the init order), `src/d_main.cpp` (`I_FPSTime` clock), `src/p_switch.cpp` (`SetLineTexture`/`SoundPoint` server commands), `src/sv_commands.cpp` (`SERVERCOMMANDS_SetLineTexture`, `SERVERCOMMANDS_SetCameraToTexture`), `src/p_acs.cpp` (`SetCameraToTexture`), `src/p_doors.cpp` (`EV_SlidingDoor`'s `FindAnimatedDoor` calls), `src/network.cpp` (connect-time lump authentication list) and `wadsrc/static/animdefs.txt`. Keyword list cross-checked against UltimateDoomBuilder's `Build/Scripting/ZDoom_ANIMDEFS.cfg` and SLADE's `z_animdefs` block in `dist/res/config/languages/zdoom.txt`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

ANIMDEFS (a Hexen lump, extended by ZDoom) defines everything about textures that changes on its
own or on use: **flat and texture animations**, **switch** textures, **warping** textures,
**animated doors**, **camera textures** that show an actor's view, and per-texture **sky
offsets**. UZDoom adds **canvas textures** and procedural **fire textures**. This page covers the
lump's outer grammar, load order, redefinition, errors, and where the two engines differ. Each
block type's detail belongs to its own page.

## When it is read

- **Once at startup**, after all textures exist. Both engines run the same four steps in order:
  the Boom binary `ANIMATED` lump, then **every lump named `ANIMDEFS`** in load order, then a
  fix-up pass over the animations, then the Boom binary `SWITCHES` lump. Only the last-loaded
  `ANIMATED` and the last-loaded `SWITCHES` are read; every `ANIMDEFS` is.
- The engine's own `animdefs.txt` loads first, so a mod's lump can redefine stock animations and
  switches (see "Redefinition" for the one block type where that doesn't work).
- **Texture names resolve at parse time**, against every texture known at startup (any
  namespace; flats and wall textures are tried in the block's own namespace first).

## Outer grammar

ANIMDEFS has **no braces**. Each block starts with a top-level keyword and ends at the first word
its parser doesn't recognise, which is then read as the next top-level keyword. So a misspelled or
unsupported keyword inside a block is reported as an unknown *top-level* keyword, and that error is
fatal. Comments are `//` and `/* */`. Keywords and texture names are case-insensitive.

```text
texture [optional] <base texture>          // wall texture animation
flat    [optional] <base flat>             // flat animation
    range <last texture> <duration>        // one range per block, or:
    pic <texture | frame number> <duration>   // two or more pic lines
    allowdecals
    oscillate                              // Zandronum: only directly after the range line
    random                                 // UZDoom-only
    notrim                                 // UZDoom-only

    <duration> is: tics <n> | rand <min> <max>

switch [doom [<n>] | heretic | hexen | strife | any] <texture>
    [quest]
    on  [sound <sound>] pic <texture> <duration> [pic ...]
    off [sound <sound>] pic <texture> <duration> [pic ...]

warp  flat | texture <name> [<speed>] [allowdecals]
warp2 flat | texture <name> [<speed>] [allowdecals]

cameratexture <name> <width> <height> [fit <w> <h>] [worldpanning]
    // UZDoom also takes hdr, translucent and offset [<x> <y>], in any order
canvastexture <name> <width> <height> ...       // UZDoom-only, same options as cameratexture

animateddoor <texture>                     // then, in any order and repeatable:
    opensound <sequence> | closesound <sequence> | pic <texture | frame number> | allowdecals

skyoffset <texture> <offset>

// UZDoom-only; always 64x128, allowdecals only directly after the tics value
firetexture <name> tics <n> [allowdecals] color <r> <g> <b> <a> | palette <index> ...
```

A frame number in `pic` counts from the base texture: `pic 1` is the base itself, `pic 2` the
next texture in texture order. A minimal example that works on both engines (the texture, flat
and sound names are the mod's own):

```text
// Four-frame lava fall that runs forward, then back, decals allowed
texture MYLAVA1
    allowdecals
    range MYLAVA4 tics 6 oscillate

// Slime with an uneven third frame
flat MYSLIME1
    pic MYSLIME1 tics 8
    pic MYSLIME2 tics 8
    pic MYSLIME3 rand 4 12

switch MYSWOFF
    on sound mymod/switch pic MYSWON tics 0

warp2 flat MYWATER 2.0

cameratexture MYCAMTEX 256 128
    fit 64 32
```

### The block types

- **`texture` / `flat`** animate a base texture. `range` cycles through every texture from the
  base to the named last one, in texture order, with one duration for all frames (a last texture
  that comes *before* the base runs the range backward). `pic` lists frames explicitly, each with
  its own duration. A block uses one or the other, not both. `oscillate` plays forward then back.
- **`switch`** names the texture a switch shows when off, and the frames it shows once used
  (`on`), with an optional sound. `off` lists the frames for switching back (only matters for
  repeatable switches); without it, the switch just returns to the base texture. The optional game
  name limits the switch to that game (any number after `doom` is ignored). `quest` marks it a
  Strife quest panel.
- **`warp` / `warp2`** make a texture or flat ripple (two different distortion styles). The
  number sets the speed.
- **`cameratexture`** replaces (or creates) a texture with a live view, drawn at `<width>` x
  `<height>` and displayed at the texture's original size, or at `fit`'s size. ACS
  `SetCameraToTexture` picks the actor whose view it shows.
- **`animateddoor`** gives a door texture an opening sequence of frames and SNDSEQ sound
  sequences, used by the `Door_Animated` special (Strife-style sliding doors) and, on UZDoom only,
  `Door_AnimatedClose`.
- **`skyoffset`** sets a sky texture's vertical offset. Only some renderers and sky heights honour
  it; Zandronum's software renderer never does (see [skyoffset](firetexture-skyoffset.md)).
- **`canvastexture`** (UZDoom-only) makes a blank texture ZScript can draw on. **`firetexture`**
  (UZDoom-only) makes a procedural fire effect coloured by a list of up to 256 colours.

### Interface graphics (HUD icons and menu cursors)

A `texture` animation works on any graphic, not just level textures, so the stock
`animdefs.txt` of both engines animates HUD and menu graphics too, each with `texture optional`
so a game without the graphic doesn't error:

- **Menu cursors:** `M_SKULL1` (Doom, 2 frames at 8 tics), `M_SLCTR1` (Heretic/Hexen, 2 frames at
  16 tics), `M_CURS1` (Strife, 8 frames at 4 tics).
- **Heretic/Hexen powerup icons:** `SPINBK0`, `SPBOOT0`, `SPSHLD0`, `SPMINO0` (16 frames at 3 tics
  each). The Wings of Wrath icon is left out, since it stops spinning when the player stops
  flying and so can't be a plain animation.
- **UZDoom only:** `INVGEML1`/`INVGEMR1` (2 frames at 4 tics each).
- **Zandronum only:** `SPKMINI1` (3 frames at 5 tics), the voice-chat speaker icon drawn by
  `voicechat.cpp` and the scoreboard.

### Timing

- **Animation durations are in tics but take fractions** (`tics 2.5`). They are converted to
  milliseconds (x 1000 / 35, truncated), and animations advance on the renderer's millisecond
  clock, not the game's tic counter. So they keep animating while the game is paused or a menu is
  open.
- **Switch frame durations are whole game tics** (0 to 65535), and `rand` with its bounds
  reversed is swapped rather than rejected.

### `optional`

`optional` goes directly after `texture`/`flat`, before the base name. It only matters when the
**base** texture doesn't exist. Then the block is skipped silently, and named frames that don't
exist aren't errors either. When the base texture does exist, `optional` changes nothing: every
named frame must still exist.

Without `optional`, a missing base texture prints `ANIMDEFS: Can't find <name>` to the console and
the block is skipped, but a named frame that doesn't exist is still a fatal error.

### Decals

Animated textures, warping textures and animated-door textures refuse wall decals by default.
`allowdecals` inside the block turns them back on. For a `range`, the setting is copied to every
texture in the range.

## Redefinition

| Block type | A later definition for the same texture |
|---|---|
| `texture`, `flat` | **Replaces** the earlier animation, including one from the `ANIMATED` lump (read first). A backward `range` is keyed by its lower-numbered end (the named last frame), so a replacement must name that texture |
| `switch` | **Replaces** the earlier switch. A switch from the `SWITCHES` lump (read last) beats any ANIMDEFS `switch` for the same texture |
| `warp`, `warp2` | Keeps the **first** warp style. Takes the speed from the last definition that gives one, and `allowdecals` (present or absent) from the last |
| `animateddoor` | **Ignored**: door lookup returns the first definition. A mod can't redefine a stock animated door (UZDoom and Zandronum each ship seven, for Strife) |
| `skyoffset` | Replaces the offset |

## Errors

| Condition | UZDoom | Zandronum |
|---|---|---|
| Unknown top-level keyword, including any unsupported keyword inside a block | Fatal script error | Same |
| `texture`/`flat` base missing, no `optional` | Console message `ANIMDEFS: Can't find <name>`; block skipped | Same |
| A named frame missing (`range` end or `pic`) | Fatal `Unknown texture <name>`, unless `optional` and the base is missing | Same |
| `pic` and `range` in one block, or two `range` lines | Fatal | Same |
| Fewer than two `pic` frames | Fatal `Animation needs at least 2 frames` | Same |
| A frame without `tics`/`rand` | Fatal `Must specify a duration for animation frame` | Same |
| `random` and `oscillate` in one block | Fatal | `random` is itself fatal (unknown keyword) |
| `range`, or `warp`, on a long (full-path) texture name | Fatal | No such check |
| `warp` without `flat`/`texture` | Fatal | Same |
| `skyoffset` or `animateddoor` naming a missing texture, or a bare `warp` line naming one | Silently ignored | Same |
| `warp` naming a missing texture, followed by a speed or `allowdecals` | Fatal: the trailing words reach the top level as unknown keywords | Same |
| `switch` base texture missing | Silently skipped | Same |
| A switch frame texture missing | That `on`/`off` state is dropped silently. With no `on` state the whole switch is skipped; with no `off` state a default one is made | Same |
| Second `on`, second `off`, second `sound` in one state, or a state with no `pic` | Fatal, unless the first `on`/`off` was dropped for a missing texture or the first `sound` name was unknown | Same |
| The `on` state's last frame is the base texture | Fatal `The on state for switch ... must end with a texture other than ...` | Same |

## Engine-family divergence

- **Top-level keywords.** `canvastexture` and `firetexture` are UZDoom-only; each is a fatal error
  on Zandronum.
- **`oscillate` placement.** Zandronum only reads `oscillate` as the word directly after a
  `range` line's duration. Anywhere else, including in a `pic` animation, it's an unknown keyword
  and fatal. UZDoom accepts `oscillate` anywhere in a `texture`/`flat` block, and it works on `pic`
  animations too. `range <last> tics <n> oscillate` works on both, provided the base exists and
  the last frame differs from it; otherwise Zandronum returns before reading `oscillate`, which is
  then fatal even under `optional` (Zandronum `animations.cpp:433-453`).
- **`random`** (frames in random order) and **`notrim`** are UZDoom-only and fatal on Zandronum.
- **`cameratexture` options.** Zandronum reads at most `fit` then `worldpanning`, in that order.
  UZDoom reads `fit`, `worldpanning`, `hdr`, `translucent` and `offset [<x> <y>]` in any order.
  A replaced texture's offsets are reset to 0 on both, except that a bare UZDoom `offset` copies
  them. On Zandronum, any other option (or `worldpanning` before `fit`) is fatal.
- **Long texture names.** UZDoom rejects `range` and `warp` on full-path texture names; Zandronum
  has no such check.
- **Stock definitions.** Zandronum's `animdefs.txt` adds the `SPKMINI` speaker icon animation.
  UZDoom's adds the `INVGEML`/`INVGEMR` inventory gem animations and a `warp` on the `b@ckdrop`
  texture. Everything else matches.
- **`Door_AnimatedClose`** (special 274) is UZDoom-only.
- **Editors.** UltimateDoomBuilder's config lacks `canvastexture`, `firetexture`, `notrim`,
  `hdr`, `color` and `palette`. SLADE lists them. Neither lists `skyoffset`, `quest`, `any`,
  `translucent` or `offset`, and neither says which keywords Zandronum rejects.

## Zandronum-specific: which machine's copy is used

ANIMDEFS is not among the lumps Zandronum checksums when a client connects (`src/network.cpp`'s
authentication list), so a client and server can run different ANIMDEFS contents with no connect
error.

- **Animations, warps, sky offsets and camera textures** are presentation, resolved by each client
  from its own copy.
- **Switches are decided by the server.** It checks its own copy to see whether a line's texture
  is a switch, changes the texture, and sends clients the new texture's *name* and the switch
  sound's name. A client whose copy lacks the switch still sees the change the server sends.
- **ACS `SetCameraToTexture`** run on the server is sent to clients (texture name, camera actor
  and FOV, the FOV as one byte). The camera texture itself must exist in each client's copy.
- **Animated doors** are run by the server, which sends each frame as a texture name; the
  client's own `animateddoor` definition is never used. See [animated doors](animated-doors.md).

## See also

- [Texture and flat animations](texture-flat-animations.md) for per-keyword detail, frame
  numbering, how a `range` is built, and duration hazards.
- [Switches](switches.md) for `switch` block keywords, frame timing (`tics 0`), runtime playback
  and the `SWITCHES` lump.
- [Warps](warps.md) for speed-to-motion mapping and how each renderer draws a warp.
- [Animated doors](animated-doors.md) for `animateddoor` keywords, how `Door_Animated` finds a
  definition, frame timing, and Zandronum netcode.
- [Camera and canvas textures](camera-canvas-textures.md) for every `cameratexture`/`canvastexture`
  option per engine, how `SetCameraToTexture` gets a view, and render cost.
- [skyoffset and firetexture](firetexture-skyoffset.md) for which renderers honour a sky offset
  and the procedural fire texture.

- [`../../textures/concepts/textures-lump.md`](../../textures/concepts/textures-lump.md) for
  defining the textures ANIMDEFS names.
- [`../../decaldef/concepts/decaldef-lump.md`](../../decaldef/concepts/decaldef-lump.md) for the
  decals `allowdecals` lets through.
- `SetCameraToTexture` in [`../../acs/INDEX.md`](../../acs/INDEX.md) (signature only so far).
