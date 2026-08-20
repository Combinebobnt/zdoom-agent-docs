# Client-side scripting

**Tier:** B (wiki + partial source spot-check, not exhaustive — see Tiers in
`../../shared/AUTHORING.md` for why this doesn't qualify as A).
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-28)
**Provenance:** wiki page `Client-side scripting - Zandronum Wiki.html` (`_intake/`, retrieved
2026-07-28, `https://wiki.zandronum.com/w/index.php?title=Client-side_scripting&oldid=1545`) + spot-verified against engine source for the `CLIENTSIDE`/`NET` script
flags (`p_acs.h:358-359`) and the existence of `RequestScriptPuke`/`NamedRequestScriptPuke`
(`zcommon.bcs:1755,1759`). The client/server variable-isolation and networking-reliability claims
are wiki-sourced and plausible but **not** traced through the netcode source in this pass. The
`ENTER`/`RESPAWN CLIENTSIDE` broadcast-to-every-client behavior and its `GetPlayerInput`
consequence, and the `StaticStopMyScripts`-on-spectate persistent-loop hazard and generation-
counter fix (both added 2026-07-28, found while building a clientside input-queueing feature in
a real project — the second only after that feature shipped with the
boolean-flag version and broke in exactly this way during in-game testing) **are** fully
source-verified (`p_acs.cpp:3384-3420,3659-3679,7163-7171,12380-12389,13028-13030`,
`cl_main.cpp:4103-4110,7163-7193`, `p_interaction.cpp:2546,2772,2781`). The
`NamedSendNetworkString`-relay pattern for server→client string delivery (added 2026-07-29) is
attested by a working production implementation (`LogTo`/`LogBold`/`Log_To`, in production use)
plus [`SendNetworkString`](../functions/sendnetworkstring.md)'s own tier-A source
verification (`p_acs.cpp:1818-1886`) — fully source-verified, not a wiki restatement. The
LIFO-batch execution-order section and the server→client reliability verification (both added
2026-08-09, found while diagnosing a persistent latency-dependent client-visual item-sync desync
in a real multiplayer mod) are fully source-verified
(`p_acs.cpp:3602-3611,3831-3849`, `cl_main.cpp:1144-1166,1333-1402,7163-7193`,
`sv_commands.cpp:3567-3605`, `sv_main.cpp:1006-1031,6169-6217`,
`network/netcommand.cpp:109-118`, `network/servercommands.cpp:11793-11812`).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

What `CLIENTSIDE` scripts are, why they exist, and the client/server execution model they run
under. "Which functions are meaningful clientside" is exactly the class of gotcha a signature-only
function doc can't capture — this concept page is the missing context those function docs assume,
and is worth reading before writing (or debugging) any `CLIENTSIDE` script.

## What it is and why it exists

A `CLIENTSIDE` script runs entirely on one machine (the client that triggered it) and never
executes on, or reports back to, the server — confirmed in engine source: `SCRIPTF_ClientSide`
is a real per-script flag (the Zandronum source's `src/p_acs.h:359`, `"Is executed on the clients,
not on the server"`). The point is bandwidth: a HUD element, an on-screen effect, or anything
purely cosmetic doesn't need the server to compute it and broadcast the result to everyone as
`HudMessage` packets — running it clientside means it costs zero network traffic and is invisible
to other players, since it never leaves the machine it ran on.

`NET` is the companion flag (`SCRIPTF_Net`, `p_acs.h:358`, `"Safe to puke in multiplayer"`) — it
marks a script as safe to trigger via the console `puke` command or from a `CLIENTSIDE` script
asking the server to run something. `CLIENTSIDE` and `NET` are independent flags and commonly
combined (`script 4 OPEN NET CLIENTSIDE`).

## Execution model

- **Client and server have entirely separate variable state.** A global/world variable changed
  on the server is *not* reflected in a `CLIENTSIDE` script reading "the same" variable — each
  side runs its own independent copy. This is the single most important gotcha: don't assume a
  `CLIENTSIDE` script sees server-side state changes unless that data was explicitly sent to it
  (see "Server to client" below).
- **The client predicts, it doesn't poll.** Per the wiki: the client does three things — polls
  local input, renders the world, and receives data from the server — and interpolates actor
  movement locally (e.g. a monster walking a straight line is simulated identically on both ends
  via DECORATE state logic, not re-transmitted every tic). The server only needs to correct the
  client when something happens that the client can't predict on its own (an angle change, a
  state change).
- **Script types combine with `CLIENTSIDE`:** `OPEN CLIENTSIDE` runs once per client on level
  load/connect; `ENTER CLIENTSIDE` runs when any player joins; `RESPAWN CLIENTSIDE` runs on
  respawn.
- **`ENTER`/`RESPAWN CLIENTSIDE` broadcast to every client, not just the joining/respawning
  player's own machine — source-verified, not a wiki restatement.** `FBehavior::StartTypedScripts`
  (`p_acs.cpp:3384-3420`) treats every script type the same way here (only `SCRIPT_Unloading` is
  excluded): when `NETWORK_GetState()==NETSTATE_SERVER && ACS_IsScriptClientSide(ptr)`, it calls
  `SERVERCOMMANDS_ACSScriptExecute(...)`, which defaults to broadcasting to *all* clients, each of
  which then calls `P_StartScript(activator, ...)` locally (`cl_main.cpp:7163-7193`) with **the
  entering/respawning player as activator — not the local machine's own player.** So on a server
  with players A and B, when A joins, both A's client and B's client run `ENTER CLIENTSIDE` with
  activator = A. Every such script needs an explicit
  `if (PlayerNumber() != ConsolePlayerNumber()) terminate;` guard as its first statement, or code
  meant for "the local player" silently runs against a remote one on every other client.
  `PlayerNumber()` is derived from the activator (`p_acs.cpp:12380-12389`); `ConsolePlayerNumber()`
  reads the local `consoleplayer` global (`p_acs.cpp:7163-7171`, `-1` on the server) and is the
  only reliable "is this actually me" check.
- **Consequence for `GetPlayerInput(-1, ...)` specifically:** `-1` resolves to *the activator's*
  player. Unguarded inside a broadcast `ENTER CLIENTSIDE`, that reads a remote player's button
  state on every client except the one they're actually on — and a remote player's full button
  bitfield generally isn't replicated to other clients at all (only `BT_ATTACK`/`BT_ALTATTACK` are
  synthesized into `cmd.ucmd.buttons` via `ServerCommands::MovePlayer::Execute`,
  `cl_main.cpp:4103-4110`; movement bits never are), so the read is close to garbage. With the
  `PlayerNumber() == ConsolePlayerNumber()` guard above, the activator *is* the local player and
  `GetPlayerInput(-1, ...)` works exactly as it would in any other locally-relevant clientside
  context.

## Server → client (sending data down)

A server-side script cannot directly call a `CLIENTSIDE` script's body — instead, calling
`ACS_ExecuteAlways` (or similar) on a `CLIENTSIDE` script from server code causes the engine to
tell the client(s) to run it there, with the same integer arguments passed through:

```text
script 900 (int data, int moredata, int evenmoredata) NET
{
    ACS_ExecuteAlways(901, 0, data, moredata, evenmoredata);
}

script 901 (int a, int b, int c) CLIENTSIDE
{
    Log(s: "The server sent us: ", d: a, s: " ", d: b, s: " ", d: c);
}
```

Integer script arguments transmit fine this way. **Per the wiki (not independently source-
verified in this pass — see Tier below): a string built with `StrParam()` does *not* survive
being passed this way**, which makes sending dynamic text to a `CLIENTSIDE` script harder than it
looks; treat any string argument crossing the server→client boundary as suspect until you've
tested it for your specific case.

### Relaying a server-side Log to one or all clients via a CLIENTSIDE relay script

[`Log`](../functions/log.md) has **no server→client networking at all** — a server-run `Log()`
call never reaches any client, only the server's own console (source-verified, see that doc).
Combined with the unverified-but-plausible `ACS_ExecuteAlways`-drops-strings caveat just above,
neither of the two obvious approaches gets a dynamic, server-computed message onto a specific
player's (or every player's) screen/console. The fix is a
**`CLIENTSIDE` relay script driven by [`NamedSendNetworkString`](../functions/sendnetworkstring.md)
instead of `ACS_ExecuteAlways`**:

```text
script "Log_To" (int string) CLIENTSIDE
{
    Log(s:string);
}

function void LogTo(int p_num, str msg)
{
    NamedSendNetworkString("Log_To", StrParam(s:msg), p_num);
}
```

This works, and reliably carries dynamic text, for a reason distinct from the `ACS_ExecuteAlways`
path above: `NamedSendNetworkString` doesn't pass a string as one of several plain integer script
arguments — it serializes the *actual string content* over the wire and re-inserts it into the
receiving client's own string table, then hands the script exactly one argument (the client's
freshly-assigned index into that table) — see the "string travels via the normal ACS
global-string-table mechanism" note in
[`SendNetworkString`](../functions/sendnetworkstring.md). `Log_To`'s `int string` parameter is
that reconstituted index, which `Log(s:string)` then formats as a string like any other `s:`
format item. No `NET` flag is needed on the receiving script for this direction — `NET` is only
checked when a `CLIENTSIDE` script pukes *up* to the server (see "Client → server" below);
server→client only requires the target be `CLIENTSIDE`.

**Generalizes directly to a broadcast variant with no new networking primitive** — per
`SendNetworkString`'s source-verified behavior, omitting the `client` argument (or passing a
negative one) doesn't mean "no target," it means **broadcast to every connected client**. A
sibling helper, `LogBold`, is `LogTo` minus the target — named by analogy with `Print`/`PrintBold`
even though — like the Zandronum engine fork's actual `PrintBold`, see
[`PrintBold`](../functions/printbold.md) —
it's visually identical to its non-broadcast sibling; "Bold" here means *wider delivery*, not a
distinct look:

```text
function void LogBold(str msg)
{
    // omit playernum arg to broadcoast to all clients
    NamedSendNetworkString("Log_To", StrParam(s:msg));
}
```

The existing `Log_To` receiver needs no changes to support this — it just runs once per
client, same as it already does for `ENTER`/`RESPAWN CLIENTSIDE` scripts (see above). A variant
with an actually distinct visual treatment would need a second relay script whose body calls
`PrintBold`/`HudMessage` instead of `Log`, reusing the exact same `NamedSendNetworkString`
delivery mechanism — the relay pattern is what solves "get a server-computed string to a
client," independent of which client-side print function ultimately displays it.

## A persistent CLIENTSIDE loop can be killed out from under you

A common pattern is an `ENTER CLIENTSIDE` script that starts an infinite per-tic loop meant to
outlive the triggering event — e.g. re-binding its own activator every tic with `SetActivator` so
it survives a death/respawn cycle rather than needing to be restarted. **This works for ordinary
death/respawn, but not for a player manually becoming a spectator and rejoining** — see the ENTER
entry in [Script types](script-types.md) for the full trace. Short version: `PLAYER_SetSpectator`
and `PLAYER_SpectatorJoinsGame` both call `FBehavior::StaticStopMyScripts` on the player's actor,
which hard-kills any script (including a `CLIENTSIDE` one) whose activator currently matches —
with **no code path for the dying script to run its own cleanup**. If that loop was guarded by a
"don't start a second one, I'm already running" boolean meant to survive re-triggering, that
boolean can never be reset, and the *next* legitimate `ENTER`/`RESPAWN CLIENTSIDE` invocation
(rejoining a manual spectate genuinely fires a fresh `ENTER`, not `RESPAWN`) sees the stale flag
and refuses to start a replacement loop — permanently, until the level ends.

**Fix: own the loop with a generation counter the newest invocation always claims, not a flag
the old instance is responsible for clearing:**

```text
int cl_loop_gen = 0;   // bumped and adopted by every fresh invocation, never reset elsewhere

script "MyLoop" (void) ENTER CLIENTSIDE
{
    if (PlayerNumber() != ConsolePlayerNumber()) terminate;

    cl_loop_gen++;
    int my_gen = cl_loop_gen;

    while (cl_loop_gen == my_gen)     // superseded (or the engine already killed the old
    {                                  // instance) -> this loop notices and exits on its own
        SetActivator(1000 + ConsolePlayerNumber());
        ...
        delay(1);
    }
}
```

Any prior instance — whether it's already dead from `StaticStopMyScripts` or, in the ordinary
death/respawn case, still alive and harmless — either doesn't exist to conflict, or notices the
generation mismatch on its next tic and exits cleanly. A `RESPAWN CLIENTSIDE` script that just
calls this same script again (the common "self-heal after respawn" idiom) is then always safe to
call unconditionally, since it always produces exactly one authoritative loop rather than
depending on whether the previous one happened to survive.

## Server→client script executions batched into one client tic run in REVERSE order

**Source-verified.** When the server runs a `CLIENTSIDE` script (via `ACS_ExecuteAlways`,
`ACS_NamedExecuteWithResult`, etc.), the client does not execute it at packet-parse time — it
creates a `DLevelScript` (`cl_main.cpp:7163-7193` → `P_StartScript` without `ACS_WANTRESULT`,
so no immediate `RunScript()`), which runs on the next `DACSThinker::Tick`. Two engine facts
combine into an ordering hazard:

- `DLevelScript::Link()` **prepends** the new script to the head of the thinker's script list
  (`p_acs.cpp:3831-3849`).
- `DACSThinker::Tick()` iterates that list **head→tail** (`p_acs.cpp:3602-3611`).

So all server-triggered clientside script instances that arrive within one client tic window run
**newest-first — the reverse of the order the server sent them** — even though the transport
itself delivers them reliably and in order (see Networking note below). Reversal applies within a
single packet (a 1024-byte default packet holds ~40 script-execute commands) and across every
packet parsed since the previous tick. Under normal latency, one server tic's commands usually
arrive alone, so only same-server-tic commands reverse; under lag/jitter/catch-up, several server
tics' worth of commands coalesce into one client tick and the whole batch reverses.

**Who this bites:** any mod that streams state to clients as a sequence of per-field absolute
writes via repeated clientside-script executions (the standard "item/inventory sync" pattern) and
assumes they apply in send order. If the same client-side location is written twice in one
coalesced batch, the *older* value wins and the client's copy stays wrong until the next resync —
a persistent, latency-dependent, client-visual-only desync that is impossible to reproduce in
singleplayer (where the puked script runs in the shared VM, or the sync path is skipped
entirely). A `Delay(1)` inside the receiving script pushes its write to the next tick and beats
LIFO for same-batch pairs, but *inverts* against instant writes arriving in the following tick —
it narrows the race, it doesn't close it.

**Robust patterns:**

- **Version/sequence-stamp the writes.** Have the server bump a small per-target version (spare
  bits of an existing packed argument are enough) each time it begins rewriting that target; the
  receiving script drops any write whose version is older than the last one applied to that
  target (wraparound-aware compare). Reversed application then converges to the newest value.
- **Client-side reorder queue.** Receiving scripts push `(seq, target, value)` into a clientside
  buffer; one persistent clientside loop drains it each tic in `seq` order. Restores total order
  with one added script.
- **Self-heal on view-open.** Re-send the full authoritative snapshot whenever the client opens
  the UI that displays the synced data — doesn't prevent the desync, but bounds its lifetime.

## Client → server (requesting data up)

There's no direct call in this direction — a `CLIENTSIDE` script asks the server to run a `NET`
script via `RequestScriptPuke`/`NamedRequestScriptPuke` (both real extension functions,
`zcommon.bcs:1755`/`1759`):

```text
script "DoAction" (void) NET
{
    if (!MayDoAction())
        terminate;
    if (CheckInventory("ActionDone"))
        terminate;          // double-execution guard
    DoServersideStuff();
    GiveInventory("ActionDone", 1);
}

script "RequestAction" (void) CLIENTSIDE
{
    while (ActionStillNeeded() && !CheckInventory("ActionDone", 1))
    {
        NamedRequestScriptPuke("DoAction");
        Delay(10);
    }
}
```

Two things worth internalizing from this pattern, both load-bearing for correctness:

- **A `NET` script is callable by anyone from the console** (`puke`/`pukename`), including
  players who never went through the intended `CLIENTSIDE` trigger path. Never trust data coming
  from a `NET` script's arguments as authoritative without validating it server-side — the wiki's
  own example guards with `MayDoAction()` for exactly this reason.
- **Client→server delivery isn't guaranteed** (unreliable channel — see Networking note below),
  so the idiom is: client repeatedly re-pukes until it observes (via an inventory flag or similar
  server-visible signal) that the server actually ran it, and the server-side script itself must
  be idempotent (the `CheckInventory("ActionDone")` guard) since it may receive the same puke more
  than once, or none at all without a retry loop.

## Networking note (server→client now source-verified; client→server still wiki-only)

**Server→client script activation is reliable and strictly ordered — source-verified 2026-08-09.**
`NetCommand` defaults to the reliable buffer (`_unreliable(false)`,
`network/netcommand.cpp:109/118`) and `ServerCommands::ACSScriptExecute::BuildNetCommand`
(`network/servercommands.cpp:11793-11812`) never calls `setUnreliable`, so script-execute
commands ride the reliable stream. The client parses reliable packets strictly in sequence — a
gap makes it buffer later packets and request the missing one (`cl_main.cpp:1144-1166`,
`1333-1402`); unrecoverable loss ends the session loudly rather than silently skipping: the
server kicks ("Too many missed packets", `sv_main.cpp:6169-6217`) or the client bails ("Missing
more than N packets. Unable to recover."). Consequence: **server→client clientside-script
executions are never silently dropped or transport-reordered — but see the LIFO execution-order
section above for how they still get *applied* out of order.** All four script arguments transmit
(`sv_commands.cpp:3567-3605`, `arg3` included since the command carries four `addVariable` slots).

The wiki describes client→server traffic (`RequestScriptPuke` etc.) as effectively unreliable;
that direction was *not* traced in this pass — keep the retry idiom above, which degrades
gracefully either way.

## Engine-family divergence

**`CLIENTSIDE` is non-functional on UZDoom — disabled, not absent.** Both engines parse the same
`SFLG` chunk bit (`0x0002`) with no validation of unknown bits — UZDoom's loader assigns the
16-bit flags word straight into the script record without masking or rejecting anything
(`src/playsim/p_acs.cpp:2887-2901`) — and UZDoom currently defines that
bit as `SCRIPTF_Ignored` with an explicit comment that it carries no meaning there (the UZDoom
source's `src/playsim/p_acs.h:332`) — see
[Zandronum/UZDoom compatibility](zandronum-uzdoom-compat.md) for the SFLG-level finding. A script
compiled with `CLIENTSIDE` for Zandronum loads cleanly under UZDoom and simply runs as an ordinary
server-side script: no per-client isolation, no local prediction exemption, nothing.

**Why that matters more than "the bit is ignored" suggests.** UZDoom does carry a structural
notion of a clientside ACS script, and that machinery is intact and live: a separate per-level
`ClientSideACSThinker` alongside the main `ACSThinker` (`src/g_levellocals.h:789`), a per-script
`bClientSide` field that selects between the two and is savegame-serialized
(`src/playsim/p_acs.cpp:3533,3550`), an ownership check that refuses to start a clientside script
whose activator belongs to a player other than the local console player
(`src/playsim/p_acs.cpp:653-660`), and both-thinker iteration in the string mark/lock,
`StopMyScripts`, and script-state paths (`src/playsim/p_acs.cpp:2034,2058,3364,10524`). What is
dead is its only entry point. `IsClientSideScript()` — the helper `P_GetScriptGoing` calls to
decide whether a newly-started script is clientside (`src/playsim/p_acs.cpp:10436`) — is
hard-coded to return `false` in the checked revision (`src/playsim/p_acs.cpp:664-667`). It
previously tested exactly this `0x0002` bit, under the name `SCRIPTF_ClientSide`, and was
deliberately switched off (commit "Disabled CLIENTSIDE ACS
scripts") because honouring the flag broke too many existing mods whose `CLIENTSIDE` scripts had
been running as ordinary scripts on UZDoom. Two consequences:

- **`ClientSideACSThinker` is never instantiated.** The sole `DLevelScript` construction site
  takes its `clientside` argument from `IsClientSideScript()` (`src/playsim/p_acs.cpp:10453`), so
  no code path can produce one. Anything documented as UZDoom being able to *reach* a clientside
  script instance — e.g. [`Acs_NamedTerminate`](../functions/acs_namedterminate.md)'s
  second-thinker lookup, which Zandronum structurally lacks — is reachable code searching a list
  that is always empty, for this same root cause.
- **Don't design around `CLIENTSIDE` returning.** The in-source note says the replacement will be
  a *new* flag matching UZDoom's own client-side model, not a revival of Zandronum's `CLIENTSIDE`
  semantics — so a script written to this page's patterns should not be expected to start working
  on a later UZDoom revision. UZDoom also has no client/server split for those semantics to attach
  to yet: the comment above the disabled check describes the clientside path as being kept
  deliberately identical between singleplayer and multiplayer in anticipation of a client/server
  mode that this engine does not have today (`src/playsim/p_acs.cpp:10434-10435`).

The non-functional flag breaks every pattern documented on this page, not just the flag check
itself.
`ConsolePlayerNumber` (the `PlayerNumber() != ConsolePlayerNumber()` guard this file recommends for
every broadcast `ENTER`/`RESPAWN CLIENTSIDE` script) and `RequestScriptPuke`/
`NamedRequestScriptPuke`/`NamedSendNetworkString` (the client-to-server puke idiom and the
server-to-client relay pattern) are all bound in Zandronum's reserved 100-199 ACSF range and
confirmed absent from UZDoom's own ACSF table, which skips straight from index 99 to
`ACSF_CheckClass = 200`, carrying Zandronum's 100-106 block only as a commented-out reservation
note telling future contributors not to reuse those indices (`src/playsim/p_acs.cpp:4824-4834`). A Zandronum-compiled object calling any of them
under UZDoom gets a silent `0` back instead of an error — `DLevelScript::CallFunction`'s `switch`
has no diagnostic default, it just falls through to `return 0`
(`src/playsim/p_acs.cpp:6874-6877`). `ConsolePlayerNumber()` therefore always reads as
`0`, so the activator guard above either always or never passes depending on which player number
the activator resolves to, and the puke/relay functions simply do nothing every time they're
called. None of this produces a log line or a crash; a script built around this page's patterns
just stops working as designed the moment it runs under UZDoom instead of Zandronum.
