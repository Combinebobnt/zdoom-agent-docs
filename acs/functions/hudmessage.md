# `HudMessage`

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

**Tier:** A. **Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD —
see "Engine scope" in `../../shared/AUTHORING.md`).

**Provenance:** `HudMessage - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=HudMessage&oldid=48530`), verified against
the Zandronum source's `src/p_acs.cpp` (`PCD_OPTHUDMESSAGE`/`PCD_ENDHUDMESSAGE`/
`PCD_ENDHUDMESSAGEBOLD`, lines 10980-11144), the Zandronum source's `src/p_acs.h` (lines 367-380, the
`HUDMSG_*` bit layout), the Zandronum source's `src/g_shared/hudmessages.cpp` (`DHUDMessage`/
`DHUDMessageFadeOut`/`DHUDMessageTypeOnFadeOut`/`DHUDMessageFadeInOut` Tick/Draw), and
the zt-bcc source's `lib/zcommon.bcs` (lines 190-248, the `CR_*`/`HUDMSG_*` enums) on 2026-07-29.

## Syntax

```
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
- **`x`, `y`** (fixed) — screen-space position; semantics (sign meaning, box-centering ranges) are
  as the wiki describes and are unaffected by anything Zandronum-specific; not re-verified line by
  line here since this is core ZDoom rendering math untouched by the fork.
- **`holdTime`** (fixed, seconds) — for `HUDMSG_PLAIN` only, `0` means "stays forever, until the
  same id is reused": `HoldTics = holdTime * TICRATE` becomes `0`, and `DHUDMessage::Tick`'s
  expiry check is gated on `HoldTics != 0` (`hudmessages.cpp:322-330`), so a `0` `HoldTics` simply
  never satisfies the expiry condition. **This does not carry over to the other three types** — see
  "0 holdTime is not 'infinite' for FADEOUT/TYPEON/FADEINOUT" below.

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
