# `int ExecuteClientScript(int script, int client [, int arg0, int arg1, int arg2, int arg3])`

**Tier:** A.
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-28)
**Provenance:** wiki page `ExecuteClientScript - Zandronum Wiki.html` (`_intake/`, retrieved
2026-07-28, `https://wiki.zandronum.com/w/index.php?title=ExecuteClientScript&oldid=1311`) + source-verified (`p_acs.cpp:1758-1808,5509-5510,7824-7833,13684-13697,13721-13725`,
`p_interaction.cpp:3006-3014`, `sv_commands.cpp:3567`, `sv_commands.h:73`). The wiki's core
behavior (one-client `ACS_ExecuteAlways`, the two named failure reasons, arg passthrough, offline
local-execution) holds; the silent-fail-on-invalid-`client` case, the demo-playback no-op, and the
`SCRIPTF_Net`/compat-flag carve-out on the CLIENTSIDE check are this doc's source-verified
additions.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function.

Runs a `CLIENTSIDE` script for exactly one connected player, instead of everyone (like
`ACS_ExecuteAlways` would). `NamedExecuteClientScript(str script, int client, ...)` is the same,
by name instead of number. Extension functions (`ACSF_ExecuteClientScript`/
`ACSF_NamedExecuteClientScript`, indices -144/-145 in `zcommon.bcs`), both dispatching
(the Zandronum source's `src/p_acs.cpp:7824-7833`) into one shared helper,
`ExecuteClientScript` (`p_acs.cpp:1758-1808`) — the named variant just resolves the string to the
standard negative "named script" number first.

- **`client` is a plain player index (0..`MAXPLAYERS`-1), not a separate "client id" namespace.**
  Validated with the same `PLAYER_IsValidPlayer` used everywhere else in ACS for player numbers
  (`p_interaction.cpp:3006-3014`: rejects `client >= MAXPLAYERS` or `playeringame[client] ==
  false`). **If `client` fails this check, the function silently returns `0` with no console
  message** (falls through to the final `return 0;` at `p_acs.cpp:1807`) — unlike the two
  script-validation failures below, which do print one. The wiki doesn't mention this failure mode
  at all.
- **Must be called from a server-sided (non-`CLIENTSIDE`) script; a client calling it is rejected
  outright**, matching the wiki: `NETWORK_GetState() == NETSTATE_CLIENT` prints
  `"ExecuteClientScript can only be invoked from serversided scripts..."` and returns `0`
  (`p_acs.cpp:1773-1779`).
- **Target script must exist and be `CLIENTSIDE`-flagged**, checked server-side in that order:
  `ACS_ExistsScript` (`p_acs.cpp:13721-13725`) then `ACS_IsScriptClientSide`
  (`p_acs.cpp:13684-13697`) — either failing prints a message and returns `0`
  (`p_acs.cpp:1785-1796`). **The CLIENTSIDE check has a legacy carve-out**: a script flagged
  `SCRIPTF_Net` (i.e. `NET`) instead also counts as clientside if the compat flag
  `ZACOMPATF_NETSCRIPTS_ARE_CLIENTSIDE` is enabled (old Skulltag map compatibility) — so "doesn't
  have the CLIENTSIDE flag" per the wiki isn't the complete story on the Zandronum engine fork.
- **`arg0..arg3`** are copied into a fixed 4-slot buffer, zero-padded if fewer are supplied
  (`p_acs.cpp:1798-1801`), then sent via `SERVERCOMMANDS_ACSScriptExecute(...,  client,
  SVCF_ONLYTHISCLIENT)` (`sv_commands.cpp:3567+`, flag at `sv_commands.h:73`) — the
  `SVCF_ONLYTHISCLIENT` flag is what restricts delivery to just that one player instead of
  broadcasting, i.e. this is the actual network-traffic savings the wiki alludes to.
- **⚠ The dispatched script inherits the CALLING script's own activator, not the target client's
  local player, and not `NULL`.** `SERVERCOMMANDS_ACSScriptExecute` serializes whatever activator
  the server-side call itself had (`command.SetActivator(pActivator)`, `sv_commands.cpp:3595`); the
  receiving client's `ServerCommands::ACSScriptExecute::Execute()` deserializes it and passes it
  straight into `P_StartScript(activator, ...)` unchanged (`cl_main.cpp:7163-7193`, notably line
  7192). Concretely: if the caller was itself an `ENTER`/pukeable script activated by player A, then
  `NamedExecuteClientScript("Foo", B)` starts `Foo` on client B **with player A's actor still set as
  the activator** — not B's own player, and not `NULL`. This matters for anything in the dispatched
  script that's activator-sensitive: non-bold `HudMessage`/`Print` only draw locally when the
  activator is `NULL` or matches `players[consoleplayer].mo` (see the `PCD_ENDHUDMESSAGE` check in
  `p_acs.cpp` around line 11000), and `GetCVar`/`GetCVarString` on a `CVAR_USERINFO` cvar resolve
  against the activator's player, not the console player (see `families/cvar.md`'s "Userinfo
  redirect" section). A dispatched script that needs to act on "whoever this client's local player
  is" must explicitly call `SetActivatorToPlayer(ConsolePlayerNumber())` first — nothing about
  `NamedExecuteClientScript`'s dispatch does this automatically, unlike, say, an `ENTER`-typed script
  which starts with no activator per-client. Not documented on the wiki, which has no concept of the
  client/server activator-serialization split at all.
- **Offline (`NETSTATE_SINGLE`/`NETSTATE_SINGLE_MULTIPLAYER`) runs the script locally with no
  networking, no client-index check, and no CLIENTSIDE-flag check at all** — a direct
  `P_StartScript(..., ACS_ALWAYS)` call (`p_acs.cpp:1766-1771`), the same `ACS_ALWAYS` flag
  `ACS_ExecuteAlways` uses, confirming the wiki's "equivalent to `ACS_ExecuteAlways`" framing for
  this path specifically.
- **During demo playback, the call is a no-op that still returns `1`** (`CLIENTDEMO_IsPlaying()`,
  `p_acs.cpp:1762-1764`) — checked before any other branch. A `1` return therefore does not always
  mean the script actually ran; this case isn't mentioned by the wiki.

**Example:**

```text
ExecuteClientScript(3, client, hudSlot, 0, 0, 0);
```

**Returns:** `int` — `1` if the script was executed or successfully dispatched to the client
(or skipped as a demo-playback no-op), `0` on any of: caller is a client, target script doesn't
exist, target script isn't clientside, or `client` isn't a valid in-game player index.

## Engine-family divergence

`ExecuteClientScript`/`NamedExecuteClientScript` are ACSF indices 144/145 — inside the 100–199
range UZDoom's own ACSF enum reserves for Zandronum's extensions and implements none of (see
[Zandronum/UZDoom compatibility](../concepts/zandronum-uzdoom-compat.md)). A Zandronum-compiled
object calling either under UZDoom hits the `default: break;` arm of UZDoom's `CallFunction`
dispatcher: no error, no log line, the interpreter stack is rebalanced as if the call had
succeeded, and execution just continues with `0` in place of this function's real return value.

The dangerous part isn't the return value, it's what silently doesn't happen alongside it: on
Zandronum this function's whole job is dispatching a `CLIENTSIDE` script to run on one specific
connected player via a targeted server command (see the body above). Under UZDoom none of that
fires — no script gets sent to the client, nothing runs there — but the `0` result is
indistinguishable from any of this function's own legitimate Zandronum-side failures (invalid
`client`, missing/non-`CLIENTSIDE` target script, caller not server-sided), so a caller has no way
to tell "the dispatch mechanism doesn't exist here" apart from "the dispatch was rejected." A
hand-ported call site can't route around this by targeting the receiving script directly either:
UZDoom repurposes the same `SFLG` bit Zandronum uses for `CLIENTSIDE` as `SCRIPTF_Ignored`, with no
client/server execution split at all (see [Client-side scripting](../concepts/clientside-scripting.md))
— there's no UZDoom-side equivalent to redirect to, only ordinary single-sided script execution.
