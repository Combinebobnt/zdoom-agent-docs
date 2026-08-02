# `int DamageThing(int amount [, int mod])`

Damages, heals, or guarantees a kill on the actor that activated the script. Action special (positive
index 73 in `zcommon.bcs`'s `special` table), semantics in the Zandronum source's `src/p_lnspec.cpp`,
`FUNC(LS_DamageThing)` (line 1123), which delegates damage calculation to `P_DamageMobj`.

**Bucket:** action special.

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

```
DamageThing(20, MOD_FIRE);
```

**Example — heal the activator for 50 hitpoints:**

```
DamageThing(-50);
```

**Example — guarantee a kill regardless of invulnerability:**

```
DamageThing(0);
```

**Returns:** `int` — `1` (true) if an activator exists and action completed; `0` (false) if
called from a script with no activator (e.g., `OPEN`/`ENTER`/`RESPAWN`/`DISCONNECT`) or other
failure. **Not a success/failure indicator for the damage itself** — a called on an invulnerable
actor that took no damage still returns `1` if the activator existed.

**Provenance:** wiki page `DamageThing - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`oldid=49026`) + source-verified (`p_lnspec.cpp:1123-1152`, `p_interaction.cpp:1152-1230,1515-1596,
1586`, `MODtoDamageType` `p_lnspec.cpp:97-119`) for behavior including TELEFRAG_DAMAGE invulnerability
bypass, attacker-null implications, healing non-replication, and sparse MOD mapping. **Engine:**
Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD). **Tier:** A.
