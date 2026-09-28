# Activation

**Tier:** A (ZDoom-wiki-sourced, verified line-by-line against fork C++; the fork's total absence of ZScript was independently confirmed by searching the Zandronum source's `src` for any ZScript lexer/parser/lump handling, not just inferred from the wiki gap).
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** wiki page `Activation - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29, `https://zdoom.org/w/index.php?title=Activation&oldid=54953`) + verified against the Zandronum source's `src/p_lnspec.cpp` (`LS_Thing_Activate`/ `LS_Thing_Deactivate`/`DoActivateThing`/`DoDeactivateThing`), `p_mobj.cpp` (`AActor::Activate`/ `Deactivate`), `p_map.cpp` (`P_ActivateThingSpecial`; `P_UseTraverse` at 5362-5384; the sideways `BUMPSPECIAL` path at 1340-1342/1358-1384), `p_mobj.cpp:4439-4456` (standing-on-top `BUMPSPECIAL`), `p_interaction.cpp:550-554` (death call), `cl_main.cpp:5895-5905`, `sv_commands.cpp:2197-2206` and `protocolspec/spec.things.txt:332-340` (`ThingActivate`/`ThingDeactivate` broadcast), `actor.h` (`THINGSPEC_*`, `MF2_DORMANT`, `MF5_USESPECIAL`, `MF6_BUMPSPECIAL`), and `thingdef_properties.cpp` (`Activation` property) (2026-07-29).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

What ACS's `Thing_Activate(tid)`/`Thing_Deactivate(tid)` action specials actually do to an actor
in Zandronum, and why most of the ZDoom wiki's "Activation" page — written for ZScript — doesn't
apply here at all. Read this before assuming an actor's `Activate`/`Deactivate` behavior can be
customized from script the way the wiki describes.

## The big fork divergence: no ZScript

**Zandronum has no ZScript support whatsoever** — it is a DECORATE-only engine (confirmed: no
`ZScript` lexer/parser anywhere in the Zandronum source's `src`, no `zscript` lump handling). The
ZDoom wiki's "Activation" page is majority-ZScript: it describes `Activate`/`Deactivate` as
*Actor virtual functions* that a custom actor can override, and that can be called directly on a
pointer (`target.Activate()`). None of that exists here. In Zandronum:

- `AActor::Activate`/`AActor::Deactivate` (`p_mobj.cpp:5229,5249`) are fixed C++ methods — DECORATE
  has no syntax to add a new override of its own, only to instantiate one of the native classes
  below that already carries one.
- **At least nineteen actor classes across unrelated subsystems override one or both** (grepped
  tree-wide for every `Activate`/`Deactivate` method declaration and qualified definition, not just
  the handful the wiki happens to mention): `AAmbientSound` (`s_advsound.cpp:2259,2309` —
  starts/stops the ambient sound), the three Invasion spot classes
  `ABaseMonsterInvasionSpot`/`ABasePickupInvasionSpot`/`ABaseWeaponInvasionSpot` (`invasion.cpp`),
  `ASwitchableDecoration`/`ASwitchingDecoration` (`a_action.cpp:27-64` — **does** exist natively in
  Zandronum; see the correction below), `ASectorAction` (`a_sectoraction.cpp`), `AMapMarker`
  (`a_mapmarker.cpp`), `APathFollower`/`AActorMover` (`a_movingcamera.cpp`), `AScriptedMarine`
  (`a_scriptedmarine.cpp`), `AParticleFountain` (`a_fountain.cpp`), `ASpark` (`a_spark.cpp`,
  `Activate` only), `ASoundEnvironment` (`a_soundenvironment.cpp`), `ASecretTrigger`
  (`a_secrettrigger.cpp`, `Activate` only), `ASoundSequence` (`a_soundsequence.cpp`), `AZBell`
  (`a_hexenspecialdecs.cpp`, `Activate` only), `ADynamicLight` (`gl_dynlight.h`/`a_dynlight.cpp`),
  and `AThrustFloor` (`a_spike.cpp`). Every other actor gets the base `AActor` behavior below.
  **Correcting an earlier version of this file: `SwitchableDecoration` is real and
  DECORATE-instantiable in Zandronum too** (`ASwitchableDecoration : public AActor`,
  `IMPLEMENT_CLASS`-registered, `a_action.cpp:27-53`; `ASwitchingDecoration` subclasses it and
  overrides only `Deactivate`, `a_action.cpp:57-62` — see
  [SwitchableDecoration](../../decorate/classes/switchabledecoration.md) for the full writeup). It
  is not a GZDoom/ZScript-era addition that was "never backported" — it's one more fixed native
  override like the others, just not itself further overridable from DECORATE the way ZScript lets
  a mod override it on UZDoom. There is no `Used` virtual anywhere in the Zandronum source, though
  — that part of the original claim holds.
- The wiki's "calling them directly ... in ZScript" bullet and the entire "ZScript" section
  don't apply. The *only* way to trigger `Activate`/`Deactivate` in Zandronum is the
  `Thing_Activate`/`Thing_Deactivate` action specials below (from ACS, or as a line/thing
  special), or the DECORATE `USESPECIAL`/`BUMPSPECIAL` actor flags through
  `P_ActivateThingSpecial`. A sideways `BUMPSPECIAL` collision never calls either method on
  Zandronum; see the bump section below.

## ACS: `Thing_Activate`/`Thing_Deactivate`

Both are action specials (positive indices in `zcommon.bcs`'s `special` table: `Thing_Activate`
= 130, `Thing_Deactivate` = 131), implemented as `FUNC(LS_Thing_Activate)`/
`FUNC(LS_Thing_Deactivate)` in `p_lnspec.cpp:1232,1271`. Signature: `Thing_Activate(tid)` /
`Thing_Deactivate(tid)`, both return `bool` (`int` in BCS) — `true` if at least one actor was
found and processed, `tid=0` means "no tid given" and falls back to the calling script's
activator (`it`) if one exists, otherwise returns `false`. With a nonzero `tid`, every matching
actor is processed and the return is `count != 0` — there's no way to tell "some matched but did
nothing" from "some matched and did something," since `DoActivateThing`/`DoDeactivateThing`
(`p_lnspec.cpp:1210,1221`) always run unconditionally per matched actor regardless of whether the
actor's `activationtype` flags make anything observable happen.

Verified against `p_lnspec.cpp:1210-1230` — calling `Thing_Activate`/`Thing_Deactivate` on a
matched actor does two things locally, both unconditional (plus a network broadcast on a Zandronum
server, below):

1. **Clears/sets the `THINGSPEC_Switch` bookkeeping.** If the actor's `activationtype` currently
   has `THINGSPEC_Activate` (or `THINGSPEC_Deactivate`) set, that flag is cleared and, if
   `THINGSPEC_Switch` is also set, the opposite flag is set instead — so the *next*
   USESPECIAL/BUMPSPECIAL trigger flips direction. This only rewrites those three bits; it does
   not gate whether step 2 happens.
2. **Unconditionally calls the actor's `Activate`/`Deactivate` C++ method** — regardless of the
   actor's `activationtype` flags. This matches the wiki's claim that these ACS functions "always"
   call the virtual, "regardless of how the activation property is set up."

On a Zandronum server, `LS_Thing_Activate`/`LS_Thing_Deactivate` also send
`SERVERCOMMANDS_ThingActivate`/`ThingDeactivate` (actor plus activator, `spec.things.txt:332-340`)
for each matched actor before step 1. The client handler (`cl_main.cpp:5895-5905`) calls the raw
`Activate`/`Deactivate` method, not `DoActivateThing`, so the client's copy of the
`activationtype` bits is not rewritten. Nothing is sent for an actor that has no net ID
(`sv_commands.cpp:2197-2206`).

The **default** `AActor::Activate`/`Deactivate` (`p_mobj.cpp:5229-5267`, what every actor gets
unless it's one of the overriding classes above) only does something if
`(flags3 & MF3_ISMONSTER) && (health > 0 || flags & MF_ICECORPSE)` — i.e. a living monster or an
ice corpse. Even then it is not a toggle. `Activate` acts only if the actor is currently dormant
(`MF2_DORMANT`, `actor.h:192`): it clears the flag and enters the `Active` state, or sets
`tics = 1` ("advance to whatever's next") if there is none. `Deactivate` acts only if the actor is
not dormant: it sets the flag and enters the `Inactive` state, or sets `tics = -1` (freezes on the
current frame) if there is none. Activating an already-active monster, or deactivating a dormant
one, does nothing. **On any other actor — a decoration, a non-monster, a dead monster without
`MF_ICECORPSE` — the actor-side effect of `Thing_Activate`/`Thing_Deactivate` is a confirmed
no-op** unless that actor is one of the overriding classes above; only the step-1
`activationtype` bookkeeping still happens. Real-world callers have been observed calling both
on a TID assigned to non-monster decoration actors — worth double-checking that whatever actor
carries that TID is actually a monster/ice-corpse or one of the overriding classes, or the
calls do nothing.

## `USESPECIAL`/`BUMPSPECIAL` and the `Activation` DECORATE property

Separately from the ACS functions above, an actor can trigger its own `Activate`/`Deactivate` (and
optionally its `special` line-special) when a player uses (`MF5_USESPECIAL`, `actor.h:284`) or
bumps (`MF6_BUMPSPECIAL`, `actor.h:312`) it — both flags confirmed present in Zandronum.
`USESPECIAL` does not need `SOLID`: the use trace (`P_UseTraverse`, `p_map.cpp:5362-5384`) checks
every blockmap actor it crosses, with no solidity test, on both engines. `BUMPSPECIAL` on
Zandronum does need the actor to be `SOLID`, on both of its bump paths.

Zandronum has two `BUMPSPECIAL` paths, and only one of them uses the `activationtype` machinery:

- **Standing on top** of the actor (`p_mobj.cpp:4439-4456`, a mover resting on a solid actor
  found by `P_TestMobjZ`) goes through `P_ActivateThingSpecial`: players by default,
  monsters/projectiles only with `THINGSPEC_MonsterTrigger`/`MissileTrigger`, at most once a
  second per actor (`lastbump`).
- **Colliding sideways** (`p_map.cpp:1358-1384`, with `solid` computed at `p_map.cpp:1340-1342`; Zandronum keeps Skulltag's implementation here;
  the ZDoom version at `p_map.cpp:1014-1025` is commented out) bypasses it entirely. Offline or on
  the server, whenever a mover that is `SOLID` (or `BLOCKEDBYSOLIDACTORS`) collides with a `SOLID`,
  non-`NOCLIP` `BUMPSPECIAL` actor, it runs the actor's `special` directly with the mover as
  activator, on every collision check, with no `lastbump` rate limit. `activationtype` is ignored:
  no player-only default, no `MonsterTrigger`/`MissileTrigger` gate, no activator choice, no
  `ClearSpecial`, no target switching, and no `Activate`/`Deactivate` call. Skulltag score
  pillars are also handled in this path.

The DECORATE `Activation` property (confirmed:
`DEFINE_PROPERTY(activation, N, Actor)`, `thingdef_properties.cpp:1362`) sets the `activationtype`
bitfield read by `P_ActivateThingSpecial` (`p_map.cpp:7087-7141`) and `THINGSPEC_*` flag values
(`actor.h:603-619`, all confirmed present and bit-identical to the wiki's list —
`THINGSPEC_Default`=0, `ThingActs`=1, `ThingTargets`=1<<1, `TriggerTargets`=1<<2,
`MonsterTrigger`=1<<3, `MissileTrigger`=1<<4, `ClearSpecial`=1<<5, `NoDeathSpecial`=1<<6,
`TriggerActs`=1<<7, `Activate`=1<<8, `Deactivate`=1<<9, `Switch`=1<<10).

`P_ActivateThingSpecial(thing, trigger, death)` is the one function that reconciles all of this —
called on death (when the actor has a `special`, is not `MF_SPECIAL` unless it is a monster, and
lacks `THINGSPEC_NoDeathSpecial`, `p_interaction.cpp:550-554`), on a use of a `USESPECIAL` actor,
or on the standing-on-top `BUMPSPECIAL` path (on Zandronum, not the sideways one above). Verified
behavior, matching the wiki:

- `THINGSPEC_ThingTargets` sets `thing`'s `target` to `trigger`, and `THINGSPEC_TriggerTargets`
  sets `trigger`'s `target` to `thing`. Each is gated only on its own flag and runs before
  anything else. It is not a swap.
- The `Activate`/`Deactivate`/`Switch` state machine only runs `if (!death && ...)` — death never
  calls the actor's `Activate`/`Deactivate` virtual, only its `special` (see below). A switchable
  actor (`THINGSPEC_Switch` set, neither `Activate` nor `Deactivate` set yet) defaults to
  activating first, exactly as the wiki states.
- The actor's `special` line-special runs (`P_ExecuteSpecial`) if `thing->special != 0`, with the
  activator chosen by `THINGSPEC_ThingActs`/`TriggerActs`/the `LEVEL_ACTOWNSPECIAL` MAPINFO flag —
  confirmed `TriggerActs` overrides the level flag, matching the wiki. `death` clears
  `special` after running it once (always on Zandronum; UZDoom skips the clear under
  `LEVEL2_HEXENHACK`, `src/playsim/p_map.cpp:7283`); `THINGSPEC_ClearSpecial` does the same on a non-death success
  only.

## See also

- [Script types](script-types.md) — `DEATH`/`ENTER`/`RESPAWN` script types are a different concept
  from actor-level `Activate`/`Deactivate`; don't confuse the two "activation" senses.

## Engine-family divergence

The core mechanism documented above — the `Thing_Activate`/`Thing_Deactivate` action specials at
indices 130/131, the `THINGSPEC_*` bitfield and the `Activation` DECORATE property,
`P_ActivateThingSpecial`'s dispatch, and the default `AActor::Activate`/`Deactivate` monster/ice-
corpse gate — is confirmed present and structurally unchanged in the UZDoom source
(`src/playsim/p_lnspec.cpp`, `src/playsim/actor.h`, `src/playsim/p_mobj.cpp`). A script calling
`Thing_Activate`/`Thing_Deactivate` behaves the same way on both engines, apart from the
Zandronum-only server-to-client broadcast described above.

`BUMPSPECIAL` differs. UZDoom's sideways collision path (`src/playsim/p_map.cpp`'s
`PIT_CheckThing`) goes through `P_ActivateThingSpecial` with the player-only default,
`MonsterTrigger`/`MissileTrigger` and `lastbump`, like its standing-on-top path. Zandronum's
sideways path is Skulltag's direct special call described above, which ignores `activationtype`
and never calls `Activate`/`Deactivate`. That path is unchanged since 3.2.1 apart from a score
pillar setting.

The default-vs-override picture changes shape on UZDoom, though. Zandronum's fixed
(nineteen-and-counting-class) override list doesn't carry over as a fixed list at all: UZDoom's
`AActor::Activate`/`Deactivate` are dispatched through `AActor::CallActivate`/`CallDeactivate`
(`src/playsim/p_mobj.cpp`), which check `IFVIRTUAL(AActor, Activate)` (respectively `Deactivate`)
before falling back to the base C++ implementation — this looks up the calling actor's actual
runtime class in its virtual-function table (`src/common/scripting/vm/vm.h`'s
`IFVIRTUAL`/`IFVIRTUALPTR` macros), so **any ZScript actor class that overrides the
`Activate`/`Deactivate` virtual gets called, not a fixed list of native C++ classes**.
`Thing_Activate`/`Thing_Deactivate`'s engine-side handlers (`DoActivateThing`/`DoDeactivateThing`
in `src/playsim/p_lnspec.cpp`) call `CallActivate`/`CallDeactivate`, not the raw method, so this
applies to the ACS action specials documented above, not just direct ZScript calls.

The UZDoom ZScript stdlib alone already overrides one or both virtuals on more than a dozen classes
spanning several unrelated subsystems — `AmbientSound` (a native override, the same role
`AAmbientSound` plays on Zandronum), `SwitchableDecoration`/`SwitchingDecoration`,
`PathFollower`/`ActorMover` (moving-camera path nodes), `SectorAction`, `SecretTrigger`,
`SoundEnvironment`, `SoundSequence`, `Spark`, `DynamicLight`, `ThrustFloor`, `ZBell`,
`ParticleFountain`, and `MapMarker` — and any mod-defined ZScript actor can add its own override on
top, since nothing in the dispatch gates who may do so. If no override applies (a base `AActor` or
a DECORATE-only actor with no ZScript override in its class chain), `CallActivate`/`CallDeactivate`
resolves to the base implementation, which runs the same monster/ice-corpse gate documented above
for Zandronum — confirmed identical logic in `src/playsim/p_mobj.cpp`. The three Zandronum-only
Invasion spot classes
(`ABaseMonsterInvasionSpot`/`ABasePickupInvasionSpot`/`ABaseWeaponInvasionSpot`) still don't exist
on UZDoom — Invasion is a Zandronum-only gametype with no UZDoom equivalent — but that's no longer
a meaningful gap to track: on UZDoom there is no fixed exception list for a class to be missing
from.
