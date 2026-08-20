# `DamageFactor "<type>", <float>`

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Source-derived (no wiki page consulted) — verified against the Zandronum source's
`src/p_interaction.cpp` (`P_DamageMobj`, the order-of-operations around its `MF2_INVULNERABLE`
check and its `DamageFactor`/`DamageFactors` application).
**Bucket:** `DEFINE_PROPERTY(damagefactor, ZF, Actor)` in `src/thingdef/thingdef_properties.cpp`
(stores into the actor's `DamageFactor` field for the untyped/`"Normal"` case, or into its
per-type `DamageFactors` table for a named type). See
[Custom damage types](../concepts/custom-damage-types.md) for the general precedence chain this
property participates in; this note covers a narrower interaction that chain doesn't mention.

On Zandronum, `P_DamageMobj` (`src/p_interaction.cpp:1337-1343`) applies an actor's
`DamageFactor`/`DamageFactors` unconditionally, with no floor or magnitude check — this is true
even when the incoming `damage` value is `TELEFRAG_DAMAGE` (the sentinel used for instant-kill
effects: telefragging, `A_Die`, forced falling-damage kills, etc.). A `DamageFactor "<type>", 0`
entry (or a `Factor 0` on the matching global `DamageType` block, if the actor has no more
specific override) genuinely zeroes out an incoming `TELEFRAG_DAMAGE` hit of that type, the same
way it zeroes any smaller hit — there is no special case anywhere in Zandronum's `P_DamageMobj`
that exempts telefrag-magnitude damage from the multiply. The `DamageFactor` property genuinely
exists on UZDoom too, registered the same way in that engine's own copy of the property table
(`src/scripting/thingdef_properties.cpp`), but behaves differently at telefrag magnitude — see the
divergence section below.

## Contrast with `+INVULNERABLE` (Zandronum)

This is the opposite of how `+INVULNERABLE` behaves in the same function. `P_DamageMobj`'s
`MF2_INVULNERABLE` check is explicitly gated on `damage < TELEFRAG_DAMAGE` — so a hit that carries
`TELEFRAG_DAMAGE` (or higher) bypasses `+INVULNERABLE` entirely and always applies, regardless of
the flag. `DamageFactor 0` has no such carve-out and blocks the damage unconditionally, including
at telefrag magnitude. A modder reaching for "make this actor immune to telefrag/instakill damage
of type X" wants `DamageFactor "<type>", 0`, not `+INVULNERABLE` — the flag alone does not achieve
that for this class of damage, **on Zandronum**. UZDoom does not share this contrast — see below.

Both checks run inside the same function and in this relative order on Zandronum: the
`+INVULNERABLE` gate runs first (near the top of `P_DamageMobj`, before pointer-based damage
modifiers), and `DamageFactor`/`DamageFactors` application runs later (after `PowerProtection`-style
[passive/active inventory damage modifiers](../classes/powerprotection.md), guarded only by the
caller-supplied `DMG_NO_FACTOR` flag — not by damage magnitude).

## Engine-family divergence: UZDoom exempts telefrag-magnitude damage from `DamageFactor` too, unless `+LAXTELEFRAGDMG`

UZDoom's damage pipeline (the internal `DamageMobj` helper backing `AActor.DamageMobj`,
`src/playsim/p_interaction.cpp:1080-1247`) derives a local telefrag-magnitude flag, set when the
incoming raw damage reaches `TELEFRAG_DAMAGE` or higher (`src/playsim/p_interaction.cpp:1087`).
Like Zandronum, it exempts a hit at that magnitude from the `MF2_INVULNERABLE` check
(`src/playsim/p_interaction.cpp:1128`) — that half of the picture agrees between engines. But
unlike Zandronum, UZDoom also wraps its entire chain of damage modifiers — difficulty scaling,
special-damage-type hooks, active source-side modifiers, passive target-side modifiers, and
`ApplyDamageFactor` itself (`src/playsim/p_interaction.cpp:1232-1235`) — in a single guard that
only runs that whole block when the hit isn't telefrag-magnitude, or the target carries the
`LAXTELEFRAGDMG` actor flag (`src/playsim/p_interaction.cpp:1174`). When a hit carries
`TELEFRAG_DAMAGE` or more and the target does not carry `+LAXTELEFRAGDMG`, that whole block —
including the `DamageFactor` multiply — is skipped outright, so `DamageFactor "<type>", 0` does
**not** block a telefrag-magnitude hit of that type by default on UZDoom, the opposite of
Zandronum's behavior described above.

`+LAXTELEFRAGDMG` (the `MF7_LAXTELEFRAGDMG` actor flag, whose purpose — allowing telefrag damage
to be reduced by the normal modifier chain instead of always applying in full — is stated directly
in its own declaring comment, `src/playsim/actor.h:380`) is a real DECORATE-settable flag on
UZDoom, registered on `AActor`'s `flags7` word (`src/scripting/thingdef_data.cpp:293`), with no
Zandronum counterpart at all — Zandronum's `P_DamageMobj` never gates its modifier chain on
telefrag magnitude, so there is nothing to opt into or out of there. A modder porting a
"`DamageFactor "Falling", 0` blocks the forced-falling-damage telefrag kill"-style mitigation from
Zandronum to UZDoom needs to also flag the actor `+LAXTELEFRAGDMG`, or the `DamageFactor` entry is
silently inert against that specific kill path on UZDoom. Practically, this also means UZDoom does
not have the Zandronum-specific "`+INVULNERABLE` bypassed at telefrag magnitude but `DamageFactor`
still applies" contrast at all — by default, both are bypassed together.

## See also

- [Custom damage types](../concepts/custom-damage-types.md) — the general `DamageFactor`
  precedence chain (per-type entry > global type default > untyped `"Normal"` fallback).
- [`PowerProtection`](../classes/powerprotection.md) — a different damage-reduction mechanism
  (inventory-based rather than a class property) that applies earlier in the same function and has
  its own magnitude-independent behavior.
- [Monster and player falling damage](../concepts/falling-damage.md) — the mechanism whose
  unconditional `TELEFRAG_DAMAGE` output makes this magnitude-independence practically relevant:
  `DamageFactor "Falling", 0` is a working mitigation for it on Zandronum (where `+INVULNERABLE`
  is not) — on UZDoom the actor also needs `+LAXTELEFRAGDMG` for the same mitigation to take
  effect, per the divergence section above.
