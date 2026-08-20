# `HudMessage`

**Tier:** A.
**Applies to:** N/A — zt-bcc-declared, neither engine implements it
**Verified against:** none
**Provenance:** `HudMessage - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=HudMessage&oldid=48530`), verified against
the Zandronum source's `src/p_acs.cpp` (`PCD_OPTHUDMESSAGE`/`PCD_ENDHUDMESSAGE`/
`PCD_ENDHUDMESSAGEBOLD`, lines 10980-11144), the Zandronum source's `src/p_acs.h` (lines 367-380, the
`HUDMSG_*` bit layout), the Zandronum source's `src/g_shared/hudmessages.cpp` (`DHUDMessage`/
`DHUDMessageFadeOut`/`DHUDMessageTypeOnFadeOut`/`DHUDMessageFadeInOut` Tick/Draw), and
the zt-bcc source's `lib/zcommon.bcs` (lines 190-248, the `CR_*`/`HUDMSG_*` enums) on 2026-07-29.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin — like [`StrParam`](strparam.md)/`Print`/`Log`/`PrintBold`/
`HudMessageBold`, this is one of the five names in `zt-bcc/src/builtin.c`'s dedicated "Format
functions" block (`builtin.c:171`: `{ "hudmessage", ";iiifff;fff" }`), not a `zcommon.bcs`
`special`-table entry. It never appears with a positive or negative index there. The `g_funcs[]`
format string decodes as: a leading `;` (format-item list comes first, same
`peek_format_cast`/`read_format_item_list` grammar as `Print`/`Log`/`StrParam` —
`zt-bcc/src/parse/expr.c:901-931,949-1035`), then `iii` (three required plain ints: `type`, `id`,
`color`), then `fff` (three required plain fixed values: `x`, `y`, `holdTime`), then another `;`
starting an **optional** tail of up to three more plain fixed values (`fff`) whose meaning depends
on `type` (fade time / type+fade time / in+out time, then alpha) — see "Optional tail" below.

## Syntax

```text
HudMessage( <format-item-list>; type, id, color, x, y, holdTime [, extra1] [, extra2] [, alpha] );
```

`<format-item-list>` is exactly the format-item grammar documented in [`StrParam`](strparam.md#syntax)
(`s:`, `d:`, `c:`, `f:`, `x:`, `b:`, `k:`, `l:`, `n:`, `i:`, `a:`) — the text argument is built the
same way `Print`/`Log` build theirs, then handed to `HudMessage` instead of printed/logged
directly. `HudMessageBold` (undocumented here, but confirmed identical at the opcode level except
it always renders — see "Activator resolution" below) shares this same signature.

## Parameters

- **`type`** — one of the four base message-type enum values (`HUDMSG_PLAIN`=0, `HUDMSG_FADEOUT`=1,
  `HUDMSG_TYPEON`=2, `HUDMSG_FADEINOUT`=3, `zcommon.bcs:223-228`), OR'd with any of the flag groups
  below. The engine reads the base type as `type & 0xFF` (`p_acs.cpp:11023`) and switches on it —
  values 0-3 are the only ones implemented; anything else in the low byte silently falls into the
  `default:` ("normal"/plain) branch rather than erroring.
- **`id`** — HUD message slot id (`int`, full 32-bit range per the wiki). `0` means "anonymous" —
  never replaces or is replaced by anything. A non-zero id replaces any currently-displayed message
  with the same id (`StatusBar->AttachMessage(msg, id ? 0xff000000|id : 0, ...)`,
  `p_acs.cpp:11115-11116` — the engine ORs a `0xff000000` tag onto the caller's id internally to
  namespace ACS-created messages against other engine-internal HUD messages; this is transparent to
  the script, the script's own `id` value is unaffected).
- **`color`** — a `CR_*` enum value (`zcommon.bcs:190-220`) by default, clamped by the engine via
  `CLAMPCOLOR` (`p_acs.cpp:189`: any value `>= NUM_TEXT_COLORS` collapses to `CR_UNTRANSLATED`
  rather than erroring or reading out of bounds). If `type` has `HUDMSG_COLORSTRING` OR'd in,
  `color` is instead read as a **string** (a color name, including a custom one from a `TEXTCOLO`
  lump) via `V_FindFontColor` (`p_acs.cpp:11014-11021`) — matches the wiki's documented
  `HUDMSG_COLORSTRING` usage.
- **`x`, `y`** (fixed) — screen-space position, interpreted one of two structurally different ways
  depending on whether [`SetHudSize`](sethudsize.md) has been called with a nonzero width/height on
  this script instance (see that page's "Reset behavior" and "What drawing path each state actually
  takes" sections for the full mode split). Verified independently this pass (not just "as the wiki
  describes") since a caller converting between the two modes needs the actual formula, not just the
  documented ranges:
  - **`SetHudSize` not in effect (`hudwidth`/`hudheight` == 0, the default):** the wiki's
    "positions center of box" wording for the `[0.0, 1.0]` range is **misleading** — verified
    against `DHUDMessage::Draw` (Zandronum `hudmessages.cpp:385-402`; UZDoom's equivalent is
    structurally identical) that the real formula is `x = (screen_width - Width) * Left` (`Width`
    being the rendered text box's own pixel width) — a **lerp between flush-left (`Left=0`) and
    flush-right (`Left=1`)**, exactly centered only at `Left=0.5`. A caller assuming every value in
    `[0,1]` means "centered at that fraction of the screen" will be wrong by
    `Width * (Left - 0.5)` pixels at any other value — e.g. `Left=0.05` lands close to the left
    edge, not "centered 5% across the screen." Same shape for `y`/`Top` against `screen_height`.
  - **`SetHudSize` in effect (nonzero `hudwidth`/`hudheight`):** `x`/`y` become literal pixel
    coordinates in that virtual canvas, with the **fractional digit** (after `value * 10`, rounded)
    reinterpreted as an alignment-selector bitfield rather than a sub-pixel offset — verified against
    `DHUDMessage`'s constructor and `Draw` (Zandronum `hudmessages.cpp:108-139,405-432`; UZDoom
    structurally identical): bits 0-1 (`digit & 3`) choose whether the given pixel is the box's
    center (`0`), left/top edge (`1` or `3`, the unhandled default case), or right/bottom edge (`2`);
    bit 2 (`digit & 4`, **X only** — no Y equivalent) additionally self-centers each line of text
    within the box, and can combine with any anchor digit (e.g. digit `4` = center-anchor +
    self-centered text). Because the digit *is* the selector, the integer pixel part must be exact —
    a caller computing `pixel = fraction * canvasWidth` without rounding will, on many inputs, encode
    a *different* alignment than intended (e.g. `0.22 * 480 = 105.6` decodes to digit `6` = bottom
    edge, not the presumably-intended digit `0`/`1`).
- **`holdTime`** (fixed, seconds) — for `HUDMSG_PLAIN` only, `0` means "stays forever, until the
  same id is reused": `HoldTics = holdTime * TICRATE` becomes `0`, and `DHUDMessage::Tick`'s
  expiry check is gated on `HoldTics != 0` (`hudmessages.cpp:322-330`), so a `0` `HoldTics` simply
  never satisfies the expiry condition. **This does not carry over to the other three types** — see
  "0 holdTime is not 'infinite' for FADEOUT/TYPEON/FADEINOUT" below.

## The position quantum when `SetHudSize` is active, and two undocumented edge cases in the digit decode (verified 2026-08-12)

Building on the `x`/`y` bullet above: once `hudwidth`/`hudheight` are nonzero, `x = (int)intpart`
(`DrawSetup`, `hudmessages.cpp:408-409`,`422-423` for `x`/`y` respectively) — **there is no
sub-virtual-unit positioning at all** in this mode. A caller computing a fractional pixel position
(e.g. from a perspective-divide calculation) gets it silently truncated to the nearest whole virtual
unit before the alignment-digit decode even runs; **one virtual unit is the smallest position
increment this drawing mode can express**, and the resulting on-screen distance per unit is exactly
[`SetHudSize`'s glyph-size invariant](sethudsize.md#the-glyph-size-invariant-and-the-widthheight-you-pass-is-genuinely-free-to-rescale-verified-2026-08-12)'s
`quantum_real_px = RealScreenWidth / virtWidth`.

Two edge cases in the digit-decode formula itself (`fracpart = (int)(fabsf(modff(x, &intpart)) *
10.f + 0.5f)`, `hudmessages.cpp:118-119` for the encode side computing `Left`/`Top` from the raw
`x`/`y` passed to the constructor; `hudmessages.cpp:408-409`,`422-423` for the decode side
reconstructing `fracpart` from `Left`/`Top` at draw time) not covered by the bullet above:

- **The digit-10 boundary: `frac >= 0.95` decodes to the right/bottom anchor at the *lower*
  integer, not a carry to the next integer's digit 0.** `frac * 10 + 0.5`, truncated, can reach
  `10` (not just `0`-`9`) whenever `frac >= 0.95`. `10 & 3 == 2` (right/bottom edge) and `10 & 4 ==
  0` (no self-centered text) — i.e. `fracpart == 10` behaves identically to `fracpart == 2`, applied
  to the UNCHANGED (not incremented) integer part. The bullet above implies digits `0`-`7` are the
  only reachable values (`fracpart & 3` combined with `fracpart & 4`); `10` is a real, reachable
  ninth encoded state with no distinct digit of its own. Concretely: `x = 5.94` and `x = 5.95` decode
  to visibly different behavior (`fracpart` `9` → left/top edge + self-centered text vs. `fracpart`
  `10` → right/bottom edge, not self-centered) — a discontinuity at a boundary a caller would
  reasonably expect to be smooth or at worst carry to `x = 6.0`'s digit `0`.
- **Anchor-to-edge centring uses INTEGER division, adding up to an extra half-pixel of bias.**
  `DrawSetup`'s digit-`0`/`2` cases (`hudmessages.cpp:412-413`, `426-427` for `x`/`y`) do `x -=
  Width / 2;` / `x -= Width;` — `Width` is an `int` (already-rescaled real/virtual pixel width), so
  `Width / 2` on an odd `Width` truncates rather than rounds, landing the "centered" anchor up to
  half a pixel off from true center. Digit `4`'s separate self-centered-text adjustment
  (`hudmessages.cpp:436-438`, `x += Width * xscale / 2;`, and per-line at `:457`, `Lines[i].Width *
  xscale / 2`) has the same integer-division shape. None of this is specific to any one
  caller's math — it's baseline behavior any script drawing centered/self-centered `SetHudSize`
  text inherits, on top of whatever precision loss the caller's own position computation
  introduces upstream.

## Optional tail (`extra1`, `extra2`, `alpha`)

The trailing `fff` in the `g_funcs[]` signature is handled by `PCD_OPTHUDMESSAGE` recording a stack
mark (`optstart`) before however many of the optional args the caller actually passed
(`p_acs.cpp:10980-10989`), then `PCD_ENDHUDMESSAGE`/`PCD_ENDHUDMESSAGEBOLD` indexing relative to
that mark per type (`p_acs.cpp:11023-11092`):

| `type & 0xFF` | Meaning of trailing args, in order | Default if omitted |
|---|---|---|
| `HUDMSG_PLAIN` (0) | `alpha` | `alpha` = `FRACUNIT` (1.0) |
| `HUDMSG_FADEOUT` (1) | `fadeTime`, `alpha` | `fadeTime` = 0.5s, `alpha` = 1.0 |
| `HUDMSG_TYPEON` (2) | `typeTime`, `fadeTime`, `alpha` | `typeTime` = 0.05s, `fadeTime` = 0.5s, `alpha` = 1.0 |
| `HUDMSG_FADEINOUT` (3) | `inTime`, `outTime`, `alpha` | `inTime` = 0.5s, `outTime` = 0.5s, `alpha` = 1.0 |

This matches the wiki's per-type parameter lists and default note ("Alpha ... defaulting to 1.0 if
omitted"). As the wiki also notes, `alpha` only actually applies if `HUDMSG_ALPHA` is OR'd into
`type` — `SetAlpha(alpha)` is only called when `type & HUDMSG_ALPHA` (`p_acs.cpp:11107-11110`);
otherwise the parsed `alpha` value is computed but discarded, silently, not an error.

### `0` `holdTime` is not "infinite" for `HUDMSG_FADEOUT`/`TYPEON`/`FADEINOUT`

Verified in `DHUDMessageFadeOut::Tick` (`hudmessages.cpp:553-566`, inherited by the type-on and
fade-in-out subclasses): unlike plain `DHUDMessage::Tick`, this override has **no** `HoldTics != 0`
guard — it unconditionally checks `HoldTics <= Tics` to advance out of the "hold" state. With
`holdTime = 0` (`HoldTics = 0`), that condition is already true on the very first tick, so the
message immediately begins fading out (skipping straight past any hold) instead of holding forever.
The wiki's "you cannot specify an infinite (0) HoldTime when using any of these message types" is
correct, but it undersells what actually happens: it isn't rejected or clamped, it just silently
means "hold time zero," which for these types reads as "no hold, fade immediately."

### Out-of-range `alpha` is silently clamped, never an error

An `alpha` outside `[0.0, 1.0]` is not rejected and produces no diagnostic — it is clamped in two
separate places, and only the second one enforces the lower bound:

- The `DTA_Alpha` render-tag handler clamps the **upper** bound only:
  `parms->alpha = MIN<fixed_t>(FRACUNIT, va_arg(tags, fixed_t))` (`v_draw.cpp:541`). A value above
  `1.0` is capped here; a negative value passes through unchanged.
- The lower bound is enforced later, in the software renderer's `R_SetPatchStyle`, in the general
  alpha path: `alpha = clamp<fixed_t>(alpha, 0, FRACUNIT)` (`r_draw.cpp:2378-2381`). This is the
  `else` branch of a three-way check — `style.BlendOp == STYLEOP_Shadow` (`r_draw.cpp:2363`) forces
  `alpha = FRACUNIT*3/10`, `STYLEF_TransSoulsAlpha` (2370) forces the `transsouls` value, and
  `STYLEF_Alpha1` (2374) forces `FRACUNIT` outright — each overriding `alpha` instead of clamping
  it. Ordinary HUD text takes none of those style flags, so it falls into the `else` and gets the
  plain `[0, FRACUNIT]` clamp.

Practical upshot: `alpha = 1.2` renders byte-identical to `alpha = 1.0` — there is no visual tell
that a value was out of range, so a clamp expression accidentally written with `max` where `min`
was intended (or vice versa) can produce "always fully opaque" with no error and no obviously wrong
rendering to notice. Verified on the **software renderer** path only (`R_SetPatchStyle` is in
`r_draw.cpp`); the OpenGL renderer's equivalent path was not traced.

[`FadeTo`](fadeto.md)'s `amount` parameter documents the same silently-clamped-to-`[0, FRACUNIT]`
convention for full-screen alpha fades — this is evidently a general engine convention for
fixed-point alpha parameters, not something specific to `HudMessage`.

## Flags (OR'd into `type`)

All bit values below are from `p_acs.h:367-380` / `zcommon.bcs:230-248`; they line up with the
wiki's flag list exactly (no divergence found):

- `HUDMSG_LOG` (`0x8000'0000`) — in addition to the on-screen message, echoes the raw text (no
  format codes stripped) to the console and, if `-log`ging, to the log file, bracketed by an
  orange progress-bar-style separator line (`p_acs.cpp:11118-11139`). The console text color
  applies **only** if `color` (post-`CLAMPCOLOR`) falls in `[CR_BRICK, CR_YELLOW]`
  (`p_acs.cpp:11126`); every color enum value defined *after* `CR_YELLOW` in `zcommon.bcs`
  (`CR_BLACK`, `CR_LIGHTBLUE`, `CR_CREAM`, `CR_OLIVE`, `CR_DARKGREEN`, `CR_DARKRED`,
  `CR_DARKBROWN`, `CR_PURPLE`, `CR_DARKGRAY`/`CR_DARKGREY`, `CR_CYAN`, `CR_ICE`, `CR_FIRE`,
  `CR_SAPPHIRE`, `CR_TEAL`) — plus `CR_UNTRANSLATED` — falls outside that range and renders in the
  console's default color instead of the requested one. This is a real, silent console-only
  quirk the wiki doesn't mention; it has no effect on the on-screen HUD rendering, which uses the
  full color unclamped.
- `HUDMSG_COLORSTRING` (`0x4000'0000`) — see `color` above.
- `HUDMSG_ADDBLEND` (`0x2000'0000`) — `msg->SetRenderStyle(STYLE_Add)`.
- `HUDMSG_ALPHA` (`0x1000'0000`) — gates whether the parsed `alpha` tail value is applied at all
  (see above).
- `HUDMSG_NOWRAP` (`0x0800'0000`) — `msg->SetNoWrap(true)`.
- Layer (not a flag — an exclusive 2-bit field at `HUDMSG_LAYER_MASK` = `0x0000F000`,
  `HUDMSG_LAYER_SHIFT` = 12): `HUDMSG_LAYER_OVERHUD` (`0x0`, default), `HUDMSG_LAYER_UNDERHUD`
  (`0x1000`), `HUDMSG_LAYER_OVERMAP` (`0x2000`) — confirmed exclusive-field, not flag, usage: the
  wiki's own note ("these are not flags, thus can't be combined with each other") matches
  `StatusBar->AttachMessage`'s single masked-and-shifted read (`p_acs.cpp:11115-11116`).
- Visibility (an exclusive-ish bitmask field at `HUDMSG_VISIBILITY_MASK` = `0x00070000`,
  `HUDMSG_VISIBILITY_SHIFT` = 16): `HUDMSG_NOTWITH3DVIEW` (`0x1'0000`), `HUDMSG_NOTWITHFULLMAP`
  (`0x2'0000`), `HUDMSG_NOTWITHOVERLAYMAP` (`0x4'0000`). `DHUDMessage::Draw` skips drawing entirely
  when `VisibilityFlags & visibility` is nonzero for the view currently being rendered
  (`hudmessages.cpp:348-352`) — confirms the wiki's "does NOT appear when ... is active" wording
  (this is a suppression mask per view, not a positive "only show in" mask).

## Activator resolution and Zandronum netcode caveats (not covered by the ZDoom-wiki page at all)

The ZDoom wiki page describes purely single-player-oriented behavior; it says nothing about who
the message target actually is or how it reaches other machines. Verified in
`p_acs.cpp:10990-11141`:

- **Activator substitution.** If the activator is a projectile (`MF_MISSILE`) with no player and a
  non-null `target`, the message's real target becomes the missile's `target` (the actor that fired
  it), not the missile itself (`p_acs.cpp:10991-10998`) — same substitution `Print`/`Log` do.
- **Local display gating.** For plain `HudMessage` (not `HudMessageBold`), the message is only
  actually built/attached locally when `screen == NULL` (no specific target — e.g. an
  `activator`-less script), or the target *is* the local console player's body
  (`players[consoleplayer].mo == screen`), or the local machine is a listen/dedicated server
  (`NETWORK_GetState() == NETSTATE_SERVER`) (`p_acs.cpp:10999-11000`). `HudMessageBold` always
  passes this check (broadcasts to everyone, matching `PrintBold` semantics).
- **Server → client forwarding.** When running as a server, the message is never drawn locally by
  `DHUDMessage`/`StatusBar->AttachMessage` at all (`if (NETWORK_GetState() != NETSTATE_SERVER)`
  gates that whole block, `p_acs.cpp:11095`); instead the server sends
  `SERVERCOMMANDS_PrintACSHUDMessage` — broadcast to all clients if `HudMessageBold` or there's no
  specific target, or unicast (`SVCF_ONLYTHISCLIENT`) to the one client owning the target player
  otherwise (`p_acs.cpp:11029-11090`, one call site per message-type case). A script author running
  the mod purely single-player will never observe this path; it only matters once the mod is played
  as a server with remote clients, at which point the *client's own* copy of the ACS bytecode is
  not what renders the message — the server tells the client what to draw.

## Bucket note for `HudMessageBold`, `Print`, `Log`, `PrintBold`

All five share `builtin.c`'s "Format functions" table and the `peek_format_cast`/
`read_format_item_list` grammar; `HudMessage`/`HudMessageBold` additionally share essentially all
of `p_acs.cpp:10980-11144` (`PCD_ENDHUDMESSAGE` vs `PCD_ENDHUDMESSAGEBOLD` differ only in the
activator-gating check described above). All four siblings are now documented — see the See Also
list below.

## See also

[`StrParam`](strparam.md) for the full format-item cast table shared by `HudMessage`.
[`Print`](print.md)/[`Log`](log.md)/[`PrintBold`](printbold.md)/
[`HudMessageBold`](hudmessagebold.md) share the same grammar and much of the same opcode path —
see the bucket note above. [Client-side scripting](../concepts/clientside-scripting.md#relaying-a-server-side-log-to-one-or-all-clients-via-a-clientside-relay-script)
documents a `NamedSendNetworkString`-based relay pattern for getting a `Log()`-equivalent message
to a specific (or every) client, for cases where `HudMessage`'s own built-in forwarding isn't the
right shape.
