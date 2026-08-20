# menu_save

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes — both engines' `menu_save` CCMD bodies were read this
pass and are functionally identical (see below); an earlier pass had only name-verified Zandronum's
side.
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3
(2026-08-17)
**Provenance:** Verified against the UZDoom source's `src/menu/doommenu.cpp`.

Bound to F2 by default on both engines (UZDoom's `wadsrc/static/engine/commonbinds.txt`;
Zandronum's `src/c_bind.cpp`). Thin wrapper: opens the control panel and switches straight to the
save-game screen — it doesn't save anything itself, it just navigates to the menu that lets the
player pick a slot and save. On UZDoom this is `M_SetMenu(NAME_SavegameMenu, -1)`, reaching
[`SavegameManager`](../../zscript/classes/savegamemanager.md)`.DoSave()`; on Zandronum the CCMD
body is line-for-line the same shape (`M_StartControlPanel(true); M_SetMenu(NAME_Savegamemenu,
-1);`, `src/menu/menu.cpp`), reaching the equivalent native `DSaveMenu::DoSave()`
(`src/menu/loadsavemenu.cpp`) — see the divergence note below for why that's a different
implementation, not just a different name. See also [`menu_load`](menu_load.md) (F3, the
equivalent for loading) and [Autosave and quicksave/quickload
triggers](../../zscript/concepts/autosave-triggers.md) for the full manual-trigger picture (UZDoom
only — see that file's own engine claim).

## Engine-family divergence: what `SavegameMenu` is backed by

`menu_save` itself behaves identically on both engines, but the save-game screen it opens is
implemented two different ways, because Zandronum has no ZScript at all. On UZDoom, `SavegameMenu`
is backed by the ZScript-side [`SavegameManager`](../../zscript/classes/savegamemanager.md) struct
(`Applies to: UZDoom=yes, Zandronum=no` on that file) — `DoSave()` there calls
`PerformSaveGame()` → `G_SaveGame()`. On Zandronum, the equivalent screen is the native
`DSaveMenu` C++ class (`src/menu/loadsavemenu.cpp`): its own `DoSave(FSaveGameNode*)` method
picks an unused `saveNN` filename for a fresh slot (or reuses the selected node's filename) and
calls `G_SaveGame()` directly — same eventual save-writing call, reached through native code
instead of a ZScript struct. A Zandronum-side caller has no `SavegameManager` to reach at all; the
[`SavegameManager`](../../zscript/classes/savegamemanager.md) doc's `Zandronum=no` claim is not
just "unverified there," it's a genuine absence.
