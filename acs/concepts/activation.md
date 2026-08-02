# Activation

**Tier:** A (ZDoom-wiki-sourced, verified line-by-line against fork C++; the fork's total absence of ZScript was independently confirmed by searching the Zandronum source's `src` for any ZScript lexer/parser/lump handling, not just inferred from the wiki gap).
**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD, a `3.3-alpha` development snapshot ahead of the 3.2.1 target — every construct checked here is Hexen/Boom-era action-special/DECORATE machinery, long predating that gap, so it is unaffected).
**Provenance:** wiki page `Activation - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29, `oldid=54953`) + verified against the Zandronum source's `src/p_lnspec.cpp` (`LS_Thing_Activate`/ `LS_Thing_Deactivate`/`DoActivateThing`/`DoDeactivateThing`), `p_mobj.cpp` (`AActor::Activate`/ `Deactivate`), `p_map.cpp` (`P_ActivateThingSpecial`), `actor.h` (`THINGSPEC_*`, `MF2_DORMANT`, `MF5_USESPECIAL`, `MF6_BUMPSPECIAL`), and `thingdef_properties.cpp` (`Activation` property) (2026-07-29).

What ACS's `Thing_Activate(tid)`/`Thing_Deactivate(tid)` action specials actually do to an actor
in this fork, and why most of the ZDoom wiki's "Activation" page — written for ZScript — doesn't
apply here at all. Read this before assuming an actor's `Activate`/`Deactivate` behavior can be
customized from script the way the wiki describes.

## The big fork divergence: no ZScript

**Zandronum has no ZScript support whatsoever** — it is a DECORATE-only engine (confirmed: no
`ZScript` lexer/parser anywhere in the Zandronum source's `src`, no `zscript` lump handling). The
ZDoom wiki's "Activation" page is majority-ZScript: it describes `Activate`/`Deactivate` as
*Actor virtual functions* that a custom actor can override, and that can be called directly on a
pointer (`target.Activate()`). None of that exists here. In this fork:

- `AActor::Activate`/`AActor::Deactivate` (`p_mobj.cpp:5229,5249`) are fixed C++ methods, not
  overridable from DECORATE.
- Only three actor classes in the entire engine override them: `AAmbientSound`
  (`s_advsound.cpp:2259,2309` — starts/stops the ambient sound) and the three Invasion spot
  classes `ABaseMonsterInvasionSpot`/`ABasePickupInvasionSpot`/`ABaseWeaponInvasionSpot`
  (`invasion.cpp`). Every other actor gets the base `AActor` behavior below — there is no
  `SwitchableDecoration` class and no `Used` virtual in this fork (both are GZDoom/ZScript-era
  additions the wiki page references that were never backported).
- The wiki's "calling them directly ... in ZScript" bullet and the entire "ZScript" section
  don't apply. The *only* way to trigger `Activate`/`Deactivate` in this fork is the ACS action
  specials below, or the DECORATE `USESPECIAL`/`BUMPSPECIAL` actor flags.

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
matched actor does exactly two things, both unconditional:

1. **Clears/sets the `THINGSPEC_Switch` bookkeeping.** If the actor's `activationtype` currently
   has `THINGSPEC_Activate` (or `THINGSPEC_Deactivate`) set, that flag is cleared and, if
   `THINGSPEC_Switch` is also set, the opposite flag is set instead — so the *next*
   USESPECIAL/BUMPSPECIAL trigger flips direction. This only rewrites those three bits; it does
   not gate whether step 2 happens.
2. **Unconditionally calls the actor's `Activate`/`Deactivate` C++ method** — regardless of the
   actor's `activationtype` flags. This matches the wiki's claim that these ACS functions "always"
   call the virtual, "regardless of how the activation property is set up."

The **default** `AActor::Activate`/`Deactivate` (`p_mobj.cpp:5229-5262`, what every actor gets
unless it's one of the three overriding classes above) only does something if
`(flags3 & MF3_ISMONSTER) && (health > 0 || flags & MF_ICECORPSE)` — i.e. a living monster or an
ice corpse. In that case it flips `MF2_DORMANT` (`actor.h:192`) and switches to the `Active`/
`Inactive` state if the actor defines one (falls back to `tics = 1`, i.e. "advance to whatever's
next," if it doesn't). **On any other actor — a decoration, a non-monster, a dead monster without
`MF_ICECORPSE` — `Thing_Activate`/`Thing_Deactivate` is a confirmed no-op** unless that actor is
one of the three C++-overriding classes above. Real-world callers have been observed calling both
on a TID assigned to non-monster decoration actors — worth double-checking that whatever actor
carries that TID is actually a monster/ice-corpse or one of the three special classes, or the
calls do nothing.

## `USESPECIAL`/`BUMPSPECIAL` and the `Activation` DECORATE property

Separately from the ACS functions above, an actor can trigger its own `Activate`/`Deactivate` (and
optionally its `special` line-special) when a player uses (`MF5_USESPECIAL`, `actor.h:284`) or
bumps (`MF6_BUMPSPECIAL`, `actor.h:312`) it — both flags confirmed present in this fork. This
requires the actor to also have `SOLID` (collision-based triggering needs collision), matching the
wiki. The DECORATE `Activation` property (confirmed:
`DEFINE_PROPERTY(activation, N, Actor)`, `thingdef_properties.cpp:1362`) sets the `activationtype`
bitfield read by `P_ActivateThingSpecial` (`p_map.cpp:7087-7141`) and `THINGSPEC_*` flag values
(`actor.h:603-619`, all confirmed present and bit-identical to the wiki's list —
`THINGSPEC_Default`=0, `ThingActs`=1, `ThingTargets`=1<<1, `TriggerTargets`=1<<2,
`MonsterTrigger`=1<<3, `MissileTrigger`=1<<4, `ClearSpecial`=1<<5, `NoDeathSpecial`=1<<6,
`TriggerActs`=1<<7, `Activate`=1<<8, `Deactivate`=1<<9, `Switch`=1<<10).

`P_ActivateThingSpecial(thing, trigger, death)` is the one function that reconciles all of this —
called on death, or on a successful USESPECIAL/BUMPSPECIAL collision check elsewhere. Verified
behavior, matching the wiki:

- `THINGSPEC_ThingTargets`/`TriggerTargets` swap `target` pointers between `thing` and `trigger`
  unconditionally, before anything else.
- The `Activate`/`Deactivate`/`Switch` state machine only runs `if (!death && ...)` — death never
  calls the actor's `Activate`/`Deactivate` virtual, only its `special` (see below). A switchable
  actor (`THINGSPEC_Switch` set, neither `Activate` nor `Deactivate` set yet) defaults to
  activating first, exactly as the wiki states.
- The actor's `special` line-special runs (`P_ExecuteSpecial`) if `thing->special != 0`, with the
  activator chosen by `THINGSPEC_ThingActs`/`TriggerActs`/the `LEVEL_ACTOWNSPECIAL` MAPINFO flag —
  confirmed `TriggerActs` overrides the level flag, matching the wiki. `death` always clears
  `special` after running it once; `THINGSPEC_ClearSpecial` does the same on a non-death success
  only.

## See also

- [Script types](script-types.md) — `DEATH`/`ENTER`/`RESPAWN` script types are a different concept
  from actor-level `Activate`/`Deactivate`; don't confuse the two "activation" senses.
