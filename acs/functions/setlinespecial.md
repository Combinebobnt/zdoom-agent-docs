# `SetLineSpecial`

**Tier:** A
**Engine:** Zandronum 3.2.1 (core builtin predates the fork; the Named-special interop described below — commit `cbf7162e1`, "Allow for using ACS_NamedExecute and friends with SetLineSpecial" — also predates the `28f736fb3` "3.2.1" version-bump commit, so no version-gap concern for any of this file's claims).
**Provenance:** `SetLineSpecial - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=SetLineSpecial&oldid=35849`), verified 2026-07-29 against the Zandronum source's `src`.

`void SetLineSpecial(int lineid, int special, raw arg0 = 0, raw arg1 = 0, raw arg2 = 0, raw arg3 = 0, raw arg4 = 0)`

## Bucket

**Compiler builtin.** `SetLineSpecial` is entry 19 of `zt-bcc/src/builtin.c`'s parallel
`g_funcs[]`/`g_deds[]` tables (`builtin.c:55`: `{ "setlinespecial", ";ii;rrrrr" }`, paired with
`{ PCD_SETLINESPECIAL }` at the same index in `g_deds[]`, `builtin.c:203`) — it compiles straight
to the `PCD_SETLINESPECIAL` opcode, not through the `zcommon.bcs` `special` table (no positive
action-special or negative `ACSF_` index; it never appears in that table at all). Engine-side
behavior lives in the Zandronum source's `src/p_acs.cpp`, `case PCD_SETLINESPECIAL:` (line 11496).

The `g_funcs[]` format string `";ii;rrrrr"` decodes as: two required plain-int params (`lineid`,
`special`), then an optional tail of five `raw` params (`arg0`-`arg4`). `raw` (`SPEC_RAW`) accepts
an int, a fixed-point value, or an action-special name used as a bare value, without a cast —
matches how `arg0`-`arg4` are also used for e.g. `Acs_Execute`-style specials that expect encoded
angles/fixed values in some slots.

## Parameters

- **`lineid`** — line ID (assigned via `Line_SetIdentification`, or directly in UDMF), **not** a
  line index. The engine iterates every line sharing that ID via `P_FindLineFromID`
  (`p_acs.cpp:11509`) and sets the special/args on **all** of them — matches the wiki. If no line
  has that ID, the `while` loop body never runs and the call is a silent no-op (no error, no
  return value to check — this function returns nothing at all).
- **`special`** — the new action-special number to assign to the line(s). Per general BCS
  convention (not something specific to this function), an action-special's own name used as a
  bare value — e.g. `ACS_Execute` — resolves to its numeric special id, so
  `SetLineSpecial(9, ACS_Execute, 10)` and `SetLineSpecial(9, 80, 10)` compile to the same bytecode
  (`Acs_Execute` is declared at positive index `80` in `zcommon.bcs`'s `special` table,
  `zcommon.bcs:1440`). This param is plain `int` in the signature, not `raw`, but named specials
  still work because of that general name-decays-to-id behavior, not because of this param's type.
- **`arg0`-`arg4`** (raw, optional, default `0` each) — the five args stored into the line's
  `args[0..4]`. Omitted trailing args compile to a literal `0` default value
  (`zt-bcc/src/builtin.c:462-480`: `setup_default_value` falls through to
  `param->default_value = setup->task->dummy_expr`, a folded raw literal whose value is `0` —
  the `MorphActor`-specific empty-string-default special case in that same function does not apply
  to this opcode), which the engine then unconditionally reads (`p_acs.cpp:11513-11517`) — there is
  no engine-side "argument not supplied" distinction once the call reaches the opcode; it always
  sees exactly 5 arg values, some possibly compiler-supplied zeros.

## Named-script interop (`ACS_NamedExecute` and friends) — not on the ZDoom wiki page

Not mentioned by the (ZDoom, single-player-oriented) wiki page at all, but present since before
this fork's 3.2.1 tag (commit `cbf7162e1`): if `special` is one of the seven `ACSF_ACS_Named*`
extension-function indices — `Acs_NamedExecute`, `Acs_NamedSuspend`, `Acs_NamedTerminate`,
`Acs_NamedLockedExecute`, `Acs_NamedLockedExecuteDoor`, `Acs_NamedExecuteWithResult`,
`Acs_NamedExecuteAlways` (indices `-39` through `-45`, `zcommon.bcs:1667-1673`, checked via
`specnum >= -ACSF_ACS_NamedExecuteAlways && specnum <= -ACSF_ACS_NamedExecute`,
`p_acs.cpp:11503`) — then `arg0` is instead treated as a **string** (script name): the engine
looks it up as a string-table index and rewrites it to a negative `FName` script id
(`p_acs.cpp:11506`: `arg0 = -FName(FBehavior::StaticLookupString(arg0))`), and `specnum` itself is
remapped through `NamedACSToNormalACS[]` (`p_lnspec.cpp:86`) to the real numbered action special
(e.g. `Acs_NamedExecute` → `LS_ACS_Execute`) before being stored on the line. `arg1`-`arg4` pass
through unchanged. This means a line can be wired at runtime to run a *named* script (not just a
numbered one) — e.g. `SetLineSpecial(9, Acs_NamedExecute, "MyScriptName", 10)` — with no special
syntax beyond passing one of the `Acs_Named*` function names as `special`. `SetThingSpecial`
(`PCD_SETTHINGSPECIAL`, `p_acs.cpp:11531-11533`) has the identical special-case, added in the same
era (commit `7106c0681`, immediately preceding `cbf7162e1` in the same series) — see that
function's own doc if/when it exists.

## Divergence from the wiki

None found for the documented single-player behavior — the wiki's description (change the special
on all lines with a given id, args passed straight through, named-special-as-int-constant
convenience) matches `p_acs.cpp` exactly. The wiki simply doesn't cover the `ACS_Named*` interop
above (a Skulltag/Zandronum-lineage extension, not upstream ZDoom at the wiki's revision) or any
Zandronum netcode angle — but this opcode has no netcode angle to cover: it only mutates
server/local map state (`line->special`/`line->args[]`) directly, with no `SERVERCOMMANDS_*` call
of its own (contrast `PCD_SETLINEBLOCKING`, which does call
`SERVERCOMMANDS_SetSomeLineFlags` a few cases above this one in the same switch, `p_acs.cpp:11472`)
— a line's `special`/`args` aren't part of what gets synced to clients via that mechanism in this
fork; not re-verified further here since it's outside this function's own behavior.

## See also

`ClearLineSpecial` (`PCD_CLEARLINESPECIAL`, `p_acs.cpp:10677`) is not this function's inverse in
the way its name suggests: it takes **no `lineid` argument at all** (`g_funcs[]` format `""`, zero
params) and clears the special only on `activationline` — the line that triggered the
currently-running script — not on an arbitrary line looked up by id. To "clear" a `SetLineSpecial`
target by id, call `SetLineSpecial(lineid, 0)` instead.
