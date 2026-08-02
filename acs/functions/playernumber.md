# `int PlayerNumber(void)`

Returns the player number of the script's **activator**, starting at 0. Base ACS compiler
builtin (`PCD_PLAYERNUMBER`, listed in `zt-bcc/src/builtin.c`'s `g_funcs[]`), implementation at
the Zandronum source's `src/p_acs.cpp:12380-12389`.

**Bucket:** compiler builtin.

```cpp
case PCD_PLAYERNUMBER:
    if (activator == NULL || activator->player == NULL)
    {
        PushToStack (-1);
    }
    else
    {
        PushToStack (int(activator->player - players));
    }
    break;
```

- **Derived from the script's `activator` actor**, not from any free-standing global — it
  computes `activator->player - players`, i.e. the activator's index into the `players[]` array
  (`doomstat.h`).
- **Returns `-1` whenever there is no usable player activator**: either `activator == NULL`
  (script has no activator at all — e.g. most `OPEN` scripts) or `activator->player == NULL`
  (activator exists but isn't a player-controlled actor, e.g. a monster or the world). The wiki's
  own example (`if (PlayerNumber() >= 0)`) relies on exactly this to detect non-player activators.
- **Also returns `-1` in `DISCONNECT` scripts** (per the wiki) — during disconnect the activator's
  `player` link can already be torn down by the time the script runs, so the `activator->player ==
  NULL` branch is taken. See `functions/consoleplayernumber.md` for the direct contrast:
  `ConsolePlayerNumber()` is a *different*, Zandronum-added extension function
  (`ACSF_ConsolePlayerNumber`) that reads the persistent `consoleplayer` global instead of the
  activator, so it keeps returning a valid value in `DISCONNECT` scripts where `PlayerNumber()`
  has already gone to `-1`. Use `ConsolePlayerNumber()` (in a `CLIENTSIDE` script) when you need
  the local player's number independent of activator state; use `PlayerNumber()` when you
  specifically need "who/what activated this script."
- Unlike `ConsolePlayerNumber()`, `PlayerNumber()` is plain base ACS — it works identically
  singleplayer, client, or server, since it never touches `NETWORK_GetState()`; its only failure
  mode is activator-shaped, not netcode-shaped.

**Example** (from the wiki — assigns each player a unique TID on join):

```
script 5 ENTER
{
    Thing_ChangeTID(0, 1000 + PlayerNumber());
}
```

**Returns:** `int` — activator's player index (`0`-based), or `-1` if the script has no player
activator (including `DISCONNECT` scripts, where the activator's player link may already be torn
down).

**Provenance:** wiki page `PlayerNumber - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-28,
`oldid=37556`) + source-verified (`p_acs.cpp:12380-12389`; builtin registration confirmed at
`zt-bcc/src/builtin.c:258`). This is a ZDoom-wiki page, not Zandronum-wiki, but `PCD_PLAYERNUMBER`
is core base-ACS pcode present unchanged in this fork — no ZDoom-ahead-of-Zandronum divergence
found for this function. The wiki's usage/return description holds as written; the `DISCONNECT`
interaction and the contrast with `ConsolePlayerNumber()` are this doc's source-verified addition,
kept consistent with `functions/consoleplayernumber.md`. **Engine:** Zandronum 3.2.1 (verified
against the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.

**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.
