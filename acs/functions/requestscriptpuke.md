# `int RequestScriptPuke(int script [, int arg0, int arg1, int arg2, int arg3])`

Asks the server to run a `NET` script with the given args, from a `CLIENTSIDE` script — the
client→server counterpart of `ExecuteClientScript`/`SendNetworkString`.
`NamedRequestScriptPuke(str script [, int arg0, int arg1, int arg2, int arg3])` is the same by
script name. Extension functions (`ACSF_RequestScriptPuke`/`ACSF_NamedRequestScriptPuke`, indices
-122/-126 in `zcommon.bcs`), both dispatching (the Zandronum source's `src/p_acs.cpp:7348-7356`) into
one shared helper, `RequestScriptPuke` (`p_acs.cpp:1705-1748`).

**Bucket:** extension function.

- **Signature correction vs. the wiki:** `zcommon.bcs:1755,1759` (`RequestScriptPuke(int;int,int,int,int):int`,
  `NamedRequestScriptPuke(str;int,int,int,int):int`) puts the `;` (required/optional split)
  immediately after the script param — **only `script`/the name string is required; all four
  `arg0..arg3` are optional**. The wiki page itself shows two conflicting overload lines (one with
  `arg0, arg1, arg2` required and `arg3` optional, one with all four optional) — the fully-optional
  form is the one that matches this fork's actual declared signature.
- **Target script must be `NET`-flagged, checked unconditionally client-side before anything is
  sent** (`p_acs.cpp:1718-1723`, `scriptdata->Flags & SCRIPTF_Net`, flag defined `p_acs.h:358`,
  "Safe to 'puke' in multiplayer"): fails → prints a message, returns `0`. **No `sv_cheats`
  bypass exists for this check** — contrast with the separate server-side gate
  `ACS_IsScriptPukeable` (`p_acs.cpp:13701-13717`, used for the console `puke`/`pukename` CCMDs and
  to sanity-check incoming packets), which *does* allow non-`NET` scripts when `sv_cheats` is on.
  A cheat-enabled server can `puke` a non-`NET` script from its own console, but
  `RequestScriptPuke`/`NamedRequestScriptPuke` from ACS can never target one, regardless of
  `sv_cheats`, since the decision is made purely client-side.
- **Must run where `NETWORK_GetState() != NETSTATE_SERVER`** (`p_acs.cpp:1710-1716`) — calling
  it while acting as the server prints a warning and returns `0`. Note this checks the *machine's*
  netstate, not literally "is the calling script flagged `CLIENTSIDE`" — in practice a true
  `CLIENTSIDE` script never runs with `NETSTATE_SERVER`, so the effect matches the wiki's framing,
  but the enforcement mechanism is netstate-based, not flag-based.
- **Offline (`NETSTATE_SINGLE`/`NETSTATE_SINGLE_MULTIPLAYER`) runs locally**
  (`p_acs.cpp:1729-1736`): `P_StartScript(players[consoleplayer].mo, ..., ACS_ALWAYS | ACS_NET)` —
  console player as activator, forced execute-always. During demo playback
  (`CLIENTDEMO_IsPlaying()`, `p_acs.cpp:1725-1727`) it's a silent no-op that still returns `1`,
  same undocumented-by-wiki pattern as `ExecuteClientScript`.
- **"Execute always, no negative script number needed" is hardcoded, not client-chosen:** the
  networked path always sends `always = true` (`p_acs.cpp:1746`,
  `CLIENTCOMMANDS_Puke(script, scriptArgs, true)`), and the server unconditionally honors it
  (`sv_main.cpp:7496-7497`, ORs in `ACS_ALWAYS` whenever the received flag is set — which it always
  is from this path).
- **Unreliable, fire-and-forget transport, confirmed structurally rather than by a named flag:**
  `CLIENTCOMMANDS_Puke` (`cl_commands.cpp:757-783`) writes the `CLC_PUKE` command into the same
  per-tic local command buffer (`g_LocalBuffer`) that ordinary tic commands use, flushed once per
  tic via `CLIENT_SendServerPacket` → `NETWORK_LaunchPacket` (`network.cpp:867+`) — a single UDP
  send with no sequencing/ack/retry. The server→client direction has an explicit
  reliable-vs-unreliable split (`SERVER_SendClientPacket(client, bReliable)`,
  `sv_main.cpp:966`); **no equivalent reliable channel exists client→server**, so a dropped
  `CLC_PUKE` packet is simply lost with no retransmission — matching the wiki's caveat.
- **Server-side activator is always the puking player, never the original `CLIENTSIDE` script's
  activator:** `server_Puke` (`sv_main.cpp:7461-7500`) re-validates with `ACS_IsScriptPukeable`
  then calls `P_StartScript(players[g_lCurrentClient].mo, ...)` — `g_lCurrentClient` is whichever
  client's packet is currently being processed, entirely independent of what triggered the
  original client-side script. Confirmed exactly as the wiki states.
- **Return `1` means "packet handed off," not "server received/ran it"** — the networked branch
  returns `1` immediately after calling `CLIENTCOMMANDS_Puke`, with no feedback from the actual
  send. A secondary, very unlikely edge case: `CLIENTCOMMANDS_Puke` has its own
  `ACS_ExistsScript` early-out (`cl_commands.cpp:759-760`) that, if it ever disagreed with the
  check already done in `RequestScriptPuke`, would silently write nothing to the buffer while the
  outer call still returns `1` — not expected to be reachable in normal operation.
- **An unresolvable script name/number is a client-side crash, not a printed warning.** Unlike
  every other failure branch in this function, the `StaticFindScript` result at `p_acs.cpp:1707`
  is dereferenced (`scriptdata->Flags` at `p_acs.cpp:1718`) with no intervening NULL check. Compare
  `ACS_IsScriptPukeable` and `ACS_IsScriptClientSide`, both of which NULL-check their lookup
  first. Double-check spelling before shipping a `NamedRequestScriptPuke` call — a typo doesn't
  fail gracefully.
- **The server never rate-limits a valid puke to a `NET` script.** `server_Puke`
  (`sv_main.cpp:7461-7500`) only calls `server_CheckForClientCommandFlood`
  (`sv_main.cpp:5783-5810`, a `sv_limitcommands`-gated temp-ban) in the branch taken when
  `ACS_IsScriptPukeable` is *false* (`sv_main.cpp:7488-7495`) — i.e. exactly the cheat-server
  case. A legitimately `NET`-flagged script can be puked every tic with no engine-side throttle;
  any rate limiting for a retry/heartbeat loop has to be done in the script's own logic (or by
  the server script refusing to act more than once per some interval), not assumed from the
  engine.
- **A NULL activator on the server side fans a `Give`/`TakeInventory` out to every player**, not a
  no-op. `server_Puke` calls `P_StartScript(players[g_lCurrentClient].mo, ...)` unconditionally —
  if that client has no body right now (spectator, not yet spawned), the target `NET` script runs
  with a NULL activator. `GiveInventory`/`TakeInventory` (`p_acs.cpp:1338-1340,1378-1386` and the
  matching take-side helper) special-case a NULL activator as "loop over every player currently in
  the game and apply to each," not "do nothing" — see `functions/giveinventory.md` if it exists,
  or the engine source directly. Any `NET` script reachable via `RequestScriptPuke` that gives or
  takes inventory must validate `PlayerNumber() >= 0 && PlayerInGame(...) &&
  !PlayerIsSpectator(...)` itself before touching inventory; the engine will not stop a
  NULL-activator call from broadcasting.

**Example** (from the wiki):

```
Script 1 (int numcookies) NET
{
    Print(n: 0, s: " gives the server host ", d: numcookies, s: " cookies");
}

Script 2 (int numcookies) CLIENTSIDE
{
    RequestScriptPuke(1, numcookies, 0, 0);
}
```

**Returns:** `int` — `1` if the puke request was handed off for sending (or executed locally
offline), `0` if called on the server or the target script isn't `NET`. `1` does not guarantee
the server actually received or ran the script.

**Provenance:** wiki page `RequestScriptPuke - Zandronum Wiki.html` (`_intake/`, retrieved
2026-07-28, `oldid=1312`) + source-verified (`p_acs.cpp:1338-1340,1378-1386,1705-1748,5487,5491,
7348-7356,13701-13717`, `p_acs.h:358`, `cl_commands.cpp:757-783`,
`sv_main.cpp:966,5210,5783-5810,7461-7500,7488-7495`, `network.cpp:867`).
The wiki's NET-flag requirement, client-only restriction, unreliable delivery, and
puker-is-activator claims all hold; the corrected (fully-optional) signature, the missing
`sv_cheats` bypass, the demo-playback no-op, the exact transport mechanism, the unchecked NULL
deref on an unresolvable script name, the missing flood-check on valid `NET` pukes, and the
NULL-activator all-players fan-out on `Give`/`TakeInventory` are this doc's source-verified
additions (the last three found and added 2026-07-28 while building a clientside input-queueing
feature in a real project). **Engine:** Zandronum 3.2.1 (verified
against the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.
