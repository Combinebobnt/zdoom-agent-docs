# `PrintBold`

**Bucket:** compiler builtin — one of the five names in `zt-bcc/src/builtin.c`'s dedicated
"Format functions" block (`builtin.c:167-174`: `print`, `printbold`, `hudmessage`,
`hudmessagebold`, `log`, `strparam`), sharing [`Print`](#see-also)/[`Log`](#see-also)/
[`HudMessage`](hudmessage.md)/[`StrParam`](strparam.md)'s `peek_format_cast`/
`read_format_item_list` format-item grammar rather than an ordinary parenthesized argument list —
see [`StrParam`](strparam.md)'s bucket note for why the auto-generated tier-C stub shows a
misleading `void PrintBold()` (zero-arg) signature. `printbold` never appears in `zcommon.bcs`'s
`special` table (positive or negative index). It compiles to `PCD_ENDPRINTBOLD`
(`g_funcs[]`/`g_formats[]`, `zt-bcc/src/builtin.c:170,321`), a distinct opcode from `Print`'s
`PCD_ENDPRINT` — they are not literally the same opcode, but see "Wiki's core claim" below for why
they render identically anyway.

**Tier:** A. **Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD —
see "Engine scope" in `../../shared/AUTHORING.md`).

**Provenance:** `PrintBold - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=PrintBold&oldid=47031`), verified against
the Zandronum source's `src/p_acs.cpp` (`PCD_ENDPRINT`/`PCD_ENDPRINTBOLD` shared case block, lines
10932-10970), the Zandronum source's `src/c_console.cpp` (`C_MidPrint`/`C_MidPrintBold`, lines
2231-2280; `PrintColors[]` table, line 293), the Zandronum source's `src/p_mobj.cpp`
(`AActor::CheckLocalView`, lines 1257-1272), and a repo-wide grep for `CorrectPrintBold` (zero
hits anywhere in the Zandronum source) on 2026-07-29.

## Syntax

```
PrintBold( <format-item-list> );
```

`<format-item-list>` is exactly the format-item grammar documented in
[`StrParam`](strparam.md#syntax) (`s:`, `d:`, `c:`, `f:`, `x:`, `b:`, `k:`, `l:`, `n:`, `i:`,
`a:`) — identical to `Print`'s. There is no plain-argument tail (unlike `HudMessage`); the
compiled text is the only payload.

## Wiki's core claim — confirmed true, and unfixable in this fork

The ZDoom wiki page opens with: *"due to an oversight, the engine executes `Print` when this
function is called. The function still prints to all player screens, but its default color is
different. To rectify that, the `CorrectPrintBold` MAPINFO property must be set to true."*

This is **verified accurate for the "same visual as Print" half, on this fork, with no way to opt
out**:

- `PCD_ENDPRINT` and `PCD_ENDPRINTBOLD` share one `case` block (`p_acs.cpp:10932-10970`). Both
  paths that actually draw the message call the exact same function, `C_MidPrint(activefont,
  work)` (`p_acs.cpp:10955-10957`) — **not** `C_MidPrintBold`, a separate, unrelated function that
  exists in `c_console.cpp` (used elsewhere for engine-internal messages, e.g. death/obituary
  text in `cl_main.cpp:6013`, never for ACS `PrintBold`).
- `C_MidPrint` hardcodes `(EColorRange)PrintColors[PRINTLEVELS]` = `PrintColors[7]` = `CR_GOLD`
  (`c_console.cpp:2250`, table at `c_console.cpp:293`) for every message it draws, regardless of
  whether the opcode was `PCD_ENDPRINT` or `PCD_ENDPRINTBOLD`. `C_MidPrintBold`'s own distinct
  default, `PrintColors[PRINTLEVELS+1]` = `PrintColors[8]` = `CR_ORANGE`, is never reached by ACS
  `PrintBold` at all. So the wiki's "different default color" claim does **not** hold here either
  — on this fork, `PrintBold` and `Print` render in the identical default color (gold) unless the
  script overrides it with a `\c` color escape in the string itself.
- **`CorrectPrintBold` does not exist anywhere in the Zandronum source** (confirmed by a
  repo-wide grep, zero hits) — it's a ZDoom-only `MAPINFO` compatibility flag that was never
  ported to this fork. There is no MAPINFO property, CVar, or compile flag that restores a
  visually distinct "bold" style for ACS `PrintBold` in Zandronum 3.2.1. The wiki frames this as a
  fixable historical oversight; on this engine it is a permanent characteristic with no opt-out.

## What actually differs from `Print`

Despite rendering identically, `PCD_ENDPRINTBOLD` is a genuinely separate opcode with two real
behavioral differences from `PCD_ENDPRINT`, both in `p_acs.cpp`'s shared case block — this is the
part of the wiki's description ("all players will see the printed text ... instead of just the
activator") that **is** accurate:

- **Local display is unconditional.** `Print` only draws locally when `screen == NULL` (no
  activator, e.g. an `OPEN` script) or `screen->CheckLocalView(consoleplayer)` is true — i.e. the
  activator is the actor the local client is currently viewing through (`p_acs.cpp:10954-10957`).
  `CheckLocalView` (`p_mobj.cpp:1257-1272`) can be false even for a live, in-game activator: e.g.
  the local console player is spectating/chasing a different actor than the script's activator.
  `PrintBold` short-circuits this whole check (`pcd == PCD_ENDPRINTBOLD || ...`) — it always draws
  locally on whichever client evaluates the opcode, independent of whose body is the activator or
  what the local client happens to be viewing.
- **Server broadcast targets everyone, not just the activator's owner.** When running as a
  server, `Print` unicasts `SERVERCOMMANDS_PrintMid` only to the client owning the activator
  player (`else if (screen->player) ... SVCF_ONLYTHISCLIENT`, `p_acs.cpp:10965-10968`).
  `PrintBold` instead takes the broadcast branch unconditionally (`pcd == PCD_ENDPRINTBOLD ||
  screen == NULL`, same lines) — every connected client gets the message regardless of who or
  what the activator was. This is the actual mechanism behind the wiki's "all players will see
  it," not a distinct render style.
- **Missile-activator substitution and console/logfile echo are identical to `Print`** — same
  `screen->target` substitution for a missile activator with no player (`p_acs.cpp:10938-10944`),
  same `AddToConsole`/`Logfile` echo inside `C_MidPrint` itself. No divergence found there.

## See also

[`StrParam`](strparam.md) for the full format-item cast table shared by `PrintBold`.
[`HudMessage`](hudmessage.md) for the sibling format-function that *does* take a plain-argument
tail after the format-item list, and for the equivalent activator-substitution logic.
[`Print`](print.md)/[`Log`](log.md)/[`HudMessageBold`](hudmessagebold.md) share the same grammar
and much of the same opcode path — see `hudmessage.md`'s bucket note for the shared-machinery
summary.
