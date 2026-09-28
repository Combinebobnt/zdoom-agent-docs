# Thing_Hate

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** ZDoom Wiki (Thing_Hate) (retrieved 2026-08-06, https://zdoom.org/w/index.php?title=Thing_Hate&oldid=32902) + verified against Zandronum source `src/p_lnspec.cpp:1394-1562` (immediate-target gate `src/p_lnspec.cpp:1526`; hate-group look `src/p_enemy.cpp:1459-1558`, player look `src/p_enemy.cpp:1709-1849`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Action special, index 177.

```acs
int Thing_Hate(int hater, int hatee, int type)
```

## Summary

Makes a monster hate another actor or a TID group. With a non-zero hater TID, every actor carrying that TID that is alive (`health > 0`) and shootable is affected. A hatee picked by TID must be shootable, alive and not dormant. Players are refused only on the activator path: with `hater = 0` and a player as the activator, it does nothing and returns `false` (`src/p_lnspec.cpp:1420-1424`). The TID path does not filter players out.

## Parameters

- **hater** (int): TID of the actor that will hate and attack. A TID of 0 refers to the activator of the script. If that activator is a player, the call fails (returns `false`); with no activator (e.g. an `OPEN` script) nothing happens.
- **hatee** (int): TID of the target actor to be hated. A TID of 0 means the activator. It is not checked for health, shootability or dormancy, and with no activator there is no hatee.
- **type** (int): The hate behavior type (see Type Values below).

## Type Values

| Type | Behavior |
|------|----------|
| **0** | Attack the specific target actor. The target is assigned at once and the hater wakes into its See state, no sight needed. If distracted by player damage, will attack the player. After defeating the target (if not distracted), returns to normal monster behavior. |
| **1** | Attack actors with the given TID on sight. If distracted by player damage, will attack the player. After defeating the target (if not distracted), returns to sleep and ignores the player unless harmed. |
| **2** | Attack actors with the given TID. Like type 1, but will pursue the target without needing to see it first (no line-of-sight check). |
| **3** | Hunt actors with the given TID *and* actively hunt players. On sight, will attack. If distracted by player damage, will also attack the player. After defeating the target (if not distracted), returns to normal monster behavior. |
| **4** | Hunt actors with the given TID and players. Like type 3, but will pursue actors with the given TID without needing to see them first. Players are still looked for with a sight check outside Zandronum's invasion mode (`src/p_enemy.cpp:1849`). |
| **5** | Attack actors with the given TID on sight. *Never* attacks the player before or after, even if damaged by them. |
| **6** | Attack actors with the given TID. Like type 5, but will pursue without needing to see the target first. |

## Behavioral Notes

- **When a target is assigned immediately:** the hater gets `target = hatee` and enters its See state on the spot only for type 0, or for types 1-6 when the hater has a `goal` it isn't currently targeting (`src/p_lnspec.cpp:1526`). Otherwise types 1-6 only record the hate data (TID to hate plus flags) and leave target selection to the monster's look code (`P_LookForTID`, `src/p_enemy.cpp:1459-1558`). A dormant (`MF2_DORMANT`) or dead hater gets the target but no state change.
- **TID 0 activator use:** from an `ENTER` script, `Thing_Hate(tid, 0, 0)` targets the activating player immediately and wakes the monsters. `Thing_Hate(tid, 0, 2)` does not do this for a monster without a goal. It records a TID to hate of 0 (normal behavior) and sets `MF3_NOSIGHTCHECK`, but that flag is only honored when looking for a TID group (`src/p_enemy.cpp:1518`). The player search always checks sight outside Zandronum's invasion mode (`src/p_enemy.cpp:1849`). The engine's own source comment (`src/p_lnspec.cpp:1478-1479`) says type 2 with hatee 0 makes a monster go after a player without seeing him first; the code at `:1526` doesn't do that, so don't rely on the comment.
- **Hatee validation:** if the hatee TID matches no shootable, living, non-dormant actor, the call still returns `true` and is not a no-op. Types 1-6 record the TID to hate, set or clear the three flags, reset the look iterator, and clear the hater's current `target`/`lastenemy` when their TID differs from the hatee TID (`src/p_lnspec.cpp:1449-1466`), so the monster drops its current enemy. Type 0 only rewrites the flags.
- **Type 0 specifics:** type 0 hates one actor: the activator for `hatee = 0`, or the first valid actor with the hatee TID (every hater gets that same one). It does not touch the TID to hate, so an earlier group hate from types 1-6 stays in effect.
- **Flag patterns:** each call sets or clears three flags:
  - **No-sight-check** (`MF3_NOSIGHTCHECK`): set for types 2, 4, 6; cleared otherwise.
  - **Hunt players** (`MF3_HUNTPLAYERS`): set for types 3, 4; cleared otherwise.
  - **Ignore players** (`MF4_NOHATEPLAYERS`): set for types 5, 6; cleared otherwise.
- **Wiki divergence:** the wiki's initial example uses `Thing_Hate(100, 0, 0)` to make monsters attack the player at map start. From an `ENTER` script that is the form that works: the activator is the player and type 0 assigns the target at once. From an `OPEN` script there is no activator, so nothing happens. The wiki prose recommends `Thing_Hate(tid, 0, 4)` for a no-sight-check idiom and the source comment names type 2 instead. Neither makes a goal-less monster chase a player it hasn't seen, since players are always sight-checked (outside Zandronum's invasion mode); type 4 additionally sets `HUNTPLAYERS`.
- **Server/network:** offline and on a Zandronum server the special runs locally. When the hater is put into its See state, the server also sends `SERVERCOMMANDS_SetThingState` with `STATE_SEE` (gated on `NETSTATE_SERVER`, `src/p_lnspec.cpp:1538-1539`). Only the state change is sent; the hate data, flags and `target` stay server-side, where the monster AI runs.
- **All matching TIDs:** with a non-zero hater TID the function applies the hate to **all** matching alive, shootable actors, not just the first one. An actor with no See state is skipped (`src/p_lnspec.cpp:1444`).

## Engine-family divergence: server-authoritative state sync is Zandronum-only

The core hate-assignment logic is identical between the two engines apart from Zandronum's
network lines: UZDoom's `FUNC(LS_Thing_Hate)` (`src/playsim/p_lnspec.cpp:1565-1726`) sets the TID
to hate and resets the look iterator, clears/updates `target` and `lastenemy`, applies the same
`MF3_NOSIGHTCHECK` / `MF3_HUNTPLAYERS` / `MF4_NOHATEPLAYERS` flag rules per type, uses the same
immediate-target gate, and assigns `target` before putting the hater into its See state, matching
the Zandronum engine fork's `src/p_lnspec.cpp:1394-1562`.

The one difference is the "Server/network" behavioral note above. Just before the See-state
change, the Zandronum engine fork adds a check that, when running as the server, sends clients a
`SERVERCOMMANDS_SetThingState` with `STATE_SEE` so they also put the actor into its see state.
UZDoom has no `SERVERCOMMANDS_*` system at all (confirmed absent from its source tree); it just
changes the state with no separate network-sync step. This has no single-player-visible effect
either way. It only matters for how the state change propagates to remote clients in a networked
game, so the "Server/network" bullet above should be read as Zandronum-specific, not a claim
about UZDoom.

## Examples

Make all monsters with TID 100 wake and attack the entering player at map start. Type 0 assigns the target immediately; `ENTER` supplies the player as activator (an `OPEN` script has none):

```acs
script 1 ENTER
{
    Thing_Hate(100, 0, 0);  // Type 0: target the activator now
}
```

Set up opposing monster groups to fight each other:

```acs
script 1 (int marines_tid, int demons_tid, int cam)
{
    ChangeCamera(cam, 1, 0);
    PrintBold(s:"The marines attack the demon stronghold!");
    
    Thing_Hate(marines_tid, demons_tid, 6);  // Marines wake on their next look and ignore players
    Thing_Hate(demons_tid, marines_tid, 3);  // Demons hunt both marines and players
    
    Delay(350);
    ChangeCamera(0, 1, 0);
}
```
