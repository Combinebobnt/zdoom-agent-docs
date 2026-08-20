# CloseMenu

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** [CloseMenu - Zandronum Wiki](https://wiki.zandronum.com/w/index.php?title=CloseMenu&oldid=2243), verified against the Zandronum source on 2026-07-29.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

```text
int CloseMenu (void)
```

Extension function, index -171 (`zt-bcc/lib/zcommon.bcs`); implemented as `case ACSF_CloseMenu:` in `p_acs.cpp`.

## Usage

Closes the menu the activator is currently using (a menu defined in `MENUDEF`, opened either by
the player or previously by [OpenMenu](openmenu.md)).

## Wiki/engine divergence: return-value claim

The wiki claims the return value is "1 if the menu was closed successfully, or 0 on error (e.g.
if the client is not currently in a menu)". That is **not what Zandronum actually does**:

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

## Engine-family divergence

`CloseMenu` is ACSF (CALLFUNC) index 171, inside the 100–199 range UZDoom reserves for
Zandronum's extensions and implements none of. Its `CallFunction` dispatcher is a `switch` with
no `case` for this index, falling to `default: break;` and returning `0` — no error, no log line,
execution just continues.

That silent `0` is a bigger behavior change here than the index-171-generic case, because of what
this file already establishes about the real (Zandronum) implementation above: `CloseMenu` almost
never returns `0` there — only an invalid/non-player activator produces it, and every other call
unconditionally reports `1` regardless of whether a menu was actually open. Under UZDoom that
inverts: the return is unconditionally `0` on every call, and — more importantly — none of the
real side effect happens either. There's no `SERVERCOMMANDS_CloseMenu`/`M_ClearMenus()` call at
all, since the dispatcher never reaches this function's implementation. A script that calls
`CloseMenu` expecting the player's open menu to dismiss gets no error and no visible failure — the
menu simply stays open, exactly as if the call were never made, while the script itself proceeds
as though it succeeded (or, reading the `0`, as though the "invalid activator" case fired, which
it didn't). See [OpenMenu](openmenu.md) for the counterpart call this pairs with — same reserved-
range mechanism, same silent-no-op shape under UZDoom.

See [Zandronum/UZDoom compatibility](../concepts/zandronum-uzdoom-compat.md) for the general
mechanism (reserved ACSF range, `default: break;` dispatcher, why this differs from an unknown-PCD
failure).
