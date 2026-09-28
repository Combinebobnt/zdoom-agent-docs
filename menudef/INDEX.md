# MENUDEF doc index

Router only. See `AGENTS.md` for where MENUDEF parsing lives in engine source,
`../shared/AUTHORING.md` for tiers/engine-scope/licensing.

## Concepts

- [Item-keyword dispatch model](concepts/item-dispatch-model.md) — tier B. The section-defining
  divergence: Zandronum resolves a MENUDEF keyword through a hardcoded, closed `sc.Compare(...)`
  chain that constructs a fixed C++ class per keyword; UZDoom resolves it dynamically via
  `PClass::FindClass` against a ZScript class name, so the item-type set is open to any mod-defined
  class with a public `Init` method. Every other file in this section should cross-reference this
  one rather than restate it.

## Inventory tables (hand-written — no extractor exists yet)

`PClass::FindClass`-based enumeration on the UZDoom side would need runtime reflection data this
tree's static-analysis extractors don't have a precedent for, so these are a source-read bootstrap
(tier C throughout) rather than generator output, same starting state `mapinfo/`/`sbarinfo/`/
`cvarinfo/` began from.

- [`ListMenu` item keywords](inventory/listmenu-items.md) — 11 keywords, both engines' presence.
- [`OptionMenu` item keywords](inventory/optionmenu-items.md) — 31 rows: base set (12 keywords on
  both engines), Zandronum-only additions (6 items + 2 menu-level flags), UZDoom-only additions (11
  keywords).

## Notes (curated, per item type)

- [`TextField`](notes/textfield.md) — tier A. Base-grammar option-menu text field; Zandronum caps
  input at 127 characters, UZDoom has no fixed limit.
- [`NumberField`](notes/numberfield.md) — tier A. Base-grammar option-menu numeric field; wraps at
  `minimum`/`maximum` rather than clamping, on both engines.
- [`PlayerField`](notes/playerfield.md) — tier A. Zandronum-only player-selector item; `nobots`/
  `notself` attributes.
- [`NetgameOnly`](notes/netgameonly.md) — tier A. Zandronum-only descriptor flag; blocks menu
  opening outside a netgame with an on-screen error.
