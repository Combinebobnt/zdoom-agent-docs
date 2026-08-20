# ZScript doc index

Router only. **UZDoom/GZDoom-family only — see
[ZScript engine availability](concepts/zscript-engine-availability.md) before answering anything
here for a Zandronum-targeting project.** See `AGENTS.md` for engine-source buckets,
`../shared/AUTHORING.md` for tiers/engine-scope/licensing.

**Engine-version note (resolved 2026-08-03):** this tree's older convention of citing `UZDoom
4.15pre` was stale even before the checkout moved — [ZScript data types](concepts/data-types.md)
first caught `src/version.h` already reporting `5.0.0-pre`. The checkout has since been pulled
forward for real, landing on commit `fbad53bff5` (~750 commits / 8 months past the commit this
section was originally verified against). Every file in this section was re-verified against the
new commit and now cites `UZDoom 5.0.0-pre`. That pass mostly found no behavioral drift, but did
surface a few real changes (each noted in the affected file's own `**Provenance:**` line) and one
likely **upstream engine bug** worth flagging outside this docs tree too: `extend class`/`extend
struct` with no matching base in the same translation unit is now silently dropped instead of
raising a compile error — see [ZScript class definitions](concepts/zscript-class-definitions.md)'s
"Class extension" section (introduced by UZDoom commit `e85bf3f569`, which otherwise correctly
fixed an ordering restriction).

## Concepts

- [ZScript engine availability](concepts/zscript-engine-availability.md) — tier A. ZScript is
  completely absent from Zandronum (no parser, no VM, structurally predates it) and fully present
  in the local UZDoom checkout — every doc in this section is necessarily verified against
  UZDoom/GZDoom, never Zandronum.
- [ZScript load order and compile sequence](concepts/zscript-load-and-compile-order.md) — tier B.
  ZScript and DECORATE compile in sequence; DECORATE can inherit from ZScript but not vice versa;
  error handling differs between them.
- [ZScript special words](concepts/special-words.md) — tier A. Keywords for type inference
  (`let`), pass-by-reference parameters (`out`, `&`), vector operations (`dot`, `cross`),
  type-checking (`is`), and action-function context references (`self`, `invoker`).
- [ZScript statements](concepts/statements.md) — tier A. Control-flow constructs (if/else, switch,
  for, while, do-while, the four `foreach` variants, break/continue/return) and the switch
  int/name-only type constraint.
- [ZScript operators](concepts/operators.md) — tier B. Precedence, associativity, and
  ZScript-specific semantics: `~==` approximate-equality tolerance (1/65536), vector dot/cross
  products, string concatenation via `..`, `is` for inheritance checks, integer-division
  truncation, and the `<=>`/`<>=` three-way comparison.
- [ZScript data types](concepts/data-types.md) — tier B. Primitive scalar/vector type system
  (int/uint/double with `.min`/`.max`/`.NaN`/`.equal_epsilon`; Vector2/3/4 and Quat types, methods,
  and swizzle accessors) and special value types (String, Name, Sound, StateLabel, Color,
  TextureID, SpriteID, class types). Cross-references `function-pointers.md`, `array.md`,
  `associative-maps.md`, and `operators.md` rather than duplicating their scope. Corrects a
  pre-existing doc error (`Vector.Sum()` sums absolute values, not a plain algebraic sum) and notes
  a new UZDoom 5.0.0-pre feature (implicit int-to-`TextureID` casts).
- [ZScript function declarations and modifiers](concepts/functions.md) — tier B. Declaration
  syntax, `static`/`action`/`virtual` modifiers, multiple-return syntax, `in`/`out` parameters, and
  per-function VM resource limits (register/return counts).
- [Function pointers](concepts/function-pointers.md) — tier A. ZScript language feature enabling
  indirect function calls with callbacks and runtime polymorphism; fully supported in UZDoom
  5.0.0-pre, absent from Zandronum.
- [ZScript virtual functions and override dispatch](concepts/virtual-functions.md) — tier B.
  Override dispatch and `Super` calling, abstract functions, `virtual`/`virtualscope`/`clearscope`
  qualifiers, and per-lifecycle call semantics (Actor/PlayerPawn/Inventory/Weapon) for the
  most-used virtuals; not an exhaustive trace of every virtual across the class hierarchy. Notes a
  UZDoom 5.0.0-pre change: the damage-pipeline virtuals (`DoSpecialDamage`/`TakeSpecialDamage`/
  `ModifyDamage`/`AbsorbDamage`) gained new trailing params — existing overrides need updating to
  keep matching as `override`.
- [ZScript class definitions, modifiers, and hierarchy](concepts/zscript-class-definitions.md) —
  tier B. Class hierarchy overview, `play`/`ui`/`data` scope modifiers, the `abstract` modifier,
  and cross-mod class-extension rules. Corrects two wiki inaccuracies: `String` is a built-in
  primitive, not a class, and `Class<Object>.IsAbstract()` works (only the separate `Object`
  instance-method form of `IsAbstract()` is unimplemented). Documents a likely upstream engine bug
  in UZDoom 5.0.0-pre: an `extend class`/`extend struct` with no matching base in the same
  translation unit is now silently dropped instead of raising a compile error.
- [ZScript structs: semantics and native vs. scripted](concepts/structs.md) — tier A. Automatic
  pointer wrapping for struct parameters/return values, the `out` modifier's mutability semantics,
  and the native-vs-scripted struct distinction (native structs can't be instantiated, only
  referenced). Corrects a wiki claim that structs can't be passed/returned at all, and a
  pre-existing doc error: struct/dynarray/map parameters are never made read-only regardless of
  `out` (the engine's const-enforcement code path for these types is dead code).
- [Named arguments](concepts/named-arguments.md) — tier A. Version-gated named-argument rules:
  strict ordering/positional-only pre-4.13.0, relaxed in GZDoom 4.13.0+. Supersedes the
  version-unaware description previously in `decorate-to-zscript-differences.md`.
- [Object scopes and versions](concepts/object-scopes-and-versions.md) — tier B. The `data`/`play`/
  `ui` scope barrier system, the `version` directive, and scope keywords (`ui`, `play`,
  `clearscope`, `virtualscope`, plus the wiki-undocumented `unsafe(clearscope)`).
- [Custom properties](concepts/custom-properties.md) — tier A. Mapping custom property names to
  actor fields for initialization in `Default` blocks without a `BeginPlay` override.
- [ZScript actor flags](concepts/actor-flags.md) — tier A. How ZScript syntax exposes the actor
  flag table: `b`-prefixed boolean field access in code, `+`/`-` syntax in `Default` blocks, custom
  flags via `flagdef`, and the two flags requiring `A_ChangeLinkFlags()`. Cross-references
  DECORATE's `inventory/actor-flags.md` for the underlying flag table.
- [ZScript spawn flags](concepts/spawn-flags.md) — tier A. The separate `MTF_*` mapthing
  spawn-flag namespace, accessed via bitwise operations on a `SpawnFlags` uint rather than
  synthesized boolean fields — the key distinction from actor flags.
- [Mixins](concepts/mixins.md) — tier A. Named class-member groups (variables/methods/enums/
  structs/states/properties/flags/constants) reusable across classes; global-scope-only
  definition, classes-only usage, same-translation-unit scope, and a `flagdef` namespacing gotcha.
- [Global variables in ZScript](concepts/global-variables.md) — tier B. Built-in globals with
  `play`/`ui` scope qualifiers, and `StaticEventHandler`/`Thinker` patterns for custom persistent
  state. Known divergence: wiki lists ~60 globals; only ~21 verified present in the local UZDoom
  5.0.0-pre checkout.
- [Multiplayer-safe ZScript](concepts/multiplayer-safe-zscript.md) — tier B. Deterministic,
  desync-free ZScript: the packet-server model, scope enforcement, RNG separation
  (`Random` vs. `CRandom`), player-number handling, CVar lookups, and prediction safety.
  Engine-family note: the packet-server networking model is UZDoom-specific, not cross-checked
  against GZDoom's peer-to-peer model.
- [ZScript HUDs: design patterns and concepts](concepts/zscript-huds.md) — tier B. HUD design
  patterns (virtual resolution, coordinate system), play-scope-to-UI-scope event bridging via
  `SendInterfaceEvent`/`InterfaceProcess`, and the BaseStatusBar-vs-AltHUD class-role split.
  Deliberately scoped apart from `classes/basestatusbar.md`'s class reference.
- [ZScript menus](concepts/zscript-menus.md) — tier B. Menu base classes (`Menu`, `ListMenu`,
  `OptionMenu`, `GenericMenu`), menu items, and `ui`-scope restrictions. Corrects wiki constructor
  signatures for `OptionMenuItem`/`ListMenuItem` that omit real parameters found in source.
- [DECORATE to ZScript migration: syntax and language differences](concepts/decorate-to-zscript-differences.md)
  — tier A. Actor instantiation, property-type quotation, DoomEdNum placement, class naming,
  multi-return syntax, plus general language additions DECORATE never had: `readonly`,
  public-by-default access control, `let` type inference, and the absence of `&`/`*`.
- [Converting DECORATE code to ZScript](concepts/decorate-to-zscript-conversion.md) — tier B.
  Broader conversion patterns distinct from the file above: state-resolution null semantics,
  `Damage` → `DamageFunction`, direct flag assignment and subclass flag-prefix rules, `invoker`
  scope for weapon/CustomInventory code, and virtual lifecycle functions.
- [Custom data in savegames](concepts/savegame-custom-data.md) — tier B. The automatic per-field
  reflection mechanism (`SerializeUserVars`/`WriteAllFields`) that persists any custom
  Actor/Thinker/EventHandler field with zero code required, the `transient` opt-out, why there's
  no overridable `Serialize()` hook in ZScript despite one existing natively, and which of the two
  global-state patterns from `global-variables.md` actually survive a save.
- [Autosave and quicksave/quickload triggers](concepts/autosave-triggers.md) — tier B. The three
  ways an autosave can fire (`Level.MakeAutoSave()`, callable from play scope; the `Autosave`
  linedef special; the automatic `DAutosaver` thinker) versus the five UI-only manual save/load
  triggers, and why all three autosave paths capture identical custom data to a manual save but
  can't customize the save's own description/filename.

## Families

_None yet._ Several sibling pages were evaluated against `../shared/AUTHORING.md`'s three
family-file rationales (mandatory sequence / shared implementation / shared root cause) during
this batch and rejected: the CVar/LevelLocals/Structs-overview trio (distinct native structs, no
shared implementation), and the actor-functions/functions/virtual-functions trio (overlapping
topic, not a shared mechanism). See those files' own text for the reasoning if revisiting.

## Classes

- [Event handlers: StaticEventHandler and EventHandler](classes/eventhandler.md) — tier B.
  Lifecycle, virtual method overrides, and dispatch order for the two event handler base classes.
  Covers all event types (world/player/render/input/network, plus the 4.12+ network-entity API),
  handler ordering, and scope semantics. Known divergence noted: wiki claims RenderOverlay is
  reverse-ordered; source shows forward-order dispatch. Also corrects a wiki self-contradiction on
  whether `UiProcess`'s MouseX/MouseY are absolute or delta (source: absolute), and two pre-existing
  doc transcription errors (`WorldLightning`'s `WorldEvent e` param; `EventHandler.Find`'s declared
  `class<StaticEventHandler>` signature). Also corrects a previous-pass error in this same file:
  handlers do **not** have an overridable `Serialize()` virtual (none exists anywhere in the
  ZScript stdlib) — see [Custom data in savegames](concepts/savegame-custom-data.md) for the
  actual persistence mechanism.
- [Actor behavior management methods](classes/actor_behaviors.md) — tier A. `FindBehavior`,
  `AddBehavior`, `RemoveBehavior`, `TickBehaviors`, `ClearBehaviors`, `MoveBehaviors` — the only
  subsection of the wiki's "ZScript actor functions" page with real semantics beyond bare
  signatures; the page's remaining 100+ signatures didn't earn their cost per the Authoring rule.
- [BaseStatusBar and StatusBarCore](classes/basestatusbar.md) — tier A. HUD base class for status
  bars and fullscreen HUDs: virtual resolution, coordinate systems, event handler integration,
  MAPINFO registration, and the StatusBarCore engine-sharing split. Several wiki signature/version
  divergences corrected (see file).
- [`DynamicLight` class](classes/dynamiclight.md) — tier B. Dynamic light actors: color/intensity/
  animation-type parameters and rendering flags (additive/subtractive, attenuation, shadow maps).
  Corrects a wiki omission (`DONTLIGHTOTHERS` flag), an undocumented `LIGHT_SCALE` enum alias, and
  a pre-existing doc error (`ADDITIVE`/`SUBTRACTIVE` are independent flags, not mutually exclusive).
- [Dynamic arrays (`Array<T>`)](classes/array.md) — tier B. Resizable container with 16 methods
  across 9 element-type variants (int8/16/32, float, double, pointers, objects, strings, TRS).
  Corrects wiki gaps on element-type coverage and a stale bracket-spacing claim for nested
  `Array<Class<...>>` declarations.
- [Associative maps: `Map<K,V>` and `MapIterator<K,V>`](classes/associative-maps.md) — tier A.
  Type-safe generic key-value containers over a fixed set of 16 concrete instantiations; critical
  caveat on iterator invalidation when `Get()` inserts missing keys during iteration. Corrects a
  wiki error: `InsertNew` returns `void`, not `bool`.
- [`CVar` (struct)](classes/cvar.md) — tier A. `FindCVar`/`GetCVar` and type accessors for all five
  cvar types; per-player vs. global scope semantics. Corrects a stale wiki version-gate on the
  `GetDefault*` accessors and a missing `SaveConfig()` method; documents an undocumented menu-only
  write restriction on non-mod (hardcoded engine/game) cvars.
- [`LevelLocals` struct](classes/levellocals.md) — tier B. Level state, geometry arrays, and
  methods (iterators, sector/line manipulation, UDMF access). A dozen wiki/source divergences
  corrected (return types, omitted parameters/fields, mutability, deprecated members) — see file
  for the full list.
- [`SavegameManager` (struct) and `SaveGameNode`](classes/savegamemanager.md) — tier B. The
  `ui`-scope-only native struct backing the stock Load/Save menus — the sole ZScript path to
  `G_SaveGame`/`G_LoadGame`, plus `ExtractSaveData()`'s no-load metadata/thumbnail read. Not
  documented on the ZDoom Wiki.
