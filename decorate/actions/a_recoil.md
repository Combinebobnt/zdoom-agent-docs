# `void A_Recoil(float xyvel)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_Recoil` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_Recoil&oldid=48676) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:2797-2818`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `AActor` action function.

Applies velocity to the calling actor in the direction opposite to its facing angle, simulating weapon recoil or knockback. Recoil is purely horizontal (x/y only); the z velocity component is never modified.

## Parameters

- **`xyvel`** — The magnitude of recoil velocity applied opposite to the actor's facing direction. A positive value pushes the actor backward (180° offset from facing); a negative value pushes it forward (in the direction it faces). The value is interpreted as a fixed-point velocity.

## Behavior

**Horizontal-only:** The function only modifies x and y velocity components, computed using the actor's current `angle` via cosine/sine. The z (vertical) component remains unchanged — `A_Recoil` does not apply upward or downward velocity, even indirectly.

**No pitch adjustment:** The action function does not account for the actor's pitch (up/down facing angle). For a weapon, this means recoil is applied horizontally even if the weapon points upward. If vertical recoil relative to pitch is desired, adjust `xyvel` in DECORATE itself: e.g., `A_Recoil(base_recoil * cos(pitch))` — `pitch` is accessible in DECORATE expressions (see [`concepts/expressions.md`](../concepts/expressions.md)).

**Network multiplayer (Zandronum):**
- **For players:** Recoil is applied on the client-side actor without sending updates to the server. The server does not broadcast the velocity change.
- **For non-player actors:** Recoil is skipped on clients (even if `+CLIENTSIDEONLY` is not set); the server applies it and broadcasts a full position/velocity resync via `SERVERCOMMANDS_MoveThingExact` to all clients.

(The fork author flagged the player-side behavior as deliberate-but-unsure in a source comment.)

## Zandronum-specific: client/server behavior

**This entire client/server split is Zandronum-only.** UZDoom's `A_Recoil` (`src/playsim/p_actionfunctions.cpp`, `DEFINE_ACTION_FUNCTION(AActor, A_Recoil)`) calls `self->Thrust(self->Angles.Yaw + DAngle::fromDeg(180.), xyvel)` unconditionally — there is no client-mode check, no player/non-player distinction, and no follow-up position/velocity resync. `Thrust(DAngle, double)` (`src/playsim/actor.h`) only adds to `Vel.X`/`Vel.Y`, matching the horizontal-only behavior described above. UZDoom's source tree has no `NETWORK_InClientMode`-equivalent gate and no `SERVERCOMMANDS_*`-equivalent broadcast mechanism anywhere, so recoil is applied identically for every actor and every peer with no server-authoritative resync step at all.

## Related functions

- **[`A_ChangeVelocity`](a_changevelocity.md)** — more general velocity manipulation with flags for additive/replace and relative/absolute coordinate modes.
- **[`A_ScaleVelocity`](a_scalevelocity.md)** — multiply the actor's velocity by a scalar.
- **[`A_Stop`](a_stop.md)** — set velocity to zero on all axes.
