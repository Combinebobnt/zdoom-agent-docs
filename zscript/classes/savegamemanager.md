# `SavegameManager` (struct) and `SaveGameNode`

**Tier:** B — reverse-engineered directly from UZDoom engine source; the ZDoom Wiki does not
document this native struct (it's menu-implementation plumbing, not typically modded against
directly).
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** Verified against the UZDoom source's `wadsrc/static/zscript/engine/ui/menu/
loadsavemenu.zs`, `src/common/menu/savegamemanager.cpp`/`.h`, `src/menu/loadsavemenu.cpp`, and
`src/g_game.cpp`.
**Bucket:** ZScript stdlib (`loadsavemenu.zs`; struct declarations) backed by native engine code
in `src/common/menu/savegamemanager.cpp` (cross-platform logic) and `src/menu/loadsavemenu.cpp`
(the concrete `FSavegameManager` implementation used by the stock menus).

`SavegameManager` is the native struct backing the stock Load Game / Save Game menus. It is the
only ZScript-side entry point to actually list, save, or load `.zds` save files — there is no
other native class that reaches `G_SaveGame`/`G_LoadGame`.

## Scope: `ui` only

The struct is declared `struct SavegameManager native ui` — every member is therefore only
reachable from ui-scope ZScript (menus, the ui-scope portions of a `StatusBar`, or a custom
`ui`-scope class). Play-scope code (`Actor`, `Inventory`, `Weapon` — anything in the networked
simulation) is blocked from calling any of it, enforced both at compile time and, for calls the
compiler can't resolve statically (e.g. through a function pointer), at runtime — an
out-of-scope call throws `"Cannot call ui function %s from %s context"`
(`src/common/scripting/core/scopebarrier.cpp`). See [Object scopes and
versions](../concepts/object-scopes-and-versions.md) for the general scope-barrier rules this
follows.

## `SaveGameNode`

One entry in the save-file list:

- `String SaveTitle` — the save's display title. Declared writable (no `readonly`), but the stock
  menu never assigns it directly to rename a save — renaming goes through `DoSave()`, whose
  `savegamestring` argument becomes the new title on the native side via `NotifyNewSave()` (called
  from `G_SaveGame()` in `src/g_game.cpp` after a successful write), which then updates this field
  on the in-memory node. Writing to it directly from ui-scope code would only change the displayed
  value until the next `ReadSaveStrings()` re-reads titles from disk and overwrites it.
- `readonly String Filename` — the file path on disk.
- `readonly String UUID` — the save's `GameUUID`, read from its `info.json`.
- `bool bOldVersion` — set if the save predates a version this build can load.
- `bool bMissingWads` — set if the save references a WAD/PK3 not currently loaded.
- `bool bNoDelete` — marks a special, non-removable slot (used for the "new save" placeholder
  entry the menu inserts at the top of the list).

## `SavegameManager` members

- `static SavegameManager GetManager()` — the singleton instance.
- `int WindowSize` — number of visible slots in the menu's scroll window.
- `SaveGameNode quickSaveSlot` — the slot last used for quicksave (see [Autosave and quicksave/
  quickload triggers](../concepts/autosave-triggers.md) for how `quicksave`/`quickload` resolve
  this).
- `readonly String SaveCommentString` — the currently-selected save's extracted comment/timestamp
  text, populated by `ExtractSaveData()`.
- `void ReadSaveStrings()` — (re)scans the save directory and rebuilds the in-memory save list.
- `void UnloadSaveData()` — releases the cached thumbnail/comment for the currently-selected save.
- `int RemoveSaveSlot(int index)` — deletes a save file from disk and the in-memory list.
- `void LoadSavegame(int Selected)` — triggers loading the save at `Selected`; this is the actual
  "Load" action, calling into `G_LoadGame()`.
- `void DoSave(int Selected, String savegamestring)` — triggers saving to the slot at `Selected`
  (or an auto-picked new filename if `Selected == 0`) with `savegamestring` as both the filename
  hint (in netgames, sanitized into a path) and the save's title; calls
  `PerformSaveGame()` → `G_SaveGame(fn, savegamestring)`. **This is the only ZScript-reachable path
  to actually writing a save file**, and it is ui-scope only — no play-scope or ACS equivalent
  exists (ACS additionally has its console-command escape hatch disabled outright in this engine,
  so there's no indirect route via `ConsoleCommand("save ...")` either).
- `int ExtractSaveData(int index)` — reads a save's `info.json`/`savepic.png` **without loading the
  game** — opens the file as a plain resource archive, parses just those two entries, and
  populates `SaveCommentString` and the drawable thumbnail. This is how the menu shows a
  description/thumbnail for the highlighted slot before the player commits to loading it. `index
  == -1` resolves to the currently-selected/last-accessed slot.
- `void ClearSaveStuff()` — releases menu-side save-list state.
- `bool DrawSavePic(int x, int y, int w, int h)` — draws the thumbnail last populated by
  `ExtractSaveData()`, if one exists; returns `false` if there's no picture to draw.
- `void SetFileInfo(int Selected)` — (re)reads just the on-disk filename/title metadata for a slot
  without doing the full `ExtractSaveData()` work.
- `int SavegameCount()` — number of entries in the current save list (including any placeholder
  "new save" row).
- `SaveGameNode GetSavegame(int i)` — the node at index `i`.
- `void InsertNewSaveNode()` / `bool RemoveNewSaveNode()` — add/remove the placeholder "create a
  new save" row the Save menu shows at the top of the list.
- `int RemoveUUIDSaveSlots()` — removes every save sharing the current game's `GameUUID` (used
  when starting a new game to clear out its own prior saves).
- `deprecated("4.0") void DrawSaveComment(...)` — deprecated no-op; kept for source compatibility
  only.

## What it does *not* give you

- No generic file-listing or arbitrary-file-read API — `ExtractSaveData()` only ever reads the two
  fixed entries (`info.json`, `savepic.png`) of a `.zds` file, nothing else in the archive.
- No way to inspect or modify a save's actual gameplay payload (`globals.json`, per-level snapshot
  data) from ZScript — only the display metadata.
- No parameter to `DoSave()`/the autosave paths for anything beyond a plain title string; see
  [Autosave and quicksave/quickload triggers](../concepts/autosave-triggers.md) for the
  autosave-specific hardcoded-description caveat.
