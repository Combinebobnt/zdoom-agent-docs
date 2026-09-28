# `A_JumpIfNoAmmo (state label)` / `A_JumpIfNoAmmo (int offset)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki `A_JumpIfNoAmmo` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_JumpIfNoAmmo&oldid=53829) + verified against Zandronum source's `src/thingdef/thingdef_codeptr.cpp:1472-1485` and `src/g_shared/a_weapons.cpp:630-701` (`AWeapon::CheckAmmo` implementation), plus `src/thingdef/thingdef_codeptr.cpp:695-753` (`DoJump`), `src/thingdef/thingdef.h:439` (`ACTION_CALL_FROM_WEAPON`) and `src/thingdef/thingdef_states.cpp:378-397` (integer offset parsing).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_JumpIfNoAmmo)` in `src/thingdef/thingdef_codeptr.cpp` — callable only from weapon states (verified via `ACTION_CALL_FROM_WEAPON()` guard).

Jumps to a target state (or forward by an offset) if the player carrying the weapon lacks sufficient ammunition for the current firing mode.

## Signatures

```decorate
state A_JumpIfNoAmmo(state "label")
state A_JumpIfNoAmmo(int offset)
```

The parameter can be either a state label (as a quoted string) or an integer frame offset — DECORATE resolves both forms via the parser.

## Parameters

| Parameter | Type | Meaning |
|-----------|------|---------|
| `label` or `offset` | state label or `int` | The target state label to jump to (if string), or a forward offset (if integer). An offset of N targets the state N positions after the calling state, so 1 is the next state. An offset of 0 means no jump, and a negative offset is a parse error. |

## Behavior

The function checks the ready weapon's ammunition sufficiency via `AWeapon::CheckAmmo()`, considering both the primary and alternate firing modes (determined by the weapon's `bAltFire` flag):

- **Jumps if ammunition is insufficient** for one attack of the current fire mode, as defined by the weapon's `AmmoUse1`/`AmmoUse2` properties.
- **Never jumps if infinite ammo is active** — either the `DF_INFINITE_AMMO` deathmatch flag or the player's `CF_INFINITEAMMO` cheat flag. The function always checks these conditions first via `CheckAmmo()`.
- **Weapon-optional-ammo caveat:** If the weapon has the `+WEAPON.AMMO_OPTIONAL` flag set on the current fire mode, `CheckAmmo` ordinarily returns `true` (fires without ammo). However, `A_JumpIfNoAmmo` passes `requireAmmo = true` to `CheckAmmo`, *overriding* that flag behavior — even an `AMMO_OPTIONAL` weapon will report "no ammo" and trigger the jump if its ammo is below that fire mode's `AmmoUse1`/`AmmoUse2`. This differs from `A_CheckReload`, which respects `AMMO_OPTIONAL`.
- **No automatic weapon switching** — unlike `A_CheckReload`, this function never auto-switches weapons; it only tests and jumps.

## Network synchronization

In Zandronum multiplayer, `A_JumpIfNoAmmo` **has no early-return network gate** — server and client each evaluate it against their own copy of the player's ammo. A jump it takes sends no state-change command to clients (`ACTION_JUMP` with no client-update flags), relying on clients already having ammo information (per the `// [BC] Clients have ammo information.` comment in the source). This is an exception to the server-authoritative pattern; most `A_JumpIf*` actions defer their decision to the server. See [`network-jump-synchronization.md`](../concepts/network-jump-synchronization.md) for the broader jump-function synchronization model.

## Zandronum-specific: network synchronization

UZDoom's implementation (`StateProvider::A_JumpIfNoAmmo` in `wadsrc/static/zscript/actors/inventory/stateprovider.zs`) has no client/server distinction at all: it evaluates `Weapon.CheckAmmo()` and jumps in one code path, with no network-authority branch. UZDoom's source tree has no client/server split mechanism analogous to Zandronum's anywhere (no `NETWORK_InClientMode`-style check, no `SERVERCOMMANDS_*`-style server-to-client sync commands exist at all). The "Network synchronization" section above, describing how Zandronum's server and client each evaluate the jump locally, is Zandronum-only and does not apply to UZDoom.

## Engine-family divergence: infinite ammo cheat check

UZDoom implements the player-side "infinite ammo" cheat differently from Zandronum's `CF_INFINITEAMMO` cheat-flag bit. `Weapon::CheckAmmo()` (`wadsrc/static/zscript/actors/inventory/weapons.zs`) instead checks `Owner.FindInventory('PowerInfiniteAmmo', true) != null` — whether the player currently owns a `PowerInfiniteAmmo` powerup item. UZDoom's `constants.zs` still declares a `CF_INFINITEAMMO` enum member, but its value is hardcoded to `0` with the comment "These flags no longer exist, but keep the names for some stray mod that might have used them" — it is a dead compatibility placeholder, not a functioning flag. The deathmatch-level `DF_INFINITE_AMMO` flag (exposed as the `sv_infiniteammo` cvar) is unchanged and still checked the same way as on Zandronum.

## Weapon-state-only guard

The function must be called from a weapon state — the `ACTION_CALL_FROM_WEAPON()` guard ensures `self->player` is not NULL. Calling it from a monster's state, a player pawn's own actor states, or a `CustomInventory` Pickup/Use chain returns without jumping.

## See also

- `A_CheckReload` — a related function that also tests ammo, but switches weapons if empty and respects `AMMO_OPTIONAL`.
- `A_JumpIfInventory` — conditionally jumps based on any inventory item's count, not just weapon ammo.
