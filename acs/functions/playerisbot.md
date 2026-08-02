# `bool PlayerIsBot(int playernumber)`

**Tier:** A
**Engine:** Zandronum 3.2.1 (checked against the Zandronum source's master/3.3-alpha snapshot)
**Provenance:** ZDoom Wiki (`PlayerIsBot`, `https://zdoom.org/w/index.php?title=PlayerIsBot&oldid=36026`), verified against fork source 2026-07-28.
**Bucket:** compiler builtin.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Returns whether a given player slot is a bot. Compiler builtin (`PCD_PLAYERISBOT`,
the zt-bcc source's `src/builtin.c:129,277`), implementation in `p_acs.cpp:12403-12412`.

- `playernumber` — a player slot index. **The wiki's "[0..7]" range is a ZDoom-era holdover and
  does not hold in Zandronum**: this fork raises `MAXPLAYERS` to `64`
  (the Zandronum source's `src/doomdef.h:57`), so the valid range for a Zandronum server is actually
  `[0, 63]`, not `[0, 7]`. Don't hardcode `8` as a loop bound when iterating players in this fork.
- **Out-of-range or empty slots are bounds-checked and fail closed, not undefined:** the actual
  case (`p_acs.cpp:12403-12412`) is
  ```cpp
  case PCD_PLAYERISBOT:
      if (STACK(1) < 0 || STACK(1) >= MAXPLAYERS || !playeringame[STACK(1)])
      {
          STACK(1) = false;
      }
      else
      {
          STACK(1) = players[STACK(1)].bIsBot;
      }
      break;
  ```
  So a negative index, an index `>= MAXPLAYERS` (64 here), or a slot with no connected player all
  silently return `false` rather than reading garbage or reporting a bot — this exact
  fail-closed behavior isn't mentioned by the wiki page at all, only the in-range case is.
- No Zandronum-specific spectator carve-out here (unlike `PlayerInGame`, which excludes
  spectators — `p_acs.cpp:12398-12399`): a spectating bot still reports `true` as long as its
  slot is in use, since `playeringame[]` doesn't care about spectator status.
