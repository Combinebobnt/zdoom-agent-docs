# `bool IsPlayerContestingControlPoint(int player, int point)`

Reads whether a player is currently one of the contesters of a Domination-gametype control
point (a `SECTINFO` "point" entry — same underlying data as `GetControlPointInfo`, see
`functions/getcontrolpointinfo.md` for the point-index/`SectorInfo.Points` background).
Extension function, `zcommon.bcs:1813` declares it at index `-185`
(`ACSF_IsPlayerContestingControlPoint`, the Zandronum source's `src/p_acs.cpp:5550`), implementation
is the `case ACSF_IsPlayerContestingControlPoint:` block at `p_acs.cpp:8059-8069`.

**Bucket:** extension function (negative index, `p_acs.cpp`'s `ACSF_*`/`ASCF_*` switch).

- `player` — a player index. Validated with `PLAYER_IsValidPlayerWithMo()`
  (`p_interaction.cpp:3018-3022`): **out-of-range index, a player slot not in the game, a
  spectator, or a player with no body (`mo == NULL`, e.g. between death and respawn) all
  silently return `false`** rather than erroring — there is no way to distinguish "not
  contesting" from "not a valid interactable player" from the return value alone.
- `point` — zero-based index into `level.info->SectorInfo.Points`, same array
  `GetControlPointInfo`/`SetControlPointInfo` use. **Out-of-range `point` also silently returns
  `false`** (`p_acs.cpp:8064-8065`), not an error.
- Return value: `level.info->SectorInfo.Points[point].contesting.count(pln) != 0`
  (`p_acs.cpp:8068`) — `contesting` is a `std::set<int>` of player indices
  (`DPOINT_s::contesting`, the Zandronum source's `src/sectinfo.h:66`).

## Wiki's parameter signature is wrong: `point` is not a `bool`

The wiki page gives the signature as `bool isPlayerContestingControlPoint (int player, bool
point)`. That's inconsistent with every other control-point function (`GetControlPointInfo`'s
`point` param is `int`, and `zcommon.bcs`'s own declaration for this function is
`(raw, raw):raw` — both params generic, neither pinned to `bool`) and with the implementation,
which reads `args[1]` straight into `const unsigned int point` and uses it as an array index
(`p_acs.cpp:8064`). Passing a literal `true`/`false` would just mean point index `1`/`0` — there
is no boolean semantics anywhere in this path. Treat `point` as `int`, same as the sibling
functions; the wiki's `bool` is very likely a copy/paste slip from a nearby boolean-returning
signature on the same wiki.

## `contesting` is populated only while Domination is the active gametype, but degrades safely

Unlike `GetControlPointInfo`'s `owner`/`disabled` fields (plain `int`/`bool` members left at
whatever `DPOINT_s`'s default construction happens to leave them outside Domination — see
`functions/getcontrolpointinfo.md`'s footgun section), `contesting` is a `std::set<int>`, which
default-constructs empty regardless of gametype. `DOMINATION_Tick()` — the only code that ever
inserts into it — starts with `if (!domination) return;` (`domination.cpp:114-115`), so on a
non-Domination gametype (or before the first tick) the set simply stays empty and this function
correctly returns `false` for every player/point pair. There's no uninitialized-garbage trap
here the way there is for `owner`/`disabled`, but the function is still only *meaningful* (i.e.
can ever return `true`) while Domination is active — a `SECTINFO` map played in another gametype
will report every player as not-contesting, which could be mistaken for "nobody's on the point"
rather than "contesting isn't tracked in this gametype."

Server computes `contesting` fresh every tick from actual player positions
(`DPOINT_s::PlayerInsidePoint`, counting only players with `bOnTeam` set and, if
`gameinfo.bAllowDominationContestScripts` is on, passing the `GAMEEVENT_DOMINATION_CONTEST` event
check — `domination.cpp:126-146`) and replicates changes to clients via
`SERVERCOMMANDS_SetDominationPointState` (`domination.cpp:213-224`), so reading this function
clientside reflects real state, not just server-local state.

**Example — check if the local player is contesting point 0 (Domination gametype only):**

```
if (IsPlayerContestingControlPoint(PlayerNumber(), 0))
    Log(s: "You are contesting the point.");
```

**Provenance:** wiki page `IsPlayerContestingControlPoint - Zandronum Wiki.html` (`_intake/`,
retrieved 2026-07-29, `oldid=2254`) + source-verified against `p_acs.cpp:5550,8059-8069`,
`sectinfo.h:61-70`, `domination.cpp:90-102,113-183,211-224`,
`p_interaction.cpp:3005-3022`, `zt-bcc/lib/zcommon.bcs:1813`. The wiki's prose description
("Returns whether the given player is currently contesting the given control point") is
accurate; only its parameter signature (`bool point`) is wrong, and it omits both the
silent-`false`-on-invalid-input behavior and the Domination-only-populates-`contesting` caveat
above. **Engine:** Zandronum 3.2.1 — the introducing commit (`c2eb5ab96`, "Add
IsPlayerContestingControlPoint function to test if a player is contesting a particular control
point", 2024-09-11) was confirmed via `git merge-base --is-ancestor` to predate the `28f736fb3`
("changed the version string to 3.2.1") commit in the Zandronum source's checkout, i.e.
it ships in 3.2.1, not just the checkout's `3.3-alpha` HEAD. **Tier:** A.

**Note on family grouping:** this function is closely related to `GetControlPointInfo` /
`SetControlPointInfo` (same `SectorInfo.Points` data, same Domination-only caveats) and could
arguably be consolidated into a `families/control-points.md` page alongside them instead of
living as a separate per-function file. This file was kept standalone per this batch's
instructions; a future pass may want to merge it into such a family file.
