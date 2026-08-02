# `int SetActorState(int tid, str statename, bool exact = false)`

Forces the actor(s) matching `tid` into a DECORATE state, found by label name. Compiler builtin
(`PCD_SETACTORSTATE`, the Zandronum source's `src/p_acs.cpp:12604-12652`), backed by
`FActorInfo::FindStateByString`/`FindState` (`p_states.cpp:274-317`) and `AActor::SetState`
(`p_mobj.cpp:502`).

**Bucket:** compiler builtin.

- `tid` — **`0` means "the activator"**, matching the same convention as `GetActorProperty` and
  other actor-targeting builtins. If `tid == 0` and there is no activator (e.g. called from a
  script type with no activating actor), the function silently does nothing and returns `0` —
  there's no NULL-activator crash here because the `0`-branch only touches `activator` inside an
  `if (activator != NULL)` guard (`p_acs.cpp:12609-12628`); the falls-through case leaves the
  return stack slot at its already-pushed value of `0`.
  For any other `tid`, it iterates **every** actor with that TID via `FActorIterator`
  (`p_acs.cpp:12631-12649`) and changes state on all of them, not just the first match.
- `statename` — a state label as defined in the actor's DECORATE (dot-separated for nested labels,
  e.g. `"Missile.Explode"`). Resolved through `FActorInfo::FindStateByString`, which supports the
  legacy compound death-state names (`"Burn"` → `Death.Fire`, `"Ice"` → `Death.Ice`,
  `"Disintegrate"` → `Death.Disintegrate`, `"XDeath"` → `Death.Extreme`) before falling back to a
  literal dotted lookup (`p_states.cpp:217-257`).
- `exact` (optional, defaults to `false` per `zt-bcc/src/builtin.c:151`'s `"i;is;b"` format string —
  everything after the second `;` is optional) — matches the wiki description and is verified
  against `FActorInfo::FindState` (`p_states.cpp:274-305`): the lookup walks the dotted label
  path one segment at a time and remembers the **last state found along the way** (`best`). If
  `exact` is false (or omitted) and the full path isn't found, the best partial match found so far
  is used instead (e.g. `"Foo.Bar"` falls back to `"Foo"` if `"Foo.Bar"` doesn't exist). If `exact`
  is true, any leftover unmatched segments (`count < numnames`) make the whole lookup return
  `NULL` — i.e. the actor's state is left unchanged — even if a shorter prefix matched. This
  confirms the wiki's description is accurate for this fork.
- **Return value** — the number of actors that actually changed state (0 or 1 for `tid == 0`, an
  arbitrary count for a shared `tid`), matching the wiki. If the state label doesn't resolve at
  all for a given actor (`FindState` returns `NULL`), that actor is simply skipped and not counted
  — there is no error/exception path, just an undercount.

## Side effect the wiki's "unpredictable results" warning is actually about

`AActor::SetState` (`p_mobj.cpp:502`) doesn't just flip a state pointer — it also resets `tics`
via `GetTics(newstate)` and, walking further down the function, **calls the new state's action
function immediately and synchronously**, inline in the same call, rather than waiting for the
actor's normal per-tic `think()`/`P_SetMobjState` cycle. For a monster still under AI control (its
`think()` still running `A_Chase` etc. on its own schedule), forcing a state change from ACS can
therefore invoke a state's action pointer at a point in the actor's lifecycle the DECORATE author
never expected (e.g. mid-attack, before `A_Chase` next runs), which is the concrete mechanism
behind the wiki's "refrain from using this for actors with monster AI" caution — this held up
against the fork's actual `SetState` implementation, not just wiki folklore.

## Zandronum-specific netcode note (not in the ZDoom wiki source)

On a listen/dedicated server (`NETWORK_GetState() == NETSTATE_SERVER`), every successful state
change triggers `SERVERCOMMANDS_SetThingFrame` to replicate the new frame to clients
(`p_acs.cpp:12617-12618`, `12641-12642`) — this is a Zandronum multiplayer addition with no
equivalent in the vanilla ZDoom wiki page this doc was sourced from.

**Provenance:** wiki page `SetActorState - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`oldid=36009`) + source-verified against `p_acs.cpp:12604-12652`, `p_states.cpp:217-317`,
`p_mobj.cpp:502-560`, `zt-bcc/src/builtin.c:151`. No wiki/fork behavioral divergence found beyond
the Zandronum-only netcode replication call noted above (an addition, not a contradiction).
**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.
