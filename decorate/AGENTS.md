# decorate/ — DECORATE action functions, actor flags, actor properties

DECORATE semantics for UZDoom/GZDoom-family (primary target) and, where UZDoom/GZDoom-family's
ZScript-first codebase doesn't cover something Zandronum's older DECORATE-only codebase added or
kept, Zandronum instead — see `../shared/AUTHORING.md`'s "Engine scope". **Read
`../shared/AUTHORING.md` and `../shared/ARCHETYPES.md` first** — this file only covers what's
specific to DECORATE.

If the `zdoom-docs-lookup` subagent is registered, prefer delegating a lookup question to it
instead of reading this tree by hand — see the root [`AGENTS.md`](../AGENTS.md)'s "Subagents"
section.

## Layout

- `INDEX.md` — this section's router.
- `actions/<name>.md` — one file per action function (lowercase filename, e.g. `a_look.md` for
  `A_Look`). Archetype 1 (Callable).
- `classes/<name>.md` — one file per documented built-in DECORATE base class (lowercase filename,
  e.g. `randomspawner.md` for `RandomSpawner`) — the base classes a modder inherits from
  (`Inventory`, `Health`, `Key`, `Powerup`, `PlayerPawn`, `RandomSpawner`, `MapSpot`, `MapMarker`,
  `SwitchableDecoration`, `TeleportFog`, etc.), not a per-mod actor definition. Archetype 1
  (Callable) — same header-block shape as `actions/`, but the H1 is the class name, not a call
  signature, and `Bucket:` names the class's own definition site (see the bucket table below)
  rather than an action-function macro.
- `families/<topic>.md` — grouped action functions or classes, same three rationales as ACS's —
  see `../shared/AUTHORING.md`. Archetype 1.
- `inventory/actor-flags.md`, `inventory/actor-properties.md` — generated, complete tables of
  every actor flag / property the engine defines. Archetype 2 (Table-of-entries), generated half.
  Regenerate with `python3 tools/gen_inventory.py decorate-flags` /
  `python3 tools/gen_inventory.py decorate-properties`.
- `notes/<flag-or-property-name>.md` — curated prose for a flag/property that earns it (lowercase
  filename matching the inventory row's name column). Archetype 2, curated half.
- `concepts/<topic>.md` — DECORATE-specific knowledge not tied to one action/flag/property (the
  state-machine model, inheritance, `DEFINE_ACTION_FUNCTION`'s calling convention). Archetype 3.
  `concepts/crash-and-bug-checklist.md` is the DECORATE-specific crash/bug review index — read it
  before/during a DECORATE code review.

## The engine-source buckets

Unlike ACS's three cleanly-separated dispatch tables, DECORATE's engine-source surface is spread
across many files with a consistent macro shape, not a single indexed table:

| What | How to recognize it | Where it lives (Zandronum) |
|---|---|---|
| Action function | `DEFINE_ACTION_FUNCTION(<Class>, <Name>)` | Spread across ~85 files under `src/` — `p_enemy.cpp`, `p_pspr.cpp`, `p_user.cpp`, `g_shared/a_weapons.cpp`, `g_shared/a_pickups.cpp`, per-game `g_doom/`/`g_heretic/`/`g_hexen/`/`g_strife/a_*.cpp`, and more. Grep tree-wide (`grep -rn "DEFINE_ACTION_FUNCTION(.*, <Name>)" src/`); don't assume one file. |
| Actor flag | `DEFINE_FLAG`/`DEFINE_FLAG2`/`DEFINE_DEPRECATED_FLAG`/`DEFINE_DUMMY_FLAG` | `src/thingdef/thingdef_data.cpp` — five separate tables (`ActorFlags`, `InventoryFlags`, `WeaponFlags`, `PlayerPawnFlags`, `PowerSpeedFlags`), dispatched via `FlagLists[]` and resolved by `FindFlag()`. The macro's own arguments (`prefix, name, type, variable`) tell you the owning C++ class and which `flags`/`flags2`.../`flags7` word for free — record both, same reasoning as ACS's bucket rule. |
| Actor property | `DEFINE_PROPERTY`/`DEFINE_CLASS_PROPERTY`/`DEFINE_CLASS_PROPERTY_PREFIX` | `src/thingdef/thingdef_properties.cpp`. The `_PREFIX` variant's DECORATE spelling is `prefix.name` (e.g. `DEFINE_CLASS_PROPERTY_PREFIX(armor, maxbonus, I, BasicArmorBonus)` → `armor.maxbonus`). |
| Built-in base class | Two distinct shapes, check both before concluding a class doesn't exist: | |
| — native C++ class | `class A<Name> : public A<Parent>` | Spread across `src/g_shared/*.cpp`/`*.h` (most shared base classes — `a_pickups.h`, `a_artifacts.h`, `a_keys.h`, `a_sharedglobal.h`, `a_action.cpp`) and `src/d_player.h` (`APlayerPawn`). Grep tree-wide (`grep -rn "class A<Name>" src/`) — the native class defines the engine-side behavior (virtual method overrides like `TryPickup`/`Use`, native fields); record the file:line and parent class. |
| — DECORATE-only class | `ACTOR <Name> <doomednum> { ... }` with no backing native C++ class | `wadsrc/static/actors/**/*.txt` (e.g. `MapSpot`/`MapSpotGravity` in `wadsrc/static/actors/shared/sharedmisc.txt`) — the class is plain DECORATE inheriting from a native ancestor (`AActor`, etc.); record which `.txt` file and what it inherits from instead of a C++ file:line, since there is no native override to point at. |

The table above is Zandronum-side only by necessity, not by primary-engine framing — UZDoom's
equivalent surface has a fundamentally different shape (most of it moved into ZScript, not a
parallel set of C++ macro tables), so a "Where it lives (UZDoom)" column with a straight per-row
path wouldn't be accurate. See "UZDoom's ZScript source and the licensing guardrail" below for
where that side actually lives (`wadsrc/static/zscript/**/*.zs`) and the extractor conventions for
reading it.

A `DEFINE_ACTION_FUNCTION`'s **class** argument matters for inheritance — a function defined on
`AActor` is callable from any actor's state table; one defined on a narrower class (e.g.
`APlayerPawn`, `AWeapon`) only compiles in a state table for that class or its subclasses. Record
the class in the `Bucket:` field.

## Cross-engine divergence

DECORATE is not new to any ZDoom-family engine, but the flag/property/action-function *set* has
grown differently per fork since they diverged. UZDoom/GZDoom-family engines have added flags,
properties, and action functions Zandronum's older codebase never received (and vice versa,
rarely, for Zandronum-only multiplayer-specific additions). The `inventory/*.md` tables record
per-engine presence in their `Zan`/`UZD` columns for exactly this reason — always check both
before assuming a flag/property/action portable across engines.

## UZDoom's ZScript source and the licensing guardrail

Most DECORATE properties and many action functions no longer live in UZDoom's C++ at all — they
moved into `wadsrc/static/zscript/**/*.zs` (`property Name: field;` declarations; `A_*` methods
declared directly in a `class`/`extend class` body, often with a real ZScript body rather than a
`native` stub). `tools/gen_inventory.py`'s `decorate-properties`/`decorate-actions` extractors read
both the C++ side and this ZScript tree for the `UZD` presence column. Two things to know before
touching that code or hand-verifying a claim against it yourself:

- **ZScript keywords (`class`, `property`) are case-insensitive**, and the tree is inconsistent —
  most files spell them lowercase, but ~50 files use `Class Name : Parent` and 17 declarations use
  `Property Name: field;`. Any hand search or new extractor needs to match both cases (`re.I`), not
  just the common one.
- **Property names are PascalCase in ZScript over a differently-cased backing field**
  (`property Health: health;`), where Zandronum's C++ macro uses the backing-field-style name
  (`DEFINE_PROPERTY(health, I, Actor)`). DECORATE property names are case-insensitive at the
  language level, so matching exact-case between the two engines' sources under-reports presence.
- **UZDoom/GZDoom source, ZScript included, is GPL-3.0 and may never be quoted verbatim** (see
  `shared/AUTHORING.md`'s "Quoting engine/compiler source verbatim") — the reverse of the
  permissive-Zandronum/zt-bcc carve-out. `gen_inventory.py`'s ZScript extractors enforce this
  mechanically: they only ever pull a bare property/action **name** into a generated table cell —
  never the backing-field expression after a property's `:`, never a method's parameter list or
  body text, even though both are trivially available mid-regex-match. Names and facts aren't
  copyrightable and the tree already extracts names from GPL-3.0 C++ the same way; a pasted
  declaration or body would not be.
- **A `UZD: —` on a `class-property`/`property`-kind row isn't a reliable absence claim** if the
  two engines nest the property at different points in the class hierarchy (Zandronum's C++
  macros register some properties on a broader class than UZDoom's ZScript declares them on, e.g.
  `maxabsorb` on `Armor` vs. `BasicArmorBonus`) — the extractor doesn't do inheritance-aware
  matching. Spot-check the ZScript source directly before citing one of these rows as evidence a
  property doesn't exist on UZDoom.

## Writing a tier-B/C entry for DECORATE

Follow `../shared/AUTHORING.md`'s "Writing a tier-B/C entry" using the bucket table above for step
2 — a source-verified, no-wiki-intake-yet action-function entry follows the same
`actions/<name>.md` shape as a tier-A one, just without the wiki `Provenance:` line. Tier B for a
flag/property row is a `notes/` file, not a change to the row itself — see
`../shared/ARCHETYPES.md`'s Archetype 2.
