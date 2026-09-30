# The `DECALDEF` lump

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** ZDoom Wiki `DECALDEF` (https://zdoom.org/w/index.php?title=DECALDEF&oldid=54190, retrieved 2026-09-28) + verified against the UZDoom source's `src/gamedata/decallib.cpp` and `decallib.h` (`ReadAllDecals`, `ReadDecals`, `GetDecalID`, `ParseDecal`, `ParseDecalGroup`, `ParseGenerator`, `ParseFader`, `ParseStretcher`, `ParseSlider`, `ParseColorchanger`, `ParseCombiner`, `AddDecal`, `FindAnimator`, `ReadScale`), `src/d_main.cpp` (the `ReadAllDecals` call), `src/scripting/thingdef_properties.cpp` (the `decal` property), `src/playsim/a_decals.cpp` (`DImpactDecal::StaticCreate`, `ShootDecal`, the map-placed `Decal` thing), `src/playsim/p_acs.cpp` (`SpawnDecal`), `src/playsim/p_map.cpp` (the blood-decal algorithm at lines 5190-5219), `src/playsim/p_actionfunctions.cpp` and `wadsrc/static/zscript/actors/actor.zs` (`A_SprayDecal`, `TraceBleed`, `TraceBleedAngle`), `wadsrc/static/mapinfo/common.txt` and `wadsrc/static/decaldef.txt`, and the Zandronum source's `src/decallib.cpp` and `decallib.h` (same functions), `src/d_main.cpp`, `src/thingdef/thingdef_properties.cpp`, `src/g_shared/a_decals.cpp`, `src/p_map.cpp` (`SpawnShootDecal`, the blood-decal algorithm at lines 4653-4683), `src/p_mobj.cpp` (the missile-impact decal), `src/p_acs.cpp` (`DoSpawnDecal`), `src/sv_commands.cpp` (`SERVERCOMMANDS_ShootDecal`), `src/cl_main.cpp` (the `SVC2_SHOOTDECAL` handler), `src/network.cpp` (connect-time lump authentication list), `wadsrc/static/actors/shared/decal.txt`, `wadsrc/static/decaldef.txt` and `wadsrc_st/static/decaldef.txt`. Keyword list cross-checked against SLADE's `z_decaldef` block in `dist/res/config/languages/zdoom.txt`; UltimateDoomBuilder has no DECALDEF config.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

DECALDEF defines **decals**: small textures stamped onto walls by bullet hits, projectile
explosions, blood, map-placed `Decal` things, ACS `SpawnDecal` and (UZDoom only) `A_SprayDecal`.
Besides plain decal definitions it has **decal groups** (pick one member at random), **generator**
lines (which decal an actor class leaves) and five kinds of **animator** (fade, stretch, slide,
recolor, and a combiner of the others). This page covers the lump's outer grammar, the order and
redefinition rules, errors, and where the two engines differ. The per-keyword detail of each block
type belongs to its own page.

## When it is read

- **Every lump named `DECALDEF` is parsed, in load order**, once at startup, after actor classes
  exist (`ReadAllDecals`, called from `d_main.cpp`). The engine's own `decaldef.txt` loads first,
  so a mod's lump can redefine stock decals by name.
- **Nearly every reference resolves at parse time**, against what has been defined so far across
  all earlier lumps. A decal group member, a `generator` target, a `lowerdecal`, an `animator` and
  a combiner's animators must all be defined **above** the line that names them. What happens when
  they aren't depends on the reference (see "Errors").
- **The one late reference is the DECORATE `Decal` property.** It stores the name, and the name is
  looked up only after every DECALDEF lump has been read, so DECALDEF order doesn't matter for it.
  An unknown name leaves the class with no decal, silently.

## Outer grammar

The lump is a flat sequence of top-level blocks and lines. Comments are `//` and `/* */`. Keywords
and decal names are case-insensitive.

```text
decal <name> [<id>] { <decal keywords> }
decalgroup <name> [<id>] { <member> <weight> ... }
generator [optional] <actor class> <decal or group | None>   // "optional" is UZDoom-only
fader <name> { DecayStart <sec> DecayTime <sec> }
stretcher <name> { GoalX <scale> GoalY <scale> StretchStart <sec> StretchTime <sec> }
slider <name> { DistY <units> SlideStart <sec> SlideTime <sec> }
colorchanger <name> { Color <color> FadeStart <sec> FadeTime <sec> }
combiner <name> { <animator> ... }
```

There are no game conditionals and no include directive. A minimal example that works on both
engines (the texture and actor class are the mod's own):

```text
fader MyScorchFade
{
    DecayStart 8
    DecayTime  2
}

decal MyScorchA
{
    pic MYSCRCH1
    shade "20 10 00"
    randomflipx
    animator MyScorchFade
}

decal MyScorchB
{
    pic MYSCRCH2
    shade "20 10 00"
    randomflipy
    animator MyScorchFade
}

decalgroup MyScorch
{
    MyScorchA 2
    MyScorchB 1
}

generator MyRocketProjectile MyScorch
```

### The four definition types

- **`decal <name> [<id>] { ... }`** defines one decal: its texture (`pic`), scale, render style,
  flips, colour, an optional animator and an optional `lowerdecal` drawn beneath it.
- **`decalgroup <name> [<id>] { ... }`** lists members, each a decal *or another group*, followed
  by an integer weight. Spawning a group picks a member by weight each time, repeating the pick
  while the result is itself a group.
- **`generator <class> <decal>`** sets which decal (or group) an actor class leaves: the puff or
  weapon for hitscan, the projectile for an explosion. `None` clears it. The class must already
  exist (DECORATE, and ZScript on UZDoom, are loaded before DECALDEF). A `generator` line wins over
  the class's own DECORATE `Decal` property: the line stores the resolved decal in the same slot
  the property's name occupies, and the later name lookup skips a slot that already holds one.
- **Animators** (`fader`, `stretcher`, `slider`, `colorchanger`, `combiner`) are named effects a
  decal attaches with `animator <name>`. Their times are in seconds (fractions allowed), converted
  to tics (x35, truncated) at parse time. See [animators](animators.md).

Decals and groups share one namespace. Animators have their own.

### IDs

The optional number after a decal or group name (1 to 65535) is for the map-placed `Decal` thing
(editor number 9200), whose first two args pick a decal by ID (`args[0] + args[1] * 256`). An ID is
unique: giving a new definition an ID that's already in use takes it away from the old one. Only
UZDoom's `Decal` thing can also pick a decal by name.

### Redefinition

- **Redefining a decal or group by name replaces it.** References to the old one are carried
  over: groups that listed it, decals that used it as `lowerdecal`, and every class whose
  generator pointed at it now use the new definition. This works across lumps, so a mod can
  replace a stock decal without touching the classes that use it.
- **A new definition without an ID drops the old one's ID.** To keep a stock decal usable from
  `Decal` things, repeat its ID.
- **Animators are not replaced.** A second animator with the same name is added alongside the
  first. Lines below it that name it get the new one; decals parsed earlier keep the old one.

## Blood decals

Wall blood uses two hardcoded names, `BloodSplat` and `BloodSmear` (a decal or a group; the stock
lump defines both as groups). `P_TraceBleed` (`p_map.cpp` on both engines) picks by damage:

| Damage | Decals traced toward nearby walls |
|---|---|
| 10 or less | none 160 times in 256 (62.5%), otherwise one `BloodSplat` |
| 11 to 14 | one `BloodSplat` |
| 15 to 24 | two `BloodSplat` |
| 25 or more | one `BloodSmear` 24 times in 256 (9.4%), otherwise three `BloodSplat` |

Each trace is randomly spread around the hit direction and reaches 172 units (on UZDoom,
GAMEINFO's `BloodSplatDecalDistance` overrides this when positive). Nothing is sprayed if the
victim has `NOBLOOD` or `NOBLOODDECALS`, is invulnerable, dormant or in god mode, or the
`cl_bloodsplats` cvar is off. The decal is tinted with the victim's blood color at half
brightness. Redefining either name in a mod's DECALDEF changes all wall blood. UZDoom's ZScript
also exposes the call as `TraceBleed` and `TraceBleedAngle`.

## Decal keywords at a glance

| Keyword | Value | UZDoom | Zandronum |
|---|---|---|---|
| `pic` | texture or graphic lump name | yes | yes |
| `x-scale`, `y-scale` | number, clamped to 1/256 .. 256 | yes | yes |
| `solid` | flag | yes | yes |
| `add`, `translucent` | alpha | yes | yes |
| `fuzzy` | flag | yes | yes |
| `shade` | colour, or `BloodDefault` | yes | yes |
| `colors` | two colours (a gradient translation) | yes | yes |
| `flipx`, `flipy`, `randomflipx`, `randomflipy` | flag | yes | yes |
| `fullbright` | flag | yes | yes |
| `animator` | animator name | yes | yes |
| `lowerdecal` | decal or group name | yes | yes |
| `translatable` | flag | yes | **fatal unknown keyword** |
| `opaqueblood` | flag, deprecated alias of `translatable` | yes | **fatal unknown keyword** |

`shade BloodDefault` uses the game's default blood colour (`gameinfo`). The last render-style
keyword in a block wins: `solid`, `add`, `translucent`, `fuzzy`, `shade` and (UZDoom)
`translatable` each overwrite it. Per-keyword detail: [the `decal` block](decal-definition.md).

**`lowerdecal` naming a group** differs by engine. UZDoom picks one member at load time, at
random, and uses it every time; redefining the group afterwards doesn't change the pick.
Zandronum stores the group and picks a member at every stamp (`decallib.cpp:958-970`,
`a_decals.cpp:679-682`).

## Errors

| Condition | UZDoom | Zandronum |
|---|---|---|
| Unknown top-level keyword, or unknown keyword inside a block | Fatal script error | Fatal script error |
| Missing `{` after the name (or ID) | Fatal: `Expected '{', got ...` | Same |
| ID outside 1 .. 65535 | Fatal: `Decal ID must be between 1 and 65535` | Fatal, with a garbled `Expected 'Decal ID must be between 1 and 65535'` message |
| Group member not defined yet | Fatal: `... has not been defined` | Same |
| `generator` names an unknown class, or a decal not defined yet | Fatal. With `optional`: an unknown class skips the line silently; a known class with an unknown decal gets its decal **cleared**, silently (this also discards its DECORATE `Decal` property). | Fatal, always |
| `animator` names an animator not defined yet | Red `Script error, "<lump>" line N: Unable to find animator ...` line that looks fatal but isn't (`ScriptMessage`); no animation | **Silent**; no animation |
| `lowerdecal` names a decal not defined yet | Silent; no lower decal | Same |
| Combiner lists an animator not defined yet | Fatal: `Undefined animator ...` | Same |
| `pic` names a missing texture | Silent at parse time. A `Decal` thing using it prints `does not have a valid texture` and spawns nothing. | Same |

**Animators that create nothing.** A `stretcher` with neither `GoalX` nor `GoalY`, a `slider`
without a nonzero `DistY`, and a `combiner` with no entries are parsed but never registered. A
later `animator` line naming one is then "not defined" (above). `DistX` in a slider is accepted and
ignored with a console message, on both engines.

## Engine-family divergence

The two parsers share one ancestor and differ only in small ways:

- **`translatable`** (and its deprecated alias `opaqueblood`) is UZDoom-only. On an unshaded decal
  it applies the translation the spawner passes in, so blood decals follow a bleeding actor's
  blood colour, and it forces the `solid` style. Zandronum rejects both keywords as fatal errors.
- **`generator optional`** is UZDoom-only. On Zandronum `optional` is read as the class name,
  which fails as `optional is not an actor`. Note that `optional` only silences errors: with a
  known class and an unknown decal, UZDoom still clears that class's decal (see "Errors").
- **Unknown `animator`**: UZDoom prints a console message, Zandronum says nothing.
- **`A_SprayDecal`** (a ZScript/DECORATE action that sprays a named decal) is UZDoom-only. ACS
  `SpawnDecal`, the DECORATE `Decal` property and the `Decal` thing exist on both; see
  [`../../acs/families/spawning.md`](../../acs/families/spawning.md) for `SpawnDecal`, whose
  `SDF_FIXED_ZOFF`/`SDF_FIXED_DISTANCE` flags are UZDoom-only.
- **Stock definitions** differ both ways. UZDoom's `decaldef.txt` adds ID24 decals and a few
  `generator` lines, and one blood-smear decal uses a different texture. Zandronum ships a second
  DECALDEF in `skulltag_actors.pk3` (`wadsrc_st/static/decaldef.txt`) with `generator` lines for
  the Skulltag classes (`Minigun`, `BFG10K`, `Railgun` and others). Don't assume a stock decal or
  generator exists on both without checking both engines' files.
- **SLADE's** keyword list includes `optional` but lacks `translatable` and `opaqueblood`.

## Zandronum-specific: which machine's copy is used

DECALDEF is not among the lumps Zandronum checksums when a client connects (`src/network.cpp`'s
authentication list), so a client and server can run different DECALDEF contents with no connect
error. Decals are purely visual, and each client draws them from its own copy:

- **Impact decals** (hitscan, projectile explosions, blood) are never created on a server at all.
  Clients create them, resolving the actor's generator against their own DECALDEF and DECORATE.
- **ACS `SpawnDecal`** on a server creates the decal there and sends clients the decal's *name*
  (`SVC2_SHOOTDECAL`). For a group, that's the group's name, not the member the server picked
  (`p_acs.cpp:5812-5826`, `sv_commands.cpp:5290`), so each client picks its own member (seen
  live, see [decalgroups-and-generators.md](decalgroups-and-generators.md)). Each
  client looks the name up in its own copy. A name the client doesn't have spawns nothing, with
  no message.
- **Map-placed `Decal` things** are never spawned on clients, so online only the server has the
  decal; see [the `decal` block](decal-definition.md#zandronum-specific-which-machines-copy-is-used).

Ship identical DECALDEF contents to server and clients if decals must look the same for everyone.

## See also

- [The `decal` block](decal-definition.md) for per-keyword detail, the ID and the `Decal` thing,
  including the Zandronum client gap.
- [Decal groups and generators](decalgroups-and-generators.md) for weights and picking, which
  impacts use a generator, inheritance, and redefinition traps.
- [Animators](animators.md) for each animator block's keywords, units, defaults and runtime
  behaviour.
- [`../../acs/families/spawning.md`](../../acs/families/spawning.md) for ACS `SpawnDecal`.
- [`../../console/notes/cl_maxdecals.md`](../../console/notes/cl_maxdecals.md) for the decal
  limit, and which decals it doesn't count.
- The DECORATE `Decal` property and the `FORCEDECAL`, `NODECAL`, `NOBLOODDECALS` flags in
  [`../../decorate/inventory/`](../../decorate/inventory/).
