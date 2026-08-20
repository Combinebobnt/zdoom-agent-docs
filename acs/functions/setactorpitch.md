# `void SetActorPitch(int tid, fixed pitch)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `SetActorPitch - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29, `https://zdoom.org/w/index.php?title=SetActorPitch&oldid=22666`) + source-verified against `p_acs.cpp:5869-5895,12039-12044,12599-12601`, `p_mobj.cpp:3929-3937`, `p_user.cpp:3336-4014`, `zt-bcc/src/builtin.c:150`. Wiki's `int pitch` typing corrected to `fixed` per the actual builtin signature; wiki's implied "there is a valid range" note confirmed true in *convention* but not enforced by this function (no clamp in source).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Sets an actor's view/aim pitch. Compiler builtin (`PCD_SETACTORPITCH`,
the zt-bcc source's `src/builtin.c:150`: `{ "setactorpitch", ";if" }` — void return, `int` then
`fixed` params), implementation via the static helper `SetActorPitch(AActor*, int tid, int angle,
bool interpolate)` at the Zandronum source's `src/p_acs.cpp:5869-5895`, called from
`case PCD_SETACTORPITCH:` at `p_acs.cpp:12599-12601`.

- `tid` — **`0` means "the activator"** (`p_acs.cpp:5871`: `if (tid == 0) { if (activator != NULL) ... }`).
- `pitch` — a **fixed-point angle** in the sense documented in
  [Units and encodings](../concepts/units-and-encodings.md#pitches): a `fixed` value where the
  useful range is `-0.25` (looking straight up) to `0.25` (looking straight down), negative-is-up.
  The wiki page types this parameter as plain `int`, but `zcommon.bcs`'s own declaration and
  `builtin.c`'s `;if` signature both agree it's `fixed`, matching the type actually pushed on the
  ACS stack and left-shifted by 16 into the engine's internal BAM-style pitch representation
  (`angle << 16`, `p_acs.cpp:5891`/`5893`) before being stored in `AActor::pitch`.

## `tid != 0` sets **every** actor with that TID — this is a real, verified divergence from `GetActorPitch`

`GetActorPitch` (`p_acs.cpp:12039-12044`) resolves its TID through the `SingleActorFromTID` helper
(`p_acs.cpp` — `tid == 0 ? defactor : iterator.Next()`), which reads only the **first** actor an
`FActorIterator` finds. `SetActorPitch`'s own TID branch does not use that helper — for `tid != 0`
it walks the *entire* iterator itself:

```cpp
FActorIterator iterator(tid);
AActor *actor;
while ((actor = iterator.Next()))
{
    actor->SetPitch(angle << 16, interpolate);
    ...
}
```

(`p_acs.cpp:5886-5895`) — so calling `SetActorPitch(tid, p)` with a TID shared by multiple actors
sets **all of them**, while `GetActorPitch(tid)` would only ever have read the first one. Don't
assume Get/Set are symmetric for a shared TID.

## No range clamping — unlike normal player mlook input

The wiki's "See GetActorPitch for the possible range" note implies pitch is range-limited, and the
*useful* fixed-point range genuinely is `-0.25`..`0.25` per the engine's normal look-up/down
convention (see the concepts doc). But `AActor::SetPitch` itself performs **no clamping at all**:

```cpp
void AActor::SetPitch(int p, bool interpolate)
{
    if (p != pitch)
    {
        pitch = p;
        ...
    }
}
```

(`p_mobj.cpp:3929-3937`) — a plain assignment. Ordinary player mouselook pitch *is* clamped
elsewhere (e.g. the `ANGLE_1*90` bound in `P_PlayerThink`/camera code, `p_user.cpp:3336-4014`), but
that clamp lives in the mlook input path, not in `SetPitch`/`SetActorPitch`. Calling
`SetActorPitch` from ACS with a value outside `-0.25`..`0.25` is not rejected or wrapped by this
function — it will set an out-of-normal-range pitch verbatim, which can flip the view/aim past
straight up or down.

## Engine-family divergence: player-actor pitch is clamped, unlike Zandronum

UZDoom's version of the underlying helper (`DLevelScript::SetActorPitch`, UZDoom's
`src/playsim/p_acs.cpp`) forwards into `AActor::SetPitch`, which is not the unconditional field
assignment Zandronum uses. When the actor being written to is a player pawn, `SetPitch` first
clamps the requested angle to that player's own current look-up/look-down limits — the same
bounds that constrain their ordinary mouselook input — before storing it. A non-player actor is
only clamped if the caller opts in via a dedicated "force clamp" flag on the call, and the
ACS-facing `PCD_SETACTORPITCH` case never sets that flag, so monsters and other non-player
actors remain unclamped exactly as described above for Zandronum.

Net effect: `SetActorPitch(tid, pitch)` behaves the same as the Zandronum description above when
`tid` resolves only to non-player actors. But when it resolves to a player (`tid == 0` against a
player activator, or an explicit TID that happens to be a player), UZDoom silently pulls an
out-of-range pitch back within that player's configured look limits instead of storing it
verbatim — a script that relies on "no clamping at all" to snap a player's view straight up,
straight down, or past either extreme gets the literal requested pitch on Zandronum but a
clamped one on UZDoom. This engine's per-player look-limit bounds are themselves configurable
and networked per-client, not a single fixed constant, so the exact clamp range isn't a fixed
number to document here.

Separately, the "Netcode" section above is Zandronum-specific: it describes that engine's
client-server replication step, which has no equivalent in UZDoom's single-process networking
model — nothing comparable fires there.

## Interpolation is hardcoded off from ACS

The static `SetActorPitch` helper takes an `interpolate` flag (used to set `player->cheats |=
CF_INTERPVIEW` for smooth camera transitions), but the ACS-facing `PCD_SETACTORPITCH` case always
calls it with `false` (`p_acs.cpp:12600`: `SetActorPitch(activator, STACK(2), STACK(1), false);`)
— there is no ACS-level way to request a smoothly-interpolated pitch change through this function;
the pitch snaps instantly.

## Netcode: server-authoritative, replicated per matching actor

After each `SetPitch` call, if this is running on the server it also does
`SERVERCOMMANDS_MoveThingExact(actor, CM_PITCH)` (`p_acs.cpp:5890`/`5894`) to sync the new pitch to
clients. On a listen/dedicated server this replicates correctly; if called from a `CLIENTSIDE`
script on a non-server client, the local pitch still changes but nothing is sent out — the usual
Zandronum clientside caveat (state stays local, doesn't propagate).

**Example — reset the activator's pitch to level (from the wiki):**

```text
script 1 (void)
{
    SetActorPitch(0, 0);
}
```
