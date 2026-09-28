# MENUDEF item-keyword dispatch: closed on Zandronum, open on UZDoom

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc51 (2026-09-09); Zandronum 3.3-alpha @bdd0f7beb43d (2026-09-09)
**Provenance:** written from the UZDoom source's `src/common/menu/menudef.cpp` and the Zandronum
source's `src/menu/menudef.cpp`; no wiki page covers this.

MENUDEF's `ListMenu`/`OptionMenu` blocks are both a sequence of menu-item declarations, one
keyword per line (e.g. `TextField "Name", "cvar"`). How that keyword resolves to an actual item
implementation is the single biggest structural divergence between the two engines' otherwise
near-identical parsers, and every other MENUDEF doc in this section builds on it rather than
restating it.

## Zandronum: a closed, hardcoded keyword chain

`src/menu/menudef.cpp`'s block-body parsers (`ParseListMenuBody`, `ParseOptionMenuBody`) are a
long `if (sc.Compare("Keyword")) { ... } else if (sc.Compare("OtherKeyword")) { ... }` chain. Each
branch directly constructs a fixed C++ class — e.g. the option-menu body's `TextField` branch
(around `src/menu/menudef.cpp:826`) constructs an `FOptionMenuTextField`
(`src/menu/optionmenuitems.h`) after parsing its own argument list by hand. A keyword that isn't
one of the hardcoded `sc.Compare(...)` branches falls through to the chain's final `else` and is a
script error (`sc.ScriptError("Unknown keyword '%s'", sc.String)`).

The practical consequence: **the MENUDEF item-type set is closed on Zandronum.** A mod cannot add
a new MENUDEF keyword or a new item-widget type without an engine source change — there is no
plugin point, ZScript or otherwise, since Zandronum's own DECORATE-only codebase predates
ZScript's introduction upstream.

## UZDoom: an open, reflection-based keyword dispatch

`src/common/menu/menudef.cpp`'s equivalent fall-through branch (reached once every hardcoded
UZDoom-side keyword, like `Slider` or `StaticText`, has already been checked) does not error
immediately. Instead it builds a class name by prefixing the keyword text with `OptionMenuItem`
(`menudef.cpp:1128-1130`; the list-menu body uses the same pattern with a `ListMenuItem` prefix)
and resolves that name to an actual ZScript class via `PClass::FindClass`. If the class resolves
and is a descendant of `OptionMenuItem` (or `ListMenuItem`), the parser looks up an `Init` method
on it and requires that method be public — `menudef.cpp:1133`'s check rejects a `protected` or
`private` `Init`, which marks an internal implementation class not meant to be reached from
MENUDEF text directly. If a public `Init` is found, the parser reads MENUDEF's own argument list
and calls it via the VM, constructing whatever ZScript object the class describes.

The practical consequence: **the MENUDEF item-type set is open on UZDoom.** Any ZScript class
deriving from `OptionMenuItem`/`ListMenuItem` with a public `Init` method becomes a usable MENUDEF
keyword — the keyword text is just that class's name with the `OptionMenuItem`/`ListMenuItem`
prefix stripped — including a class defined by a loaded mod's own ZScript, not just the engine's
stock set. The stock classes live in
`wadsrc/static/zscript/engine/ui/menu/{listmenuitems,optionmenuitems}.zs`, with a few more
contributed by sibling files under the same `ui/menu/` directory (e.g. `joystickmenu.zs`,
`reverbedit.zs`) — the true count is a source enumeration, not a fixed number worth repeating in
prose here, since a mod can add to it at any time regardless of what the engine itself ships.

## Why this matters for the rest of this section

Because the keyword set is closed on Zandronum, every Zandronum-only MENUDEF keyword (see
`shared/AUTHORING.md`'s engine-scope rules) is necessarily a hardcoded engine addition, findable
by grepping `src/menu/menudef.cpp`'s own `sc.Compare(...)` chain and matching author-attribution
comments — there is no separate "did a mod add this" question to ask, unlike UZDoom where a
keyword's absence from the engine's own `.zs` files doesn't mean it doesn't exist in a given game's
loaded content. A `notes/`/`inventory/` entry for a Zandronum-only item type should cite the
`sc.Compare(...)` branch and its constructed C++ class directly; a UZDoom-side entry should cite
the ZScript class and its `Init` signature instead.
