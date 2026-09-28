# quickload

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes — both engines' `quickload` CCMD bodies were read this
pass and are functionally close but not identical (see below); an earlier pass had only
name-verified Zandronum's side.
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb
(2026-09-26)
**Provenance:** Verified against the UZDoom source's `src/menu/doommenu.cpp`. Zandronum side: the
Zandronum source's `src/menu/messagebox.cpp:640` and `:671-697`, `src/network.h:267-282`,
`src/menu/loadsavemenu.cpp:418-421` and `:451-457`, `src/sdl/i_input.cpp:382-395`,
`src/win32/i_keyboard.cpp:231-239`, `src/g_game.cpp:1424-1430`, `src/c_console.cpp:2176-2182`.

Bound to F9 by default on both engines. Loads the remembered "quicksave slot" (see
[`quicksave`](quicksave.md)) without going through the Load menu. If no quicksave slot has been
picked yet, opens the Load menu instead (`LoadgameMenu` on UZDoom, `Loadgamemenu` on Zandronum) and
marks whichever save gets loaded there as the new quicksave slot going forward (a sentinel pointer
value `1`, not a real `FSaveGameNode*`, is stashed in the quicksave-slot variable to signal this).
On UZDoom, refuses outright in a netgame (loading isn't possible mid-netgame) and shows the
`QLOADNET` message instead. Zandronum refuses the same way in any network state other than plain
single-player: as a client, as a server, and also in an offline game emulating a network game
(e.g. one where a bot was added). Otherwise loads via `G_LoadGame()`.

## Engine-family divergence: confirmation prompt

On UZDoom, the confirmation prompt before the load is conditional: `G_LoadGame()` runs immediately,
with no prompt, when the `saveloadconfirmation` cvar is off, and only goes through a
`QLPROMPT`-text confirmation menu when it's on (`src/menu/doommenu.cpp`'s `quickload` CCMD).
Zandronum has no `saveloadconfirmation` cvar at all. Its
`quickload` CCMD (`src/menu/messagebox.cpp`) unconditionally builds a `DQuickLoadMenu`, so the
`QLPROMPT` confirmation always appears once a quicksave slot is set, with no way to skip it.

Separately, UZDoom's re-entry guard on the "no slot picked yet" path checks the quicksave-slot
variable against both `NULL` and the sentinel `1` before treating it as a real save to load from;
Zandronum's equivalent check only tests for `NULL`. On UZDoom, running quickload again while the
sentinel is set just reopens the Load menu. On Zandronum, the same call would build the
confirmation prompt and read the save title through the sentinel pointer, an invalid dereference.
The F9 bind can't trigger this on Zandronum, though: while a menu is open, neither input backend
posts the plain key-down events that bindings act on, and the console takes no input. Closing
the Load menu resets the sentinel to `NULL`. Whether a non-keyboard route (a delayed console
command, a script) can run the CCMD in that window is unchecked.

One of the [UI-scope manual save/load triggers](../../zscript/concepts/autosave-triggers.md) — not
reachable from play-scope ZScript or ACS. See also
[`SavegameManager`](../../zscript/classes/savegamemanager.md), UZDoom's ZScript-side backing for
the Load menu this CCMD opens (both linked docs are `Applies to: UZDoom=yes, Zandronum=no` — they
describe UZDoom-only ZScript plumbing; Zandronum reaches the equivalent native `DLoadMenu`
(`src/menu/loadsavemenu.cpp`) instead, undocumented here). This note's own CCMD description above
covers both engines.
