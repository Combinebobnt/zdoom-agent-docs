# ACS_NamedExecuteWithResult

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** written from the Zandronum source's `src/botcommands.cpp` (`botcmd_ACS_NamedExecuteWithResult`). No wiki page covers this command.

## Engine-family divergence

`ACS_NamedExecuteWithResult` is a bot command, not an ACS/BCS function — it lives in Zandronum's
bot-command dispatcher (`botcommands.cpp`), which UZDoom/GZDoom-family engines don't have at all.
There is no UZDoom counterpart to diverge from; see `../AGENTS.md`.

The named-script sibling of `ACS_ExecuteWithResult` — the only one of the three ACS-bridge bot
commands that takes a string argument. Call shape is
`ACS_NamedExecuteWithResult(scriptName, arg0, arg1, arg2, arg3)` — 4 int arguments plus 1 string
argument, `RETURNVAL_INT`.

- **`scriptName`** — the string argument, resolved to a script number via `-FName(scriptName)`
  (Zandronum's standard named-script encoding: a named script's internal number is the negation of
  its interned `FName` index). No validation that the name actually resolves to a real script —
  an unknown name still produces *some* negative number, which `P_StartScript` then fails to find
  (`FBehavior::StaticFindScript` returns null), printing `P_StartScript: Unknown <script>` and
  returning `false`/no result rather than erroring out.
- **`arg0`..`arg3`** — up to 4 script arguments, same slot count as `ACS_ExecuteWithResult`.
- Always targets the current map (`level.mapname`), same as `ACS_ExecuteWithResult` — there is no
  cross-map named-script bridge in this table (`ACS_Execute` is the only one with a `map`
  argument, and it only takes a numbered script).
- Runs with `ACS_ALWAYS|ACS_WANTRESULT`, identically to `ACS_ExecuteWithResult`: an already-running
  instance never blocks a new call, and the script's result value becomes this command's return.
- **Activator: the bot's own pawn.** The command calls `P_StartScript` with the bot player's `mo`
  as the activator, so the started script's `PlayerNumber()`/`ActivatorTID()` identify the bot.
  Scripts *that* script launches in turn (`ACS_*Execute*` from ACS) inherit whatever its activator
  is at that moment, so a failed `SetActivator` hop earlier in it hands them a NULL activator (see
  [SetActivator](../../acs/functions/setactivator.md)'s "Return value / failure behavior").

## Related

- `ACS_ExecuteWithResult` — identical shape (current map, 4 args, `ACS_ALWAYS|ACS_WANTRESULT`, int
  result) but targets a numbered script instead of a named one.
- `ACS_Execute` — the fire-and-forget, numbered-script, `map`-argument-taking sibling with no
  result and no `ACS_ALWAYS`.
