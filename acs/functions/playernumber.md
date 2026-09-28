# `int PlayerNumber(void)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** wiki page `PlayerNumber - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-28,
`https://zdoom.org/w/index.php?title=PlayerNumber&oldid=37556`) + source-verified (`p_acs.cpp:12380-12389`; Zandronum `DISCONNECT` start `p_interaction.cpp:3457-3460`, `d_net.cpp:650`; builtin registration confirmed at
`zt-bcc/src/builtin.c:258`). This is a ZDoom-wiki page, not Zandronum-wiki, but `PCD_PLAYERNUMBER`
is core base-ACS pcode present unchanged in Zandronum. The one engine difference is which
activator a `DISCONNECT` script gets (see body). The wiki's usage/return description holds as written; the `DISCONNECT`
interaction and the contrast with `ConsolePlayerNumber()` are this doc's source-verified addition,
kept consistent with `functions/consoleplayernumber.md`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Returns the player number of the script's **activator**, starting at 0. Base ACS compiler
builtin (`PCD_PLAYERNUMBER`, listed in `zt-bcc/src/builtin.c`'s `g_funcs[]`), implementation at
the Zandronum source's `src/p_acs.cpp:12380-12389`.

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
  (script has no activator at all, e.g. `OPEN` scripts) or
  `activator->player == NULL` (activator exists but isn't a player-controlled actor, e.g. a
  monster). The wiki's own example (`if (PlayerNumber() >= 0)`) relies on exactly this to detect
  non-player activators.
- **`DISCONNECT` scripts differ by engine.** On Zandronum the engine starts them with no activator
  at all (`p_interaction.cpp:3460`, `d_net.cpp:650` both pass `NULL`), so `PlayerNumber()` always
  returns `-1` there. They run offline and on the server only (the `NETWORK_InClientMode()` gate at
  `p_interaction.cpp:3457`); a `CLIENTSIDE` one is forwarded to clients by the server. On UZDoom
  (at `5a9b0ec511`) the leaving player's actor is the activator and the script runs immediately,
  before the engine clears that actor's player link (`g_game.cpp:1900-1904`), so `PlayerNumber()`
  returns the leaving player's number until the script's first delay and `-1` after it.
- **To know who left, read the script's argument.** Both engines pass the leaving player's number
  as the `DISCONNECT` script's first argument (`script N (int player) DISCONNECT`). Don't
  substitute `ConsolePlayerNumber()` (Zandronum-only, see `functions/consoleplayernumber.md`): it
  reads the `consoleplayer` global instead of the activator, so it returns `-1` on a server, the
  local player offline, and the receiving client's own number in a forwarded `CLIENTSIDE` script.
  None of those is the leaving player.
- Unlike `ConsolePlayerNumber()`, `PlayerNumber()` is plain base ACS — it works identically
  singleplayer, client, or server, since it never touches `NETWORK_GetState()`; its only failure
  mode is activator-shaped, not netcode-shaped.

**Example** (from the wiki — assigns each player a unique TID on join):

```text
script 5 ENTER
{
    Thing_ChangeTID(0, 1000 + PlayerNumber());
}
```

**Returns:** `int` — activator's player index (`0`-based), or `-1` if the script has no player
activator (including every Zandronum `DISCONNECT` script, which runs with no activator).
