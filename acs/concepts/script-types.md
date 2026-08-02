# Script types

**Tier:** B (wiki-sourced concept page, spot-checked against fork source for the load-bearing claims — existence of each type, the `REOPEN` gap, the two spectator-interaction notes, the `UNLOADING` execution-mode claim, the `KILL`/`NOKILLSCRIPTS` nuance — but the `ACS_Terminate`/ `ENTER` interaction and the closed-script compiler grammar were not traced to source, so this doesn't qualify as tier A).
**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — a `3.3-alpha` development snapshot ahead of the 3.2.1 target; every `SCRIPT_*` type and call site checked here predates that gap and is unaffected by it — see "Engine scope" in `../../shared/AUTHORING.md`).
**Provenance:** wiki page `Script types - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-28, `oldid=50186`) + verified against the Zandronum source's `src/p_acs.h` (`SCRIPT_*` enum) and every `StaticStartTypedScripts(SCRIPT_*, ...)` call site across the Zandronum source's `src` (2026-07-28). The `ACS_Terminate`-vs-`ENTER` claim and the closed-script-grammar claim are wiki/observed-only, not traced through VM/parser source — see notes above. The `StaticStopMyScripts`-on-spectate finding under **ENTER** (added 2026-07-28) is fully source-verified (`p_interaction.cpp:2546,2781,2772`, `p_acs.cpp:3659-3679,13028-13030`).

What `SCRIPT_*` types actually exist in this fork, which of the ZDoom wiki's ten still apply,
and which of the fork's own types (`EVENT`, plus the `CLIENTSIDE`/`NET` flags) the wiki page
doesn't cover at all. Read this before assuming a ZDoom-documented script type "just works" here
— the wiki page enumerates ZDoom's evolving list, not this fork's.

## The authoritative list (from the Zandronum source's `src/p_acs.h:338-352`)

```
SCRIPT_Closed      = 0
SCRIPT_Open        = 1
SCRIPT_Respawn     = 2
SCRIPT_Death       = 3
SCRIPT_Enter       = 4
SCRIPT_Pickup      = 5
SCRIPT_BlueReturn  = 6
SCRIPT_RedReturn   = 7
SCRIPT_WhiteReturn = 8
SCRIPT_Lightning   = 12
SCRIPT_Unloading   = 13
SCRIPT_Disconnect  = 14
SCRIPT_Return      = 15
SCRIPT_Event       = 16   // [BB] — Zandronum's own addition, not a ZDoom script type
SCRIPT_Kill        = 17   // [JM] — Zandronum's own addition, not on the ZDoom page's list of ten
```

Every one of these has a real `StaticStartTypedScripts(SCRIPT_*, ...)` call site (verified by
grep across the Zandronum source's `src`), so none of them are dead enum values — **except
`SCRIPT_Lightning`, which does have a live call site** (`g_shared/a_lightning.cpp:192`), so scratch
that concern; every declared type in this list actually fires.

**`REOPEN` does not exist in this fork at all** — no enum value, no call site. If you're tempted
to use it because the ZDoom wiki lists it as one of the "special scripts," it will not compile as
a script type in `bcc`/this engine. This is the single most important divergence from the wiki
page: the page's own prose says "eight types are special" while its table lists ten — `KILL` and
`REOPEN` are later ZDoom additions bolted onto an older page. Zandronum picked up `KILL` (as
`SCRIPT_Kill`, independently, tagged `[JM]`) but never `REOPEN`.

`CLIENTSIDE` and `NET` are **not** script types — they're independent per-script flags
(`SCRIPTF_ClientSide` / `SCRIPTF_Net`, `p_acs.h:358-359`) that combine with any of the types
above (`script 1 OPEN CLIENTSIDE`). See [Client-side scripting](clientside-scripting.md) for that
flag's execution model. `EVENT` scripts have their own dedicated concept page — see
[EVENT scripts](event-scripts.md) — since the `(int type, int arg1, int arg2)` signature and the
`GAMEEVENT_*` enum are a family of their own.

`Pickup`, `BlueReturn`, `RedReturn`, `WhiteReturn` are real, called types (Hexen-style item pickup
and Skulltag/Zandronum CTF-flag-return hooks — `g_shared/a_teamitems.cpp:146,195`) that the ZDoom
wiki page doesn't document at all; out of scope for this pass, noted here only so their existence
in the enum isn't mistaken for dead/vestigial values.

## Per-type notes, verified against this fork

- **OPEN** — world-activated, runs once per level load. Confirmed callers: `g_game.cpp:3294`,
  `p_spec.cpp:1796/1800`. Matches the wiki: don't rely on an activator in an `OPEN` script.
- **ENTER** — player-activated, once per player per level. **Confirmed: spectators never trigger
  it** — `g_game.cpp:4286` and `p_mobj.cpp:5763` both gate the `StaticStartTypedScripts(SCRIPT_Enter, ...)`
  call on `bSpectating == false`. This matches the wiki's "In Skulltag, spectators never trigger
  an ENTER script" note, and it still holds in this fork.
  The wiki's claim that an infinite-loop `ENTER` script can't be stopped by the `ACS_Terminate`
  action special (only by the `terminate` keyword from inside the script) is plausible given how
  `ACS_Terminate` works (`p_lnspec.cpp:1866` → `P_TerminateScript` → `SetScriptState(...,
  SCRIPT_PleaseRemove)`, a state flag rather than an immediate kill) but **was not traced through
  the VM's instruction-stepping loop to confirm** — treat as unverified wiki claim, not confirmed
  fork behavior.
  **A genuine external kill *does* exist, though, and it's easy to hit if you write an
  `ENTER CLIENTSIDE` loop that re-binds its own activator every tic (e.g. via `SetActivator`) to
  outlive a normal death/respawn cycle** (found and source-verified 2026-07-28, building a
  clientside input-queueing feature in a real project): manually turning
  a player into a *true* (not dead) spectator via `PLAYER_SetSpectator(..., bDeadSpectator=false)`
  keeps their `mo` alive but calls `FBehavior::StaticStopMyScripts(pPlayer->mo)`
  (`p_interaction.cpp:2546`) — this hard-kills *every* script (`CLIENTSIDE` or not) whose
  `activator` is currently that actor, via `DACSThinker::StopScriptsFor` (`p_acs.cpp:3659-3679`)
  setting `SCRIPT_PleaseRemove` and unlinking the thread with **no further code execution** — the
  script gets no chance to run its own cleanup. `PLAYER_SpectatorJoinsGame()` (the native "rejoin"
  path back out of spectator mode) calls the same `StaticStopMyScripts` again
  (`p_interaction.cpp:2781`, comment: "otherwise they would get disassociated and continue to
  run") before setting `playerstate = PST_ENTERNOINVENTORY` — a `PST_ENTER`-family state, so
  **rejoining after a *manual* spectate fires a fresh `SCRIPT_Enter`, not `SCRIPT_Respawn`**,
  consistent with "spectators never trigger ENTER" above (once they stop being spectators, ENTER
  is exactly what fires for them again). Net effect: any state a `CLIENTSIDE` script kept in a
  boolean like "am I already running" to avoid double-starting on a re-entrant call **cannot be
  trusted to have been reset**, because the loop holding that state can be killed from outside
  with zero opportunity to reset it. Design ownership as a token/generation counter that a fresh
  invocation always overwrites, not a flag that requires the old instance to clean up after
  itself — see [Client-side scripting](clientside-scripting.md) for the pattern. (Dying and
  respawning normally, by contrast, does **not** go through this spectator path and does **not**
  call `StaticStopMyScripts` — a `CLIENTSIDE` loop that re-acquires its activator via `SetActivator`
  survives an ordinary death/respawn cycle untouched.)
- **RETURN** — confirmed real and hub-gated: `g_level.cpp:1993` only fires
  `StaticStartTypedScripts(SCRIPT_Return, ...)` inside a `level.clusterflags & CLUSTER_HUB` block,
  i.e. it only matters for maps using ZDoom-style hub clusters, same as upstream.
- **RESPAWN** — confirmed, `p_mobj.cpp:5803`, coop/multiplayer respawn.
- **DEATH** — confirmed, `p_interaction.cpp:742`, activator is the dying player.
- **LIGHTNING** — confirmed live, `a_lightning.cpp:192`. Not dead despite being rare in practice.
- **UNLOADING** — confirmed, `g_level.cpp:758`. The `always` parameter passed to
  `StaticStartTypedScripts` is `false`, which maps to the non-`ACS_ALWAYS` (i.e. `ACS_Execute`-
  equivalent, single-instance, blocking-capable) execution path — this directly confirms the
  wiki's claim that `UNLOADING` runs like `ACS_Execute` and not `ACS_ExecuteAlways`, and therefore
  can genuinely block itself from re-running next unload if it hasn't finished.
- **DISCONNECT** — confirmed, fired from `PLAYER_LeavesGame()` (`p_interaction.cpp:3447`, and
  `d_net.cpp:650` for the network-disconnect path). **Confirmed: also fires when a player becomes
  a true spectator**, not just on a real disconnect — `PLAYER_SetSpectator()`
  (`p_interaction.cpp:2463,2530`) calls `PLAYER_LeavesGame()` whenever `bDeadSpectator == false`.
  This matches the wiki's "In Skulltag, DISCONNECT scripts are also executed when a player turns
  into a spectator" note, and the EVENT-scripts page's own `GAMEEVENT_PLAYERLEAVESSERVER` note
  independently corroborates the same spectator-triggers-leave behavior from a different angle.
- **KILL** — confirmed, `p_interaction.cpp:503-507`. Condition is
  `!(flags7 & MF7_NOKILLSCRIPTS) && ((flags7 & MF7_USEKILLSCRIPTS) || gameinfo.forcekillscripts)`
  (`actor.h:354-355`) — **one nuance beyond the wiki**: the per-actor `NOKILLSCRIPTS` flag
  overrides `forcekillscripts` from `GameInfo`, i.e. an actor can opt out of `KILL` scripts even
  when the map/gameinfo forces them on globally. The wiki only documents the opt-in side.
- **REOPEN** — **does not exist in this fork.** See above.
- **Closed scripts** — must declare an argument list, even `(void)`. Not independently traced
  through the `zt-bcc` grammar in this pass, but real-world BCS code has been observed to be
  fully consistent with it (every closed script in the observed codebase declares `(void)` or real
  params, never a bare `script N { ... }`).
- **Net scripts** — the `net` keyword maps to `SCRIPTF_Net` (`p_acs.h:358`), independently
  confirmed — see [Client-side scripting](clientside-scripting.md).

## Authoring rule note

This page earns its cost specifically because the wiki page's type *list* is wrong for this fork
in both directions (missing `EVENT`/`KILL` as Zandronum-native additions on top of the ZDoom set,
wrongly including `REOPEN` which was never ported) — that's not a signature-only fact, it's a
"don't trust the enumerated list" correction.
