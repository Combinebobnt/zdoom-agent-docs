# `A_AlertMonsters(float maxdist = 0, int flags = 0)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_AlertMonsters` (retrieved 2026-08-01, oldid=44133) + verified against the Zandronum source's `src/g_strife/a_strifeweapons.cpp:172`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_AlertMonsters)` in the Zandronum source's `src/g_strife/a_strifeweapons.cpp:172`. Callable from any actor's state table despite the Strife-specific filename.

Alerts all monsters within a specified distance to a target actor. Commonly used on projectiles (via Death state) or monsters (via Pain state) to wake nearby enemies to pursue the same target. **Server-side only** — function returns immediately on clients without alerting anyone.

## Parameters

- **`maxdist`** (float, default `0`) — maximum distance from the caller at which monsters can be alerted, measured as 2D horizontal distance (vertical component ignored). A value of `0` means unlimited range; any non-zero value triggers a distance check via `P_AproxDistance(actor - emitter, maxdist)`. Note that the sound-alerting mechanism in `P_NoiseAlert` still propagates through connected sectors regardless of this distance; `maxdist` controls only which individual actors in those sectors get their `LastHeard` field updated.
- **`flags`** (int, default `0`) — Optional flags controlling target and emitter selection. Combine multiple flags with the `|` operator.

## Flags

- **`AMF_TARGETEMITTER`** (1) — Alerts monsters to chase the caller (emitter) itself, rather than the caller's current target. Only takes effect if the caller is alive and has the `SHOOTABLE` flag; otherwise no alert occurs.
- **`AMF_TARGETNONPLAYER`** (2) — If the caller has a non-player target, alerts other monsters to pursue that target. Without this flag, only player targets propagate the alert.
- **`AMF_EMITFROMTARGET`** (4) — The alert originates from the target actor's location, not the caller's. This affects distance checks and sector-traversal in the noise-alert system. If the target is NULL, the function does nothing (safe due to the `target != NULL && emitter != NULL` guard).

## Target selection

The function selects a target to alert other monsters about, using this precedence:

1. If the caller is a player, or `AMF_TARGETEMITTER` is set, the target is the **caller**.
2. Else, if the caller has a non-null target and either `AMF_TARGETNONPLAYER` is set or the target is a player, the target is the **caller's target**.
3. Otherwise, no target is selected and the function does nothing.

Note: The wiki's statement "does nothing on monsters which already have a target" is potentially misleading. The function operates based on whether the target *selection* succeeds (resulting in a non-null target); a caller that already has a target still alerts others if the target is a player or if `AMF_TARGETNONPLAYER` is set.

## Compatibility caveats

**`compat_soundtarget` mode:** If the `compat_soundtarget` compatibility flag is enabled, monsters use `Sector->SoundTarget` (the last actor that made noise in that sector) instead of the individual actor's `LastHeard` field. This affects which specific target a monster selects after being alerted, but does not bypass the `maxdist` distance check — the limiting effect of `maxdist` still applies.

## Return value

None.

## Example

```decorate
Projectile
// ...
States
{
Death:
  ZAP1 A 3 A_AlertMonsters
  ZAP1 BCDEFE 3
  ZAP1 DCB 2
  ZAP1 A 1
  Stop
}
```
