# `bool IsPlayerContestingControlPoint(int player, int point)`

**Tier:** A.
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `IsPlayerContestingControlPoint - Zandronum Wiki.html` (`_intake/`,
retrieved 2026-07-29, `https://wiki.zandronum.com/w/index.php?title=IsPlayerContestingControlPoint&oldid=2254`) + source-verified against `p_acs.cpp:5550,8059-8069`,
`sectinfo.h:61-70`, `domination.cpp:90-102,113-183,211-224`,
`p_interaction.cpp:3005-3022`, `zt-bcc/lib/zcommon.bcs:1813`. The wiki's prose description
("Returns whether the given player is currently contesting the given control point") is
accurate; only its parameter signature (`bool point`) is wrong, and it omits both the
silent-`false`-on-invalid-input behavior and the Domination-only-populates-`contesting` caveat
above.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (negative index, `p_acs.cpp`'s `ACSF_*`/`ASCF_*` switch).

Reads whether a player is currently one of the contesters of a Domination-gametype control
point (a `SECTINFO` "point" entry — same underlying data as `GetControlPointInfo`, see
`functions/getcontrolpointinfo.md` for the point-index/`SectorInfo.Points` background).
Extension function, `zcommon.bcs:1813` declares it at index `-185`
(`ACSF_IsPlayerContestingControlPoint`, the Zandronum source's `src/p_acs.cpp:5550`), implementation
is the `case ACSF_IsPlayerContestingControlPoint:` block at `p_acs.cpp:8059-8069`.

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

```text
if (IsPlayerContestingControlPoint(PlayerNumber(), 0))
    Log(s: "You are contesting the point.");
```

**Note on family grouping:** this function is closely related to `GetControlPointInfo` /
`SetControlPointInfo` (same `SectorInfo.Points` data, same Domination-only caveats) and could
arguably be consolidated into a `families/control-points.md` page alongside them instead of
living as a separate per-function file. This file was kept standalone per this batch's
instructions; a future pass may want to merge it into such a family file.

## Engine-family divergence

This function's ACSF index (185, per `zcommon.bcs:1813`'s `-185` binding above) falls inside the
100–199 range UZDoom's own ACSF enum reserves for Zandronum's extensions and implements none of —
see [Zandronum/UZDoom compatibility](../concepts/zandronum-uzdoom-compat.md) for the mechanism.
UZDoom's `CallFunction` dispatcher is a plain `switch` with `default: break;` falling through to
`return 0`; a Zandronum-compiled object calling this function under UZDoom gets a silent `0` back
with no error, no log line, and the script keeps running as if nothing happened.

Because the return value is a boolean, that silent `0` reads as `false` — "not contesting" — which
is already one of *three* ways this function legitimately returns `false` on Zandronum itself (an
invalid/spectating/bodyless player, an out-of-range `point`, or a non-Domination gametype all
silently produce the same result; see above). Under UZDoom the reserved-range miss becomes a
fourth, indistinguishable source of the same `false` — there is no error channel anywhere in this
function's contract, on either engine, so a UZDoom port has no observable signal that the call
never did anything.
