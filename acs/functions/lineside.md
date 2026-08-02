# `int LineSide(void)`

Returns which side of the activating line special the actor was on when the special fired.
Compiler builtin (`PCD_LINESIDE`, the zt-bcc source's `src/builtin.c:43`/`:191`), implementation is a
one-line push of a per-script member variable in `DLevelScript::RunScript`'s main switch
(the Zandronum source's `src/p_acs.cpp:10652-10654`: `case PCD_LINESIDE: PushToStack(backSide); break;`).

**Bucket:** compiler builtin.

- No parameters. Returns `LINE_FRONT` (0) or `LINE_BACK` (1) — both real named constants in
  `zt-bcc/lib/zcommon.bcs:26-29`, matching the wiki's claimed `zdefs.acs` defines exactly.
- `backSide` is a `bool` field on the running `DLevelScript` instance, set exactly once at script
  construction time from a `flags` bitmask: `backSide = flags & ACS_BACKSIDE;`
  (`p_acs.cpp:13094`, inside `DLevelScript::DLevelScript`). It is **not** read fresh from any live
  line/activator state when `LineSide()` executes — it's a snapshot taken when the script instance
  was created, for the lifetime of that instance.
- **Not Cross-only.** The wiki's own example only demonstrates a walkover (`SPAC_Cross`-style)
  corridor, which could read as "this only means something for line-crossing scripts." In this
  fork `ACS_BACKSIDE` is set from a real geometric/traced `side` value for **every** line
  activation type that can start an ACS script — cross (`p_map.cpp:2190-2208`, `SPAC_Cross`/
  `MCross`/`PCross`/`AnyCross`), use (`p_map.cpp:5448/5459`, `SPAC_Use`/`UseBack`), push/bump and
  shoot/impact (`p_map.cpp:1863/1871/1875`, `SPAC_Push`/`SPAC_Impact`) all flow through the same
  `P_ActivateLine(line, mo, side, activationType)` → `P_ExecuteSpecial(..., side == 1, ...)` →
  `flags |= (backSide ? ACS_BACKSIDE : 0)` chain (`p_lnspec.cpp:1759/1790/1840` for the three
  `LS_ACS_Execute*` specials, `p_spec.cpp:324-327` for `P_ActivateLine`'s own dispatch). So
  `LineSide()` is meaningful for a script started by `Use`-tagged, `Push`/`Impact`-tagged, or
  `Cross`-tagged specials alike, not just walkover triggers.
- **When there is no activating line at all, `LineSide()` deterministically returns `LINE_FRONT`
  (0) — not garbage, not undefined, and not a distinguishable sentinel.** Every script-start path
  that doesn't originate from a line special passes a `flags` value with the `ACS_BACKSIDE` bit
  never set, so `backSide` is simply left at its default-false state:
  - **Script types with no line context at all** — `OPEN`/`ENTER`/`RESPAWN`/`DEATH`/etc. — are
    started via `FBehavior::StartTypedScripts` → `P_GetScriptGoing(activator, NULL, ..., always ?
    ACS_ALWAYS : 0)` (`p_acs.cpp:3412-3413`): `where` is `NULL` and the flags word only ever
    carries `ACS_ALWAYS`, never `ACS_BACKSIDE`.
  - **Console/`ACS_Execute`/`ACS_ExecuteAlways`/`ACS_ExecuteWithResult`-family starts** — all route
    through `P_StartScript(who, NULL, ...)` with a flags word built from `ACS_ALWAYS`/
    `ACS_WANTRESULT`/`ACS_NET`/etc. only (`p_acs.cpp:1733/1769/1832`, `p_lnspec.cpp:1759/1790/1840`
    for the non-line call sites of the same specials) — again no `ACS_BACKSIDE`.
  - In every one of these cases `backSide` is constructed as `false`, so `LineSide()` returns `0`
    (`LINE_FRONT`) — indistinguishable from "genuinely activated from the front of a line." A
    script that wants to know whether it was actually started by a line special at all has no way
    to ask that through `LineSide()` alone; it would need `GetLineSpecial`/checking
    `activationline` state (unexposed to ACS) or simply knowing its own script type.
- Argument order/count and the `LINE_FRONT`/`LINE_BACK` values themselves fully match the wiki;
  the only gap is the wiki's silence on the two points above (no-line default, and use/push/shoot
  activation types besides plain crossing).

**Provenance:** wiki page `LineSide - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`oldid=35823`) + source-verified against `p_acs.cpp:10652-10654,13074-13094,3412-3413,1733,1769,1832`,
`p_map.cpp:1863,1871,1875,2190-2208,5448,5459`, `p_lnspec.cpp:1759,1790,1840`, `p_spec.cpp:324-327`,
`p_spec.h:1153` (`ACS_BACKSIDE` definition), and `zt-bcc/lib/zcommon.bcs:26-29`/`src/builtin.c:43,191`.
No wiki/fork behavioral discrepancy found for the has-a-line case; the no-line-context default and
the use/push/shoot applicability are both undocumented additions, not corrections.
**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.
