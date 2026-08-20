# `bool Thing_Deactivate(int tid)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `Activation - ZDoom Wiki.html` (`_intake/`, retrieved
2026-07-29, `https://zdoom.org/w/index.php?title=Activation&oldid=54953`) + verified against the Zandronum source's `p_lnspec.cpp`
(`LS_Thing_Deactivate`/`DoDeactivateThing`) and `p_mobj.cpp` (`AActor::Deactivate`) — see
[Activation](../concepts/activation.md) for the full source citation list.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** action special, index 131.

Unconditionally calls the matching actor(s)' `Deactivate` C++ method. On the vast majority of
actors this is a no-op — see Behavior below and [Activation](../concepts/activation.md) for the
full write-up (this file is the canonical signature entry; the concept page has the rest of the
verification, including why the ZDoom wiki's ZScript-era "Activation" page mostly doesn't apply
to Zandronum specifically — see this file's own Engine-family divergence section below for how
that changes on UZDoom, whose ZScript override surface the wiki page describes accurately).

## Parameters

- `tid` — TID of the actor(s) to deactivate. `0` means "no tid given": falls back to the calling
  script's activator (`it`) if one exists, otherwise the call does nothing and returns `false`.
  Non-zero processes every actor matching that TID.

## Behavior

Returns `true` if at least one actor was found and processed; with a non-zero `tid` this is
`count != 0` — there is no way to distinguish "some actors matched but did nothing observable"
from "some actors matched and did something," since the underlying `DoDeactivateThing`
(`p_lnspec.cpp:1221`) always runs unconditionally per matched actor regardless of whether anything
observable happens.

Per matched actor, two things happen unconditionally: the `THINGSPEC_Switch` bookkeeping bits are
cleared/flipped (so a switchable actor's *next* USESPECIAL/BUMPSPECIAL trigger goes the other
way), and the actor's `Deactivate` C++ method is called regardless of its `activationtype` flags.
The **default** `AActor::Deactivate` (what every actor gets unless it's one of the native classes
that override it — at least nineteen, spanning several unrelated subsystems, not a short
enumerable handful; see the linked concept page) only does something for a living monster or an
ice corpse — on any other actor (decoration, non-monster, dead monster without `MF_ICECORPSE`)
this call is a confirmed no-op.

## See also

- [Activation](../concepts/activation.md) — full verification against `p_lnspec.cpp`/`p_mobj.cpp`,
  the native classes that override the default `Deactivate`, and how this interacts with the
  DECORATE `Activation` property and `USESPECIAL`/`BUMPSPECIAL` flags.

## Engine-family divergence

`FUNC(LS_Thing_Deactivate)` and `DoDeactivateThing` (UZDoom source's `src/playsim/p_lnspec.cpp:1451-1479`
and `:1410-1419`) are structurally unchanged from the description above: the same tid-iteration/
count-return shape, and the same unconditional `THINGSPEC_Switch` bookkeeping flip per matched
actor. The default `AActor::Deactivate` (`src/playsim/p_mobj.cpp:5873`) is also unchanged — the
same `(flags3 & MF3_ISMONSTER) && (health > 0 || flags & MF_ICECORPSE)` gate, byte-identical logic
to Zandronum's.

The **"fixed native class list" framing above becomes open-ended on UZDoom.** `DoDeactivateThing`
doesn't call `thing->Deactivate()` directly; it calls `thing->CallDeactivate(activator)`
(`src/playsim/p_mobj.cpp:5901-5909`), which first checks — via `IFVIRTUAL(AActor, Deactivate)` —
whether the actor's class has a ZScript override, and only falls back to the native default above
if it doesn't. Any ZScript actor class can add its own `override void Deactivate(Actor activator)`,
on top of whatever the stdlib already overrides — `SwitchableDecoration`
(`actors/shared/sharedmisc.zs:210,217`; **also a real, native, DECORATE-instantiable class on
Zandronum** — `ASwitchableDecoration`, `a_action.cpp:27-53` — not the ZScript-only class an earlier
version of [Activation](../concepts/activation.md) claimed; see
[SwitchableDecoration](../../decorate/classes/switchabledecoration.md) for the full writeup),
`AmbientSound` (a native override on both engines — the Zandronum-side `AAmbientSound` is present
here too, `wadsrc/static/zscript/actors/shared/soundsequence.zs:63`), `MovingCamera`
(`actors/shared/movingcamera.zs:501`), `SoundEnvironment` (`actors/shared/soundenvironment.zs:49`),
`MapMarker` (`actors/shared/mapmarker.zs:66`), `Fountain`
(`actors/shared/fountain.zs:54`), `SoundSequence` (`actors/shared/soundsequence.zs:182`),
`SectorAction` (`actors/shared/sectoraction.zs:95`), and Hexen's `Spike`
(`actors/hexen/spike.zs:111`) all override it. `Thing_Deactivate`'s no-op claim therefore only
holds on UZDoom for an actor whose class (and ancestors) don't declare their own `Deactivate`
override — not, as on Zandronum, for every actor except a fixed, enumerable set.
