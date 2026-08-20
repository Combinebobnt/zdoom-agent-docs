# `int CheckAutomap()`

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Not wiki-sourced (unfetchable — see `shared/AUTHORING.md`'s "Locating the
engine/compiler source"). Derived directly from the Zandronum source's `src/p_acs.cpp`
(`EACSFunctions` enum and the `ACSF_CheckAutomap` case), cross-checked against `zt-bcc`'s
`lib/zcommon.bcs`, and exercised live via a Zandronum MCP session (declared the wrapper below,
loaded it as an autoloaded library via `LOADACS`, and read the return value into a global ACS
variable across all three states — off/fullscreen/overlay, toggled via the `togglemap` CCMD and
the `am_overlay` cvar — confirming the values below against what was actually on screen).
**Bucket:** extension function (index -189; dispatched as `ACSF_CheckAutomap`).

Returns the local client's automap display state: `0` = off, `1` = fullscreen automap (the
automap replaces the 3D view entirely), `2` = automap overlay (the map is drawn semi-transparent
on top of the still-rendering 3D view). Reads purely local client render state
(`automapactive`/`viewactive`), takes no arguments, and ignores its calling context — safe to call
from a `CLIENTSIDE` script to test what the console player is currently looking at.

**Not declared in `zt-bcc`'s `lib/zcommon.bcs`** — Zandronum implements this ACSF (confirmed
present, positioned immediately after `ACSF_CheckScript` in the `EACSFunctions` enum, index
computed by counting forward from `ACSF_ResetMap = 100` and cross-checked against three other
already-declared indices in the same enum run), but no BCS-side `special` wrapper exists for it in
the compiler's shipped headers. A project that wants to call it must declare its own wrapper
before use:

```text
special
-189:CheckAutomap():int;
```

This is a plain `raw import`-style extension-function declaration (see the BCS wiki's
`Grammar.md` `special` production), not an engine or compiler change — it just tells the compiler
which negative index to emit for a call site the compiler's own headers don't already know about.
Verified live in Zandronum: returns `0` with no automap open, `1` while `automapactive && !viewactive`
(fullscreen — `togglemap` with `am_overlay 0`), and `2` while both are true (overlay —
`togglemap` with `am_overlay 1`), matching the `AM_ToggleMap` source exactly, including the
overlay→fullscreen transition on a third `togglemap` (`am_overlay==1 && viewactive` only clears
`viewactive`, it does not call `AM_Stop`) rather than the naive "toggle closes it" assumption.

Distinct from `GetPlayerChasecam(int player)` (index -137, already declared in `zcommon.bcs`),
which reports whether a player has chasecam active — a different local render state that,
combined with `CheckAutomap()` returning `1`, covers "is the console player currently seeing
something other than their own first-person 3D view."

## Zandronum-specific: no UZDoom equivalent ACS function

`CheckAutomap()` is a Zandronum-only extension function — it is not in UZDoom's `EACSFunctions`
enum (`src/playsim/p_acs.cpp`) at all, and UZDoom's ACS extension-function dispatch has no
`automap`-related case anywhere in that file (grepped absent). Calling the `special` wrapper
declared above against a UZDoom server has no defined behavior; this doc's guidance only applies
to Zandronum.

The underlying local-client state this function reads is not Zandronum-specific, though: UZDoom's
`automapactive`/`viewactive` globals and its `AM_ToggleMap` off/fullscreen/overlay three-state
toggle (`src/am_map.cpp:3548-3583`) are logically identical to Zandronum's, including the same
third-toggle overlay→fullscreen edge case (`am_overlay == 1 && viewactive` clears only
`viewactive`, not a full `AM_Stop()`). UZDoom just doesn't expose that state to ACS the way
Zandronum does — it exposes the two booleans to ZScript instead, as native engine globals:

```text
DEFINE_GLOBAL(automapactive);
DEFINE_GLOBAL(viewactive);
```

(`src/g_game.cpp:3225-3226`). A UZDoom mod that wants `CheckAutomap()`'s three-state result would
have to read both ZScript globals itself and reconstruct the same off/fullscreen/overlay mapping
this function returns — there's no built-in call that already does it.
