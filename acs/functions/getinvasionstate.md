# GetInvasionState

**Tier:** A
**Engine:** Zandronum 3.2.1 (opcode and behavior present verbatim since the original Skulltag 0.97c2 import commit `bc562a817` — this is not a recent addition, no 3.2.1-vs-3.3-alpha gate applies).
**Provenance:** `GetInvasionState - Zandronum Wiki.html` (intake), verified against the Zandronum source's `src` on 2026-07-29.

```
int GetInvasionState(void)
```

Compiler builtin (`PCD_GETINVASIONSTATE`, `p_acs.cpp`). Returns the current Invasion gametype
state machine value, or `-1` if Invasion is not the active gametype (checked via the global
`invasion` bool, same flag used throughout `gamemode.cpp`) — this matches the wiki exactly, no
fork divergence found.

Implementation is a two-line passthrough: `invasion == false ? -1 : INVASION_GetState()`
(`p_acs.cpp` case `PCD_GETINVASIONSTATE`), where `INVASION_GetState()` (`invasion.cpp`) just
returns the file-local `g_InvasionState` variable — no side effects, no filtering.

## Return value

Named `IS_*` constants are real, in `zcommon.bcs` (unlike some other Zandronum enums that only
exist as raw literals) — safe to use directly instead of magic numbers:

| Constant | Value | Meaning |
|---|---|---|
| `IS_WAITINGFORPLAYERS` | 0 | Lobby wait before the match starts |
| `IS_FIRSTCOUNTDOWN` | 1 | Initial pre-wave-1 countdown |
| `IS_INPROGRESS` | 2 | A wave is actively spawning/being fought |
| `IS_BOSSFIGHT` | 3 | Boss wave in progress |
| `IS_WAVECOMPLETE` | 4 | Wave cleared, brief pause before next countdown |
| `IS_COUNTDOWN` | 5 | Countdown between waves (not the first) |
| `IS_MISSIONFAILED` | 6 | All players out of lives / mission failed |
| (not Invasion gametype) | -1 | `invasion` global is false |

## See also

- `GetInvasionWave` (`functions/getinvasionwave.md`, if present) — the sibling extension
  function returning the current wave number instead of the state; **not documented in this
  file even though the two are closely related** — a sibling intake pass is handling it
  separately. If a `families/invasion.md` gets created later to cover both together, this file's
  content should fold into it.
