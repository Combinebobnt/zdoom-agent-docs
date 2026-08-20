# Exit_Secret

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
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
2. Otherwise, **falls back to `G_GetExitMap()`**, the normal non-secret exit map. Exit_Secret with no
   secret level defined silently becomes Exit_Normal.

If neither secret nor normal exit map is found (a configuration error), the fallback branches on
network state:

- **Singleplayer:** builds an end-sequence (`enDSeQ...`) and displays the end credits.
- **Server:** reloads the current map (`level.mapname`).

## Execution deferral

The exit is **not immediate**. `G_ChangeLevel` sets `gameaction = ga_completed` and returns; the
actual map change executes during `G_DoCompleted()` in the next tic. Any further ACS commands in
the same script execute (unless blocked by a `Delay` or `Terminate`) up to that boundary. To halt
the script immediately, place a `Delay(1)` or `Terminate` after the `Exit_Secret` call.

## Return value and gate conditions

The function returns `true` only if all exit gates pass and the exit queues successfully. It returns
`false` when any gate blocks the exit. However, `true` does not guarantee the level will change:

- A NULL/missing activator (e.g., `OPEN` script call) bypasses all gates and returns `true` without
  even evaluating them (see gate 1 below).
- `G_SecretExitLevel` has a redundant survival-countdown check *after* `CheckIfExitIsGood` passes
  (see gate 3) — so a NULL activator during countdown still returns `true` from the gate check but
  then fails the second check, and the exit never queues.
- `G_ChangeLevel` bails silently on `unloading` (console error printed) or `gameaction == ga_completed`
  (second exit in the same tic, no message) — both return values mislead by the time control reaches
  them.

**When the return value is `true`, it means the gate checks passed.** This is not the same as "the
exit will happen," but it is reliable: if you see `false`, a gate blocked the exit and side effects
already happened (activator was killed or teleported).

## Gate conditions: CheckIfExitIsGood

Before calling `G_SecretExitLevel`, the function checks `CheckIfExitIsGood(activator, ...)` — a
gate that controls all exit-family functions (Exit_Normal, Exit_Secret, Teleport_NewMap,
Teleport_EndGame). Multiple failure conditions apply:

### 1. Activator missing or NULL

**The activator is `null` in an `OPEN` script or when called from the world** (e.g., as a line
special with no thing activating it). `CheckIfExitIsGood` opens with:

```c
if (self == NULL)  return true;
```

So `OPEN` and world-activator cases bypass all exit gates below. Player-activated calls (via
linedef or explicit script call with a player activator) apply all gates.

### 2. DF_NO_EXIT (deathmatch, teamgame, alwaysapplydmflags)

If set and the map is not a lobby, the function **kills the activator**:

```c
P_DamageMobj(self, self, self, TELEFRAG_DAMAGE, NAME_Exit)
return false;
```

This is a real state change (the activator dies), not just a return-value signal. **Not mentioned by
the ZDoom wiki.**

### 3. Survival mode countdown

During the survival-countdown phase, exit is blocked:

```c
|| (survival && SURVIVAL_GetState() == SURVS_COUNTDOWN)
```

If triggered, also kills the activator with `TELEFRAG_DAMAGE`. This gate is checked twice — once in
`CheckIfExitIsGood` and again in `G_SecretExitLevel` before calling `G_ChangeLevel`. This is not
redundant: it is the only gate that stops a NULL-activator call (e.g., from an `OPEN` script,
which bypasses all other checks via the short-circuit at gate 1). The first check would return
`true` on NULL; the second check still fires and prevents the exit.

### 4. DF2_KILL_MONSTERS (cooperative only)

In cooperative mode with this flag and monster count below `sv_killallmonsters_percentage` %, the
activator is **teleported back to a random cooperative spawn spot**, not killed:

```c
P_Teleport(self, spot->x, spot->y, ONFLOORZ, ...);
NETWORK_Printf("You need to kill %d percent of the monsters before exiting the level.\n", ...);
return false;
```

This is a **Zandronum-specific survival mechanic**, absent from ZDoom and its wiki. Particularly
relevant to coop horde mods.

### 5. Hub map, same cluster, activator dead (singleplayer)

In a hub-mode map (MAPINFO `cluster` with `Hub` flag), if exiting to another map in the same
cluster while the activator is dead, the exit is blocked. This is a singleplayer-only gate
(`NETWORK_GetState() == NETSTATE_SINGLE`).

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
  message. It's also checked *before* `DF_NO_EXIT` rather than after, though that ordering has no
  observable effect since both gates simply return `false`.
- **No network-state fallback split on a missing exit map.** `GetSecretExitMap()` falls back from the
  secret map to the normal next map exactly like Zandronum's singleplayer branch, but if that next
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
