# ZScript virtual functions and override dispatch

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki "ZScript virtual functions" (retrieved 2026-08-03, https://zdoom.org/w/index.php?title=ZScript_virtual_functions&oldid=55213) + spot-checked against the UZDoom source's `wadsrc/static/zscript/doombase.zs` and `actors/` class definitions; re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — damage-pipeline virtuals gained trailing flags/angle params (see inline note); no semantic changes to lifecycle, morph, weapon, or powerup virtuals.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

Virtual functions in ZScript are methods designed for inheritance purposes, allowing child classes to override them with their own implementation while optionally calling `Super.<method>()` to invoke the parent's version. This enables polymorphic behavior and controlled extension of engine-provided class behavior.

## Virtual function mechanism

A method is declared `virtual` to permit overriding:

```zscript
class MyActor : Actor
{
    virtual void MyMethod()
    {
        // Base implementation
        a++;
    }
}

class MyDerivedActor : MyActor
{
    override void MyMethod()
    {
        b++;
        Super.MyMethod();  // Calls parent version
    }
}
```

Calling `Super.<methodname>()` executes the parent class's version of that method. Through chaining, every class in the inheritance hierarchy can contribute behavior if each override calls `Super`.

### Abstract virtual functions

Abstract virtual functions have no body (code) and exist only in abstract classes. Child classes must override them:

```zscript
class Base abstract
{
    abstract int MyFunc();
}

class Derived : Base
{
    override int MyFunc()
    {
        return 1;
    }
}
```

Attempting to instantiate a class with unoverridden abstract methods is a compile-time error (unless the derived class is also abstract). **Calling an abstract function via `Super` is a script error.**

## Scope qualifiers: `virtual` vs. `virtualscope` vs. `clearscope`

Most game-affecting virtual functions are declared `virtual native` (engine-provided, called from the engine on its tic/frame lifecycle):

- `virtual` — standard override target, can call engine functions and modify game state.
- `virtualscope` — overrides are restricted to their class's scope (play/ui/data). Cannot access members of other scopes even if the parent can. Used for event handlers and UI-aware virtuals; the calling code (the engine) manages scope enforcement.
- `clearscope` — returns a value without side effects on game state; safe to call from both play and ui scope. Used for query methods like `GetMaxHealth()`.

## Actor lifecycle virtuals

The following virtuals are called at specific points in an actor's lifetime, in sequence:

### BeginPlay → PostBeginPlay → Tick

**`void BeginPlay()`** — Called immediately after an actor is spawned, before the very first `Tick()`.

**`void PostBeginPlay()`** — Called after `BeginPlay()` but before the first `Tick()`, and before the first state is reached. Useful for one-time initialization (e.g., setting local variables) without worrying about the actor being dormant initially and triggering `Deactivate()` instead of `Spawn()` state entry. Inherited from `Thinker`.

**`void Tick()`** — Called every tic (35 times per second) for the lifetime of the actor. This is where most per-tic behavior (AI, animation, collision checks) happens. Inherited from `Thinker`.

**`void OnLoad()`** — Called every time the thinker is loaded from a save game (deserialized). Added in UZDoom 4.14.2. Inherited from `Thinker`.

### Activation and deactivation

**`void Activate(Actor activator)`** — Called when an actor is activated (e.g., via a linedef action, use button, or script call). The specific semantics depend on the actor's flags and type.

**`void Deactivate(Actor activator)`** — Called when an actor is deactivated. Again, exact behavior is flag/type dependent.

### Damage and death

**`int DoSpecialDamage(Actor target, int damage, Name damagetype, int flags = 0, double angle = 0)`** — Called by a projectile *before* hitting another actor, allowing the projectile to modify or prevent damage. Return value is used as the modified damage amount. Called *before* the target's `TakeSpecialDamage()`.

**`int TakeSpecialDamage(Actor inflictor, Actor source, int damage, Name damagetype, int flags = 0, double angle = 0)`** — Called on the *target* when about to take damage (after all damage modifiers are applied). Return value is the new damage amount to actually take.

*As of UZDoom 5.0.0-pre, the whole damage-pipeline family — the virtuals `DoSpecialDamage`, `TakeSpecialDamage`, `ModifyDamage`, `AbsorbDamage`, plus the non-virtual native helper `GetModifiedDamage` that drives `ModifyDamage`/`AbsorbDamage` internally — carries trailing `int flags = 0, double angle = 0` params (the same `flags`/`angle` that were passed into the triggering `DamageMobj` call). For the four virtuals, an override must restate the full parameter list to compile, including these trailing params — a pre-5.0.0-pre override written with the shorter signature will fail to compile as an `override`, even though the params are defaulted. `GetModifiedDamage` itself is `native` but not `virtual` and cannot be overridden; its signature grew the same trailing params purely to pass them through. The engine's own base implementations of `DoSpecialDamage`/`TakeSpecialDamage` ignore both params entirely; they exist only so a `Super.DoSpecialDamage()`/`Super.TakeSpecialDamage()` call from within an override stays parameter-consistent, not because the base behavior uses them.*

**`void Die(Actor source, Actor inflictor, int dmgflags = 0, Name MeansOfDeath = 'none')`** — Called when the actor is killed (health <= 0).

### Collision and movement

**`bool CanCollideWith(Actor other, bool passive)`** — Called on both actors involved when two actors are about to collide. If either returns `false`, the collision does not occur. The `passive` flag indicates which actor is moving (non-passive) vs. stationary (passive).

**`void CollidedWith(Actor other, bool passive)`** — Called on both actors after a collision has been confirmed. Used for collision side effects.

**`bool CanCrossLine(Line crossing, Vector3 next)`** — Called when an actor attempts to cross a linedef (requires the actor to have the `CROSSLINECHECK` flag). Returning `false` blocks the crossing.

**`bool Slam(Actor victim)`** — Called when an actor with `SKULLFLY` set collides with another. Returning `true` tells the engine to skip standard collision code for this victim; returning `false` uses standard behavior.

**`void FallAndSink(double grav, double oldfloorz)`** — Called during falling and sinking in deep water (with `Transfer_Heights` special or swimmable 3D floors). The `grav` parameter is the current gravity; `oldfloorz` is the sector's floor Z coordinate.

### Inventory and item interaction

**`bool CanTouchItem(Inventory item)`** — Called when an actor touches an item but has not yet picked it up. Returning `false` prevents pickup.

**`bool CanReceive(Inventory item)`** — Called before other checks when trying to pick up an item. Returning `false` rejects it.

**`void HasReceived(Inventory item, class<Inventory> itemcls = null)`** — Called at the end of item pickup, after the item has been added to inventory. (Doc previously omitted the defaulted `itemcls` param; pre-existing gap, not related to the 5.0.0-pre pull.)

**`void AddInventory(Inventory item)`** — Called to add an item to the actor's inventory.

**`void RemoveInventory(Inventory item)`** — Called to remove an item from the actor's inventory.

**`bool UseInventory(Inventory item)`** — Called to use an item. Returning `true` means the item was used successfully.

**`void ClearInventory()`** — Called to destroy all valid inventory items.

### Special interactions

**`bool Used(Actor user)`** — Called when an actor (with the `SPECIAL` flag) is used by a player. Returning `true` means it was used; `false` means it wasn't.

**`bool CanResurrect(Actor other, bool passive)`** — Called on both the dead actor and its resurrecter before resurrection. If either returns `false`, resurrection is blocked.

**`bool SpecialBlastHandling(Actor source, double strength)`** — Called when an actor is about to be blasted by a disc of repulsion. Returning `false` prevents the blast; `true` uses standard behavior.

**`int SpecialMissileHit(Actor victim)`** — Called when a missile hits an actor, after all other collision checks. The return value determines what the missile does next: `1` continues traveling, `-1` dies, etc.

**`int SpecialBounceHit(Actor bounceMobj, Line bounceLine, readonly<SecPlane> bouncePlane, bool is3DFloor = false)`** — Called when a bouncing projectile collides with an actor, line, or plane. (Doc previously omitted `readonly<>` and the defaulted `is3DFloor` param; pre-existing gap, not related to the 5.0.0-pre pull.)

**`void Touch(Actor toucher)`** — Called on an actor (with `SPECIAL` flag) when touched by another. Normally used by inventory and spectral monsters.

### Morphing

**`bool Morph(Actor activator, class<PlayerPawn> playerClass, class<Actor> monsterClass, int duration, EMorphFlags style, ...)`** — Called when a morph is initiated. Returning `true` means the morph succeeded.

**`bool Unmorph(Actor activator, EMorphFlags flags = 0, bool force = false)`** — Called when unmorph is initiated. (Source spells it `Unmorph`, not `UnMorph`; ZScript identifiers are case-insensitive so this made no functional difference, but the doc previously used the wrong case. Pre-existing gap, not related to the 5.0.0-pre pull.)

**`bool CheckUnmorph()`** — Called every tic while morphed to check if the actor should revert.

**`bool MorphMonster(Class<Actor> spawnType, int duration, EMorphFlags style, ...)`** — Monster-specific morph function.

**`bool UndoMonsterMorph(bool force = false)`** — Monster-specific unmorph function.

**`void PreMorph(Actor mo, bool current)`** — Called on both the original and morph actors right before morphing.

**`void PostMorph(Actor mo, bool current)`** — Called on both actors right after morphing.

**`void PreUnmorph(Actor mo, bool current)`** — Called on both actors right before unmorphing.

**`void PostUnmorph(Actor mo, bool current)`** — Called on both actors right after unmorphing.

**`Actor, int, int MorphedDeath()`** — Called when an actor dies while morphed. Return values are no longer used in modern UZDoom.

### Death and obituary

**`string GetObituary(Actor victim, Actor inflictor, Name mod, bool playerattack)`** — Returns the obituary message for an actor's death.

**`string GetSelfObituary(Actor inflictor, Name mod)`** — Returns the obituary when an actor kills itself (UZDoom development version f1e6445+).

**`int GetGibHealth()`** — Returns the health threshold at which the actor gibs on death.

**`double GetDeathHeight()`** — Returns the height the actor assumes when dead (accounts for special deaths).

### Blood and damage effects

**`class<Actor> GetBloodType(int type)`** — Returns the class type for blood spawning. Type 0 = standard blood, 1 = splatters, 2 = axe blood.

**`void SpawnLineAttackBlood(Actor attacker, Vector3 bleedpos, double SrcAngleFromTarget, int originaldamage, int actualdamage)`** — Called to spawn blood from a hitscan attack.

**`void ApplyKickback(Actor inflictor, Actor source, int damage, double angle, Name mod, int flags)`** — Called to thrust the actor from an attack.

**`int DamageMobj(Actor inflictor, Actor source, int damage, Name mod, int flags = 0, double angle = 0)`** — Called whenever the actor takes damage. Return value is the actual damage taken.

**`int OnDrain(Actor victim, int damage, Name dmgtype)`** — Called when this actor is draining health from another. Return value is the amount to actually drain.

### Other actor virtuals

**`bool ShouldSpawn()`** — Called at spawn time to determine whether the actor should actually enter the level. Returning `false` prevents spawn.

**`bool Grind(bool items)`** — Called when the actor is crushed. Returning `true` uses standard crushing behavior. The `items` flag indicates whether dropped items should be crushed too.

**`bool OkayToSwitchTarget(Actor other)`** — Called on an actor that's been damaged, to check if it should switch its target. Returning `false` prevents the switch.

**`void MarkPrecacheSounds()`** — Called to cache sound variables for faster access during play.

**`bool OnGiveSecret(bool printmsg, bool playsound)`** — Called when the actor discovers a secret. Returning `false` suppresses the default message.

**`bool PreTeleport(Vector3 destpos, double destangle, int flags)`** — Called before teleporting. Returning `false` blocks the teleport.

**`void PostTeleport(Vector3 destpos, double destangle, int flags)`** — Called after teleport completes.

**`void PlayerLandedMakeGruntSound(Actor onmobj)`** — Called when a player lands on this actor.

## PlayerPawn lifecycle virtuals

`PlayerPawn` has its own set of virtuals, many of which are called every tic as part of player input/think processing. **Caution:** Overriding player virtuals can cause desyncs in networked games if you modify behavior that affects client prediction. Only override if you fully understand the implications.

**Tic-level callbacks (called every tic):**

- **`void PlayerThink()`** — Called every tic before anything else. Handles all player checks and movement.
- **`void HandleMovement()`** — Handles movement functions for the current tic.
- **`void MovePlayer()`** — Actually moves the player based on button input.
- **`void CheckWeaponChange()`** — Checks for pending weapon changes.
- **`void TickPSprites()`** — Handles player weapon sprite animation.
- **`void CalcHeight()`** — Calculates view height offset (e.g., bobbing while running).
- **`void CheckCheats()`** — Handles cheat input (flying, noclipping).
- **`bool CheckFrozen()`** — Checks freeze flags and returns frozen state. (Doc previously misdeclared this `void`; pre-existing gap, not related to the 5.0.0-pre pull.)
- **`void CheckCrouch(bool totallyfrozen)`** — Handles crouch input and state.
- **`void CrouchMove(int direction)`** — Handles view height changes during crouch/uncrouch.
- **`void CheckJump()`** — Handles jump input and logic.
- **`void CheckMoveUpDown()`** — Handles up/down flight movement.
- **`void CheckPitch()`** — Updates pitch based on input.
- **`void CheckFOV()`** — Handles FOV transitions (zooming).
- **`void DeathThink()`** — Called every tic while dead.
- **`void CheckUndoMorph()`** — Checks if the player should unmorph.
- **`void CheckPoison()`** — Applies poison damage and effects (Hexen).
- **`void CheckDegeneration()`** — Checks health degeneration if over max.
- **`void CheckAirSupply()`** — Checks underwater air supply.
- **`double, double TweakSpeeds(double forward, double side)`** — Modifies movement speeds based on items/properties.

**State and animation:**

- **`void PlayIdle()`** — Sets the player to spawn state when stopped.
- **`void PlayRunning()`** — Sets the player to see state when moving.
- **`void PlayAttacking()`** — Sets missile state during primary attack.
- **`void PlayAttacking2()`** — Sets melee state during secondary attack or muzzle flash.
- **`void FireWeapon(State stat)`** — Called when primary fire is triggered.
- **`void FireWeaponAlt(State stat)`** — Called when alt fire is triggered.

**Morphing:**

- **`void MorphPlayerThink()`** — Called every tic while morphed.
- **`void ActivateMorphWeapon()`** — Called on the morph actor to give morph-appropriate weapon.
- **`bool MorphPlayer(PlayerInfo activator, Class<PlayerPawn> spawnType, ...)`** — Initiates player morph.
- **`bool UndoPlayerMorph(PlayerInfo activator, ...)`** — Reverts player morph.

**Spawning and initialization:**

- **`void OnRespawn()`** — Called when the player respawns.
- **`void GiveDefaultInventory()`** — Called to give starting inventory.
- **`void GiveDeathmatchInventory()`** — Called to give deathmatch-specific starting items.

**Item and cheat interactions:**

- **`void CheatGive(String name, int amount)`** — Called when the `give` cheat is used.
- **`void CheatTake(String name, int amount)`** — Called when the `take` cheat is used.
- **`void CheatSetInv(String strng, int amount, bool beyond)`** — Called when the `setinv` cheat is used.
- **`String CheatMorph(class<PlayerPawn> morphClass, bool quickundo)`** — Called when `morphme` cheat is used.
- **`void CheatTakeWeaps()`** — Takes away non-wimpy weapons.

**Weapon and item queries:**

- **`Weapon PickWeapon(int slot, bool checkammo)`** — Called to pick a weapon from a slot.
- **`Weapon PickNextWeapon()`** — Gets the next weapon.
- **`Weapon PickPrevWeapon()`** — Gets the previous weapon.
- **`int GetTeleportFreezeTime()`** — Returns how many tics to freeze after teleporting.

**Rendering and UI:**

- **`Vector2 BobWeapon(double ticfrac)`** — Called every frame to calculate weapon bob offset.
- **`clearscope color GetPainFlash() const`** — Returns the pain flash color.

**Travel (hub/map transitions):**

- **`void PreTravelled()`** — Called before traveling to a new map.
- **`void Travelled()`** — Called after arriving in a new map.

**Other:**

- **`bool CanCrouch() const`** — Checks if crouch is possible.
- **`bool ResetAirSupply(bool playgasp = true)`** — Resets drowning state.

## Inventory lifecycle virtuals

**Pickup and ownership:**

- **`Inventory CreateCopy(Actor other)`** — Called from `CallTryPickup()` to determine whether to directly pick up the item or create a copy (for respawning).
- **`bool TryPickup(in out Actor toucher)`** — Called when an actor tries to pick up the item.
- **`bool CanPickup(Actor toucher)`** — Checks if the actor can pick up based on class type.
- **`bool TryPickupRestricted(in out Actor toucher)`** — Called when `CanPickup` is false but `INVENTORY.RESTRICTABSOLUTELY` flag is not set.
- **`bool HandlePickup(Inventory item)`** — Called on existing inventory items when a new item is being picked up.
- **`void DoPickupSpecial(Actor toucher)`** — Called when an item is picked up to activate special behavior.
- **`void AttachToOwner(Actor other)`** — Called the first time an item is picked up by an owner.
- **`void DetachFromOwner()`** — Called when the item is removed from inventory.

**Dropping and respawning:**

- **`Inventory CreateTossable(int amt = -1)`** — Called when the item is being dropped; returns the item to toss.
- **`bool ShouldStay()`** — Checks if the item should remain after being picked up (for respawning).
- **`bool ShouldRespawn()`** — Checks if the item should respawn.
- **`void Hide()`** — Called when a respawning item is hidden.
- **`void DepleteOrDestroy()`** — Called when amount reaches 0; determines if item should stay or be destroyed.
- **`void DepleteBy(int by)`** — Called every time an item is drained (UZDoom development version 9c383e9+).

**Usage and effects:**

- **`bool Use(bool pickup)`** — Called when the item is used. Returning `true` means it was used successfully.
- **`void UseAll(Actor user)`** — Called when using "use all inventory items" key.
- **`void DoEffect()`** — Called every tic if the item has an owner (for continuous effects like powerups).
- **`void OwnerDied()`** — Called when the item's owner dies.

**Damage modification:**

- **`void ModifyDamage(int damage, Name damageType, out int newdamage, bool passive, Actor inflictor = null, Actor source = null, int flags = 0, double angle = 0.0)`** — Called before damage is applied to the owner, to allow modification (e.g., PowerDamage). Not called if `DMG_NO_ENHANCE` flag is set. Gained the trailing `angle` param in UZDoom 5.0.0-pre (see the damage-pipeline note under "Damage and death") — existing overrides must add it to their signature to keep compiling as an `override`.
- **`void AbsorbDamage(int damage, Name damageType, out int newdamage, Actor inflictor = null, Actor source = null, int flags = 0, double angle = 0.0)`** — Called after `ModifyDamage()` to allow further modification (e.g., armor). Not called if `DMG_NO_PROTECT` flag is set. Same UZDoom 5.0.0-pre `angle` addition as `ModifyDamage()`.

**Queries:**

- **`String PickupMessage()`** — Returns the pickup message string. Default returns `PickupMsg`.
- **`double GetSpeedFactor()`** — Returns the speed modifier applied to the owner (players only).
- **`bool GetNoTeleportFreeze()`** — Returns whether the owner should skip teleport freeze.
- **`color GetBlend()`** — Returns the screen blend color (mainly for powerups).

**Special effects and sounds:**

- **`void PlayPickupSound(Actor toucher)`** — Called when picked up (if not `QUIET` flag); plays pickup sound.
- **`bool SpecialDropAction(Actor dropper)`** — Called when dropping the item; returning `true` prevents default drop. (Doc previously misdeclared this `void`; pre-existing gap, not related to the 5.0.0-pre pull.)
- **`void OnDrop(Actor dropper)`** — Called after drop completes.
- **`void ModifyDropAmount(int dropamount)`** — Modifies the amount when dropping.
- **`void SetGiveAmount(Actor receiver, int amount, bool givecheat)`** — Called when an item is being given via cheat or code.
- **`ui void AlterWeaponSprite(VisStyle vis, in out int changed)`** — Allows direct modification of weapon sprite visuals (ui-scoped).

**Map travel:**

- **`void PreTravelled()`** — Called before carrying the item to a new map.
- **`void Travelled()`** — Called after arriving on a new map.

## Weapon virtuals

**Slot and state queries:**

- **`int, int CheckAddToSlots()`** — Called at level load for weapons without a defined slot. Returns slot number and priority (multiplied by 65536).
- **`State GetReadyState()`** — Returns the weapon's ready state.
- **`State GetUpState()`** — Returns the select state (when becoming current weapon).
- **`State GetDownState()`** — Returns the deselect state (when being lowered).
- **`State GetAtkState(bool hold)`** — Returns the fire state (or hold state if `hold` is true).
- **`State GetAltAtkState(bool hold)`** — Returns the altfire state (or althold state if `hold` is true).

**Sound and powerup:**

- **`void PlayUpSound(Actor origin)`** — Plays the upSound when becoming current.
- **`void EndPowerup()`** — Called when Tome of Power expires.

**Ammunition and firing:**

- **`bool CheckAmmo(int fireMode, bool autoSwitch, bool requireAmmo = false, int ammocount = -1)`** — Checks if weapon has enough ammo to fire or switch to.
- **`bool DepleteAmmo(bool altFire, bool checkEnough = true, int ammouse = -1, bool forceammouse = false)`** — Consumes ammo on attack. (Doc previously omitted the trailing defaulted `forceammouse` param; pre-existing gap, not related to the 5.0.0-pre pull.)

**Bob and rendering (ui-scoped):**

- **`ui Vector2 ModifyBobLayer(Vector2 bob, int layer, double ticfrac)`** — Modifies weapon bob offset for a sprite layer.
- **`ui Vector3, Vector3 ModifyBobLayer3D(Vector3 Translation, Vector3 Rotation, int layer, double ticfrac)`** — Modifies 3D model weapon bob.
- **`ui Vector3 ModifyBobPivotLayer3D(int layer, double ticfrac)`** — Modifies 3D model pivot point.

## Powerup virtuals

- **`virtual void InitEffect()`** — Called when the powerup becomes active.
- **`virtual void EndEffect()`** — Called when the powerup expires.
- **`virtual clearscope TextureID GetPowerupIcon() const`** — Returns the icon drawn on screen.
- **`virtual clearscope bool isBlinking() const`** — Returns true if the powerup is blinking (nearly expired).

## Event handler virtuals

`StaticEventHandler` has numerous virtuals for responding to world, player, input, and render events — see the `eventhandler` class documentation for details on their dispatch order and scopes.

## Known divergences and implementation notes

- The wiki correctly documents virtual function semantics and class membership. However, not all wiki examples have been exhaustively traced against source — focus has been on verifying existence, signature, and basic call site for frequently-used virtuals (Actor lifecycle, PlayerPawn think cycle, Inventory pickup).
- Some virtuals like `OnLoad()` were added in mid-version releases (4.14.2+); verify version requirements in source or release notes before assuming availability.
- Scope qualifiers (`virtual`, `virtualscope`, `clearscope`) are not always visible in the wiki; verify against source for scope-sensitive code.
