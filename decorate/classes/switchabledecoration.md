# `SwitchableDecoration`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** ZDoom Wiki Classes:SwitchableDecoration (retrieved 2026-07-29, https://zdoom.org/w/index.php?title=Classes%3ASwitchableDecoration&oldid=54551) + verified against
Zandronum source `src/g_shared/a_action.cpp:25-53` (class definition) and `src/p_mobj.cpp:5229-5267` (base-class Activate/Deactivate behavior).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** native C++ class in Zandronum (`src/g_shared/a_action.cpp:27-64`; `ASwitchableDecoration : public AActor`, `ASwitchingDecoration : public ASwitchableDecoration`); ZScript class in UZDoom (`wadsrc/static/zscript/actors/shared/sharedmisc.zs:210-229`; `class SwitchableDecoration : Actor`, `class SwitchingDecoration : SwitchableDecoration`).

A built-in actor class that toggles between two state sequences, `Active` and `Inactive`, when activated or deactivated via map specials (`Thing_Activate` / `Thing_Deactivate` line actions) or ACS functions (`Thing_Activate` / `Thing_Deactivate`).

## State requirements and missing-state behavior

A `SwitchableDecoration` subclass must declare at least a `Spawn` state and an `Active` state. An `Inactive` state is optional (required only if the actor is to be switched off as well).

**Critical: missing state behavior (Zandronum).** If `Activate()` is called when no `Active` state exists, `FindState()` returns NULL. `SetState(NULL)` (`src/p_mobj.cpp:513-521`) then calls `HideOrDestroyIfSafe()` (`src/p_mobj.cpp:619-648`), causing the actor to be hidden (in Zandronum's map-reset game modes, i.e. `GAMEMODE_GetCurrentFlags() & GMF_MAPRESETS`, for a level-spawned actor not running client-side) or permanently destroyed (`Destroy()`, in every other case). Similarly, if `Deactivate()` is called with no `Inactive` state, the same destruction/hiding occurs. The wiki's statement "a valid Inactive state is needed if the actor is to be switchable off" is accurate but understates the consequence: forgetting the state doesn't merely leave the actor unchanged — it removes it from the game (or, on Zandronum with map resets active, hides it until the next reset). See "Engine-family divergence: missing-state destroy behavior" below for how this differs on UZDoom.

## Engine-family divergence: missing-state destroy behavior

UZDoom's `AActor::SetState` (`src/playsim/p_mobj.cpp:868-873`) handles a NULL target state differently: it clears the actor's `state` field and calls `Destroy()` outright, returning false — an unconditional destroy, with no hide-and-restore branch. `HideOrDestroyIfSafe()` does not exist anywhere in the UZDoom source (confirmed by search), and neither does the "map-reset game mode" concept it depends on (`GMF_MAPRESETS`) — both are Zandronum-only.

Practical consequence: a level-spawned `SwitchableDecoration` (or `SwitchingDecoration`) missing its `Active`/`Inactive` state behaves differently across engines when the missing transition is triggered. On Zandronum, whether it's temporarily hidden (survivable, restored on the next map reset) or permanently destroyed depends on the current game mode's `GMF_MAPRESETS` flag and whether the actor was level-spawned. On UZDoom, the outcome is always the same regardless of game mode: the actor is destroyed outright, with no hide/restore path at all. A subclass built to rely on Zandronum's "missing state just hides it, come back after the round" behavior will lose the actor permanently if run on UZDoom.

## Override behavior: how `SwitchableDecoration` differs from base `AActor`

The `SwitchableDecoration` class overrides the base `AActor::Activate()` and `AActor::Deactivate()` methods to call `SetState()` unconditionally. The base-class implementations, by contrast:

- **Only apply to monsters** (check for `MF3_ISMONSTER` flag).
- **Manage the `MF2_DORMANT` flag** (base Activate clears it; base Deactivate sets it) to gate which activation/deactivation is allowed next.
- **Fall back to `tics = 1` or `tics = -1`** if the target state is missing, leaving the actor alive in the current state rather than destroying it.

`SwitchableDecoration` bypasses all three of these behaviors: it works on any actor class (not just monsters), never touches `MF2_DORMANT`, and — on Zandronum — calls `HideOrDestroyIfSafe()` when the target state is missing (see "Engine-family divergence: missing-state destroy behavior" above for the UZDoom equivalent, an unconditional `Destroy()`). The result is an actor class suitable for decorations and one-way switches that isn't constrained to the monster-centric base-class semantics.

## Engine-family divergence: `Activate`/`Deactivate` override dispatch

On Zandronum, `AActor::Activate`/`Deactivate` (`src/p_mobj.cpp:5229,5249`) are plain C++ virtual methods with no DECORATE-level override point — a DECORATE actor definition can't supply its own body for either. They're still ordinary C++ virtuals, though, so a real set of native classes override them directly, `SwitchableDecoration`/`SwitchingDecoration` among them: `ScriptedMarine`, `AmbientSound`, `SecretTrigger`, `SoundSequence`, `PathFollower`, `ActorMover`, `SoundEnvironment`, `ParticleFountain`, `MapMarker`, `Spark`, `SectorAction`, `DynamicLight`, `ThrustFloor`, and `ZBell` also do (verified by grepping every `::Activate`/`::Deactivate` definition and declaration in the Zandronum source) — at least sixteen classes total, not a short, easily-enumerable handful. Every other actor class, including any DECORATE-only definition, gets the base `AActor` implementation described above unless it inherits from one of these.

On UZDoom, the same call is routed through `AActor::CallActivate`/`CallDeactivate` (`src/playsim/p_mobj.cpp:5856,5901`), which checks `IFVIRTUAL(AActor, Activate)`/`IFVIRTUAL(AActor, Deactivate)` against the actor's actual ZScript class before falling back to the native default — an open-ended runtime lookup, not a fixed list at all. `SwitchableDecoration`/`SwitchingDecoration` reach the engine as ordinary `override void Activate/Deactivate` ZScript methods through that same path, alongside UZDoom's ZScript counterparts of most of the Zandronum list above plus anything a mod author cares to add on top. The practical difference for this class specifically is narrower than it might first look: Zandronum already treats `SwitchableDecoration` as one of a genuine double-digit set of native override exceptions, not a rare special case — the real difference is that Zandronum's set is fixed at compile time in engine C++ source, while UZDoom's is open to any ZScript actor a mod defines.

## Activation control and the `activationtype` field

An actor's `activationtype` field, set at map time (via the `Activation` property in DECORATE) or through ACS, carries these relevant bits:

- `THINGSPEC_Activate` — actor is currently eligible to be activated.
- `THINGSPEC_Deactivate` — actor is currently eligible to be deactivated.
- `THINGSPEC_Switch` — sets the complementary flag after each call (one-way on, one-way off, or toggle depending on the flag set).

**These bits gate the call on one path but not the other.** When a player uses (`MF5_USESPECIAL`) or bumps (`MF6_BUMPSPECIAL`) the actor, `P_ActivateThingSpecial` checks `THINGSPEC_Activate`/`THINGSPEC_Deactivate` before deciding whether to call `Activate()` or `Deactivate()` at all — here the flags are a genuine gate. But the ACS action specials `Thing_Activate`/`Thing_Deactivate` don't consult it: `DoActivateThing`/`DoDeactivateThing` call `Activate()`/`Deactivate()` on every matched actor unconditionally, regardless of `activationtype`, and only use the `THINGSPEC_Activate`/`Deactivate`/`Switch` bits as bookkeeping — clearing/flipping them so the actor's *next* USESPECIAL/BUMPSPECIAL trigger goes the other way. A `SwitchableDecoration` subclass activated/deactivated via ACS therefore always runs its override; only the USESPECIAL/BUMPSPECIAL path actually gates on `activationtype`. This split holds on both engines — `DoActivateThing`/`DoDeactivateThing` and `P_ActivateThingSpecial` are structurally the same on UZDoom (`src/playsim/p_lnspec.cpp:1399-1419`; `src/playsim/p_map.cpp:7233-7288`) as on Zandronum. **In neither case does `activationtype` change *which* method is called** — it's always `Activate()` or `Deactivate()` matching the caller, never something else.

## Network synchronization: `IsActive()` state transmission

`SwitchableDecoration` defines a `IsActive()` method that returns `!InState(NAME_Inactive)` — effectively, any state other than `Inactive` is considered "active." In multiplayer games, Zandronum uses this method to synchronize the dormant/active state when a client joins mid-game: the server checks `IsActive()` for every actor during the connection snapshot (`src/sv_main.cpp:2929-2937`) and sends `SERVERCOMMANDS_ThingDeactivate()` to the client if the actor is not active, ensuring late-joiners see the correct state initially.

This specific mechanism is Zandronum-specific: UZDoom has no `AActor::IsActive()` at all — the only `IsActive()` anywhere in the UZDoom source belongs to `ADynamicLight` (`src/playsim/a_dynlight.h:237`, an unrelated GPU light-culling flag with no connection to actor activation state). There is consequently no `IsActive()`-keyed activation-state sync for `SwitchableDecoration` on UZDoom the way there is on Zandronum; whether UZDoom's own (structurally different) netcode replicates actor state to late joiners through some other mechanism entirely wasn't traced as part of this entry.

---

## `SwitchingDecoration`

`SwitchingDecoration` is a variant that inherits from `SwitchableDecoration` and overrides `Deactivate()` with an empty function body, making it a one-way switch: the actor can be activated (transitions to `Active` state) but cannot be deactivated (the `Deactivate()` method does nothing). It's used for toggle switches and single-use decorative elements.

`SwitchingDecoration` is declared as a native DECORATE class on Zandronum (`wadsrc/static/actors/shared/sharedmisc.txt:134-136`) and as an ordinary ZScript class on UZDoom (`wadsrc/static/zscript/actors/shared/sharedmisc.zs:224-229`). It's the parent class of several Hexen decorations — `ZGemPedestal`, `ZWingedStatueNoSkull`, etc. — declared in `wadsrc/static/actors/hexen/hexenspecialdecs.txt` on Zandronum and `wadsrc/static/zscript/actors/hexen/hexenspecialdecs.zs` on UZDoom.

## See also

- [The state-machine model](../concepts/state-machine.md) — DECORATE state syntax, label resolution, and special state names like `Active` and `Inactive`.
- [Actor definition syntax](../concepts/actor-definition-syntax.md) — `ACTOR` keyword and inheritance syntax.
- `Thing_Activate` / `Thing_Deactivate` line actions and `Thing_Activate()` / `Thing_Deactivate()` ACS functions (see the root `acs/INDEX.md` and `console/INDEX.md` for links).
