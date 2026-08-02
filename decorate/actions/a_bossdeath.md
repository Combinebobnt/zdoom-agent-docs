# `A_BossDeath`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_BossDeath` (retrieved 2026-08-01, oldid=47208) + verified against the Zandronum source's `src/p_enemy.cpp:3650-3791`.
**Bucket:** Action function on `AActor` (`DEFINE_ACTION_FUNCTION` in `src/p_enemy.cpp:3686`).

Triggers special end-map effects when all monsters of the calling actor's type are dead. The function checks both MAPINFO-defined special actions and hardcoded classic Doom boss specials (floor/door sequences and level exit). **Server-side only in multiplayer.**

## Signature

```decorate
void A_BossDeath()
```

## Behavior

When called, the action performs these steps:

1. **Server-side gate.** In client mode (network play), returns immediately without executing any effects. The server handles all boss-death logic and replicates outcomes to clients.

2. **Player alive check.** If no players are alive (all players dead or spectating in some edge case), returns without triggering any effects. The map never exits if the last player dies at the same instant a final boss does.

3. **MAPINFO special actions lookup.** Iterates `level.info->specialactions[]` (assigned via MAPINFO's `specialaction` command) and executes any action whose `Type` field matches either:
   - `mytype`: The calling actor's own class name (useful for custom boss classes with custom special actions).
   - `type`: The calling actor's "replacee" class — determined by `GetReplacee()`, the actor class this one declares `replaces` (crucial for RandomSpawner and boss replacement scenarios — see "Actor replacement" below).
   
   If a matching special action is found, calls `CheckBossDeath()` exactly once to verify all bosses of that type are dead, then executes the action via `P_ExecuteSpecial()` and **continues to the next action** (multiple special actions can fire for a single death).

4. **Hardcoded level specials.** If the map has none of the hardcoded Doom boss-trigger level flags set (`LEVEL_MAP07SPECIAL`, `LEVEL_BRUISERSPECIAL`, `LEVEL_CYBORGSPECIAL`, etc.), returns without further action.
   
   If a matching level special is active:
   - For `LEVEL_MAP07SPECIAL`: triggers different specials depending on whether the dying boss is a **Fatso** (lower floor to lowest) or **Arachnotron** (raise floor by texture).
   - For other level specials: triggers a corresponding floor-lowering, floor-raising, or door-opening special by level flag.
   - **Note:** These hardcoded specials match only the `type` (replacee class), not `mytype`. A custom boss class with no `replaces` clause will not trigger these built-in specials — only MAPINFO `specialaction` entries keyed to the custom class will fire.

5. **Level exit.** After all hardcoded specials, calls `G_ExitLevel()` to end the map — **unless playing in deathmatch/teamgame mode and the `DF_NO_EXIT` dmflag is set**, which aborts the exit.

## Actor replacement and the `replaces` mechanism

A_BossDeath uses `GetReplacee()` internally to determine which boss *species* the death counts as. This allows a single actor that replaces a boss to inherit the boss's classic special effects:

```decorate
actor CustomBaron : Baron replaces Baron {}   // CustomBaron inherits Baron's special actions
```

When `CustomBaron` dies, `A_BossDeath()` sees `type == Baron` (the replacee), so:
- MAPINFO `specialaction`s keyed to `Baron` fire (checked via both `mytype` and `type`).
- Hardcoded specials like `LEVEL_BRUISERSPECIAL` trigger (checked via `type` only).

**Critical class-identity detail:** The actual "all bosses dead?" check (`CheckBossDeath()`) compares **exact class pointer equality** — `other->GetClass() == actor->GetClass()` — not species or replacee. If two separate classes both declare `replaces Baron` and are both alive on the map, the death of the first class will trigger baron-death specials while the second class is still alive, potentially breaking the map. This is why `RandomSpawner` (which handles exactly this scenario) explicitly monitors the spawner instance's death and synchronizes boss-death accounting — see the RandomSpawner documentation for details.

## Network considerations

This action is **server-authoritative in multiplayer.** Clients never execute `A_BossDeath()` — they return on the early `NETWORK_InClientMode()` check and receive the map-exit outcome via server broadcast.

## Zombie actors and item corpses

**Frozen bosses (MF_ICECORPSE flag)** are counted as **alive** until they shatter, so a frozen boss doesn't satisfy the "all dead" condition. **Actors hidden by `HideOrDestroyIfSafe()`** (Zandronum's support for map-reset game modes) are also excluded from the count via the `STFL_HIDDEN_INSTEAD_OF_DESTROYED` flag check in `CheckBossDeath()`.

## Zandronum additions and divergences

The `COMPATF_ANYBOSSDEATH` compatibility flag (checked in the hardcoded special section) makes any of the hardcoded boss types (Fatso, Arachnotron, Baron, Cyberdemon, etc.) satisfy any of the level-special flags, useful for custom maps that want to repurpose boss specials.

The ZDoom wiki does not document the server-side-only restriction, the `type`-vs-`mytype` asymmetry between MAPINFO and hardcoded specials, or the frozen-boss-counts-as-alive behavior — all verified against Zandronum source.

## Examples

```decorate
actor MyDemonBoss : Cyberdemon replaces Cyberdemon
{
  // Inherits all Cyberdemon classic specials
}

actor CustomFinalBoss : BaronOfHell
{
  States
  {
  Death:
    BOSS A 8
    BOSS B 8 A_Scream
    BOSS C 10
    BOSS D -1 A_BossDeath
    Stop
  }
}
```

```mapinfo
// Level 01 - trigger a custom action when CustomFinalBoss dies
Level MAP01 "Test Map"
{
  specialaction Ceiling_RaiseByValue 32 0 0 0 0, CustomFinalBoss
}
```

## See also

- [RandomSpawner](../classes/randomspawner.md) — handles boss death accounting when multiple actor classes replace the same boss, avoiding the class-identity trap described above.
- [Creating monsters](../concepts/creating-monsters.md) — covers `DropItem` and other monster-definition mechanics.
- MAPINFO `specialaction` key — assigns special actions to a boss type (documented in the MAPINFO section of this docs tree if available).
