# The 3D view window's screen rectangle (`screenblocks`, `viewwidth`/`viewheight`, `viewwindowx`/`viewwindowy`)

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** written from the Zandronum source's `src/r_utility.cpp` (`R_SetWindow`
`:410-465`, `R_ExecuteSetViewSize` `:473-485`, the `screenblocks` `CUSTOM_CVAR` `:496-504`),
`src/r_main.cpp` (`R_InitTextureMapping` `:212-218`, `R_SWRSetWindow` `:354-399`,
`R_SetupFreelook` `:584-601`) and `src/gl/scene/gl_scene.cpp` (`FGLRenderer::SetViewport`
`:190-216`, `FGLRenderer::SetProjection` `:263-290`, and the projection-argument setup at
`:1056-1078`); no wiki page covers this.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

`screenblocks` is normally described only as "how big the 3D view is." The exact rectangle it
produces is worth writing down, because two things follow from it that are easy to get wrong:
where the view's centre row actually sits on the physical screen, and whether shrinking the view
*crops* the world or *squashes* it. Both matter to anything that has to line an overlay up with
the rendered world.

For what the cvar itself is (default, clamp, per-value meaning, and the Zandronum-vs-UZDoom
default divergence), see [`../notes/screenblocks.md`](../notes/screenblocks.md). For where the
`ST_Y` value feeding the table below comes from, see [`../notes/st_scale.md`](../notes/st_scale.md).

## The rectangle, per `screenblocks` value

`R_SetWindow(windowSize, fullWidth, fullHeight, stHeight)` computes the view size;
`R_ExecuteSetViewSize` is the caller that supplies the real arguments, passing `setblocks`,
`SCREENWIDTH`, `SCREENHEIGHT` and the global `::ST_Y` (the first screen row occupied by the status
bar) respectively. So `stHeight` in the table below *is* `ST_Y`.

| `screenblocks` | `viewwidth` | `viewheight` | `freelookviewheight` |
|---|---|---|---|
| 11, 12 | `SCREENWIDTH` | `SCREENHEIGHT` | `SCREENHEIGHT` |
| 10 | `SCREENWIDTH` | `ST_Y` | `SCREENHEIGHT` |
| 3 to 9 | `((setblocks*SCREENWIDTH)/10) & ~15` | `((setblocks*ST_Y)/10) & ~7` | `((setblocks*SCREENHEIGHT)/10) & ~7` |

Placement onto the screen happens in the caller, not in `R_SetWindow`:

```text
viewwindowx = (screen->GetWidth() - viewwidth) >> 1
viewwindowy = (viewwidth == screen->GetWidth()) ? 0 : (ST_Y - viewheight) >> 1
```

(The source spells the placement lines with `screen->GetWidth()` rather than the `SCREENWIDTH`
macro used just above them in the `R_SetWindow` call. The two are the same on a client but
not on a dedicated server, where `SCREENWIDTH`/`SCREENHEIGHT` expand to `0` by design
(`v_video.h:435-436`), so the distinction is worth preserving when quoting these formulas.)

Consequences worth stating explicitly:

- **The view window is always horizontally centred**, at every `screenblocks` value. There is no
  setting that shifts it left or right, so anything computing a screen X position can ignore
  `screenblocks` entirely except for the width scale factor.
- **`viewwindowy` is zero whenever the view spans the full screen width**, which covers
  `screenblocks` 10, 11 and 12. Only the 3 to 9 range produces a non-zero top offset.
- The two masks differ (`& ~15` horizontally, `& ~7` vertically) and are applied *after* the
  division, so below 10 neither axis is guaranteed to be exactly `screenblocks/10` of the full
  dimension.

**One caveat on reading the source table literally:** `R_SetWindow`'s `< 10` branch computes from
the file-scope global `setblocks`, not from its own `windowSize` parameter (the `>= 11` and `== 10`
branches do use the parameter). The two are the same value at the `R_ExecuteSetViewSize` call site,
which is the only path that matters in normal play, but the table above is accurate for that call
site specifically rather than for an arbitrary direct call.

## Where the view's centre row lands

The renderer's own vertical centre is `centery = viewheight/2` (`r_utility.cpp:440`), carried into
rendering as `centeryfrac = (viewheight << 15) + dy` (`r_main.cpp:598`, i.e. `viewheight/2` in
16.16 fixed point). `dy` is the freelook pitch term, zero when there is no camera or the view
pitch is level, so the half-pixel discussed below is the *unpitched* centre.

The centre row in **screen** coordinates is therefore `viewwindowy + viewheight/2`, and it collapses
to a simple value:

- **`screenblocks` 3 to 9:** exactly `floor(ST_Y / 2)`. `viewheight` is a multiple of 8 (hence even)
  and `viewwindowy` is a whole row, so `((ST_Y - viewheight) >> 1) + viewheight/2` cancels down to
  `floor(ST_Y/2)` regardless of which value in that range is set.
- **`screenblocks` 10:** `viewwindowy` is 0 and `viewheight` is `ST_Y`, so the centre is `ST_Y/2`,
  keeping a genuine half-pixel when `ST_Y` is odd (`centeryfrac` is fixed-point, so the half is
  really carried, not truncated).
- **`screenblocks` 11 and 12:** `SCREENHEIGHT/2`, same half-pixel note.

So across the whole `screenblocks <= 10` range the unpitched horizon sits on the same screen row
(to within that half pixel), and it is *not* the middle of the screen: it is the middle of the area
above the status bar.

## Shrinking the view crops the world, it does not squash it

This is the fact most worth having verified rather than assumed. In the software renderer the
projection is driven entirely by the view **width**:

- `FocalLengthX = FixedDiv(centerxfrac, FocalTangent)` and
  `FocalLengthY = Scale(centerxfrac, yaspectmul, FocalTangent)` (`r_main.cpp:217-218`), where
  `centerxfrac` is `viewwidth/2` in fixed point (`r_main.cpp:372`).
- `yaspectmul` is derived from `virtwidth`/`virtheight`, which are seeded from the `fullWidth` and
  `fullHeight` arguments, that is the whole screen, never from `viewwidth` or `viewheight`
  (`r_main.cpp:375-376,397`).

Neither focal length sees `viewheight` at any point. A shorter view window therefore renders the
same world at the same scale and simply shows fewer rows of it: the vertical field of view narrows,
nothing is anamorphically compressed. Both axes scale together by `viewwidth / SCREENWIDTH`.

**OpenGL cross-check.** The GL renderer reaches the same outcome by a different route, and both
halves of it were checked:

- The projection matrix does not see the view rectangle at all. `FGLRenderer::SetProjection`
  (`gl/scene/gl_scene.cpp:263-290`) takes only `fov`, `ratio` and `fovratio` and feeds them to
  `gluPerspective`; its caller (`gl_scene.cpp:1056-1078`) sets `ratio` from a fixed per-bucket table
  indexed by `WidescreenRatio`, the *full screen's* aspect bucket, and `fovratio` to a constant
  `1.6` outside the 5:4 bucket. Nothing on that path reads `viewwidth` or `viewheight`, which is the
  GL equivalent of the `yaspectmul` argument above.
- `FGLRenderer::SetViewport` (`gl/scene/gl_scene.cpp:190-216`) then sets `glViewport` to a height of
  `SCREENHEIGHT` when `screenblocks >= 10` and `((screenblocks*SCREENHEIGHT)/10) & ~7` below that,
  at `x = viewwindowx` and a width of `viewwidth`, and uses `glScissor` to clip the drawn region
  down to `viewheight`. Clipping via scissor rather than shrinking the viewport is a crop.

Version note (Zandronum): the aspect buckets these paths index gained a 21:9 entry (bucket 6)
after 3.2.1. None of the commits below is an ancestor of the 3.2.1 version-bump commit.
`41947975f` added the bucket (`v_video.cpp`/`v_video.h`) and switched the 5:4 tests in
`r_utility.cpp` and `r_main.cpp` from `& 4` to `Is54Aspect()`, since `& 4` would also match
buckets 5 and 6. `ba9b39759` did the same for the GL `ratios` table, and `10221d769` made
`CheckRatio` pick the nearest bucket. A 3.2.1 client has only buckets 0 to 4, so a 21:9 screen
lands in some other bucket there. That changes which `ratio` and `yaspectmul` a given screen gets,
not the crop argument above: no bucket reads the view rectangle.

The two renderers are not bit-identical below `screenblocks` 10, though, and it is worth being
honest about the size of the gap rather than claiming they match:

- At `screenblocks` 10 and above they agree exactly (viewport height is the full `SCREENHEIGHT`,
  matching software's full-width-derived scale).
- Below 10, software's scale factor is `(((blocks*SCREENWIDTH)/10) & ~15) / SCREENWIDTH` while GL's
  vertical viewport factor is `(((blocks*SCREENHEIGHT)/10) & ~7) / SCREENHEIGHT`. Both come out to
  approximately `blocks/10`; they differ only by the two different bit masks, which is under 1% at
  typical resolutions (for example at 1920x1080 and `screenblocks` 9: 0.900 against 0.896).

One small trap for anyone reading `SetViewport`: it computes a local `width` alongside `height`
(`gl_scene.cpp:206`) and then never uses it. `glViewport`/`glScissor` both take `viewwidth`, so the
horizontal behaviour is genuinely shared with the software path.

## The cvar's own clamp

`screenblocks`'s `CUSTOM_CVAR` callback (`r_utility.cpp:496-504`) clamps writes to the inclusive
range 3 to 12 by assigning back to `self`. A read is therefore always in range, and code consuming
it does not need its own bounds check. Note the callback's structure: the clamping branches only
reassign `self` and do not call `R_SetViewSize` themselves, relying on the re-entrant callback from
that assignment to do it.
