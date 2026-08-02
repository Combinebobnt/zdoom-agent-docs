# Client-side scripting

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

```
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

```
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
even though — like this fork's actual `PrintBold`, see [`PrintBold`](../functions/printbold.md) —
it's visually identical to its non-broadcast sibling; "Bold" here means *wider delivery*, not a
distinct look:

```
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

```
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

## Client → server (requesting data up)

There's no direct call in this direction — a `CLIENTSIDE` script asks the server to run a `NET`
script via `RequestScriptPuke`/`NamedRequestScriptPuke` (both real extension functions,
`zcommon.bcs:1755`/`1759`):

```
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

## Networking note (wiki claim, not independently source-verified)

The wiki describes client→server traffic as effectively unreliable (UDP) and server→client
traffic for script-activation as a more reliable channel the engine layers on top ("RUDP"). This
plausibly explains the retry pattern above, but tracing the actual net-code
(`sv_commands.cpp`/`cl_demo.cpp`/`network.cpp`) to independently confirm the reliability
asymmetry was out of scope for this pass — treat the retry idiom above as safe regardless of
whether the exact reliability story is precisely as described, since it degrades gracefully if
delivery actually is reliable.

**Provenance:** wiki page `Client-side scripting - Zandronum Wiki.html` (`_intake/`, retrieved
2026-07-28, `oldid=1545`) + spot-verified against engine source for the `CLIENTSIDE`/`NET` script
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
verification (`p_acs.cpp:1818-1886`) — fully source-verified, not a wiki restatement. **Engine:**
Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — see "Engine scope" in
`../../shared/AUTHORING.md`). **Tier:** B (wiki + partial source spot-check, not exhaustive — see Tiers in
`../../shared/AUTHORING.md` for why this doesn't qualify as A).
