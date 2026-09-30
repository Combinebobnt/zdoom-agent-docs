# Camera and canvas textures (`cameratexture`, `canvastexture`)

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/gamedata/textures/animations.cpp` (`InitAnimDefs`, `ParseCanvasTexture`, `ParseCameraTexture`), `src/common/textures/textures.h` (`FCanvasTexture`, `GetTranslucency`), `src/common/textures/gametexture.cpp` (`FGameTexture::Setup`), `src/common/textures/texturemanager.cpp` (`CheckForTexture`), `src/common/engine/sc_man.cpp` (`GetNumber`, `ScriptError`), `src/r_data/r_canvastexture.cpp` (`FCanvasTextureInfo::Add`, `UpdateAll`, `Serialize`, `SetCameraToTexture`), `src/scripting/vmthunks.cpp` (`TexMan.SetCameraToTexture`, `SetCameraTextureAspectRatio`), `src/common/2d/v_2ddrawer.cpp` (`GetTextureCanvas`), `src/common/scripting/interface/vmnatives.cpp` (`TexMan.GetCanvas`), `src/rendering/hwrenderer/hw_entrypoint.cpp` (`RenderView`), `src/rendering/swrenderer/r_swrenderer.cpp` (`RenderView`, `RenderTextureView`), `src/rendering/swrenderer/textures/swcanvastexture.cpp`, `src/rendering/r_utility.cpp` (`R_SetFOV`), `src/common/rendering/vulkan/textures/vk_hwtexture.cpp` (`CreateImage`), the OpenGL, GLES and Vulkan render-state `ApplyMaterial` code, `src/playsim/p_acs.cpp` (`PCD_SETCAMERATOTEXTURE`), `src/p_setup.cpp` and `wadsrc/static/zscript/engine/base.zs`/`doombase.zs` (the `TexMan` and `Canvas` declarations), and the Zandronum source's `src/textures/animations.cpp` (`ParseCameraTexture`), `src/textures/canvastexture.cpp` (`FCanvasTexture`), `src/textures/texture.cpp` (`SetScaledSize`), `src/textures/texturemanager.cpp` (`CheckForTexture`), `src/r_utility.cpp` (`FCanvasTextureInfo::Add`, `UpdateAll`, `EmptyList`, `UpdateToClient`, `R_SetFOV`), `src/p_acs.cpp` (`PCD_SETCAMERATOTEXTURE`), `src/sv_commands.cpp` (`SERVERCOMMANDS_SetCameraToTexture`, `EnsureActorHasNetID`), `src/cl_main.cpp` (`client_SetCameraToTexture`), `src/sv_main.cpp` (the connect-time replay), `src/r_swrenderer.cpp` (`RenderView`, `RenderTextureView`), `src/gl/scene/gl_scene.cpp` (`FGLInterface::RenderTextureView`), `src/gl/textures/gl_material.cpp` and `src/p_setup.cpp`. Keyword list cross-checked against UltimateDoomBuilder's `Build/Scripting/ZDoom_ANIMDEFS.cfg` and SLADE's `z_animdefs` block in `dist/res/config/languages/zdoom.txt`.

A **camera texture** is a texture whose pixels are a live render of the world from an actor's
point of view: a security monitor, a mirror-like screen, a scope. `cameratexture` in ANIMDEFS
declares the texture and its render resolution; a script then picks the actor it shows. UZDoom
adds **`canvastexture`**, a texture ZScript can draw 2D graphics into. This page covers both
keywords, their options per engine, how a view gets assigned, and what they cost. For the lump's
outer grammar, load order and error handling in general, see
[the ANIMDEFS lump](animdefs-lump.md).

## Syntax

```text
cameratexture <name> <width> <height> [fit <display width> <display height>] [worldpanning]

// UZDoom: options in any order, each optional, plus three more
cameratexture <name> <width> <height> [fit <w> <h>] [worldpanning] [hdr] [translucent] [offset [<x> <y>]]
canvastexture <name> <width> <height> [same options as cameratexture]
```

A block ends at the first word that isn't one of its options, like every other ANIMDEFS block.

| Keyword | Arguments | Meaning | UZDoom | Zandronum |
|---|---|---|---|---|
| `cameratexture` | name, width, height (integers) | Creates the texture, or replaces an existing one of that name, with a render target of `width` x `height` texels | yes | yes |
| `canvastexture` | same as `cameratexture` | Same texture type; the name signals it's meant for ZScript drawing | yes | no (fatal unknown keyword) |
| `fit` | display width, display height (integers) | The size the texture occupies in the world, independent of its render resolution | yes, any position | yes, only as the first option |
| `worldpanning` | none | Texture offsets on lines using it are in world units, not texels | yes, any position | yes, only after `fit` (or first if no `fit`) |
| `hdr` | none | Floating-point render target (Vulkan only, see "Renderers") | yes | no |
| `translucent` | none | Hardware renderers honour the texture's alpha instead of drawing it opaque | yes | no |
| `offset` | optional x, y (integers) | Sets the texture's left/top offsets. With no numbers, copies the offsets of the texture being replaced (0, 0 for a new one) | yes | no |

### Sizes and units

- **`<width>` and `<height>` are render resolution in texels.** Every update renders the scene at
  exactly that size, so they set both the image sharpness and the cost (see "Update behavior").
- **The display size defaults to the replaced texture's size.** If `<name>` already exists, the
  camera texture takes over its displayed (scaled) size. So a 256 x 256 camera texture replacing
  a 64 x 64 wall texture still covers 64 x 64 map units. For a brand-new name, the display size is
  `width` x `height`. `fit` overrides either default. UZDoom: `animations.cpp:731-746,755-760`,
  applied at `:788-789`; Zandronum: `animations.cpp:632-647,650-656`, applied via
  `SetScaledSize` at `:673`.
- **All numbers are integers.** A value like `64.5` fails `GetNumber` with
  `SC_GetNumber: Bad numeric constant`, a fatal script error on both engines. Neither parser
  range-checks width, height or `fit`. What a zero or negative value does at render time was not
  traced.
- **Hardware renderers derive the camera's aspect ratio from the display size**, not the render
  size: UZDoom stores `fit width / fit height` at parse time (`animations.cpp:788`) and divides it
  by the map's pixel stretch when rendering (`hw_entrypoint.cpp:382`). Zandronum's OpenGL path
  uses the texture's scaled size (`gl_scene.cpp:1290-1291,1333`). The software renderers render
  into a `width` x `height` canvas; the aspect they derive from it was not traced.

### Which texture gets replaced

- The name is looked up as a **flat first**, then any texture type. A replaced texture keeps its
  use type; a new one is a wall texture. UZDoom: `animations.cpp:727-729,738`; Zandronum:
  `animations.cpp:630,637,645`.
- **UZDoom never replaces a full-path texture** (one named by its path in a PK3). The lookup skips
  long-name textures (`TEXMAN_ShortNameOnly`, `texturemanager.cpp:173`), so a new texture is
  created alongside it instead.
- **Zandronum keeps the first 8 characters** of the name, like every Zandronum texture
  (`char Name[9]`, `textures.h:185`; `canvastexture.cpp:44`).
- **The old image is gone.** Nothing of the replaced texture survives except its display size,
  use type and (on UZDoom, with a bare `offset`) its offsets. Zandronum always resets offsets to
  0 (`canvastexture.cpp:47`). UZDoom also starts at 0 unless `offset` is given
  (`gametexture.cpp:57-79`).

### Example

```text
// Works on both engines: 256x128 render shown at the 64x32 size of a monitor texture
cameratexture MYMONTR1 256 128
    fit 64 32
    worldpanning

// UZDoom only: a translucent drawing surface for ZScript
canvastexture MYSCREEN 320 200
    translucent
```

## Giving a camera texture its view

No world view is rendered into the texture until an actor is assigned to it.

### ACS `SetCameraToTexture` (both engines)

```acs
SetCameraToTexture(12, "MYMONTR1", 90);   // tid 12's view, 90 degree FOV
```

- **Arguments:** camera TID, texture name, field of view. TID 0 means the script's activator;
  otherwise the first actor with that TID is used. **FOV is plain integer degrees**, not fixed
  point.
- **Failures:** no matching actor (or TID 0 with no activator) does nothing, silently. A name
  that isn't a texture prints `SetCameraToTexture: <name> is not a texture`. A texture that
  exists but isn't a camera/canvas texture prints `<name> is not a valid target for a camera`.
  Neither stops the script. UZDoom: `p_acs.cpp:9979-10008` and `r_canvastexture.cpp:40-55`;
  Zandronum: `p_acs.cpp:12558-12590` and `r_utility.cpp:1012-1026`.
- **The script lookup only finds wall (or override) textures** (texture type wall, no fallback to
  other types), in both engines. Per those lookup flags, a camera texture that replaced a *flat*
  keeps the flat use type and can't be found by name, so the call prints "is not a texture".
  Observed live on both engines (2026-09-29, local test builds, probe map): after
  `cameratexture FCAM 64 64` over a PK3 flat `FCAM`, `SetCameraToTexture(tid, "FCAM", 90)`
  printed `SetCameraToTexture: FCAM is not a texture`, while a new name made the same way was
  accepted silently.
- **Reassigning** a texture that already has a camera switches it to the new actor and FOV. One
  texture shows one camera; one actor can feed several textures.
- **FOV range.** The software renderers clamp FOV to 5 to 170 degrees (`R_SetFOV`, UZDoom
  `r_utility.cpp:227-237`, Zandronum `r_utility.cpp:362-374`). The hardware renderers pass it
  straight to the projection with no clamp (UZDoom `hw_entrypoint.cpp:97-160`, Zandronum
  `gl_scene.cpp:263-271,892-933`).

### ZScript (UZDoom only)

Described in prose; see the `TexMan` and `Canvas` declarations in the UZDoom source's
`wadsrc/static/zscript/doombase.zs` and `engine/base.zs`.

- **`TexMan.SetCameraToTexture`** takes an actor, a texture name and a floating-point FOV in
  degrees. It does the same assignment as the ACS call, but **every failure is silent**: a missing
  texture or a non-canvas texture just does nothing. The actor is not null-checked, unlike the ACS
  path (`r_canvastexture.cpp:87-99`).
- **`TexMan.SetCameraTextureAspectRatio`** overrides the aspect ratio a hardware renderer uses
  for the texture: the given scale, multiplied by the texture's *render* width/height ratio unless
  told not to (`vmthunks.cpp:79-100`, `textures.h:332`). Silent on a non-canvas texture. The
  software renderer doesn't read this value.
- **`TexMan.GetCanvas`** returns a `Canvas` object for a camera or canvas texture (null for any
  other texture or an unknown name), creating it on first use (`v_2ddrawer.cpp:1236-1258`). Its drawing methods mirror
  the `Screen` 2D API: textures, text, characters, lines, shapes, fills, dims, clears, clipping
  rectangles, stencil and transforms. Draw calls are queued, and the queue is replayed into the
  texture and then emptied the next time the texture needs an update (`hw_entrypoint.cpp:358-371`).
  **Only the hardware renderers do this**; the software renderer never replays a canvas queue.

`canvastexture` and `cameratexture` build the same texture type: UZDoom's `ParseCanvasTexture`
just calls `ParseCameraTexture` (`animations.cpp:698-702`; the source marks this sharing as
the present state, not a fixed design). So `GetCanvas` works on a `cameratexture` and `SetCameraToTexture` on a
`canvastexture`. That's present-day behavior, not a documented guarantee. On a texture with both
a canvas and a camera, the hardware renderer draws the canvas queue first and the camera view
second, so the camera view wins (`hw_entrypoint.cpp:359-388`).

## Update behavior and render cost

- **Only textures drawn in the previous frame are re-rendered.** Drawing a camera/canvas texture
  (any renderer) marks it as needing an update; before the next main view, the engine renders
  every assigned texture that is marked, then clears the mark (UZDoom `r_canvastexture.cpp:109-118`,
  Zandronum `r_utility.cpp:1062-1080`). So a monitor nobody can see costs nothing, and a newly
  visible one shows its previous image for one frame.
- **Each visible camera texture is one extra full scene render per frame**, at the texture's
  `width` x `height`, with no rate cap. Several visible monitors, or one large one, multiply the
  renderer's work. Lower resolutions are the only knob.
- **A camera that is destroyed** stops the updates; the texture keeps its last image (the
  viewpoint pointer is a GC-cleared object pointer in both engines).
- **Assignments are per map.** They're cleared when a map loads (UZDoom `p_setup.cpp:339`,
  Zandronum `p_setup.cpp:3943`) and saved in savegames.
- **Automap side effect.** Walls a camera sees are marked as seen on the automap, as if the
  player had seen them. The software renderers skip this on the first update after an
  assignment only (UZDoom `r_swrenderer.cpp:244`, Zandronum `r_swrenderer.cpp:284`); the hardware
  BSP pass marks lines in every view (UZDoom `hw_bsp.cpp:439`, Zandronum `gl_bsp.cpp:180`).

## Renderers

| Renderer | Camera view | ZScript canvas drawing | `hdr` | `translucent` |
|---|---|---|---|---|
| UZDoom Vulkan | yes | yes | 32-bit float RGBA image (`vk_hwtexture.cpp:116`) | honoured |
| UZDoom OpenGL / GLES | yes | yes | no reader, ignored | honoured |
| UZDoom software | yes, for the viewed map only | no | ignored | no reader, ignored |
| Zandronum software | yes | n/a | n/a | n/a |
| Zandronum OpenGL | yes | n/a | n/a | n/a |

- **UZDoom's hardware renderers update the camera textures of every loaded map**; the software
  renderer only updates those of the map being viewed (`hw_entrypoint.cpp:375-386` against
  `r_swrenderer.cpp:184-187`).
- **`translucent`**: without it, the OpenGL, GLES and Vulkan render states draw a canvas texture
  in opaque mode, so its alpha channel is ignored (`gl_renderstate.cpp:306`,
  `gles_renderstate.cpp:432`, `vk_renderstate.cpp:375`).
- **Zandronum OpenGL** renders a camera view into the back buffer and copies it into the texture,
  unless the `gl_usefb` cvar is on or the texture is larger than the screen, in which case it
  renders into a framebuffer object (`gl_scene.cpp:1286-1340`, the size test at `:1299`).

## Errors

| Condition | UZDoom | Zandronum |
|---|---|---|
| Name, width or height missing, or width/height not an integer | Fatal script error | Same |
| `fit` with fewer than two integers | Fatal | Same |
| `offset` followed by exactly one number | Fatal (the second is required) | `offset` itself is fatal |
| An option Zandronum lacks (`hdr`, `translucent`, `offset`), or `worldpanning` before `fit` | Accepted | Fatal unknown top-level keyword |
| `canvastexture` | Accepted | Fatal unknown top-level keyword |
| Zero or negative width, height or `fit` | Not checked | Not checked |

"Fatal" here is `FScanner::ScriptError`, which aborts startup. See the lump page's
[Errors](animdefs-lump.md#errors) section for the general mechanism.

## Engine-family divergence

- **`canvastexture`** and the ZScript `TexMan`/`Canvas` interfaces exist only on UZDoom.
- **Option order.** Zandronum reads at most one `fit`, then at most one `worldpanning`, in that
  order (`animations.cpp:649-672`). UZDoom loops over its five options in any order and any number
  of times, the last value winning (`animations.cpp:749-786`).
- **`hdr`, `translucent`, `offset`** are UZDoom-only.
- **Offsets.** Zandronum always zeroes the texture's offsets. UZDoom zeroes them too unless
  `offset` is given.
- **Long names.** UZDoom won't replace a full-path texture; Zandronum truncates every texture name
  to 8 characters.
- **FOV type.** UZDoom stores the camera FOV as a double (ZScript can pass fractions; ACS still
  passes an integer). Zandronum stores an integer.
- **Editors.** Neither UltimateDoomBuilder's config nor SLADE's lists `translucent` or `offset`.
  UltimateDoomBuilder also lacks `canvastexture` and `hdr`; SLADE has both. Neither marks which
  keywords Zandronum rejects.

## Zandronum-specific: which machine's copy is used

Each client renders its own camera textures from its own ANIMDEFS, so the texture must be defined
in every client's copy. The assignment comes from the server:

- **Server sends every assignment.** When a server-side script runs `SetCameraToTexture`, the
  server applies it and sends `SVC_SETCAMERATOTEXTURE` to all clients with the camera's network
  ID, the texture name as the script gave it, and the FOV (`p_acs.cpp:12584-12587`,
  `sv_commands.cpp:5038-5051`). It sends this even when its own `Add` refused the texture as not
  a camera texture.
- **FOV travels as one byte.** Values outside 0 to 255 arrive wrapped on clients, while the
  server keeps the original.
- **No network ID, no message.** A camera actor without a network ID (for example a server-only
  actor) is never sent; clients show nothing.
- **Client side** (`cl_main.cpp:9485-9515`): an unknown network ID is ignored silently; a texture
  name the client can't find prints the warning `client_SetCameraToTexture: <name> is not a
  texture`; otherwise the client makes the same assignment locally.
- **Late joiners** get every current assignment replayed when they connect
  (`sv_main.cpp:2984`, `r_utility.cpp:1167-1173`), using the texture's stored (8-character) name.
- **Clientside scripts** calling `SetCameraToTexture` just assign locally; nothing is sent.

## See also

- [The ANIMDEFS lump](animdefs-lump.md) for the outer grammar, load order and error mechanism.
- [Texture and flat animations](texture-flat-animations.md), [warps](warps.md) and
  [fire textures and sky offsets](firetexture-skyoffset.md), the other ANIMDEFS blocks that change
  how a texture looks.
- `SetCameraToTexture` in [`../../acs/INDEX.md`](../../acs/INDEX.md) (signature only so far).
- [`../../textures/concepts/textures-lump.md`](../../textures/concepts/textures-lump.md) for
  defining the texture a camera texture replaces.
