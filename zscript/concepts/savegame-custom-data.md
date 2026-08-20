# Custom data in savegames

**Tier:** B — reverse-engineered directly from UZDoom engine source; no ZDoom Wiki page documents
this mechanism at the level of detail below (the wiki's savegame-related pages describe the
`.zds` file layout and menu-level save/load flow, not the underlying field-serialization
mechanism).
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** Verified against the UZDoom source's `src/common/objects/dobject.cpp`,
`src/common/objects/dobjtype.cpp`, `src/common/engine/serializer.cpp`, `src/events.cpp`, and
`src/g_levellocals.h`.

A mod can make arbitrary custom data survive a save/load cycle without writing any serialization
code at all, for any object whose class it controls. This is a side effect of how the engine
serializes every `Object`-derived instance generically, not a dedicated "save custom data" API.

## The mechanism: automatic per-field reflection

Every `Object`-derived instance that gets written into a save — an `Actor`, a `Thinker`, or a
custom class deriving from either — has its ZScript-declared fields serialized generically by the
engine's own object archiver. Concretely: the archiver calls `SerializeUserVars()` on every object
it writes or reads, which in turn calls the owning class's `WriteAllFields()`/`ReadAllFields()` —
a reflection walk over that class's (and its parent classes') declared fields. Each class's field
block is tagged with the class's own type name so that a subclass's fields never collide with or
get misread as a parent class's fields of the same name.

The practical upshot: declare a field —

```zscript
class MyThinker : Thinker
{
    int myCustomCounter;
    string myCustomLabel;
    Array<int> myCustomHistory;
}
```

— and its value is written into the save when `myCustomCounter`'s owning object is archived, and
restored to the same value on load. No override, no explicit read/write call, nothing beyond the
field declaration itself.

## Opting out: `transient`

A field marked `transient` is skipped by this reflection walk in both directions — useful for
cached/derived state (a lookup table rebuilt in `PostBeginPlay`, a per-session-only counter) that
shouldn't round-trip through a save. This is the only opt-out; there's no equivalent "opt a field
in" qualifier, since normal fields are included by default.

## There is no overridable `Serialize()` hook

Unlike the native C++ side (where `DObject::Serialize()`/`DThinker::Serialize()` are real
overridable virtuals that native engine classes use to control exactly what gets archived and
how), **no such hook is exposed to ZScript.** A full-tree, case-sensitive grep of
`wadsrc/static/zscript/` for the literal text `Serialize` turns up exactly one hit anywhere, and it
isn't even a declaration — it's a doc-comment ("Serializes a dictionary to a string") on
`Dictionary`'s unrelated `ToString()`/`FromString()` string-(de)serialization helpers in
`engine/dictionary.zs`, which has nothing to do with savegames. Neither `Object`, `Thinker`,
`StaticEventHandler`, nor `EventHandler` declares a virtual `Serialize()` a mod class could
override. All ZScript-side control over what persists is therefore exercised entirely through
field declarations (plain field = included, `transient` = excluded) —
there's no way to, say, write a derived/computed value into the save instead of a raw field, or to
version-migrate an old field layout by hand, from ZScript alone.

(An earlier version of [Event handlers: `StaticEventHandler` and
`EventHandler`](../classes/eventhandler.md) claimed handlers "can override virtual `Serialize()` to
control what state persists" — that claim did not hold up against the stdlib source and was
corrected in that file on 2026-08-05.)

## Where to anchor data that isn't naturally tied to one actor

The mechanism above only fires for objects that are actually part of the save's object graph.
Two patterns exist for global (not-per-actor) persistent state, with different save-survival
characteristics — see [Global variables in ZScript](global-variables.md)'s "Creating custom
global variables" section for the full comparison and code patterns:

- A `Thinker` (registered with `STAT_STATIC` to also survive map-to-map travel within a session)
  is part of the level's thinker list, which is archived — so its fields persist across
  save/load, via the exact mechanism described above.
- A non-static `EventHandler` (map-scoped) is also archived — its owning `EventManager`'s handler
  chain is explicitly serialized as part of the level snapshot (`arc("firstevent",
  localEventManager->FirstEventHandler)` / `("lastevent", ...)` in `src/p_saveg.cpp`). Its fields
  persist the same way.
- A `StaticEventHandler` (session-global, not map-scoped) is **not** archived at all: it lives in
  a separate, singular `staticEventManager` (`src/events.cpp`) that the per-level archive code
  never touches, distinct from each level's own `localEventManager`. Fields on a
  `StaticEventHandler` never survive a save/load — only a fresh initialization
  (`EventManager::InitStaticHandlers()`, itself skipped entirely when restoring from a save, so a
  `StaticEventHandler`'s state during a loaded game is whatever the *previous* session's
  initialization left it as, not anything freshly computed nor anything from the save file).

## `WorldEvent.IsSaveGame`

A `WorldLoaded`/`WorldUnloaded` override can check `WorldEvent.IsSaveGame` to distinguish a
savegame load from a fresh level entry — useful for one-time fixup logic that should only run on
one path or the other (e.g. re-deriving a `transient` cache after a load, or skipping a
one-time-per-new-game setup step when actually restoring). See [Event handlers:
`StaticEventHandler` and `EventHandler`](../classes/eventhandler.md) for the full event-dispatch
detail.

## No generic named-value API

There is no ZScript equivalent of directly writing an arbitrary named entry into a save's
`info.json`/`globals.json` (the way the native C++ `FSerializer`'s `arc("key", value)` call can,
freely, from engine code) — no `SaveGame.WriteValue(name, value)`-shaped native exists. Every path
to custom persisted data goes through the field-reflection mechanism above, anchored to an object
that's actually part of the save's serialized graph.
