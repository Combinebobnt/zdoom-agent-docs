# `st_scale` (cvar), and where the `ST_Y` status-bar top row comes from

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** written from the Zandronum source's `src/g_shared/shared_sbar.cpp` (the `st_scale`
`CUSTOM_CVAR` `:108-115` and `DBaseStatusBar::SetScaled` `:292-327`), `src/g_shared/sbar.h`
(`:341`, `:406-408`), `src/g_doom/doom_sbar.cpp` (`:47`), `src/g_shared/sbarinfo.cpp` (`:471`,
`:632-633`, `:818`, `:979`, `:1052-1059`, `:1556`, `:1575-1597`, `:1615`), `src/gametype.h`
(`:5-14`), `src/v_video.cpp` (`CheckRatio` `:1719-1753`, `BaseRatioSizes` `:1764-1773`) and
`src/v_draw.cpp` (`DCanvas::VirtualToRealCoords` `:758-799`); no wiki page covers this. The
`base`-less `SBARINFO` dispatch section was added 2026-08-26 after an in-engine measurement
contradicted a source reading of `CreateStatusBar` taken in isolation.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

`st_scale` is usually described as "stretch the status bar to the full screen width." Its more
consequential effect is that it decides the value of the global `ST_Y`, the first screen row
occupied by the status bar, which in turn drives the 3D view rectangle (see
[`../concepts/view-window-geometry.md`](../concepts/view-window-geometry.md)) and the vertical
extent of any status-bar-respecting HUD message canvas (see
[`../../acs/functions/sethudsize.md`](../../acs/functions/sethudsize.md)).

## The cvar

Declared `CUSTOM_CVAR (Bool, st_scale, true, CVAR_ARCHIVE)` (`shared_sbar.cpp:108`), so it defaults
to on. Its callback calls `StatusBar->SetScaled(self)` and sets `setsizeneeded`, which is what makes
a change to it recompute the view window as well as the bar.

The flag set matters for scripting: `CVAR_ARCHIVE` and nothing else. It is **not** `CVAR_USERINFO`,
so it is not replicated between server and client and it is not routed through the user-cvar path
that [the ACS CVar family](../../acs/families/cvar.md) documents. A `GetCVar("st_scale")` therefore
reads whichever machine's own config is running the script: only a `CLIENTSIDE` script sees the
actual viewer's setting, and a server-side read returns the server's own local copy, which says
nothing about any player.

## `DBaseStatusBar::SetScaled`, and the three `ST_Y` formulas

`SetScaled(bool scale, bool force)` (`shared_sbar.cpp:292-327`) decides scaling with:

```text
Scaled = (RelTop != 0 || force) && ((SCREENWIDTH != 320 || HorizontalResolution != 320) && scale)
```

where `scale` is the cvar's value. Two gates are easy to miss: a bar with `RelTop == 0` is never
scaled unless `force` is passed, and a bar that is 320 units wide on a literally 320-pixel-wide
screen is never scaled either (nothing to stretch).

`RelTop`, `HorizontalResolution` and `VirticalResolution` (spelled that way in the source) are the
status bar object's own fields (`sbar.h:406-408`), supplied by its constructor
(`sbar.h:341`: `DBaseStatusBar (int reltop, int hres=320, int vres=200)`). `RelTop` is the bar's
height in its own vertical resolution units. The formulas below are written in those terms rather
than in the stock bar's numbers, because a mod-supplied bar changes them (see the next section).

**Unscaled** (`shared_sbar.cpp:298-308`):

```text
ST_X   = (SCREENWIDTH - HorizontalResolution) / 2
::ST_Y = SCREENHEIGHT - RelTop
```

The bar keeps its literal pixel height, so the space above it grows with the screen.

**Scaled, and the real screen is not in the 5:4 aspect bucket** (`shared_sbar.cpp:312-317`):

```text
ST_X   = 0
::ST_Y = Scale(VirticalResolution - RelTop, SCREENHEIGHT, VirticalResolution)
```

That is, the bar occupies a constant *fraction* `RelTop / VirticalResolution` of screen height at
every resolution.

**Scaled, and the real screen is in the 5:4 bucket** (`shared_sbar.cpp:320-321`). `CheckRatio`
(`v_video.cpp:1719-1753`) returns a bucket index by nearest match over 4:3, 16:9, 16:10, 17:10, 5:4
and 21:9, with `4` meaning 5:4; the `vid_aspect` override feeds the same function, so a forced
aspect selects this branch too. The formula is:

```text
localTop = VirticalResolution - RelTop
::ST_Y   = Scale(localTop - VirticalResolution/2,
                 SCREENHEIGHT*3,
                 Scale(VirticalResolution, BaseRatioSizes[4][1], 200))
           + SCREENHEIGHT/2
           + (SCREENHEIGHT - SCREENHEIGHT * BaseRatioSizes[4][3] / 48) / 2
```

with `BaseRatioSizes[4] = { 960, 640, 6.5*FRACUNIT, 45 }` (`v_video.cpp:1764-1773`), so
`BaseRatioSizes[4][1]` is 640 and `BaseRatioSizes[4][3]` is 45. This is not an arbitrary special
case: it is algebraically the same transform (modulo the inner `Scale`'s integer truncation for a
`VirticalResolution` other than 200) that `VirtualToRealCoords` applies to the Y axis on the 5:4
bucket, plus that function's `vbottom` offset. See the last section.

**Added after 3.2.1: which screens land in the 5:4 bucket.** The nearest-match `CheckRatio`
described above came in with `10221d769`, and the 21:9 bucket with `41947975f`; neither is an
ancestor of the 3.2.1 release. A 3.2.1 client's `CheckRatio` uses tolerance tests instead
(16:9, 17:10 and 16:10 within fixed pixel tolerances, anything else 4:3). It returns 5:4 only
when `vid_tft` is on and `height * 5/4 == width` exactly, and `vid_aspect` is capped at 5, so
there is no 21:9 bucket. The three `ST_Y` formulas and `BaseRatioSizes[4]` are the same on both
versions. Only which resolutions select the 5:4 branch differs.

For the **stock Doom status bar** (`doom_sbar.cpp:47`: `DDoomStatusBar () : DBaseStatusBar (32)`,
taking the 320/200 constructor defaults) the three formulas evaluate to:

| State | `::ST_Y` |
|---|---|
| Unscaled | `SCREENHEIGHT - 32` |
| Scaled, not 5:4 | `168 * SCREENHEIGHT / 200`, i.e. 0.84 of screen height |
| Scaled, 5:4 | approximately 0.85 of screen height |

## A mod-supplied `SBARINFO` bar changes all three inputs

`DSBarInfo`'s constructor passes the parsed lump's own values straight through
(`sbarinfo.cpp:979`: `DBaseStatusBar(script->height, script->resW, script->resH)`), so every
`RelTop`/`HorizontalResolution`/`VirticalResolution` above becomes whatever the `SBARINFO` lump
declared, and the 32/320/200 numbers in the table stop applying.

`SBARINFO` *can* force-scaling, via `SetScaled(true, true)` at `sbarinfo.cpp:1059` and `:1556`,
which bypasses the `RelTop != 0` gate and the `st_scale` value alike — but this is **conditional,
not automatic**: `:1052` guards it on the currently-drawn hud block declaring `forcescaled`, and
`:1053-1054` diverts to setting `hud_scale` instead when that block also uses
`fullscreenoffsets`. A lump with no `forcescaled` anywhere never reaches it.

One edge worth knowing: `sbarinfo.cpp:1615` constructs a plain `DBaseStatusBar(0)` as a fallback,
giving `RelTop == 0`. With `RelTop` zero and no `force`, `Scaled` is false and the unscaled formula
puts `::ST_Y` at `SCREENHEIGHT`, i.e. no reserved status-bar area at all.

### Whether `DSBarInfo` is used at all: the `base`-less trap

The section above only matters if `CreateStatusBar` (`sbarinfo.cpp:1575-1597`) actually builds a
`DSBarInfo`, and its dispatch is easy to read backwards. It tests, in order:

```cpp
	if (SBarInfoScript[SCRIPT_CUSTOM] != NULL)
	{
		int cstype = SBarInfoScript[SCRIPT_CUSTOM]->GetGameType();

		// [BB] Skulltag doesn't use the SBARINFO version of the Doom status bar yet.
		if( ( cstype & GAME_DoomChex ) )
		{
			sbar = CreateDoomStatusBar ();
		}
		else
		//Did the user specify a "base"
		if(cstype == GAME_Strife)
		{
			sbar = CreateStrifeStatusBar();
		}
		else if(cstype == GAME_Any) //Use the default, empty or custom.
		{
			sbar = CreateCustomStatusBar(SCRIPT_CUSTOM);
		}
```

The `GAME_DoomChex` branch carries the comment *"[BB] Skulltag doesn't use the SBARINFO version of
the Doom status bar yet"*, and reading only this function suggests that a Doom-gametype `SBARINFO`
is ignored in favour of the stock bar. **That conclusion is wrong**, because `gameType` is not what
it looks like:

- `SBarInfo`'s parser initialises `gameType = gameinfo.gametype` (`sbarinfo.cpp:471`) — for Doom,
  `GAME_Doom`.
- **But the first `statusbar` block overwrites it** when the lump declared no `base`:
  `if(!baseSet) gameType = GAME_Any;` (`sbarinfo.cpp:632-633`).
- `GAME_Any` is **0** (`gametype.h:5`), so `cstype & GAME_DoomChex` is `0 & 17 == 0` and the Doom
  branch does not fire. Dispatch falls through to `cstype == GAME_Any` → `DSBarInfo`.

So for the common case — an `SBARINFO` lump with `statusbar` blocks and no `base` directive —
`DSBarInfo` *is* constructed, and `RelTop` becomes the lump's `height`. `height` defaults to **0**
(`sbarinfo.cpp:818`), so a lump that never mentions `height` yields `RelTop == 0` and therefore
`::ST_Y == SCREENHEIGHT`: no reserved status-bar rows, and a 3D view that stays full-height even at
`screenblocks 10`.

**Practical consequence.** Any code reconstructing `ST_Y` from the stock bar's `RelTop = 32` (ACS
cannot read `ST_Y` directly) is wrong by `32 * SCREENHEIGHT / 200` rows whenever such a lump is in
the load order — about 154 px at 960 high, i.e. a ~77 px error in anything derived from the view's
vertical centre. Verified by measurement, not only by reading: with such a mod loaded, an engine
build printing `ST_Y` and the view rect reports `statusbar_y == SCREENHEIGHT` and a full-height
view rect at `screenblocks 10`. Reading `:471` and `CreateStatusBar` alone gives the opposite
answer and looks airtight; `:632-633` is the line that decides it.

## The 5:4 bucket's vertical squeeze, and one unreachable branch

`DCanvas::VirtualToRealCoords` (`v_draw.cpp:758-799`) is where any virtual-canvas drawing (HUD
messages included) lands. Its Y handling has exactly two shapes:

- Every bucket except 5:4: a plain proportional scale, `y = y * Height / vheight`
  (`v_draw.cpp:796`).
- The 5:4 bucket: `y = (y - vheight*0.5) * Height * 600 / (vheight * BaseRatioSizes[4][1]) +
  Height * 0.5` (`v_draw.cpp:787`), i.e. a squeeze of `600/640 = 0.9375` applied about the screen's
  vertical centre. This is the same shape as the 5:4 `ST_Y` formula above, which is why the two
  agree on where the bar's top edge is.

The extra `vbottom`-gated offset immediately after the 5:4 line (`v_draw.cpp:789-792`) is
**unreachable from a HUD message**. `virtBottom` defaults to `false` (`v_draw.cpp:356`) and is set true only by the
`DTA_Bottom320x200` tag (`v_draw.cpp:478`), which the HUD-message draw path's tag list never passes
(`g_shared/hudmessages.cpp:503-512`). Worth recording because the `ST_Y` formula *does* include the
equivalent term, so the bar's own top row and a HUD-message coordinate are offset relative to each
other by that amount on a 5:4 screen.

After 3.2.1 the function also remaps the 21:9 bucket to index 2, the 16:10 one, on entry
(`v_draw.cpp:763-767`, added by `b43f7a490`; its comment says 16:9, the code picks 16:10). That
changes only the X axis, so the two Y shapes above hold on both versions.

## Engine note

UZDoom declares `st_scale` differently: an `Int` defaulting to `-1` rather than Zandronum's `Bool`
defaulting to `true`, and its status bar computes `ST_Y` as a member of a restructured base class
rather than through the global written here. Its scaling path was not traced for this entry, so
treat every formula above as Zandronum-verified only. `con_scaletext` has the same Bool-vs-Int
shape difference between the two engines, already written up at
[`con_scaletext`](con_scaletext.md).

## Related

- [`screenblocks`](screenblocks.md) - the cvar that consumes `ST_Y` to size the 3D view.
- [`../concepts/view-window-geometry.md`](../concepts/view-window-geometry.md) - the resulting view
  rectangle, and why shrinking it crops rather than squashes.
- [`SetHudSize`](../../acs/functions/sethudsize.md) - the ACS-visible consequence: a HUD message
  canvas that does not cover the status bar is scaled into `ST_Y` rows rather than `SCREENHEIGHT`.
