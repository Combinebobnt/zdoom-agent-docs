# ANIMDEFS `warp` and `warp2`

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/gamedata/textures/animations.cpp` (`InitAnimated`, `InitAnimDefs`, `ParseWarp`, `FixAnimations`, `UpdateAnimations`), `src/common/textures/gametexture.h` (warp style, shader speed, clamp mode), `src/common/engine/sc_man.cpp`/`sc_man.h` (`CheckFloat`, `ScriptError`), `src/rendering/swrenderer/textures/warptexture.cpp` and `warpbuffer.h` (software warp), `src/rendering/swrenderer/textures/r_swtexture.cpp`, `src/common/textures/hw_material.cpp`, `src/common/rendering/gl/gl_renderstate.cpp`, `gles/gles_renderstate.cpp` and `vulkan/renderer/vk_renderstate.cpp` (shader timer), `src/common/rendering/hwrenderer/data/hw_shaderpatcher.cpp`, `wadsrc/static/shaders/glsl/func_warp1.fp`/`func_warp2.fp`, `src/rendering/hwrenderer/scene/hw_walls.cpp`, `src/r_data/gldefs.cpp`, `src/common/utility/i_time.cpp` and `src/d_main.cpp` (frame clock, init order) and `wadsrc/static/animdefs.txt`; and the Zandronum source's `src/textures/animations.cpp` (same functions), `src/textures/warptexture.cpp` (`FWarpTexture`, `FWarp2Texture`), `src/textures/texture.cpp` (`CalcBitSize`), `src/sc_man.cpp`, `src/r_utility.cpp` and `src/sdl/i_system.cpp`/`src/win32/i_system.cpp` (`r_FrameTime`, `I_GetTimeFrac`), `src/gl/textures/gl_material.cpp` (`FGLTexture::WarpBuffer`, shader index, clamp mode), `src/gl/renderer/gl_renderstate.cpp` (`SetupShader`), `src/gl/shaders/gl_shader.cpp` (`gl_warp_shader`, `FShader::Bind`, GLDEFS shader check), `src/gl/textures/gl_texture.cpp` (brightmap check), `src/gl/system/gl_interface.cpp` (shader model), `src/gl/scene/gl_scene.cpp` (`gl_frameMS`, `gl_ParseDefs` call), `src/d_main.cpp` and `wadsrc/static/shaders/glsl/func_warp1.fp`/`func_warp2.fp`. Keyword names cross-checked against UltimateDoomBuilder's `Build/Scripting/ZDoom_ANIMDEFS.cfg` and SLADE's `z_animdefs` block in `dist/res/config/languages/zdoom.txt`.

`warp` and `warp2` make a wall texture or flat ripple continuously. They are one-line top-level
blocks in ANIMDEFS; see [the ANIMDEFS lump](animdefs-lump.md) for the outer grammar, load order
and the other block types. This page covers the per-keyword detail, what each style looks like,
how the speed number maps to motion, and how each renderer draws it on each engine.

## Syntax

```text
warp  flat | texture <name> [<speed>] [allowdecals]
warp2 flat | texture <name> [<speed>] [allowdecals]
```

| Keyword / argument | Meaning | UZDoom | Zandronum |
|---|---|---|---|
| `warp` | Warp style 1: the classic Hexen-style swirl | Yes (`animations.cpp:319`) | Yes (`animations.cpp:290`) |
| `warp2` | Warp style 2: a finer ripple (the source credits it as Eternity-like) | Yes | Yes |
| `flat` / `texture` | Required. Picks the namespace searched *first*; the lookup falls back to any namespace, so `warp flat X` still finds a wall texture named `X` if no flat has that name | `ParseWarp`, `animations.cpp:627-687` | `ParseWarp`, `animations.cpp:552-607` |
| `<name>` | The texture or flat to warp | Resolved at parse time | Same |
| `<speed>` | Optional multiplier on the warp's clock. Any number `strtod` accepts, integer or decimal. Default `1.0`. No range or sign check | Stored on the texture (`gametexture.h:136`, `240`) | Stored on the warp texture object (`warptexture.cpp:44`) |
| `allowdecals` | Optional. Lets wall decals stick to the texture. Without it, decals are refused | Yes | Yes |

**Argument order is fixed.** The speed, if present, must come before `allowdecals`. Each is read
once, in that order; anything left over goes back to the top-level loop, which rejects it (see
"Bad input").

**Units.** Nothing about a warp is in tics. The speed scales a millisecond clock (software
renderers) or a seconds timer (shader renderers); at `1.0` a full cycle takes several seconds
(see "What the styles look like"). The speed multiplies linearly: `2.0` runs twice as fast,
`0.5` half as fast.

```text
// A slow-rolling lava flat, and a fast rippling water wall that takes decals
warp  flat    MYLAVA1  0.5
warp2 texture MYWATER1 2 allowdecals
```

UZDoom's own stock ANIMDEFS uses a fractional speed on one texture (`warp texture b@ckdrop
0.83445`, UZDoom `wadsrc/static/animdefs.txt:407`).

## Redefinition

A later `warp`/`warp2` for the same texture:

- **Keeps the first style.** Both engines skip re-warping a texture that already warps
  (UZDoom `animations.cpp:661-664`; Zandronum `animations.cpp:578-584`), so `warp` followed by
  `warp2` leaves it on style 1.
- **Changes the speed only if it gives one.** An omitted speed keeps the earlier value.
- **Always re-decides decals.** Every definition turns decals off, then back on only if it says
  `allowdecals` (UZDoom `animations.cpp:674-683`; Zandronum `animations.cpp:594-603`). So the last
  definition's `allowdecals` (present or absent) wins.

The Boom binary `ANIMATED` lump is read before any ANIMDEFS. An entry there with a speed above
65535 (the SMMU "swirl" convention) makes its start texture warp as style 2 at the default speed
(UZDoom `animations.cpp:244-248`; Zandronum `animations.cpp:215-220`). A later ANIMDEFS `warp`
for that texture can then set its speed and decals, but not change it to style 1.

## Bad input

| Input | UZDoom | Zandronum |
|---|---|---|
| No `flat`/`texture` after the keyword | Fatal `Bad syntax.` (`animations.cpp:645`) | Same (`animations.cpp:570`) |
| Texture doesn't exist, bare line (`warp flat NOSUCH`) | Silently ignored | Same |
| Texture doesn't exist, with a speed or `allowdecals` after it | **Fatal** `Bad syntax.`: the lookup fails before the trailing words are read, so they reach the top-level loop as unknown keywords (`animations.cpp:351`) | Same (`animations.cpp:314`) |
| `allowdecals` before the speed | Fatal `Bad syntax.` on the speed, for the same reason | Same |
| A long (full-path) texture name | Fatal `You cannot use "warp" for long texture names.` (`animations.cpp:653-657`) | No check |
| Speed `0` | Accepted. See "Renderers" for what it does | Accepted |
| Negative speed | Accepted, not validated. Only UZDoom's shader renderers treat it as "run backward"; the software paths convert the scaled time to an unsigned integer, so don't rely on it | Accepted, not validated. The GL shader path ignores it (see "Renderers") |

Every "fatal" here really aborts. The scanner's `ScriptError` goes straight to `I_Error` on both
engines (UZDoom `sc_man.cpp:1086`, with `NoFatalErrors` defaulting to false at `sc_man.h:236` and
never set for ANIMDEFS; Zandronum `sc_man.cpp:904-905`), and ANIMDEFS is read at startup.

## What the styles look like

Both styles sample the base texture at a displaced position; neither changes the colours.

- **`warp` (style 1)** slides whole rows sideways and whole columns up and down, each by a slow
  sine wave. The result is the classic slow swirl of Hexen/Heretic liquids.
- **`warp2` (style 2)** displaces every pixel by the sum of two sine waves per axis, smaller and
  faster. The result is a busier, finer ripple.

The software and hardware versions are separate implementations and don't match. At speed `1.0`:

| Path | Style 1 | Style 2 |
|---|---|---|
| Software (both engines) | Rows shift up to 8 pixels, one wave per 64 rows, one cycle every 7168 ms (about 7.2 s). Columns shift up to 8 pixels, one wave per 64 columns, one cycle every 8192 ms **regardless of speed** (see below) | Up to 4 pixels per axis (two 2-pixel waves summed). Cycle times 1147 ms, 1434 ms and 1911 ms for the three time rates. Row-driven waves repeat every 64 rows; column-driven waves every 32 columns on Zandronum, every 64 on UZDoom (see "Engine-family divergence") |
| GLSL shader (UZDoom GL/GLES/Vulkan; Zandronum GL) | Each axis offset by up to 10% of the texture's size, as a sine of the other axis; one wave per texture repeat; one cycle every 8 s. Same on both engines | UZDoom: each axis offset by up to 5% of the texture size, plus a fixed 1.25% shift; one wave per repeat vertically, two horizontally; rates about 0.61, 0.36 and 0.49 cycles per second. Zandronum: a different function with up to about 6% vertical and 5% horizontal offset, rates 0.75 and 0.45 cycles per second |

**How speed enters.** In the software warps, the millisecond clock is multiplied by the speed and
a fixed ratio before it indexes a sine table (style 1 rows: x 32/28; style 2: x 40/28). In the
shaders, the timer uniform is seconds x speed. In both, a speed of `n` divides every cycle time by
`n`.

**Software style 1 quirk, both engines.** The column (vertical) pass is computed from the raw
clock, not the speed-scaled one (UZDoom `warpbuffer.h:54`; Zandronum `warptexture.cpp:163`; both
compute a scaled value and don't use it). So in the software renderers, speed changes only the
sideways motion. Speed `0` freezes the rows but the columns keep moving. Zandronum's GL CPU
fallback (below) does scale the column pass.

## Renderers

### UZDoom

- **Clock.** Both renderers read `screen->FrameTime`, milliseconds since the first frame, taken
  once per rendered frame (`d_main.cpp:1216`, `i_time.cpp:155`). It is real time, not game tics.
- **Software renderer** (paletted and true-colour). A warping texture gets an `FWarpTexture`
  wrapper (`r_swtexture.cpp:531`) that regenerates its pixels whenever the frame time changes
  (`warptexture.cpp:43-86`). Coordinates wrap with modulo, and the per-row/column step is scaled for
  non-power-of-two sizes so the wave still tiles (`warptexture.cpp:88-97`). Honours
  `gl_texture_hqresizemult` when hq-resizing applies to textures.
- **Hardware renderers** (OpenGL, GLES, Vulkan). The material picks the built-in "Warp 1" or
  "Warp 2" shader by warp style (`hw_material.cpp:71-74`, `hw_shaderpatcher.cpp:284-285`). The timer
  is frame time / 1000 x speed, uploaded unconditionally, so `0` freezes the warp at a fixed
  distortion and a negative speed runs it backward (`gl_renderstate.cpp:124`,
  `gles_renderstate.cpp:239`, `vk_renderstate.cpp:344`). A `func_warp3.fp` also ships in the shader
  folders but nothing selects it.
- **No clamping.** Warped textures are never edge-clamped (`gametexture.h:355`), including on
  two-sided mid-textures (`hw_walls.cpp:234`). Displaced samples wrap around to the opposite edge.

### Zandronum

- **Software renderer.** The warp replaces the texture's slot with an `FWarpTexture` or
  `FWarp2Texture` wrapping the original (`animations.cpp:578-584`), regenerated whenever
  `r_FrameTime` changes (`warptexture.cpp:76-90`). `r_FrameTime` is set by `I_GetTimeFrac`
  (`r_utility.cpp:852`) to the millisecond start of the next game tic (`src/sdl/i_system.cpp:316`,
  `src/win32/i_system.cpp:536-539`). So the software warp advances in 1/35-second steps, not every
  frame. Coordinates wrap with bit masks (`warptexture.cpp:154`, `163`, `215`, `218`), and
  `CalcBitSize` rounds the width mask down (`texture.cpp:188-212`). So a width or height that isn't a power
  of two warps incorrectly: part of the source is never sampled and the rest repeats or scrambles.
- **OpenGL renderer, shader path.** On a GPU reporting GLSL 1.30 or the shader4 extensions
  (`gl_interface.cpp:260-262`, shader model 4), the material uses the warp style as its shader index
  (`gl_material.cpp:617-622`) and the GLSL warp functions run. The timer is `gl_frameMS` (per-frame
  milliseconds, `gl_scene.cpp:1047`) / 1000 x speed. It is **only uploaded when the speed is above
  0** (`gl_shader.cpp:224`), so a warp with speed `0` or below shows whatever timer value that
  shader last had, which can be another warp's.
- **OpenGL renderer, CPU fallback.** On shader model 3 with `gl_warp_shader` off (its default,
  `gl_shader.cpp:63`), or on shader model 2 or lower, `SetupShader` asks for a software warp
  instead (`gl_renderstate.cpp:108-132`). `FGLTexture::WarpBuffer` then warps the 32-bit texels
  with the software math, on the tic-stepped `r_FrameTime` clock, and skips any texture wider or
  taller than 256 pixels, which shows unwarped (`gl_material.cpp:195-266`).
- **No clamping** on the GL path either (`gl_material.cpp:849`).

## Interaction with other definitions

### A texture/flat animation on the same texture

Warping is a property of each individual texture, not of an animation. An animation works by
redirecting the base texture to its current frame (UZDoom `animations.cpp:1176-1182`; Zandronum
`animations.cpp:928-934`), and the renderer then draws that frame with the frame's own warp
setting. So:

- A `warp` on an animation's base texture only warps while the base itself is the frame shown.
  To warp the whole animation, warp every frame, with the same style and speed if they should
  look continuous.
- The two blocks can come in either order.
- **Decals.** After all ANIMDEFS lumps are read, every texture in a **`range`** animation gets
  the base texture's decal setting (`FixAnimations`, UZDoom `animations.cpp:882-905`; Zandronum
  `animations.cpp:686-727`). An `allowdecals` on a warp for a non-base frame of a range is lost.
  `pic` animations aren't touched by that pass, so each frame keeps its last setting. Since the
  animation block and the warp both write the same per-texture decal flag, whichever is read
  last decides for a `pic` frame or a range's base.

See [texture and flat animations](texture-flat-animations.md) for the animation side.

### GLDEFS

GLDEFS is parsed after ANIMDEFS on both engines (UZDoom `d_main.cpp:3632`, `3670`; Zandronum
`TexMan.Init` at `d_main.cpp:2984` before `R_Init` at `3012`, which reaches `gl_ParseDefs` via
`gl_scene.cpp:1274`).

- **A `HardwareShader` on a warped texture is dropped** with the console message `Cannot combine
  warping with hardware shader on texture '<name>'` (UZDoom `gldefs.cpp:1543-1546`,
  `1962-1965`; Zandronum `gl_shader.cpp:690-693`). The warp stays.
- **A brightmap on a warped texture** is dropped on Zandronum with `Cannot combine warping with
  brightmap on texture '<name>'` (`gl_texture.cpp:771-774`). UZDoom has no such check; whether its
  warp shaders then draw the brightmap was not traced.

See [the GLDEFS overview](../../gldefs/concepts/gldefs-overview.md).

## Engine-family divergence

- **Long texture names.** UZDoom rejects `warp` on a full-path texture name (fatal); Zandronum has
  no check.
- **Software clock.** UZDoom's software warp updates every frame; Zandronum's steps once per game
  tic.
- **Non-power-of-two sizes.** UZDoom's software warp handles them; Zandronum's software warp and
  GL CPU fallback use bit masks and draw them wrong.
- **Software style 2 width.** UZDoom's `FWarpTexture` constructor sets a column multiplier of 256
  for style 2 and then unconditionally overwrites it with 128 (`warptexture.cpp:38-39`). Zandronum
  uses 256 (`warptexture.cpp:215`, `218`). So UZDoom's software `warp2` column-driven waves are
  twice as wide as Zandronum's.
- **GLSL style 2.** The two engines ship different `func_warp2.fp` functions (amplitudes and rates
  in the table above). Style 1's shader math is the same on both.
- **Speed 0 or negative on hardware.** UZDoom uploads the timer anyway (frozen at `0`, backward
  when negative). Zandronum's GL skips the upload, leaving the shader's previous timer value.
- **Zandronum GL fallback.** Zandronum can warp on the CPU inside its GL renderer (old shader
  models, or `gl_warp_shader` off on shader model 3), with a 256-pixel size limit. UZDoom's hardware
  renderers always use the shader.
- **Brightmaps.** Zandronum refuses a brightmap on a warped texture; UZDoom has no such check.
- **Editors.** UltimateDoomBuilder and SLADE both list `warp`, `warp2` and `allowdecals`. Neither
  describes the speed argument or the argument order.

## See also

- [The ANIMDEFS lump](animdefs-lump.md) for the outer grammar, load order and redefinition rules
  of every block type.
- [Texture and flat animations](texture-flat-animations.md) for animations sharing a texture with
  a warp.
- [`../../decaldef/concepts/decaldef-lump.md`](../../decaldef/concepts/decaldef-lump.md) for the
  decals `allowdecals` lets through.
- [`../../gldefs/concepts/gldefs-overview.md`](../../gldefs/concepts/gldefs-overview.md) for
  hardware shaders and brightmaps.
