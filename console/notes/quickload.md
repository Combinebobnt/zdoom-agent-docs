# quickload

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes — both engines' `quickload` CCMD bodies were read this
pass and are functionally close but not identical (see below); an earlier pass had only
name-verified Zandronum's side.
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3
(2026-08-17)
**Provenance:** Verified against the UZDoom source's `src/menu/doommenu.cpp`.

Bound to F9 by default on both engines. Loads the remembered "quicksave slot" (see
[`quicksave`](quicksave.md)) without going through the Load menu. If no quicksave slot has been
picked yet, opens the Load menu instead (`LoadgameMenu` on UZDoom, `Loadgamemenu` on Zandronum) and
marks whichever save gets loaded there as the new quicksave slot going forward (a sentinel pointer
value `1`, not a real `FSaveGameNode*`, is stashed in the quicksave-slot variable to signal this).
In a netgame, refuses outright (loading isn't possible mid-netgame) and shows a message instead.
Otherwise loads via `G_LoadGame()`.

## Engine-family divergence: confirmation prompt

On UZDoom, the confirmation prompt before the load is conditional: `G_LoadGame()` runs immediately,
with no prompt, when the `saveloadconfirmation` cvar is off, and only goes through a
`QLPROMPT`-text confirmation menu when it's on (`src/menu/doommenu.cpp`'s `quickload` CCMD).
Zandronum has no `saveloadconfirmation` cvar at all (confirmed absent from its source tree) — its
`quickload` CCMD (`src/menu/messagebox.cpp`) unconditionally builds a `DQuickLoadMenu`, so the
`QLPROMPT` confirmation always appears once a quicksave slot is set, with no way to skip it.

Separately, UZDoom's re-entry guard on the "no slot picked yet" path checks the quicksave-slot
variable against both `NULL` and the sentinel `1` before treating it as a real save to load from;
Zandronum's equivalent check only tests for `NULL`. Practical effect: pressing quickload a second
time while the Load menu from the first press is still open dereferences the sentinel safely on
UZDoom (falls through to opening the Load menu again) but not obviously so on Zandronum's path —
not independently confirmed as a live crash this pass, just a source-level asymmetry worth noting
if this behavior is ever revisited.

One of the [UI-scope manual save/load triggers](../../zscript/concepts/autosave-triggers.md) — not
reachable from play-scope ZScript or ACS. See also
[`SavegameManager`](../../zscript/classes/savegamemanager.md), UZDoom's ZScript-side backing for
the Load menu this CCMD opens (both linked docs are `Applies to: UZDoom=yes, Zandronum=no` — they
describe UZDoom-only ZScript plumbing; Zandronum reaches the equivalent native `DLoadMenu`
(`src/menu/loadsavemenu.cpp`) instead, undocumented here). This note's own CCMD description above
covers both engines.
