# `SwitchableDecoration`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki Classes:SwitchableDecoration (retrieved 2026-07-29, oldid=54551) + verified against
Zandronum source `src/g_shared/a_action.cpp:25-53` (class definition) and `src/p_mobj.cpp:5229-5267` (base-class Activate/Deactivate behavior).
**Bucket:** `src/g_shared/a_action.cpp` (native C++ class `ASwitchableDecoration : public AActor`).

A built-in actor class that toggles between two state sequences, `Active` and `Inactive`, when activated or deactivated via map specials (`Thing_Activate` / `Thing_Deactivate` line actions) or ACS functions (`Thing_Activate` / `Thing_Deactivate`).

## State requirements and missing-state behavior

A `SwitchableDecoration` subclass must declare at least a `Spawn` state and an `Active` state. An `Inactive` state is optional (required only if the actor is to be switched off as well).

**Critical: missing state behavior.** If `Activate()` is called when no `Active` state exists, `FindState()` returns NULL. The actor then calls `HideOrDestroyIfSafe()`, causing the actor to be hidden (in map-reset game modes) or permanently destroyed (in standard modes). Similarly, if `Deactivate()` is called with no `Inactive` state, the same destruction/hiding occurs. The wiki's statement "a valid Inactive state is needed if the actor is to be switchable off" is accurate but understates the consequence: forgetting the state doesn't merely leave the actor unchanged — it removes it from the game.

## Override behavior: how `SwitchableDecoration` differs from base `AActor`

The `SwitchableDecoration` class overrides the base `AActor::Activate()` and `AActor::Deactivate()` methods to call `SetState()` unconditionally. The base-class implementations, by contrast:

- **Only apply to monsters** (check for `MF3_ISMONSTER` flag).
- **Manage the `MF2_DORMANT` flag** (base Activate clears it; base Deactivate sets it) to gate which activation/deactivation is allowed next.
- **Fall back to `tics = 1` or `tics = -1`** if the target state is missing, leaving the actor alive in the current state rather than destroying it.

`SwitchableDecoration` bypasses all three of these behaviors: it works on any actor class (not just monsters), never touches `MF2_DORMANT`, and calls `HideOrDestroyIfSafe()` when the target state is missing. The result is an actor class suitable for decorations and one-way switches that isn't constrained to the monster-centric base-class semantics.

## Activation control and the `activationtype` field

Activation is gated by an actor's `activationtype` field, which can be set at map time (via the `Activation` property in DECORATE) or through ACS. The field's bits govern **when** `Activate()` and `Deactivate()` can be called:

- `THINGSPEC_Activate` — actor can be activated.
- `THINGSPEC_Deactivate` — actor can be deactivated.
- `THINGSPEC_Switch` — sets the complementary flag after each call (one-way on, one-way off, or toggle depending on the flag set).

When a map special or ACS calls `Thing_Activate` or `Thing_Deactivate`, the engine checks these flags before calling the virtual method. A `SwitchableDecoration` subclass inherits these gates, so the instance-level `activationtype` value controls whether the actor responds to activation commands at all. **The `activationtype` field does not change which virtual method is called** — both `Activate()` and `Deactivate()` are called unchanged if the gate permits.

## Network synchronization: `IsActive()` state transmission

`SwitchableDecoration` defines a `IsActive()` method that returns `!InState(NAME_Inactive)` — effectively, any state other than `Inactive` is considered "active." In multiplayer games, Zandronum uses this method to synchronize the dormant/active state when a client joins mid-game: the server checks `IsActive()` for every actor during the connection snapshot and sends `SERVERCOMMANDS_ThingDeactivate()` to the client if the actor is not active, ensuring late-joiners see the correct state initially.

---

## `SwitchingDecoration`

`SwitchingDecoration` is a variant that inherits from `SwitchableDecoration` and overrides `Deactivate()` with an empty function body, making it a one-way switch: the actor can be activated (transitions to `Active` state) but cannot be deactivated (the `Deactivate()` method does nothing). It's used for toggle switches and single-use decorative elements.

`SwitchingDecoration` is declared in the engine's DECORATE (`wadsrc/static/actors/shared/sharedmisc.txt`) and is the parent class of several Hexen decorations (`ZGemPedestal`, `ZWingedStatueNoSkull`, etc., in `wadsrc/static/actors/hexen/hexenspecialdecs.txt`).

## See also

- [The state-machine model](../concepts/state-machine.md) — DECORATE state syntax, label resolution, and special state names like `Active` and `Inactive`.
- [Actor definition syntax](../concepts/actor-definition-syntax.md) — `ACTOR` keyword and inheritance syntax.
- `Thing_Activate` / `Thing_Deactivate` line actions and `Thing_Activate()` / `Thing_Deactivate()` ACS functions (see the root `acs/INDEX.md` and `console/INDEX.md` for links).
