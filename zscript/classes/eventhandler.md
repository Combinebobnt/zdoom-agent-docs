# Event handlers: `StaticEventHandler` and `EventHandler`

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki "Events and handlers" (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=Events_and_handlers&oldid=54876) + verified against UZDoom native dispatch code in `src/events.cpp` and the stdlib declaration in `wadsrc/static/zscript/events.zs`; re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — the events.zs/events.cpp/events.h/inputevents.zs diff across the pull is a license-header rewrite only (no dispatch/signature drift), so both wiki-divergence corrections still hold; also corrected two pre-existing stdlib signature transcriptions found during re-verification (`WorldLightning` takes a `WorldEvent e` param; `EventHandler.Find`'s declared signature is `class<StaticEventHandler> type` returning `StaticEventHandler`, not `class<EventHandler>`/`EventHandler`), and noted a new internal client-prediction caveat on network-entity ID timing (not a scripted-API change).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** ZScript stdlib (`events.zs`; class/method definitions) and UZDoom native engine (`src/events.cpp`; event dispatch and handler lifecycle).

Event handlers are a plugin-like system allowing ZScript code to receive world, client, and system events. Two base classes are provided: `StaticEventHandler` (initialized at engine startup, lives until engine shutdown) and `EventHandler` (created at map start, destroyed at map end, serializable to saves).

## Design overview

Both `StaticEventHandler` and `EventHandler` classes are virtual-method-based. Each event type is a virtual method override; the engine calls every registered handler's override in order. A handler need not override all events — empty virtual defaults are provided. Calling `Super.EventName()` in an override is unnecessary.

## Event handler lifecycle

**StaticEventHandler:**
- Initialized at GZDoom/UZDoom engine startup
- Destroyed when closing the engine
- Not serializable (does not persist across save/load)
- Registered in MAPINFO's `GameInfo` section via `EventHandlers = "ClassName"` (multiple entries comma-separated or via multiple `EventHandlers` lines; both append)

**EventHandler:**
- Initialized at map start (beginning of every level)
- Destroyed at map end
- Serializable (persisted in saved games)
- Registered per-level in MAPINFO `Map` or per-all-levels in `GameInfo` section

## Methods and lifecycle hooks

**Note on method scope:** The virtual event override methods (WorldLoaded, WorldThingDied, etc.) are declared without `static` or `clearscope`. The methods that *are* static and clearscope are utility functions — `Find()`, `SendNetworkEvent()`, `SendNetworkCommand()`, `SendNetworkBuffer()`, and `SendInterfaceEvent()` — which govern their calling convention from the engine but are not the event-handling overrides.

### Registration/initialization

```text
void OnRegister() — Called when the handler is registered (added to the handler list).
   Event handler order setup can be performed here; call SetOrder() to specify relative 
   dispatch position.

void OnUnregister() — Called when the handler is unregistered (removed from the list).

void OnEngineInitialize() — Called once, right after engine startup (after messages like CPU 
   information print). StaticEventHandler only.
```

### World lifecycle

```text
void WorldLoaded(WorldEvent e) — Called when a level loads. 
   WorldEvent.IsSaveGame is set to true if loading from a saved game (notably, non-static 
   EventHandlers are skipped entirely if loading from a save game, so this field is most useful 
   for StaticEventHandlers).
   WorldEvent.IsReopen is set to true if re-entering a hub level.

void WorldUnloaded(WorldEvent e) — Called when a level unloads.
   WorldEvent.IsSaveGame is set to true if the level is unloading to load a saved game.
   WorldEvent.NextMap contains the name of the next map, if any.
   (Dispatched in reverse order: last registered handler first.)
```

### Thing spawning/death/destruction

```text
void WorldThingSpawned(WorldEvent e) — Called just after an actor spawns or respawns.
   Fired after PostBeginPlay.

void WorldThingDied(WorldEvent e) — Called just before an actor dies.
   WorldEvent.Thing is the actor that died.
   WorldEvent.Inflictor is the projectile/weapon that caused the damage (may be null).
   The actor that killed Thing (the damage source) is accessible via Thing.target after 
   this event fires (it is set to the source parameter of DamageMobj).

void WorldThingRevived(WorldEvent e) — Called just after an actor is revived/raised/resurrected.

void WorldThingDestroyed(WorldEvent e) — Called just before an actor is destroyed.
   (Dispatched in reverse order.)

void WorldThingGround(WorldEvent e) — Called when an actor's corpse is crushed into gibs.
   WorldEvent.CrushedState is the crush state the actor entered.
```

### Thing damage

```text
void WorldThingDamaged(WorldEvent e) — Called when an actor receives damage.
   Arguments are the same as the engine's internal DamageMobj call:
   - WorldEvent.Thing: the actor being damaged
   - WorldEvent.Inflictor: the thing that caused the damage (may be null)
   - WorldEvent.Damage: raw damage before modification
   - WorldEvent.DamageSource: the source of the damage
   - WorldEvent.DamageType: the damage type name
   - WorldEvent.DamageFlags: damage behavior flags (EDmgFlags)
   - WorldEvent.DamageAngle: angle from Inflictor to Thing (may differ from direct angle if portals involved)
```

### Line/sector damage

```text
void WorldLineDamaged(WorldEvent e) — Called before a line takes damage.
   Allows manipulation of damage via Damage (raw) and NewDamage (after modification).
   - WorldEvent.DamageLine: the line
   - WorldEvent.DamageLineSide: which side (0=front, 1=back)
   - Shared fields: DamageSource, Damage, NewDamage, DamageType, DamagePosition, DamageIsRadius

void WorldSectorDamaged(WorldEvent e) — Called before a sector takes damage.
   - WorldEvent.DamageSector: the sector
   - WorldEvent.DamageSectorPart: which part (ceiling/floor/etc.)
   - Shared fields: DamageSource, Damage, NewDamage, DamageType, DamagePosition, DamageIsRadius
```

### Attack pre/post hooks (UZDoom 4.14.0+)

```text
bool WorldHitscanPreFired(WorldEvent e) — Called before any hitscan (non-railgun) attack.
   Returning true blocks the attack from happening.
   - WorldEvent.thing: the attacking actor
   - WorldEvent.AttackAngle, AttackPitch: attack direction
   - WorldEvent.AttackDistance: attack range
   - WorldEvent.damage: damage value
   - WorldEvent.damageType: damage type name
   - WorldEvent.AttackLineFlags: special flags
   - WorldEvent.AttackPuffType: puff actor class
   - WorldEvent.AttackZ, AttackOffsetForward, AttackOffsetSide: position offsets
   Note: only called for "bullet" hitscans, not railguns.

void WorldHitscanFired(WorldEvent e) — Called after a hitscan attack completes.
   - WorldEvent.thing: the attacking actor
   - WorldEvent.AttackPos: position where attack originated
   - WorldEvent.DamagePosition: where the attack landed
   - WorldEvent.Inflictor: the projectile/inflictor (if any)
   - WorldEvent.AttackLineFlags: special flags
   Note: only called for "bullet" hitscans, not railguns.

bool WorldRailgunPreFired(WorldEvent e) — Called before a railgun attack.
   Returning true blocks the attack.
   - WorldEvent.thing, AttackAngle, AttackPitch, AttackDistance, damage, damageType,
     AttackPuffType, AttackZ, AttackOffsetSide: as hitscan, plus
   - WorldEvent.RailParams: FRailParams struct with full rail configuration

void WorldRailgunFired(WorldEvent e) — Called after a railgun attack completes.
   Fields similar to WorldHitscanFired but with railgun-specific context.
   Note: only called for railgun attacks, not regular "bullet" hitscans.
```

### Line activation

```text
void WorldLinePreActivated(WorldEvent e) — Called upon line activation, before the line's 
   special is executed. Allows veto of activation.
   - WorldEvent.Thing: the activating actor
   - WorldEvent.ActivatedLine: the line (readonly)
   - WorldEvent.ActivationType: how it was activated (SPAC_Cross, SPAC_Use, SPAC_MCross,
     SPAC_Impact, SPAC_Push, SPAC_PCross, SPAC_UseThrough, SPAC_AnyCross, SPAC_MUse, SPAC_MPush)
   - WorldEvent.ShouldActivate: set to false to abort activation

void WorldLineActivated(WorldEvent e) — Called after a line's special executes successfully.
   - WorldEvent.Thing, ActivatedLine, ActivationType: as WorldLinePreActivated
   (Note: ActivationType may differ from what triggered it; a line can execute multiple times.)
```

### World tick

```text
void WorldTick() — Called at the beginning of each game tick (35 times per second).

void WorldLightning(WorldEvent e) — Called for lightning events, same as LIGHTNING ACS script type.
```

### Player lifecycle

```text
void PlayerEntered(PlayerEvent e) — Called when a player connects to the game.
   PlayerEvent.PlayerNumber identifies the player.

void PlayerSpawned(PlayerEvent e) — Called when a player spawns in the level (like ENTER ACS script).

bool PlayerRespawning(PlayerEvent e) — Called to determine whether a respawn is allowed.
   Return true to allow respawn (default), false to block it.
   If any handler returns false, respawn is prevented.
   PlayerEvent.IsReturn is set if the player is returning to a hub level.

void PlayerRespawned(PlayerEvent e) — Called after a player respawns (including the resurrect cheat).

void PlayerDied(PlayerEvent e) — Called when a player dies (also triggers WorldThingDied).

void PlayerDisconnected(PlayerEvent e) — Called when a player disconnects.
   (Dispatched in reverse order.)
```

### UI/input events (UI scope)

```text
bool UiProcess(UiEvent e) — Receive UI input events (keyboard/mouse).
   Only called if IsUiProcessor is set to true.
   Only receives mouse events if RequireMouse is set to true.
   Dispatched in reverse order (highest-Order handler first); returning true blocks further
   processing by other handlers with lower Order.
   UiEvent fields:
   - EGUIEvent Type: input type (Type_KeyDown, Type_KeyUp, Type_Char, Type_MouseMove, 
     Type_LButtonDown, etc.)
   - KeyChar: raw key value for the event (interpretation depends on Type; a Unicode code unit
     for Type_Char, not necessarily ASCII)
   - KeyString: single-character string of the key
   - MouseX, MouseY: **absolute screen coordinates in UI space** (not delta offsets; differs from InputProcess)
   - IsShift, IsCtrl, IsAlt: modifier keys
   **Correction:** UiEvent has no `KeyScan` field — that field belongs to InputEvent only (see below).
   A previous pass of this file listed `KeyScan` as a UiEvent field; the native field-binding list
   for UiEvent (`Type`, `KeyString`, `KeyChar`, `MouseX`, `MouseY`, `IsShift`, `IsAlt`, `IsCtrl`) has
   no such member.

bool InputProcess(InputEvent e) — Direct interface to player input (keyboard/mouse).
   No special setup required; called automatically for all handlers.
   Dispatched in the same reverse order as UiProcess (highest-Order handler first).
   Returning true blocks the game input handler, preventing player movement.
   InputEvent is a distinct struct from UiEvent (no modifier-key fields):
   - EGenericEvent Type: input type (Type_KeyDown, Type_KeyUp, Type_Mouse, Type_DeviceChange)
   - KeyScan: scan-code value from the EDoomInputKeys enum (only set for KeyDown/KeyUp)
   - KeyChar: ASCII char value (only set for KeyDown/KeyUp)
   - KeyString: single-character string of the key (only set for KeyDown/KeyUp)
   - MouseX, MouseY: **delta offsets** (only set for Type_Mouse; differs from UiProcess's absolute
     screen coordinates)

void UiTick() — Called at beginning of each tick, in UI context.
   Runs even outside levels (matters for StaticEventHandlers).

void PostUiTick() — Called after all game operations on the given tick, in UI context.
```

### Console/network events

```text
void ConsoleProcess(ConsoleEvent e) — Called when "event" console command is used (UI context).
   ConsoleEvent fields:
   - String Name: event name
   - int Args[3]: three integer arguments

void NetworkProcess(ConsoleEvent e) — Called when network event arrives (from "netevent" command
   or EventHandler.SendNetworkEvent()). Runs in play scope.
   - ConsoleEvent.Player: player number that sent it
   - ConsoleEvent.Name, Args[3]: event name and arguments
   - ConsoleEvent.IsManual: true if sent manually from console

void InterfaceProcess(ConsoleEvent e) — Called for interface events ("interfaceevent" command
   or EventHandler.SendInterfaceEvent()). Runs in UI scope; used for play→UI communication.
   - ConsoleEvent fields: Name, Args[3], IsManual (as NetworkProcess)

void NetworkCommandProcess(NetworkCommand cmd) — Called for network commands sent via
   EventHandler.SendNetworkCommand() or EventHandler.SendNetworkBuffer() (available UZDoom 4.12+).
   NetworkCommand allows sending arbitrary typed data (int8/16/32, float/double, string).
   Call cmd.ReadInt(), cmd.ReadDouble(), cmd.ReadString(), etc. to parse incoming data.
   Also provides Read*Array() methods for array deserialization.
```

### Actor replacement

```text
void CheckReplacement(ReplaceEvent e) — Called when actor class replacement happens.
   - ReplaceEvent.Replacee: the actor class being replaced (readonly)
   - ReplaceEvent.Replacement: the replacement class (modifiable)
   - ReplaceEvent.IsFinal: marks replacement as final; other handlers should respect it
   Note: CheckReplacement runs *before* skill-based replacements and DECORATE/ZScript `replaces`
   keyword replacement chains are applied, but setting Replacement alone does not bypass those
   chains; only setting IsFinal = true does. See "Wiki/engine divergence" below for the
   correction and its citation.

void CheckReplacee(ReplacedEvent e) — Called by engine functions like A_BossDeath to check
   if a replacee has been replaced (determines if special completion logic triggers).
   Used for hub map completion checks, e.g. ensuring all Archviles (or their replacements) are dead.
   - ReplacedEvent.Replacee: the original class
   - ReplacedEvent.Replacement: the replacement class (readonly)
   - ReplacedEvent.IsFinal: marks as final
```

### Rendering (UI scope)

```text
void RenderOverlay(RenderEvent e) — Called to draw overlay HUD elements (drawn over the HUD).
   RenderEvent fields:
   - Vector3 ViewPos: camera position
   - double ViewAngle, ViewPitch, ViewRoll: camera orientation
   - double FracTic: fractional tick (0.0-1.0) for interpolation
   - Actor Camera: camera actor
   **Divergence:** Wiki claims reverse-ordered dispatch (last-registered first), but UZDoom 
   source dispatch iterates forward (FirstEventHandler...next). Handlers registered later 
   execute later (draw on top). Dispatch order is forward, not reverse.

void RenderUnderlay(RenderEvent e) — Called to draw overlay HUD elements (drawn under the HUD).
   Fields and order same as RenderOverlay.
```

### New game

```text
void NewGame() — Called when starting a new game (also called when entering a titlemap,
   or on reborn after death without a saved game).
```

## Handler registration and ordering

Handlers are registered via `SetOrder(int)` in their `OnRegister()` override. The `Order` value
is arbitrary; only relative ordering matters. Default order is 0.

Most events are dispatched in forward order (first-registered handler first, i.e. ascending
`Order`, ties broken by registration order). **Reverse-ordered events** (last-registered/highest-
`Order` handler first) are:
- `PlayerDisconnected`
- `WorldThingDestroyed`
- `WorldUnloaded`
- `UiProcess` and `InputProcess` (**correction:** missing from a previous pass of this list — both
  are dispatched via the same reverse `LastEventHandler`-to-`prev` loop in `EventManager::Responder`
  in `src/events.cpp`)

For render events, the order determines *drawing order*, not receipt order: higher-order handlers
draw last (on top).

## Static event handler methods

All utility methods are declared `static clearscope`, meaning they are callable without an 
instance and have restricted scope access:

- `StaticEventHandler.Find(Class<StaticEventHandler> type)` — Retrieves a pointer to an existing *static* handler of the given type, searching the static-handler list.
- `EventHandler.Find(class<StaticEventHandler> type)` — Same declared signature as the parent's `Find` (param type `class<StaticEventHandler>`, return type `StaticEventHandler`, **not** `class<EventHandler>`/`EventHandler` as might be assumed), but its native implementation searches the current level's per-level handler list instead of the static one. Pass a `class<EventHandler>` subclass (valid, since it widens to `class<StaticEventHandler>`) and cast the result back down, e.g. `EventHandler(EventHandler.Find(MyHandlerClass))`.

## EventHandler-only methods

`EventHandler` extends `StaticEventHandler` and adds:

- `static void SendNetworkEvent(String name, int arg1 = 0, int arg2 = 0, int arg3 = 0)` — Sends
  a network event from UI scope to play scope. Only supports three integer arguments; to pass a
  string, embed it in the event name and use `String.Split()` to extract it on the receiving end.

- `static bool SendNetworkCommand(Name cmd, ...)` — Sends a network command with typed arguments
  (UZDoom 4.12+). Supports variadic argument list: pass pairs of (NET_INT, value), (NET_DOUBLE, value),
  (NET_STRING, value), etc. More efficient than `SendNetworkEvent` for structured data; cannot be
  sent from console.

- `static bool SendNetworkBuffer(Name cmd, NetworkBuffer buffer)` — Sends a pre-built network buffer.
  Allows building complex messages before sending.

- `static void SendInterfaceEvent(int playerNum, string name, int arg1 = 0, int arg2 = 0, int arg3 = 0)` —
  Sends interface event from play scope to UI scope. Pass `consoleplayer` as `playerNum` to notify all clients;
  `net_arbitrator` to notify only the server host. Runs instantly (not networked like game events).

## Properties

All handlers expose:

- `native readonly int Order` — Current dispatch order (set-only in `OnRegister()` via `SetOrder()`).
- `native bool IsUiProcessor` — Set to true to receive `UiProcess` events. Must be set in `OnRegister()`.
- `native bool RequireMouse` — Set to true to receive mouse events in `UiProcess`. Must be set in `OnRegister()`.

## Networking notes

**Scope separation:** Play scope can modify actors and the world; UI scope cannot. Network events bridge the gap.

**EventHandler.SendNetworkEvent vs. SendNetworkCommand:** The old `SendNetworkEvent` allows three integers plus a string-embedded-in-name workaround. The newer `SendNetworkCommand` (4.12+) sends arbitrary typed data more cleanly. Both fire corresponding `NetworkProcess` handlers; they are functionally similar but `SendNetworkCommand` is more flexible.

**Note on 4.12 networking API:** The `NetworkCommand`, `NetworkBuffer`, `SendNetworkCommand`, `SendNetworkBuffer`, and `NetworkCommandProcess` features were verified to exist in UZDoom 4.15pre, and their declarations are unchanged (still present, byte-for-byte, modulo whitespace) as of 5.0.0-pre; their precise semantics under network conditions (lag, packet loss, order guarantees) were not exhaustively traced either time. Behavior is described from source inspection; consult the UZDoom source or experimental testing for edge cases.

## Serialization note

`EventHandler` handlers (non-static) are serialized to saved games; static handlers are never
serialized (see the lifecycle section above). **Correction (2026-08-05):** there is no overridable
`Serialize()` virtual anywhere in the ZScript stdlib — `wadsrc/static/zscript/` has exactly one
declaration containing "Serialize" tree-wide (`Dictionary`'s unrelated string-serialize helper in
`engine/dictionary.zs`), and neither `Object`, `Thinker`, `StaticEventHandler`, nor `EventHandler`
expose one. A previous pass of this file stated a handler "can override virtual `Serialize()` to
control what state persists"; that claim does not check out against the local UZDoom 5.0.0-pre
stdlib and has been removed. Persistence for a non-static `EventHandler`'s own fields instead comes
from the generic per-field reflection mechanism described in
[Custom data in savegames](../concepts/savegame-custom-data.md) — declare a field, don't override
anything, and it's written/restored automatically unless marked `transient`.

## Destruction

Event handlers inherit from `Object` and can be destroyed via `Destroy()`. Caveats:
- Do not call `Destroy()` from within an event callback (processing may continue and cause crashes).
- Non-static handlers are automatically destroyed at map end; static handlers only when the engine shuts down.
- Handlers cannot be recreated with `new` (they require engine-level initialization); destroyed handlers are gone.
- Safe pattern: set a flag in WorldTick and check it, calling `Destroy()` only after the event frame is done, using the `bDESTROYED` flag (inherited from `Object`) as a safety check before destruction.

## Passing objects through networks

As of UZDoom 4.12+, objects can be passed over networks for serialization and retrieval using three methods on `Object`:

- `native clearscope uint GetNetworkID() const` — Returns the network ID of this object. Actors always have networking enabled; non-actors must call `EnableNetworking(true)` first.
- `native play void EnableNetworking(bool enable)` — Enables or disables networking for this object (play scope only). Actors always have networking enabled and cannot be disabled.
- `native clearscope static Object GetNetworkEntity(uint id)` — Retrieves an object by its network ID.

**Caveats:**
- Actor networking is always enabled; non-actor networking is opt-in via `EnableNetworking(true)`.
- IDs are first-come-first-serve; when an object disables networking or is destroyed, its ID becomes eligible for immediate reassignment.
- Network IDs must never be cached as permanent object references — they can change at any moment due to recycling, silently pointing to a different object or becoming invalid.
- **New internal caveat (as of 5.0.0-pre):** network-entity registration/removal is suspended during the engine's internal client-side movement-prediction window (`P_PredictClient`/`P_UnPredictClient` in `src/playsim/p_user.cpp`, gated by `NetworkEntityManager::IsPredicting()`; unrelated to any scripted API — **correction:** a previous pass of this file named these functions `P_PredictPlayer`/`P_UnPredictPlayer`, which do not exist under those names in the current source), so ID assignment/freeing is not immediate for non-client-side objects spawned inside that window — they are flagged and destroyed once prediction ends, not merged into the normal ID pool. Doesn't change the documented API contract for direct `EnableNetworking`/`GetNetworkID`/`GetNetworkEntity` calls.

## Wiki/engine divergence

- **RenderOverlay dispatch order:** Wiki claims last-registered-first (reverse order), but UZDoom source shows forward iteration from FirstEventHandler. Handlers registered later draw on top.
- **UiProcess MouseX/MouseY:** Wiki contains self-contradictory statements (claims both "absolute screen position" and "delta offsets"). UZDoom source confirms they are **absolute screen coordinates in UI space**, not deltas (differs from InputProcess which uses deltas).
- **CheckReplacement priority (correction, 2026-08-15 re-verification pass):** a previous pass of this file claimed that a handler setting `ReplaceEvent.Replacement` alone was "used immediately, bypassing the other mechanisms" (skill-based replacement and the DECORATE/ZScript `replaces` chain). That does not check out against the actor-replacement code path in `PClassActor::GetReplacement` (`src/gamedata/info.cpp`): the caller only takes the immediate-return short-circuit when the *aggregate* `IsFinal` flag CheckReplacement produces is true. If a handler sets `Replacement` without also setting `IsFinal = true`, that value is merely the starting point the skill-based lookup and DECORATE chain run on top of next — and a skill-based replacement, when one is configured for the class, replaces it outright rather than building on it. CheckReplacement genuinely does run *before* those other mechanisms (that half of the original claim holds), but only `IsFinal` controls whether it preempts them.
- **Network prediction caveat function names (correction, 2026-08-15 re-verification pass):** a previous pass of this file named the internal client-side movement-prediction functions `P_PredictPlayer`/`P_UnPredictPlayer`. The current source has no functions under those names; the real functions are `P_PredictClient`/`P_UnPredictClient` in `src/playsim/p_user.cpp`, gating `NetworkEntityManager::IsPredicting()`. The behavioral claim itself (registration/removal suspended during that window) still checks out against `NetworkEntityManager::AddNetworkEntity`/`RemoveNetworkEntity`/`DisablePrediction` in `src/common/objects/dobject.cpp`.
- **UiEvent.KeyScan (correction, 2026-08-15 re-verification pass):** a previous pass of this file listed `KeyScan` as a `UiEvent` field. The native field-binding list for `UiEvent` in `src/common/engine/d_event.cpp` (`Type`, `KeyString`, `KeyChar`, `MouseX`, `MouseY`, `IsShift`, `IsAlt`, `IsCtrl`) has no such member; `KeyScan` belongs to `InputEvent` only. The reverse-ordered-events list under "Handler registration and ordering" was also missing `UiProcess`/`InputProcess`, which dispatch through the same reverse `LastEventHandler`-to-`prev` loop (`EventManager::Responder` in `src/events.cpp`) as the three events already listed there.

## Engine-scope note

ZScript does not exist in Zandronum and event handlers are a GZDoom/UZDoom-family feature only.
See `zscript/concepts/zscript-engine-availability.md` for details.
