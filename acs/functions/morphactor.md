# MorphActor

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-06)
**Provenance:** ZDoom Wiki (https://zdoom.org/w/index.php?title=MorphActor&oldid=53654), verified against Zandronum source (src/p_acs.cpp PCD_MORPHACTOR, src/g_shared/a_morph.cpp, src/g_shared/a_morph.h), 2026-08-06
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin (`PCD_MORPHACTOR` in `src/p_acs.cpp`).

## Signature

```text
int MorphActor(int tid [, str playerclass [, str monsterclass [, int duration [, int style [, str morphflash [, str unmorphflash]]]]])
```

## Description

Morphs actors (players and monsters) into specified classes. Returns the count of actors successfully morphed. Complements `UnMorphActor` for programmatic morph control without strategically placing DECORATE items.

## Parameters

- **tid**: Target actor(s). If `0`, uses the activator; otherwise searches for actors with this TID. Non-existent TID succeeds with return value `0` (no actors to morph).
- **playerclass**: Destination class for players (string name). Defaults to empty string; if omitted or empty, the morph fails for players.
- **monsterclass**: Destination class for monsters (string name). Defaults to empty string; if omitted or empty, the morph fails for monsters.
- **duration**: Morph duration in tics. Defaults to `0`; if `0`, uses engine default (`MORPHTICS = 40 * TICRATE`, approximately 40 seconds at standard 35 FPS). For players, morphing uses the exact duration. For monsters, morphing duration has 0–255 tics of random jitter added (cosmetic variation, not a functional difference).
- **style**: Bit flags controlling morph behavior (see Style flags below). Defaults to `0` (legacy Heretic/Hexen semantics).
- **morphflash**: Spawn class for the morph entrance flash effect (string name). Defaults to empty string; if omitted or empty, uses engine default (teleport fog). Only spawned for the first morph call; subsequent calls (e.g., super-morphing) may skip it.
- **unmorphflash**: Spawn class for the unmorph exit flash effect (string name). Defaults to empty string; if omitted or empty, uses engine default (teleport fog). Spawned by `UnMorphActor`, not by `MorphActor` itself.

## Return value

Integer count of actors successfully morphed. For `tid = 0`, this is effectively a boolean: `0` (failed) or `1` (succeeded, if activator morphed successfully). `0` can also mean no actors with the given `tid` existed.

## Failure cases

Returns `0` (no morphs) if any of these hold for every target actor:

- The actor has the `DONTMORPH` flag set.
- For players: the actor is already morphed, already dead (`health <= 0`), or invulnerable (`MF2_INVULNERABLE` flag) and either (a) the `MRF_WHENINVULNERABLE` style flag is not set, or (b) they are not the activator of the call.
- For players: `playerclass` is empty or names a non-existent class, or the named class is not a descendant of `APlayerPawn`, or the player is already that class.
- For monsters: `monsterclass` is empty or names a non-existent class, or the named class is not a descendant of `AMorphedMonster` (all morphed monsters must inherit this class, not arbitrary monster types).
- Activator is `NULL` and `tid` is `0` (no target can be determined).

## Style flags

Zandronum exposes morph style flags via the `MRF_*` enum in `zcommon.bcs`. The engine internally refers to these as `MORPH_*` in the C++ source (`src/g_shared/a_morph.h`). Both names refer to the same flags:

| Flag | Value | Effect |
|------|-------|--------|
| `MRF_OLDEFFECTS` | `0x0` | Default: legacy Heretic/Hexen behavior. Player is limited to morphed health cap; no stamina bonus. |
| `MRF_ADDSTAMINA` | `0x1` | Player gains stamina (treated as a power) rather than a curse; maintains normal health semantics. |
| `MRF_FULLHEALTH` | `0x2` | Player uses new health behavior: if not a stamina power, use morphed class's max health; if a power, use normal health semantics. |
| `MRF_UNDOBYTOMEOFPOWER` | `0x4` | Player unmorphs upon picking up a Tome of Power. |
| `MRF_UNDOBYCHAOSDEVICE` | `0x8` | Player unmorphs upon picking up a Chaos Device. |
| `MRF_FAILNOTELEFRAG` | `0x10` | Player stays morphed if unmorph by Tome of Power fails. |
| `MRF_FAILNOLAUGH` | `0x20` | Player doesn't laugh if unmorph by Chaos Device fails. |
| `MRF_WHENINVULNERABLE` | `0x40` | Invulnerable players can morph, but **only when morphing themselves** (activator equals target). Morphing an invulnerable player via another actor always fails, even with this flag. |
| `MRF_LOSEACTUALWEAPON` | `0x80` | Player loses the specifically morphed weapon (not "whichever they have when unmorphing"). |
| `MRF_NEWTIDBEHAVIOUR` | `0x100` | Transfer the original actor's TID to the morphed actor. Default is no TID transfer. |
| `MRF_UNDOBYDEATH` | `0x200` | Actor unmorphs when killed (and stays dead, unless `MRF_UNDOBYDEATHSAVES` is also set). |
| `MRF_UNDOBYDEATHFORCED` | `0x400` | Forces unmorph when killed (mainly useful with `MRF_UNDOBYDEATHSAVES`). |
| `MRF_UNDOBYDEATHSAVES` | `0x800` | Actor (if unmorphed upon death) regains health and doesn't die. |
| `MRF_UNDOALWAYS` | `0x1000` | Player unmorphs once the countdown expires. (Engine calls this flag `MORPH_UNDOBYTIMEOUT` in `a_morph.h`, same value, different name.) |
| `MRF_TRANSFERTRANSLATION` | `0x2000` | **Engine note:** defined in `zcommon.bcs` but not implemented in this Zandronum version; has no effect. |

### Known divergence from ZDoom wiki

The ZDoom wiki page names the style parameter flag `MRF_WHENINVULNERABLE`; Zandronum's C++ source calls it `MORPH_WHENINVULNERABLE`. The zcommon.bcs header uses the `MRF_` prefix for all morph-style flags, consistent with the script API. Both refer to the same flags.

The wiki states that this flag allows "when used on a player, provided that player is also the activator." The source code (`src/g_shared/a_morph.cpp:49`) enforces a stricter condition: an invulnerable player can morph **only if they are the activator AND the flag is set**. Morphing an invulnerable player who is not the activator always fails, regardless of the flag's state.

## Engine-family divergence: morph style flags (UZDoom)

UZDoom's `EMorphFlags` enum (`wadsrc/static/zscript/constants.zs`) keeps every flag from the Zandronum-derived table above at the same bit value through `MRF_UNDOBYDEATHSAVES` (`0x800`), but diverges from that point on:

- **`MRF_UNDOALWAYS` and `MRF_UNDOBYTIMEOUT` are two distinct flags in UZDoom, not aliases.** `MRF_UNDOBYTIMEOUT` keeps value `0x1000` and the "unmorphs once the countdown expires" meaning the doc's table attributes to `MRF_UNDOALWAYS`. `MRF_UNDOALWAYS` moves to `0x2000` and instead means "powerup-style morphs must always unmorph regardless of other conditions." A script relying on the doc's Zandronum-derived claim that these are the same flag under two names will be wrong on UZDoom.
- **`MRF_TRANSFERTRANSLATION` moves from `0x2000` to `0x4000`, and is now actually implemented** (it copies the pre-morph actor's translation onto the morphed monster, when the morphed actor doesn't have `DONTTRANSLATE`), unlike Zandronum where the doc notes it's defined but has no effect. Because `~/source/zt-bcc/lib/zcommon.bcs` still defines `MRF_TRANSFERTRANSLATION` as `0x2000` (matching Zandronum, not UZDoom), a BCS script compiled against that header and run on UZDoom would set UZDoom's `MRF_UNDOALWAYS` bit instead of requesting translation transfer — a real constant/engine mismatch trap for cross-engine scripts, not just a documentation nuance.
- **Two flags exist in UZDoom with no equivalent in the doc's table or in zt-bcc's `zcommon.bcs`:** `MRF_KEEPARMOR` (`0x8000`, skips the automatic armor-removal that normally happens when a monster morphs) and `MRF_IGNOREINVULN` (`0x10000`, bypasses the invulnerability check entirely for both morph and unmorph, regardless of activator identity or whether `MRF_WHENINVULNERABLE` is set). Scripts targeting UZDoom must pass these as raw integer literals since no named BCS constant exists for them yet.
- **The monster-morph failure case "named class is not a descendant of `AMorphedMonster`" no longer holds in UZDoom.** `MorphMonster()` (`wadsrc/static/zscript/actors/morph.zs`) only optionally casts the spawned actor to `MorphedMonster` — the source comments this is kept "for backwards compatibility as MorphedMonster used to be required" — and proceeds regardless of whether the cast succeeds. Any `Actor`-derived class can now be a morph target for monsters; `AMorphedMonster`-specific bookkeeping (its stored pre-morph alternate/style/flags fields) is simply skipped for classes that aren't descendants, rather than the morph failing outright.

## Network replication

In multiplayer, the morph operation is automatically replicated to all clients:
- Morph entrance and exit fog effects are spawned on all clients.
- Player and monster state updates (flags, position, animation) are synchronized.
- For monsters, the old actor is destroyed and the new one spawned on all clients.
- No explicit server-side calls are needed; the engine handles replication internally.

## Related functions

- `UnMorphActor` — reverts a morphed actor to its original form.

## Example

Morph a cyberdemon (TID 1) into a different actor class, with a 3-second morph duration and entrance flash:

```acs
script 1 (void)
{
    int count = MorphActor(1, "", "MorphDemon", 105, 0, "CustomMorphFlash", "");
    if (count == 0)
    {
        Log(s: "Morph failed");
    }
}
```

Note: The morphed demon class must inherit from `AMorphedMonster` in DECORATE/ZSCRIPT, not an arbitrary `Cyberdemon` variant. See the ZDoom wiki's example for a minimal `MorphDemon` subclass.
