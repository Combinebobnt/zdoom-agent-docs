# Event handlers: `StaticEventHandler` and `EventHandler`

**Tier:** B
**Engine:** UZDoom 4.15pre
**Provenance:** ZDoom Wiki "Events and handlers" (retrieved 2026-07-31, oldid=54876) + verified against UZDoom native dispatch code in `src/events.cpp` and the stdlib declaration in `wadsrc/static/zscript/events.zs`.
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

All event handler methods are declared `static` and `clearscope` in the stdlib (despite being instance methods, not class-static — the modifiers govern their calling convention from the engine).

### Registration/initialization

```
void OnRegister() — Called when the handler is registered (added to the handler list).
   Event handler order setup can be performed here; call SetOrder() to specify relative 
   dispatch position.

void OnUnregister() — Called when the handler is unregistered (removed from the list).

void OnEngineInitialize() — Called once, right after engine startup (after messages like CPU 
   information print). StaticEventHandler only.
```

### World lifecycle

```
void WorldLoaded(WorldEvent e) — Called when a level loads. 
   WorldEvent.IsSaveGame is set to true if loading from a saved game.
   (Non-static EventHandlers are skipped if loading from a save game.)
   WorldEvent.IsReopen is set to true if re-entering a hub level.

void WorldUnloaded(WorldEvent e) — Called when a level unloads.
   WorldEvent.NextMap contains the name of the next map, if any.
   (Dispatched in reverse order: last registered handler first.)
```

### Thing spawning/death/destruction

```
void WorldThingSpawned(WorldEvent e) — Called just after an actor spawns or respawns.
   Fired after PostBeginPlay.

void WorldThingDied(WorldEvent e) — Called just before an actor dies.
   WorldEvent.Thing is the actor that died.
   WorldEvent.Inflictor is the actor that caused the damage (may be null).

void WorldThingRevived(WorldEvent e) — Called just after an actor is revived/raised/resurrected.

void WorldThingDestroyed(WorldEvent e) — Called just before an actor is destroyed.
   (Dispatched in reverse order.)

void WorldThingGround(WorldEvent e) — Called when an actor's corpse is crushed into gibs.
   WorldEvent.CrushedState is the crush state the actor entered.
```

### Thing damage

```
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

```
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

```
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

```
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

```
void WorldTick() — Called at the beginning of each game tick (35 times per second).

void WorldLightning() — Called for lightning events, same as LIGHTNING ACS script type.
```

### Player lifecycle

```
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

```
bool UiProcess(UiEvent e) — Receive UI input events (keyboard/mouse).
   Only called if IsUiProcessor is set to true.
   Only receives mouse events if RequireMouse is set to true.
   Returning true blocks further processing by other handlers with lower Order.
   UiEvent fields:
   - EGUIEvent Type: input type (Type_KeyDown, Type_KeyUp, Type_Char, Type_MouseMove, 
     Type_LButtonDown, etc.)
   - KeyScan: internal ASCII value of the key
   - KeyChar: ASCII value for the key
   - KeyString: single-character string of the key
   - MouseX, MouseY: delta offsets from last mouse position (not absolute screen position)
   - IsShift, IsCtrl, IsAlt: modifier keys

bool InputProcess(InputEvent e) — Direct interface to player input (keyboard/mouse).
   No special setup required; called automatically for all handlers.
   Returning true blocks the game input handler, preventing player movement.
   InputEvent fields similar to UiProcess.

void UiTick() — Called at beginning of each tick, in UI context.
   Runs even outside levels (matters for StaticEventHandlers).

void PostUiTick() — Called after all game operations on the given tick, in UI context.
```

### Console/network events

```
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

```
void CheckReplacement(ReplaceEvent e) — Called when actor class replacement happens.
   - ReplaceEvent.Replacee: the actor class being replaced (readonly)
   - ReplaceEvent.Replacement: the replacement class (modifiable)
   - ReplaceEvent.IsFinal: marks replacement as final; other handlers should respect it

void CheckReplacee(ReplacedEvent e) — Called by engine functions like A_BossDeath to check
   if a replacee has been replaced (determines if special completion logic triggers).
   Used for hub map completion checks, e.g. ensuring all Archviles (or their replacements) are dead.
   - ReplacedEvent.Replacee: the original class
   - ReplacedEvent.Replacement: the replacement class (readonly)
   - ReplacedEvent.IsFinal: marks as final
```

### Rendering (UI scope)

```
void RenderOverlay(RenderEvent e) — Called to draw overlay HUD elements (drawn over the HUD).
   RenderEvent fields:
   - Vector3 ViewPos: camera position
   - double ViewAngle, ViewPitch, ViewRoll: camera orientation
   - double FracTic: fractional tick (0.0-1.0) for interpolation
   - Actor Camera: camera actor
   Note: Divergence found — wiki claims reverse-ordered dispatch, but source code shows 
   forward order (FirstEventHandler...next). Handlers registered later execute later 
   (draw on top). Execution is forward-ordered, not reverse.

void RenderUnderlay(RenderEvent e) — Called to draw overlay HUD elements (drawn under the HUD).
   Fields and order same as RenderOverlay.
```

### New game

```
void NewGame() — Called when starting a new game (also called when entering a titlemap,
   or on reborn after death without a saved game).
```

## Handler registration and ordering

Handlers are registered via `SetOrder(int)` in their `OnRegister()` override. The `Order` value
is arbitrary; only relative ordering matters. Default order is 0.

Most events are dispatched in forward order (first-registered handler first). **Reverse-ordered
events** (last-registered first) are:
- `PlayerDisconnected`
- `WorldThingDestroyed`
- `WorldUnloaded`

For render events, the order determines *drawing order*, not receipt order: higher-order handlers
draw last (on top).

## Static event handler methods

All `StaticEventHandler` class methods are declared `static clearscope`, meaning they are
callable without an instance and have restricted scope access:

- `StaticEventHandler Find(Class<StaticEventHandler> type)` — Retrieves a pointer to an existing handler of the given type.

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

**Note on 4.12 networking API:** The `NetworkCommand`, `NetworkBuffer`, `SendNetworkCommand`, `SendNetworkBuffer`, and `NetworkCommandProcess` features were verified to exist in UZDoom 4.15pre but their precise semantics under network conditions (lag, packet loss, order guarantees) were not exhaustively traced. Behavior is described from source inspection; consult the UZDoom source or experimental testing for edge cases.

## Serialization note

`EventHandler` handlers (non-static) are serialized to saved games. Handlers can override virtual
`Serialize()` to control what state persists. Static handlers are never serialized.

## Destruction

Event handlers inherit from `Object` and can be destroyed via `Destroy()`. Caveats:
- Do not call `Destroy()` from within an event callback (processing may continue and cause crashes).
- Non-static handlers are automatically destroyed at map end; static handlers only when the engine shuts down.
- Safe pattern: set a flag in WorldTick and check it, calling `Destroy()` only after the event frame is done.

## Engine-scope note

ZScript does not exist in Zandronum and event handlers are a GZDoom/UZDoom-family feature only.
See `zscript/concepts/zscript-engine-availability.md` for details.
