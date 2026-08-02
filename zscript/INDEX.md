# ZScript doc index

Router only. **UZDoom/GZDoom-family only — see
[ZScript engine availability](concepts/zscript-engine-availability.md) before answering anything
here for a Zandronum-targeting project.** See `CLAUDE.md` for engine-source buckets,
`../shared/AUTHORING.md` for tiers/engine-scope/licensing.

## Concepts

- [ZScript engine availability](concepts/zscript-engine-availability.md) — tier A. ZScript is
  completely absent from Zandronum (no parser, no VM, structurally predates it) and fully present
  in the local UZDoom checkout — every doc in this section is necessarily verified against
  UZDoom/GZDoom, never Zandronum.
- [ZScript load order and compile sequence](concepts/zscript-load-and-compile-order.md) — tier B.
  ZScript and DECORATE compile in sequence; DECORATE can inherit from ZScript but not vice versa;
  error handling differs between them.
- [Function pointers](concepts/function-pointers.md) — tier A. ZScript language feature enabling
  indirect function calls with callbacks and runtime polymorphism; fully supported in UZDoom
  4.15pre, absent from Zandronum.
- [DECORATE to ZScript migration: actor-definition differences](concepts/decorate-to-zscript-differences.md)
  — tier A. Actor instantiation, strict property-type quotation rules, DoomEdNum placement, and
  named-argument ordering constraints when migrating from DECORATE to ZScript.

## Families

_None yet._

## Classes

- [Event handlers: StaticEventHandler and EventHandler](classes/eventhandler.md) — tier B.
  Lifecycle, virtual method overrides, and dispatch order for the two event handler base classes.
  Covers all event types (world/player/render/input/network), handler ordering, and scope
  semantics. Known divergence noted: wiki claims RenderOverlay is reverse-ordered; source shows
  forward-order dispatch.
