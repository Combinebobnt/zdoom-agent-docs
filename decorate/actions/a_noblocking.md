# `A_NoBlocking` / `A_Fall` (actor unblocking and item drops)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_NoBlocking` (retrieved 2026-07-31, oldid=53222) + verified against the Zandronum source's `src/p_enemy.h:60`, `src/g_shared/a_action.cpp:72-128` and `130-138`.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_NoBlocking)` and `DEFINE_ACTION_FUNCTION(AActor, A_Fall)` in `src/g_shared/a_action.cpp` — both wrap `A_Unblock()` implemented at `src/g_shared/a_action.cpp:72-128`.

Marks an actor as no longer blocking collision and spawns any items attached to the actor (dialogue-set drops and regular drop items). `A_Fall` is Doom's original name for this function; both names are equivalent in Zandronum.

**Zandronum-specific:** In multiplayer, the `MF_SOLID` flag clear is **server-side only** — clients return early from this action until the server replicates the change via `SERVERCOMMANDS_SetThingFlags`. This means a client-side actor remains solid locally until network synchronization arrives. See "Network synchronization" below.

## Signature

```
void A_NoBlocking()
void A_Fall()
```

## Behavior

When called, the action performs these steps:

1. **Stealth handling**: If the actor has the `MF_STEALTH` flag set, sets its alpha to fully opaque (`OPAQUE` = 1.0) and clears stealth-tracking state.

2. **Solid flag clear**: Removes the `MF_SOLID` flag, making the actor non-blocking to other objects. (In multiplayer, this happens server-side; clients don't execute this until the server replicates it — see "Network synchronization" below.)

3. **Dialogue-set drop priority**: If the actor's `Conversation` field is set (assigned via a dialogue lump), spawns the dialogue's associated drop item (`Conversation->DropType`) at a fixed height and immediately clears the `Conversation` field, then **returns** — skipping the regular drop item list.

4. **Regular drop items**: If the actor has a `DropItem` list and the `Conversation` field was not set (step 3 didn't return), iterates the list and spawns each item according to its probability roll. This list is **not** cleared, so subsequent calls to `A_NoBlocking` will spawn the items again (or the action could be called multiple times if the actor remains in a state that calls it).

5. **PlayerPawn exclusion**: Regular drop items (step 4) are not spawned if the actor is a `PlayerPawn` or a subclass of it.

## Parameters

None. Unlike the ZDoom/UZDoom/GZDoom-family versions, Zandronum's `A_NoBlocking` takes no optional parameters — it always spawns drop items (step 4 above always happens unless Conversation was set). The wiki describes an optional `drop` parameter present in upstream engines; **Zandronum does not support this**.

## Drop item behavior

**Dialogue-set vs. regular drops (from the source):** The action prioritizes dialogue-set drops. If both exist, only the dialogue-set item spawns on the current call; the `Conversation` field is cleared, so all subsequent calls spawn regular items instead. If only regular items exist, they spawn on every call until manually cleared.

**Probability rolls:** Both dialogue-set and regular drop items spawn at a fixed 256-unit height offset from the actor, and probability is rolled per-item in the regular list (dialogue-set drops have a fixed drop type, no probability). See the "Creating monsters" concept page for the verified `DropItem` roll mechanism and the idiom that `256` represents "always drop".

## Network synchronization

**Zandronum multiplayer only.** The `A_Unblock` function (which both `A_NoBlocking` and `A_Fall` call) has a server-mode check: in client mode, it returns early without clearing the `MF_SOLID` flag locally. The server separately replicates the flag clear via `SERVERCOMMANDS_SetThingFlags`, and stealth-visibility changes via `SERVERCOMMANDS_FlashStealthMonster`.

**Implication:** In a networked game, if a client-side pawn (a player's actor) calls `A_NoBlocking`, the client's local collision will remain solid until the server's replication arrives. For server-side monsters and projectiles, this is transparent (the server decides when to call the action), but in any `+CLIENTSIDEONLY` actor or a client-run state callback, items/projectiles can still collide with the actor briefly until the network catch-up.

## Alternatives

- **`A_ScreamAndUnblock`** — a composite action that calls `A_Scream` followed by `A_Unblock`, used in standard death states (e.g., `A_Scream` plays a sound, then `A_NoBlocking` unblocks and drops items).
- **`+NODROPOFF` actor flag** — affects actor movement constraints, not item drops; see the "Creating monsters" concept for flag bundles.

## Related

- `A_ScreamAndUnblock` — calls `A_Scream` then `A_NoBlocking` in sequence.
- `A_Scream` — plays the actor's death sound without unblocking.
- `A_FreezeDeathChunks` — an unrelated Hexen-specific action that also calls `A_Unblock` at its end.
- **DECORATE concept:** "Creating monsters" — covers `DropItem`, `Monster` property, and other death-related mechanics.
