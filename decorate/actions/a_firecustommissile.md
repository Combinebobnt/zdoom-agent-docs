# `void A_FireCustomMissile(class<Actor> missiletype, angle angle = 0, bool useammo = true, int spawnofs_xy = 0, fixed spawnheight = 0, bool aimatangle = false, angle pitch = 0)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_FireCustomMissile` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_FireCustomMissile&oldid=45025) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:1739–1814`, its helper `A_FireCustomMissileHelper` (`thingdef_codeptr.cpp:1703-1737`), the DECORATE declaration `wadsrc/static/actors/shared/inventory.txt:13`, `P_SpawnPlayerMissile` (`src/p_mobj.cpp:7444-7566`) and the spectral damage check (`src/p_interaction.cpp:1275-1286`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_FireCustomMissile)` in `src/thingdef/thingdef_codeptr.cpp`; declared for DECORATE on `Inventory` (`wadsrc/static/actors/shared/inventory.txt:13`), so only `Inventory`-derived classes can call it.

Fires a projectile from a player's weapon or a CustomInventory. **This action is player-only.** It silently does nothing when the actor running it (the item's owner) is not a player. **Fork divergence note:** This page describes the ZDoom Wiki, which documents GZDoom/UZDoom. Zandronum's signature and behavior differ significantly from the wiki: the sixth parameter is a single boolean (`aimatangle`), not a flags field. The wiki's `FPF_*` constant names do not exist in Zandronum; writing one is an unknown-identifier error that aborts startup. A bare integer is accepted and read as the boolean, so any nonzero value means `aimatangle = true`. The wiki also describes a deprecation warning (recommending `A_FireProjectile`); this warning is GZDoom-family only and does not apply to Zandronum, where `A_FireCustomMissile` is the standard weapon-variant projectile action.

## Parameters

- **missiletype** — The class name of the projectile to fire (required).
- **angle** — Adjusts horizontal aiming. Behavior depends on `aimatangle` (see "Aiming behavior" below). Positive turns left (counterclockwise). Default is `0`.
- **useammo** — If true and the player has a ready weapon, deducts that weapon's ammo cost before firing. If there isn't enough ammo, the action returns without firing. Default is `true`.
- **spawnofs_xy** — Moves the projectile spawn point perpendicular to the actor's facing angle, in the plane parallel to the ground. Positive values offset to the right, negative to the left. Zandronum interprets this as an integer. Default is `0`.
- **spawnheight** — Raises the projectile spawn point vertically, in map units, relative to the normal player-missile spawn height. Default is `0`.
- **aimatangle** — Affects how the `angle` parameter is used when aiming. See "Aiming behavior" below. Default is `false`.
- **pitch** — Vertical aiming adjustment, applied to the player's pitch only for the duration of the shot. Positive values aim upward, negative values aim downward. On Zandronum, an autoaim lock on a target replaces the vertical aim with the slope to that target, and with freelook disallowed and no target found the missile flies level. A weapon with `WEAPON.NOAUTOAIM` uses the adjusted pitch directly. Default is `0`.

## Aiming behavior

The `aimatangle` parameter controls how the `angle` parameter is applied:

- **`aimatangle = false` (default)** — The player aims a projectile toward their target (with autoaim if enabled). The `angle` parameter offsets the projectile's final trajectory angle. Internally, the missile is spawned with its calculated aim, then the velocity vector is rotated by the `angle` offset (preserving speed while changing direction).
- **`aimatangle = true`** — The `angle` parameter is added directly to the actor's facing angle before spawning the projectile. Autoaim still runs, searching around that shifted direction.

## Return value

None.

## Behavior notes

- **Player-only requirement:** The action checks `if (!self->player) return;` at entry. In weapon states `self` is the player holding the weapon, so it fires normally there. When a CustomInventory chain runs on a non-player owner (e.g. an item given to a monster), the action silently does nothing. Calling it from a non-Inventory actor's own states is a parse error on Zandronum ("Invalid state parameter").
- **Ammo depletion:** When `useammo` is true and the actor has a ready weapon, `DepleteAmmo(weapon->bAltFire, true)` is called. If this returns false (ammo exhausted), the action returns without firing. If `useammo` is false, ammo is never checked regardless of weapon state.
- **No ready weapon:** The ammo check is skipped when `player->ReadyWeapon` is null, so the projectile still fires, just without deducting anything.
- **Network handling:** After the ammo check, the action calls `NETWORK_ShouldActorNotBeSpawned()`. A client skips the spawn unless the spawner or the projectile type is `NETFL_CLIENTSIDEONLY`, and the server skips it when either one is. A null projectile class also stops here. Note that ammo was already deducted by then. On the server, each spawned projectile is sent with `SERVERCOMMANDS_SpawnMissileExact()` after its angle and velocity are final. A projectile that explodes on spawn is sent by `P_SpawnPlayerMissile` itself instead.
- **Spread rune:** If the player has the `CF2_SPREAD` flag set (granted by the Spread rune powerup, `PowerSpread`), three projectiles fire instead of one: the primary at `shootangle`, and two additional projectiles at ±15° (ANGLE_45 / 3) offsets. All three use the same aiming logic.
- **Spectral (friendly) missiles:** If the spawned projectile has `MF4_SPECTRAL` set, `P_SpawnPlayerMissile` records the firing player via `SetFriendPlayer`. The damage code checks that, so the missile does not hurt players outside deathmatch. The helper also sets the missile's `health` to `-1`; no reader of that value was found in the damage code.
- **Homing missiles:** If the spawned projectile has `MF2_SEEKERMISSILE` set, its `tracer` field is automatically populated with the autoaimed target actor (if any).

## Examples

```text
ACTOR MyLauncher : Weapon
{
    Weapon.AmmoType "RocketAmmo"
    Weapon.AmmoUse 1
    Weapon.AmmoGive 10
    States
    {
    Ready:
        MISG A 1 A_WeaponReady
        Loop
    Deselect:
        MISG A 1 A_Lower
        Loop
    Select:
        MISG A 1 A_Raise
        Loop
    Fire:
        // useammo defaults to true, so this deducts Weapon.AmmoUse
        MISG B 8 A_FireCustomMissile("Rocket")
        MISG B 12 A_ReFire
        Goto Ready
    AltFire:
        // No ammo cost, 16 units higher, aimed upward by 5 degrees
        MISG B 0 A_FireCustomMissile("Rocket", 0, false, 0, 16, false, 5)
        // No ammo cost, velocity turned 15 degrees left after aiming
        MISG B 8 A_FireCustomMissile("Rocket", 15, false, 0, 0, false)
        Goto Ready
    }
}
```

## Engine-family divergence: deprecated compatibility wrapper and flags-based signature

In UZDoom, `A_FireCustomMissile` (`wadsrc/static/zscript/compatibility.zs`) is a `deprecated("2.3", "Use A_FireProjectile() instead")` compatibility function, not a native action in its own right. It forwards directly to `A_FireProjectile(missiletype, angle, useammo, spawnofs_xy, spawnheight, flags, -pitch)`. Its actual declared signature takes `int flags = 0` (enum `EFireCustomMissileFlags`: `FPF_AIMATANGLE = 1`, `FPF_TRANSFERTRANSLATION = 2`, `FPF_NOAUTOAIM = 4`) rather than Zandronum's single `bool aimatangle` — confirming, from direct verification of the UZDoom source rather than the wiki page alone, the existing "Fork divergence note" above. `useammo` defaults to `true` on both engines. UZDoom's ammo-depletion check additionally requires the call to come from an actual weapon pspr state (`stateinfo.mStateType == STATE_Psprite`) in addition to `weapon` being non-null; Zandronum's check (documented in "Ammo depletion" above) only requires a ready weapon.

## Engine-family divergence: no client/server split, no spread rune

UZDoom has no client/server authority split anywhere in its source tree (no `NETWORK_InClientMode`/`SERVERCOMMANDS_*`-style construct exists at all) — the "Network handling" behavior note above (`NETWORK_ShouldActorNotBeSpawned()` gate, `SERVERCOMMANDS_SpawnMissileExact()` broadcast) is Zandronum-only; on UZDoom the call goes straight through `A_FireProjectile` to the native `P_SpawnPlayerMissile` with no server-authoritative branch to trace. UZDoom also has no `CF2_SPREAD` flag handling anywhere in its source — the "Spread rune" behavior note above is likewise Zandronum-only, so exactly one projectile fires per call regardless of player cheats. Spectral-missile handling works the same way on both engines: each engine's `P_SpawnPlayerMissile` calls `SetFriendPlayer` on `MF4_SPECTRAL` missiles. Zandronum's `A_FireCustomMissileHelper` additionally sets `health = -1` on them, an extra assignment UZDoom lacks.

## See also

- [A_CustomMissile](a_custommissile.md) — monster-variant projectile action for non-player actors.
- [Creating weapons](../concepts/creating-weapons.md) — weapon state names and firing-state semantics.
- [Creating projectiles](../concepts/creating-projectiles.md) — projectile flags and state requirements.
