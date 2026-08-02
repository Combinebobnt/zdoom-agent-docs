# `int ExecuteClientScript(int script, int client [, int arg0, int arg1, int arg2, int arg3])`

Runs a `CLIENTSIDE` script for exactly one connected player, instead of everyone (like
`ACS_ExecuteAlways` would). `NamedExecuteClientScript(str script, int client, ...)` is the same,
by name instead of number. Extension functions (`ACSF_ExecuteClientScript`/
`ACSF_NamedExecuteClientScript`, indices -144/-145 in `zcommon.bcs`), both dispatching
(the Zandronum source's `src/p_acs.cpp:7824-7833`) into one shared helper,
`ExecuteClientScript` (`p_acs.cpp:1758-1808`) — the named variant just resolves the string to the
standard negative "named script" number first.

**Bucket:** extension function.

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
  have the CLIENTSIDE flag" per the wiki isn't the complete story on this fork.
- **`arg0..arg3`** are copied into a fixed 4-slot buffer, zero-padded if fewer are supplied
  (`p_acs.cpp:1798-1801`), then sent via `SERVERCOMMANDS_ACSScriptExecute(...,  client,
  SVCF_ONLYTHISCLIENT)` (`sv_commands.cpp:3567+`, flag at `sv_commands.h:73`) — the
  `SVCF_ONLYTHISCLIENT` flag is what restricts delivery to just that one player instead of
  broadcasting, i.e. this is the actual network-traffic savings the wiki alludes to.
- **Offline (`NETSTATE_SINGLE`/`NETSTATE_SINGLE_MULTIPLAYER`) runs the script locally with no
  networking, no client-index check, and no CLIENTSIDE-flag check at all** — a direct
  `P_StartScript(..., ACS_ALWAYS)` call (`p_acs.cpp:1766-1771`), the same `ACS_ALWAYS` flag
  `ACS_ExecuteAlways` uses, confirming the wiki's "equivalent to `ACS_ExecuteAlways`" framing for
  this path specifically.
- **During demo playback, the call is a no-op that still returns `1`** (`CLIENTDEMO_IsPlaying()`,
  `p_acs.cpp:1762-1764`) — checked before any other branch. A `1` return therefore does not always
  mean the script actually ran; this case isn't mentioned by the wiki.

**Example:**

```
ExecuteClientScript(3, client, hudSlot, 0, 0, 0);
```

**Returns:** `int` — `1` if the script was executed or successfully dispatched to the client
(or skipped as a demo-playback no-op), `0` on any of: caller is a client, target script doesn't
exist, target script isn't clientside, or `client` isn't a valid in-game player index.

**Provenance:** wiki page `ExecuteClientScript - Zandronum Wiki.html` (`_intake/`, retrieved
2026-07-28, `oldid=1311`) + source-verified (`p_acs.cpp:1758-1808,5509-5510,7824-7833,13684-13697,13721-13725`,
`p_interaction.cpp:3006-3014`, `sv_commands.cpp:3567`, `sv_commands.h:73`). The wiki's core
behavior (one-client `ACS_ExecuteAlways`, the two named failure reasons, arg passthrough, offline
local-execution) holds; the silent-fail-on-invalid-`client` case, the demo-playback no-op, and the
`SCRIPTF_Net`/compat-flag carve-out on the CLIENTSIDE check are this doc's source-verified
additions. **Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — see
"Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.
