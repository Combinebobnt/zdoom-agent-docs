# `int Exit_Normal(int pos)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `Exit_Normal - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=Exit_Normal&oldid=44667`), verified 2026-07-29 against the Zandronum source's `src/p_lnspec.cpp`, `p_spec.cpp` (`CheckIfExitIsGood`), and `p_mobj.cpp` (`P_SpawnMapThing`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Action special, index 243 in `zcommon.bcs`'s `special` table.

Exit the current level, moving to the next map defined in MAPINFO, and spawn the player at a player start whose `arg0` matches `pos`.

## Parameters

- `pos` — player start spot identifier. The engine searches the map for player start things (type 1-4, i.e. player spawn points) whose `arg0` field matches `pos`, and only those player starts are made available for spawning on the next map. **The fallback behavior when no player start with matching `pos` is found was not traced; treat this as an edge case to avoid.**

## Return value

`int` (called as an action special, so `1` on success, `0` on failure per the declared signature). However, **`true` does not guarantee the level will actually exit:**

- **`false` return cases** (player or script receives immediate failure signal):
  - Activator is not NULL and `DF2_KILL_MONSTERS` is set and insufficient monsters are dead — in cooperative only, the activator is teleported back to a random player start instead (not the requested exit).
  - Activator is not NULL and deathmatch/teamgame/`alwaysapplydmflags` is true and `DF_NO_EXIT` is set — activator takes **TELEFRAG_DAMAGE** (1000000 raw damage, instant death) instead of exiting; fork-specific to Zandronum.
  - Activator is not NULL and the `survival` mode's countdown is running (`SURVIVAL_GetState() == SURVS_COUNTDOWN`) — activator takes TELEFRAG_DAMAGE instead, fork-specific to Zandronum.
  - In singleplayer hub mode: activator is dead, next map is in the same cluster, and the map has the `CLUSTER_HUB` flag set.
  - Activator is NULL and `info` (the next level) does not exist (`FindLevelInfo()` returned NULL).
  - Activator is NULL and `info` is not NULL but is not part of a valid cluster (rare, structural map error).

- **`true` return but exit still does not happen:**
  - `unloading` flag is set (an `UNLOADING`-type script is running; such scripts cannot trigger map exits). `G_ChangeLevel` returns silently.
  - `gameaction` is already set to `ga_completed` (a level change is already in progress). `G_ChangeLevel` returns silently.
  - A `CLIENTSIDE` script calls this during level load/transition (technically the activator can be NULL and exit-blocked via `CheckIfExitIsGood`, but a CLIENTSIDE script can't call action specials server-side anyway).

## Special behavior notes

- **Exit is deferred.** Setting the action special does not immediately exit the level; instead, it sets `gameaction = ga_completed`, which causes the engine to transition to the next level at the end of the current tic. Any subsequent ACS commands in the same script **continue executing** until the first `Delay` or `terminate` call. To halt the script immediately at the exit, either make `Exit_Normal` the last command or follow it with `terminate;` or `Delay(1);`.

- **Zandronum divergences not on the ZDoom wiki:**
  - The survival countdown check (`SURVIVAL_GetState() == SURVS_COUNTDOWN`) is Zandronum-specific and not mentioned on the ZDoom wiki. If either the deathmatch `DF_NO_EXIT` flag or this survival countdown gate is active and `CheckIfExitIsGood` returns `false`, the activator takes **TELEFRAG_DAMAGE** (instant death) rather than silently failing.
  - The fork includes a `DF2_KILL_MONSTERS` percentage gate that only applies in cooperative modes, with a Zandronum-specific teleport-back-to-start consolation behavior instead of a simple `false` return.

- **`CheckIfExitIsGood` applies to `Exit_Secret` and `Teleport_NewMap` identically** — all three action specials (243, 244, 74) share the same validation logic. `Exit_Normal` and `Exit_Secret` differ only in which MAPINFO field is consulted to find the next map (`nextmap` vs `secretmap`).

## Engine-family divergence: `DF2_KILL_MONSTERS` gate and `DF_NO_EXIT` conditions

UZDoom's `CheckIfExitIsGood` (`src/playsim/p_spec.cpp`) implements `DF2_KILL_MONSTERS` as a plain exact-kill gate: if `killed_monsters != total_monsters`, it returns `false` immediately, with no percentage threshold, no cooperative-only restriction, and no teleport-back-to-a-random-start consolation behavior. The percentage cvar and the teleport-back logic described above (under "false return cases" and "Zandronum divergences") are Zandronum-only additions not present in UZDoom at all — UZDoom has no equivalent of that cvar.

UZDoom's `DF_NO_EXIT` check also only tests `deathmatch || alwaysapplydmflags`, with no `teamgame` clause and no lobby-map exemption (both Zandronum-specific concepts absent from UZDoom); the TELEFRAG_DAMAGE consequence when it triggers is otherwise identical between the two engines. The survival-countdown gate remains Zandronum-only and is absent entirely from UZDoom's version, consistent with what's already noted above.

## Contract with scripts using `null` activators

If you call this as `ACS_ExecuteAlways(special, 0, ...)` with no activator (activator is the world), `CheckIfExitIsGood` **returns `true` immediately without checking game state or dmflags** — the null case is a blanket permission. This is sometimes exploited to force an exit that would otherwise be blocked (e.g., during a survival countdown). The cost is that the next map still won't load if `unloading` or `gameaction == ga_completed` is already true.

## Example

Exit to the next map, spawning at player start whose `arg0` is 0 (the first/default player start):

```text
script 1(void) {
    Exit_Normal(0);
    Print(s:"This prints (before the delay/tic end), then the map exits.");
    // Script halts at level transition, so no further code runs.
}
```
