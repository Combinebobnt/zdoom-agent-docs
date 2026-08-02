# `HudMessageBold`

**Bucket:** compiler builtin — same "Format functions" block as
[`HudMessage`](hudmessage.md)/[`StrParam`](strparam.md)/`Print`/`Log` (`zt-bcc/src/builtin.c:172`:
`{ "hudmessagebold", ";iiifff;fff" }`), byte-for-byte the same `g_funcs[]` format string as
`hudmessage` (`builtin.c:171`). Never appears in `zcommon.bcs`'s `special` table. Full parameter
grammar, format-item casts, flag bits, per-type optional-tail table, and the `holdTime=0` footgun
are all identical to `HudMessage` — see [`HudMessage`](hudmessage.md) for those; this file only
covers what's actually different about the Bold variant.

**Tier:** A. **Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD —
see "Engine scope" in `../../shared/AUTHORING.md`).

**Provenance:** `HudMessageBold - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=HudMessageBold&oldid=41033`), verified against
the Zandronum source's `src/p_acs.cpp` (`PCD_ENDHUDMESSAGEBOLD`, shares the single `case
PCD_ENDHUDMESSAGE: case PCD_ENDHUDMESSAGEBOLD:` block at lines 10984-11144 with `HudMessage`) and
the zt-bcc source's `src/builtin.c:172` on 2026-07-29.

## Syntax

```
HudMessageBold( <format-item-list>; type, id, color, x, y, holdTime [, extra1] [, extra2] [, alpha] );
```

Identical call grammar to [`HudMessage`](hudmessage.md#syntax) — the wiki's own per-type overload
list (separate signatures for plain/`HUDMSG_FADEOUT`/`HUDMSG_TYPEON`/`HUDMSG_FADEINOUT`) is purely
documentation convenience; at the compiler level (`builtin.c:172`) there is exactly one signature,
`;iiifff;fff`, same as `hudmessage` — the trailing `fff` is always up to three optional plain
fixed values, and which of them means `fadeTime`/`typeTime`/`inTime`/`outTime`/`alpha` is resolved
at runtime by `type & 0xFF`, not by which overload the compiler picked. See
[`HudMessage`](hudmessage.md#optional-tail-extra1-extra2-alpha) for the full per-type table.

## What's actually different: always broadcasts, and activator resolution is dead code

The wiki's one substantive claim — "prints a message in the same manner as `HudMessage` but for
all players," directly analogous to `PrintBold`/`Print` — is correct, and the engine implements it
by short-circuiting on the opcode itself (`pcd == PCD_ENDHUDMESSAGEBOLD`) at every branch point
that would otherwise narrow `HudMessage` to one target, rather than through any separate logic
path:

- **The missile-activator substitution still runs, but its result is provably irrelevant for
  Bold.** Both opcodes share the same setup code (`p_acs.cpp:10990-10998`): if the activator is a
  target-less-player projectile (`MF_MISSILE`) with a non-null `target`, `screen` is resolved to
  the firing actor, exactly as documented for [`HudMessage`](hudmessage.md#activator-resolution-and-zandronum-netcode-caveats-not-covered-by-the-zdoom-wiki-page-at-all).
  For `HudMessageBold` this computation is dead code: every later branch that reads `screen` is
  guarded `pcd == PCD_ENDHUDMESSAGEBOLD || screen == NULL || ...` (`p_acs.cpp:10999`) or
  `pcd == PCD_ENDHUDMESSAGEBOLD || screen == NULL` (`p_acs.cpp:11031,11047,11065,11083`) — the
  left disjunct is a compile-time-constant `true` for the Bold opcode, so the `screen` value never
  actually changes which branch is taken. Whether the activator is a player, a monster, a
  target-less projectile, or has no activator at all (`OPEN`/etc.), the outcome is identical.
- **Local build/attach is unconditional (not gated on "is this the console player's body").**
  `HudMessage`'s local-display gate (`screen == NULL`, or `screen` is the console player's body, or
  the local machine is a listen/dedicated server) never applies to Bold — the same `pcd ==
  PCD_ENDHUDMESSAGEBOLD` disjunct at `p_acs.cpp:10999` makes the whole condition true
  unconditionally, so on any non-server instance (single-player or a connected client) the message
  is always locally built and attached via `StatusBar->AttachMessage`, regardless of who or what
  the activator is.
- **Server → client forwarding always takes the broadcast path, never the per-client unicast
  path.** In all four per-type cases (`p_acs.cpp:11031/11047/11065/11083`), the condition guarding
  the broadcast call is `(pcd == PCD_ENDHUDMESSAGEBOLD) || (screen == NULL)` — true unconditionally
  for Bold — so `SERVERCOMMANDS_PrintACSHUDMessage` is always called with no player argument (goes
  out to every connected client). The `else if (screen->player) ... SVCF_ONLYTHISCLIENT` unicast
  branch that `HudMessage` can take is structurally unreachable for `PCD_ENDHUDMESSAGEBOLD` — not
  just "usually broadcasts," genuinely dead code for this opcode.
- **All `HUDMSG_*` flags behave identically to `HudMessage`.** The flag-application block
  (`p_acs.cpp:11095-11117`: layer, visibility, `NOWRAP`, `ALPHA`, `ADDBLEND`) and the `HUDMSG_LOG`
  console-echo block (`p_acs.cpp:11118-11139`) run unconditionally after the type switch for both
  opcodes — no Bold-specific gap or extra restriction found in any flag.

Net effect: for `HudMessageBold`, the `activator` has **zero influence** on who receives or sees
the message — not "usually everyone," but structurally guaranteed everyone, because every branch
that would consult the activator-derived `screen` is unreachable when `pcd ==
PCD_ENDHUDMESSAGEBOLD`. This is a stronger and more precise claim than either the ZDoom wiki page
(which only says "for all players" without explaining why activator-substitution logic doesn't
leak through) or a naive reading of the shared code block would suggest at a glance.

## See also

[`HudMessage`](hudmessage.md) for the full shared syntax, format-item grammar, parameter meanings,
optional-tail-by-type table, flag bit values, and the `holdTime=0` non-infinite footgun — all
identical for `HudMessageBold`. [`StrParam`](strparam.md) for the format-item cast table.
