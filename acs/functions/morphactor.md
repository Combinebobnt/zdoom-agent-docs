# MorphActor

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki, verified against Zandronum source, 2026-07-30

## Signature

```
int MorphActor(int tid [, str playerclass [, str monsterclass [, int duration [, int style [, str morphflash [, str unmorphflash]]]]])
```

## Description

Morphs actors (players and monsters) into specified classes. Returns the count of actors successfully morphed. Complements `UnMorphActor` for programmatic morph control without strategically placing DECORATE items.

## Parameters

- **tid**: Target actor(s). If `0`, uses the activator; otherwise searches for actors with this TID. Non-existent TID succeeds with return value `0` (no actors to morph).
- **playerclass**: Destination class for players (string name). Defaults to empty string; if omitted or empty, the morph fails for players.
- **monsterclass**: Destination class for monsters (string name). Defaults to empty string; if omitted or empty, the morph fails for monsters.
- **duration**: Morph duration in tics. Defaults to `0`; if `0`, uses engine default (`MORPHTICS = 40 * TICRATE`, ~1.3 seconds at standard 35 FPS). All actors use the same timer regardless of player/monster class.
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
| `MRF_UNDOALWAYS` | `0x1000` | Player unmorphs once the countdown expires. |
| `MRF_TRANSFERTRANSLATION` | `0x2000` | **Engine note:** defined in `zcommon.bcs` but not implemented in this Zandronum version; has no effect. |

### Known divergence from ZDoom wiki

The ZDoom wiki page names the style parameter flag `MRF_WHENINVULNERABLE`; Zandronum's C++ source calls it `MORPH_WHENINVULNERABLE`. The zcommon.bcs header uses the `MRF_` prefix for all morph-style flags, consistent with the script API. Both refer to the same flags.

The wiki states that this flag allows "when used on a player, provided that player is also the activator." The source code (`src/g_shared/a_morph.cpp:49`) enforces a stricter condition: an invulnerable player can morph **only if they are the activator AND the flag is set**. Morphing an invulnerable player who is not the activator always fails, regardless of the flag's state.

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

```c
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
