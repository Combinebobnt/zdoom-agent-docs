# Multiplayer-safe ZScript

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki "Creating multiplayer-friendly ZScript" (retrieved 2026-08-03, https://zdoom.org/w/index.php?title=Creating_multiplayer-friendly_ZScript&oldid=55402) + verified against UZDoom stdlib in `wadsrc/static/zscript/` for CVar/RNG/scope/event interfaces; re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — no behavioral drift found
**Engine-family note:** The networking architecture described here (packet-server, host redistribution per tick) is specific to UZDoom; mainline GZDoom uses classic peer-to-peer deterministic lockstep instead. Claims about the packet-server model are verified against UZDoom sources only, not cross-checked against GZDoom.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

Multiplayer in UZDoom uses deterministic gameplay logic — every client runs the same code with the same inputs, so all clients should always see the same game state. Desyncs (mismatched game state between clients) occur when code behaves non-deterministically across clients. This guide covers the synchronization model, scoping rules, common desync pitfalls, and how to write prediction-safe player code.

## Deterministic networking and the client-server model

UZDoom uses packet-server networking: each client sends inputs to a host, which collects all inputs for a tick and distributes them back to all clients before the next tick advances. All clients then simulate that tick identically. Because determinism is the only synchronization mechanism, any code path that produces different results on different machines will cause a desync.

A desync means at least two clients no longer agree on the game state — an enemy might be alive on client A but dead on client B. UZDoom marks the affected client as inconsistent and shows a persistent on-screen "Out of sync" indicator once this occurs, but gameplay continues (though broken) — the game does not attempt to resync on its own. The only recovery is to load a save file distributed from the host.

## Scoping: ui, play, data, clearscope

ZScript enforces scoping as a safety mechanism. The three execution contexts are:

- **`play` scope** — runs on every client's machine during the deterministic simulation (once per tick). All clients execute the same code with the same inputs, so `play`-scoped code must be deterministic.
- **`ui` scope** — runs only on each client's own machine, outside the synchronized simulation. Some `ui` entry points (`RenderOverlay()`/`RenderUnderlay()`, `UiProcess()`) run once per render frame; others (`UiTick()`/`PostUiTick()`) run once per elapsed game tic instead, not per frame. `ui`-scoped code is never synchronized either way; for frame-driven `ui` code specifically, if client A renders at 200 FPS and client B at 100 FPS, A executes that code twice as many times per tick as B.
- **`data` scope** — a neutral zone for data storage, readable and writable by both `play` and `ui` without being a communication channel between them. Both scopes can read and write data-scoped fields freely, but coordination across the two scopes via data fields is not allowed (the rule is "read and write data freely, but don't use it to communicate").
- **`clearscope`** — marks a function/method as data-scoped, useful for pure calculators or getters that don't depend on scope-specific state.

The rule: `play` scope cannot read from `ui` scope (and certainly cannot write to it). `ui` scope can read from `play` scope and can call `clearscope`/`data`-scoped functions, but must never modify play-scoped state.

## Common sources of desyncs

### RNG and seed state

Each random seed has a state that advances when a function using that seed is called. If a seed ends up in different states across clients, they will generate different numbers and desynchronize.

**The pitfall:** If client-side code (UI) and play-scoped code both use the same RNG seed, the seed's state will drift — one client's UI code runs at a different frame rate, consuming random numbers at a different rate, so the play-scope RNG state advances differently on each machine.

**The fix:** Use `CRandom` (client-side, per-client RNG) for `ui`-scoped code. Use `Random` (networked RNG, synchronized across clients) for `play`-scoped code. `CRandom` has its own set of unique seed identifiers (`CRandom[MyIdentifier](min, max)`) that do not interact with the networked seeds.

### Using `consoleplayer` in play scope

`consoleplayer` is the player number for the current client — it's 0 on the host, 1 for the first guest, etc. Every client has a different value for `consoleplayer`. Using this value in `play`-scoped code means each client executes different logic and desynchronizes.

**The pitfall:**
```zscript
// Wrong: each client has a different consoleplayer value
let weapon = players[consoleplayer].ReadyWeapon;
```

**The fixes:** Prefer generic actor references over player numbers (use `actor.target` rather than a player index). When a player-specific action must happen, iterate over all players, or use a reference to the player's pawn:

```zscript
// Right: use the actor's player field if it's a player
if (myActor.player)
{
    DoThing(myActor.player.mo);
}

// Right: iterate over all players
PlayerInfo player;
while ((player = PlayerInfo.GetNextPlayer(player)))
{
    DoThing(player.mo);
}
```

### Events with player-specific hooks

Event handlers receive callbacks with arguments naming which player the event is for. The trap: using `consoleplayer` instead of the argument.

**Wrong:**
```zscript
override void PlayerSpawned(PlayerEvent e)
{
    // This uses the local player, not the spawning player
    players[consoleplayer].mo.GiveInventory("Item", 1);
}
```

**Right:**
```zscript
override void PlayerSpawned(PlayerEvent e)
{
    // Use the argument — applies to the correct player on all clients
    players[e.PlayerNumber].mo.GiveInventory("Item", 1);
}
```

Note: `ConsoleProcess()` and `InterfaceProcess()` run in `ui` scope, so using `consoleplayer` in them is safe — they only run locally anyway. For `NetworkProcess()` (play scope), always use the argument.

### CVar handling

`CVar.FindCVar(name)` reads the CVar from the current client's machine only. If two clients have different values for a user CVar, and play-scoped code calls `FindCVar`, each client will get its own value and execute different logic, causing a desync.

**The pitfall:**
```zscript
// Wrong: reads client A's value on A's machine, client B's value on B's machine
let myCVar = CVar.FindCVar("mycvar");
```

**The fix:** Use `CVar.GetCVar(name, PlayerInfo)` and pass the appropriate player's `PlayerInfo`:

```zscript
// Right: gets the specific player's CVar value
let myCVar = CVar.GetCVar("mycvar", owner.player);
```

Server and `nosave` CVars can be accessed directly in ZScript — they are already synchronized (server CVars) or client-local (nosave CVars) without explicit CVar lookups.

### Client-side prediction pitfalls

Client-side prediction allows movement to feel instant by letting the client move their pawn on-screen immediately while waiting for server verification. If the movement is later verified to be wrong, the client is "rubberbanded" back to the correct position.

**The trap:** Logic that modifies anything other than the predicting player's immediate position/state can cause desyncs if called during prediction, because the prediction run on the client won't be replayed on other clients — the change persists locally but doesn't happen elsewhere.

**Unsafe during prediction:**
- Modifying anything in the world (actors, level geometry, play-scoped globals)
- Creating new actors or play-scoped objects
- Triggering map actions or ACS scripts
- Changing the predicting player's state machine (call `SetState()` on a predicting player)
- Modifying objects the player has a reference to (only the reference itself is backed up; the object's state is not)

**Safe during prediction:**
- Modifying fields directly on the predicting player pawn or their `PlayerInfo`
- Changing view-related properties (view angle, zoom, etc.) on the pawn
- Creating client-side objects (`ui`/`data`-scoped, not world-affecting)

**Detection:** Check `if (player.cheats & CF_PREDICTING)` to know whether the current code is executing during prediction. This check only matters in player code; other actors' logic only runs when the client isn't predicting.

**The `CanCollideWith()` exception:** This method must be called during prediction to check collisions correctly, but it can trigger side effects. Guard it:

```zscript
override bool CanCollideWith(Actor other, bool passive)
{
    if (!other.player || !(other.player.cheats & CF_PREDICTING))
    {
        // Safe: only runs if the colliding actor isn't predicting
        DoThing(other);
    }
    return true;
}
```

Both `PlayerThink()` and `Tick()` are called during prediction — do not assume they are safe contexts unless the method's documentation explicitly says it isn't called while predicting (e.g., `TickPSprites()` is not).

## Writing prediction-safe player code

When overriding player logic (especially `PlayerThink()` or `Tick()`):

1. **Do not modify the world state** — avoid creating actors, changing globals, calling play functions with side effects.
2. **Do not change the player's state** — do not call state-change functions on a predicting player.
3. **Do not modify objects via references** — the player's reference to an actor is backed up during prediction, but the actor's state is not. Modifying it will desync.
4. **Guard non-safe operations:**
   ```zscript
   if (!(player.cheats & CF_PREDICTING))
   {
       // Only run outside prediction
       DoRiskyThing();
   }
   ```
5. **Re-apply original safety guards** — if completely overriding `PlayerThink()` or `Tick()`, make sure to replicate the safety logic the original implementation has; it doesn't happen automatically.

## Network events: synchronizing UI changes back to play

To send a message from `ui` scope (menu, HUD) back to the `play` scope (the simulation), use `EventHandler.SendNetworkEvent()`:

```zscript
// In UI code
EventHandler.SendNetworkEvent("myevent");

// In EventHandler, in NetworkProcess (play scope)
override void NetworkProcess(ConsoleEvent e)
{
    if (e.Name ~== "myevent")
    {
        // This runs on all clients, with the player who triggered it in e.Player
        players[e.Player].mo.GiveInventory("Item", 1);
    }
}
```

**Network event best practices:**

- **Avoid sending every tick** — rapid event spam can clog the network buffer and cause VM aborts. If your logic loops per-tick, calculate everyone's state once instead.
- **Use arguments, not strings** — integers are 4 bytes; the string `"123456789"` is 9 bytes. Pass an int argument instead.
- **Keep identifiers short** — event names are sent over the network. A short identifier saves bandwidth.
- **For more complex data, use network commands** — `EventHandler.SendNetworkCommand()` allows fine-grained control over data types and size (int8/16/32, float, double, string).

The reverse direction — sending from `play` to `ui` — uses `EventHandler.SendInterfaceEvent()`:

```zscript
// In play-scoped code (e.g., Actor.Activate())
if (activator && activator.player)
{
    EventHandler.SendInterfaceEvent(activator.PlayerNumber(), "myui");
}

// In UI handler
override void InterfaceProcess(ConsoleEvent e)
{
    if (e.Name ~== "myui")
    {
        // This is UI scope, so consoleplayer is safe here
        DoUIThing(players[consoleplayer].mo);
    }
}
```

See [Event handlers: StaticEventHandler and EventHandler](../classes/eventhandler.md) for the full event system reference, including dispatch order, lifecycle, and all event types.

## Summary checklist

- **`play` scope is deterministic** — the same code with the same inputs produces the same result on every client.
- **`ui` scope is non-deterministic and local** — each client runs it independently.
- **Use `Random` in `play`, `CRandom` in `ui`** — don't mix RNG families.
- **Never use `consoleplayer` in `play` scope** — it's different on every client.
- **Use event arguments, not hardcoded player numbers** — `PlayerEvent.PlayerNumber`, `ConsoleEvent.Player`, etc.
- **Use `CVar.GetCVar(name, player)`, not `FindCVar`** — respect per-player values.
- **Guard player logic against prediction** — check `CF_PREDICTING` and avoid modifying world state during prediction.
- **Send network events for UI→play communication** — avoid direct cross-scope modification.
