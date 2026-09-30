# DECALDEF decal groups and generators

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/gamedata/decallib.cpp` (`FDecalGroup`, `FDecalGroup::GetDecal`, `ParseDecalGroup`, `ParseGenerator`, `AddDecal`, `ReplaceDecalRef`, `ScanTreeForName`, `GetDecalByName`, `ReadAllDecals`), `src/common/utility/weightedlist.h` (`TWeightedList::AddEntry`, `PickEntry`, `RecalcRandomVals`, `ReplaceValues`), `src/common/engine/m_random.h` (`FCRandom`), `src/common/engine/sc_man.cpp` (`FScanner::GetNumber`), `src/scripting/thingdef_properties.cpp` (the `decal` property), `src/gamedata/info.cpp` (`PClassActor::StaticInit`, `PClassActor::InitializeDefaults`), `src/scripting/decorate/thingdef_parse.cpp` and `src/scripting/zscript/zcc_compile_doom.cpp` (`ZCCDoomCompiler::InitDefaults`), `src/playsim/actor.h` (`PClass::FindActor`), `src/d_main.cpp` (startup order), `src/gamedata/d_dehacked.cpp` (the DeHackEd `Decal` field), `src/playsim/p_map.cpp` (`P_LineAttack`, `P_RailAttack`, `P_TraceBleed`, `SpawnShootDecal`), `src/playsim/p_mobj.cpp` (`P_ExplodeMissile`), `src/playsim/a_decals.cpp` (`DImpactDecal::StaticCreate`, `ShootDecal`, the `Decal` thing's `SpawnDecal`), `src/playsim/p_acs.cpp` (`ACSF_SpawnDecal`), `wadsrc/static/zscript/actors/actor.zs`, `wadsrc/static/zscript/actors/heretic/weaponmace.zs`, `wadsrc/static/decaldef.txt`, and the history of that file and `p_map.cpp` (commits `19444194a5`, `057b746e58`); and the Zandronum source's `src/decallib.cpp` (same functions), `src/weightedlist.h`, `src/m_random.h`, `src/sc_man.cpp`, `src/thingdef/thingdef_properties.cpp`, `src/dobjtype.cpp` (`PClass::CreateDerivedClass`, `PClass::InitializeActorInfo`), `src/thingdef/thingdef.cpp`, `src/info.cpp` (`FActorInfo::StaticInit`), `src/d_main.cpp`, `src/d_dehacked.cpp`, `src/p_map.cpp` (same functions, plus `cl_hitscandecalhack`), `src/p_mobj.cpp`, `src/g_shared/a_decals.cpp`, `src/p_acs.cpp`, `src/cl_main.cpp`, `wadsrc/static/actors/heretic/hereticweaps.txt`, `wadsrc/static/decaldef.txt` and `wadsrc_st/static/decaldef.txt`. Keyword names cross-checked against SLADE's `z_decaldef` block in `dist/res/config/languages/zdoom.txt`.

A **decal group** is a named, weighted list whose members are decals or other groups. Anything
that spawns a group picks one member at random at that moment. A **generator** line attaches a
decal or group to an actor class, and is what hitscan and projectile impacts read. This page
covers both in detail on each engine. The lump's outer grammar, load order and redefinition rules
are on the section's lump page, [The DECALDEF lump](decaldef-lump.md); single decal definitions are on
[decal-definition.md](decal-definition.md), animators on [animators.md](animators.md).

## `decalgroup`

```text
decalgroup <name> [<id>]
{
    <decal or group name> <weight>
    ...
}
```

| Part | Value | Meaning | UZDoom | Zandronum |
|---|---|---|---|---|
| `<name>` | string | Group name. Shares one case-insensitive namespace with decals. | yes | yes |
| `<id>` | 1 .. 65535, optional | ID for the map-placed `Decal` thing; see the lump page's "IDs". | yes | yes |
| member name | decal or group name | Must be defined **above** this line, in this lump or an earlier one. Case-insensitive. | yes | yes |
| `<weight>` | integer | Relative chance. Required after every member. | yes | yes |

There are no other keywords inside a group. The block ends at `}`, and the group only enters the
namespace then, so a group can't name itself as a member (see "Redefinition hazards" below for
what happens when it names an older definition of itself).

### Weights

Both engines use the same weighted-list code (UZDoom `src/common/utility/weightedlist.h:71-157`,
Zandronum `src/weightedlist.h`, identical logic).

- **The weight is read as an integer, then stored in 16 bits.** Decimal, `0x` hex and
  leading-zero octal are accepted (`FScanner::GetNumber` parses with base 0), and so is `MAXINT`.
  A fraction such as `1.5` is a fatal `Bad numeric constant` error. Values are truncated, not
  clamped: `65536` becomes 0, `70000` becomes 4464, `-1` becomes 65535.
- **Weight 0 drops the member.** It's never added to the list, with no message
  (`weightedlist.h:74-78`). A group whose members are all weight 0 is an empty group.
- **Chances are quantized to 1/256.** Members are kept sorted by ascending weight, and each gets a
  one-byte cumulative threshold (share of the total x 255, truncated). A pick rolls a byte 0..255
  and takes the first member whose threshold isn't below the roll (`weightedlist.h:95-142`). So
  the lowest-weight member always gets at least 1/256, the highest-weight member takes whatever
  is left, and a member whose threshold truncates to the same byte as the previous member's is
  **never picked**. Example: weights `1`, `1`, `1000` give thresholds 0, 0, 255, so one of the two
  weight-1 members is chosen 1 time in 256 and the other never.
- Equal weights sort newest-first, which only matters through the truncation above.

### How a member is picked

Every spawn through a group rolls again: two bullet hits using the same group can show different
members. When the pick is itself a group, that group is picked from in turn, until a plain decal
comes back (`FDecalGroup::GetDecal`, UZDoom `decallib.cpp:1053-1069`, Zandronum
`decallib.cpp:1127-1143`). Nesting depth is not limited.

When the pick happens depends on who references the group:

| Reference | When the member is picked | UZDoom | Zandronum |
|---|---|---|---|
| `generator <class> <group>` | At every impact (`SpawnShootDecal`, `P_ExplodeMissile`) | yes | yes |
| DECORATE/ZScript `Decal` property naming a group | At every impact, same as a generator | yes | yes |
| `lowerdecal <group>` in a `decal` block | UZDoom: **once, at load**; that member is used every time. Zandronum: at every stamp | yes | yes |
| Map-placed `Decal` thing (9200) | When the thing spawns | yes | yes |
| ACS `SpawnDecal(tid, "<group>", ...)` | UZDoom: **once per call**, so every actor matching the TID gets the same member (`p_acs.cpp:6185`). Zandronum: once per actor (`p_acs.cpp:6701` keeps the group, `ShootDecal` picks, `a_decals.cpp:782`) | yes | yes |
| `A_SprayDecal("<group>")` | Every call | yes | no (action doesn't exist) |
| DeHackEd `Decal = <group>` on a Thing or Weapon | UZDoom: **once, at DEH load**, after DECALDEF. Zandronum: at every impact, like a generator. Unknown name prints `Thing N: Unknown decal ...` / `Weapon N: Unknown decal ...` and changes nothing. UZDoom `d_dehacked.cpp:1313-1324`, `2302-2316`; Zandronum `d_dehacked.cpp:882-893`, `1622-1634`. | yes | yes |

The split has one cause: `GetDecalByName`, which `lowerdecal`, ACS and DeHackEd all use, picks a
member on UZDoom (`decallib.cpp:884-896`) but returns the group itself on Zandronum
(`decallib.cpp:958-970`), leaving the pick to each stamp (`a_decals.cpp:682`, `:782`). The
`lowerdecal` detail is on [decal-definition.md](decal-definition.md). One twist belongs here:
`lowerdecal` stores whatever the name resolved to, and redefinition swaps that pointer. If the
name was a plain decal that a later definition replaces with a **group** of the same name, the
lower decal becomes a per-spawn random pick on both engines.

### Empty groups

`decalgroup Nothing { }` is legal on both engines. Spawning it at top level creates no decal and
no message. **Nesting an empty group inside another group is unsafe:** when the outer group picks
it, the inner pick comes back empty and the picker returns the inner *group* object as if it were a
decal (`decallib.cpp:1060-1068` UZDoom, `1133-1142` Zandronum). That is undefined behaviour.
Probed live with ACS `SpawnDecal` (2026-09-29, local test builds, probe map): top-level `Nothing`
returned 0 on both engines. A group whose only member is `Nothing` crashed Zandronum on the first
spawn (SIGSEGV in `FDecalTemplate::ApplyToDecal`, `decallib.cpp:1060`). On UZDoom four spawns
returned 0 and drew nothing, which is one build's luck, not a safe outcome.

## `generator`

```text
generator [optional] <actor class> <decal or group | None>
```

| Part | Value | Meaning | UZDoom | Zandronum |
|---|---|---|---|---|
| `optional` | literal, first token | Silences both lookup errors. | yes | **no**: read as the class name, fatal `optional is not an actor.` |
| `<actor class>` | class name, case-insensitive | Must already exist. DECORATE and ZScript are loaded before DECALDEF. | yes | yes |
| `<decal or group>` | name | Must be defined above this line. | yes | yes |
| `None` | literal, case-insensitive | Clears the class's decal. | yes | yes |

A generator writes one field on the named class's **default instance** (`DecalGenerator`), the
same field the DECORATE/ZScript `Decal` property writes. Actors copy it when they spawn. The
class is also recorded as a user of the decal, so if that decal or group is later redefined by
name, the class follows the new definition (UZDoom `decallib.cpp:552-559`, `843-848`; Zandronum
`decallib.cpp:636-641`, `924-929`).

### What the class's decal is used for

"Generating" means being the source of an **impact decal**. The engine looks up a class's decal
in these places only:

- **Hitscan hitting a wall** (`P_LineAttack`; UZDoom `p_map.cpp:4839-4862`, Zandronum
  `p_map.cpp:4337-4367`). Skipped entirely if the puff class has `NODECAL`, the attack has
  `LAF_NOIMPACTDECAL`, or the line is a horizon (UZDoom also skips visual portals). Otherwise:
  1. If the **shooter** has a decal, or the shooter is a player whose **ready weapon** has one: use
     the spawned puff's decal if the puff class has `FORCEDECAL` and a decal; otherwise the
     shooter's. For a player, "the shooter's" means the **weapon's** (`SpawnShootDecal`, UZDoom
     `p_map.cpp:7184-7201`, Zandronum `p_map.cpp:7014-7033`). A player class with a decal but a
     weapon without one therefore leaves **no** decal, and does not fall back to the puff.
  2. Else, if a puff was spawned and it has a decal: the puff's.
  3. Else: no decal.

  This is why the stock generators sit on weapons (`Pistol`, `Shotgun`, ...) and hitscan monsters
  (`ZombieMan`, `ShotgunGuy`, ...), not on `BulletPuff`.
- **Railgun hitting a wall** (`P_RailAttack`; UZDoom `p_map.cpp:5581-5584`, Zandronum
  `p_map.cpp:5004-5007`): the puff's decal if the puff class has `FORCEDECAL` and a decal,
  otherwise the shooter's (for a player, the weapon's). There is no plain puff fallback. On
  Zandronum the puff's decal also needs the puff class to have `ALWAYSPUFF` (see "Engine-family
  divergence").
- **A projectile exploding against a line** (`P_ExplodeMissile`; UZDoom `p_mobj.cpp:1985-2027`,
  Zandronum `p_mobj.cpp:1586-1596`): the projectile's own decal. Only when the client cvar
  `cl_missiledecals` is on, and only for a line hit, not a floor, ceiling or actor.

**Blood never uses generators.** `P_TraceBleed` sprays the fixed names `BloodSplat` (or, for a
heavy hit, sometimes `BloodSmear`) when `cl_bloodsplats` is on (UZDoom `p_map.cpp:5173-5252`,
Zandronum `p_map.cpp:4636-4674`). To change blood decals, redefine those two names (the stock
ones are groups). The bleeding actor's `NOBLOODDECALS` flag turns them off.

Every one of these paths picks from a group at the moment of impact. Impact decals also count
against `cl_maxdecals`; see [`../../console/notes/cl_maxdecals.md`](../../console/notes/cl_maxdecals.md).

### Generator versus the `Decal` property

The [`Decal`](../../decorate/inventory/actor-properties.md) actor property stores only a name
while actors are being defined. After every DECALDEF lump is read, `ReadAllDecals` walks all actor
classes and resolves each stored name (UZDoom `decallib.cpp:269-285`, Zandronum
`decallib.cpp:369-377`). A slot a `generator` line already filled holds a real decal, which the
walk recognizes and skips. So:

- **A `generator` line beats the class's `Decal` property**, whichever lump either comes from.
- **`generator <class> None` also cancels the property**: it clears the slot before the walk.
- **The DeHackEd `Decal` field beats both.** DeHackEd loads after `ReadAllDecals` on both engines
  (UZDoom `d_main.cpp:3679` then `3684`; Zandronum `d_main.cpp:3015` then `3038`).
- An unknown name in the property leaves the class with no decal, silently.

**Never name a decal or group `None`.** A class with no decal has an empty slot, and the walk
treats an empty slot as the name `None` (name index 0 is always `None`). A decal literally named
`None` then attaches itself to every actor class without one, including classes cleared with
`generator <class> None`. Observed live on both engines (2026-09-29, local test builds, probe map):
with `generator Pistol None` and `generator BulletPuff None`, a pistol shot left no mark; adding
`decal None { ... }` made the same shot stamp that decal. Clearing only `BulletPuff` isn't enough
to see it, because the pistol's own stock generator wins (see "What the class's decal is used for").

### Inheritance: a generator does not reach subclasses

A `generator` line affects **only the class it names**, never its DECORATE or ZScript subclasses.
A `Decal` property, by contrast, **is** inherited.

Why, on both engines: a new class's default instance is a byte copy of its parent's, made when the
class is created (UZDoom `PClassActor::InitializeDefaults`, `info.cpp:453-506`, called from
`thingdef_parse.cpp:103` for DECORATE and `zcc_compile_doom.cpp:838-859` for ZScript, parents
first; Zandronum `PClass::CreateDerivedClass` and `PClass::InitializeActorInfo`,
`dobjtype.cpp:273-320` and `405-420`). All classes are created while actors load, and actors load
before DECALDEF (UZDoom `PClassActor::StaticInit` at `d_main.cpp:3650`, `ReadAllDecals` at `3679`;
Zandronum `FActorInfo::StaticInit` at `d_main.cpp:2993`, `ReadAllDecals` at `3015`). So:

- When a subclass copies its parent, the parent's slot holds either nothing or a `Decal`-property
  name. A later `generator Parent ...` writes only the parent's slot.
- A property name copied into the subclass is resolved for the subclass by the post-DECALDEF walk,
  so the subclass ends up with the parent's `Decal` property decal unless it sets its own.
- If a parent has both a `Decal` property and a `generator` line, a subclass gets the
  **property's** decal, not the generator's.

The stock files show it: `MaceFX2` and `MaceFX3` both inherit from `MaceFX1`, which has
`generator MaceFX1 BaronScorch`. UZDoom added separate `generator MaceFX2`/`MaceFX3` lines in
commit `19444194a5` ("added missing decal assignments to the medium mace spheres");
Zandronum's `wadsrc/static/decaldef.txt` still lacks them, so those two projectiles leave no scorch
there.

**Practical consequence.** A mod actor that inherits from a stock weapon, hitscan monster or
projectile, including one that `replaces` it, does **not** get the stock scorch or bullet chip.
The actor that actually spawns (the replacement, or the subclass) is the one whose slot is read.
Give it its own `generator` line or `Decal` property:

```text
// MyRocket inherits from Rocket and replaces it. Rocket's stock generator
// does not carry over, so name the scorch again.
generator MyRocket Scorch
```

## Errors

"Fatal" here means startup stops. Every such row goes through `FScanner::ScriptError`, which calls
`I_Error` (UZDoom `src/common/engine/sc_man.cpp:1086`, Zandronum `src/sc_man.cpp:904`), and
neither engine's `ReadAllDecals`/`ReadDecals` catches it; DECALDEF is only read at startup. The
group and generator rows (the rest of the lump's errors are on the lump page):

| Condition | UZDoom | Zandronum |
|---|---|---|
| Group member not defined yet | Fatal: `<name> has not been defined` | Same |
| Weight missing, or not an integer | Fatal: `SC_GetNumber: Bad numeric constant "..."` (a `}` in the weight position also lands here) | Same |
| Weight 0, or truncating to 0 | Silent; member dropped | Same |
| `generator`: class unknown | Fatal: `<name> is not an actor.` With `optional`: the line is skipped silently. | Fatal: same message (`decallib.cpp:614-617`) |
| `generator`: class exists but isn't an actor | Fatal, same message (`PClass::FindActor` only returns actor classes, `actor.h:1807-1811`) | Fatal, same message (the class has no `ActorInfo`) |
| `generator`: decal unknown | Fatal: `<name> has not been defined.` With `optional` and a known class: the class's decal is **cleared**, silently, which also discards its `Decal` property. | Fatal, always |
| `generator` with `optional` | Accepted | Fatal: `optional is not an actor.` |

## Redefinition hazards

The lump page covers the normal case (a redefined decal or group replaces the old one, and references
follow). The same machinery has three traps specific to groups and generators, on both engines.
All three are derived from reading `AddDecal` (UZDoom `decallib.cpp:800-861`, Zandronum
`decallib.cpp:881-940`). The second and third were then observed live on both engines with ACS
`SpawnDecal` (2026-09-29, local test builds, probe map). The stale generator was observed live on
both too: with `generator Pistol GenA` then `generator Pistol GenB` in one pk3, a pistol shot
left a `GenB` decal, and adding a second pk3 whose DECALDEF redefines `GenA` made the shot leave
the new `GenA` instead.

- **A stale generator can come back.** `generator` adds the class to the new target's user list
  but never removes it from the old target's. Given `generator Foo A`, then `generator Foo B`, a
  later redefinition of `A` (in any later lump) resets `Foo` to the new `A`, silently undoing the
  second line. The same happens after `generator Foo None`. Put a class's final `generator` line
  after any redefinition of decals it used to point at, or don't redefine them.
- **Don't extend a group by naming it inside its own redefinition.** In
  `decalgroup BulletChip { BulletChip 3  MyChip 1 }` the member `BulletChip` resolves to the *old*
  group, the reference update runs before the new group is linked in (so its own member list is
  not updated), and the old group is then freed. The new group keeps a dangling member.
  List the stock members explicitly instead. Live, the first spawn of such a group crashed both
  engines (SIGSEGV; UZDoom in `FDecalGroup::GetDecal`, `decallib.cpp:1065`; Zandronum in
  `DImpactDecal::StaticCreate`, `a_decals.cpp:682`).
- **Redefinition can create a cycle.** With `decalgroup A { B 1 }` defined, redefining `B` as
  `decalgroup B { A 1 }` makes `A` point at the new `B` and `B` at `A`. Picking from either
  recurses forever (a stack overflow) if every path loops, and otherwise keeps rolling until it
  happens to reach a plain decal. Live, spawning a fully looping pair killed both engines
  instantly with no crash report, as a stack overflow would.

## Engine-family divergence

The group and generator parsers are otherwise identical line for line. Differences:

- **`generator optional`** is UZDoom-only (UZDoom `decallib.cpp:528-551`). Zandronum reads
  `optional` as the class name and fails.
- **Group-pick RNG.** UZDoom draws group picks from a client-side RNG (`pr_decalchoice` is an
  `FCRandom`, `decallib.cpp:52`, `m_random.h:235-240`), kept on a separate list from the play RNGs.
  Zandronum uses an ordinary named play RNG (`FRandom`, `decallib.cpp:67`); it has no `FCRandom`.
- **Weapon decal source.** UZDoom reads the ready weapon **instance's** decal
  (`p_map.cpp:7190`), and `DecalGenerator` is a writable native field on ZScript `Actor`
  (`actor.zs:346`), so ZScript can change it per actor at run time (the stock scripted marine
  does, `scriptedmarine.zs:642`; Zandronum's native marine does the same in
  `g_doom/a_scriptedmarine.cpp:718`, so shooter decals are read per instance on both engines and
  only the weapon read differs). UZDoom also has a native
  `GetDecalName()` that returns an actor's decal or group name (`a_decals.cpp:933-941`).
  Zandronum always reads the weapon **class default** (`p_map.cpp:7024`) and has no script access.
- **Rail `FORCEDECAL` puffs.** UZDoom reads the puff class's defaults, so a `FORCEDECAL` puff's
  decal is used whether or not a puff actor spawned (`p_map.cpp:5581`; changed in UZDoom commit
  `057b746e58`, "The rail attack only considered the puff's decal if it had ALWAYSPUFF set").
  Zandronum still reads the spawned puff (`p_map.cpp:5004`), which a rail only spawns for an
  `ALWAYSPUFF` puff class (`p_map.cpp:4987`), so without `ALWAYSPUFF` the shooter's decal is used.
- **Stock generators.** UZDoom's `wadsrc/static/decaldef.txt` has `generator MaceFX2` and
  `generator MaceFX3` lines Zandronum's lacks (see "Inheritance"). Zandronum's
  `skulltag_actors.pk3` DECALDEF (`wadsrc_st/static/decaldef.txt`) adds generators for Skulltag
  classes (`Minigun`, `BFG10K`, `Railgun`, `SuperShotgunGuy`, `BelphegorBall`, `CacolanternBall`,
  `DarkImpBall`, `HectShot`) that UZDoom doesn't have.
- **SLADE** lists `decalgroup`, `generator` and `optional` as keywords, with no engine marking, so
  it won't warn that `optional` breaks Zandronum.

## Zandronum-specific: which machine's copy is used

The lump page's section of the same name covers the general rule: a server never creates impact
decals, and each client resolves generators against its own DECALDEF and DECORATE. For generators
specifically:

- **Clients don't spawn hitscan puffs**, so where the rules above read "the spawned puff's decal",
  a Zandronum client reads the **puff class default** instead (`p_map.cpp:4357-4361` for hitscan,
  `p_map.cpp:4998-5004` for an `ALWAYSPUFF` rail puff). The outcome matches the rules above as long as the puff's
  decal isn't changed per actor.
- **Client hitscan decals depend on `cl_hitscandecalhack`** (archived client cvar, default `true`,
  `cl_main.cpp:10034`). With it off, a client skips hitscan wall decals entirely
  (`p_map.cpp:4334-4335`), and also the blood decals of a hitscan that hits an actor, since the
  client returns before its `P_TraceBleed` call (`p_map.cpp:4440-4441`). Projectile decals, and
  blood from projectile hits, are unaffected.
- **Group picks are per client.** Each client rolls its own member for every impact, so two players
  can see different members of the same group on the same wall. ACS `SpawnDecal` is no exception:
  the server sends the **group's** name (`sv_commands.cpp:5290` writes the unpicked template's
  name), so each client picks its own member. Observed live (2026-09-29, local test build, a
  server and 2 clients, probe map): eight server-side `SpawnDecal` calls with a two-member group drew
  `BBBBRRBR` on one client and `BBRRRRRR` on the other.

## See also

- [The DECALDEF lump](decaldef-lump.md): outer grammar, load order, redefinition, IDs, the
  full error table and the netcode overview.
- [decal-definition.md](decal-definition.md) for `decal` blocks, including `lowerdecal`.
- [animators.md](animators.md) for `fader`, `stretcher`, `slider`, `colorchanger`, `combiner`.
- [`../../acs/families/spawning.md`](../../acs/families/spawning.md) for ACS `SpawnDecal`.
- [`../../console/notes/cl_maxdecals.md`](../../console/notes/cl_maxdecals.md) for the decal limit.
- The `Decal` property, and the `FORCEDECAL`, `NODECAL`, `NOBLOODDECALS` flags, in
  [`../../decorate/inventory/actor-properties.md`](../../decorate/inventory/actor-properties.md)
  and [`../../decorate/inventory/`](../../decorate/inventory/).
