# ANIMDEFS doc index

Router only. See `AGENTS.md` for scope and source locations, `../shared/AUTHORING.md` for
tiers/engine-scope/licensing.

**Both engines parse ANIMDEFS**; `canvastexture`, `firetexture`, `random`, `notrim` and the
`hdr`/`translucent`/`offset` camera texture options are UZDoom-only.

## Concepts

- [The ANIMDEFS lump](concepts/animdefs-lump.md) — tier A. When it's read (`ANIMATED`, every
  `ANIMDEFS`, then `SWITCHES`); outer grammar with no braces (a block ends at the first unknown
  word, so a bad keyword is a fatal top-level error); texture/flat animations, switches,
  warp/warp2, camera textures, animated doors, sky offsets; timing (animations in milliseconds on
  the render clock, switches in game tics); what `optional` does and doesn't cover; redefinition
  per block type (animated doors: first wins); errors; `oscillate` placement and other engine
  differences; which Zandronum machine's copy decides what (switches server-side).
- [`texture` and `flat` animation blocks](concepts/texture-flat-animations.md) — tier B. Every
  keyword per engine (`optional`, `pic`, `range`, `tics`/`rand`, `allowdecals`, `oscillate`,
  UZDoom-only `random`/`notrim`); frame numbers and the all-digits trap; how a `range` follows
  texture order (same kind and same file, or it's silently dropped); durations in truncated ms,
  the zero-duration hang and reversed-`rand` stall; `oscillate` placement and the Zandronum
  `optional` hole; `allowdecals` order on backward ranges; UZDoom per-map reset; errors.
- [ANIMDEFS switches](concepts/switches.md) — tier B. Game words (`doom` also covers Chex),
  `quest`, `on`/`off` states with `sound` and `pic` frames in whole game tics (integers only); the
  last frame's duration is never read (repeatable switches hold 35 tics) and `tics 0` on any other
  frame freezes the switch; omitted `off` inherits the `on` sound; press/reset sounds; the Boom
  `SWITCHES` lump and why it beats ANIMDEFS; part check order and Push activation differ by
  engine; server-side switches on Zandronum.
- [ANIMDEFS warp and warp2](concepts/warps.md) — tier B. Syntax and fixed argument order (speed
  before `allowdecals`); speed as a multiplier on a millisecond or seconds clock, never tics;
  redefinition keeps the first style; a missing texture with trailing arguments is fatal; what
  each style looks like per renderer; warps on animation frames; GLDEFS shader and brightmap
  conflicts; each engine's software, shader and CPU-fallback paths and their clocks.
- [ANIMDEFS animated doors](concepts/animated-doors.md) — tier B. `animateddoor` keywords
  (`opensound`/`closesound` are SNDSEQ sequence names, not SNDINFO sounds); first definition
  wins; matched on the line's front upper texture; `Door_Animated` speed/delay in raw tics (a frame
  lasts speed+1 tics); `Door_AnimatedClose` is UZDoom-only; the Zandronum server runs the door and
  sends texture names, line flags, ceiling heights and sequence names.
- [Camera and canvas textures](concepts/camera-canvas-textures.md) — tier B. `cameratexture`
  (both engines) and `canvastexture` (UZDoom-only): render size vs `fit` display size, option
  order per engine, UZDoom-only `hdr`/`translucent`/`offset`; which texture gets replaced; ACS
  `SetCameraToTexture` and its failures; ZScript `TexMan`/`Canvas` in prose; re-rendering only
  visible textures, one full scene render each; per-renderer support; the Zandronum server
  broadcast (FOV sent as a byte, replayed to late joiners).
- [ANIMDEFS skyoffset and firetexture](concepts/firetexture-skyoffset.md) — tier B. `skyoffset`
  parses the same on both engines but only some renderers and sky heights honour it (never
  Zandronum's software renderer); `firetexture` is UZDoom-only: fixed 64x128, `tics`,
  `color`/`palette` entries coolest first, one step per frame on the render clock, reset on level
  load, and a sub-0.035 `tics` hang (source reading).
