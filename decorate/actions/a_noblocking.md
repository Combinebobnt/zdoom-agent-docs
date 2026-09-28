# `A_NoBlocking` / `A_Fall` (actor unblocking and item drops)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_NoBlocking` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_NoBlocking&oldid=53222) + verified against the Zandronum source's `src/p_enemy.h:60`, `src/g_shared/a_action.cpp:72-128` and `130-138`, `src/p_enemy.cpp:3463-3491` (`P_DropItem`), `src/network.cpp:1552-1555`, `src/sv_main.cpp:5653-5668` and `src/cl_main.cpp:5807-5809`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_NoBlocking)` and `DEFINE_ACTION_FUNCTION(AActor, A_Fall)` in `src/g_shared/a_action.cpp` — both wrap `A_Unblock()` implemented at `src/g_shared/a_action.cpp:72-128`.

Marks an actor as no longer blocking collision and spawns any items attached to the actor (dialogue-set drops and regular drop items). `A_Fall` is Doom's original name for this function; both names are equivalent in Zandronum.

**Zandronum-specific:** In multiplayer, the whole action is **server-side only**. On a client it returns immediately, so the client neither clears `MF_SOLID` nor spawns drops itself. It learns the flag change from `SERVERCOMMANDS_SetThingFlags` and sees the server's drops via `SERVERCOMMANDS_SpawnThing`. A `+CLIENTSIDEONLY` actor has no server copy, so on a client this action never does anything for it. See "Network synchronization" below.

## Signature

```text
void A_NoBlocking()
void A_Fall()
```

## Behavior

When called, the action performs these steps:

1. **Stealth handling**: If the actor has the `MF_STEALTH` flag set, sets its alpha to fully opaque (`OPAQUE` = 1.0) and clears stealth-tracking state.

2. **Solid flag clear**: Removes the `MF_SOLID` flag, making the actor non-blocking to other objects. (On Zandronum in multiplayer, this and every other step run only on the server. See "Network synchronization" below.)

3. **Dialogue-set drop priority**: If the actor's `Conversation` field is set (assigned via a dialogue lump) and that dialogue names a drop item (`Conversation->DropType`), spawns that item, clears the `Conversation` field, then **returns**, skipping the regular drop item list.

4. **Regular drop items**: Otherwise the `Conversation` field is cleared anyway (even when it was set without a drop item), and each entry of the actor's `DropItem` list is spawned according to its own probability roll. Entries naming a class that doesn't exist are skipped. The list is **not** cleared, so a later call to `A_NoBlocking` spawns the items again.

5. **PlayerPawn exclusion**: Regular drop items (step 4) are not spawned if the actor is a `PlayerPawn` or a subclass of it.

## Parameters

None. Unlike the ZDoom/UZDoom/GZDoom-family versions, Zandronum's `A_NoBlocking` takes no optional parameters — it always spawns drop items (step 4 above always happens unless a dialogue-set drop spawned in step 3). The wiki describes an optional `drop` parameter present in upstream engines; **Zandronum does not support this**.

## Drop item behavior

**Dialogue-set vs. regular drops (from the source):** The action prioritizes dialogue-set drops. If both exist, only the dialogue-set item spawns on the current call; the `Conversation` field is cleared, so all subsequent calls spawn regular items instead. If only regular items exist, they spawn again on every call.

**Probability rolls:** The dialogue-set drop is passed a chance of `256` and the item's default amount, so it always drops. Each regular `DropItem` entry rolls against its own probability. See the "Creating monsters" concept page for the verified `DropItem` roll mechanism and the idiom that `256` represents "always drop".

**Spawn position (Zandronum):** `P_DropItem` spawns the item at the actor's position, raised by half the actor's height (or by 24 units under Strife-style drops, `sv_dropstyle 2` or the Strife default), then tosses it. With the `COMPATF_NOTOSSDROPS` compat flag set it spawns at the actor's `z` and is not tossed.

## Network synchronization

**Zandronum multiplayer only.** The `A_Unblock` function (which both `A_NoBlocking` and `A_Fall` call) returns at its first line in client mode (a network client, or client-side demo playback). That skips every step above: stealth handling, the `MF_SOLID` clear, the `Conversation` clear and all drops. `P_DropItem` also refuses to spawn anything in client mode on its own. The server replicates the results instead: the flag clear via `SERVERCOMMANDS_SetThingFlags` (sent only when the flags actually changed), stealth visibility via `SERVERCOMMANDS_FlashStealthMonster`, and each dropped item via `SERVERCOMMANDS_SpawnThing`. There is no `+CLIENTSIDEONLY` exception. `A_Unblock`'s third C++ argument lets engine code run it on a client (the client's handler for the server's "thing is corpse" command does this), but the DECORATE wrappers never set it. Offline play is not client mode, so the action runs normally there.

**Implication:** For actors the server runs (monsters, players, projectiles), clients see the actor become non-solid once the server's flag update arrives. A `+CLIENTSIDEONLY` actor exists only on clients (the server destroys its own copy), so no update ever comes. In multiplayer, calling `A_NoBlocking` from such an actor leaves it solid for good and drops nothing.

## Engine-family divergence: `drop` parameter support

UZDoom's `A_NoBlocking` exposes an optional boolean `drop` parameter defaulting to true. It is declared as a native method in `wadsrc/static/zscript/actors/actor.zs` and thunked via `DEFINE_ACTION_FUNCTION_NATIVE(AActor, A_NoBlocking, A_Unblock)` in `src/scripting/vmthunks_actors.cpp`, which reads the boolean from the DECORATE/ZScript call site and forwards it straight to `A_Unblock`. Calling `A_NoBlocking(false)` skips step 4 above (the regular `DropItem` list) while the `MF_SOLID` clear, stealth handling, and any dialogue-set drop (step 3) still happen unconditionally. `A_Fall` stays a plain ZScript wrapper in `actor.zs` with no parameter of its own; it calls `A_NoBlocking` with no argument, so the default `true` always applies. This confirms — rather than contradicts — what the "Parameters" section above already anticipated from the wiki: UZDoom is exactly the "ZDoom/UZDoom/GZDoom-family" upstream the wiki's optional-parameter description refers to, and it does support it. Zandronum does not: its `DEFINE_ACTION_FUNCTION(AActor, A_NoBlocking)` wrapper (`src/g_shared/a_action.cpp:130-133`) always calls `A_Unblock(self, true)` and never exposes a `drop` parameter to DECORATE, even though the underlying `A_Unblock` C++ function accepts one.

## Engine-family divergence: no client/server authority split

UZDoom's `A_Unblock` (`src/playsim/a_action.cpp:40-82`) unconditionally clears `MF_SOLID` and updates stealth alpha/`visdir` — there is no client-mode gate, and no equivalent of Zandronum's `NETWORK_InClientMode` check or `SERVERCOMMANDS_SetThingFlags`/`SERVERCOMMANDS_FlashStealthMonster` replication calls exists anywhere in the UZDoom source tree. The entire "Network synchronization" section above, and the header's "Zandronum-specific" callout, are therefore Zandronum-only behavior: on UZDoom, `A_NoBlocking`/`A_Fall` take effect immediately and identically regardless of caller or connection role, with no server-replication lag for a client-side actor to catch up on.

## Alternatives

- **`A_ScreamAndUnblock`** — a composite action that calls `A_Scream` followed by `A_Unblock`, used in standard death states (e.g., `A_Scream` plays a sound, then `A_NoBlocking` unblocks and drops items).
- **`+NODROPOFF` actor flag** — affects actor movement constraints, not item drops; see the "Creating monsters" concept for flag bundles.

## Related

- `A_ScreamAndUnblock` — calls `A_Scream` then `A_NoBlocking` in sequence.
- `A_Scream` — plays the actor's death sound without unblocking.
- `A_FreezeDeathChunks` — the shared ice-death action (from Hexen, but callable by any actor and used by the generic ice death) that also unblocks the actor near its end.
- **DECORATE concept:** "Creating monsters" — covers `DropItem`, `Monster` property, and other death-related mechanics.
