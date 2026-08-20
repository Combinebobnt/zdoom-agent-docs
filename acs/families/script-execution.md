# Named script execution family

**Tier:** A for all four.
**Applies to:** UZDoom=yes, Zandronum=yes — `Acs_NamedExecuteWait` resolves to `compiler-only` by
bare name (it's a `zt-bcc` macro with no opcode of its own, see Bucket below), but both of its
expansion components (`Acs_NamedExecute`, an ACSF present on both engines; `PCD_SCRIPTWAITNAMED`,
a base PCD present on both engines) are fully portable, so the macro is too
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-28)
**Provenance:** wiki pages `ACS_NamedExecute - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=ACS_NamedExecute&oldid=35683`),
`ACS_NamedExecuteAlways - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=ACS_NamedExecuteAlways&oldid=40212`), `ACS_NamedExecuteWait - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=ACS_NamedExecuteWait&oldid=36649`), `ACS_NamedExecuteWithResult - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=ACS_NamedExecuteWithResult&oldid=46388`) (all `_intake/`,
retrieved 2026-07-28) + source-verified against `p_acs.cpp:5400-5406,6339-6360,9120-13050,
9190-13288`, `p_lnspec.cpp:86-95,1753-1851`, `zcommon.bcs:1565,1667,1672-1673`,
`zt-bcc/src/builtin.c:178,331-332`, `zt-bcc/src/codegen/expr.c:1991-2033`; see each function's own
section below for its full source citations.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `Acs_NamedExecute`/`Acs_NamedExecuteAlways`/`Acs_NamedExecuteWithResult` are extension
functions (negative index in `zcommon.bcs`: -39, -45, -44 respectively). `Acs_NamedExecuteWait` is
different in kind — a `zt-bcc` compiler-internal macro (`src/builtin.c:178`, no engine opcode of
its own) that expands at the call site into `Acs_NamedExecute` + `PCD_SCRIPTWAITNAMED`.

`Acs_NamedExecute`, `Acs_NamedExecuteAlways`, `Acs_NamedExecuteWait`, `Acs_NamedExecuteWithResult`
— the named-by-string counterparts of the numbered `Acs_Execute`/`Acs_ExecuteAlways`/
`Acs_ExecuteWait`/`Acs_ExecuteWithResult` family. Grouped into one file because none of them have
an independent implementation: all four (plus `NamedSuspend`/`NamedTerminate`/
`NamedLockedExecute`/`NamedLockedExecuteDoor`, undocumented here) are handled by the same shared
block in `p_acs.cpp:6339-6356`, which resolves the script name to a negative script number and
forwards to the matching *numbered* action special via `NamedACSToNormalACS[]`
(`p_lnspec.cpp:86-95`) — reading any one of these in isolation from `p_acs.cpp` alone is
misleading, since the real behavior lives in the numbered special's code, not in a `case
ACSF_...:` block of its own.

All four are documented below regardless of real-world usage — see the family-coverage rule in
`../../shared/AUTHORING.md`'s Authoring rule section (a family's less-used members are exactly the ones nobody
has figured out yet).

**Shared traits across all four** (established once here instead of repeated per function below):
- The script name is resolved via `-FName(FBehavior::StaticLookupString(args[0]))`
  (`p_acs.cpp:6347`) into a negative script number, then handled by ordinary `P_StartScript`
  machinery — same lookup failure mode (console message, silent `false`/`0`) across all of them.
- Each has a Zandronum-specific clientside/netcode carve-out the ZDoom wiki has no reason to
  mention (ZDoom has no client/server split): if the *server* is calling on behalf of a script
  flagged `CLIENTSIDE`, the server never actually runs the script — it broadcasts
  `SERVERCOMMANDS_ACSScriptExecute(...)` for clients to run it themselves. The **polarity of the
  fallback return value differs per function** — see each section below; this is not uniform
  across the family and has bitten at least one doc draft already.
- None of the fork-specific caveats below are documented on the ZDoom wiki, which predates or
  doesn't model Zandronum's client/server split.

## Engine-family divergence: CLIENTSIDE carve-out is dead code on UZDoom

The Zandronum-specific clientside/netcode carve-out described above (and per function below, for
`Acs_NamedExecute`, `Acs_NamedExecuteAlways`, and `Acs_NamedExecuteWithResult`) has no live
counterpart on UZDoom. UZDoom's script-launch path (`P_GetScriptGoing`/the `DLevelScript`
constructor in `p_acs.cpp`) does carry a `bClientSide` flag and a second, separate
`ClientSideACSThinker` script table alongside the normal one, but which table a given script lands
in is decided by a small helper that currently returns false unconditionally for every script,
regardless of that script's own `CLIENTSIDE` flag — a proper flag-driven replacement for that
helper hasn't been wired up yet. UZDoom also has no server-broadcasts-to-clients mechanism
comparable to Zandronum's `SERVERCOMMANDS_ACSScriptExecute` at all. Net effect: on UZDoom, a
`CLIENTSIDE`-flagged script launched through any of these three functions is dispatched exactly
like an ordinary script — the ordinary same-map/cross-map/deferred/not-found logic, no
special-casing, no return-value override — so the
per-function polarity differences documented below (unconditional `true` for
`Acs_NamedExecute`/`Acs_NamedExecuteAlways`, unconditional `false`/`0` for
`Acs_NamedExecuteWithResult`) describe Zandronum-only behavior that UZDoom's dispatch path never
actually reaches. `Acs_NamedExecuteWait` needs no mention of its own here, since it already discards
`Acs_NamedExecute`'s return value before this carve-out could matter either way.

---

## `bool Acs_NamedExecute(str script; int map, raw s_arg1, raw s_arg2, raw s_arg3)`

Named-script variant of the numbered `Acs_Execute` — runs the exact same
`FUNC(LS_ACS_Execute)` code (`p_lnspec.cpp:1753-1778`) as the numbered action special, just with
the name pre-resolved to a number first.

- `map` — **not a map/lump name** despite the wiki's generic "map which contains the script"
  phrasing. It's a numeric MAPINFO `levelnum`, resolved via `FindLevelByNum` (`g_mapinfo.cpp:128`,
  a linear scan of `wadlevelinfos[].levelnum`). `0` means "the current map" and skips the lookup
  entirely (`p_lnspec.cpp:1768-1769`). **If `map` is nonzero and no loaded level has that
  `levelnum`, the call fails immediately — returns `false`, without even attempting to defer**
  (`p_lnspec.cpp:1775-1777`). A typo'd/unconfigured map number is silently indistinguishable from
  "script not found" (both return `false`), not a deferred-and-eventually-run case.
- `s_arg1`/`s_arg2`/`s_arg3` — passed through as the script's own args; in `zt-bcc`'s signature
  these are optional (after the `;`) and default to `0` if omitted, unlike the wiki's C-style
  prototype which shows all 5 params as mandatory.
- **Return value**, per `P_StartScript` (`p_acs.cpp:13234-13284`):
  - Script not found on the target map -> `false`, plus a console message.
  - Target map differs from the current map -> queued via `addDefered`, **always returns `true`**
    immediately — but only reached if `map` resolved to a real `levelnum` in the first place.
  - Target map is the current map -> the script actually runs; return value is the normal
    start/failure result.
- **Clientside carve-out:** server-side call for a `CLIENTSIDE`-flagged script unconditionally
  returns **`true`** — success is reported regardless of whether any client actually
  has/loads the script.
  - Zandronum only; this carve-out is dead code on UZDoom — see "Engine-family divergence:
    CLIENTSIDE carve-out is dead code on UZDoom" above.

**Provenance:** wiki page `ACS_NamedExecute - ZDoom Wiki.html` (`_intake/`, `https://zdoom.org/w/index.php?title=ACS_NamedExecute&oldid=35683`) +
source-verified against `zt-bcc/lib/zcommon.bcs:1667`, `p_acs.cpp:5400,6339-6353,13234-13284`,
`p_lnspec.cpp:86-92,1753-1778`, `g_mapinfo.cpp:128-134`.

---

## `bool Acs_NamedExecuteAlways(str script, int map [, raw s_arg1, raw s_arg2, raw s_arg3])`

"Always" meaning it re-runs the target script even if an instance of it is already running,
unlike plain `Acs_NamedExecute`. Target special: `LS_ACS_ExecuteAlways` (`p_lnspec.cpp:1784-1813`).

- **Signature is exactly as declared, not the wiki's version:** `zcommon.bcs:1673`
  (`Acs_NamedExecuteAlways(str,int;raw,raw,raw):bool`) puts the required/optional split (`;`)
  after `str,int` — **`script` and `map` are both mandatory from this toolchain**, only the three
  `s_arg*` are optional. The underlying C++ would tolerate omitting `map` too (defaulting to 0),
  but `bcc` rejects a 1-arg call outright since `zcommon.bcs` declares `map` before the `;`.
- **`map == 0` means "current map"** (`p_lnspec.cpp:1800-1802`) — the wiki page never states this
  explicitly. A non-zero `map` is resolved via `FindLevelByNum(arg1)`; if that lookup fails, the
  call **returns `false` without running or deferring anything** (`p_lnspec.cpp:1808-1810`).
- **Confirmed not available as an action special**, matching the wiki's claim — `zcommon.bcs` has
  no positive-index `Acs_NamedExecuteAlways` entry, only the numbered `Acs_ExecuteAlways` (index
  226). To trigger a named script from a UDMF line/thing special, use `Acs_ExecuteAlways` with
  `arg0str` set to the script name; there is no toolchain-level named equivalent for specials.
- **Deferred cross-map execution always reports success**, matching the wiki's "Deferred scripts
  are always considered successful" — no way to observe whether the deferred script ever actually
  ran once that map loads.
- **Clientside carve-out:** server-side call for a `CLIENTSIDE`-flagged script returns **`true`**
  unconditionally (`p_lnspec.cpp:1792-1798`) — same polarity as `Acs_NamedExecute`.
  - Zandronum only; this carve-out is dead code on UZDoom — see "Engine-family divergence:
    CLIENTSIDE carve-out is dead code on UZDoom" above.
- `s_arg1`/`s_arg2`/`s_arg3` map straight to the target script's parameters, untyped `raw`
  (`p_lnspec.cpp:1789`) — no unit/fixed-point conversion happens anywhere in this path.

**Example** (from the wiki, unmodified — a `CustomInventory` item that arms buddha mode and
polls for near-death to auto-heal once):

```text
Actor AvoidDeath : CustomInventory
{
  Inventory.MaxAmount 0
  +INVENTORY.AUTOACTIVATE
  States
  {
  Use:
    TNT1 A 0 ACS_NamedExecuteAlways("AvoidDeathScript", 0)
    Stop
  }
}
```
```text
script "AvoidDeathScript" (void)
{
  SetPlayerProperty(0, 1, PROP_BUDDHA);
  while(1)
  {
    if(GetActorProperty(0, APROP_HEALTH) <= 1)
    {
      SetPlayerProperty(0, 0, PROP_BUDDHA);
      GiveInventory("Health", 100);
      terminate;
    }
    delay(1);
  }
}
```

**Provenance:** wiki page `ACS_NamedExecuteAlways - ZDoom Wiki.html` (`_intake/`, retrieved
2026-07-28, `https://zdoom.org/w/index.php?title=ACS_NamedExecuteAlways&oldid=40212`) + source-verified (`p_acs.cpp:5406,6339-6356,13234-13288`,
`p_lnspec.cpp:86-95,1784-1813`, `zcommon.bcs:1565,1673`).

---

## `void Acs_NamedExecuteWait(str script [, raw unused, raw arg1, raw arg2, raw arg3])`

Not a real engine opcode — `zt-bcc` treats it as an "internal function" macro
(`src/builtin.c:178`, `{ "acs_namedexecutewait", ";s;rrrr" }`) that the compiler expands, at the
call site (`src/codegen/expr.c:1991-2033`, `write_executewait`'s `named_impl == true` branch), into
a fixed sequence of real engine operations: push the script name, duplicate it (keeping a copy for
the wait step), push a hardcoded literal `0` for the "unused"/map argument regardless of what was
actually passed, push `arg1`/`arg2`/`arg3` verbatim, call extension function `-39`
(`Acs_NamedExecute`) and discard its `bool` return, then wait on the duplicated name via
`PCD_SCRIPTWAITNAMED`.

A grep of `p_acs.cpp` for `NAMEDEXECUTEWAIT` finds nothing and could wrongly suggest this isn't
implemented — the real behavior lives in two *other* places: the `ACSF_ACS_NamedExecute` case
(`p_acs.cpp:6339`) for the execute half, and `PCD_SCRIPTWAITNAMED` (`p_acs.cpp:10672-10674`) for
the wait half.

- **The wiki's "you must specify 0 here" for the `unused` map argument is stronger than reality
  in zt-bcc.** The compiler doesn't just ask you to pass 0 — it silently discards whatever
  value you pass for that argument and hardcodes a literal `PCD_PUSHNUMBER, 0` instead
  (`expr.c:2022`). Passing a nonzero value there is a no-op, not a bug.
- **All of `unused`/`arg1`/`arg2`/`arg3` are optional here**, contrary to the wiki's signature
  which shows them as required. `builtin.c`'s format string is `";s;rrrr"` —
  `[return];[required];[optional]` — only the script name is mandatory.
- **`PCD_SCRIPTWAITNAMED` waits by name hash, not by script instance**
  (`p_acs.cpp:10672-10674`), using the same `SCRIPT_ScriptWait`/`SCRIPT_ScriptWaitPre` state
  machine as the numbered `PCD_SCRIPTWAIT`/`ScriptWait()` (`p_acs.cpp:9190-9200`) — it just keys
  `RunningScripts` by a negative `FName` instead of a positive script number.
- **Footgun: if the named script never actually starts, the caller waits forever, not
  immediately.** `SCRIPT_ScriptWaitPre` (`p_acs.cpp:9190-9193`) only advances to
  `SCRIPT_ScriptWait` once `RunningScripts.CheckKey(statedata) != NULL` — no timeout, no path back
  to `SCRIPT_Running` if the key never appears. `Acs_NamedExecute`'s `bool` success/failure return
  is discarded by the `PCD_DROP` above, so the caller has no way to detect a bad name. A
  misspelled name, a `#library`-scoped name that doesn't resolve from the caller's compilation
  unit, or a named script that fails to start for any other reason (e.g. already running as a
  non-repeatable/singleton instance) all produce the same result: the calling script silently
  hangs in `SCRIPT_ScriptWaitPre` for the rest of the map — a permanent stall, not a clean
  failure.
- The map-number restriction the wiki calls out ("you can only wait on scripts in the current
  map") isn't a documented rule being followed — it falls straight out of the hardcoded literal
  `0` above; there's no other map number this macro is capable of producing.
- Unlike its two siblings above, this one has **no clientside/netcode carve-out of its own** to
  document — it's a thin macro over `Acs_NamedExecute` (which does have one) plus a wait opcode.

**Wiki's worked example** (unmodified, matches zt-bcc's actual expansion):
```text
script "WaitOnMonsters" (int tid)
{
    while (ThingCount(T_NONE, tid))
        delay(1);
}

script "MonsterChallengeA" (int tid, int tag, int speed)
{
    print(s:"Kill all the monsters to open the door.");
    ACS_NamedExecuteWait("WaitOnMonsters", 0, tid);
    Door_Open(tag, speed, TRUE);
}
```

**Returns:** nothing (`void`) — see the footgun note above; there is no way to observe whether the
named script actually ran.

**Provenance:** wiki page `ACS_NamedExecuteWait - ZDoom Wiki.html` (`_intake/`, retrieved
2026-07-28, `https://zdoom.org/w/index.php?title=ACS_NamedExecuteWait&oldid=36649`) + source-verified against `zt-bcc` codegen
(`src/builtin.c:178,331-332`, `src/codegen/expr.c:1991-2033`, `src/parse/token/info.c:166`) and
the Zandronum source's `src/p_acs.cpp:6339-6360,9190-9200,10672-10674`.

---

## `int Acs_NamedExecuteWithResult(str script [, raw s_arg1, raw s_arg2, raw s_arg3, raw s_arg4])`

Runs the target script **synchronously, in the caller's own tic**, and returns whatever it passes
to `SetResultValue`, instead of just starting it as a background script and returning a
start/fail `bool` like `Acs_NamedExecute`/`Acs_NamedExecuteAlways` do. Target special:
`LS_ACS_ExecuteWithResult` (`p_lnspec.cpp:1833-1851`).

- **Signature is stricter than the wiki's version:** `zcommon.bcs:1672`
  (`Acs_NamedExecuteWithResult(str;raw,raw,raw,raw):int`) puts the required/optional split (`;`)
  right after `str` — **only `script` is mandatory; all four `s_arg*` are optional**, defaulting
  to `0`. Unlike the sibling `Acs_NamedExecuteAlways` (which the toolchain forces a mandatory
  `map` onto), this function has no `map` parameter at all in either the wiki or this toolchain —
  it always runs on the current map (`p_lnspec.cpp:1850`, hardcoded `level.mapname`).
- **Runs immediately, in-line, not queued to next tic — and the result is only correct if the
  script never blocks before calling `SetResultValue`.** `P_StartScript` (`p_acs.cpp:13260-13269`)
  creates the script instance and, because `ACS_WANTRESULT` is set, calls
  `runningScript->RunScript()` **directly, synchronously**. `DLevelScript::RunScript`
  (`p_acs.cpp:9120-13050`) initializes `resultValue = 1` and only overwrites it when the bytecode
  interpreter hits `PCD_SETRESULTVALUE`; it keeps interpreting instructions until the script
  terminates (`PCD_TERMINATE`) **or hits any blocking state** (`Delay`, `PolyWait`, `TagWait`,
  `ScriptWait`, `Suspend`), at which point the loop exits early and whatever `resultValue`
  currently holds is returned right then, with the rest of the script continuing later with **no
  way to retrieve its eventual real result**. Concretely:
  - A script that never calls `SetResultValue` at all before terminating returns **`1`, not
    `0`** — easy to mistake for "success" boolean semantics when it's actually just the
    uninitialized default.
  - A script that `Delay`s/waits *before* calling `SetResultValue` returns whatever `resultValue`
    was at that pause point (`1` if nothing was set yet), **not** the value it eventually computes.
- **Unresolved script name returns `0` but does print a console message** — indistinguishable *by
  return value alone* from a resolved script that legitimately returns `0` via
  `SetResultValue(0)` or by never setting a result.
- **Clientside carve-out has the opposite polarity from its siblings:** inside
  `LS_ACS_ExecuteWithResult` (`p_lnspec.cpp:1842-1848`), a server handing a `CLIENTSIDE`-flagged
  target off to clients **unconditionally returns `false`/`0`** (not `true`, unlike
  `Acs_NamedExecute`/`Acs_NamedExecuteAlways`) — with no way to observe what any client's copy of
  the script actually computed. This failure mode is silent and ambiguous in a way the
  `bool`-returning siblings aren't, since `0` is exactly the value a legitimate
  `SetResultValue(0)` would also produce.
  - Zandronum only; this carve-out is dead code on UZDoom — see "Engine-family divergence:
    CLIENTSIDE carve-out is dead code on UZDoom" above.
- `s_arg1`-`s_arg4` map straight to the target script's parameters, untyped `raw`
  (`p_lnspec.cpp:1839`) — no unit/fixed-point conversion happens anywhere in this path.

**Example** (from the wiki, unmodified — an item that branches on player class via a result):

```text
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
```
```text
TNT1 A 0 A_JumpIf(CallACS("CheckPlayerClass", 0, 0, 0) == 0, "NormalPlayer")
```

**Returns:** `int` — whatever the target script passed to `SetResultValue`, **or `1` if it never
called `SetResultValue` before terminating/blocking**, or `0` if the script name doesn't resolve,
or (Zandronum only — dead on UZDoom, see the divergence note above) `0` unconditionally if the
server had to hand the call off to clients because the target script is `CLIENTSIDE`. The `0` cases
are indistinguishable from each other and from a real `SetResultValue(0)`.

**Provenance:** wiki page `ACS_NamedExecuteWithResult - ZDoom Wiki.html` (`_intake/`, retrieved
2026-07-28, `https://zdoom.org/w/index.php?title=ACS_NamedExecuteWithResult&oldid=46388`) + source-verified (`p_acs.cpp:5405,6339-6356,9120-13050,13234-13288`,
`p_lnspec.cpp:86-95,1833-1851`, `zcommon.bcs:1672`).
