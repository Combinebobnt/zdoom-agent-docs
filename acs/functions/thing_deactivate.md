# `bool Thing_Deactivate(int tid)`

Unconditionally calls the matching actor(s)' `Deactivate` C++ method. On the vast majority of
actors this is a no-op — see Behavior below and [Activation](../concepts/activation.md) for the
full write-up (this file is the canonical signature entry; the concept page has the rest of the
verification, including why the ZDoom wiki's ZScript-era "Activation" page mostly doesn't apply
to this fork).

**Bucket:** action special, index 131.

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
The **default** `AActor::Deactivate` (what every actor gets unless it's one of three classes that
override it) only does something for a living monster or an ice corpse — on any other actor
(decoration, non-monster, dead monster without `MF_ICECORPSE`) this call is a confirmed no-op.

## See also

- [Activation](../concepts/activation.md) — full verification against `p_lnspec.cpp`/`p_mobj.cpp`,
  the three C++ classes that override the default `Deactivate`, and how this interacts with the
  DECORATE `Activation` property and `USESPECIAL`/`BUMPSPECIAL` flags.

**Tier:** A. **Provenance:** wiki page `Activation - ZDoom Wiki.html` (`_intake/`, retrieved
2026-07-29, `oldid=54953`) + verified against the Zandronum source's `p_lnspec.cpp`
(`LS_Thing_Deactivate`/`DoDeactivateThing`) and `p_mobj.cpp` (`AActor::Deactivate`) — see
[Activation](../concepts/activation.md) for the full source citation list. **Engine:** Zandronum
3.2.1 (verified against the Zandronum source `master` HEAD, a `3.3-alpha` development snapshot
ahead of the 3.2.1 target; this is Hexen/Boom-era action-special machinery, long predating that
gap, so it is unaffected).
