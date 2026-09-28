# LookForSuperArmor

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.
**Provenance:** written from the Zandronum source's `src/botcommands.cpp` (`botcmd_LookForItemWithFlag`, `BOTCMD_IgnoreItem`, `botcmd_ValidateItemNetID`), `src/thingdef/thingdef_data.cpp` (`STFL_*`), and `src/p_mobj.cpp` (net-ID assignment). No wiki page covers this command. Net-ID validation: `botcmd_LookForItemWithFlag`'s `unsigned short` cast (`botcommands.cpp:983`) and `botcmd_ValidateItemNetID`'s 65536 bound (`botcommands.cpp:843`).

## Engine-family divergence

`LookForSuperArmor` is a bot command, not an ACS/BCS function — it lives in Zandronum's bot-command
dispatcher (`botcommands.cpp`), which UZDoom/GZDoom-family engines don't have at all. There is no
UZDoom counterpart to diverge from; see `../AGENTS.md`.

Scans **upward** from a starting net ID and returns the first actor carrying `STFL_SUPERARMOR`, or
`-1` if none is found before the net ID space is exhausted. One of a family of four sharing a single
implementation, `botcmd_LookForItemWithFlag( pBot, Flag, FunctionName )`, differing only in which
`STFL_` bit they pass:

| Command | Flag |
| --- | --- |
| `LookForBaseHealth` | `STFL_BASEHEALTH` |
| `LookForBaseArmor` | `STFL_BASEARMOR` |
| `LookForSuperHealth` | `STFL_SUPERHEALTH` |
| `LookForSuperArmor` | `STFL_SUPERARMOR` |

(`LookForPowerups`/`LookForWeapons`/`LookForAmmo` are a *different* helper,
`botcmd_LookForItemType<T>`, which does restrict by C++ class.)

## Argument order is the reverse of the push order

Both arguments come off the stack inside the handler, newest first:

```c
bool visibilityCheck = !!alStack[lStackPosition - 1];  pBot->PopStack();
unsigned short netID = static_cast<unsigned short>( alStack[lStackPosition - 1] );  pBot->PopStack();
```

So `visibilityCheck` is popped **first** and `netID` second — meaning the caller must push
`startNetID` first and `visibilityCheck` second. Getting this backwards is silent, not an error:
the lump still assembles and the engine still runs, but the scan starts at whatever
`visibilityCheck` was (typically 0, which is never a valid net ID) and applies the visibility gate
according to what was meant to be the start ID.

The pushed start ID is cast to `unsigned short` before `botcmd_ValidateItemNetID` checks it
against 65536, so that check's fatal `I_Error` can never fire. An out-of-range value silently wraps
modulo 65536 and the scan starts wherever it lands. `SetGoal`/`GetItemName`/`IsItemVisible` share
the same cast-then-check convention.

## The scan imposes no class restriction — any actor with the flag matches

This is the non-obvious part, and it is what makes the family usable for things that are not items
at all. The loop is:

```c
while ( BOTCMD_IgnoreItem( pBot, netID, visibilityCheck ) ||
        (( g_ActorNetIDList.findPointerByID( netID )->STFlags & Flag ) == false ))
```

`BOTCMD_IgnoreItem` tests only three things: the net ID resolves to a non-NULL actor, that actor
has `MF_SPECIAL`, and — only when `visibilityCheck` is set — `BOTS_IsVisible` passes. There is no
`AInventory` cast, no `dynamic_cast`, and no `IsKindOf` anywhere on this path; the flag test reads
`->STFlags` straight off the `AActor`. So the full match predicate is exactly:

> has a net ID **and** `+SPECIAL` **and** the `STFL_` bit **and** (if checking) is visible

Any actor satisfying that matches, including one derived from `MapSpot`. Actors get a net ID
unless they set `+NONETID` or `+SERVERSIDEONLY` (`p_mobj.cpp`, at spawn), which `MapSpot` does not.

The NULL case is safe by short-circuit ordering, not by a check in the flag test:
`BOTCMD_IgnoreItem` returns true for a NULL pointer, so the `||` never evaluates
`findPointerByID(netID)->STFlags` on it.

### Consequence: the `STFL_` bits are usable as private scan channels

`STFL_SUPERARMOR` in particular is **set by no stock Zandronum actor** — it is defined in
`thingdef_data.cpp` and referenced by this scan, but nothing in `wadsrc/` or
`skulltag_actors.pk3` declares it. A mod can therefore put `+SUPERARMOR` on an actor of its own and
have `LookForSuperArmor` return that actor and nothing else, using the family as a general
"find my actor's net ID" mechanism rather than as an item search.

That matters because **ACS cannot obtain a net ID at all** — there is no `ACSF_`, no `APROP_`, and
no reference to net IDs anywhere in `p_acs.cpp`. For a botscript that needs to name an actor ACS
knows by TID, this scan is the only channel available at ordinal <= 107 (see
`../concepts/botscript-lump-format.md` on why the ordinal ceiling matters). Post-3.2.1 engines add
`SetGoalTID` (ordinal 113, commit `86e33a32d`), which sets the bot's goal from a TID directly.
It covers only the `SetGoal` use and returns no net ID, so `GetItemName`/`IsItemVisible` and the
other net-ID-taking commands still need this scan. The mod side keeps the
match unique by toggling `+SPECIAL`, which is reachable from ACS through a `CustomInventory`
`Pickup:` state running `A_ChangeFlag` — the receiver is `self` there — since ACS has no
`SetActorFlag`.

## `visibilityCheck` is narrower than line of sight

Passing 1 gates matches on `BOTS_IsVisible`, which requires the target to be within **+/-45
degrees of the bot's facing** in addition to an actual sight check. It is a "can the bot see it
right now, looking forward" test, not "is there an unobstructed line". Pass 0 for a scan that
should find an actor regardless of where the bot happens to be looking.

## Related

- `SetGoal` — takes a net ID, so it is the natural consumer of this command's return value.
- `GetItemName`, `IsItemVisible`, `GetDistanceToItem`, `GetPathingCostToItem` — the other
  net-ID-taking commands.
