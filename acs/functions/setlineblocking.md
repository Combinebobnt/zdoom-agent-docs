# `void SetLineBlocking(int lineid, int setting)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `SetLineBlocking - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`https://zdoom.org/w/index.php?title=SetLineBlocking&oldid=52803`) + source-verified against `p_acs.cpp:11441-11478`, `p_spec.cpp:281-288`,
`doomdata.h:118,143-146`, and `zt-bcc/lib/zcommon.bcs:21-22,70-76`/`src/builtin.c:54,202`. One
undocumented-by-wiki behavior found (out-of-range `setting` silently aliasing to
`BLOCK_CREATURES` via the engine's own `default:` case) plus one Zandronum-only addition (server
→ client flag replication); no outright wiki/fork contradiction on the five documented `setting`
values themselves.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.

Sets/clears the blocking-related line flags on every line sharing `lineid`, replacing whichever
blocking mode was previously set (not additive — each `setting` value maps to a fixed
flag *state*, not a flag to OR in). Compiler builtin (`PCD_SETLINEBLOCKING`,
the zt-bcc source's `src/builtin.c:54`/`:202`); implementation is `case PCD_SETLINEBLOCKING:` in
`DLevelScript::RunScript`'s main switch (the Zandronum source's `src/p_acs.cpp:11441-11478`).

- **Applies to every line with a matching ID, not just one.** `lineid` is looked up via
  `P_FindLineFromID(id, start)` (`p_spec.cpp:281-288`), a hash-chain walk (`lines[id %
  numlines].firstid`, then `.nextid`) that the engine loops over with `while ((line =
  P_FindLineFromID(STACK(2), line)) >= 0)` — so a map with several lines sharing the same Hexen
  line ID gets the setting applied to all of them in one call, same as most other line-ID-keyed
  specials. This is a literal `lines[i].id` match, not sector-tag-style "0 means something
  special" — line ID 0 just matches lines whose ID is literally 0.
- **`setting` selects one of five mutually-exclusive flag states**, each an unconditional
  clear-then-set of the relevant bits in `line.flags` (`doomdata.h:118,143-146` for the raw bit
  values) — not a bitwise OR of `setting` into the flags word:
  - `BLOCK_NOTHING` (0) — clears `ML_BLOCKING`, `ML_BLOCKEVERYTHING`, `ML_RAILING`,
    `ML_BLOCK_PLAYERS`. Also usable as Hexen-compatible `OFF` (`zcommon.bcs:22`, `OFF = 0`).
  - `BLOCK_CREATURES` (1) — clears the other three, sets `ML_BLOCKING` (blocks players and
    monsters, not projectiles/hitscans). Also usable as Hexen-compatible `ON` (`zcommon.bcs:21`,
    `ON = 1`). **This is also the `default:` case of the engine's `switch` — any `setting` value
    outside 0-4 silently falls through to the same behavior as `BLOCK_CREATURES`,** not an error
    and not a no-op. Undocumented by the wiki.
  - `BLOCK_EVERYTHING` (2) — sets `ML_BLOCKING|ML_BLOCKEVERYTHING` (blocks projectiles and
    hitscans too).
  - `BLOCK_RAILING` (3) — sets `ML_RAILING|ML_BLOCKING` (Strife railing emulation, per wiki).
  - `BLOCK_PLAYERS` (4) — sets only `ML_BLOCK_PLAYERS` (blocks players but not monsters).
  - The wiki's five constants and the `ON`/`OFF` Hexen-compatibility aliases are both confirmed
    real in `zt-bcc/lib/zcommon.bcs:70-76` (enum, in that same order) and `:21-22`, and the flag
    semantics for all five match the wiki's prose exactly — no divergence found there.
- **Zandronum-only netcode side effect, absent from the (singleplayer-descended) wiki page:**
  after updating a line, if the local instance is the network server
  (`NETWORK_GetState() == NETSTATE_SERVER`), the engine calls
  `SERVERCOMMANDS_SetSomeLineFlags(line)` per matching line (`p_acs.cpp:11471-11473`) to replicate
  the new flags to clients. No client-side gotcha beyond this — the call is a plain flag write on
  the server, replicated outward; nothing about it silently no-ops on a client the way some other
  Zandronum-clientside functions do.
- **Deprecation note carried over from the wiki, not independently re-verified here:** the wiki
  page states this function is deprecated upstream in favor of `Line_SetBlocking` and warns
  future GZDoom compatibility isn't guaranteed. That's an upstream-GZDoom concern; Zandronum
  (forked pre-deprecation) still implements `SetLineBlocking` as a normal, undeprecated
  compiler builtin with no engine-side warning/removal — it isn't going away in this codebase.
- No unusual failure/no-op behavior found: an id matching zero lines is simply a zero-iteration
  loop (no error), and the stack is popped (`sp -= 2`) unconditionally regardless of match count.
