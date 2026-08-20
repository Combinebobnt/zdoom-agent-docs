# `A_BossDeath`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_BossDeath` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_BossDeath&oldid=47208) + verified against the Zandronum source's `src/p_enemy.cpp:3650-3791`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
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
   - **The `compat_anybossdeath` cvar (`COMPATF_ANYBOSSDEATH`) makes any of the hardcoded boss types (Fatso, Arachnotron, Baron, Cyberdemon, etc.) satisfy any of the level-special flags** — useful for custom maps that want to repurpose boss specials. This is shared behavior, not a Zandronum addition: the flag and its use inside the hardcoded-special check are both present on UZDoom too (`src/playsim/p_enemy.cpp:3324`, upstream GZDoom's own `[GZ]`-tagged addition), confirmed via `console/inventory/cvars.md`'s `compat_anybossdeath` row (`Zan=yes`, `UZD=yes`).

5. **Level exit.** After all hardcoded specials, calls `G_ExitLevel()` to end the map — **unless playing in deathmatch/teamgame mode and the `DF_NO_EXIT` dmflag is set**, which aborts the exit.

## Engine-family divergence: hardcoded specials can fire without a `replaces` clause

The note at the end of "Hardcoded level specials" above says a custom boss class with no `replaces` clause "will not trigger these built-in specials" because the hardcoded-special gate only checks the replacee class (`type`). That holds for Zandronum but not for UZDoom. Zandronum's gate is a pure `type`-against-a-fixed-boss-class-name comparison (`NAME_Fatso`, `NAME_BaronOfHell`, etc.) with no other mechanism available — Zandronum's `AActor` has no `flags8`/`flags3` fields at all. UZDoom's gate instead (or additionally) checks per-actor `flags8`/`flags3` bits — `MF8_MAP07BOSS1`/`MF8_MAP07BOSS2`, `MF8_E1M8BOSS`, `MF8_E2M8BOSS`, `MF8_E3M8BOSS`, `MF8_E4M8BOSS`, `MF8_E4M6BOSS` (MBF21-style boss-death flags), gated by the corresponding `LEVEL3_E*SPECIAL` level flags — and these are inherited from the replacee's defaults whenever the dying actor's own class name differs from its replacee's. A custom class with no `replaces` clause that sets one of these flags directly will still trigger the matching hardcoded special on UZDoom, even though the `type`-based reasoning in "Hardcoded level specials" says it shouldn't.

UZDoom's MAP07 handling also differs in a second way: it can execute both the Fatso-side (`floorLowerToLowest`) and Arachnotron-side (`floorRaiseByTexture`) floor specials from a single death — there is no early `return` separating the two `if` checks, and a `samereplacement` case explicitly fires both when Fatso and Arachnotron have been set up (via `flags8` and `GetReplacement()`) to share a replacement target. Zandronum's MAP07 branch returns immediately after the first matching `type` check, so it can only ever trigger one of the two floor specials per death.

## Actor replacement and the `replaces` mechanism

A_BossDeath uses `GetReplacee()` internally to determine which boss *species* the death counts as. This allows a single actor that replaces a boss to inherit the boss's classic special effects:

```decorate
actor CustomBaron : Baron replaces Baron {}   // CustomBaron inherits Baron's special actions
```

When `CustomBaron` dies, `A_BossDeath()` sees `type == Baron` (the replacee), so:
- MAPINFO `specialaction`s keyed to `Baron` fire (checked via both `mytype` and `type`).
- Hardcoded specials like `LEVEL_BRUISERSPECIAL` trigger (checked via `type` only).

**Critical class-identity detail:** The actual "all bosses dead?" check (`CheckBossDeath()`) compares **exact class pointer equality** — `other->GetClass() == actor->GetClass()` — not species or replacee. If two separate classes both declare `replaces Baron` and are both alive on the map, the death of the first class will trigger baron-death specials while the second class is still alive, potentially breaking the map. This is why `RandomSpawner` (which handles exactly this scenario) explicitly monitors the spawner instance's death and synchronizes boss-death accounting — see the RandomSpawner documentation for details.

## Engine-family divergence: boss-death class-identity check

The "Critical class-identity detail" paragraph above states that `CheckBossDeath()` compares **exact class pointer equality** and nothing else. That is accurate for Zandronum but not for UZDoom. UZDoom's `CheckBossDeath()` counts another living actor as a match if *either* its class is an exact match *or* its replacee's type name matches the dying actor's replacee's type name — not exact-class-only. Practically, this means the two-classes-both-`replaces Baron` scenario the doc's paragraph warns about does not reproduce the same way on UZDoom: a second, differently-named class that also replaces `Baron` is still recognized as the same "species" via the replacee-type comparison, so its continued presence correctly blocks the baron-death specials from firing early. The `RandomSpawner` synchronization behavior described as a workaround for this trap is Zandronum-motivated; on UZDoom the underlying identity check itself already accounts for same-replacee-different-class cases.

## Network considerations

This action is **server-authoritative in multiplayer.** Clients never execute `A_BossDeath()` — they return on the early `NETWORK_InClientMode()` check and receive the map-exit outcome via server broadcast.

## Engine-family divergence: no client-mode execution gate

UZDoom's `A_BossDeath()` has no equivalent of Zandronum's `NETWORK_InClientMode()` early return — the function body has no client/server branch at all, and no `NETWORK_InClientMode`/`InClientMode`-named check exists anywhere in the UZDoom source tree. The function runs to completion on every machine rather than being gated to a single authoritative side.

## Zombie actors and item corpses

**Frozen bosses (MF_ICECORPSE flag)** are counted as **alive** until they shatter, so a frozen boss doesn't satisfy the "all dead" condition. **Actors hidden by `HideOrDestroyIfSafe()`** (Zandronum's support for map-reset game modes) are also excluded from the count via the `STFL_HIDDEN_INSTEAD_OF_DESTROYED` flag check in `CheckBossDeath()`.

## Wiki/engine divergence: undocumented behaviors

The ZDoom wiki does not document the server-side-only restriction, the `type`-vs-`mytype` asymmetry between MAPINFO and hardcoded specials, or the frozen-boss-counts-as-alive behavior — all verified against Zandronum source (not independently re-checked against UZDoom source as part of this entry).

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
