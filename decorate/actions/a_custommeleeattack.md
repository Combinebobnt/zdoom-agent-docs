# `void A_CustomMeleeAttack(int damage = 0, sound meleesound = "", sound misssound = "", name damagetype = "none", bool bleed = true)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `A_CustomMeleeAttack` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_CustomMeleeAttack&oldid=54194) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:1380–1409`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Action function, defined on `AActor` (callable from any actor's state table).

A customizable melee attack for monsters. Calls `A_FaceTarget` and checks if the caller's target is within melee range. If in range, deals damage and plays the `meleesound`; if out of range, plays the `misssound` instead. Does nothing if there is no current target.

## Zandronum-specific: server-side execution gate

On a Zandronum client, this action returns immediately unless the calling actor has the `+CLIENTSIDEONLY` flag — the entire attack (facing the target, range check, damage, sound) is server-side only. This is a Zandronum-specific netcode gate; the ZDoom wiki, describing upstream behavior, makes no mention of this restriction.

## Engine-family divergence: no client-mode execution gate

UZDoom's `A_CustomMeleeAttack` (`src/playsim/p_actionfunctions.cpp`, `DEFINE_ACTION_FUNCTION(AActor, A_CustomMeleeAttack)`) has no equivalent of Zandronum's client/`+CLIENTSIDEONLY` gate — the function body has no client/server branch at all, and no `NETWORK_InClientMode`/`SERVERCOMMANDS_*`-style check exists anywhere in the UZDoom source tree. The function runs to completion on every machine rather than being gated to a single authoritative side. Every other behavior described in this file (the `damage`/`meleesound`/`misssound`/`damagetype`/`bleed` parameters, the `"none"`-to-`"Melee"` damagetype fallback, and the bleeding fallback to the original `damage` value when `newdam` is `0`) matches UZDoom's implementation exactly.

## Parameters

- **damage** — Amount of damage to inflict. Accepts an expression. Default `0`.
- **meleesound** — Sound to play on a successful hit, played on the weapon channel (`CHAN_WEAPON`). Default empty string (no sound). In multiplayer, the server replicates this sound to clients.
- **misssound** — Sound to play when the attack misses (target out of range). Played on `CHAN_WEAPON`. Default empty string. Server-replicated in multiplayer.
- **damagetype** — Type of damage to deal. Takes a name constant or string. Default `"none"`, which is silently converted to `"Melee"` at entry — **you cannot deal `none`-typed damage with this action**. Any other type (e.g. `"Fire"`, `"Plasma"`) is passed through.
- **bleed** — If `true`, the target leaves blood decals on nearby walls after being hit. Default `true`. Only takes effect on a successful hit.

## Bleeding behavior

The `bleed` parameter calls `P_TraceBleed` with the actual damage inflicted (`newdam`). If the damage is absorbed entirely by resistances and `newdam` returns `0`, blood is still traced using the original `damage` value — a hit that deals no actual damage still produces blood decals.

## See also

- `A_CustomComboAttack` — extends this with an optional projectile fallback if the target is out of melee range.
- `A_CustomPunch` — a player weapon variant with casing/sound/alert mechanics.
