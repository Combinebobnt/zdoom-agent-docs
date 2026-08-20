# `A_RadiusGive(class<Inventory> itemtype, int distance, int flags [, int amount = 0])`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `A_RadiusGive` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_RadiusGive&oldid=52881) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:5833-6002` and `wadsrc/static/actors/constants.txt:174-189`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_RadiusGive)` at `src/thingdef/thingdef_codeptr.cpp:5863`.

Gives inventory items to all eligible actors within a specified radius. Unlike `A_GiveToTarget` (which targets a single actor), `A_RadiusGive` operates on a region of space and returns a CustomInventory state-chain success code (not an item count).

## Parameters

- **`itemtype`** — the inventory item class to give. This must be a valid class derived from `Inventory`.
- **`distance`** — the search radius around the calling actor's position. A value of 0 or less causes the function to do nothing. The range check is a **3D sphere** based on actor center points (`z + height/2` on both source and target), so targets directly above or below qualify if within range.
- **`flags`** — bitfield determining which actors are eligible to receive items. At least one eligibility flag must be set, or the function does nothing. See "Eligibility flags" below.
- **`amount`** — how many of the item to give to each qualifying recipient. Default is `0`, which is internally treated as `1`. If the item is a `Health` subclass, the amount is multiplied by the item's own `Amount` property; otherwise it is set directly. **A negative value does not reliably "remove items instead":** for `Health` subclasses it routes through the Strife heal path, where a negative `Amount` is treated as a positive healing percentage (e.g. `-100` means heal 100%) — it heals, it doesn't remove. For ordinary stackable items, a negative give against a stack that's already at `MaxAmount` (and `sv_unlimited_pickup` unset) is a no-op; when it does apply, there's no floor-at-zero clamp, so the stack can be driven negative.

## Eligibility flags

| Flag | Bit | Effect |
|---|---|---|
| `RGF_GIVESELF` | 0 | The calling actor itself is eligible. **On Zandronum, self is still subject to the ordinary eligibility chain** — classification (`RGF_MONSTERS`/`RGF_PLAYERS`/etc. still gates a self-caller the same as any other candidate), the `MF_SPECIAL`/corpse/dead checks, distance, and line-of-sight all apply; `A_RadiusGive(Item, 128, RGF_GIVESELF)` alone from a monster gives nothing. **On UZDoom, self bypasses classification and filter/species**, but distance and sight checks still run against it (self's Z is offset by half its own height for the distance test, so a tall caller with a small `distance` can still fail its own check). Neither engine makes `RGF_GIVESELF` unconditional. |
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
| `RGF_MISSILES` | 11 | Missile actors (where `flags & MF_MISSILE`) are eligible. **When this flag is set, the search changes from a blockmap-based `FBlockThingsIterator` (used for all other flags) to a whole-level `TThinkerIterator`** — but range is still fully bounded: the per-candidate cube/sphere distance test runs unconditionally on every actor the iterator yields, missiles included, on both engines. Only the coarse pre-filter changes; nothing outside `distance` (or the cube half-width) can ever qualify. |

## Zandronum-specific: feature divergence from wiki

The wiki describes ZDoom behavior. Zandronum's implementation has several notable gaps:

- **Parameters not supported:** The wiki documents optional `filter` (actor class), `species`, `mindist`, and `limit` parameters. Zandronum's declaration (in `wadsrc/static/actors/actor.txt`) only accepts four parameters: `itemtype`, `distance`, `flags`, `amount`. Attempting to pass additional arguments will fail to compile.

- **Flags not implemented:** The wiki lists `RGF_KILLED`, `RGF_INCLUSIVE`, `RGF_EXFILTER`, `RGF_EXSPECIES`, and `RGF_ITEMS` flags. Zandronum does not define these; using them will fail at compile time as unknown identifiers. Specifically, there is no way to target inventory items themselves in Zandronum — all `MF_SPECIAL` actors are unconditionally skipped at the start of the iteration loop.

- **Return value behavior:** The wiki states "CustomInventory actors can set success or failure of an item's reception" by checking the return value. In Zandronum, `A_RadiusGive` does not call `ACTION_SET_RESULT`, so the CustomInventory state-chain result field retains its default initialization value (`true`/success) regardless of whether any items were actually given. This means a CustomInventory cannot distinguish between "items were given" and "no eligible recipients were found" using the return value. (The actual inventory impact still occurs on the server regardless of the result flag.)

- **Second wiki example inapplicable:** The wiki's second example uses DECORATE anonymous action blocks (`{ ... }`) and `return state(...)` control flow. These are ZScript-only features unavailable in Zandronum's DECORATE dialect. See [The state-machine model](../concepts/state-machine.md) for Zandronum's DECORATE-only state syntax.

## Engine-family divergence: full wiki parameter/flag set, a real return value, and an asymmetric range check

UZDoom's `A_RadiusGive` (`src/playsim/p_actionfunctions.cpp`, `DEFINE_ACTION_FUNCTION(AActor, A_RadiusGive)` and its `DoRadiusGive` helper) differs from what's documented above in several real ways:

- **No client/server gate at all.** The function has no `NETWORK_InClientMode`-style early return and never calls a `SERVERCOMMANDS_*` sync function anywhere — grepping the entire UZDoom source tree for both turns up zero matches. It runs to completion identically on every machine; the "Server-side and network behavior" section below is Zandronum-only and does not apply to UZDoom.
- **`RGF_PLAYERS` does not exclude spectators.** The eligibility check is a bare `thing->player->mo == thing`, with no `bSpectating` test — the "and the player is not spectating" clause in the Eligibility flags table above is Zandronum-specific.
- **Full 8-parameter signature, matching the wiki.** UZDoom's real declaration is `A_RadiusGive(class<Inventory> itemtype, double distance, int flags, int amount = 0, class<Actor> filter = null, name species = "None", double mindist = 0, int limit = 0)`. The four extra parameters the "Zandronum-specific" section above says the wiki documents but Zandronum's declaration omits are all present and functional on UZDoom:
  - `filter` — an actor class; only actors of this class are eligible (`RGF_EXFILTER` flips this to an exclusion instead).
  - `species` — a species name; only actors of this species are eligible (`RGF_EXSPECIES` flips this to an exclusion instead).
  - `mindist` — a minimum-distance floor excluding anything closer; the call is rejected outright if `mindist >= distance`.
  - `limit` — caps the number of successful gives per call; `0` or negative means unlimited.
  - By default both the filter and species checks must pass; `RGF_EITHER` (bit 17) relaxes this to pass if either one matches.
- **New eligibility flags are implemented**, in contrast to the "Zandronum-specific" section's note that using them fails to compile there: `RGF_ITEMS` (bit 13) makes world/dropped `Inventory` actors themselves eligible recipients — the opposite of Zandronum's blanket skip of every `MF_SPECIAL` actor; `RGF_KILLED` (bit 14) makes actors carrying `MF6_KILLED` eligible independently of the `MF_CORPSE` check `RGF_CORPSES` uses; `RGF_INCLUSIVE` (bit 12) changes how `RGF_NOTARGET`/`RGF_NOTRACER`/`RGF_NOMASTER` combine, from "excluded if it matches any one flagged pointer role" to "excluded only if it matches every flagged pointer role that's set."
- **The return value is a real recipient count the CustomInventory state chain consumes, not a fixed success code.** UZDoom's action returns `given`, the actual number of actors the item was successfully given to (`ACTION_RETURN_INT(given)`), and `ACustomInventory::CallStateChain` (same file) ORs that int directly into the chain's running success result. A `Pickup` state chain calling this action genuinely succeeds only when at least one recipient received the item, and fails when none did. This contradicts both the top-of-file description ("returns a CustomInventory state-chain success code (not an item count)") and the "Zandronum-specific" section's claim that the result can't distinguish "gave" from "no recipients" — both statements are true of Zandronum only.
- **The 3D range check uses an asymmetric Z origin, unlike Zandronum's center-to-center check.** The Eligibility flags table above states the sphere/cube check compares `z + height/2` on both source and target — true for Zandronum, not for UZDoom. UZDoom's fine-grained check computes the difference vector as `thing->PosRelative(self) - self->Pos()`, where `Pos()` is an actor's base/origin Z (its own separate `Center()` accessor is what adds `Height/2`), then adds only the *target's* `Height * 0.5`. The result compares the target's center to the source's base, not center-to-center — a tall calling actor's effective vertical origin for both the sphere and (since `RGF_CUBE`'s `dz` reuses the same difference) the cube check sits `Height/2` lower than it would on Zandronum. This also disagrees with UZDoom's own coarse pre-filter, which builds its search volume around `self->Center()` — the fine check and the volume feeding it don't agree on the source's Z origin, which reads as an unintentional inconsistency rather than a deliberate design choice.
- **Non-missile iteration is portal-aware and fully 3D.** Zandronum's non-missile branch uses a flat, 2D `FBlockThingsIterator` bounded by an X/Y `FBoundingBox`, enforcing the Z distance by hand afterward. UZDoom's uses `FMultiBlockThingsIterator` with `FPortalGroupArray::PGA_Full3d`, which correctly traverses line/sector portals in three dimensions — actors reachable only through a portal can be found by `A_RadiusGive` on UZDoom but not on Zandronum, which has no comparable portal system.

## Server-side and network behavior

**This is server-authoritative.** On clients:

- **For client-handled actors** (the real predicate is `(pActor->NetworkFlags & NETFL_CLIENTSIDEONLY) || (pActor->NetID == 0)`, `src/network.cpp` — the `+CLIENTSIDEONLY` DECORATE actor flag, or any actor with no network ID; **`MF6_CLIENTSIDE` does not exist in Zandronum**), the function runs and gives items locally.
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
