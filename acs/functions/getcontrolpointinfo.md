# `mixed GetControlPointInfo(int point, int type)`

Reads one piece of state about a Domination-gametype control point (a `SECTINFO` "point" entry,
not a generic map sector). Extension function, `zcommon.bcs:1810` declares it at index `-182`
(`ASCF_GetControlPointInfo`, the Zandronum source's `src/p_acs.cpp:5547`), implementation is the
`case ASCF_GetControlPointInfo:` block at `p_acs.cpp:7996-8026`.

**Bucket:** extension function (negative index, `p_acs.cpp`'s `ACSF_*`/`ASCF_*` switch).

- `point` — zero-based index into `level.info->SectorInfo.Points` (the array parsed from the
  map's `SECTINFO` lump, the Zandronum source's `src/sectinfo.cpp:267-312`). **Out-of-range `point`
  does not error** — it falls into a dedicated branch (`p_acs.cpp:8000-8013`) that returns a
  type-appropriate safe default instead of the real field: `""` for `POINTINFO_NAME`, `TEAM_None`
  for `POINTINFO_OWNER`, `false`/`0` for `POINTINFO_DISABLED`, `0` for any other `type`. A map
  with zero `SECTINFO` points defined (i.e. not a Domination map at all) makes *every* call take
  this branch, so calling this function on a non-Domination map fails silently rather than
  erroring.
- `type` — one of `POINTINFO_NAME` / `POINTINFO_OWNER` / `POINTINFO_DISABLED`
  (the zt-bcc source's `lib/zcommon.bcs:1269-1273`, values `0`/`1`/`2`). Any other value hits the
  switch's own `default: return 0;` (`p_acs.cpp:8023-8024`) even for a valid `point`.
- Return type genuinely varies by `type`, matching the wiki's `mixed`: `POINTINFO_NAME` returns a
  string handle (`GlobalACSStrings.AddString(...)`, must be read as `str`); `POINTINFO_OWNER`
  returns a raw team number (see below); `POINTINFO_DISABLED` returns a plain `bool`/`0`-`1`.

## `POINTINFO_OWNER`'s "no owner" value has no matching BCS constant — a real footgun

`POINTINFO_OWNER` returns `level.info->SectorInfo.Points[point].owner` verbatim (`p_acs.cpp:8020`),
an `int` field (`DPOINT_s::owner`, the Zandronum source's `src/sectinfo.h:65`). When a point is
unclaimed, this field holds `TEAM_None`, a **C++-side sentinel defined as `255`**
(the Zandronum source's `src/teaminfo.h:38`) — completely different from `NO_TEAM` (`= 2`), the only
"no team" constant BCS scripts can actually name (the zt-bcc source's `lib/zcommon.bcs:807-811`:
`TEAM_BLUE=0, TEAM_RED=1, NO_TEAM=2`). `zcommon.bcs` never exposes `TEAM_None`/`255` under any
name. A script comparing `GetControlPointInfo(p, POINTINFO_OWNER) == NO_TEAM` to detect an
unclaimed point will **always be false** for a genuinely unclaimed point — the correct comparison
is against the raw literal `255`, undocumented anywhere in BCS-visible source. This divergence is
absent from the wiki page, which just says the return is "the team number of the current owner."

## `owner`/`disabled` are only ever initialized if the current gametype is Domination

`DPOINT_s::owner` (`int`) and `DPOINT_s::disabled` (`bool`) have no default member initializer
and are left at whatever `DPOINT_s Point;`'s default construction happens to leave them
(`sectinfo.cpp:273`, pushed by value into the `Points` array at line 305) when the `SECTINFO` lump
is parsed at map load — parsing itself never sets either field. The only code that gives them a
defined value is `DOMINATION_Init()` (the Zandronum source's `src/domination.cpp:90-102`), which
resets every point's `disabled=false` and `owner=TEAM_None` — but it starts with
`if (!domination) return;` (line 92), i.e. it's a no-op unless the Domination gametype cvar is
actually active for the current map. **On a map that defines `SECTINFO` points but is being played
in a non-Domination gametype (e.g. CTF, deathmatch), `POINTINFO_OWNER`/`POINTINFO_DISABLED` read
back whatever was left over from construction — not a defined "no owner" value.** This is a real
fork gotcha not mentioned by the wiki at all; only call this function meaningfully while
Domination is the active gametype.

**Example — print a point's name and whether it's claimed (Domination gametype only):**

```
str pointName = GetControlPointInfo(0, POINTINFO_NAME);
int owner = GetControlPointInfo(0, POINTINFO_OWNER);
if (owner == 255) // TEAM_None has no BCS constant; NO_TEAM (2) is NOT the same value
    Log(s: pointName, s: " is unclaimed.");
else
    Log(s: pointName, s: " is owned by team ", i: owner);
```

**Provenance:** wiki page `GetControlPointInfo - Zandronum Wiki.html` (`_intake/`, retrieved
2026-07-29, `oldid=2273`) + source-verified against `p_acs.cpp:7996-8026`/`5547`,
`sectinfo.h:61-70`, `sectinfo.cpp:267-312`, `domination.cpp:90-102`, `teaminfo.h:38`,
`zt-bcc/lib/zcommon.bcs:807-811,1269-1273,1810`. Wiki page itself is accurate as far as it goes
(it just doesn't mention either divergence above — both were only found by reading the C++).
**Engine:** Zandronum 3.2.1 — the introducing commit (`7e92bc6ff`, "Add ACS function to get
control point info...") was confirmed via `git merge-base --is-ancestor` to predate both the
`28f736fb3` ("changed the version string to 3.2.1") and `0dc8d30cc` ("Added tag ZA_3.2.1")
commits in the Zandronum source's checkout, i.e. it ships in 3.2.1, not just the
checkout's `3.3-alpha` HEAD. **Tier:** A.
