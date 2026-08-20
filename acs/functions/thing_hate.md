# Thing_Hate

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-06)
**Provenance:** ZDoom Wiki (Thing_Hate) (retrieved 2026-08-06, https://zdoom.org/w/index.php?title=Thing_Hate&oldid=32902) + verified against Zandronum source `src/p_lnspec.cpp:1394-1562`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Action special, index 177.

```acs
int Thing_Hate(int hater, int hatee, int type)
```

## Summary

Forces a monster to hate and attack another actor. Both the hater and hatee must be alive with health > 0 for this to take effect. Cannot be used on players.

## Parameters

- **hater** (int): TID of the actor that will hate and attack. A TID of 0 refers to the activator of the script (usually the player).
- **hatee** (int): TID of the target actor to be hated. A TID of 0 means the hater will target the activator.
- **type** (int): The hate behavior type (see Type Values below).

## Type Values

| Type | Behavior |
|------|----------|
| **0** | Attack the specific target actor. On sight, wake and attack. If distracted by player damage, will attack the player. After defeating the target (if not distracted), returns to normal monster behavior. |
| **1** | Attack actors with the given TID on sight. If distracted by player damage, will attack the player. After defeating the target (if not distracted), returns to sleep and ignores the player unless harmed. |
| **2** | Attack actors with the given TID. Like type 1, but will pursue the target without needing to see it first (no line-of-sight check). |
| **3** | Hunt actors with the given TID *and* actively hunt players. On sight, will attack. If distracted by player damage, will also attack the player. After defeating the target (if not distracted), returns to normal monster behavior. |
| **4** | Hunt actors with the given TID and players. Like type 3, but will pursue without needing to see targets first. |
| **5** | Attack actors with the given TID on sight. *Never* attacks the player before or after, even if damaged by them. |
| **6** | Attack actors with the given TID. Like type 5, but will pursue without needing to see the target first. |

## Behavioral Notes

- **TID 0 activator use:** `Thing_Hate(tid, 0, type)` sets a monster to hate the script activator (the player). Crucially, `Thing_Hate(tid, 0, 2)` makes a monster attack the player without requiring a line-of-sight (no sight check), even if the monster is normally dormant — this is the intended idiom.
- **Hatee validation:** If the hatee TID does not correspond to any valid, living, shootable, non-dormant target, the function returns `true` but has no effect (the hate flags are set but no target is assigned).
- **Type 0 exception:** Type 0 operates on a single specific actor rather than a TID group — it does not set `TIDtoHate` or enable dynamic target cycling. Consequently, it cannot be used with `hatee = 0` (activator) in the way types 1–6 can.
- **Flag patterns:** Engine sets three separate flags:
  - **No-sight-check** (`MF3_NOSIGHTCHECK`): Types 2, 4, 6 only (not 0).
  - **Hunt players** (`MF3_HUNTPLAYERS`): Types 3, 4 only.
  - **Ignore players** (`MF4_NOHATEPLAYERS`): Types 5, 6 only.
- **Wiki divergence:** The wiki's initial example uses `Thing_Hate(100, 0, 0)` to make monsters attack the player "at map start," but type 0 does not set the dynamic TID-tracking mode; type 2 is likely intended. Additionally, the wiki prose recommends `Thing_Hate(tid, 0, 4)` for the activator no-sight-check idiom, but the source comment explicitly documents `Thing_Hate(tid, 0, 2)` instead; both set `NOSIGHTCHECK`, but type 4 additionally sets `HUNTPLAYERS`, making them not equivalent. Prefer type 2 for the "attack without seeing" effect alone.
- **Server/network:** Setting a hater to its see state is server-authoritative; clients receive a `SERVERCOMMANDS_SetThingState` packet.
- **All matching TIDs:** The function iterates and applies the hate to **all** actors with the matching hater TID, not just the first one.

## Engine-family divergence: server-authoritative state sync is Zandronum-only

The core hate-assignment logic is byte-for-byte identical between the two engines: UZDoom's
`FUNC(LS_Thing_Hate)` (`src/playsim/p_lnspec.cpp:1565-1726`) sets `TIDtoHate`/`LastLookActor`,
clears/updates `target` and `lastenemy`, applies the same `MF3_NOSIGHTCHECK` /
`MF3_HUNTPLAYERS` / `MF4_NOHATEPLAYERS` flag rules per type, and assigns `hater->target` before
calling `hater->SetState(hater->SeeState)`, matching the Zandronum engine fork's
`src/p_lnspec.cpp:1394-1562` line for line.

The one difference is the "Server/network" behavioral note above: immediately before
`hater->SetState(hater->SeeState)`, the Zandronum engine fork inserts `if (NETWORK_GetState() ==
NETSTATE_SERVER) SERVERCOMMANDS_SetThingState(hater, STATE_SEE);` — a server-authoritative
broadcast telling clients to also put the actor into its see state, part of Zandronum's own
client-server netcode. UZDoom has no `SERVERCOMMANDS_*` system at all (confirmed absent from its
source tree); it calls `hater->SetState(hater->SeeState)` directly with no separate network-sync
step. This has no single-player-visible effect either way — it only matters for how the state
change propagates to remote clients in a networked game — so the "Server/network" bullet above
should be read as Zandronum-specific, not a claim about UZDoom.

## Examples

Make all monsters with TID 100 attack the player without seeing them first at map start:

```acs
script 1 ENTER
{
    Thing_Hate(100, 0, 2);  // Type 2: pursue players without sight check
}
```

Set up opposing monster groups to fight each other:

```acs
script 1 (int marines_tid, int demons_tid, int cam)
{
    ChangeCamera(cam, 1, 0);
    PrintBold(s:"The marines attack the demon stronghold!");
    
    Thing_Hate(marines_tid, demons_tid, 6);  // Marines wake and ignore players
    Thing_Hate(demons_tid, marines_tid, 3);  // Demons hunt both marines and players
    
    Delay(350);
    ChangeCamera(0, 1, 0);
}
```
