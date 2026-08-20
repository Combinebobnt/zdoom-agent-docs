# `+POWERSPEED.NOTRAIL`

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Source-derived (no wiki page consulted) — verified against `src/thingdef/
thingdef_data.cpp` (flag registration) and `src/g_shared/a_artifacts.cpp` (`APowerSpeed::
DoEffect`).
**Bucket:** `DEFINE_FLAG(PSF, NOTRAIL, APowerSpeed, SpeedFlags)` in `src/thingdef/
thingdef_data.cpp`; registered under `RUNTIME_CLASS(APowerSpeed)` in `FlagLists`. `PSF_NOTRAIL ==
1` (`src/g_shared/a_artifacts.h`). On UZDoom the equivalent lives in the ZScript `PowerSpeed`
class itself (`wadsrc/static/zscript/actors/inventory/powerups.zs:1196-1201`), not in engine C++.

Suppresses the `PlayerSpeedTrail` afterimage spawning that `PowerSpeed` (and any DECORATE
subclass of it) produces while active. On Zandronum it is a **flag only**, written
`+POWERSPEED.NOTRAIL` (qualified) or `+NOTRAIL` (unqualified — resolves to the same flag since
it's the only `NOTRAIL` registered against a class in the `PowerSpeed` ancestry chain) — **not**
a property on that engine; `PowerSpeed.NoTrail <value>` does not exist there and is a natural but
wrong guess. UZDoom changes this — see "Engine-family divergence: property form" below.

## Behavior

On Zandronum, `APowerSpeed::DoEffect` spawns trail actors based purely on player velocity (>12
map units/tic) — it never consults the `Speed` property at all. This means even a `Speed 1.0`
subclass (a true no-op speed multiplier — see
[powerup-as-inert-timer](../concepts/powerup-as-inert-timer.md)) still spawns trails unless this
flag is set. UZDoom's ZScript `PowerSpeed.DoEffect` agrees: it also gates purely on the owner's
velocity magnitude (again a >12-unit threshold) and never reads `Speed` either — this part of the
behavior is a clean cross-engine match, not a divergence.

**Trail arbitration gotcha (Zandronum):** `DoEffect` walks the player's inventory for other active
`PowerSpeed` instances, and only the *last* one **without** `PSF_NOTRAIL` set actually draws a
trail. A `PowerSpeed` subclass without this flag therefore doesn't just draw its own (likely
unwanted) trail — it can also participate in and disrupt the arbitration for a genuine, trail-
bearing speed powerup (e.g. a turbosphere) the player is also holding, suppressing or replacing
its trail. **This arbitration logic is not the same on UZDoom** — see "Engine-family divergence:
trail arbitration" below.

**Negative finding:** no `cl_speedtrails`-style client cvar exists anywhere in the Zandronum
source (checked via a case-insensitive search for `speedtrail` across `src/`), nor anywhere in
UZDoom's source (same case-insensitive search, engine C++ and ZScript stdlib both) — on either
engine there is no alternate way to suppress trails short of this flag/property.

## Engine-family divergence: property form

**UZDoom exposes `NoTrail` as both a property and a flag; Zandronum exposes it only as a flag.**
The `PowerSpeed` ZScript class declares an `int NoTrail` field with both a `Property NoTrail`
binding and a `FlagDef NoTrail` binding to that same field, at bit 0 — the same bit position as
Zandronum's `PSF_NOTRAIL`. A comment on the property declaration itself notes it was originally
flag-only, matching Zandronum's implementation. Practically: on UZDoom, `PowerSpeed.NoTrail 1` (or
any non-zero value) in a subclass's `Default` block works exactly like `+NOTRAIL`/
`+POWERSPEED.NOTRAIL` — the "natural but wrong guess" caveat above applies to Zandronum only, not
to UZDoom.

## Engine-family divergence: trail arbitration

**UZDoom's arbitration loop checks the wrong instance's `NoTrail` value, changing the observed
outcome when multiple `PowerSpeed` items overlap.** Zandronum's loop (described in prose only, per
this tree's licensing rule — see `src/g_shared/a_artifacts.cpp:1267-1273`) walks the remaining
inventory chain and, for each further `PowerSpeed` item found, tests *that other item's* own
no-trail flag; it only backs off (returns without drawing) if a later item without `PSF_NOTRAIL`
exists, which is what lets an earlier item still draw its trail when every later `PowerSpeed` item
has `PSF_NOTRAIL` set.

UZDoom's equivalent loop (`powerups.zs:1240-1247`) walks the same chain shape (via the native
`Inv` pointer) but its per-item test reads the *executing instance's own* `NoTrail` field instead
of the other item's — and since the method already returned earlier in the function if its own
`NoTrail` were true, that condition is always true by the time the loop runs. The practical effect
is that the loop backs off as soon as it finds *any* further `PowerSpeed` item in the chain,
regardless of that item's own `NoTrail` setting. Worked example: player holds `A` (no `NoTrail`,
earlier in the inventory chain) and `B` (`NoTrail` set, later in the chain). On Zandronum, `A`'s
`DoEffect` walks forward, sees `B` has `PSF_NOTRAIL` set (so `B` doesn't count), finds nothing
else, and proceeds to draw a trail — `B` itself returns early and draws nothing, so `A` alone
draws. On UZDoom, `A`'s `DoEffect` walks forward, finds `B` is *a* `PowerSpeed` instance (its own
`NoTrail` setting is never inspected), and backs off; `B` still returns early on its own `NoTrail`
check. Neither item draws a trail in that configuration on UZDoom, where Zandronum would still
show one from `A`. This reads as an unintentional variable-scoping slip in the ZScript port
(`NoTrail` vs. the qualified `sitem.NoTrail` it likely should be) rather than a deliberate design
change, but this doc only reports what the checked-out source actually does, not upstream intent
— see `shared/AUTHORING.md`'s caveat that this UZDoom checkout can diverge from mainline GZDoom in
ways not yet catalogued here.

## See also

- [Using a `Powerup` subclass as an inert countdown timer](../concepts/powerup-as-inert-timer.md)
- [`Powerup`](../classes/powerup.md)
