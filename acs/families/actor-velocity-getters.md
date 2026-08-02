# Actor velocity-getter family

`GetActorVelX`, `GetActorVelY`, `GetActorVelZ` — three extension functions
(`zcommon.bcs` indices -9/-10/-11) that are one-line `case`s in the same engine switch statement,
differing only in which velocity member is read (`velx`/`vely`/`velz`). Neither requires the
others to be useful — this isn't a mandatory-sequence family like [Lump I/O](lump-io.md) — but
every finding below is identical prose for all three except the sign-convention axis and
`GetActorVelZ`'s one extra player-struct wrinkle, so one file avoids maintaining three
near-duplicate `functions/*.md` pages (same precedent as the
[plane-trigger family](plane-trigger.md)).

**Bucket:** all three extension functions (negative indices in `zcommon.bcs`'s `special` table).
`ACSF_GetActorVelX`/`ACSF_GetActorVelY`/`ACSF_GetActorVelZ` are consecutive `case`s in
`DLevelScript::CallFunction` (the Zandronum source's `src/p_acs.cpp:5926-5936`), each resolving the
actor via the file-local `SingleActorFromTID(int, AActor*)` helper (`p_acs.cpp:4445-4456`) and
returning `actor != NULL ? actor->vel{x,y,z} : 0`. All three enum members and switch cases are
confirmed live (not in either of the dead ACSF ranges 93-99/205-209 already documented in
[the spawning family](spawning.md)/[zdoom-math-stubs](zdoom-math-stubs.md)).

**Tier:** A. **Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master`/`3.3-alpha`
HEAD — see "Engine scope" in `../../shared/AUTHORING.md`).

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

## Example (adapted from the wiki)

```c
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

**Provenance:** wiki pages `GetActorVelX - ZDoom Wiki.html` (`oldid=35628`),
`GetActorVelY - ZDoom Wiki.html` (`oldid=36021`), `GetActorVelZ - ZDoom Wiki.html`
(`oldid=35625`) (all `_intake/`, retrieved 2026-07-29) + source-verified against
`p_acs.cpp:5926-5936` (the three `ACSF_GetActorVel*` cases), `p_acs.cpp:4445-4456`
(`SingleActorFromTID`), `p_mobj.cpp:2004,2061-2122,2908` (sign convention and per-tic
consumption), `actor.h:998` (`velz` field type), and `setactorvelocity.md` for cross-checked
velocity units and the player-bob-field asymmetry. Return type, units, per-axis sign convention,
`tid=0`→activator semantics, first-match-only asymmetry with `SetActorVelocity`, and the
Z-specific player-struct wrinkle all verified; no wiki/fork divergence found for any of the
three — each wiki page correctly states sign and `fixed` return but omits units, TID/NULL
behavior, and the Get/Set asymmetry, which are gaps this file fills rather than corrections.
**Engine:** Zandronum 3.2.1. **Tier:** A.
