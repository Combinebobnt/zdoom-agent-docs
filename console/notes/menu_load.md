# menu_load

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes — the `menu_load` CCMD and menu-navigation step are
structurally identical on both engines, but the actual load-on-slot-select step diverges because
Zandronum has no ZScript; see the divergence section below.
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15);
Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Verified against the UZDoom source's `src/menu/doommenu.cpp`.

Bound to F3 by default (UZDoom's `wadsrc/static/engine/commonbinds.txt`; Zandronum's
`src/c_bind.cpp` default-bindings table — same key on both engines). Thin wrapper: opens the
control panel and switches straight to the `LoadgameMenu` screen
(`M_SetMenu(NAME_LoadgameMenu, -1)`) — it doesn't load anything itself, it just navigates to the
menu that lets the player pick a slot and load via
[`SavegameManager`](../../zscript/classes/savegamemanager.md)`.LoadSavegame()`. See also
[`menu_save`](menu_save.md) (F2, the equivalent for saving) and [Autosave and quicksave/quickload
triggers](../../zscript/concepts/autosave-triggers.md) for the full manual-trigger picture.

The CCMD body itself is equivalent on both engines — start the control panel, then jump straight
to the load menu, nothing else:

- UZDoom: `src/menu/doommenu.cpp:1475-1479`
- Zandronum: `src/menu/menu.cpp:968-972` — same two calls in the same order, targeting
  `NAME_Loadgamemenu` (the descriptor name differs only in casing — both engines' `menudef.txt`
  declare it as `ListMenu "LoadGameMenu"`, `FName` lookups are case-insensitive).

## Engine-family divergence: how the selected save actually loads

The `SavegameManager.LoadSavegame()` call this file describes is a ZScript struct method
(`wadsrc/static/zscript/engine/ui/menu/loadsavemenu.zs`, backed by a native implementation) —
it's how UZDoom's `LoadSaveMenu` reacts once the player picks a slot in the `LoadgameMenu` this
CCMD opens. Zandronum has no ZScript at all, so there is no `SavegameManager` struct and no
`LoadSavegame()` method to call. Its equivalent menu class, `DLoadMenu` (`src/menu/loadsavemenu.cpp`),
is plain native C++: `DLoadMenu::MenuEvent` calls the engine's `G_LoadGame()` function directly on
the selected slot's filename (`src/menu/loadsavemenu.cpp:1096-1098`) when the player presses Enter
on a slot, with no intermediate manager object. The `menu_load` CCMD and the menu it opens are the
same shape on both engines; only the load-dispatch step underneath differs, as a direct consequence
of Zandronum predating ZScript's introduction upstream.
