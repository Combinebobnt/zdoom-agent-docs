# OpenMenu

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** [OpenMenu - Zandronum Wiki](https://wiki.zandronum.com/w/index.php?title=OpenMenu&oldid=2261), verified against the Zandronum source on 2026-07-29.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

```text
int OpenMenu (str name)
```

Extension function, index -170 (`zt-bcc/lib/zcommon.bcs`); implemented as `case ACSF_OpenMenu:` in `p_acs.cpp`.

## Usage

Opens a menu for the activating player — a menu defined in `MENUDEF`, or (see below) any class
descending from `DMenu`.

## Parameters

- `name`: the menu's name. The wiki says "as defined in MENUDEF", which is the common case, but
  the actual validity check (`M_IsValidMenu()` in `menu.cpp`) accepts two things: a key present
  in `MenuDescriptors` (i.e. a `MENUDEF`-defined menu), *or*, if that lookup fails, a class name
  resolvable via `PClass::FindClass()` that is a descendant of `DMenu`. So a hardcoded native
  menu class name also works, not just MENUDEF entries.

## Return value

Matches the wiki: returns `1` if the menu was opened, `0` on error. Unlike `CloseMenu`, this
function *does* validate before acting:

- **Server (`NETSTATE_SERVER`):** first calls `M_IsValidMenu(name)` — returns `0` immediately if
  the name resolves to neither a MENUDEF entry nor a `DMenu`-derived class. Then returns `0` if
  `activator` is `NULL` or has no `player` (non-player-activated script context). Otherwise it
  calls `SERVERCOMMANDS_OpenMenu(...)` to tell that client to open the menu, and returns `1`.
- **Client-side / non-networked:** same `M_IsValidMenu()` check (`0` on failure), otherwise calls
  `M_StartControlPanel(true)` then `M_SetMenu(name, -1)` directly and returns `1`.
- **Server → client execution (`ServerCommands::OpenMenu::Execute()`, `cl_main.cpp`):** the
  receiving client does **not** blindly trust the server's menu name — it re-runs
  `M_IsValidMenu(menu)` itself and silently does nothing (`return;`, no error surfaced back) if
  that fails, before calling the same `M_StartControlPanel(true)` / `M_SetMenu(menu, -1)` pair.
  This means a server-side call can return `1` (the name was valid when the server checked it)
  while the client still ends up not opening anything, if some client-side state makes the name
  invalid there — though in practice `MenuDescriptors`/class tables are the same on both sides,
  so this is a theoretical rather than commonly-hit gap.

So, unlike `CloseMenu` (which never checks whether a menu is actually open and effectively always
reports success for a valid player activator), `OpenMenu`'s `0` return genuinely means "this name
isn't a real menu" or "no player activator" — its wiki-documented return semantics hold up against
the fork source.

## See also

- [CloseMenu](closemenu.md) — added in the same commit; note that function's return-value
  behavior diverges from its own wiki page in ways `OpenMenu`'s does not.

## Engine-family divergence

`OpenMenu` is ACSF (CALLFUNC) index 170, inside the 100–199 range UZDoom reserves for Zandronum's
extensions and implements none of. Its `CallFunction` dispatcher is a `switch` with no `case` for
this index, falling to `default: break;` and returning `0` — no error, no log line, execution just
continues.

That silent `0` return happens to line up with one of this function's two genuine Zandronum
failure returns (invalid menu name, no player activator) — but the side effect doesn't happen
either way: there's no `M_IsValidMenu()` check, no `SERVERCOMMANDS_OpenMenu(...)`/
`M_StartControlPanel(true)`+`M_SetMenu(...)` call, nothing, since the dispatcher never reaches this
function's implementation. A script that calls `OpenMenu` expecting the named menu to appear for
the activating player gets a `0` back indistinguishable from "invalid menu name" and no visible
failure — the menu simply never opens, exactly as if the call were never made. Unlike `CloseMenu`,
whose Zandronum-side `0` is rare enough that a UZDoom `0` is already a strong tell something's
wrong, `OpenMenu` returning `0` is unremarkable on both engines, so this divergence is easy to miss
by reading return values alone. See [CloseMenu](closemenu.md) for the counterpart call this pairs
with — same reserved-range mechanism, same silent-no-op shape under UZDoom.

See [Zandronum/UZDoom compatibility](../concepts/zandronum-uzdoom-compat.md) for the general
mechanism (reserved ACSF range, `default: break;` dispatcher, why this differs from an unknown-PCD
failure).
