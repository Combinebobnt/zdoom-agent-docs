# Actor velocity-getter family

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki pages `GetActorVelX - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=GetActorVelX&oldid=35628`),
`GetActorVelY - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=GetActorVelY&oldid=36021`), `GetActorVelZ - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=GetActorVelZ&oldid=35625`) (all `_intake/`, retrieved 2026-07-29) + source-verified against
`p_acs.cpp:5926-5936` (the three `ACSF_GetActorVel*` cases), `p_acs.cpp:4445-4456`
(`SingleActorFromTID`), `p_mobj.cpp:2004,2061-2122,2908` (sign convention and per-tic
consumption), `actor.h:998` (`velz` field type), and `setactorvelocity.md` for cross-checked
velocity units and the player-bob-field asymmetry. Return type, units, per-axis sign convention,
`tid=0`→activator semantics, first-match-only asymmetry with `SetActorVelocity`, and the
Z-specific player-struct wrinkle all verified; no wiki/fork divergence found for any of the
three — each wiki page correctly states sign and `fixed` return but omits units, TID/NULL
behavior, and the Get/Set asymmetry, which are gaps this file fills rather than corrections.
The landing/at-rest predicate note (added later, no wiki source) is source-verified against
`p_mobj.cpp:2058,2475,2514,2565-2585,3084-3125,3150-3153` (Zandronum `master` HEAD, 2026-08-03) —
derived while debugging a project's "play a sound when a thrown item lands" script that
misfired at the apex of vertical throws and never fired on wall impacts.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** all three extension functions (negative indices in `zcommon.bcs`'s `special` table).
`ACSF_GetActorVelX`/`ACSF_GetActorVelY`/`ACSF_GetActorVelZ` are consecutive `case`s in
`DLevelScript::CallFunction` (the Zandronum source's `src/p_acs.cpp:5926-5936`), each resolving the
actor via the file-local `SingleActorFromTID(int, AActor*)` helper (`p_acs.cpp:4445-4456`) and
returning `actor != NULL ? actor->vel{x,y,z} : 0`. All three enum members and switch cases are
confirmed live (not in the Zandronum-dead ACSF range 93-99 documented in
[the spawning family](spawning.md), nor the 205-209 range documented in
[zdoom-math-stubs](zdoom-math-stubs.md) — dead on Zandronum, but note that range is live on
UZDoom). **UZDoom source-verified
too:** the same three case names are still consecutive `case`s in `DLevelScript::CallFunction`
(the UZDoom source's `src/playsim/p_acs.cpp:5410-5423`), each resolving the actor via
`FLevelLocals::SingleActorFromTID` — now a header-inline `Level` method
(`src/g_levellocals.h:342-345`) rather than a file-local helper, but with the identical
`tid == 0 ? defactor : iterator.Next()` logic — and returning `actor != NULL ? DoubleToACS(actor->Vel.{X,Y,Z}) : 0`.
See the "Engine-family divergence" section below for what `DoubleToACS` and `actor->Vel` imply for
the return value's precision.

`GetActorVelX`, `GetActorVelY`, `GetActorVelZ` — three extension functions
(`zcommon.bcs` indices -9/-10/-11) that are one-line `case`s in the same engine switch statement,
differing only in which velocity member is read (`velx`/`vely`/`velz`). Neither requires the
others to be useful — this isn't a mandatory-sequence family like [Lump I/O](lump-io.md) — but
every finding below is identical prose for all three except the sign-convention axis and
`GetActorVelZ`'s one extra player-struct wrinkle, so one file avoids maintaining three
near-duplicate `functions/*.md` pages (same precedent as the
[plane-trigger family](plane-trigger.md)).

---

## `fixed GetActorVelX(int tid)`
## `fixed GetActorVelY(int tid)`
## `fixed GetActorVelZ(int tid)`

Gets one velocity component of an actor by TID, as **fixed-point map units per tic**, read
directly from the actor's `velx`/`vely`/`velz` field with no scaling macro applied (contrast
[Floor_MoveToValue](../functions/floor_movetovalue.md)'s `/8`-scaled `speed` argument). These are
the same units [SetActorVelocity](../functions/setactorvelocity.md) expects.

- **Sign convention, per axis** (all verified against source, not just the wiki's claim):
  - X: positive = eastward, negative = westward — `actor->velx = FixedMul(speed, finecosine[angle])`,
    angle `0` (East) paired with `+FRACUNIT` (`p_mobj.cpp:2004`); consumed per-tic by
    `P_XYMovement` (`p_mobj.cpp:2061-2122`).
  - Y: positive = northward, negative = southward.
  - Z: positive = upward, negative = downward — `mo->z += mo->velz` once per tic
    (`p_mobj.cpp:2908`).
- `tid` — **`0` means "the activator"** (`SingleActorFromTID`'s `tid == 0` fallback); the
  caller-side ternary guards against a NULL activator (e.g. an `OPEN`/`ENTER`-type script with no
  natural activator), returning `0` silently rather than crashing.
- **`tid != 0`: reads only the first actor matching that TID**, via a single `Next()` call in
  `SingleActorFromTID`. **Asymmetric with `SetActorVelocity`**, which mutates *every* actor
  sharing that TID in one call via `TActorIterator`. In projects where TIDs are deliberately
  shared across many actors, a Get on a shared TID reads only the first match, but a Set touches
  every one. (The asymmetry can go unexercised for `GetActorVelZ` specifically if every call site
  happens to pass `tid=0`, but the mechanism is identical to X/Y.)
- **Silent `0` conflation: bad TID, no activator, and a genuinely stationary actor are
  indistinguishable** — same NULL/zero-value conflation pattern already documented for
  [ActivatorTID](../functions/activatortid.md)/[GetSectorFloorZ](../functions/getsectorfloorz.md)/
  [GetActorAngle](../functions/getactorangle.md). **The conflation is materially worse for
  `GetActorVelZ` than for the angle getter:** a zero angle is one of 65536 possible return values,
  but `velz == 0` is the *majority case* in a level — nearly every stationary monster, item, and
  fixture is at rest. A caller can't tell "bad TID," "no activator," and "standing still" apart
  from the return value alone; validate the TID/activator separately first if that distinction
  matters.
- **`GetActorVelZ` vs. player velocity setters: an asymmetry not present for X/Y in the same
  way.** `SetActorVelocity`'s underlying `P_Thing_SetVelocity` updates `actor->velz`
  unconditionally, but for a player actor it only updates the player-bob-only `player->velx`/
  `player->vely` fields, not a separate Z-bob field (there isn't one). `GetActorVelZ` always
  reads `actor->velz` directly, so for a player this getter reads the real actor velocity, not a
  bob-only copy — X and Y don't have this player-struct wrinkle since there's no separate
  non-bob field they could diverge from. In practice this rarely matters since most scripts read
  the actor's own velocity, but it's a structural quirk worth knowing about.
- **Netcode note (`CLIENTSIDE` scripts only), applies to all three identically:** a `CLIENTSIDE`
  script reading any of these on a non-local actor can see a stale value — the server uses delta
  compression (only sends velocity when it changes from the last-sent value), so a `CLIENTSIDE`
  script sees the last snapshot, not necessarily current server-side state. This applies to
  actor-reading getters generally, not specifically to velocity. Local actors (the activator in
  most contexts, or any actor looked up locally under client-side prediction) have no
  stale-value issue.
- **Velocity sign is not a landing/at-rest predicate — a common scripting mistake.** A script
  that waits for an airborne actor to "land" by polling for `velz` to cross zero, or for a sign
  flip, is unreliable in two ways (`p_mobj.cpp`'s `P_ZMovement`/`P_XYMovement`, function names
  vary by fork vintage but the logic below is stable across ZDoom-family engines):
  - `velz` is zeroed **only on a descending floor/actor contact**, gated on `mo->velz < 0` at the
    moment `mo->z` is snapped to `mo->floorz` (Zandronum `p_mobj.cpp:3150-3153`: `mo->z =
    mo->floorz; if (mo->velz < 0) { ... mo->velz = 0; }`). A purely vertical throw (`velx == 0`)
    passes through `velz == 0` at the apex of its arc from ordinary gravity deceleration, with no
    floor contact at all — a script polling for "`velz` was positive, now it's zero or negative"
    fires at the apex, not on landing. Missiles take a separate branch first (non-`NOEXPLODEFLOOR`
    missiles explode instead of landing; see the surrounding `MF_MISSILE` block at
    `p_mobj.cpp:3084-3125`).
  - A **blocked horizontal move zeroes X/Y velocity only**, never `velz`: the non-missile,
    non-bouncing failure branch of `P_XYMovement`'s wall-collision handling is a flat
    `mo->velx = mo->vely = 0;` (`p_mobj.cpp:2475`, inside the `else` of the blocked-move check —
    it does not deflect or slide). A script watching only `velz` for "stopped" never observes a
    wall impact.
  - Ground friction (the `STOPSPEED` snap, `0x1000` = 0.0625 map units/tic, `p_mobj.cpp:2058`)
    also zeroes X/Y once speed drops below that threshold (`p_mobj.cpp:2565-2585`), but this block
    is skipped entirely for missiles/`MF_SKULLFLY` and early-returns while airborne (guarded on
    `mo->z > mo->floorz`, `p_mobj.cpp:2514`) — so it never fires *before* the actor is actually on
    the ground, and the velocity drop it produces is small (from at most ~0.0625 units/tic) versus
    a wall impact killing an arbitrary in-flight speed in one tic. A caller distinguishing "wall
    hit" from "friction stopped a slide" can use that magnitude gap as a threshold.
  - **Correct predicate:** test position, not velocity — `GetActorZ(tid) - GetActorFloorZ(tid) ==
    0` (feet on floor; see [GetActorFloorZ](../functions/getactorfloorz.md) for the 3D-floor and
    stale-on-spawn caveats) combined with `GetActorVelZ(tid) == 0 && <previous-tic velz> < 0` to
    also catch landing on a raised 3D floor or another actor's head (not just the sector floor).
    A large one-tic drop in `abs(velx) + abs(vely)` (above the `STOPSPEED` range) is a reasonable
    proxy for a wall/obstacle impact specifically.

## Engine-family divergence: internal velocity representation is double, not fixed-point

Zandronum stores an actor's velocity as three native `fixed_t` fields (`velx`/`vely`/`velz` on
`AActor`); every mechanism the sign-convention and landing/at-rest bullets above cite —
`FixedMul`-driven angle-to-velocity conversion, the floor-snap zeroing, the `STOPSPEED` friction
snap, gravity accumulation — operates on that fixed-point value directly, truncating to 16.16
precision at every intermediate step.

**UZDoom stores the same quantity as `actor->Vel`, a `DVector3` of `double`s
(`src/playsim/actor.h:1189`)**, and the whole physics chain these bullets describe now runs in
double precision on that engine — angle-to-velocity conversion goes through `AActor::VelFromAngle`
calling `DAngle::Cos()`/`Sin()` (`actor.h:1645-1660`, no `finecosine`/`finesine` table involved),
Z is integrated via `AActor::AddZ(Vel.Z)` once per tic (`p_mobj.cpp:2952`), gravity is subtracted
from `Vel.Z` in `AActor::FallAndSink` (`p_mobj.cpp:3336-3354`), and the floor-snap zeroing,
blocked-move X/Y zeroing, and `STOPSPEED` friction snap are all still present and structurally
identical to the Zandronum mechanism described above — same guard conditions, same early-return
shape, just phrased over `double`s and at different line numbers (`p_mobj.cpp:2751` blocked-move
zero, `p_mobj.cpp:2793-2814` airborne-friction early return, `p_mobj.cpp:2399,2848-2866`
`STOPSPEED` snap — `#define STOPSPEED (0x1000/65536.)`, the same 0.0625 map-units/tic threshold,
`p_mobj.cpp:3096-3097,3126` landing zero gated on `Vel.Z < 0` at the floor-snap `SetZ` call). None
of the sign-convention or landing-predicate claims above change in substance on UZDoom.

`GetActorVelX`/`Y`/`Z` themselves only read the field and encode it for return —
`return actor != NULL ? DoubleToACS(actor->Vel.{X,Y,Z}) : 0`, where `DoubleToACS` is
`FloatToFixed<16>` (`src/playsim/p_acs.cpp:607-610`) — so the **ACS-visible return value stays a
16.16 fixed-point map-units-per-tic quantity on both engines**, and a single read of a settled
(non-moving) actor's velocity returns identically on both. The divergence only becomes observable
across a chain of physics ticks: Zandronum's `fixed_t` arithmetic truncates to 16.16 at every
intermediate multiply/add inside `P_XYMovement`/`P_ZMovement`, while UZDoom's `double` arithmetic
carries far more precision through the same chain and is only rounded down to 16.16 at the moment
`GetActorVelX`/`Y`/`Z` returns it. A script polling velocity after several ticks of gravity,
friction, or angle-based thrust (e.g. `VelFromAngle`/`Thrust`) can see a UZDoom value that differs
from Zandronum's by a fraction of a fixed-point unit for the "same" scripted scenario — not a
behavioral bug, just accumulated floating-point-vs-fixed-point rounding drift, the same class of
divergence already documented for [Sin](../functions/sin.md)/[Cos](../functions/cos.md) (input
quantization there; intermediate-precision drift here) and for
[GetActorProperty](../functions/getactorproperty.md)'s `APROP_SPEED`-family properties (also
routed through `DoubleToACS`).

## Engine-family divergence: netcode note doesn't carry over as stated

The "Netcode note (`CLIENTSIDE` scripts only)" bullet above describes Zandronum's client-server
delta-compression model specifically — a real, source-verified Zandronum mechanism (see
[Client-side scripting](../concepts/clientside-scripting.md), whose own file-level field already
records `Applies to: UZDoom=no` for this whole topic). UZDoom's `CLIENTSIDE`-script handling is not
just architecturally different, it is currently a stub on the checkout this file was re-verified
against: `IsClientSideScript` in `src/playsim/p_acs.cpp` (~line 664) unconditionally `return
false;`, with an inline comment (not reproduced here — GPL-3.0) noting UZDoom's own client-side
handling is disabled pending a replacement flag, because enabling it broke existing `CLIENTSIDE`
scripts. A companion helper, `ShouldIgnoreClientSideScript` (`p_acs.cpp:~653-660`), does something
UZDoom-specific instead — gating on `AActor::IsClientSide()` and console-player ownership, not on
a server/client network split with delta-compressed actor state. Whatever staleness a
`CLIENTSIDE`-flagged script's velocity reads might see on UZDoom, it is not the "server withheld an
unchanged value" mechanism this bullet describes, and this file takes no position on what, if
anything, replaces it — that question belongs to
[Client-side scripting](../concepts/clientside-scripting.md), not to this getter family.

## Example (adapted from the wiki)

```acs
script 1 ENTER
{
    // Print the angle the activator is moving in, from X/Y velocity
    while (TRUE)
    {
        int angle = VectorAngle(GetActorVelX(0), GetActorVelY(0));
        Print(f:angle);
        Delay(1);
    }
}

script 2 ENTER
{
    // Print the activator's current speed (magnitude of the 3D velocity vector)
    while (TRUE)
    {
        fixed x = GetActorVelX(0);
        fixed y = GetActorVelY(0);
        fixed z = GetActorVelZ(0);
        fixed speed_squared = FixedMul(x, x) + FixedMul(y, y) + FixedMul(z, z);
        Print(f:FixedSqrt(speed_squared));  // FixedSqrt: ACSF -49, no Zandronum divergence
        Delay(1);
    }
}
```
