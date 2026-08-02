# `Log`

**Bucket:** compiler builtin — like [`HudMessage`](hudmessage.md)/[`StrParam`](strparam.md)/
`Print`/`PrintBold`/`HudMessageBold`, this is one of the five names in `zt-bcc/src/builtin.c`'s
dedicated "Format functions" block (`builtin.c:173`: `{ "log", "" }`), not a `zcommon.bcs`
`special`-table entry — it never appears there with a positive or negative index. The empty
format string means (`builtin.c:404-419`) a `void` return with **no** plain parameter list at
all (`format[0]` is neither `'i'/'r'/'f'/'b'/'s'` nor `';'`, so `setup_return_type` defaults to
`SPEC_VOID` and `setup_param_list` never runs) — structurally identical to `print`/`printbold`
(also `""`) and simpler than `hudmessage`/`hudmessagebold` (`";iiifff;fff"`, which have a
required+optional plain-arg tail after the format-item list) or `strparam` (`"s"`, a `str`
return). All arguments to `Log` come from the separate format-item-list grammar
(`peek_format_cast`/`read_format_item_list`, `zt-bcc/src/parse/expr.c:901-931,949-1035`), the
same one `Print`/`HudMessage`/`StrParam` use. At the opcode level, `log`'s entry in `builtin.c`'s
parallel `g_formats[]` table (index 4, after `print`/`printbold`/`hudmessage`/`hudmessagebold`)
maps to `PCD_ENDLOG` (`builtin.c:319-325`); the format items themselves build the shared `work`
`FString` via the same `PCD_BEGINPRINT`/`PCD_PRINTSTRING`/`PCD_PRINTNUMBER`/etc. instructions
every format function uses (`p_acs.cpp:10730-10731` starts the buffer; `PCD_ENDLOG` at
`p_acs.cpp:10937-10942` closes it).

**Tier:** A. **Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD —
see "Engine scope" in `../../shared/AUTHORING.md`).

**Provenance:** `Log - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=Log&oldid=35648`), verified against
the Zandronum source's `src/p_acs.cpp` (`PCD_ENDLOG`, lines 10934-10978) and
the Zandronum source's `src/c_console.cpp` (`PrintString`/`VPrintf`/`Printf`, lines 1021-1192;
`C_AddNotifyString`/`C_DrawNotifyText`, lines 672-731 and ~1300-1384) on 2026-07-29.

## Syntax

```
Log( <format-item-list> );
```

`<format-item-list>` is exactly the format-item grammar documented in
[`StrParam`](strparam.md#syntax) (`s:`, `d:`, `c:`, `f:`, `x:`, `b:`, `k:`, `l:`, `n:`, `i:`,
`a:`) — the same one `Print`/`HudMessage` build their text with. Unlike `HudMessage`, there is no
`;`-separated trailing plain-argument tail (no type/id/color/position/hold-time) — `Log` always
takes exactly one thing, the format-item list, and returns nothing.

## Behavior

`PCD_ENDLOG` does exactly one thing with the finished `work` string (`p_acs.cpp:10937-10942`):

```cpp
if (pcd == PCD_ENDLOG)
{
    Printf ("%s\n", work.GetChars());
    STRINGBUILDER_FINISH(work);
}
```

That's the plain 1-argument `Printf(const char*, ...)` overload, which always uses printlevel
`PRINT_HIGH` (`c_console.cpp:1182-1192`) — **`Log` cannot select a different printlevel/color**,
unlike raw engine `Printf(printlevel, ...)` callers. `Printf` → `VPrintf` → `PrintString`
(`c_console.cpp:1021-1156`) is where the wiki's "log area (top left) + console" claim is decided:

- **`msg` cvar gate (undocumented by the wiki, Log-specific):** `PrintString` opens with
  `if (printlevel < msglevel || *outline == '\0') return 0;` (`c_console.cpp:1023`). The `msg`
  cvar (`FIntCVar msglevel`, default `0`) can silently suppress `Log` output entirely — console,
  logfile, *and* the notify overlay — if a player/server raises it above `PRINT_HIGH` (`2`).
  `Print`/`PrintBold`/`HudMessage` never go through `PrintString` at all (they call
  `C_MidPrint`/`StatusBar->AttachMessage` directly), so this gate is unique to `Log` among the
  format functions.
- **Logfile:** if a `-log` logfile is open, the (color-code-stripped) text is always appended,
  independent of everything below.
- **Console scrollback:** `AddToConsole(printlevel, outlinecopy)` always runs (for
  `printlevel != PRINT_LOG`, which `PRINT_HIGH` satisfies) — this is the "logs it to the console"
  half of the wiki's description.
- **On-screen "log area" (top-left notify overlay) — confirms the wiki, but only under a
  condition the wiki never states:** `C_AddNotifyString` (which populates `NotifyStrings[]`,
  drawn top-left via `screen->DrawText(SmallFont, color, 0, line, ...)`,
  `c_console.cpp:1360` — `x=0` is literally the left edge) only runs when
  `NETWORK_GetState() != NETSTATE_SERVER` **and** `vidactive && screen && SmallFont`
  (`c_console.cpp:1144-1150`). Once drawn, each line fades out and expires after
  `con_notifytime` seconds (cvar, default `3.0`), is skipped while `show_messages` is off (unless
  `PrintLevel == 128`, which `Log` never uses), and doesn't draw at all while the console is fully
  open (`GS_FULLCONSOLE`) — none of which the wiki mentions.

### `NETSTATE_SERVER` — the real Zandronum-only trap (not on the wiki at all)

`NETSTATE_SERVER` covers **both** a dedicated server and a listen server acting as host
(`network.h:266-282`: "Program is a server, hosting a game") — not just headless dedicated
servers. Two consequences neither the ZDoom wiki (single-player-only framing) nor any in-tree
doc for `Print`/`HudMessage` prepares you for:

1. **On any server, the on-screen notify half never fires at all.** `Log()` executed by the
   server's own copy of the script only ever reaches that machine's console/logfile — never an
   on-screen HUD line, even for the host player in a listen game.
2. **`PCD_ENDLOG` has zero networking code — no client ever sees a server-run `Log()` call, under
   any circumstance.** Compare `PCD_ENDPRINT`/`PCD_ENDPRINTBOLD`
   (`p_acs.cpp:10961-10970`, `SERVERCOMMANDS_PrintMid`) or `HudMessage`'s
   `SERVERCOMMANDS_PrintACSHUDMessage` forwarding (`p_acs.cpp:11029-11090`, see
   [`HudMessage`](hudmessage.md#activator-resolution-and-zandronum-netcode-caveats-not-covered-by-the-zdoom-wiki-page-at-all)) —
   both explicitly detect `NETWORK_GetState() == NETSTATE_SERVER` and push the message to clients
   over the network. `PCD_ENDLOG`'s branch (`p_acs.cpp:10937-10942`) does nothing of the kind; it
   is the *only* one of the five format functions with no server→client forwarding path at all.
   A non-`CLIENTSIDE` script's `Log()` call, run by the server, is therefore invisible to every
   connected player, no matter who or what the activator is — useful for admin-facing debug
   logging, useless as a player-facing message on a networked game. (A `CLIENTSIDE` script's
   `Log()` runs independently on each client's own machine instead, and *does* show there, since
   each client's local execution is its own `NETSTATE_CLIENT`/`NETSTATE_SINGLE`-context call.)

### No activator targeting at all (unlike `Print`/`PrintBold`/`HudMessage`)

`PCD_ENDLOG`'s branch is taken *before* the missile-activator-substitution and
`screen->CheckLocalView(consoleplayer)` logic that governs `Print`/`PrintBold`/`HudMessage`
(`p_acs.cpp:10944-10959`, guarded by `else if (pcd != PCD_MOREHUDMESSAGE)` — `PCD_ENDLOG` never
reaches it). `Log` is completely activator-independent: it always just prints on whichever
machine executes the opcode, with no per-player routing, no missile→shooter substitution, and no
"only show to this one target" concept — a divergence from "same parameter format as Print" that
the wiki's one-line summary doesn't capture (the *format-item* syntax is identical; the
*delivery* semantics are not).

## See also

[`StrParam`](strparam.md) for the full format-item cast table shared by `Log`.
[`HudMessage`](hudmessage.md) for the sibling format function whose Zandronum server→client
forwarding this doc contrasts `Log`'s complete lack of against. [`Print`](print.md)/
[`PrintBold`](printbold.md)/[`HudMessageBold`](hudmessagebold.md) share the same grammar and
opcode-building path — see the "Bucket note" in
[`HudMessage`](hudmessage.md#bucket-note-for-hudmessagebold-print-log-printbold).
[Client-side scripting](../concepts/clientside-scripting.md#relaying-a-server-side-log-to-one-or-all-clients-via-a-clientside-relay-script)
for the working idiom that fills the server→client gap this doc describes — a
`CLIENTSIDE` relay script invoked via `NamedSendNetworkString`, used by a helper pair
`LogTo()`/`Log_To`, plus a sibling `LogBold()` that reuses the same
`Log_To` receiver and just omits the `client` argument to broadcast to every connected client
instead of targeting one player.
