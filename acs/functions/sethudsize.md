# `SetHudSize`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `SetHudSize - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=SetHudSize&oldid=35982`), verified against
the Zandronum source's `src/p_acs.cpp` (`PCD_SETHUDSIZE` case, line 12506; `DLevelScript` constructor,
line 13120; savegame serialization, line 3769), the Zandronum source's `src/p_acs.h` (line 1074,
`hudwidth`/`hudheight` field declarations), the Zandronum source's `src/g_shared/hudmessages.cpp`
(`DHUDMessage` constructor lines 78-156, `DHUDMessage::Draw` lines 400-460), and
the Zandronum source's `src/sv_commands.cpp` (`SERVERCOMMANDS_PrintACSHUDMessage`, lines 2416-2437) on
2026-07-29.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin — `zt-bcc/src/builtin.c:117`: `{ "sethudsize", ";iib" }` (void return,
params `int, int, bool`), compiles to `PCD_SETHUDSIZE` (`zt-bcc/src/semantic/asm.c:365`,
`zt-bcc/src/codegen/pcode.c:280`, taking no operand bytes itself — all three arguments are pushed
on the ACS stack like a normal builtin call). Not a `zcommon.bcs` `special`-table entry (no
positive/negative index) and not one of the format-function builtins like `HudMessage`/`Print` —
plain fixed-arity call.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

## Syntax

```text
void SetHudSize(int width, int height, bool statusbar);
```

Matches the wiki's declared signature exactly — no fork divergence in the signature itself.

## What it actually sets, and where that state lives

`PCD_SETHUDSIZE`'s handler (`p_acs.cpp:12506-12514`) is a 3-line assignment:

```cpp
hudwidth = abs (STACK(3));   // width
hudheight = abs (STACK(2));  // height
if (STACK(1) != 0)           // statusbar
    hudheight = -hudheight;  // negative height means the HUD size covers the status bar
sp -= 3;
```

Two things here are undocumented by the wiki:

- **`statusbar` is encoded as the sign bit of the stored height, not a separate field.** There is
  no independent "covers status bar" flag stored anywhere — `hudheight < 0` *is* the flag, checked
  later in `DHUDMessage::Draw` (`hudmessages.cpp:443-450`): a negative `HUDHeight` uses the raw
  `screen_height` directly (covering the status bar), while a positive one goes through
  `Scale(HUDHeight, screen_height, bottom)` where `bottom` is the screen height *above* the status
  bar. This matches the wiki's described `TRUE`/`FALSE` behavior, just via an implementation detail
  (sign-encoding) the wiki doesn't mention.
- **`hudwidth`/`hudheight` are per-script-instance state, not global.** They're plain member fields
  of `DLevelScript` (`p_acs.h:1074`) — i.e. each running script *instance* has its own copy. The
  constructor unconditionally resets both to `0` for every newly spawned script instance
  (`p_acs.cpp:13120`, right next to the `ClipRectLeft`/`WrapWidth` resets), regardless of what any
  other currently-running script (or an earlier instance of the very same numbered/named script)
  previously set via `SetHudSize`. Concretely: `SetHudSize` in script A has **zero effect** on
  script B's `HudMessage`/`HudMessageBold` calls, and re-running script A from scratch (e.g. via
  `ACS_Execute` after it terminated) starts back at the unscaled default even if the previous run
  called `SetHudSize` and never reset it. The wiki's framing ("causes text messages to be
  stretched...") reads as if this were a global HUD mode switch; it is not — it's scoped exactly
  like `SetFont`'s `activefont` and the clip-rect/wrap-width state sitting right next to it in the
  same struct, all per-script fields.
- The value **is** preserved across a `Delay`/blocking call within the same script instance
  (nothing resets it mid-run) and is saved/restored across a savegame (`arc << hudwidth <<
  hudheight;`, `p_acs.cpp:3769`), so it survives a save/load but not a fresh script re-entry.

## Reset behavior (`width` or `height` == `0`)

Confirmed exactly as the wiki describes, but the check is on the *consuming* side
(`DHUDMessage`'s constructor, `hudmessages.cpp:81`), not in `PCD_SETHUDSIZE` itself:
`if (hudwidth == 0 || hudheight == 0)` — either one being zero (not requiring both) is enough to
fall back to the normal `[-2.0, 2.0]`-range coordinate interpretation for every subsequent
`HudMessage`/`HudMessageBold` call from that script instance, until `SetHudSize` is called again
with both nonzero. `SetHudSize(0, 0, false)` (the wiki's suggested "restore normal" call) works for
this reason, but so does e.g. `SetHudSize(0, 200, false)` — the `statusbar` argument and the
nonzero `height` are simply irrelevant once `width` is `0`.

## Calling it more than once

Safe with no cumulative or undefined effects. There is no queue, no interaction with in-flight
`HudMessage`s (an already-built `DHUDMessage` captured its own `HUDWidth`/`HUDHeight` at
construction time and doesn't re-read the script's live `hudwidth`/`hudheight` afterward), and no
per-tic accumulation — it's a flat overwrite. Calling it once per tic, or several times back-to-back
before the next `HudMessage`, only matters for whatever the *last* call before that `HudMessage` set.

## Zandronum netcode note (not on the wiki)

`SetHudSize` itself has no dedicated network message — there's no "sync HUD size to clients" call.
Instead, whenever the server forwards an ACS `HudMessage`/`HudMessageBold` to clients via
`SERVERCOMMANDS_PrintACSHUDMessage`, it reads the *originating script's own* `hudwidth`/`hudheight`
directly off the `DLevelScript*` and includes them in that message's payload, flagging
`HUDMESSAGE_SEND_HUDSIZE` only when at least one is nonzero (`sv_commands.cpp:2433-2437`). So the
HUD-size state rides along per-message with whichever script instance produced it, consistent with
it being per-script-instance state rather than a global the server would otherwise need to
broadcast independently.

## What drawing path each state actually takes, and whether the two engines agree (verified 2026-08-04)

Both branches from "Reset behavior" above bottom out in `DHUDMessage::DoDraw`. Zandronum's version
(`hudmessages.cpp:479-513`) and UZDoom's (`src/g_statusbar/hudmessages.cpp:465-490`) structurally
match line-for-line except for engine-specific scale-source calls, and both pick one of these paths:

**`hudwidth`/`hudheight` nonzero (`SetHudSize` called with both nonzero) — identical on both
engines:** always takes a `DTA_VirtualWidth, HUDWidth, DTA_VirtualHeight, hudheight` branch
(Zandronum `hudmessages.cpp:503-512`; UZDoom `hudmessages.cpp:480-489`, byte-for-byte the same tag
list) — the renderer scales glyph size and position as if the screen were exactly
`hudwidth`×`|hudheight|` pixels, then stretches that virtual canvas to the real display, on both
engines identically. This is the one drawing mode this doc can say is genuinely
engine-fork-independent: a script that always calls `SetHudSize` before emitting a `HudMessage`
gets the same relative text size and layout on Zandronum and UZDoom regardless of either engine's
own cvar defaults below. Coordinates in this mode are literal pixels in the `hudwidth`×`hudheight`
virtual grid (with the fractional-part alignment-selector encoding covered in `HudMessage`'s own
doc), not the `[-2.0, 2.0]` proportional range used in the zero case.

**`hudwidth`/`hudheight` left at `0` (never called, or reset via `SetHudSize(0,0,false)`) — the two
engines diverge here, and neither engine's own default state applies any scaling *consistently*:**

- **Zandronum:** gated on `con_scaletext`, a `Bool` cvar defaulting to **off**
  (`CUSTOM_CVAR(Bool, con_scaletext, 0, ...)`, `c_console.cpp:195`). With it off (the shipped
  default), `g_bScale` is false, so `DoDraw` takes `DTA_CleanNoMove, clean`
  (`hudmessages.cpp:483-490`) with `clean` hardcoded `false` in the caller (`Draw`,
  `hudmessages.cpp:344`; the one line that would set it `true` is commented out). This performs
  no rescale at all — text draws at literal native screen pixels, computed against the real
  `SCREENWIDTH`/`SCREENHEIGHT` (`hudmessages.cpp:356-357`). Apparent text size is therefore
  resolution-*dependent* in Zandronum's default state: the same physical pixel size regardless of
  the player's actual resolution, so it reads proportionally smaller at higher resolutions. If a
  player (or server, since it's `CVAR_ARCHIVE` client-side) opts into `con_scaletext=1`, `DoDraw`
  instead takes `DTA_UseVirtualScreen, true` (`hudmessages.cpp:491-499`), scaling against
  `con_virtualwidth`/`con_virtualheight` — two more cvars whose engine-coded defaults are **640**
  and **480** (`c_console.cpp:210-222`).
- **UZDoom:** gated on `active_con_scaletext()` (`sbar.h:36-40`), which always returns a scale —
  there is no "no scaling" state analogous to Zandronum's default-off `g_bScale`. It resolves to
  `GetUIScale(drawer, con_scaletext)` (`v_draw.cpp:128-146`); UZDoom's `con_scaletext` is an `Int`
  cvar (not `Bool`) whose engine default is also `0` (`c_notifybuffer.cpp:55`), and at `0` (and with
  `uiscale`, also default `0` — `v_video.cpp:123` — not overriding it), `GetUIScale` takes its
  "auto" branch (`v_draw.cpp:132-138`, comment: `// Default should try to scale to 640x400`):
  `scaleval = max(1, min(screenHeight/400, screenWidth/640))`, floored to an integer. `DoDraw`
  (`hudmessages.cpp:467-476`) then passes `DTA_VirtualWidth, screenWidth/scale` — e.g. at 1920×1080,
  `scale = min(2, 3) = 2`, giving an effective virtual width of 960 (a 2× enlargement versus
  "native"). **This is the previously-reported "hudmessage text renders giant regardless of
  `hud_scale`" behavior** — `hud_scale`/`hud_althudscale` govern a *different* scale path
  (`shared_hud.cpp:169`, the SBARINFO/altHUD status bar), never this one, so it has no effect on an
  unmanaged `HudMessage`. Unlike Zandronum, this "auto" scale is stepped (integer, resolution-band
  dependent) rather than smoothly proportional, and it is active by default — there is no
  UZDoom analog of Zandronum's true 1:1-native-pixel default state.

Net effect: with no `SetHudSize` call anywhere, Zandronum's default (unscaled native pixels) and
UZDoom's default (an active ~2-3×-at-typical-resolutions auto-scale, floored per resolution band)
produce visibly different, engine-specific apparent text sizes for the exact same `HudMessage` call
— confirmed from source on both sides, not just from the bug report that originally surfaced it. An
explicit `SetHudSize(w, h, false)` call is the only path documented above that routes both engines
through the same tag list and virtual canvas, unconditional on either engine's own scaling cvars.

## The wiki's "4:3 area of the screen in the center" claim, confirmed and quantified (verified 2026-08-05)

Traced past `DoDraw` into the renderer's own virtual-screen math on both engines: the wiki is right,
and the effect is a **hardcoded aspect-correction pillarbox that ignores whatever `width` the caller
passed to `SetHudSize`**, not a letterbox proportional to a virtual-canvas aspect mismatch.

`DHUDMessage::DoDraw`'s `hudheight != 0` branch (Zandronum `hudmessages.cpp:501-511`; UZDoom's
equivalent, `g_statusbar/hudmessages.cpp:481-482`, is structurally identical) draws with
`DTA_VirtualWidth, HUDWidth, DTA_VirtualHeight, hudheight` and no `DTA_KeepRatio` tag, so
`parms->keepratio` stays at its default `false` (`v_draw.cpp:384`) and the tag parser's fallthrough
(`v_draw.cpp:715-718`) calls `VirtualToRealCoords(..., vwidth, vheight, vbottom,
handleaspect=true)`. Zandronum's `VirtualToRealCoords` (`v_draw.cpp:760-798`) branches on `myratio
= CheckRatio(Width, Height)` — the REAL screen's aspect-ratio bucket (4:3/16:9/16:10/17:10/5:4/21:9,
computed from the actual framebuffer dimensions, with no input from `vwidth`/`vheight` at all) — and
for any bucket other than 4:3/5:4 (i.e. every common modern widescreen ratio) takes this branch:

```cpp
if (myratio != 0 && myratio != 4)
{ // The target surface is either 16:9 or 16:10, so expand the
  // specified virtual size to avoid undesired stretching of the
  // image. Does not handle non-4:3 virtual sizes. I'll worry about
  // those if somebody expresses a desire to use them.
    x = (x - vwidth * 0.5) * Width * 960 / (vwidth * BaseRatioSizes[myratio][0]) + Width * 0.5;
    w = (right - vwidth * 0.5) * Width * 960 / (vwidth * BaseRatioSizes[myratio][0]) + Width * 0.5 - x;
}
```

This exact fence is Zandronum-only source (`v_draw.cpp:760-798`) — see "Engine-family divergence"
below for how the pinned UZDoom checkout computes the same effect differently; the two are no
longer the same code, despite an earlier pass through this doc having claimed otherwise.

Substituting a `HudMessage` x-coordinate built as `frac * vwidth` (the standard way to derive a pixel
position from a 0.0-1.0 screen fraction once `SetHudSize` is active — see `HudMessage`'s own doc):
`vwidth` cancels out of the formula entirely, leaving `x_real = (frac - 0.5) * Width * 960 /
BaseRatioSizes[myratio][0] + Width * 0.5`. **The real on-screen X position (and by extension, the
pillarbox inset amount) is completely independent of whatever `width` value was passed to
`SetHudSize`** — changing it has zero effect on horizontal placement on a non-4:3 screen. The Y axis
has no such special-case for these ratios (`else { y = y * Height / vheight; ... }`, a plain
proportional scale) and DOES respond normally to `SetHudSize`'s `height` argument — only X is
affected, and only when the real screen's aspect ratio isn't near 4:3 or 5:4. The same `vwidth`
cancellation happens in UZDoom's differently-shaped version of this formula too (see "Engine-family
divergence" below) — the width-independence conclusion holds on both engines even though the code
computing it no longer matches.

Concretely, at 16:10 (`BaseRatioSizes[2][0] = 1152`, `v_video.cpp:1770`): `x_real` at the
virtual-canvas edges (`frac=0`/`frac=1`) lands at `Width * (0.5 - 0.5*960/1152)` ≈ `0.0833 * Width`
from each true screen edge — an ~8.3% pillarbox margin on each side, symmetric, present at
16:9/16:10/17:10 alike (with per-ratio `BaseRatioSizes` constants), and **unavoidable via any
`SetHudSize` width choice** because the formula never actually uses that width for the real
position once it's cancelled out. This is Zandronum's fixed-bucket math; UZDoom reaches the same
~8.3%-at-16:10 number too (its `AspectBaseWidth` formula reproduces the same constants for the
standard buckets — see below), but 21:9-class ultrawide screens are where the two engines actually
part ways, so "present... alike" above stops holding once a real screen goes past 16:9. Zandronum's
own source comment frames the 4:3/5:4-only fill as deliberate, not a bug: `SetHudSize`'s
virtual-canvas mode is architecturally scoped to a 4:3-equivalent centered region on non-4:3 real
screens, and there is no `width`/`height` combination that makes it fill the real screen instead.

## Engine-family divergence: aspect-correction implementation on UZDoom (verified 2026-08-15)

On the pinned UZDoom checkout, `VirtualToRealCoords` (`common/2d/v_draw.cpp:1441-1487`) reaches the
same pillarboxed-canvas effect as the fence above through different code, not the same code. Where
Zandronum looks up a discrete `myratio` bucket (0-5, covering 4:3/16:9/16:10/17:10/5:4/21:9) in a
`BaseRatioSizes` table, UZDoom computes `myratio` as a continuous float via `ActiveRatio` and derives
the equivalent base-width value with a formula (`AspectBaseWidth`, `round(240 * aspect * 3)`) instead
of a table lookup, and branches on `myratio > 1.334f` rather than an explicit bucket-index check. For
the standard buckets the two approaches land on the same numbers — `AspectBaseWidth` for 16:10
evaluates to 1152, matching Zandronum's `BaseRatioSizes[2][0]` cited above — so at 4:3, 16:9, 16:10,
17:10, and 5:4 the resulting pillarbox math is equivalent between engines even though the
implementing code isn't.

Genuinely ultrawide real screens are where the two diverge in outcome, not just implementation.
Before computing `myratio`, UZDoom clamps it through an `Int` cvar, `vid_allowtrueultrawide`
(default `1`, `CVAR_ARCHIVE`): at its default, a real screen ratio wider than 16:9 is allowed through
up to 64:27 (~21:9) rather than being folded into one fixed "21:9" bucket the way Zandronum's table
does it, so the exact pillarbox width UZDoom computes for a genuinely ultrawide monitor tracks that
monitor's actual measured ratio instead of a single constant. Setting `vid_allowtrueultrawide` to `0`
instead clamps the ratio down to 16:9 before it reaches the formula, which is closer in spirit to
(though not verified identical to) Zandronum's fixed-bucket treatment of anything wider than 16:10.
Zandronum has no cvar or code path equivalent to `vid_allowtrueultrawide` at all — this is
UZDoom-specific behavior with no Zandronum counterpart to compare against. The `vwidth`-cancellation
property described above (the real X position, and therefore the pillarbox inset, never depends on
the `width` a script passes to `SetHudSize`) holds under this formula exactly as it does under
Zandronum's, since the cancellation only relies on `vwidth` appearing once in the numerator and once
in the denominator — that part of the derivation is unaffected by which value computes
`AspectBaseWidth(myratio)`/`BaseRatioSizes[myratio][0]` upstream of it.

## The glyph-size invariant, and the `width`/`height` you pass is genuinely free to rescale (verified 2026-08-12)

A caller that wants distance-based (or otherwise dynamic) text-size falloff might reasonably worry
that resizing the virtual canvas per-message shifts *where* things draw, not just how big they
render. It doesn't, and the invariant is exact, not approximate:

Once `hudwidth`/`hudheight` are nonzero, `DoDraw` always takes the `DTA_VirtualWidth,
HUDWidth`/`DTA_VirtualHeight, hudheight` tag path (`hudmessages.cpp:503-512`), which bottoms out in
`VirtualToRealCoords` (`v_draw.cpp:717`, formula at `v_draw.cpp:785`,`799` for the non-16:9/16:10
branch — see "The wiki's '4:3 area...' claim" above for the other branch): `real_px =
virtual_units * (RealScreenWidth / virtWidth)`. This holds for BOTH a coordinate's position AND a
glyph's own rendered width (the glyph's destination width is itself in virtual units, scaled by the
exact same `RealScreenWidth / virtWidth` factor). Consequently:

- **The *drawn fraction* of the canvas (`x / virtWidth`) is invariant under rescaling `virtWidth`** —
  scale the canvas by any positive factor `k` (`SetHudSize(virtWidth*k, virtHeight*k, ...)`) and an
  `x` scaled by the same `k` lands at the identical real screen position. Resizing the canvas moves
  nothing.
- **`quantum_real_px / glyph_real_px = 1 / glyph_texture_pixels`, independent of canvas size.**
  `quantum_real_px` (how many real pixels one virtual unit spans) = `RealScreenWidth / virtWidth`;
  `glyph_real_px` = `glyph_texture_pixels * quantum_real_px`; the `RealScreenWidth / virtWidth` factor
  cancels in the ratio. Concretely: growing the virtual canvas to make a glyph render smaller (a
  common way to fake distance falloff for a world-space HUD overlay) does NOT proportionally shrink
  the *positioning* quantum's real-pixel size the same way it shrinks the glyph — the position
  quantum's real-pixel size also shrinks by the same canvas-size factor (that's `quantum_real_px`
  itself scaling with `1/virtWidth`), so raising the canvas to shrink a glyph makes position error
  read as a *larger* fraction of glyph size, not a free win. Both facts follow from the same
  cancelling `RealScreenWidth / virtWidth` factor; a caller wanting less visible position jitter
  relative to glyph size needs a higher-resolution glyph texture (and a correspondingly larger
  canvas to keep it the same apparent size), not just a canvas resize.

## `fixed_t`'s ±32767 integer-part ceiling on HUD coordinates (verified 2026-08-12)

`x`/`y` arguments to [`HudMessage`](hudmessage.md) (and `hudwidth`/`hudheight` themselves) are
`fixed_t` — `SDWORD` (signed 32-bit) in 16.16 format (`basictypes.h:94`, `m_fixed.h`'s
`FRACBITS`/`FRACUNIT`). A 16.16 value's INTEGER part is therefore bounded to `INT32_MAX >> 16 =
32767` (and `INT32_MIN >> 16 = -32768`) before the value itself overflows int32 when re-encoded as
fixed-point (e.g. `some_int_coordinate << 16`). This is a hard ceiling on the usable range of any
HUD coordinate or virtual canvas dimension a script constructs via ordinary fixed-point arithmetic
(`FixedMul`/`FixedDiv`/plain `<<16`) before passing it to `SetHudSize`/`HudMessage` — a computed
coordinate whose integer part would exceed ~32767 silently wraps rather than erroring, the same
32-bit-int wraparound behavior as any other ACS fixed-point overflow (no dedicated bounds check in
either `PCD_SETHUDSIZE` or `PCD_ENDHUDMESSAGE`/`PCD_ENDHUDMESSAGEBOLD`). Relevant to any script
computing a virtual canvas size from a runtime value (e.g. scaled by depth/distance) rather than a
small compile-time constant.

## See also

[`HudMessage`](hudmessage.md)/[`HudMessageBold`](hudmessagebold.md) — the only functions whose
coordinate interpretation `SetHudSize` affects, via the shared `DHUDMessage` constructor described
above.
