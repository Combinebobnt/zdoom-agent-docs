# Exit_Secret

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** `Exit_Secret - ZDoom Wiki.html` (https://zdoom.org/w/index.php?title=Exit_Secret&oldid=44668), verified 2026-07-29 against the Zandronum source's `src`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

`int Exit_Secret(int pos)`

## Bucket

Action special, index 244 in `zcommon.bcs`'s `special` table — `LS_Exit_Secret` in `p_lnspec.cpp:858`.

## Parameters

- `pos` — map-editor `arg0` value of a player start spot that becomes the respawn point when the
  secret level loads. Multiple player starts can share the same `arg0`; the engine's usual
  player-distribution logic applies.

## Map selection and fallback

`G_GetSecretExitMap()` determines the target map:

1. If `level.secretmap` is defined in MAPINFO and the lump exists (verified via `P_CheckMapData`),
   that map loads.
2. Otherwise, **falls back to `G_GetExitMap()`**, the normal non-secret exit map (which itself honors
   map rotation, `DF_SAME_LEVEL`, a failed campaign map and the lobby cvar). Exit_Secret with no
   secret level defined silently becomes Exit_Normal. A valid secret map, by contrast, is taken
   directly and skips those `G_GetExitMap()` rules.

If the resulting map name is empty, `G_ChangeLevel` branches on network state:

- **Not a server (singleplayer or a non-server multiplayer state):** keeps an existing
  `enDSeQ...` next-map, otherwise builds the game's default end sequence.
- **Server:** reloads the current map (`level.mapname`), since the server doesn't support end
  sequences.

## Execution deferral

The exit is **not immediate**. `G_ChangeLevel` sets `gameaction = ga_completed`, runs `UNLOADING`
scripts synchronously (inside the `Exit_Secret` call), tells clients about the map exit when it is
the server, and returns. The actual map change starts in `G_DoCompleted()` at the top of the next
tic's `G_Ticker`, before `P_Ticker` runs scripts. Any further ACS commands in the same script
execute (unless blocked by a `Delay` or `Terminate`) up to that boundary. To halt the script
immediately, place a `Delay(1)` or `Terminate` after the `Exit_Secret` call; a delayed script
does not resume before the level ends.

## Return value and gate conditions

The function returns `true` whenever `CheckIfExitIsGood` passes, whether or not the exit then
actually queues. It returns `false` when a gate blocks the exit. So `true` does not guarantee the
level will change:

- A NULL/missing activator (e.g., `OPEN` script call) bypasses all gates and returns `true` without
  even evaluating them (see gate 1 below).
- `G_SecretExitLevel` repeats the survival-countdown check *after* `CheckIfExitIsGood` passes
  (see gate 3). A NULL activator during countdown therefore returns `true` from the gate check,
  then fails the second check, and the exit never queues.
- `G_ChangeLevel` returns without exiting while `unloading` is set (it prints a red "Unloading
  scripts cannot exit the level again." message) or when `gameaction == ga_completed` already (a
  second exit in the same tic, no message). The special still returns `true` in both cases.

**When the return value is `true`, it means the gate checks passed.** This is not the same as "the
exit will happen." If you see `false`, a gate blocked the exit. Side effects may or may not have
happened: the `DF_NO_EXIT` and survival gates deal telefrag damage, the kill-monsters gate teleports
a player activator (not a monster), and the hub-dead gate has no side effect.

## Gate conditions: CheckIfExitIsGood

Before calling `G_SecretExitLevel`, the function checks `CheckIfExitIsGood(activator, ...)`, a
gate shared by the exit-family specials (Exit_Normal, Exit_Secret, Teleport_NewMap,
Teleport_EndGame). Multiple failure conditions apply. The numbering below is by topic, not by
evaluation order: the code tests gate 1, then gate 4, then gates 2 and 3 (one combined condition),
then gate 5. So a player below the kill percentage in coop is teleported by gate 4 even when
`DF_NO_EXIT` or the survival countdown would otherwise have fired.

If every gate passes in a non-singleplayer game (and no exit is already queued), it prints
"<name> exited the level." for a player activator.

### 1. Activator missing or NULL

**The activator is `null` in an `OPEN` script or when called from the world** (e.g., as a line
special with no thing activating it). `CheckIfExitIsGood` opens with:

```c
// The world can always exit itself.
if (self == NULL)
	return true;
```

So `OPEN` and world-activator cases bypass all exit gates below. Calls with a non-NULL activator
(a player or monster via linedef, or a script with an activator) apply all gates.

### 2. DF_NO_EXIT (deathmatch, teamgame, alwaysapplydmflags)

If set and the map is not a lobby, the function deals **telefrag-magnitude damage to the
activator** (normally fatal) and fails:

```c
P_DamageMobj (self, self, self, TELEFRAG_DAMAGE, NAME_Exit);
return false;
```

This is a real state change, not just a return-value signal. `TELEFRAG_DAMAGE` only skips
`+INVULNERABLE`, god mode and buddha, so `+DORMANT`, damage factors, protection powerups and a
damage event script can still leave the activator alive. **Not mentioned by the ZDoom wiki.**

### 3. Survival mode countdown

During the survival-countdown phase, exit is blocked. This is the second half of gate 2's condition:

```c
     || (( survival ) && ( SURVIVAL_GetState( ) == SURVS_COUNTDOWN ))
```

If triggered, it also deals `TELEFRAG_DAMAGE` to the activator. This gate is checked twice: once in
`CheckIfExitIsGood` and again in `G_SecretExitLevel` before calling `G_ChangeLevel`. The second
check is not redundant. It is the only gate that stops a NULL-activator call (e.g., from an `OPEN`
script, which bypasses all other checks via the short-circuit at gate 1). The first check would
return `true` on NULL; the second check still fires and prevents the exit.

### 4. DF2_KILL_MONSTERS (percentage threshold in cooperative only)

The exit fails when all of these hold: the flag is set, not every monster is dead, the killed
percentage is below `sv_killallmonsters_percentage` (default 100), and the game mode is
cooperative. If the
activator is a player, it is first **teleported back to a random cooperative spawn spot**, not
killed:

```c
P_Teleport (self, pSpot->x, pSpot->y, ONFLOORZ, ANG45 * (pSpot->angle/45), true, true, false);
NETWORK_Printf( "You need to kill %d percent of the monsters before exiting the level.\n", *sv_killallmonsters_percentage );
```

A non-player activator (e.g. a monster crossing an exit line) just gets `false`. Outside
cooperative modes the flag does not block the exit at all on Zandronum. The percentage cvar, the
coop-only restriction and the teleport are Zandronum additions; the flag itself exists on
UZDoom too (see Engine-family divergence below). Particularly relevant to coop horde mods.

### 5. Hub map, same cluster, activator dead (singleplayer)

In a hub-mode map (MAPINFO `cluster` with `Hub` flag), if exiting to another map in the same
cluster while the activator is dead, the exit is blocked with no side effect. This is a
singleplayer-only gate (`NETWORK_GetState() == NETSTATE_SINGLE`).

## Wiki vs. Zandronum: map source degradation

Per the ZDoom wiki, Exit_Secret loads the secret map "defined for this map in MAPINFO." The wiki
further states (per the wiki sources) that "on standard Doom 1 maps, ZDoom will only use this special
on maps E1M3, E2M5, E3M6 and E4M2. In Doom 2, only maps MAP15 and MAP31 will be affected by its use."
This is a MAPINFO/level-data claim and is out of scope to verify here.

## Engine-family divergence

UZDoom (GZDoom-family) implements the same `LS_Exit_Secret` → `CheckIfExitIsGood` → `SecretExitLevel`
→ `GetSecretExitMap` shape as Zandronum, but several of the Zandronum-specific gate details above
don't carry over:

- **No survival-mode countdown gate.** UZDoom has no "survival" gametype, so gate 3 (the
  countdown block, including its NULL-activator-only second check inside the secret-exit function)
  doesn't exist at all.
- **DF2_KILL_MONSTERS behaves very differently.** UZDoom's version is unconditional (not restricted
  to cooperative play), compares monster counts for exact equality (`killed_monsters !=
  total_monsters`) rather than a percentage threshold cvar, and on failure just returns `false` with
  no side effect — it does not teleport the activator to a spawn spot and prints no percentage
  message. Both engines check it before `DF_NO_EXIT`.
- **No network-state fallback split on a missing exit map.** `GetSecretExitMap()` falls back from the
  secret map to the level's plain next map (Zandronum's goes through `G_GetExitMap()`), but if that next
  map is also empty, `ChangeLevel` always takes the end-sequence path — there is no equivalent to
  Zandronum's server-only "reload the current map" branch, since UZDoom's `ChangeLevel` has no
  client/server split at all.
- **Hub-dead check tests `!multiplayer`** in place of Zandronum's `NETWORK_GetState() ==
  NETSTATE_SINGLE` — the same intent (singleplayer only), phrased against UZDoom's own state model.
- **Repeat-exit-in-the-same-tic can be allowed.** `ChangeLevel` gates on `gameaction == ga_completed`
  same as Zandronum, but only bails if the `COMPATF2_MULTIEXIT` compat flag is *not* set — an added
  escape hatch Zandronum's version doesn't have.

## Sibling functions

`Exit_Normal` shares the identical `CheckIfExitIsGood` logic and differs only in map source
(`G_GetExitMap()` vs. `G_GetSecretExitMap()`). `Teleport_EndGame` uses the same gate on a different
failure path. The three should ideally be documented together as a family covering the exit-gate
semantics once, but that consolidation is deferred to the coordinating session's serial work.
