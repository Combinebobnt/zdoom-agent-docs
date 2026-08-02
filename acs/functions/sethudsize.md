# `SetHudSize`

**Bucket:** compiler builtin — `zt-bcc/src/builtin.c:117`: `{ "sethudsize", ";iib" }` (void return,
params `int, int, bool`), compiles to `PCD_SETHUDSIZE` (`zt-bcc/src/semantic/asm.c:365`,
`zt-bcc/src/codegen/pcode.c:280`, taking no operand bytes itself — all three arguments are pushed
on the ACS stack like a normal builtin call). Not a `zcommon.bcs` `special`-table entry (no
positive/negative index) and not one of the format-function builtins like `HudMessage`/`Print` —
plain fixed-arity call.

**Tier:** A. **Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — see
"Engine scope" in `../../shared/AUTHORING.md`).

**Provenance:** `SetHudSize - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=SetHudSize&oldid=35982`), verified against
the Zandronum source's `src/p_acs.cpp` (`PCD_SETHUDSIZE` case, line 12506; `DLevelScript` constructor,
line 13120; savegame serialization, line 3769), the Zandronum source's `src/p_acs.h` (line 1074,
`hudwidth`/`hudheight` field declarations), the Zandronum source's `src/g_shared/hudmessages.cpp`
(`DHUDMessage` constructor lines 78-156, `DHUDMessage::Draw` lines 400-460), and
the Zandronum source's `src/sv_commands.cpp` (`SERVERCOMMANDS_PrintACSHUDMessage`, lines 2416-2437) on
2026-07-29.

## Syntax

```
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

## Not independently re-verified here

The wiki's claim that `SetHudSize` "only applies to the 4:3 area of the screen in the center" (and
does not itself do any aspect-ratio correction) is core ZDoom screen-scaling math
(`DTA_VirtualWidth`/`DTA_VirtualHeight` handling in the renderer) that this pass didn't trace beyond
what's shown above — treated the same as `HudMessage`'s own doc treats `x`/`y` positioning math:
plausible and unchanged by the fork, but not line-by-line confirmed.

## See also

[`HudMessage`](hudmessage.md)/[`HudMessageBold`](hudmessagebold.md) — the only functions whose
coordinate interpretation `SetHudSize` affects, via the shared `DHUDMessage` constructor described
above.
