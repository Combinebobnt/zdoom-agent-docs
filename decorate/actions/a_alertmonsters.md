# `A_AlertMonsters(float maxdist = 0, int flags = 0)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_AlertMonsters` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_AlertMonsters&oldid=44133) + verified against the Zandronum source's `src/g_strife/a_strifeweapons.cpp:172` and `src/p_enemy.cpp:132-234`. **Accuracy note (2026-08-02):** the `AMF_TARGETEMITTER` guard originally documented here (an "alive and SHOOTABLE" precondition) is not present in the Zandronum source and has been removed — see "Flags" below. **Accuracy note (2026-08-02, second pass):** the "Compatibility caveats" section previously claimed `maxdist` still applies under `compat_soundtarget`; re-verified against `p_enemy.cpp:143` vs `:149` and corrected — `maxdist` is bypassed entirely in that mode.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_AlertMonsters)` in the Zandronum source's `src/g_strife/a_strifeweapons.cpp:172`. Callable from any actor's state table despite the Strife-specific filename.

Alerts all monsters within a specified distance to a target actor. Commonly used on projectiles (via Death state) or monsters (via Pain state) to wake nearby enemies to pursue the same target. **Server-side only** — function returns immediately on clients without alerting anyone (`a_strifeweapons.cpp:182-185`).

## Engine-family divergence: network execution model

The "Server-side only" behavior above is specific to Zandronum's client/server netcode split. UZDoom has no equivalent concept for this function: its `A_AlertMonsters` (`wadsrc/static/zscript/actors/strife/strifefunctions.zs:182`) contains no client-mode guard, and the native code it calls into (`AActor::SoundAlert` → `P_NoiseAlert`/`NoiseMarkSector` in `src/playsim/p_enemy.cpp:120-243`) has no client/server branch either — the alert is not conditioned on network role at all in UZDoom.

The underlying algorithm otherwise matches: target selection, the `AMF_*` flags, and the `LastHeard`-vs-`Sector->SoundTarget` split under `compat_soundtarget` (`COMPATF_SOUNDTARGET` in UZDoom, including the `MF_NOSECTOR` disjunct present on both engines at `p_enemy.cpp:1969`/UZDoom's `:1940`) all behave the same way described below. One incidental signature difference: UZDoom declares `maxdist` as `double` rather than `float`; the practical effect is negligible.

## Engine-family divergence: `maxdist` distance check

Zandronum's per-actor gate uses `P_AproxDistance(actor->x - emitter->x, actor->y - emitter->y) <= maxdist` (`p_enemy.cpp:149`) — the classic octagonal distance approximation (`dx + dy - min(dx,dy)/2`), which overestimates true 2D distance by up to ~8% at 45°. UZDoom's equivalent gate uses `actor->Distance2D(emitter) <= maxdist` (`src/playsim/p_enemy.cpp:137`), an exact Euclidean 2D distance. Both still ignore the vertical component and both still gate only the per-actor `LastHeard` write (not the `Sector->SoundTarget` write, and not sector traversal) as described in "Compatibility caveats" below — but a monster near the `maxdist` boundary off-axis can be alerted under one engine's check and not the other's.

## Parameters

- **`maxdist`** (float, default `0`) — maximum distance from the **emitter** at which monsters can be alerted, measured as 2D horizontal distance (vertical component ignored). A value of `0` means unlimited range; any non-zero value triggers a distance check via `P_AproxDistance(actor - emitter, maxdist)` (`p_enemy.cpp:149`). Note that the sound-alerting mechanism in `P_NoiseAlert` still propagates through connected sectors regardless of this distance; `maxdist` controls only which individual actors in those sectors get their `LastHeard` field updated.
- **`flags`** (int, default `0`) — Optional flags controlling target and emitter selection. Combine multiple flags with the `|` operator.

## Flags

- **`AMF_TARGETEMITTER`** (1) — Alerts monsters to chase the caller (emitter) itself, rather than the caller's current target. No additional guard applies — the target is set unconditionally, regardless of the caller's flags or health/aliveness (`a_strifeweapons.cpp:187`).
- **`AMF_TARGETNONPLAYER`** (2) — If the caller has a non-player target, alerts other monsters to pursue that target. Without this flag, only player targets propagate the alert.
- **`AMF_EMITFROMTARGET`** (4) — The alert originates from the target actor's location, not the caller's. This affects distance checks and sector-traversal in the noise-alert system. If the target is NULL, the function does nothing (safe due to the `target != NULL && emitter != NULL` guard).

## Target selection

The function selects a target to alert other monsters about, using this precedence:

1. If the caller is a player, or `AMF_TARGETEMITTER` is set, the target is the **caller**.
2. Else, if the caller has a non-null target and either `AMF_TARGETNONPLAYER` is set or the target is a player, the target is the **caller's target**.
3. Otherwise, no target is selected and the function does nothing.

Note: The wiki's statement "does nothing on monsters which already have a target" is potentially misleading. The function operates based on whether the target *selection* succeeds (resulting in a non-null target); a caller that already has a target still alerts others if the target is a player or if `AMF_TARGETNONPLAYER` is set.

## Compatibility caveats

**Default path (`compat_soundtarget` disabled — the default):** each alerted monster's own `LastHeard` field is stamped with the noise target when `NoiseMarkSector` walks the sector's thinglist during the alert (`p_enemy.cpp:145-152`), and only then. `A_Look`/`A_LookEx` read `LastHeard` (`p_enemy.cpp:1968-1970`, `:2119-2120`) to decide whether to wake. Because the stamp is per-actor and written only at the moment the alert fires, it does **not** persist as sector state: a monster that enters the flooded sector afterward, or that isn't ticking `A_Look` at that instant, never sees it. Treat the alert as a one-shot snapshot under this (default) path, not a lingering "this room is alerted" flag.

**`compat_soundtarget` mode:** If enabled, monsters instead read `Sector->SoundTarget`, which is written unconditionally at `p_enemy.cpp:143` — *before*, and independently of, the `maxdist`-gated per-actor loop that follows. Because it's sector state rather than a per-actor stamp, a monster that enters the sector later still picks it up, unlike the default path. **This also means `maxdist` is bypassed entirely in this mode**, not merely unaffected: `maxdist` is checked only at `p_enemy.cpp:149`, which gates the per-actor `LastHeard` assignment — it has no bearing on the `Sector->SoundTarget` write at `:143` that compat mode actually reads. (A previous revision of this doc stated the `maxdist` limit "still applies" under `compat_soundtarget`; that was incorrect and has been corrected here.)

## Calling context

`self` in the codepointer body is always the logical actor executing the state, not necessarily the actor whose state table contains the call:

- **Weapon states:** `self` is the **player pawn**, not the weapon — `P_SetPsprite` invokes `state->CallAction(player->mo, player->ReadyWeapon)` (`p_pspr.cpp:257`). The `self->player != NULL` branch above is what makes this resolve to "alert monsters to the player" rather than to the weapon actor (which has no `player` field and would otherwise fall through to the `self->target`-based branches).
- **`CustomInventory` item states:** `self` is the **item's owner**, not the item — `ACustomInventory::CallStateChain` (`thingdef_codeptr.cpp:135`) invokes the state's action function with the owning actor, not the inventory item itself.

In both cases the function behaves correctly out of the box; there is no need to route through the caller's `target`/`tracer` to reach the player or owner.

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
