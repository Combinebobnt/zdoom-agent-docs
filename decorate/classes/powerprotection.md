# `PowerProtection`

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Source-derived (no wiki page consulted) — verified against the Zandronum source's
`src/g_shared/a_artifacts.h:209` (native C++ class `APowerProtection : public APowerup`) and
`src/g_shared/a_artifacts.cpp` (`APowerProtection::ModifyDamage`), plus `src/p_interaction.cpp`
(`P_DamageMobj`'s passive-modifier call site).
**Bucket:** `src/g_shared/a_artifacts.h:209` (native C++ class), implementation in
`src/g_shared/a_artifacts.cpp` — **corrected 2026-08-17: this class overrides three `Powerup`
lifecycle methods, not just `ModifyDamage`.** `InitEffect`/`EndEffect` (lines 1649/1674) handle a
flag-transfer half this file previously omitted entirely (see "Flag-transfer half" below);
`ModifyDamage` (line 1691) is the damage-reduction half this file otherwise documents. On
UZDoom/GZDoom-family engines the equivalent is the ZScript class `PowerProtection : Powerup` in
`wadsrc/static/zscript/actors/inventory/powerups.zs:1723` — same three-method split
(`InitEffect`/`EndEffect`/`ModifyDamage`), no native C++ override backing it.

A built-in [`Powerup`](powerup.md) subclass ("quarter damage") that reduces incoming damage
through the engine's passive damage-modifier mechanism, rather than through a state-machine effect.
**Correction:** an earlier version of this page also said "rather than... a flag transfer to its
owner" — that undersold the class. `PowerProtection` performs both: a damage-reduction mechanism
(`ModifyDamage`, covered below) *and* a direct flag transfer to its owner (`InitEffect`/`EndEffect`
— see "Flag-transfer half" below) — independent halves of the same class, not alternatives. It is
the DECORATE base class behind effects like a damage-resistance rune or armor-boosting powerup.

## Works on any actor with an inventory, not just players

`P_DamageMobj` calls `target->Inventory->ModifyDamage(olddam, mod, damage, true)` for **any**
target that has a non-null `Inventory` chain — this call site has no player-only check. Since
`APowerProtection::ModifyDamage` itself also has no player-only check (its condition is simply
`passive && damage > 0`), a `PowerProtection` instance held by a monster or other non-player actor
(e.g. granted via `A_GiveInventory` in that actor's own state machine, or by a script) applies its
damage reduction exactly the same way it would for a player. Nothing in this class assumes an
owning `PlayerPawn`.

Clean agreement: UZDoom's equivalent call site is `AActor::GetModifiedDamage`
(`src/playsim/p_mobj.cpp:8684`), invoked from `P_DamageMobj` (`src/playsim/p_interaction.cpp:1230`)
on the target actor for the passive/target-side pass, with the damage type, running damage value,
and a passive-mode flag passed through. Same property: no player-only check at either the call site
or inside `PowerProtection::ModifyDamage` (`wadsrc/static/zscript/actors/inventory/powerups.zs:1801`,
which only requires the passive-mode flag to be set and the incoming damage to be positive).
Mechanically it iterates rather than recursively chains (see "Stacking and ordering" below), but the
"works for any actor with an inventory" conclusion holds identically on both engines.

## The empty-`DamageFactors`-table trap

`ModifyDamage`'s reduction factor is resolved like this:

1. If the class has a non-empty `DamageFactors` table (i.e. it declares at least one
   `DamageFactor "<type>", <value>` entry), look up the incoming damage type in that table.
   - If a specific entry matches, use it.
   - If no specific entry matches but the class declared an untyped `DamageFactor` fallback (`""`
     / `"Normal"`), use that instead.
   - If neither exists, **no reduction is applied at all** for this hit — the class's own
     `DamageFactors` table takes over damage reduction entirely once it's non-empty, and an
     uncovered damage type passes through at full strength.
2. If the class has **no** `DamageFactor` entries declared anywhere (`DamageFactors` is null or
   empty), a hardcoded default factor of `FRACUNIT/4` (**0.25**) is used instead, applied to
   **every** damage type unconditionally.

The trap: a modder who subclasses `PowerProtection` expecting an inert base ("I'll add
`DamageFactor` entries for the types I care about, everything else stays full damage") gets the
opposite of what they'd expect either way. Declaring **zero** `DamageFactor` entries silently
grants a **blanket 25%-damage effect against every damage type** — not "no protection," as an
empty-config-means-off assumption would suggest. Declaring **some** `DamageFactor` entries then
switches to a wholly different mode where uncovered types get **no protection at all** (not even
the 0.25 default) — the two behaviors don't blend or fall back into each other.

Clean agreement: UZDoom implements this identical two-branch logic through a shared native helper —
`AActor::ApplyDamageFactors` (`src/scripting/vmthunks_actors.cpp:721`), which `PowerProtection`'s
`ModifyDamage` calls with the item's own class, the damage type, the running damage value, and a
quarter of that damage value as the caller-supplied default. That helper returns the class's own
`DmgFactors::Apply` result when the table is non-empty (falling back to the untyped/`"Normal"` entry,
or passing the full `damage` through unmodified if neither a specific nor untyped entry matches —
`src/gamedata/info.cpp:789`), or the caller-supplied default (the same 25%) when the table is empty.
Same trap, same two behaviors, on both engines — this is a shared native mechanism, not a per-fork
reimplementation.

On Zandronum, this reduction is applied unconditionally by damage magnitude — it is not skipped for
telefrag/instant-kill-magnitude damage the way `+INVULNERABLE` is. **This does not hold on UZDoom by
default** — see "Engine-family divergence: telefrag-magnitude damage" below. See
[`DamageFactor`](../notes/damagefactor.md) for the parallel behavior on the `DamageFactor` actor
property itself (a different mechanism — a class property rather than an inventory item — but on
Zandronum the same `TELEFRAG_DAMAGE`-is-not-special rule applies to both, since both ultimately
multiply the `damage` value inside `P_DamageMobj` with no magnitude floor; that page is Zandronum-
only and its claim should be read as such, not assumed to hold on UZDoom).

## Stacking and ordering

On Zandronum, `ModifyDamage` chains to the next item in the actor's inventory
(`Inventory->ModifyDamage(...)` at the end of the override), so multiple `PowerProtection`-derived
items held by the same actor multiply together rather than the first one encountered winning
exclusively. Passive modifiers (`PowerProtection`) run after active/attacker-side modifiers (e.g.
`PowerDamage`) in `P_DamageMobj`, and both run before `DamageFactor`/`DamageFactors` property
application — see [`DamageFactor`](../notes/damagefactor.md)'s ordering note (Zandronum-scoped, see
the caveat above).

Clean agreement on the observable result, different mechanism: UZDoom doesn't chain through the
override itself — `PowerProtection::ModifyDamage` neither calls `Super` nor touches the next
inventory item — instead `AActor::GetModifiedDamage` (`src/playsim/p_mobj.cpp:8684`) loops over the
actor's whole inventory chain natively, calling each item's `ModifyDamage` virtual in turn and
threading the running `damage` value through the loop. The net effect is identical: multiple
`PowerProtection`-derived items still multiply together. The relative ordering also agrees:
`P_DamageMobj` (`src/playsim/p_interaction.cpp:1224,1230,1234`) calls the active/attacker-side pass
first, the passive pass (`PowerProtection`) second, then `AActor::ApplyDamageFactor`
(`src/playsim/p_mobj.cpp:8700`, the `DamageFactor`/`DamageFactors` property) last — same three-stage
order as Zandronum.

## Engine-family divergence: telefrag-magnitude damage

On Zandronum, `PowerProtection`'s passive `ModifyDamage` call (`target->Inventory->ModifyDamage(...)`
in `P_DamageMobj`, `src/p_interaction.cpp:1310-1314`) is gated only by `target->Inventory != NULL` —
there is no `damage < TELEFRAG_DAMAGE` check anywhere around it, unlike the `MF2_INVULNERABLE` check
a few lines earlier in the same function, which explicitly requires `damage < TELEFRAG_DAMAGE`
(`src/p_interaction.cpp:1212`) to apply. So on Zandronum, `PowerProtection` (and `DamageFactor`,
similarly ungated at `src/p_interaction.cpp:1337`) reduces telefrag-magnitude damage exactly the
same as any other hit.

**UZDoom does not agree.** `P_DamageMobj` (`src/playsim/p_interaction.cpp`) computes a local boolean
near the top of the function (line 1087) recording whether the raw incoming damage is at or above
`TELEFRAG_DAMAGE`, then wraps the *entire* block containing both the active/passive
`GetModifiedDamage` calls and `ApplyDamageFactor` in a condition (line 1174) that skips that whole
block whenever that boolean is true, unless the target actor also has `MF7_LAXTELEFRAGDMG` set.
By default (no `MF7_LAXTELEFRAGDMG` on the target — a flag Zandronum has no equivalent of; its own
`flags7` table defines unrelated telefrag-triggering flags like `MF7_NOTELESTOMP`/
`MF7_ALWAYSTELEFRAG`, not a damage-magnitude gate), a telefrag-magnitude hit skips
`PowerProtection::ModifyDamage` — and `DamageFactor`/`DamageFactors` — entirely, the same way
`MF2_INVULNERABLE` is skipped on both engines. A `PowerProtection` (or `DamageFactor "<type>", 0`)
that would block a hit of that magnitude on Zandronum does **not** block it on UZDoom by default;
the target actor needs `MF7_LAXTELEFRAGDMG` set for UZDoom's behavior to match Zandronum's here.

This is a genuine cross-engine behavioral difference, not just a documentation gap: the Zandronum-
only [`DamageFactor`](../notes/damagefactor.md) page's claim that its property "applies
unconditionally, with no floor or magnitude check... even when the incoming damage value is
`TELEFRAG_DAMAGE`" is correct as a Zandronum-scoped claim, but does not generalize to UZDoom.

## Flag-transfer half (`InitEffect`/`EndEffect`)

Previously undocumented on this page: `PowerProtection` does more than reduce damage via
`ModifyDamage`. On `InitEffect`, it transfers a fixed set of protection-related actor flags from
itself onto its `Owner` — but only for flags the owner doesn't already have set (and clears them
from itself once transferred, so `EndEffect` only reverts what it granted, not pre-existing owner
flags); `EndEffect` reverses the transfer. This is identical in *effect* on both engines, expressed
through each engine's own flag-storage convention:

- Zandronum (`src/g_shared/a_artifacts.cpp:1649-1683`, native `flags3`/`flags5` bitmasks): transfers
  `MF3_NORADIUSDMG`, `MF3_DONTMORPH`, `MF3_DONTSQUASH`, `MF3_DONTBLAST`, `MF3_NOTELEOTHER` (the
  `PROTECTION_FLAGS3` bundle) and `MF5_NOPAIN`, `MF5_DONTRIP` (`PROTECTION_FLAGS5`).
- UZDoom (`wadsrc/static/zscript/actors/inventory/powerups.zs:1736-1793`, named ZScript bool
  properties): transfers the same seven flags by their ZScript names —
  `bNoRadiusDmg`, `bDontMorph`, `bDontSquash`, `bDontBlast`, `bNoTeleOther`, `bNoPain`, `bDontRip`.

Same seven flags, same transfer-if-owner-lacks-it / revert-on-end semantics, on both engines — clean
agreement, not a divergence (see the intro correction above for why this page previously omitted
this half entirely).

## See also

- [`Powerup`](powerup.md) — the base class `PowerProtection` inherits from; this page covers what
  `PowerProtection` itself overrides (`InitEffect`/`EndEffect`/`ModifyDamage`), not the shared
  activation/timing lifecycle, which is unmodified from `Powerup`.
- [`DamageFactor`](../notes/damagefactor.md) — the property-level equivalent of "reduce damage,"
  Zandronum-scoped; see "Engine-family divergence: telefrag-magnitude damage" above for why its
  "including at telefrag magnitude" claim does not carry over to UZDoom unmodified.
