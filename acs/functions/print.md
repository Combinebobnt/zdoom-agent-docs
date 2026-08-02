# `Print`

**Bucket:** compiler builtin — like [`HudMessage`](hudmessage.md)/[`StrParam`](strparam.md)/`Log`/
`PrintBold`/`HudMessageBold`, this is one of the five names in `zt-bcc/src/builtin.c`'s dedicated
"Format functions" block (`builtin.c:169`: `{ "print", "" }`), not a `zcommon.bcs` `special`-table
entry — it never appears there with a positive or negative index. The empty `g_funcs[]` string
means both "no return-type letter" (void) **and** "no post-format plain-argument tail at all" —
unlike [`HudMessage`](hudmessage.md)'s `";iiifff;fff"`, `Print` never takes anything after the
format-item list, and unlike `StrParam`'s `"s"` it has no return value either. Compiles to
`PCD_BEGINPRINT` (resets the "work" `FString` buffer), one `PCD_PRINT*` opcode per format item
appending to it, then `PCD_ENDPRINT` to flush — the exact same accumulation machinery
`Log`/`PrintBold`/`HudMessage` share, differing only in what the terminating opcode does with the
finished buffer (`p_acs.cpp:10730-10944`).

**Tier:** A. **Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — see
"Engine scope" in `../../shared/AUTHORING.md`).

**Provenance:** `Print - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=Print&oldid=51050`), verified against
the Zandronum source's `src/p_acs.cpp` (`PCD_BEGINPRINT`/`PCD_PRINTNAME`/`PCD_ENDPRINT`, lines
10730-10944), the Zandronum source's `src/p_mobj.cpp` (`AActor::CheckLocalView`, lines 1257-1271), and
the zt-bcc source's `lib/zcommon.bcs` (lines 1044-1048, the `PRINTNAME_*` enum) on 2026-07-29.

## Syntax

```
Print( <format-item-list> );
```

`<format-item-list>` is the same `<cast>:<expr>` grammar documented in
[`StrParam`](strparam.md#syntax): `a` (character array), `b` (binary), `c` (character), `d`/`i`
(decimal), `f` (fixed), `k` (bound key name(s) for a command), `l` (localized string), `n` (name —
see below), `s` (string), `x` (hex). Unlike the `StrParam`/`HudMessage` docs' note that their wiki
pages under-document the cast table, **`Print`'s own wiki page enumerates all 11 casts explicitly**
and every one matches `read_format_cast`'s switch (`zt-bcc/src/parse/expr.c:1003-1017`) — no
fork/wiki divergence in the cast table itself.

## `n:` name lookup — real fork divergence from the wiki

The wiki lists five `PRINTNAME_*` values: `PRINTNAME_LEVELNAME`(-1), `PRINTNAME_LEVEL`(-2),
`PRINTNAME_SKILL`(-3), `PRINTNAME_NEXTLEVEL`(-4), `PRINTNAME_NEXTSECRET`(-5). **This fork's enum
only defines the first three** (`p_acs.cpp:9066-9071`, mirrored in `zt-bcc/lib/zcommon.bcs:1044-1048`
— both stop at `PRINTNAME_SKILL = -3`). `PCD_PRINTNAME`'s switch (`p_acs.cpp:10797-10812`) has no
`case` for `-4`/`-5` either — any negative value other than -1/-2/-3 (including the wiki's -4/-5,
which don't even have BCS constants to spell them) falls into `default: work += ' ';`, silently
appending a single space instead of the next map's name. If you need the next map/secret-map lump
name in this fork, resolve it another way (e.g. reading the map-rotation functions) rather than
`n:-4`/`n:-5`.

For non-negative values, `n:` behavior matches the wiki with two undocumented edge cases visible in
the same switch:
- `n:0` (or any value whose absolute value exceeds `MAXPLAYERS`) prints the **activator's** name:
  `activator->player`'s `userinfo` name if the activator is a player, else `activator->GetTag()` (a
  tag name) if there's a non-player activator, else a **literal single space** if there is no
  activator at all (e.g. an `OPEN` script) — the wiki only documents the first two of these three
  outcomes.
- `n:<player>` (1-based) for an in-game player prints that player's name as documented, but for an
  **empty/out-of-range player slot** it prints the literal text `"Player <n>"` instead of erroring
  or printing nothing — not mentioned on the wiki at all.

## Activator/display resolution (not covered by the ZDoom-wiki page at all)

The wiki correctly states "`Print` will only display for the activator" and "if activated by
something that is not a player at all, the message will simply not be displayed anywhere," but
doesn't explain the mechanism, and glosses over a genuine third case. Verified in
`p_acs.cpp:10934-10952`:

- **Missile substitution.** Same as `HudMessage`/`Log`: if the activator is a projectile
  (`MF_MISSILE`) with no player and a non-null `target`, the effective target (`screen`) becomes
  the actor that fired it.
- **Non-player activator that exists (e.g. a monster, or a targetless missile) → dropped
  everywhere.** `screen` is non-null but `screen->player == NULL`. Locally, the display check
  `screen->CheckLocalView(consoleplayer)` requires `players[consoleplayer].mo == screen` (or that
  player's `camera == screen`, e.g. a spectator/chase-cam currently viewing that exact actor) —
  false for an ordinary monster, so nothing draws locally. On a server, the forwarding check only
  broadcasts for `PrintBold`/no-activator and only unicasts when `screen->player` is set
  (`p_acs.cpp:10943-10946`) — neither applies, so no client is told either. This matches the wiki's
  "not displayed anywhere," but only for *this specific* case.
- **No activator at all (`activator == NULL`, e.g. an `OPEN` script) → broadcasts to everyone,
  exactly like `PrintBold`.** `screen` ends up `NULL` (the missile-substitution check requires
  `screen != NULL` first, so it's skipped). The local-display condition is
  `pcd == PCD_ENDPRINTBOLD || screen == NULL || screen->CheckLocalView(...)` — `screen == NULL`
  satisfies this unconditionally, so the calling machine always draws it locally regardless of
  `consoleplayer`. The server-forwarding condition is `(pcd == PCD_ENDPRINTBOLD) || (screen ==
  NULL)` — also true, so `SERVERCOMMANDS_PrintMid` is sent with no target restriction, i.e.
  broadcast to every client. **This is the real, undocumented divergence**: the wiki's blanket "not
  a player → not displayed anywhere" is only true when there *is* a non-player activator object;
  a script with **no activator whatsoever** is treated identically to `PrintBold` (shown to every
  player), the opposite of "not displayed anywhere."
- **Player activator → local-only for that player, as documented.** `screen->player` set:
  `CheckLocalView` is true only on the machine where `players[consoleplayer].mo == screen`; the
  server unicasts (`SVCF_ONLYTHISCLIENT`) to that one player's client otherwise.

## Why the wiki says not to use `Print` as a debug tool

Confirmed structurally: `PCD_ENDLOG` (`Log`'s terminator) unconditionally calls `Printf` to the
console regardless of activator, while `PCD_ENDPRINT` is gated behind the activator/`CheckLocalView`
logic above — a `Print` call from a non-player-activated context (or from a remote player's script)
can silently produce no visible output at all on the machine/console the developer is watching,
exactly the "looks like the script does not run" trap the wiki describes; `Log`'s console `Printf`
has no such gate.

## Escape sequences and `\c` colors

The octal/hex/`\n`/`\c`-color escape handling described by the wiki is applied to the finished
`FString` by shared engine text-rendering code (`cmdlib.cpp`'s `strbin`-style unescaping and the
font/console color-code renderer), the same machinery every other printed/logged/HUD string goes
through — not logic specific to `Print`'s own opcodes, and not re-traced line-by-line here (same
treatment as `HudMessage`'s `x`/`y` params: core ZDoom text rendering untouched by this fork).

## See also

[`StrParam`](strparam.md) for the full format-item cast table. [`HudMessage`](hudmessage.md) for the
sibling format-function whose activator-substitution logic (missile → firer) is identical.
`Log`/`PrintBold`/`HudMessageBold` (not documented in this tree yet) share the same
`PCD_BEGINPRINT`/format-item/`PCD_END*` opcode family — `PrintBold` in particular is directly
referenced above since two of `Print`'s own display-gating branches key off `pcd ==
PCD_ENDPRINTBOLD`.
