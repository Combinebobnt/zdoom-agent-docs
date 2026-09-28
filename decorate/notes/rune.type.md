# `rune.type <name>`

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** engine source only, via [`RuneGiver`](../classes/runegiver.md#runetype), which carries the full citation list. Zandronum: `src/thingdef/thingdef_properties.cpp:2224-2243`, `src/dobjtype.cpp:227-252`, `src/thingdef/thingdef_properties.cpp:2203-2218`, `src/thingdef/thingdef.cpp:302-307,318-321`. UZDoom absence checked at 5.1.0-pre @98b16b78fc (`src/scripting/decorate/thingdef_parse.cpp:944-977`).
**Bucket:** `DEFINE_CLASS_PROPERTY_PREFIX(rune, type, S, RuneGiver)` in Zandronum's `src/thingdef/thingdef_properties.cpp`.

Sets a `RuneGiver` subclass's `PowerupType` to the class `Rune<name>`. The full reference, with
the two fatal errors, the parse-order trap and the workaround, is the
[`Rune.Type` section of `RuneGiver`](../classes/runegiver.md#runetype). This note is a pointer so
the generated inventory row links there.

In short:

- `Unknown rune type` (`I_Error`) if no `Rune<name>` class exists yet when the line is parsed.
  The stock `Rune<Name>` classes live only in `skulltag_actors.pk3`, which is never autoloaded.
- `Invalid rune type` (`I_Error`) if `Rune<name>` exists but isn't a `Powerup`.
- Prefer `Powerup.Type` on a `RuneGiver` subclass: it takes any `Powerup` class, and a class
  whose name starts with `Power` resolves tentatively, so its declaration order doesn't matter.
  Any other name (a `Rune<name>` class included) must already be declared when the line is
  parsed. Otherwise the engine tentatively creates `Power<name>` instead, and startup fails with
  `Class Power<name> referenced but not defined`.

## Engine-family divergence

UZDoom has no rune system, no `RuneGiver` class and no `Rune.Type` property. The line is a fatal
`is an unknown actor property` error (`sc.ScriptError`, `src/scripting/decorate/thingdef_parse.cpp:977`)
on any actor, though a `RuneGiver` subclass already fails on its missing parent class. Details in [`RuneGiver`'s divergence section](../classes/runegiver.md#engine-family-divergence).
