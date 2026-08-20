# `int DamageThing(int amount [, int mod])`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `DamageThing - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`https://zdoom.org/w/index.php?title=DamageThing&oldid=49026`) + source-verified (`p_lnspec.cpp:1123-1152`, `p_interaction.cpp:1152-1230,1515-1596,
1586`, `MODtoDamageType` `p_lnspec.cpp:97-119`) for behavior including TELEFRAG_DAMAGE invulnerability
bypass, attacker-null implications, healing non-replication, and sparse MOD mapping.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** action special.

Damages, heals, or guarantees a kill on the actor that activated the script. Action special (positive
index 73 in `zcommon.bcs`'s `special` table), semantics in the Zandronum source's `src/p_lnspec.cpp`,
`FUNC(LS_DamageThing)` (line 1123), which delegates damage calculation to `P_DamageMobj`.

**Activator-only:** operates on the activator exclusively. **No TID parameter.** If called from a
script with no activator (e.g., `OPEN`/`ENTER`/`RESPAWN`/`DISCONNECT`), returns `false`/`0` and
does nothing.

- `amount` — damage amount or healing amount.
  - **Positive** (`amount > 0`): deals `amount` hitpoints of damage via `P_DamageMobj(target, NULL,
    NULL, amount, mod_type)`. Source and inflictor are both NULL, so **no attacker is recorded**:
    no frag credit, no `target` assignment on the damaged actor, no infighting retaliation. For
    players, armor may absorb some damage.
  - **Negative** (`amount < 0`): heals by `-amount` hitpoints.
    - **Players:** uses `P_GiveBody()` which respects the player's max health bonus,
      `CF_PROSPERITY` cheat, morphing penalties, and other per-player caps. **Non-replicated on
      server mode** — direct calls with negative `amount` bypass `SERVERCOMMANDS_SetPlayerHealth()`,
      so remote clients won't see the healing.
    - **Non-players:** directly modifies `actor->health -= amount`, capped at `actor->SpawnHealth()`.
      The `mod` parameter is ignored entirely. **Non-replicated** — no network sync, clients won't
      see the change. Dead or morphing actors may be healed into a strange state with no special
      handling.
    - **One-arg form:** `mod` is optional, defaulting to `0` (see `mod` below).
  - **Zero** (`amount == 0`): **guarantees a kill** via `P_DamageMobj(..., TELEFRAG_DAMAGE, ...)`,
    which bypasses all damage invulnerability including `MF2_INVULNERABLE`, god mode (`CF_GODMODE`),
    and Buddha mode (`CF_BUDDHA`). Confirmed: line 1212 and 1519-1520 of `p_interaction.cpp` both
    gate these checks on `damage < TELEFRAG_DAMAGE`.
- `mod` *(optional)* — death message type, mapped to a `FName` damage type via `MODtoDamageType()`.
  Default is `0` (→ `NAME_None`, generic damage with no special message).
  - The mapping table is **sparse**: only indices 9, 12-18, 20, 22-27, and 1000 have entries (see
    `MODtoDamageType` in `p_lnspec.cpp:97-119`). All other `mod` values fall through to `NAME_None`.
  - **Named `MOD_*` constants exist in `zcommon.bcs`** for convenience (`MOD_ROCKET=5`, `MOD_BFG_SPLASH=9`,
    `MOD_DROWNING=12`, `MOD_FIRE=14`, etc.), so you can write readable code like `DamageThing(20,
    MOD_CRUSH)` instead of raw ints — recommended.
  - Ignored when `amount <= 0` (healing or zero-kill path).

**Returned obituary:** the engine reports the obituary based on the `mod` type, per the `MODtoDamageType`
map. If a player is killed with `mod` unset or unmapped, the engine reports a generic "died" message.
If a player is killed with a mapped `mod` (e.g., `MOD_CRUSH`), the engine reports the appropriate
cause (e.g., "crushed"). Non-players do not produce an obituary.

**Example — burn a player for 20 hitpoints:**

```text
DamageThing(20, MOD_FIRE);
```

**Example — heal the activator for 50 hitpoints:**

```text
DamageThing(-50);
```

**Example — guarantee a kill regardless of invulnerability:**

```text
DamageThing(0);
```

**Returns:** `int` — `1` (true) if an activator exists and action completed; `0` (false) if
called from a script with no activator (e.g., `OPEN`/`ENTER`/`RESPAWN`/`DISCONNECT`) or other
failure. **Not a success/failure indicator for the damage itself** — a called on an invulnerable
actor that took no damage still returns `1` if the activator existed.

## Engine-family divergence

The action special's own dispatch (`FUNC(LS_DamageThing)` in the UZDoom source's
`src/playsim/p_lnspec.cpp`) and its `MODtoDamageType` sparse mapping table are effectively
identical to Zandronum's — same three-way `amount` branch, same TELEFRAG_DAMAGE zero-kill path,
same indices mapped (9, 12-18, 20, 22-27, 1000). The divergences below are all downstream, in the
shared helpers the action special delegates to, which have each drifted independently on UZDoom:

- **`amount == 0` does not guarantee a kill against `god2`/`buddha2`.** UZDoom's damage pipeline
  (`DamageMobj` in `src/playsim/p_interaction.cpp`) adds a second, stronger cheat tier —
  `CF_GODMODE2`/`CF_BUDDHA2`, toggled by the `god2`/`buddha2` console commands — that does not exist
  in Zandronum at all. Unlike the base `CF_GODMODE`/`CF_BUDDHA`/`MF2_INVULNERABLE` checks (all
  explicitly gated on `!telefragDamage`, so `TELEFRAG_DAMAGE` bypasses them as documented above),
  the `god2`/`buddha2` short-circuit is unconditional and runs with no telefrag exception. A player
  under `god2` or `buddha2` on UZDoom takes zero damage from `DamageThing(0)` and is not killed —
  the "bypasses all damage invulnerability" claim above holds for UZDoom only against the
  Zandronum-equivalent cheat tier, not this stronger one.
- **Negative `amount` (healing) is scaled by the current skill's health factor.** UZDoom's
  `P_GiveBody` (`src/playsim/p_mobj.cpp`) multiplies a player's healing amount by
  `G_SkillProperty(SKILLP_HealthFactor)` before applying it; Zandronum's `P_GiveBody`
  (`src/g_shared/a_pickups.cpp`) has no such multiplier anywhere in the equivalent code path. The
  default `HealthFactor` for a skill definition is `1.0`, so this is numerically invisible under an
  unmodified skill set, but a MAPINFO `skill` block that sets a non-default `HealthFactor` changes
  how much `DamageThing(-amount)` heals a player on UZDoom with no Zandronum equivalent at all.
- **No `CF_PROSPERITY`-style max-health cap exists on UZDoom.** Zandronum's `P_GiveBody` special-
  cases a `CF_PROSPERITY` cheat, raising the healing cap to `deh.MaxSoulsphere + 50` while active.
  UZDoom has no matching cheat flag anywhere in its source — the healing cap there is always
  derived from the actor's regular max-health chain (`GetMaxHealth()` plus bonus-health/morph
  adjustments), with no cheat-driven override path.
- **The "non-replicated healing" caveat doesn't translate.** Zandronum's healing branch bypasses
  `SERVERCOMMANDS_SetPlayerHealth()`, a Zandronum-specific dedicated-server-to-client push that has
  no counterpart anywhere in the UZDoom source (confirmed: no `SERVERCOMMANDS`-named symbol exists
  in the UZDoom tree at all). UZDoom's multiplayer model runs every peer through the same
  deterministic simulation rather than a server pushing authoritative state to thin clients, so
  there is no separate replication step for `DamageThing`'s health change to skip in the first
  place — the Zandronum caveat describes a Zandronum-specific architecture question, not a general
  ZDoom-family one.
