# CloseMenu

**Tier:** A
**Engine:** Zandronum 3.2.1 (added in commit `9fd1b90e1`, 2024-01-22, "Added ACS functions: OpenMenu and CloseMenu" — this predates the 3.2.1 version-bump commit `28f736fb3`, 2025-08-04, so it is confirmed present in 3.2.1).
**Provenance:** [CloseMenu - Zandronum Wiki](https://wiki.zandronum.com/w/index.php?title=CloseMenu&oldid=2243), verified against the Zandronum source on 2026-07-29.

```
int CloseMenu (void)
```

Extension function, index -171 (`zt-bcc/lib/zcommon.bcs`); implemented as `case ACSF_CloseMenu:` in `p_acs.cpp`.

## Usage

Closes the menu the activator is currently using (a menu defined in `MENUDEF`, opened either by
the player or previously by [OpenMenu](openmenu.md)).

## Behavior and fork divergence

The wiki claims the return value is "1 if the menu was closed successfully, or 0 on error (e.g.
if the client is not currently in a menu)". That is **not what this fork actually does**:

- The function never checks whether a menu is actually open, on either side.
- **Server (`NETSTATE_SERVER`):** returns `0` only if `activator` is `NULL` or has no
  `player` (e.g. called from a non-player-activated script context). Otherwise it calls
  `SERVERCOMMANDS_CloseMenu(...)` to tell that client to close its menu, and unconditionally
  returns `1` — regardless of whether the target client is actually in a menu.
- **Client-side / non-networked (`M_ClearMenus()`):** called directly, and the function
  unconditionally returns `1`. `M_ClearMenus()` itself is a safe no-op if no menu is open
  (`if (DMenu::CurrentMenu != NULL) { ...Destroy... }`), so "closing" when nothing is open is
  not an error — it just silently does nothing while the ACS call still reports success.
- The server→client path (`ServerCommands::CloseMenu::Execute()` in `cl_main.cpp`) that the
  receiving client eventually runs also just calls `M_ClearMenus()` unconditionally, with no
  "was a menu actually open" check either.

So in practice, the only way to get a `0` return is an invalid/non-player activator on the
server; "was already not in a menu" is indistinguishable from "successfully closed" — both
report `1`.

## See also

- [OpenMenu](openmenu.md)
