# `int Timer()`

**Tier:** A.
**Engine:** Zandronum 3.2.1 (`PCD_TIMER` and all read/write sites above are original ZDoom-era code with no Zandronum-version-specific gating found — safe to stamp for 3.2.1, not just the checked-out `3.3-alpha` snapshot).
**Provenance:** wiki page `Timer - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29, `oldid=38125`) + source-verified against `p_acs.cpp:11321-11323` (`PCD_TIMER`), `p_tick.cpp:437-439` (per-tic increment of `time`/`maptime`/`totaltime`), `g_level.cpp:585` (`G_InitNew` reset), `g_level.cpp:1036` (`G_DoCompleted` non-hub reset), `g_level.cpp:1483` (per-load `maptime` reset), `g_level.cpp:2210-2243` (`G_SerializeLevel`, confirming `level.time` is excluded from hub snapshots), and the Zandronum-only `sv_commands.cpp:3892-3897` / `cl_main.cpp:7469-7487` client sync path. This is a ZDoom wiki page, so per the intake process it was checked for existence-first divergence — `PCD_TIMER` exists and behaves as described; the hub-vs-non-hub claim, which is easy to hand-wave past, was traced to the actual reset sites rather than trusted at face value. No feature-gap divergence found (a case where the ZDoom description holds), beyond the added Zandronum server→client sync behavior noted above.
**Bucket:** compiler builtin.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Returns the number of tics elapsed since a fork-defined epoch, as a plain ACS `int`. Compiler
builtin (`{ "timer", "i" }` in the zt-bcc source's `src/builtin.c:49`, opcode `PCD_TIMER`),
implementation in `p_acs.cpp:11321-11323`:

```cpp
case PCD_TIMER:
	PushToStack (level.time);
	break;
```

- Takes no arguments. Returns `level.time`, a tic counter (35 tics/sec, same units as `Delay()`)
  incremented once per world tic in `p_tick.cpp:437` — alongside, but **distinct from**,
  `level.maptime` (`p_tick.cpp:438`) and `level.totaltime` (`p_tick.cpp:439`), which increment on
  the exact same tics but reset on different rules (see below). There is no ACS-visible way to
  read `maptime`/`totaltime` directly; `Timer()` only ever exposes `level.time`.
- **Reset points for `level.time`** (searched all writes in the Zandronum source's `src`, not just
  the wiki's framing):
  - `G_InitNew` (`g_level.cpp:585`) — resets to `0` when an entirely new game is started (new
    single-player game, or a fresh `map`/`newgame`-style entry point), gated on
    `!savegamerestore`.
  - `G_DoCompleted`'s non-hub branch (`g_level.cpp:1036`, the `else` arm of "Forget the states of
    all existing levels", taken when the destination cluster is **not** a hub, or is a
    *different* hub than the one just left) — resets to `0` on every ordinary level transition.
  - **Deliberately not reset** when `G_DoCompleted` takes the hub-preserving branch (destination
    is the *same* hub, `!(level.flags2 & LEVEL2_FORGETSTATE)`) — that branch calls
    `G_SnapshotLevel()`/leaves `level.time` alone entirely. Confirmed by checking
    `G_SerializeLevel` (`g_level.cpp:2210-2243`, the function backing both snapshot and
    unsnapshot): its archive list is `flags, flags2, fadeto, found_secrets, found_items,
    killed_monsters, gravity, aircontrol, teamdamage, maptime, totaltime[, nextmusic]` —
    **`level.time` is never written to or read from a level snapshot at all.** So within a hub,
    `Timer()` isn't merely "preserved by save/restore" — it's a plain running counter that hub
    travel (`G_DoLoadLevel`) never touches, while `level.maptime` *is* explicitly reset to `0` on
    every load (`g_level.cpp:1483`) and then gets overwritten back to its saved value if
    `G_UnSnapshotLevel` restores a snapshot for that specific level (i.e. `maptime` is
    per-level-visit, `time` is whole-hub-session).
  - Net effect matches the wiki's framing exactly for this fork: on a map that isn't part of a
    hub, `Timer()` is time since that level started; on a hub map, it's time since the user
    started the current game (survives every level transition within the hub, including
    revisiting an earlier hub map).
- **Zandronum netcode addition absent from the ZDoom wiki:** the server treats `level.time` as
  authoritative and explicitly replicates it to clients via a dedicated command,
  `ServerCommands::SetMapTime` (`sv_commands.cpp:3892-3897`, `cl_main.cpp:7484-7487`:
  `SERVERCOMMANDS_SetMapTime` sends `command.SetTime(level.time)`; the client's
  `SetMapTime::Execute()` does a plain `level.time = time;`). A client does not free-run its own
  independent tic count that could drift from the server — it's overwritten with the server's
  value (e.g. on full-update/late-join). No equivalent mechanism exists or is needed in
  single-player ZDoom, so the wiki page has nothing to say about it.
- No failure/sentinel case — always returns a valid non-negative tic count (`0` right after a
  reset).

**Example — HUD stopwatch (from the wiki, minus its `HudMessage` syntax typo — the wiki's example
is missing a closing paren before the `;` argument separator):**

```
script 1 ENTER
{
	int t;
	while (TRUE)
	{
		t = Timer() / 35;
		HudMessage(d:t/60, s:":", d:(t%60)/10, d:t%10;
			HUDMSG_PLAIN, 1, CR_RED, 0.95, 0.95, 2.0);
		Delay(35);
	}
}
```
This only accumulates meaningfully across multiple maps if `MAPINFO` defines them as part of the
same hub cluster — on non-hub maps it just restarts at 0 on every level change, matching the
reset rules above.
