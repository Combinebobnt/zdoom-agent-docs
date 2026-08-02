# `int ACS_ExecuteWithResult(int script [, int s_arg1, int s_arg2, int s_arg3, int s_arg4])`

Action special (index 84) that runs a numbered script synchronously on the current map and returns the result value the script sets via `SetResultValue`. Unlike `ACS_Execute`/`ACS_ExecuteAlways` (which return a simple bool start/fail signal), this function is the primary implementation for synchronous script execution with a result value — the named variant `Acs_NamedExecuteWithResult` forwards to this action special via the `NamedACSToNormalACS[]` dispatch table (`p_lnspec.cpp:86-95`).

**Bucket:** Action special (index 84 in the special table). Implementation: `FUNC(LS_ACS_ExecuteWithResult)` at the Zandronum source's `src/p_lnspec.cpp:1833-1851`, dispatched via `P_StartScript` with flags `ACS_ALWAYS | ACS_WANTRESULT | (optionally ACS_BACKSIDE)`.

**Tier:** A. **Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD). **Provenance:** wiki page `ACS_ExecuteWithResult - ZDoom Wiki.html` + source-verified against `p_lnspec.cpp:1833-1851`, `p_acs.cpp:9120-13050,13234-13288`.

---

## Parameters

- **`script`** — numeric script number (required). Must be an integer constant or variable containing the script ID. A nonexistent script number causes the call to fail (return `0`, with a console message).
- **`s_arg1`, `s_arg2`, `s_arg3`, `s_arg4`** — optional arguments passed to the target script, each with a default of `0` if omitted. Unlike `ACS_Execute` (which takes only 3 arguments), this function accepts **four arguments**, a capability unique among the non-result Execute variants.

## Return value

Returns an `int` — whatever value the target script passed to `SetResultValue()`:

- **If the script calls `SetResultValue` before any blocking statement (`Delay`, `TagWait`, `PolyWait`, `ScriptWait`, `Suspend`), the return value is exactly that set value.**
- **If the script never calls `SetResultValue` at all before terminating, the return value is `1`** (the default initialization, *not* `0`) — easy to mistake for a success boolean when it's an uninitialized default. This differs from `ACS_Execute`/`ACS_ExecuteAlways`'s `bool` semantics.
- **If the script blocks (calls `Delay`, `Suspend`, etc.) before calling `SetResultValue`, the return value is whatever `SetResultValue` had been set to at the moment it hit the blocking state** — the script continues later but `ACS_ExecuteWithResult`'s caller never sees the eventual result. This is a critical correctness trap: a script like `SetResultValue(1); Delay(1); SetResultValue(2);` will return `1`, not `2`.
- **If the script is not found, the return value is `0`** (with a console warning `"P_StartScript: Unknown ..."`). This return value collides with `SetResultValue(0)`, so unresolved script names and legitimate zero returns are indistinguishable by return value alone.
- **Clientside carve-out: when invoked server-side for a script flagged `CLIENTSIDE`, returns `false`/`0`** (not `true` like `ACS_Execute`/`ACS_ExecuteAlways`'s carve-out) without running anything server-side — clients receive the instruction via `SERVERCOMMANDS_ACSScriptExecute` and compute their own result, but the server has no way to observe what they computed (`p_lnspec.cpp:1842-1848`). This failure mode is silent and ambiguous because `0` is indistinguishable from a real `SetResultValue(0)`.

## Execution model

- **Runs synchronously, in-line, in the caller's own tic** — not deferred to next tic like `ACS_Execute`/`ACS_ExecuteAlways`. The `ACS_WANTRESULT` flag passed to `P_StartScript` causes it to call the script's `RunScript()` method directly instead of just scheduling it (`p_acs.cpp:13264-13266`).
- **Always executes on the current map** — the hardcoded `level.mapname` passed to `P_StartScript` means the deferred cross-map execution path (`addDefered` at `p_acs.cpp:13282-13285`) is unreachable for this special, even though `ACS_ALWAYS` is set in the flags. A script number referring to a *different* map's script is simply not found, and the call returns `0`.
- **Always spawns a fresh script instance** — the `ACS_ALWAYS` flag means any existing instance of the target script is left untouched; a new instance runs alongside the old one. An `ACS_Execute` call (without `ALWAYS`) would instead resume a suspended instance if one exists, but `ACS_ExecuteWithResult` never does that.
- **Activator context**: The calling actor (activator) is preserved and passed to the script. In `OPEN`/`ENTER`-style script contexts with no activator, the script receives `NULL` for its activator pointer.
- **Line context**: If the action special is invoked from a UDMF line special (not from bytecode), the line pointer and backside flag are captured in the created script instance and are readable via `GetLineSpecial()`/`LineSide()` (though `LineSide()` only returns meaningful values for actual line-originated scripts; `ACS_ExecuteWithResult` invoked from bytecode sets `backSide` to `false`).

## Known fork/wiki divergence

**ZScript section inapplicable:** The wiki page includes an extensive "Return values in ZScript" section covering boolean conversion, fixed-point division (0.0–1.0 as `16/65536`), string table lookups, and texture/color conversions. **This fork has no ZScript at all** — these conversions are a ZDoom 4.x+ feature absent from Zandronum. The same limitation applies to the ZScript `CallACS` example. Only the DECORATE `A_JumpIf(1 == ACS_ExecuteWithResult(...))` example is applicable here.

## Comparison to siblings

- **vs. `ACS_Execute` (index 80):** `Execute` limits the called script to 3 arguments, supports deferred cross-map execution, and can resume suspended scripts. `ExecuteWithResult` always runs locally and accepts 4 arguments, but only works synchronously with result return.
- **vs. `ACS_ExecuteAlways` (index 226):** `ExecuteAlways` returns a bool (start/fail signal only), supports cross-map deferred execution, and takes a mandatory `map` parameter. `ExecuteWithResult` takes no `map` parameter (always current map) and returns an int result.
- **vs. `Acs_NamedExecuteWithResult` (extension function):** The named variant is a thin wrapper around this action special that pre-resolves a script name (string) to a number before dispatching. See `families/script-execution.md` for shared traits, the blocking-result trap, and the opposite-polarity clientside carve-out compared to the named `Execute`/`ExecuteAlways` siblings.

## Example

From the wiki (adapted from ZScript pseudocode to plain ACS):

```acs
// Called script that computes a result
script "CheckPlayerClass" (void)
{
  if(CheckActorClass(0, "DoomPlayer"))
  {
    SetResultValue(0);
    terminate;
  }
  else if(CheckActorClass(0, "AlternateDoomPlayer"))
  {
    SetResultValue(1);
    terminate;
  }
}

// Caller checks the result
script "test" (void)
{
  int class_id = Acs_ExecuteWithResult(1);  // Script 1 is "CheckPlayerClass"
  if (class_id == 0)
  {
    Print(s:"Normal player class");
  }
  else if (class_id == 1)
  {
    Print(s:"Alternate player class");
  }
}
```

## Gotchas

- **Result value only valid before blocking.** A script that intends to return a result must call `SetResultValue()` *before* the first blocking operation, or the caller will get the partially-computed value. The wiki example (and most well-intentioned code) follows this pattern, but a script written with `SetResultValue()` *after* a `Delay()` will silently produce wrong results.
- **No way to distinguish errors.** A nonexistent script, a script that never calls `SetResultValue`, and a script that calls `SetResultValue(0)` all return `0`, with no way for the caller to tell which case occurred without additional side-channel communication (e.g. a global variable set by the called script).
- **Different than bool-returning variants' clientside behavior.** If you're migrating from `ACS_Execute`/`ACS_ExecuteAlways` to this variant and the scripts involved are `CLIENTSIDE`, your return-value semantics change: the bool variants return `true`, this variant returns `0`.
