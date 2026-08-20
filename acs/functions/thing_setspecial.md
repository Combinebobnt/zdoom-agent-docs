# `int Thing_SetSpecial(int tid, int special, int arg0, int arg1, int arg2)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `Thing_SetSpecial - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29, `https://zdoom.org/w/index.php?title=Thing_SetSpecial&oldid=23145`) + source-verified against the Zandronum source (`p_lnspec.cpp:1050-1079`, `p_acs.cpp:11525-11555` for the `SetThingSpecial` builtin comparison, `sv_main.cpp:2896-2907` for the sync-scope finding) and `zt-bcc/lib/zcommon.bcs:1482` / `zt-bcc/src/builtin.c:92,240` (for `setthingspecial`'s builtin signature). The wiki's parameter list, the "only sets 3 args" claim, and the "use `SetThingSpecial` instead" pointer all hold and are confirmed by reading the actual assignment statements; the always-`true` return, the `tid=0`-no-activator no-op, and the no-live-replication netcode gap are this doc's source-verified additions, none of which the wiki page mentions. `LS_Thing_SetSpecial` is present verbatim in `cf11cbdb3` (a pre-SVN-import directory-restructuring commit, the oldest form of this file in this checkout's history), so it necessarily predates the 3.2.1 version-string commit (`28f736fb3`) by a wide margin; confirmed via `git merge-base --is-ancestor cf11cbdb3 28f736fb3`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** action special (positive index).
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Action special (`LS_Thing_SetSpecial`, index 127 in `zcommon.bcs`), implementation at
the Zandronum source's `src/p_lnspec.cpp:1050-1079`. Overwrites a matching actor's `special` line-
special number and the **first three** of its five `args` slots — `args[3]`/`args[4]` are left
untouched, whatever they were before. `tid=0` targets the calling script's activator (`it`)
instead of an iterator match.

```cpp
FUNC(LS_Thing_SetSpecial)	// [BC]
// Thing_SetSpecial (tid, special, arg1, arg2, arg3)
// [RH] Use the SetThingSpecial ACS command instead.
// It can set all args and not just the first three.
{
	if (arg0 == 0)
	{
		if (it != NULL)
		{
			it->special = arg1;
			it->args[0] = arg2;
			it->args[1] = arg3;
			it->args[2] = arg4;
		}
	}
	else
	{
		AActor *actor;
		FActorIterator iterator (arg0);

		while ( (actor = iterator.Next ()) )
		{
			actor->special = arg1;
			actor->args[0] = arg2;
			actor->args[1] = arg3;
			actor->args[2] = arg4;
		}
	}
	return true;
}
```

- **Only sets `args[0..2]`, exactly as the wiki says — but for a source-verifiable reason, not
  just a stated limitation.** The macro's `arg2`/`arg3`/`arg4` (the special's 3rd/4th/5th stack
  parameters) are written to `args[0]`/`args[1]`/`args[2]`; there is no `arg5` slot available to
  this special at all (its own `zcommon.bcs` signature only declares 5 total parameters:
  `tid, special, arg0, arg1, arg2`). `args[3]`/`args[4]` on the target actor are left at whatever
  they already were — not zeroed, not touched. The wiki's own text points at the fix: the
  **`SetThingSpecial` compiler builtin** (`PCD_SETTHINGSPECIAL`, the Zandronum source's `src/
  p_acs.cpp:11525-11555`) is confirmed present in the Zandronum engine fork and does set all five `args` slots —
  it takes the same `tid`/`special` plus all 5 args and additionally supports ZDoom's
  named-script (`ACS_NamedExecute`-family) special-number encoding. That builtin is a separate
  function from this one and isn't documented further here.
- **Always returns `true`, unconditionally, regardless of outcome.** Unlike `Thing_Activate`/
  `Thing_Deactivate` (see `../concepts/activation.md`), which return `count != 0`, every path through
  this function — the `tid=0`-with-`it==NULL` no-op, the `tid=0`-with-valid-activator case, and
  the iterator loop whether or not it matches anything — falls through to the same `return true;`
  at the end. There is no way to detect "no activator," "tid matched nothing," or "successfully
  updated N actors" from the return value; the wiki page doesn't mention a return value at all
  despite `zcommon.bcs` declaring `:int`.
- **`tid=0` silently no-ops with no activator**, same failure shape as the always-`true` return
  above: an `OPEN` script (no activator) or any other context where `it == NULL` calling
  `Thing_SetSpecial(0, ...)` does nothing at all, but still reports success.
- **No client notification when this changes an already-synced actor's special/args.** Unlike
  `Thing_ChangeTID` (`p_lnspec.cpp:1081` onward, in the same file), which calls
  `SERVERCOMMANDS_SetThingTID` immediately after the change, `LS_Thing_SetSpecial` calls no
  `SERVERCOMMANDS_*` function at all. The only place `SERVERCOMMANDS_SetThingSpecial` is invoked
  anywhere in the engine is `sv_main.cpp:2907`, during a *newly connecting* client's initial full
  actor-state sync — and even there it's gated to actors that are `IsKindOf("SectorAction")` **and**
  `NETWORK_IsClientPredictedSpecial(special)` or spectator-allowed. In practice: calling
  `Thing_SetSpecial` on an actor already visible to already-connected clients updates the
  server's copy of `special`/`args[0..2]` with no live replication to those clients at all — fine
  for specials that only need to be true server-side (the server executes the special locally when
  triggered), but a client that needs to *predict* the special locally (the `SectorAction` case
  the sync code exists for) will only ever see the value that was set *before* that client
  connected, not a live update.

**Returns:** `int`, but always `1`/`true` in every code path (see above) — cannot be used to
detect whether an activator existed, whether the `tid` matched anything, or whether anything
actually changed.

**Possible family:** This function, `Thing_ChangeTID` (`functions/thing_changetid.md`, if
written), and `Thing_Deactivate`/`Thing_Activate` (`../concepts/activation.md`) are all `Thing_*`
action specials operating on TID-tagged actors, processed in the same intake batch by sibling
agents, and may be worth consolidating into a `families/thing-tid-ops.md` at some point. Per this
batch's instructions, this file was kept standalone rather than folding into a family file —
flagging the overlap here for the coordinating session to consider.
