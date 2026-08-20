# `int GetLevelInfo(int levelinfo)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `GetLevelInfo - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29, `https://zdoom.org/w/index.php?title=GetLevelInfo&oldid=38211`) + source-verified against `p_acs.cpp:12516-12531` (`PCD_GETLEVELINFO` switch), `p_acs.h:998-1008` (engine-side `LEVELINFO_*` enum), `zt-bcc/lib/zcommon.bcs:344-355` (BCS-side enum), `zt-bcc/src/builtin.c:126` (signature), `g_mapinfo.cpp:254-255,961-979` (`partime`/ `sucktime` MAPINFO parsing and defaults), `g_mapinfo.cpp:1567-1658` (`GetDefaultLevelNum`/ `ParseMapHeader`, the levelnum auto-derivation-from-mapname path), `g_level.cpp:962-963,2086-2087` (par/sucktime tic conversion happening only at intermission-screen build time, cluster/levelnum assignment), `d_dehacked.cpp:1997-2011` (DeHackEd `[Par Times]` patch, confirming `level.partime`'s raw-seconds convention holds across both its writers, not just MAPINFO), `p_setup.cpp:3937` (ruled out as an unrelated `wbparms_t`-only default, not a second writer of `level.partime`), `wi_stuff.cpp:1199` (the one in-fork consumer of `level.sucktime`, used to check — not assume — its intended unit), and `sv_commands.cpp:3904-3922` (Zandronum secret/item/monster-counter replication). Per the ZDoom-wiki intake process, every one of the 10 `LEVELINFO_*` selectors was checked individually against the fork's enum and switch for the "compiles but engine doesn't implement it" trap seen elsewhere in this tree — none reproduced; the divergence that *did* turn up is the undocumented raw/unconverted (not tics) unit of `PAR_TIME`/`SUCK_TIME`, recorded above (seconds confirmed for `PAR_TIME` via two independent writers; `SUCK_TIME`'s intended unit is explicitly left unresolved rather than guessed).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Reads one property of the current map into a plain `int`. Compiler builtin (`{ "getlevelinfo",
"i;i" }` in the zt-bcc source's `src/builtin.c:126`, opcode `PCD_GETLEVELINFO`), implementation in
`DLevelScript::RunScript` (the Zandronum source's `src/p_acs.cpp:12516-12531`):

```cpp
case PCD_GETLEVELINFO:
	switch (STACK(1))
	{
	case LEVELINFO_PAR_TIME:		STACK(1) = level.partime;			break;
	case LEVELINFO_SUCK_TIME:		STACK(1) = level.sucktime;			break;
	case LEVELINFO_CLUSTERNUM:		STACK(1) = level.cluster;			break;
	case LEVELINFO_LEVELNUM:		STACK(1) = level.levelnum;			break;
	case LEVELINFO_TOTAL_SECRETS:	STACK(1) = level.total_secrets;		break;
	case LEVELINFO_FOUND_SECRETS:	STACK(1) = level.found_secrets;		break;
	case LEVELINFO_TOTAL_ITEMS:		STACK(1) = level.total_items;		break;
	case LEVELINFO_FOUND_ITEMS:		STACK(1) = level.found_items;		break;
	case LEVELINFO_TOTAL_MONSTERS:	STACK(1) = level.total_monsters;	break;
	case LEVELINFO_KILLED_MONSTERS:	STACK(1) = level.killed_monsters;	break;
	default:						STACK(1) = 0;						break;
	}
	break;
```

## All 10 wiki-listed `LEVELINFO_*` selectors exist and are implemented — no gap found here

This is a ZDoom wiki page, so per the intake process every `LEVELINFO_*` selector was checked
individually for the "compiles but the engine switch doesn't implement it" trap already confirmed
elsewhere (`GetActorProperty`'s 7 dead `APROP_*` names, `functions/getactorproperty.md`;
`SpawnParticle`'s dead ACSF range, `families/spawning.md`). It doesn't reproduce here:

- the zt-bcc source's `lib/zcommon.bcs:344-355` declares exactly the wiki's 10 names (`PAR_TIME`,
  `SUCK_TIME`, `CLUSTERNUM`, `LEVELNUM`, `TOTAL_SECRETS`, `FOUND_SECRETS`, `TOTAL_ITEMS`,
  `FOUND_ITEMS`, `TOTAL_MONSTERS`, `KILLED_MONSTERS`).
- the Zandronum source's `src/p_acs.h:998-1008` declares the engine-side enum with the same 10 names.
- The switch above has a real `case` for all 10 — none fall through to `default: return 0;`.
- `zcommon.bcs` and `p_acs.h` agree with each other 1:1 on both the 10 names and their assigned
  0-9 values (`PAR_TIME, CLUSTERNUM, LEVELNUM, TOTAL_SECRETS, FOUND_SECRETS, TOTAL_ITEMS,
  FOUND_ITEMS, TOTAL_MONSTERS, KILLED_MONSTERS, SUCK_TIME`) — only the *wiki prose's* listing
  order differs from this (it lists `SUCK_TIME` second, right after `PAR_TIME`, instead of last).
  Since `bcc` compiles each named constant to its own enum's value and the engine's `switch`
  matches on the same names, this costs nothing at runtime. Flagged only because a future
  re-ordering of just one of the two enums (without the other) would silently break every selector
  after the reordered point — there's no compile-time check tying them together.
- An unrecognized `levelinfo` value (a raw int that isn't any of the 10, e.g. a typo'd literal)
  silently returns `0` — matches the wiki's stated "0 when the property is unknown."

## Undocumented unit trap: `PAR_TIME`/`SUCK_TIME` are raw MAPINFO numbers, not tics

The wiki gives no units for these two. Tracing where `level.partime`/`level.sucktime` are
populated (the Zandronum source's `src/g_mapinfo.cpp:961-979`, the `partime`/`par`/`sucktime` MAPINFO
option parsers) shows both are stored as the **literal number written in MAPINFO**, completely
unconverted:

```cpp
DEFINE_MAP_OPTION(partime, true)
{
	parse.ParseAssign();
	parse.sc.MustGetNumber();
	info->partime = parse.sc.Number;   // seconds, as authored
}
DEFINE_MAP_OPTION(sucktime, true)
{
	parse.ParseAssign();
	parse.sc.MustGetNumber();
	info->sucktime = parse.sc.Number;  // minutes, as authored
}
```

`level.partime` is only ever multiplied by `TICRATE` at the point the intermission screen builds
its `wbparms_t` (`g_level.cpp:962`, `wminfo.partime = TICRATE * level.partime;`) — `GetLevelInfo`
itself hands back the pre-multiplication value. The classic-Doom DeHackEd `[Par Times]` patch path
(`d_dehacked.cpp:1997-2011`, `info->partime = par;` where `par = atoi(...)` off the DEH line) feeds
the same field with the same convention — DeHackEd par times are also authored in raw seconds — so
this isn't a MAPINFO-only quirk; every writer of `level.partime` uses unconverted seconds. (A
separate `wminfo.partime = 180;` at `p_setup.cpp:3937` is an early hardcoded default for the
*different* `wbparms_t::partime` field, always overwritten by the `TICRATE`-multiplied value before
an intermission screen actually displays it — not a second writer of `level.partime` and not
something `GetLevelInfo` can observe.) So:

- **`LEVELINFO_PAR_TIME` returns whole seconds**, not tics — unlike every tic-counting ACS
  function (`Timer()`, `Delay()`'s argument, etc.), dividing it by 35 would be wrong; it's already
  in seconds as authored in MAPINFO's `partime = N` line or a DEH `Par Times` patch.
- **`LEVELINFO_SUCK_TIME` returns the raw, unconverted number written in MAPINFO's `sucktime = N`
  line** — confirmed only that far, not further. The unit that number is *meant* to represent isn't
  independently established here: the only in-fork consumer of `level.sucktime` found by this
  pass, `wi_stuff.cpp:1199`'s "sucks" message check (`t >= wbs->sucktime * 60 * 60`, where `t` is
  seconds), reads as treating it as **hours** (×3600), not the "minutes" a mapper might expect from
  the option's name — and that's the only evidence available, so don't assume minutes. Whatever the
  intended unit, `GetLevelInfo(LEVELINFO_SUCK_TIME)` performs no conversion of its own.
- If a map's MAPINFO doesn't set `partime`/`sucktime` at all, both default to `0`
  (`g_mapinfo.cpp:254-255`) — indistinguishable from a mapper explicitly writing `partime = 0`.

## Other properties

`CLUSTERNUM`/`LEVELNUM` are the plain `int` MAPINFO cluster/levelnum fields (`g_level.cpp:2086`).
`LEVELNUM` in particular has **no reliable "not set" sentinel at all**: `ParseMapHeader`
(`g_mapinfo.cpp:1658`, `levelinfo->levelnum = GetDefaultLevelNum(levelinfo->mapname);`) always
auto-derives a levelnum from the map lump name (`MAP01`→`1`, `E1M1`→`1`, anything else→`0`)
*before* an explicit MAPINFO `levelnum = N` option can override it — so a map named `MAP01` reads
back `1` even with no `levelnum` line in its MAPINFO at all. `0` doesn't reliably mean "unset"
either: `SetLevelNum` (`g_mapinfo.cpp:1857-1868`) zeroes out *any other* map's levelnum that
collides with a newly-assigned one ("the level being set always has precedence"), so a `MAP01`-
named map can still read back `0` if some other map in the same WAD explicitly claims levelnum
`1`.
`TOTAL_SECRETS`/`FOUND_SECRETS`/`TOTAL_ITEMS`/`FOUND_ITEMS`/`TOTAL_MONSTERS`/`KILLED_MONSTERS` are
the same automap-panel counters `Print`'s `PRINTNAME_*` secret/item HUD stats and the intermission
screen read, and (Zandronum addition, not on the wiki) `found_secrets`/`found_items`/
`killed_monsters` are server-authoritative and replicated to clients via dedicated
`SERVERCOMMANDS_*` calls (`sv_commands.cpp:3904-3922`) rather than each client tallying its own
copy.

**Example — from the wiki, report kill progress:**

```text
script 2 (void)
{
    int mtotal = GetLevelInfo (LEVELINFO_TOTAL_MONSTERS),
        mkilled = GetLevelInfo (LEVELINFO_KILLED_MONSTERS);

    if (mkilled == mtotal)
    {
        PrintBold (s:"You  have killed all the monsters!");
    }
    else
    {
        PrintBold (s:"You have killed ", d:mkilled, s:" monsters!\n",
            d:mtotal-mkilled, s:" left to go!");
    }
}
```
