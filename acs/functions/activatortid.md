# `int ActivatorTID(void)`

Returns the TID of the script's activator. Compiler builtin (`PCD_ACTIVATORTID`,
the zt-bcc source's `src/builtin.c:111`/`:259`), implementation in `DLevelScript::RunScript`'s main
switch (the Zandronum source's `src/p_acs.cpp:12414-12423`).

**Bucket:** compiler builtin.

- No parameters.
- **If the script has no activator (`activator == NULL`), this returns `0`**, not a sentinel
  or an error — `p_acs.cpp:12415-12418`: `if (activator == NULL) PushToStack(0); else
  PushToStack(activator->tid);`. The wiki page doesn't mention this case at all; it only shows an
  example where the activator is a player. `0` here is genuinely ambiguous: it's indistinguishable
  from an activator that legitimately has TID `0` (the common "no TID assigned" default for most
  actors, since TIDs must be assigned explicitly via `Thing_ChangeTID`/`ACS_NamedExecute` args/etc.)
  — same "silent zero, no way to tell which case" shape as `GetActorProperty`'s failure path (see
  `functions/getactorproperty.md`).
- **When does `activator` end up `NULL`?** Confirmed from `../concepts/script-types.md`'s per-type
  verification: **`OPEN`** scripts are world-activated with no activator at all
  (`g_game.cpp:3294`, `p_spec.cpp:1796/1800`) — `ActivatorTID()` in an `OPEN` script always returns
  `0` for this reason, not because the activator happens to have TID 0. Line/sector specials
  triggered by non-actor sources (e.g. certain scripted/world-driven triggers) can likewise leave
  `activator` unset. Scripts genuinely triggered by a player or monster crossing a line, using it,
  dying, etc. do have a real activator pointer and behave as the wiki describes.
- The wiki's example pattern (`Thing_ChangeTID(0, 999)` in an `ENTER` script to tag the player,
  then `ActivatorTID() == 999` elsewhere to test "is this activator that player") is valid and
  matches this fork's `Thing_ChangeTID`/TID-zero-means-activator convention — but only works
  because `ENTER` scripts do have a real player activator, unlike `OPEN`.

**Example — safe pattern that accounts for the no-activator case:**

```
script "Check_Activator" (void)
{
    int tid = ActivatorTID();
    if (tid == 0)
    {
        // Either activator has TID 0, or there is no activator at all
        // (e.g. this got called from an OPEN-style/world-driven path).
        // Don't assume "no activator" vs "activator with TID 0" from this alone.
    }
}
```

**Provenance:** wiki page `ActivatorTID - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-28,
`oldid=38982`) + source-verified against `p_acs.cpp:12414-12423`, `builtin.c:111/259`, and this
tree's own `../concepts/script-types.md` for the OPEN-script no-activator case. No wiki/fork
discrepancy found beyond the wiki simply omitting the NULL-activator behavior.
**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.
