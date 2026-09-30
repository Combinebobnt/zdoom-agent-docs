# Bots doc index

Router only. See `AGENTS.md` for scope, `../shared/AUTHORING.md` for tiers/engine-scope/licensing.

**Zandronum-only section** — UZDoom/GZDoom-family engines have neither `BOTINFO` parsing nor a
botscript interpreter.

**Looking for `ANCRINFO`, `AUTHINFO`, `CMPGNINF`, `GAMEMODE`, `MEDALDEF`, `SCORINFO`, `SECTINFO`,
`SKININFO`, or `VOTEINFO`?** Those eight other Zandronum-native lumps live in
[`zandronum-lumps/INDEX.md`](../zandronum-lumps/INDEX.md), not here.

## Concepts

- [The `BOTINFO` lump](concepts/botinfo-lump.md) — tier A. The bot declaration lump: full key
  table with per-key length caps, the additive multi-archive scan, the offset `-2..6` skill scale
  and its nine-value `BOTSKILL_e` mapping, the `intelect`/`intellect` alias, which malformed
  values are fatal vs. silently defaulted, the 8-character `script` cap, and loading a bot from a
  loose directory instead of an archive.
- [The compiled botscript lump format](concepts/botscript-lump-format.md) — tier B. The binary
  bytecode a bot's behavior is compiled to, for which no compiler exists anywhere: flat
  little-endian word stream with no header, absolute-byte-offset jumps, unpadded length-prefixed
  strings, the two 8-declared/7-usable stacks, state/section markers and their fatal runtime
  rules, the capacity limits, and the `ACS_NamedExecuteWithResult` bridge into ACS. Also the
  interpreter state that persists across tics — why `delay` suspends rather than restarts the
  enclosing loop, why an unbalanced section accumulates silently until it aborts (with the
  engine's own balance assertions commented out), state variables being per-state and
  unbounds-checked, and global events being matched before state-local ones.
- [What the bot A\* pathfinder can actually reach](concepts/bot-pathing-reachability.md) — tier B.
  The 64-unit grid search shared by every pathing command, and why its reachable set is not
  "wherever the pawn could walk": the floor-step test measures every candidate node against the
  pawn's live `z` rather than against the node the search climbed from, capping a whole search at
  `pawn_z + jumpheight` no matter how gradual the staircase. Covers how `jumpheight` is derived
  per pawn (and collapses to `MaxStepHeight` alone on a no-jumping map), why a confined bot never
  climbs out, and how to recognise the pattern from logged positions plus a floor-height dump
  without launching. Also: the grid's absolute 64-unit alignment and live (uncached) walk tests,
  the per-call search budget (counted in steps, not nodes) and when `PATH_INCOMPLETE` can occur,
  what lines/things/damaging sectors block a walk, a solid goal actor blocking its own goal point
  (and how far a "beside the target" goal must sit, plus a floor check, when the target stands on a
  grid corner), and a neighbour-expansion bug that never tries the north-west diagonal.

- [The bot chat file / chat lump format](concepts/bot-chat-file.md) — tier B. The sectioned text
  format the chat bot commands read: `chatfile` is a disk path beside the executable that no
  archive can carry, while `chatlump` resolves by short name or full archive path; two parsers
  (line-based for files, token-based for lumps, where unquoted words split into separate entries
  and `#` comments leak words); silent 64-section/64-entry limits and unbounded buffer copies;
  random line choice and the `NULL` sentinel; the eleven `$` placeholders and their prefix-match
  fall-through; the engine never starts chat itself (`chatfrequency` is script-read only); four
  stock `chatlump` targets absent from the source tree.

## Inventory tables (generated)

- [Bot commands](inventory/bot-commands.md) — every entry in `g_BotCommands[]`, 114 total.

## Notes (curated, per bot command)

- [ACS_Execute](notes/acs_execute.md) — fire-and-forget bridge into a numbered ACS script; `map`
  argument and fallback-to-current-map behavior.
- [ACS_ExecuteWithResult](notes/acs_executewithresult.md) — numbered-script, always-current-map,
  `ACS_ALWAYS|ACS_WANTRESULT` sibling of `ACS_Execute`.
- [ACS_NamedExecuteWithResult](notes/acs_namedexecutewithresult.md) — the only ACS-bridge command
  taking a script *name* instead of a number; `-FName()` resolution and its unknown-name failure mode.
- [GetItemName](notes/getitemname.md) — silent-empty-string-on-overflow behavior shared by every
  `RETURNVAL_STRING` command except `GetLastChatString`, the only one whose source is pre-truncated
  upstream.
- [LookForSuperArmor](notes/lookforsuperarmor.md) — one of a four-command family sharing a single
  handler with no class restriction at all; usable as a general net-ID scan channel since ACS has
  no way to obtain a net ID itself.
- [PathToGoal](notes/pathtogoal.md) — only 3 of the 4 `PATH_*` return values are reachable; never
  detects arrival at the goal. Speed is scaled by the pawn's `ForwardMove`/`Speed`, and the goal
  position is snapshotted at path reset, not tracked.
- [PathToLastHeardSound](notes/pathtolastheardsound.md) — unimplemented stub; always returns
  `PATH_UNREACHABLE` regardless of input.
- [PathToLastKnownEnemyPosition](notes/pathtolastknownenemyposition.md) — the only pathing command
  that can return all 4 `PATH_*` values, including `PATH_REACHEDGOAL`.
- [Roam](notes/roam.md) — self-perpetuating random-destination pathing; only 2 of the 4 `PATH_*`
  values are reachable.
- [SetEnemy](notes/setenemy.md) — takes a raw player index, not the `SETENEMY_LASTSEEN`/
  `SETENEMY_LASTSHOTBY` constants their names suggest (those are dead code, never referenced).
- [StringsAreEqual](notes/stringsareequal.md) — case-insensitive comparison; one of five
  0-int/2-string arity rows (the rest are chat file/lump commands); an unguarded `sprintf` copy ahead of its own overflow check.

## Not yet documented

- **`BOTEVENT_e` and the event system** — the event ordinals a `DH_EVENT` block binds to, declared
  in `src/bots.h`. Deathmatch-shaped; no per-event semantics written up yet.
- **The bot A\* pathfinder**, beyond reachability — `src/astar.cpp`, reached from botscript via the
  `SetGoalTID` and `PathToGoal` commands. What limits its reachable set is now covered by
  [bot-pathing-reachability.md](concepts/bot-pathing-reachability.md), as are the node grid, the
  per-call search budget and the damaging-sector cost penalty; the rest of the cost model (turn
  penalty, heuristic weighting) and the path-smoothing pass are not.
