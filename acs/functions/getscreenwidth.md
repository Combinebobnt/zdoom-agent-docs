# `GetScreenWidth`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-07)
**Provenance:** ZDoom Wiki `GetScreenWidth` (https://zdoom.org/w/index.php?title=GetScreenWidth&oldid=37388, retrieved 2026-08-07) + original source-verified on 2026-08-05 against the Zandronum source's `src/p_acs.cpp:12425-12451` (PCD_GETSCREENWIDTH case handler) and the UZDoom source's `src/playsim/p_acs.cpp:9885-9892` (same case handler). Re-verified against wiki 2026-08-07.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin — `zt-bcc/src/builtin.c:113` (`{ "getscreenwidth", "i" }`, zero-arg, returns `int`), compiles to `PCD_GETSCREENWIDTH`. Not a `zcommon.bcs` `special`-table entry.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

## Syntax

```text
int GetScreenWidth(void);
int GetScreenHeight(void);
```

Documented together — same handler shape on both engines, differing only in which screen-size
field each reads.

## Warning: indeterminate feature

**⚠ Using `GetScreenWidth`/`GetScreenHeight` to modify playsim can break demo and multiplayer sync.** Reading the screen resolution is unsafe if the result controls anything that touches the random number generator, changes level geometry, spawns obstacles/monsters/powerups, or otherwise modifies the playsim state. Reading the resolution for HUD purposes (formatting messages, positioning overlays, scaling UI elements) is safe — the warning applies to the reading itself only when coupled with playsim changes.

The per-player variability of the return value is the underlying reason: even on Zandronum (where a server can query any connected player's real resolution via `SERVER_GetClient(...)->ScreenWidth`), each player reports their own screen size, and a playsim decision based on mismatched per-player data will desync. This is documented on the ZDoom wiki; the caveat applies equally to Zandronum and UZDoom.

## Wiki/engine divergence: Zandronum can query other players' resolutions

The ZDoom wiki states "GetScreenWidth only knows the resolution of the local session. Information about the resolution of other players in a game or demo does not exist." This holds for ZDoom and base-ACS engines where every script runs locally on the client that queries it. **On Zandronum, this is not a limitation**: a dedicated or listen server executing a script with a player activator can call `GetScreenWidth()`/`GetScreenHeight()` and retrieve that specific player's **real, live** screen resolution — the actual value that player's client last reported via network. This is explicitly documented in the Zandronum source code (`src/p_acs.cpp:12426-12427`), distinguishing the Zandronum fork from upstream ZDoom.

## Zandronum: works from a non-`CLIENTSIDE`, server-executed script, per-player

This is the finding worth writing down: on Zandronum, `GetScreenWidth`/`GetScreenHeight` do **not**
require a `CLIENTSIDE` script to get a real answer, contrary to what "the server doesn't have a
screen" (the handler's own comment) suggests at first read.

Zandronum `src/p_acs.cpp:12425-12451` (PCD_GETSCREENWIDTH case handler):

```cpp
case PCD_GETSCREENWIDTH:
    // [BC] The server doesn't have a screen.
    // [TP] But the server knows the clients' resolutions and can use that instead.
    if ( NETWORK_GetState( ) == NETSTATE_SERVER )
    {
        if ( activator && activator->player )
        {
            CLIENT_s *client = SERVER_GetClient( activator->player - players );
            PushToStack( client ? client->ScreenWidth : 0 );
        }
        else
        {
            PushToStack( 0 );
        }
    }
    else
    {
        PushToStack (SCREENWIDTH);
    }
    break;
```

(`PCD_GETSCREENHEIGHT` is the byte-for-byte same shape at `src/p_acs.cpp:12446-12468`, substituting `ScreenHeight`/`SCREENHEIGHT`.)

Three states, not two:

- **Server (dedicated or listen), with a player activator:** returns `SERVER_GetClient(...)->ScreenWidth`
  — that specific player's own **live, real** screen resolution, as reported by their client. This
  is what makes a non-`CLIENTSIDE` script with a player activator (an `ENTER`/`RESPAWN`/`DEATH`
  script, or any script whose activator is a player) a fully valid way to get a specific player's
  real resolution from server-executed code — no `CLIENTSIDE` conversion, no replication work
  needed.
- **Server, with no player activator** (e.g. a plain `OPEN` script, or any script whose activator
  is `NULL`/non-player): returns `0`. Not an error, not a fallback value pulled from anywhere —
  literally `0`. A caller that doesn't guard this will get a garbage-looking small resolution, not
  a crash or a diagnostic.
- **Not server** (a `CLIENTSIDE` script, or singleplayer/listen-server-local execution reaching this
  case on the client side of the split): returns the literal local `SCREENWIDTH`/`SCREENHEIGHT` —
  the executing machine's own real screen size, same as the player-activator server case would
  return for that same player, just reached via a different code path.

**Where the value comes from:** `CLIENT_s::ScreenWidth`/`ScreenHeight` (`sv_main.h`) are reset to
`0` on connect (`sv_main.cpp`) and populated by the client's `CLC_SETVIDEORESOLUTION` network
command (`sv_main.cpp`), sent by the client **both** at initial connect (explicitly commented in
the client source as being sent "for ACS scripting support") **and** again on every subsequent
resolution change the player makes in-game (`v_video.cpp`). So it is not a stale one-shot value
captured only at connect time — a player changing resolution mid-session updates it, modulo the
brief network-round-trip window between the change and the server receiving the update.

## UZDoom: no client/server split, always the local screen

UZDoom's `PCD_GETSCREENWIDTH`/`PCD_GETSCREENHEIGHT` handlers (`src/playsim/p_acs.cpp:9885-9892`,
GPL-3.0 — described here in prose rather than quoted, per `shared/AUTHORING.md`'s "Quoting
engine/compiler source verbatim") each unconditionally push the local `SCREENWIDTH`/`SCREENHEIGHT`
global. No branching at all — every call, from any script type, returns the literal local `SCREENWIDTH`/
`SCREENHEIGHT`. This is correct for UZDoom's execution model (every connected peer runs the full
simulation locally — there is no single server process executing scripts "for" other players the
way Zandronum's dedicated/listen server does), so a script reading its own `GetScreenWidth()` is
always reading the screen of whichever peer is currently running that script instance. No
`CLIENTSIDE` distinction changes this behavior on UZDoom.

## Practical consequence

A script that wants "the real resolution of the player this script is running for" should simply
call `GetScreenWidth()`/`GetScreenHeight()` with that player as the activator — this works
identically (mechanism aside) on both engines, and on Zandronum specifically does **not** require
converting the script to `CLIENTSIDE`. The one thing `CLIENTSIDE` still buys that this doesn't:
client-local-only cvars that aren't network-replicated (e.g. a player's manual aspect-ratio-related
video settings) aren't visible to a `GetScreenWidth`-based approach from a non-`CLIENTSIDE` script,
since it only returns the raw resolution, not any cvar-driven override layered on top of it by the
client's own rendering pipeline.

## Not independently re-verified here

Whether `activator->player - players` (the player-index arithmetic in the Zandronum handler) can
ever produce an out-of-range index for an unusual activator (a non-player actor with a non-NULL
`player` pointer, if that's even possible) wasn't traced — treated as safe by construction (`if
(activator && activator->player)` gates on both being set) but the invariant that guarantees a
valid index specifically wasn't chased into `AActor`'s own field semantics.
