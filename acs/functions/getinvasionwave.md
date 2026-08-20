# GetInvasionWave

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** Wiki intake `GetInvasionWave - Zandronum Wiki.html` (https://wiki.zandronum.com/w/index.php?title=GetInvasionWave&oldid=1290), verified against source 2026-07-29.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

## Bucket

Compiler builtin (`PCD_GETINVASIONWAVE`, `p_acs.cpp`), not an action special or extension
function. Declared in `zt-bcc/lib/zcommon.bcs`/`src/builtin.c` as `getinvasionwave` → `"i"`
(no arguments, returns int).

## Signature

```text
int GetInvasionWave(void);
```

## Behavior

- If the current game mode is not Invasion (`invasion == false`), always returns `-1` —
  matches the wiki.
- Otherwise returns `(LONG)INVASION_GetCurrentWave()`, i.e. the engine's internal
  `g_CurrentWave` counter (`src/invasion.cpp`).

## Wave numbering (not in the wiki)

`g_CurrentWave` is **0 before the first wave actually starts**, and becomes **1-indexed once
combat begins** — it is not "the wave about to start" or "waves completed", it's "the wave
currently being fought":

- During `IS_WAITINGFORPLAYERS` and `IS_FIRSTCOUNTDOWN` (waiting for players / the initial
  "Prepare for Invasion!" countdown before the first fight), `g_CurrentWave` is still `0`, so
  `GetInvasionWave()` returns `0`, not `-1` and not `1`.
- The instant wave 1 begins, the engine calls `INVASION_BeginWave(1)`, which sets
  `g_CurrentWave = 1` directly — so `GetInvasionWave()` reads `1` for the entire first wave,
  not `0`.
- Each subsequent wave transition calls `INVASION_BeginWave(g_CurrentWave + 1)`, so the value
  increments by exactly 1 per wave and matches the wave number a player would see on the HUD.

So a script polling `GetInvasionWave()` during the pre-game countdown will see `0`, not `-1`
(that only happens outside Invasion mode entirely) and not `1` (that only starts once the
first wave's monsters actually spawn).

## See also

- `GetInvasionState` (`functions/getinvasionstate.md`, if present) — companion Invasion-mode
  getter, documented separately. This page and that one are closely related (both read
  Invasion-gametype state) and may eventually belong in a shared `families/invasion.md` —
  left as two separate per-function files for now; not consolidated here.

## Engine-family divergence

`GetInvasionWave` is a base PCD opcode (`PCD_GETINVASIONWAVE`, index 129), not a CALLFUNC/ACSF
extension — a different name space from the 100–199 reserved-and-silent CALLFUNC range most
other Zandronum-only functions fall into (see
[Zandronum/UZDoom compatibility](../concepts/zandronum-uzdoom-compat.md)). UZDoom's interpreter
has no `case` for this opcode at all, so a Zandronum-compiled object calling it under UZDoom hits
UZDoom's unknown-PCD path: the interpreter prints `"Unknown P-Code %d in %s"` naming the script
and **terminates that script outright** — loud and fatal, the opposite failure mode from the
silent-0 return most other Zandronum-only functions produce. There is no return value to
misinterpret because the script never continues past the call; treat any script that polls
`GetInvasionWave()` as entirely non-portable to UZDoom, not merely "returns a wrong wave number."
