# Monster and player falling damage

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Source-derived (no wiki page consulted) — verified against the Zandronum source's
`src/p_mobj.cpp` (`P_MonsterFallingDamage`, `P_ZMovement`, `P_XYMovement`), `src/p_user.cpp`
(`P_FallingDamage`), `src/p_interaction.cpp` (`P_DamageMobj`'s server-only `Die()` call), `src/
g_level.h` (`LEVEL2_MONSTERFALLINGDAMAGE`), and `src/r_defs.h` (`SECF_NOFALLINGDAMAGE`).

Both engines compute falling damage for monsters and for players through two entirely separate
functions with different gates, different formulas, and — most importantly — different failure
behavior at high fall speed; this two-path structure is shared ZDoom-lineage code, verified
against both checkouts. Code that assumes the two paths behave alike (or that "no falling damage"
means the same thing for both) will be surprised by the monster path specifically. UZDoom has also
added two independent escape valves that change the monster path's practical behavior in ways
Zandronum's doesn't have — see the engine-family divergence sections below.

## Two unrelated code paths

- **`P_FallingDamage`** (`src/p_user.cpp`) — the player path. Gated on `dmflags`/`level.flags`
  (`DF_FORCE_FALLINGZD`/`DF_FORCE_FALLINGHX`/`DF_FORCE_FALLINGST`; damage is a no-op if none of the
  three bits is set), with three separate formulas (ZDoom-style, Hexen-style, and Strife-style)
  selected by whichever flag is active — a plain undercount in an earlier version of this file,
  which named only the first two; confirmed present and identical in structure on both engine
  checkouts. The ZDoom- and Hexen-style formulas each have their own "automatic death" threshold at
  extreme velocity (a `TELEFRAG_DAMAGE`, i.e. `1000000`-damage, hit), but the Hexen-style formula
  additionally applies a **no-death threshold**: below `velz < -39*FRACUNIT`, damage is clamped to
  `actor->health - 1`, i.e. a fall that would otherwise kill leaves the player alive at 1 HP
  instead, unless the fall was fast enough to bypass the clamp. The Strife-style formula has no
  automatic-death case at all — it's a straight linear scale of `vel`.
- **`P_MonsterFallingDamage`** (`src/p_mobj.cpp`) — the monster path, called from `P_ZMovement` for
  any actor with `MF3_ISMONSTER` landing at `velz < -23*FRACUNIT`. Gated on the **level flag**
  `LEVEL2_MONSTERFALLINGDAMAGE` (see "The MAPINFO gate" below) instead of `dmflags`. The function
  computes a velocity-scaled damage value (`((vel - 23*FRACUNIT) * 6) >> FRACBITS`) and a separate
  35-map-units/tic threshold for "automatic death" — but immediately afterward, on Zandronum,
  unconditionally overwrites both with `damage = TELEFRAG_DAMAGE;` before calling `P_DamageMobj`.
  On Zandronum the computed formula and threshold are dead code: every monster fall that clears the
  gate is a `TELEFRAG_DAMAGE` (1,000,000) hit, with no velocity scaling, no partial-damage case, and
  no no-death clamp of any kind. **This override is UZDoom-only optional** — see [Engine-family
  divergence: the monster path's TELEFRAG_DAMAGE override became
  optional](#engine-family-divergence-the-monster-paths-telefrag_damage-override-became-optional-on-uzdoom)
  below; the default (unset) behavior on UZDoom still matches Zandronum's.

Because the two paths don't share a formula or a gate, "falling damage is on for this map" means
something different depending on whether the faller is a monster or a player — a level author (or
mapinfo-key search) reasoning about one from the other's semantics will draw the wrong conclusion.

## The MAPINFO gate, and why it can't be cleared everywhere

`LEVEL2_MONSTERFALLINGDAMAGE` (`src/g_level.h`) is set/cleared by the MAPINFO map-definition keys
`monsterfallingdamage` / `nomonsterfallingdamage` (`src/g_mapinfo.cpp`). It is a load-time-only
level flag:

- **Not reachable from ACS, on either engine.** No `p_acs.cpp` function reads or writes
  `level.flags2`'s `LEVEL2_MONSTERFALLINGDAMAGE` bit (or `level.flags2` generically) on Zandronum
  or on UZDoom — there is no runtime lever for the level flag itself once a map has loaded, on
  either engine. UZDoom does add a *different*, per-actor lever with no Zandronum equivalent at
  all — see the engine-family divergence section below.
- **Cannot be retracted from an IWAD map declared the Hexen way.** See [Map block definitions and
  inheritance](../../mapinfo/concepts/map-block-and-inheritance.md#monster-falling-damage-and-the-hexenhack-retraction-gap)
  for the `ParseMapHeader`/`HexenHack` mechanism that forces this flag back on for any map header
  declared with a bare numeric map name, regardless of what a `defaultmap`/`gamedefaults` override
  set beforehand — including hexen.wad's own IWAD map declarations, which use exactly that form.
- **Can be set going forward on a PWAD's own new map declarations**, as long as those declarations
  use a named map lump (`map map01 "..."`) rather than a bare number (`map 1 "..."`) — the latter
  form is what triggers the retraction-defeating `HexenHack` path in the first place.

## A per-sector escape exists, but it's map-format-only

Both falling-damage functions also check `floorsector->Flags & SECF_NOFALLINGDAMAGE`
(`src/r_defs.h`) before doing anything else, and return immediately if it's set — this applies
independently of the `LEVEL2_MONSTERFALLINGDAMAGE` level flag, per landing sector rather than per
map. It's set via a UDMF sector property (`p_udmf.cpp`'s `nofallingdamage` key) at map-compile
time; nothing in `src/p_acs.cpp` sets or clears this sector flag bit at runtime either, so like the
level flag, it's a mapper-time lever, not an ACS-reachable one. It's a viable mitigation only for
sectors a map author controls directly (e.g. re-exporting/patching a map's own sector data), not
for suppressing the effect on arbitrary IWAD geometry from a PWAD.

## `DamageFactor` is a working mitigation on Zandronum; `+INVULNERABLE` is not, on either engine

On Zandronum, since the monster path's output is always exactly `TELEFRAG_DAMAGE`, and
`P_DamageMobj` applies `DamageFactor`/`DamageFactors` with no magnitude floor (see
[`DamageFactor`](../notes/damagefactor.md) — that note's own magnitude-independence claim was
verified only against Zandronum, see the divergence note below), `DamageFactor "Falling", 0` on the
monster's own class genuinely blocks the kill on Zandronum — `P_MonsterFallingDamage` always tags
its `P_DamageMobj` call with `NAME_Falling` as the damage type, and `Falling` is one of Zandronum's
predefined damage types (see [Custom damage types](custom-damage-types.md)). **On UZDoom this
mitigation is conditional, not unconditional** — see [Engine-family divergence: `DamageFactor` no
longer unconditionally blocks TELEFRAG_DAMAGE-magnitude
damage](#engine-family-divergence-damagefactor-no-longer-unconditionally-blocks-telefrag_damage-magnitude-damage-on-uzdoom)
below. `+INVULNERABLE`, by contrast, does **not** work as a mitigation on either engine:
`P_DamageMobj`'s invulnerability check is gated on `damage < TELEFRAG_DAMAGE` on both Zandronum and
UZDoom, so a `TELEFRAG_DAMAGE`-magnitude hit bypasses it unconditionally regardless of engine — this
part of the contrast is unaffected by the `DamageFactor` divergence below. See
[`DamageFactor`](../notes/damagefactor.md) for the full Zandronum-side contrast.

`MaxDropOffHeight` is **not** a mitigation for the momentum-driven case of this — see
[`MaxDropOffHeight`](../notes/maxdropoffheight.md) for why knockback/explosion-driven falls skip
its check entirely regardless of its configured value.

## Zandronum-specific: server-authoritative death resolution

`P_DamageMobj` runs on both server and client (there is no blanket client-mode early-out at the
top of the function), so a client's local copy of a falling monster's `health` field is decremented
by the same computation the server performs. The actual death transition is not, however: `AActor
::Die()` is only invoked when `NETWORK_InClientMode() == false` (`src/p_interaction.cpp`, "Deaths
are server side"), so a client never independently decides a monster died from a fall — it computes
a (possibly momentarily wrong) local `health` value, and the server's own resolution and broadcast
own the actual life/death outcome and correct the client's state. This generalizes past falling
damage specifically: any client-side damage modifier that could differ from what the server
computes (for example, if a client's local view of a monster's active inventory/powerup state lags
the server's) changes the client's locally-computed health delta, not the actor's authoritative
fate — the server recomputes independently and the client's copy resolves to match. This part of
the netcode model is spot-checked, not exhaustively traced across every inventory-replication code
path; treat the general claim as plausible but not verified to the same depth as the `Die()` gate
itself.

This entire section is Zandronum-specific: UZDoom has no `NETWORK_InClientMode()` function, no
server/client mode split of this kind, and no equivalent gate on its own `Die()` call — it's
Zandronum's own server-authoritative netcode architecture layered on top of shared ZDoom-lineage
damage code, not a GZDoom-family concept that carries over.

## Engine-family divergence: the monster path's TELEFRAG_DAMAGE override became optional on UZDoom

UZDoom added two independent additions to `P_MonsterFallingDamage` (`src/playsim/p_mobj.cpp`) that
have no Zandronum equivalent — neither symbol exists anywhere in the Zandronum source tree:

- **A second, per-actor gate.** The function's initial early-return now also checks the actor flag
  `MF8_FALLDAMAGE` (`src/playsim/actor.h:408`, exposed to DECORATE/ZScript as the flag name
  `FALLDAMAGE`, `src/scripting/thingdef_data.cpp:313`) — the function runs if *either* the level
  flag `LEVEL2_MONSTERFALLINGDAMAGE` *or* this per-actor flag is set (`p_mobj.cpp:2914`). This only
  widens the initial gate (whether the function runs at all); it does not by itself change the
  TELEFRAG_DAMAGE override discussed next. Unlike the level flag, this per-actor flag genuinely is
  ACS-reachable: the `SetActorFlag` extension function (`ACSF_SetActorFlag`, `src/playsim/
  p_acs.cpp:6657`) can set or clear any named actor flag by string, `FALLDAMAGE` included, on a
  live actor — a per-actor runtime lever Zandronum has no equivalent of at all, on top of the level
  flag remaining equally unreachable from ACS on both engines (see "The MAPINFO gate" above).
- **An opt-out from the TELEFRAG_DAMAGE override.** A new level flag, `LEVEL3_PROPERMONSTERFALLINGDAMAGE`
  (`src/gamedata/g_mapinfo.h:248`, set via the MAPINFO key `propermonsterfallingdamage`,
  `src/gamedata/g_mapinfo.cpp:1888`), gates whether the TELEFRAG_DAMAGE override still fires
  (`p_mobj.cpp:2928`). When this flag is *not* set — the default, and the only state Zandronum's
  equivalent code has ever had — the override behaves exactly as described above: the computed
  velocity-scaled formula and 35-unit/tic threshold are dead code, and every monster fall that
  clears the gate is a `TELEFRAG_DAMAGE` hit. When a map sets `propermonsterfallingdamage`, the
  override is skipped entirely and the computed formula/threshold become the actual, live damage
  output — velocity-scaled, partial-damage falls become possible for monsters on that map, which
  Zandronum cannot produce under any MAPINFO configuration.

Net effect: on both engines, an unmodified map with no `propermonsterfallingdamage` key behaves
identically (TELEFRAG_DAMAGE-only monster falls). A UZDoom map or mod that opts into either
addition diverges from anything achievable on Zandronum.

## Engine-family divergence: `DamageFactor` no longer unconditionally blocks TELEFRAG_DAMAGE-magnitude damage on UZDoom

On UZDoom, the internal `DamageMobj` function that `P_DamageMobj` (`src/playsim/p_interaction.cpp`)
delegates to wraps its entire special-damage-checks block — active/passive damage modifiers,
`DamageMultiply`, and the `ApplyDamageFactor` call (`p_interaction.cpp:1234`) among them — in a
condition that is false whenever the incoming damage is TELEFRAG_DAMAGE-magnitude, *unless* the
target actor carries a new flag, `MF7_LAXTELEFRAGDMG` (exposed to DECORATE/ZScript as
`LAXTELEFRAGDMG`, `src/scripting/thingdef_data.cpp:293`). This flag and this gate have no
Zandronum equivalent: Zandronum's own `DamageFactor` application (verified in its `p_interaction.cpp`,
around its `target->DamageFactor`/`ApplyMobjDamageFactor` calls) has no TELEFRAG_DAMAGE carve-out
at all, which is exactly the claim [`DamageFactor`](../notes/damagefactor.md) makes and that claim
holds for Zandronum.

`P_MonsterFallingDamage` calls `P_DamageMobj` with the function's default `flags` value (no
`DMG_FORCED`, no `DMG_NO_FACTOR`), so on UZDoom, a monster that does *not* carry `+LAXTELEFRAGDMG`
has its `DamageFactor`/`DamageFactors` skipped entirely for a TELEFRAG_DAMAGE-magnitude falling-
damage hit — meaning `DamageFactor "Falling", 0` does **not** block the kill by default on UZDoom,
the opposite of Zandronum's behavior. On UZDoom the mitigation described above only works if either
(a) the monster's class also carries `+LAXTELEFRAGDMG`, or (b) the map opts into
`propermonsterfallingdamage` (previous section) so the damage magnitude isn't TELEFRAG_DAMAGE to
begin with.

This directly contradicts [`DamageFactor`](../notes/damagefactor.md)'s own claim that "there is no
special case anywhere in `P_DamageMobj` that exempts telefrag-magnitude damage from the multiply" —
that note was verified only against Zandronum and its claim does not hold on UZDoom
(`p_interaction.cpp:1174`'s `telefragDamage`/`MF7_LAXTELEFRAGDMG` check is exactly such a special
case). That file is out of this file's edit scope; flagging here for a follow-up correction to it.

The `+INVULNERABLE` check (`p_interaction.cpp:1128`) sits outside this gated block and runs
unconditionally on both engines, so the "`+INVULNERABLE` doesn't help" half of the contrast above is
unaffected by this divergence.

## See also

- [`DamageFactor`](../notes/damagefactor.md) — why it, and not `+INVULNERABLE`, blocks
  `TELEFRAG_DAMAGE`-magnitude damage on Zandronum (see this file's UZDoom divergence section above
  for why that doesn't carry over unconditionally).
- [`MaxDropOffHeight`](../notes/maxdropoffheight.md) — a property that sounds related but only
  prevents monsters from voluntarily walking off ledges, not from falling due to knockback.
- [Map block definitions and inheritance](../../mapinfo/concepts/map-block-and-inheritance.md) —
  the `monsterfallingdamage`/`nomonsterfallingdamage` MAPINFO keys and the `HexenHack` retraction
  gap.
- [Custom damage types](custom-damage-types.md) — `Falling` as a predefined damage type.
