# `A_RadiusGive(class<Inventory> itemtype, int distance, int flags [, int amount = 0])`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_RadiusGive` (retrieved 2026-07-31, oldid=52881) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:5833-6002` and `wadsrc/static/actors/constants.txt:174-189`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_RadiusGive)` at `src/thingdef/thingdef_codeptr.cpp:5863`.

Gives inventory items to all eligible actors within a specified radius. Unlike `A_GiveToTarget` (which targets a single actor), `A_RadiusGive` operates on a region of space and returns a CustomInventory state-chain success code (not an item count).

## Parameters

- **`itemtype`** — the inventory item class to give. This must be a valid class derived from `Inventory`.
- **`distance`** — the search radius around the calling actor's position. A value of 0 or less causes the function to do nothing. The range check is a **3D sphere** based on actor center points (`z + height/2` on both source and target), so targets directly above or below qualify if within range.
- **`flags`** — bitfield determining which actors are eligible to receive items. At least one eligibility flag must be set, or the function does nothing. See "Eligibility flags" below.
- **`amount`** — how many of the item to give to each qualifying recipient. Default is `0`, which is internally treated as `1`. If the item is a `Health` subclass, the amount is multiplied by the item's own `Amount` property; otherwise it is set directly. Can be negative to remove items instead.

## Eligibility flags

| Flag | Bit | Effect |
|---|---|---|
| `RGF_GIVESELF` | 0 | The calling actor itself is eligible. Always succeeds; is not subject to filtering, distance, or line-of-sight checks. |
| `RGF_PLAYERS` | 1 | Player-controlled actors (where `actor->player` is non-NULL and the player is not spectating) are eligible. |
| `RGF_MONSTERS` | 2 | Actors with the `MF3_ISMONSTER` flag are eligible. |
| `RGF_OBJECTS` | 3 | Shootable or vulnerable objects (where `flags & MF_SHOOTABLE` or `flags6 & MF6_VULNERABLE`) are eligible, excluding players and monsters. |
| `RGF_VOODOO` | 4 | Voodoo dolls — player-controlled actors where the actor is **not** the player's body (`actor->player->mo`) — are eligible. |
| `RGF_CORPSES` | 5 | Dead actors carrying the `MF_CORPSE` flag are eligible. Unrelated to the `MF6_KILLED` state. |
| `RGF_NOTARGET` | 6 | Exclude the calling actor's current target from receiving items. |
| `RGF_NOTRACER` | 7 | Exclude the calling actor's tracer from receiving items. |
| `RGF_NOMASTER` | 8 | Exclude the calling actor's master from receiving items. |
| `RGF_CUBE` | 9 | Use a **cube-shaped** region instead of a sphere for the range check. Cube half-width equals `distance`. |
| `RGF_NOSIGHT` | 10 | Give items regardless of line-of-sight. By default, `P_CheckSight` is required. |
| `RGF_MISSILES` | 11 | Missile actors (where `flags & MF_MISSILE`) are eligible. **When this flag is set, the search changes from a blockmap-based `FBlockThingsIterator` (used for all other flags) to a whole-level `TThinkerIterator`, so range is not bounded for missiles.** |

## Zandronum-specific: feature divergence from wiki

The wiki describes ZDoom behavior. Zandronum's implementation has several notable gaps:

- **Parameters not supported:** The wiki documents optional `filter` (actor class), `species`, `mindist`, and `limit` parameters. Zandronum's declaration (in `wadsrc/static/actors/actor.txt`) only accepts four parameters: `itemtype`, `distance`, `flags`, `amount`. Attempting to pass additional arguments will fail to compile.

- **Flags not implemented:** The wiki lists `RGF_KILLED`, `RGF_INCLUSIVE`, `RGF_EXFILTER`, `RGF_EXSPECIES`, and `RGF_ITEMS` flags. Zandronum does not define these; using them will fail at compile time as unknown identifiers. Specifically, there is no way to target inventory items themselves in Zandronum — all `MF_SPECIAL` actors are unconditionally skipped at the start of the iteration loop.

- **Return value behavior:** The wiki states "CustomInventory actors can set success or failure of an item's reception" by checking the return value. In Zandronum, `A_RadiusGive` does not call `ACTION_SET_RESULT`, so the CustomInventory state-chain result field retains its default initialization value (`true`/success) regardless of whether any items were actually given. This means a CustomInventory cannot distinguish between "items were given" and "no eligible recipients were found" using the return value. (The actual inventory impact still occurs on the server regardless of the result flag.)

- **Second wiki example inapplicable:** The wiki's second example uses DECORATE anonymous action blocks (`{ ... }`) and `return state(...)` control flow. These are ZScript-only features unavailable in Zandronum's DECORATE dialect. See [The state-machine model](../concepts/state-machine.md) for Zandronum's DECORATE-only state syntax.

## Server-side and network behavior

**This is server-authoritative.** On clients:

- **For client-handled actors** (marked with `MF6_CLIENTSIDE` or similar), the function runs and gives items locally.
- **For all other actors**, the function returns immediately without giving items. The server separately syncs inventory changes to clients via the engine's netcode.

Spectating players (where `player->bSpectating` is true) are explicitly excluded from the `RGF_PLAYERS` eligibility check, even if the actor has a non-NULL `player` pointer.

## Item delivery mechanics

Each qualifying actor receives a freshly spawned copy of the item (`Spawn(itemtype, ...)`), with `MF_DROPPED` set and counters cleared before `CallTryPickup` is called. This means:

- The item does not count toward item-collection statistics (`AInventory::ClearCounters()`).
- The actual pickup attempt respects the item's `MaxAmount` inventory limit (enforced by `CallTryPickup`).
- A failed pickup (e.g., due to `MaxAmount`) destroys the temporary spawned copy.

## Use cases

Common applications include:
- **Healing area effects:** a projectile or temporary object giving health items to nearby allies.
- **Ammo redistribution:** a dead actor giving ammo to other monsters before exploding.
- **Temporary powerups:** granting temporary invincibility or speed to nearby eligible actors.

## Related functions

- `A_GiveToTarget` — gives items to the calling actor's target (single actor, different implementation).
- `A_GiveInventory` — gives items to the calling actor itself.
- `A_TakeInventory` — removes items.
