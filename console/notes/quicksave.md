# quicksave

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes — both bind `quicksave` to F6 by default and read/write
a remembered quicksave slot; the underlying save-path logic diverges in several respects (see
below).
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb
(2026-09-26)
**Provenance:** Verified against the UZDoom source's `src/menu/doommenu.cpp`. Zandronum's ACS
path checked against `src/p_acs.cpp:11284-11299` and `src/c_dispatch.cpp:1160-1169`.

Bound to F6 by default (`wadsrc/static/engine/commonbinds.txt` on UZDoom;
`src/c_bind.cpp:100` on Zandronum). Saves to a remembered "quicksave slot" without going through
the Save menu, so it's the fastest of the manual save triggers.

On both engines the very first gate no-ops with an "invalid" sound (`menu/invalid`) if `!usergame`
(not currently in an active game — e.g. demo playback, or the title screen) or the
player is dead in singleplayer. Recording a demo doesn't count: the new game started after
`G_RecordDemo` sets `usergame` back to true. Separately, and distinctly, it no-ops **silently**
(no sound at all) if `gamestate != GS_LEVEL` (e.g. an intermission or finale screen). Opening a
menu over a level leaves `gamestate` at `GS_LEVEL`, so this gate doesn't fire just because a menu
is open. These are two different conditions with two different outcomes, not one combined "not
currently in a level" case.

Past that shared gate, on UZDoom (`src/menu/doommenu.cpp`'s `CCMD (quicksave)`), in actual
execution order:

- If quicksave-slot rotation is enabled (`quicksaverotation` cvar, off by default) and this isn't
  a netgame, saves via `G_DoQuickSave()`, which picks the next slot in a rotating `quickNN` pool
  sized by the `quicksaverotationcount` cvar. This check runs *before* the "no slot yet" case
  below, so enabling rotation bypasses the remembered-slot logic entirely rather than only kicking
  in once a slot exists.
- Otherwise, if no quicksave slot has been picked yet (`savegameManager.quickSaveSlot` is null or
  the sentinel value `1` — set by `quickload` when it had no slot either, meaning "whatever gets
  loaded next should become the new quicksave slot"), opens the Save menu instead
  (`SavegameMenu`); the next save made through that menu becomes the new quicksave slot as an
  ordinary side effect of `NotifyNewSave()`, not something `quicksave` itself arranges specially.
- Otherwise saves directly to the remembered slot via `G_SaveGame()` — immediately and silently if
  `saveloadconfirmation` is off, or after a confirmation prompt (`menu/activate` sound when the
  prompt opens, `menu/dismiss` on confirm) if it's on (the default).

## Engine-family divergence: quicksave rotation and confirmation-skip

Zandronum has neither `quicksaverotation` nor `saveloadconfirmation` — absent from its whole
source tree. Its `quicksave` CCMD (`src/menu/messagebox.cpp:583`) plays `menu/activate`
unconditionally right after the shared gate above, before it even knows which menu it's about to
open — unlike UZDoom, which only sounds `menu/activate` once it commits to opening a menu — then
branches on the plain `quickSaveSlot` global (`src/menu/loadsavemenu.cpp:122`; not wrapped in a
`SavegameManager`-style object the way UZDoom's is): opens `SavegameMenu` if it's null, otherwise
always raises a `DQuickSaveMenu` confirmation prompt (`src/menu/messagebox.cpp:530-574`) before
overwriting the existing slot. There is no rotating slot pool and no way to skip the confirmation
prompt on this engine — every quicksave onto an existing slot goes through it.

## Engine-family divergence: ACS reachability

UZDoom's ACS `PCD_CONSOLECOMMAND`/`PCD_CONSOLECOMMANDDIRECT` opcodes are unconditionally
disabled — they print an error and no-op (`src/playsim/p_acs.cpp:10371-10378`) — so no ACS script
can trigger `quicksave` indirectly there (as scoped in
[autosave-triggers.md](../../zscript/concepts/autosave-triggers.md), which only claims UZDoom).
Zandronum's ACS keeps these opcodes fully working (`src/p_acs.cpp:11284-11299`): they call
`C_DoCommand()` for real. `quicksave` has no `ACS_IsCalledFromConsoleCommand()` guard, so a
script calling the zt-bcc/ACS builtin bound to this opcode (`ConsoleCommand("quicksave")`) reaches
the CCMD on Zandronum. It then runs the same flow as above: the Save menu if no slot is set, else
the confirmation prompt, so a script can't complete a save without the player confirming. Whether
the command is a plain `CCMD` or an `UNSAFE_CCMD` doesn't matter on this path: the unsafe check
(`src/c_dispatch.cpp:1160-1169`) only refuses inside an unsafe-execution scope, and the ACS
opcodes never open one. So the "console commands aren't reachable from ACS" framing below holds
for UZDoom only. It does not hold on Zandronum.

This is one of the [UI-scope manual save triggers](../../zscript/concepts/autosave-triggers.md) —
on UZDoom, unlike `Level.MakeAutoSave()` (a ZScript method with no Zandronum equivalent, since
Zandronum has no ZScript at all), there is no play-scope or ACS equivalent reachable through the
normal ACS opcode set; see the divergence section above for the one way Zandronum's ACS can still
reach it indirectly, and see that file for the full UZDoom trigger comparison. See also
[`quickload`](quickload.md) and [`SavegameManager`](../../zscript/classes/savegamemanager.md) —
the ZScript-exposed `quickSaveSlot` field there is UZDoom-only (ZScript doesn't exist on
Zandronum); Zandronum's equivalent is the plain C++ global cited above, with no scripting-visible
wrapper at all.
