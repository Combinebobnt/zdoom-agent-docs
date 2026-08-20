# `bool Thing_Activate(int tid)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `Activation - ZDoom Wiki.html` (`_intake/`, retrieved
2026-07-29, `https://zdoom.org/w/index.php?title=Activation&oldid=54953`) + verified against the Zandronum source's `p_lnspec.cpp`
(`LS_Thing_Activate`/`DoActivateThing`) and `p_mobj.cpp` (`AActor::Activate`) — see
[Activation](../concepts/activation.md) for the full source citation list.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** action special, index 130.

Unconditionally calls the matching actor(s)' `Activate` C++ method. On the vast majority of
actors this is a no-op — see Behavior below and [Activation](../concepts/activation.md) for the
full write-up (this file is the canonical signature entry; the concept page has the rest of the
verification, including why the ZDoom wiki's ZScript-era "Activation" page mostly doesn't apply
to Zandronum).

## Parameters

- `tid` — TID of the actor(s) to activate. `0` means "no tid given": falls back to the calling
  script's activator (`it`) if one exists, otherwise the call does nothing and returns `false`.
  Non-zero processes every actor matching that TID.

## Behavior

Returns `true` if at least one actor was found and processed; with a non-zero `tid` this is
`count != 0` — there is no way to distinguish "some actors matched but did nothing observable"
from "some actors matched and did something," since the underlying `DoActivateThing`
(`p_lnspec.cpp:1210`) always runs unconditionally per matched actor regardless of whether anything
observable happens.

Per matched actor, two things happen unconditionally: the `THINGSPEC_Switch` bookkeeping bits are
cleared/flipped (so a switchable actor's *next* USESPECIAL/BUMPSPECIAL trigger goes the other
way), and the actor's `Activate` C++ method is called regardless of its `activationtype` flags.
The **default** `AActor::Activate` (what every actor gets unless it's one of the native classes
that override it — at least nineteen, spanning several unrelated subsystems, not a short
enumerable handful; see the linked concept page) only does something for a living monster or an
ice corpse — on any other actor (decoration, non-monster, dead monster without `MF_ICECORPSE`)
this call is a confirmed no-op.

## See also

- [Activation](../concepts/activation.md) — full verification against `p_lnspec.cpp`/`p_mobj.cpp`,
  the native classes that override the default `Activate`, and how this interacts with the
  DECORATE `Activation` property and `USESPECIAL`/`BUMPSPECIAL` flags.

## Engine-family divergence

UZDoom implements the same call chain at the C++ level: `LS_Thing_Activate`
(`src/playsim/p_lnspec.cpp:1421`) and the shared `DoActivateThing` helper (`p_lnspec.cpp:1399`)
are structurally identical to Zandronum's — same `tid=0` fallback to the calling script's
activator, same unconditional `THINGSPEC_Switch` bookkeeping, same `count != 0` return semantics.

Where UZDoom diverges is what "call the actor's `Activate` method" means. Zandronum's `Activate`
is a fixed C++ virtual with no DECORATE override point (see the linked concept page). UZDoom
instead routes through `AActor::CallActivate` (`src/playsim/p_mobj.cpp:5856`), which checks for a
ZScript override of `Activate` before falling back to the native `AActor::Activate`
(`p_mobj.cpp:5828`) — itself byte-identical in logic to Zandronum's (monster-or-ice-corpse-only,
flips `MF2_DORMANT`, jumps to the `Active` state if one exists). Because UZDoom ships ZScript, and
any ZScript actor can freely override `Activate`/`Deactivate`, this doc's "confirmed no-op on
anything but a monster/ice-corpse" claim above describes only the *default*, inherited behavior on
UZDoom, not a universal one the way it is on Zandronum. Several stock UZDoom stdlib actors
override `Activate` and/or `Deactivate` with their own behavior: `AmbientSound` (now a ZScript
class in `soundsequence.zs` — no longer the Zandronum-only C++ `AAmbientSound`), plus
`SoundSequence`, `SoundEnvironment`, `SectorAction`, `SecretTrigger`, `Spark`, `Fountain`,
`MapMarker`, `MovingCamera` and a Hexen sibling, several dynamic-light actors (`dynlights.zs`),
and a couple of Hexen-specific actors (`spike.zs`, `hexenspecialdecs.zs`). Calling
`Thing_Activate`/`Thing_Deactivate` on an actor of one of these classes runs that class's own
override, not the generic monster/ice-corpse check. Zandronum's fixed (nineteen-and-counting-class)
exception list doesn't carry over as a closed set at all — Invasion has no UZDoom equivalent (see
the linked concept page), and the override surface on UZDoom is open-ended (any ZScript actor)
rather than a fixed list of native C++ classes.
