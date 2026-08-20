# `int ConsolePlayerNumber(void)`

**Tier:** A.
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-28)
**Provenance:** wiki page `ConsolePlayerNumber - Zandronum Wiki.html` (`_intake/`, retrieved
2026-07-28, `https://wiki.zandronum.com/w/index.php?title=ConsolePlayerNumber&oldid=1353`) + source-verified (`p_acs.cpp:7163-7171,12380-12389`, `network.h:270-279`,
`doomstat.h:122`, `g_game.cpp:202`). The wiki's -1-on-server and DISCONNECT-persistence claims
hold; the actual mechanism (global read vs. activator-derived in `PlayerNumber()`) is this doc's
source-verified addition.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Returns the local machine's player number — only meaningful in `CLIENTSIDE` scripts. Extension
function (`ACSF_ConsolePlayerNumber`, index -102 in `zcommon.bcs`), implementation at
the Zandronum source's `src/p_acs.cpp:7163-7171`.

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

```text
Script 1 (void) NET CLIENTSIDE
{
    PrintBold(s: "My player number is ", d: ConsolePlayerNumber());
}
```

**Returns:** `int` — local player's number, or `-1` if called on a server.

## Engine-family divergence

Bound as ACSF (CALLFUNC) index 102 — inside the 100–199 range UZDoom's own ACSF enum reserves
for Zandronum's extensions and implements none of. A Zandronum-compiled object calling
`ConsolePlayerNumber()` under UZDoom hits UZDoom's `CallFunction` dispatcher's `default: break;`
case: no error, no log line, the interpreter stack stays balanced, and the call just returns `0`
in place of the `-1`-on-server/`consoleplayer`-derived value documented above.

**This can look coincidentally correct in a narrow test.** In singleplayer, the console player's
number genuinely is `0`, so a script calling `ConsolePlayerNumber()` only in an SP context will
silently get the right answer under UZDoom even though the real logic above never runs — the
`-1`-on-server branch and the `consoleplayer` global read are both dead code on that engine.
Don't take a clean SP smoke test as evidence a Zandronum→UZDoom port is safe for this call; any
context where the console player isn't necessarily player 0 gets a wrong value with zero
diagnostic.

See [Zandronum/UZDoom compatibility](../concepts/zandronum-uzdoom-compat.md) for the general
reserved-ACSF-range silent-failure mechanism.
