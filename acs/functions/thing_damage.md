# `int Thing_Damage(int tid, int amount [, int mod])`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-28)
**Provenance:** wiki page `Thing_Damage - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-28, `https://zdoom.org/w/index.php?title=Thing_Damage&oldid=53478`) + source-verified against `p_lnspec.cpp:1373-1378`, `p_things.cpp:469-502`, `p_interaction.cpp:1152-1210` (P_DamageMobj entry), `MODtoDamageType` switch (`p_lnspec.cpp:97-119`), `zcommon.bcs:85-108` (MOD enum). Wiki/fork divergence recorded: `Thing_Damage2` (mentioned in wiki as an ACS function alternative for named damage types) does not exist in Zandronum (`zcommon.bcs` defines only `Thing_Damage` at index 119, and `zandronum/src` implements it in `p_lnspec.cpp` with no `Thing_Damage2` variant) — use the `MOD_*` int codes with `Thing_Damage` instead, accepting the enumerated-list limit (no custom damage-type names).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** action special.

Applies damage (or healing) to actor(s) selected by TID. Action special 119 (dispatched as `FUNC(LS_Thing_Damage)` in the Zandronum source's `src/p_lnspec.cpp:1373-1378`), calls the engine's `P_Thing_Damage()` helper (the Zandronum source's `src/p_things.cpp:469-502`).

## Parameters

- `tid` — actor's thing ID. **`0` means "the activator"** — when TID is 0, only the script's own activator is targeted (no iteration). A NULL activator in a script with no activation context (`OPEN`/`ENTER`/`RESPAWN`/`DISCONNECT`, etc.) is a safe no-op — the function still executes but damages nothing.
- `amount` — damage amount (positive to damage, negative or zero to heal).
  - **Positive `amount`:** damages actor(s) via the engine's `P_DamageMobj` (applies pain states, plays pain sounds, triggers death, respects invulnerability flags, applies knockback/thrust, etc.). The damage-type parameter `mod` is used for obituary/means-of-death selection.
  - **Zero or negative `amount`:** heals actor(s), but **only if their current health is less than their spawn health**. The heal is applied as `actor->health -= amount` (so a negative `amount` of e.g. `-20` adds 20 health), clamped to the actor's `SpawnHealth()` upper bound. This branch **bypasses `P_DamageMobj` entirely** — no pain states, no pain sounds, no knockback, and the `mod` parameter is ignored.
  - **In both branches**, only actors with the `MF_SHOOTABLE` flag are processed. Non-shootable actors are skipped and not counted.
- `mod` — means of death / damage type. Passed through `MODtoDamageType(arg2)` (`p_lnspec.cpp:97-119`), which converts int codes to engine damage-type `FName`s. Valid codes are: 9 (`BFGSplash`), 12 (`Drowning`), 13 (`Slime`), 14 (`Fire`), 15 (`Crush`), 16 (`Telefrag`), 17 (`Falling`), 18 (`Suicide`), 20 (`Exit`), 22 (`Melee`), 23 (`Railgun`), 24 (`Ice`), 25 (`Disintegrate`), 26 (`Poison`), 27 (`Electric`), 1000 (`Massacre`). Any other value (including 0) maps to `NAME_None` and has no obituary. **In the healing branch (`amount <= 0`), the damage type is ignored entirely and never used.** Missing the `mod` parameter compiles to a literal `0` (NAME_None), not a fallback like `-1`.
  - The zcommon.bcs signature shows `mod` as optional (third parameter after a `;` marker), defaulting to 0 when omitted: `119:Thing_Damage(int,int;int):int`.

## Return value and count semantics

The ACS action special `Thing_Damage` **always returns `true` (1)** to the script, regardless of how many actors were actually damaged or whether the function did anything (`LS_Thing_Damage` in `p_lnspec.cpp:1373-1378` calls `P_Thing_Damage` and discards its return, then `return true;`). The underlying `P_Thing_Damage` function returns a count of affected actors, but this count is never exposed to ACS.

## Activator-as-source suicide caveat (wiki-asserted, mechanism verified)

When `tid=0` (targeting the activator) **and the script's activator is also the damaged actor**, the call passes the same actor pointer as both target and source to `P_DamageMobj` (target, inflictor=NULL, source=activator) — `p_things.cpp:483`. The wiki states that this results in a suicide obituary message ("player killed self") rather than the damage type's intended obituary, regardless of the `mod` parameter. **The specific obituary-selection mechanism in `P_DamageMobj` was not traced**, only the parameter-passing path confirmed. **Workaround per wiki:** reassign the activator before calling `Thing_Damage` if the activator is the intended target and you want a non-suicide obituary message.

## Detailed example

**Damage enemies with TID 100 for 20 damage, railgun means of death:**

```text
Thing_Damage(100, 20, MOD_RAILGUN);
```

**Heal all actors with TID 50 (if below spawn health):**

```text
Thing_Damage(50, -10); // Negative amount heals; mod parameter is optional and ignored on heal path
```

## Zandronum-specific: multiplayer / client-side caveat

The positive-`amount` damage branch calls `P_DamageMobj`, which has full `SERVERCOMMANDS_*` netcode synchronization to clients. However, the negative-`amount` healing branch writes `actor->health` directly with no `SERVERCOMMANDS_*` calls (not even for players — the code writes `actor->player->health` too, but no message is sent). In a networked server, healing via `Thing_Damage(tid, -amount)` is invisible to clients, who continue seeing the (lower) pre-heal health. **Do not rely on `Thing_Damage(tid, -amount, ...)` for gameplay-critical healing in multiplayer.**

---
