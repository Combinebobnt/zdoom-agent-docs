# `void SetHUDClipRect(int x, int y, int width, int height [, int wrapwidth [, bool aspectratio]])`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `SetHudClipRect - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=SetHudClipRect&oldid=44238`), verified against
the Zandronum source's `src/p_acs.cpp:6373-6379` (`ACSF_SetHUDClipRect`), `p_acs.h:1075-1076`
(per-script `ClipRectLeft`/`Top`/`Width`/`Height`/`WrapWidth` members), `p_acs.cpp:13120-13121`
(zeroed at script start) and `:3772-3777` (save-game serialization),
the Zandronum source's `src/g_shared/sbar.h:97-120` (`DHUDMessage::SetClipRect`/`SetWrapWidth`,
`ClipX/Y/Width/Height` documented in-line as "in HUD coords"), and
the Zandronum source's `src/g_shared/hudmessages.cpp:252-272` (`DHUDMessage::CalcClipCoords`) on
2026-07-29.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function — negative index `-51` in `zt-bcc/lib/zcommon.bcs:1679`
(`SetHudClipRect(int,int,int,int;int,bool):void`), `ACSF_SetHUDClipRect` in
the Zandronum source's `src/p_acs.cpp:6373-6379`.

## What it does

Sets a clipping rectangle that future `HudMessage`/`HudMessageBold` calls **from the same running
script** will be clipped to (or wrapped to, if `wrapwidth` is given). The engine stores this as
five plain `int` members (`ClipRectLeft`, `ClipRectTop`, `ClipRectWidth`, `ClipRectHeight`,
`WrapWidth`) directly on the executing `DLevelScript` instance — **not** as global renderer state
and not tied to a specific HUD message id. Every subsequent `EndHudMessage`/`EndHudMessageBold` in
that script copies the current values onto the new `DHUDMessage` via `SetClipRect`/`SetWrapWidth`
(`p_acs.cpp:11097-11100`) until changed again or the script terminates. A concurrently running
*different* script has its own independent set of these members (zeroed at script start,
`p_acs.cpp:13120-13121`) and is unaffected.

## Parameters

- `x`, `y`, `width`, `height` — the clip rectangle, in **HUD virtual coordinates** (whatever
  width/height was last passed to `SetHudSize` by *this script*; `p_acs.cpp:12506-12513` sets the
  same per-script `hudwidth`/`hudheight` members that `DHUDMessage::CalcClipCoords` later reads as
  `HUDWidth`/`hudheight` to convert to real screen pixels via `VirtualToRealCoordsInt`,
  `hudmessages.cpp:265-266`) — the same coordinate space `HudMessage`'s own `x`/`y` use, not raw
  screen pixels.
- `wrapwidth` — wraps message text to this many HUD-coordinate-space pixels, starting at `x`.
  `0` (default) means "use the normal wrap behavior" (`ResetText`, `hudmessages.cpp:284-293`, falls
  back to `HUDWidth` or the console's virtual width instead).
- `aspectratio` — **declared in the signature (`zcommon.bcs:1679` lists it as an optional `bool`)
  but never read by Zandronum's engine code.** `ACSF_SetHUDClipRect` only branches on
  `argCount > 0` through `argCount > 4` (`p_acs.cpp:6374-6378`); there is no `argCount > 5` check
  and `args[5]` is never touched. A 6-argument call compiles fine (the BCS signature accepts it)
  but the 6th argument is silently discarded — the clip rect is *always* computed with
  `handleaspect = true` regardless of what's passed, because `CalcClipCoords` hardcodes `true` as
  the last argument to `VirtualToRealCoordsInt` (`hudmessages.cpp:266`). Per-fork this happens to
  match the wiki's stated default (`true` = force 4:3 on 16:9/16:10 displays), so passing no 6th
  argument behaves identically to upstream ZDoom — but passing `false` to get real-aspect
  clipping **does nothing** in Zandronum, unlike what the wiki implies is possible. This is a
  ZDoom-wiki-vs-fork divergence (see `../../shared/AUTHORING.md`'s "Engine scope" caveat), not a doc bug.

## Resetting: all four of x/y/width/height must be zero, not just width/height

`CalcClipCoords` treats the rect specially only when **all four** values (`x`, `y`, `width`,
`height`) are `0`, in which case it clips to the full screen (`hudmessages.cpp:256-262`,
`if ((x | y | w | h) == 0)`) — matching the wiki's documented reset idiom,
`SetHUDClipRect(0, 0, 0, 0, 0)`. If *any* of the four is non-zero (e.g. `x`/`y` left over from a
previous call while `width`/`height` are `0`), the engine takes the *other* branch and computes a
real zero-area (or negative-area, if a negative width/height is passed) clip rectangle at that
position — which clips away the entire message, making it invisible, rather than disabling
clipping. To reliably reset, always pass all four as literal `0` (as the wiki's own example does),
not just the size.

## Engine-family divergence: `aspectratio` parameter is live on UZDoom

On UZDoom, the 6th argument is not discarded. `case ACSF_SetHUDClipRect:`
(`src/playsim/p_acs.cpp:5916-5923`) stores it into a per-script `HandleAspect` member — `HandleAspect
= argCount > 5 ? !!args[5] : true` — sitting alongside the same `ClipRectLeft`/`Top`/`Width`/`Height`/
`WrapWidth` members Zandronum also has, and zeroed/defaulted the same way at script start
(`HandleAspect = true` alongside the other members being zeroed, `p_acs.cpp:10490-10491`). When a
later `EndHudMessage`/`EndHudMessageBold` builds the `DHUDMessage`, this per-script value is copied
onto the message's own `HandleAspect` member via `SetClipRect(x, y, width, height, aspect)`
(`p_acs.cpp:8882`, `src/g_statusbar/sbar.h:119-126`), and `DHUDMessage::CalcClipCoords`
(`src/g_statusbar/hudmessages.cpp:267-281`) passes that stored member through to
`VirtualToRealCoordsInt` instead of hardcoding `true` the way Zandronum's equivalent does.

Practically: omitting the 6th argument (or any call written before this parameter existed) behaves
identically on both engines, since both default to aspect-corrected clipping. But explicitly passing
`false` as the 6th argument — which the wiki describes as opting into real-aspect (non 4:3-forced)
clipping — is a genuine no-op on Zandronum (as documented above) and a real, wiki-matching behavior
change on UZDoom. Everything else documented above (the coordinate space, the wrap-width default, and
the all-four-zero reset idiom) matches between the two engines.

## See also

- [`HudMessage`](hudmessage.md) — the `x`/`y`/`holdTime` positioning this clip rect interacts with,
  and the same "HUD virtual coordinates set via `SetHudSize`" coordinate space.
