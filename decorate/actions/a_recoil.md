# `void A_Recoil(float xyvel)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_Recoil` (retrieved 2026-08-01, oldid=48676) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:2797-2818`.
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

## Related functions

- **[`A_ChangeVelocity`](a_changevelocity.md)** — more general velocity manipulation with flags for additive/replace and relative/absolute coordinate modes.
- **[`A_ScaleVelocity`](a_scalevelocity.md)** — multiply the actor's velocity by a scalar.
- **[`A_Stop`](a_stop.md)** — set velocity to zero on all axes.
