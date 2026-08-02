# `int ConsolePlayerNumber(void)`

Returns the local machine's player number — only meaningful in `CLIENTSIDE` scripts. Extension
function (`ACSF_ConsolePlayerNumber`, index -102 in `zcommon.bcs`), implementation at
the Zandronum source's `src/p_acs.cpp:7163-7171`.

**Bucket:** extension function.

```cpp
case ACSF_ConsolePlayerNumber:
{
    // [BB] The server doesn't have a reasonable associated player.
    if ( NETWORK_GetState( ) == NETSTATE_SERVER )
        return -1;
    else
        return consoleplayer;
}
```

- **`-1` on the server** — gated on `NETWORK_GetState() == NETSTATE_SERVER` specifically (one of
  four states: `NETSTATE_SINGLE`, `NETSTATE_SINGLE_MULTIPLAYER`, `NETSTATE_CLIENT`,
  `NETSTATE_SERVER`, `network.h:270-279`), i.e. only a dedicated/listen server. Singleplayer and
  client states both fall through to the local-player branch.
- **Otherwise returns the global `consoleplayer`** (`doomstat.h:122`, defined `g_game.cpp:202`,
  "player taking events") — a persistent slot index, unrelated to any script's activator actor.
- **Why this differs from `PlayerNumber()` in a `DISCONNECT` script** (per the wiki's note that
  `ConsolePlayerNumber()` keeps working there while `PlayerNumber()` doesn't): `PlayerNumber()` is
  a *different*, base-ACS builtin (`PCD_PLAYERNUMBER`, `p_acs.cpp:12380-12389`) that derives the
  number from the activating actor instead of a free-standing global:
  ```cpp
  case PCD_PLAYERNUMBER:
      if (activator == NULL || activator->player == NULL)
          PushToStack (-1);
      else
          PushToStack (int(activator->player - players));
      break;
  ```
  During disconnect the activator's `player` link can already be torn down, so `PlayerNumber()`
  returns `-1`. `ConsolePlayerNumber()` never touches `activator` — it just reads `consoleplayer`,
  which nothing in this code path resets — so it keeps returning the last valid value. This is an
  inference from the two functions' differing data sources (confirmed by source), not a directly
  documented guarantee about the disconnect sequence itself — treat it as reliable but don't
  assume the exact disconnect-ordering internals were traced further than this.

**Example:**

```
Script 1 (void) NET CLIENTSIDE
{
    PrintBold(s: "My player number is ", d: ConsolePlayerNumber());
}
```

**Returns:** `int` — local player's number, or `-1` if called on a server.

**Provenance:** wiki page `ConsolePlayerNumber - Zandronum Wiki.html` (`_intake/`, retrieved
2026-07-28, `oldid=1353`) + source-verified (`p_acs.cpp:7163-7171,12380-12389`, `network.h:270-279`,
`doomstat.h:122`, `g_game.cpp:202`). The wiki's -1-on-server and DISCONNECT-persistence claims
hold; the actual mechanism (global read vs. activator-derived in `PlayerNumber()`) is this doc's
source-verified addition. **Engine:** Zandronum 3.2.1 (verified against the Zandronum source
`master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.

**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.
