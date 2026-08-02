# `int SendNetworkString(int script, str string [, int client])`

Sends a string across the network (server→client or client→server) and runs a script on the
receiving end with that string as its argument. `NamedSendNetworkString(str script, str string [,
int client])` is the same by script name. Extension functions (`ACSF_SendNetworkString`/
`ACSF_NamedSendNetworkString`, indices -146/-147 in `zcommon.bcs`), both dispatching
(the Zandronum source's `src/p_acs.cpp:7835-7847`) into one shared helper, `SendNetworkString`
(`p_acs.cpp:1818-1886`). Added in commit `645cce9` (2020-12-26); not independently confirmed
present unmodified in the 3.2.1 release specifically (no version tags past 2.x exist in this
checkout to pin it), but core ACS engine functions of this vintage are stable across minor
versions — flag for re-check only if a claim here doesn't hold on an actual 3.2.1 client.

**Bucket:** extension function.

- `client` is optional, default `-1` (`p_acs.cpp:7836,7842-7843`), and is **only ever read in the
  `NETSTATE_SERVER` branch** (`p_acs.cpp:1862-1883`) — the client-side send path
  (`CLIENTCOMMANDS_ACSSendString`) takes no client argument at all. Confirms the wiki's "only
  matters when called by the server."
- **A negative (or omitted/default) `client` broadcasts to every connected client, not just "no
  target" — undocumented by the wiki and easy to miss even reading this function's own doc.**
  `p_acs.cpp:1875-1880`: `client < 0` calls `SERVERCOMMANDS_ACSSendString(script, activator,
  string)` with no target-restriction flag, which broadcasts; `client >= 0` calls the same
  function with `client, SVCF_ONLYTHISCLIENT` to unicast to that one player. This makes
  `NamedSendNetworkString("SomeClientsideScript", msg)` (omitting `client` entirely) the
  straightforward way to run a `CLIENTSIDE` script — and therefore deliver a string — on *every*
  client at once, no loop over `PLAYER_IsValidPlayer` slots required. See
  [Client-side scripting](../concepts/clientside-scripting.md#relaying-a-server-side-log-to-one-or-all-clients-via-a-clientside-relay-script)
  for a concrete server→client string-delivery pattern built on this.
- **Reliability is asymmetric — the wiki's "no guarantee it's received" is only accurate for
  client→server.** Server→client traffic for this function goes through the normal
  `NetCommand`/`PacketBuffer` path (`ServerCommands::ACSSendString::BuildNetCommand`,
  `servercommands.cpp:11874-11886`, never marked unreliable) and is scheduled for resend via
  `SavedPackets.ScheduleUnsentPacket` (`sv_main.cpp:975-979`); a client that notices a gap
  requests it back with `CLC_MISSINGPACKET` and the server explicitly resends
  (`sv_main.cpp:5107-5109`, `server_MissingPacket`) — i.e. this direction is acknowledged and
  resend-backed, not fire-and-forget. **Client→server has no such mechanism**:
  `CLIENTCOMMANDS_ACSSendString` writes into the per-tic `g_LocalBuffer`
  (`cl_commands.cpp:787-799`), sent once via a single `NETWORK_LaunchPacket` call with no saved/
  resend queue — matching the original commit message's own description ("sending strings from
  client to server works just like puking scripts and there's no guarantee they are sent to the
  server successfully"). Don't treat the two directions as symmetric when writing mod code that
  depends on delivery.
- **Empty/null string is a distinct, wiki-undocumented failure**: `p_acs.cpp:1845-1847` returns
  `0` if the string resolves empty — not one of the wiki's three listed failure reasons.
- **Offline (`NETSTATE_SINGLE`/`NETSTATE_SINGLE_MULTIPLAYER`) always returns `1`**
  (`p_acs.cpp:1827-1834`) — runs the script locally via `P_StartScript` with no
  `ACS_ExistsScript`/empty-string checks at all in this branch (those only execute further down,
  in the multiplayer-only code paths). During demo playback the call is a no-op that also returns
  `1` (`p_acs.cpp:1824-1825`) — same undocumented-by-wiki pattern as `ExecuteClientScript`/
  `RequestScriptPuke`.
- **Multiplayer failure checks, in order** (`p_acs.cpp:1836-1883`): target script must exist
  (`ACS_ExistsScript`) → `0`; string must be non-empty → `0`; if called client-side, target script
  must be `NET`-flagged (`SCRIPTF_Net`) → `0`; if called server-side, `client` must be a valid
  in-game player (`PLAYER_IsValidPlayer`) and the target script must be `CLIENTSIDE`-flagged
  (`ACS_IsScriptClientSide`) → `0`. Matches the wiki's three named reasons plus the extra
  empty-string case above.
- **The string travels via the normal ACS global-string-table mechanism, not a raw pass-through**:
  the sender resolves its local string index to text with `FBehavior::StaticLookupString`
  (`p_acs.cpp:1843`) and that text is what's serialized over the wire; the receiver re-inserts the
  text into its *own* string table (`GlobalACSStrings.AddString`, client-receive
  `cl_main.cpp:7201`, server-receive `sv_main.cpp:7525`) and passes the resulting **new** index as
  the script's single argument (`{ stringIndex, 0, 0, 0 }`). The received index is not guaranteed
  to equal the sender's original index — standard ACS string-arg behavior, but easy to assume
  otherwise.
- **Activator semantics differ by direction, and differ from `RequestScriptPuke`'s rule — do not
  assume the two functions share activator behavior:**
  - Client→server: hard-set to the sending player's own actor
    (`players[g_lCurrentClient].mo`, `sv_main.cpp:7504-7527`), executed with
    `ACS_ALWAYS | ACS_NET` — same pattern as `server_Puke`.
  - Server→client: the server transmits the *server-side calling script's own activator*, by
    NetID (`servercommands.cpp:11883`, `this->activator ? this->activator->NetID : 0`); the
    receiving client resolves that NetID back to an actor (`CLIENT_ReadActorFromNetID(...,
    allowNull=true)`, `cl_main.cpp:3472-3495`) and runs the script with `ACS_ALWAYS` (no
    `ACS_NET`). **If that actor has no NetID, or isn't known/visible to the particular receiving
    client, the activator silently becomes `NULL` and the script still runs** — this is not "the
    local player," contrary to what one might assume by analogy with `RequestScriptPuke`.

**Example** (from the wiki, client→server):

```
Script "SendStringToServer" (void) CLIENTSIDE
{
    NamedSendNetworkString("ReceiveStringOnServer", "Hello Server");
}

Script "ReceiveStringOnServer" (int string) NET
{
    Print(s: "Server received: ", s: string);
}
```

**Returns:** `int` — `1` if the string was sent (or executed locally offline/during demo
playback), `0` on: target script missing, string empty, wrong-direction NET/CLIENTSIDE flag
missing on the target, or (server-side only) an invalid `client`. A `1` from a client→server call
does not guarantee server receipt (unreliable in that direction only); server→client calls ride
an acknowledged, resend-backed channel.

**Provenance:** wiki page `SendNetworkString - Zandronum Wiki.html` (`_intake/`, retrieved
2026-07-28, `oldid=1684`) + source-verified (`p_acs.cpp:1818-1886,7835-7847`, `p_acs.h:358-359`,
`cl_commands.cpp:787-799`, `cl_main.cpp:1032,3472-3495,7195-7203`, `sv_main.cpp:975-979,5107-5109,7504-7527`,
`servercommands.cpp:11874-11886`, `netcommand.cpp:108-121,280-287`; introducing commit
`645cce9`). The wiki's three named failure reasons, the offline-local-execution behavior, and the
"only matters server-side" note on `client` all hold; the asymmetric reliability (reliable
server→client vs. unreliable client→server, contradicting the wiki's blanket claim), the
empty-string failure case, the demo-playback no-op, and the two different (and non-analogous to
`RequestScriptPuke`) activator-resolution rules per direction are this doc's source-verified
additions. The negative-`client`-broadcasts-to-everyone behavior (`p_acs.cpp:1875-1880`) was added
2026-07-29 — same source range as the initial pass, but the broadcast/unicast distinction itself
had been left unstated until a follow-up question about implementing a broadcast-to-all-clients
`Log()` variant surfaced it. **Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master`/3.3-alpha
HEAD — see "Engine scope" in `../../shared/AUTHORING.md`; this feature's exact behavior in a literal 3.2.1 build
was not independently re-confirmed due to the absence of a version tag in this checkout, but is
not expected to differ). **Tier:** A.
