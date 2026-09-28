# `ListMenu` item keywords

**Generated:** by hand — no `tools/gen_inventory.py` extractor exists for this table yet
(`PClass::FindClass`-based enumeration needs runtime reflection data this tree's static-analysis
extractors don't have a precedent for — see `maintainer/plans/2026-09-09_menudef_section.md`'s "Not
in scope" note). Rows below are a source-read bootstrap, same starting state
`mapinfo/`/`sbarinfo/`/`cvarinfo/` began from. A future `notes/<item-name>.md` promotes a row's
`Tier` cell the normal Archetype 2 way; this file's own rows are otherwise hand-maintained until an
extractor exists.
**Tier:** C for every row (defaults to C until a `notes/` file promotes it).
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc51 (2026-09-09); Zandronum 3.3-alpha @bdd0f7beb43d (2026-09-09).

See [`concepts/item-dispatch-model.md`](../concepts/item-dispatch-model.md) for how a `ListMenu`
block's keyword resolves to the class in the `UZDoom class`/`Zandronum class` columns below — on
UZDoom every row here (not just mod-added ones) goes through the same `PClass::FindClass("ListMenuItem"
+ keyword)` reflection lookup; on Zandronum every row is a fixed branch in `src/menu/menudef.cpp`'s
`ParseListMenuBody`/`DoParseListMenuBody` hardcoded `sc.Compare(...)` chain. This table only covers
actual **item** keywords (the things `ListMenu`'s body pushes onto `desc->mItems`); block-header
settings parsed by the same chain (`Class`, `Selector`, `Linespacing`, `Position`, `Centermenu`,
`MouseWindow`, `Font`, `NetgameMessage`, and UZDoom's further additions `TooltipFont`, `size`,
`ForceList`, `CenterText`, `Tooltip`, `DontDim`, `DontBlur`, `Selecteditem`, `animated`/
`animatedtransition`) are out of scope for this file — they configure the descriptor, not an item.

| Keyword | UZDoom class | Zandronum class | Zan | UZD | Tier | Notes |
|---|---|---|---|---|---|---|
| StaticPatch | `ListMenuItemStaticPatch` (`listmenuitems.zs`) | `FListMenuItemStaticPatch` (`menu.h`) | yes | yes | C | |
| StaticPatchCentered | `ListMenuItemStaticPatchCentered` (subclass, `listmenuitems.zs`) | `FListMenuItemStaticPatch` + `centered=true` ctor arg | yes | yes | C | UZDoom uses a dedicated subclass; Zandronum reuses the plain class with a bool |
| StaticText | `ListMenuItemStaticText` (`listmenuitems.zs`) | `FListMenuItemStaticText` (`menu.h`) | yes | yes | C | |
| StaticTextCentered | `ListMenuItemStaticTextCentered` (subclass, `listmenuitems.zs`) | `FListMenuItemStaticText` + `centered=true` ctor arg | yes | yes | C | same centered-subclass-vs-bool split as `StaticPatchCentered` |
| PatchItem | `ListMenuItemPatchItem` (`listmenuitems.zs`) | `FListMenuItemPatch` (`menu.h`) | yes | yes | C | |
| TextItem | `ListMenuItemTextItem` (`listmenuitems.zs`) | `FListMenuItemText` (`menu.h`) | yes | yes | C | |
| PlayerDisplay | `ListMenuItemPlayerDisplay` (`playerdisplay.zs`) | `FListMenuItemPlayerDisplay` (`menu.h`) | yes | yes | C | 3D player-model preview widget |
| PlayerNameBox | `ListMenuItemPlayerNameBox` (`playercontrols.zs`) | `FPlayerNameBox` (`menu.h`) | yes | yes | C | |
| ValueText | `ListMenuItemValueText` (`playercontrols.zs`) | `FValueTextItem` (`menu.h`) | yes | yes | C | |
| Slider | `ListMenuItemSlider` (`playercontrols.zs`) | `FSliderItem` (`menu.h`) | yes | yes | C | not to be confused with `OptionMenu`'s own `Slider` keyword, a different keyword/class pair — see `optionmenu-items.md` |
| CaptionItem | `ListMenuItemCaptionItem` (`listmenuitems.zs`) | — no match in `menu.h`/`menudef.cpp` | no | yes | C | UZDoom-only; post-fork addition, no `[TP]`/`[AK]`/`[BB]` marker (not Zandronum-attributed, just absent) |

**Enumeration note:** the UZDoom `ListMenuItem*` class set spans more than
`wadsrc/static/zscript/engine/ui/menu/listmenuitems.zs` alone — `playerdisplay.zs` and
`playercontrols.zs` under the same directory each contribute one or more classes (see the table
above); this list is the full set found across all of `ui/menu/*.zs` as of the verified commit, not
just the two files the plan's Phase 1 scope note named as a starting guess.
