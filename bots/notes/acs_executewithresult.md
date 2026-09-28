# ACS_ExecuteWithResult

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** written from the Zandronum source's `src/botcommands.cpp` (`botcmd_ACS_ExecuteWithResult`). Result-value semantics from `src/p_acs.cpp` (`P_StartScript`'s `ACS_WANTRESULT` branch at 13264-13266, `resultValue`'s default at 9129, `PCD_SETRESULTVALUE` at 10461-10462). No wiki page covers this command.

## Engine-family divergence

`ACS_ExecuteWithResult` is a bot command, not an ACS/BCS function — it lives in Zandronum's
bot-command dispatcher (`botcommands.cpp`), which UZDoom/GZDoom-family engines don't have at all.
There is no UZDoom counterpart to diverge from; see `../AGENTS.md`.

The numbered-script sibling of `ACS_NamedExecuteWithResult`, and the result-returning sibling of
`ACS_Execute` — see both for the full 3-way comparison. Call shape is
`ACS_ExecuteWithResult(script, arg0, arg1, arg2, arg3)` — 5 int arguments, `RETURNVAL_INT`.

- **`script`** — a numbered ACS script. Unlike `ACS_Execute`, there is no `map` argument at all —
  this command always targets the current map (`level.mapname`).
- **`arg0`..`arg3`** — up to 4 script arguments (one more than `ACS_Execute`'s 3, since there's no
  `map` slot competing for stack space).
- Runs with `ACS_ALWAYS|ACS_WANTRESULT`: unlike `ACS_Execute`, an already-running instance of the
  same script does **not** block a new call — `ACS_ALWAYS` makes every call start its own fresh
  script instance regardless of what's already running — and the script's result value is passed
  straight back as this command's int return. That value is whatever the script last passed to
  `SetResultValue` (default `1`) by the time it first blocks or ends, because `ACS_WANTRESULT` runs
  the script inline only until its first `Delay`/wait. An unknown script number returns `0`.

## Related

- `ACS_Execute` — the fire-and-forget sibling: takes a `map` argument, only 3 script arguments, no
  `ACS_ALWAYS`/`ACS_WANTRESULT`, `RETURNVAL_VOID`.
- `ACS_NamedExecuteWithResult` — identical shape to this command (current map, 4 args,
  `ACS_ALWAYS|ACS_WANTRESULT`, int result) but targets a *named* script (one string argument)
  instead of a numbered one.
