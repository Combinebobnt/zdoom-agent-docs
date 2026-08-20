# GetInvasionState

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-07)
**Provenance:** `GetInvasionState - Zandronum Wiki.html` (intake, `https://wiki.zandronum.com/w/index.php?title=GetInvasionState&oldid=1289`), verified against Zandronum source (`src/p_acs.cpp:11277–11283`, `src/invasion.h:60–70`, `src/invasion.cpp:1271–1274`) on 2026-08-07.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

```text
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

## Engine-family divergence

`GetInvasionState` is a base PCD opcode (`PCD_GETINVASIONSTATE`, index 130), not a CALLFUNC/ACSF
extension — a different name space from the 100–199 reserved-and-silent CALLFUNC range most other
Zandronum-only functions fall into (see
[Zandronum/UZDoom compatibility](../concepts/zandronum-uzdoom-compat.md)). UZDoom's interpreter
has no `case` for this opcode at all, so a Zandronum-compiled object calling it under UZDoom hits
UZDoom's unknown-PCD path: the interpreter prints `"Unknown P-Code %d in %s"` naming the script
and **terminates that script outright** — loud and fatal, the opposite failure mode from the
silent-0 return most other Zandronum-only functions produce (including this function's sibling
`GetInvasionWave`, index 129, same failure mode). There is no return value or `IS_*` constant to
misread because the script never continues past the call.
