# DECORATE doc index

Router only — one line per documented action function/family/class/inventory table. Read a target
file only when you need it. See `AGENTS.md` for engine-source buckets and layout, `../shared/
AUTHORING.md` for tiers/engine-scope/licensing.

## Concepts

- [Actor definition syntax](concepts/actor-definition-syntax.md) — tier A. The top-level `actor
  classname [: parent] [replaces X] [doomednum] [native] { }` grammar, the `replaces`/doomednum
  semantics (Zandronum's `[-1, 32767]` doomednum range check), comments, and `#include`.
- [The state-machine model](concepts/state-machine.md) — tier A. `States { }` block/label
  grammar, state-line syntax (sprite/frames/duration/flags/action), **special sprite-name tokens**
  (`TNT1`/`----`/`####` vs. the unrelated `#` frame character), duration semantics (`-1`/`0`/
  `RANDOM`, and why Zandronum rejects expression/constant durations the current wiki shows),
  `Goto`/`Stop`/`Wait`/`Fail`/`Loop` (including `Stop`'s Zandronum-specific hide-vs-destroy branch
  on map-reset game modes), label scoping/inheritance and the generic dotted-label partial-match
  fallback, a verified-vs-not-found reserved-label-name list, multi-frame single-line expansion,
  and parser quirks. Flags several ZScript-only features (anonymous action blocks, `return`,
  `FindState`/`ResolveState`, `self.tics`) as **not available** in Zandronum's DECORATE. A few
  narrower claims remain open questions pending further source tracing (see the file's own list).
- [Creating monsters](concepts/creating-monsters.md) — tier A. What the `Monster` property bundles
  (`MF_SHOOTABLE`/`MF_COUNTKILL`/`MF_SOLID` + cross-word flags), required states (Spawn/See/
  Melee-or-Missile and the action functions each must call), optional states (Pain/Death/XDeath/
  Raise), monster-specific properties (Health/Radius/Height/Speed/PainChance/Mass/sounds/
  Obituary/DropItem — including the verified `DropItem` probability-roll mechanism and why `256`
  is a legitimate "always drop" idiom, not an error), and recipes for shootable decorations and
  sound-triggered non-hostile actors as `Monster`-property alternatives.
- [Creating player classes](concepts/creating-player-classes.md) — tier A. Defining a player
  class by inheriting from `PlayerPawn`/`DoomPlayer`, the `Player.*` property set (DisplayName,
  ColorRange, StartItem, WeaponSlot, etc.), registering via MAPINFO's `PlayerClasses` key,
  `+NOMENU`, and the deprecated KEYCONF `addplayerclass` path. **Key fork divergence from the
  wiki**: Zandronum selects a player class via the `playerclass` userinfo cvar at spawn/respawn in
  multiplayer, not through the wiki's single-player new-game menu flow.
- [Inheritance](concepts/inheritance.md) — tier A. How property/flag defaults are copied
  (not looked up) at class-creation time so a multi-level chain resolves correctly, `SKIP_SUPER`'s
  reset-to-`AActor`-defaults behavior and its three caveats (ordering, inventory exception, state
  labels untouched), automatic species determination by walking `MF3_ISMONSTER` ancestors, and
  `replaces`/doomednum as two independent, non-inherited mechanisms. **Key fork divergence**:
  same-species monsters do **not** automatically avoid hurting each other with projectiles in
  Zandronum — that requires the explicit `MF6_DONTHARMSPECIES` flag, contrary to the wiki's
  "automatic" framing. Cross-references `state-machine.md` for state-label inheritance rather
  than duplicating it.
- [Creating weapons](concepts/creating-weapons.md) — tier A. Weapon-specific reserved states
  (`Ready`/`Select`/`Deselect`/`Fire`/`Hold`/`AltFire`/`AltHold`/`Flash`/`AltFlash`) and their
  `GetAtkState`/`GetAltAtkState` fallback semantics, the two-layer `ps_weapon`/`ps_flash` PSprite
  model, weapon properties (`SelectionOrder`, `AmmoGive`/`AmmoUse`/`AmmoType` and their unnumbered
  aliases, `SlotNumber`), `A_Raise`/`A_Lower`'s fixed `FRACUNIT*6` per-call increment, and
  `A_CheckReload`'s auto-switch behavior. Flags an internal inconsistency in the wiki's own Flash
  example (a firing action wrongly shown in the Flash state) that the wiki's own prose
  contradicts.
- [Creating projectiles](concepts/creating-projectiles.md) — tier A. The `Projectile` flag
  bundle, required Spawn/Death states, the Crash→XDeath→Death impact-state selection cascade,
  verified `GetMissileDamage` randomization formula (`((rand&7)+1)*Damage` normally,
  `((rand&3)+1)*Damage` for `MF4_STRIFEDAMAGE`), homing projectiles via `A_Tracer2` and a
  externally-assigned `tracer` field, and fixed-lifespan projectiles via a non-looping `Spawn:`
  plus the `RANDOMIZE` flag's verified 0–3 tic subtraction.
- [Constants (`const`/`enum`)](concepts/constants.md) — tier A. DECORATE's `const`/`enum` is a
  real, engine-parsed language construct (`ParseConstant`/`ParseEnum` in `thingdef_parse.cpp`),
  **not** a `#define` preprocessor the way ACS/BCS's constants are — DECORATE has no `#define` at
  all. `const` is restricted to `int`/`float`; `enum` auto-increments from 0 with `= value`
  overrides. See [`../acs/concepts/constants.md`](../acs/concepts/constants.md) for the unrelated
  ACS/BCS mechanism and [`../shared/concepts/constants.md`](../shared/concepts/constants.md) for
  why the two shouldn't be assumed to work alike.
- [Crash-and-bug checklist](concepts/crash-and-bug-checklist.md) — tier A. **Read this
  before/during a DECORATE code review.** Checklist-style index of verified, recurring
  crash/bug-causing patterns: a "looks risky but verified safe" `A_Chase` pointer path,
  wiki-documented `CHF_*` flags that don't exist in the Zandronum engine fork and silently no-op, and three
  reviewable `A_Jump`/`A_JumpIf*` network-synchronization footguns (RNG inside a non-`A_Jump`
  condition, a `+CLIENTSIDEONLY` actor's jump outcome given non-cosmetic weight, exact-tic
  assumptions on networked position/LOS/inventory state) each with its concrete fix inlined, not
  just linked out.
- [Jump functions and network synchronization](concepts/network-jump-synchronization.md) — tier B.
  Why `A_Jump`/`A_JumpIf*` tick on both server and client, the three recurring causes of
  server/client behavioral divergence in this family (RNG rolled before the network gate,
  networked state read before it catches up, `+CLIENTSIDEONLY` actors' RNG never being expected to
  match across machines), and four concrete strategies for structuring a randomized/conditional
  jump to avoid each one.
- [Expressions](concepts/expressions.md) — tier A. Numeric expressions in action parameters and
  dynamic contexts; operator precedence; literals, identifiers, and actor variables accessible in
  expressions; built-in functions (`random`, `frandom`, `random2`, `abs`, `sqrt`, `sin`, `cos`,
  `checkclass`, `ispointerequal`, `ACS_NamedExecuteWithResult`/`CallACS`). Flags several ZScript-
  only extensions (`crandom`/clientside RNG, dot-member access like `pos.x`, `exp`/`log`/`min`/
  `max`/`ceil`/`floor`/etc.) and per-engine-missing actor variables (`roll`, `threshold`,
  `species`, ...) as **not available** in Zandronum DECORATE.
- [User variables](concepts/user-variables.md) — tier A. Declaring custom integer fields on actors
  (`var int user_<name>` syntax, arrays supported); Zandronum's `int`-only type restriction vs. the
  wiki's float support; reading via DECORATE expressions; modification via `A_SetUserVar`/
  `A_SetUserArray` or ACS functions (all gated on the `bUserVar` flag, not just type); the verified
  Weapon/CustomInventory `self`/`stateowner` calling convention and a newly-documented read-side
  type-confusion bug when a user variable is declared on the Weapon/item class itself instead of
  the player pawn/receiver.
- [Position change during pickup touch](concepts/position-change-during-pickup-touch.md) — tier A.
  A `Pickup:` chain that moves the toucher (e.g. via ACS `SetActorPosition`) has that change
  silently overwritten when the touch was triggered by walking into the item — `P_TryMove` caches
  its destination coordinates before the nested touch runs and unconditionally restores them
  afterward, independent of whether the pickup succeeds or fails. Does not apply to `Use:`.
- [Using a `Powerup` subclass as an inert countdown timer](concepts/powerup-as-inert-timer.md) —
  tier B. The `Speed 1.0` `PowerSpeed`-as-timer trick for gating `A_JumpIfInventory` checks on a
  self-expiring duration with zero gameplay side effects; the three side-effect channels (speed
  trail, HUD icon, screen blend) that must each be closed independently; giving it directly with
  `A_GiveInventory` instead of a `PowerupGiver` wrapper.
- [Custom damage types](concepts/custom-damage-types.md) — tier A. Assigning `DamageType` to
  projectiles and puff actors; creating type-specific `Pain.<Type>`, `Death.<Type>`, `Wound.<Type>`,
  and `Crash.<Type>` states including extreme-death variants; `PainChance` per type; `DamageFactor`
  precedence (specific type > global `DefaultFactor` > untyped fallback); declaring damage types
  globally with `Factor`/`ReplaceFactor`/`NoArmor` rules. **Engine differences:** Zandronum
  supports damage-typed XDeath (`Death.Extreme.<Type>`) states contrary to the wiki's GZDoom-era
  "not supported" note; MAPINFO damagetype blocks are GZDoom-only and do not exist in Zandronum.
- [Monster and player falling damage](concepts/falling-damage.md) — tier B. `P_MonsterFallingDamage`
  and `P_FallingDamage` are separate functions with separate gates; the monster path computes a
  velocity-scaled formula and a threshold, then discards both and always deals a flat
  `TELEFRAG_DAMAGE` kill once its `LEVEL2_MONSTERFALLINGDAMAGE` gate is open — unlike the player
  path, which has no unconditional-kill floor. Covers the per-sector `SECF_NOFALLINGDAMAGE`
  escape hatch, why `DamageFactor "Falling", 0` works as a mitigation but `+INVULNERABLE` does not,
  and a netcode caveat around `P_DamageMobj` running on both server and client while `Die()` stays
  server-only.

## Families

- [A_FaceTarget / A_FaceTracer / A_FaceMaster](families/face-pointer.md) — tier A. Shared
  implementation — all three wrap one `A_Face()` helper. Adjust actor angle/pitch to face
  target/tracer/master pointer; **Zandronum 2-parameter form only** (not the extended 6-parameter
  UZDoom/GZDoom variant with `FAF_*` flags and offsets); pitch is not replicated in multiplayer;
  **null pointer safe**.
- [A_Light0 / A_Light1 / A_Light2 / A_Light / A_LightInverse](families/weapon-light.md) — tier A.
  Shared implementation — four thin `AInventory`-class wrappers around the player's `extralight`
  field (16x-scaled, additive, persists until reset); grouped with `A_LightInverse` per the wiki's
  own pairing, but that member is a distinct `AActor`-class action (compiles in any state table,
  including monsters) that repurposes the same field via an `INT_MIN` sentinel to trigger an
  inverted-colormap render effect rather than a brightness offset.

## Classes

- [CustomInventory](classes/custominventory.md) — tier A. Scripted inventory base class executing
  `Pickup:`/`Use:`/`Drop:` state chains via `CallStateChain` (OR-accumulated results, `Fail`
  self-jump hard-aborts); side effects from action functions and ACS calls run immediately with no
  rollback if a later state in the same chain fails. Also covers the `+INVENTORY.ALWAYSPICKUP`
  backstop in `AInventory::CallTryPickup` — a second, independent mechanism above the chain's own
  OR result that can force pickup success even when `Pickup:` returns false.
- [Health](classes/health.md) — tier A. Built-in base class for health-restoring pickup items;
  controls health restoration via `Inventory.Amount`/`MaxAmount`, pickup message conditions via
  `Health.LowMessage`, and `TryPickup` behavior (items fail if the actor is at max health without
  `+INVENTORY.ALWAYSPICKUP`).
- [Inventory](classes/inventory.md) — tier A. Base class for all inventory items (Ammo, Armor,
  Health, Keys, Weapons, PowerUps). Covers the pickup lifecycle (`TryPickup`, `HandlePickup`,
  `CreateCopy`, `GoAway`), respawn flow (`ShouldRespawn`, `DoRespawn`, `Hide`), key fields and
  reserved states, and Zandronum-specific flags/network/map-reset behavior.
- [Key](classes/key.md) — tier A. Built-in base class for inventory keys that unlock locked doors;
  **class-identity-based lock matching** (not inheritance- or `Species`-based, contrary to the
  wiki); `KeyNumber` is display/cheat-only, not the lock number; LOCKDEFS is the only
  lock-definition mechanism.
- [MapMarker](classes/mapmarker.md) — tier A. Automap-visible actor marker with TID tracking
  (`args[0]`), explore-gated visibility (`args[1]`), and activation/deactivation support;
  **Zandronum divergence:** `args[2]` automap-zoom scaling is a UZDoom/GZDoom-only feature, silently
  ignored in Zandronum; a subclass overriding `BeginPlay()` without chaining to the parent becomes
  permanently invisible on the automap.
- [MapSpot](classes/mapspot.md) — tier A. Invisible, non-physical, DECORATE-only anchor actor (no
  native C++ backing) referenced by TID for teleport destinations, ACS position lookups, and
  patrol points; covers the `MapSpotGravity` and `FS_Mapspot` subclasses.
- [PlayerPawn](classes/playerpawn.md) — tier A. Engine-native base class for all player
  characters; class hierarchy and PlayerPawn-specific actor flags, and **voodoo doll mechanics**
  (inventory forwarding, shared `PlayerInfo` state). See [Creating player
  classes](concepts/creating-player-classes.md) for `Player.*` property configuration and MAPINFO
  registration. **Fork divergence:** several GZDoom-era `Player.*` properties and flags are absent
  from Zandronum.
- [PowerProtection](classes/powerprotection.md) — tier B. `Powerup` subclass that reduces incoming
  damage via the engine's passive damage-modifier mechanism (`ModifyDamage`); works on **any**
  actor with an inventory, not just players. **Empty-`DamageFactors`-table trap:** zero declared
  `DamageFactor` entries silently grants a blanket 25%-damage effect against every damage type,
  while declaring some entries switches to a mode where an uncovered type gets no protection at
  all — the two behaviors don't blend. Not magnitude-gated (applies at `TELEFRAG_DAMAGE`
  magnitude too); stacks multiplicatively with other inventory-held damage modifiers.
- [Powerup](classes/powerup.md) — tier A. Timed-effect inventory class; covers the
  `Powerup`/`PowerupGiver` split, the `CreateCopy`/`InitEffect`/`DoEffect`/`EndEffect` activation
  lifecycle, several Zandronum-vs-wiki divergences (no `MaxEffectTics` field, non-virtual
  blink logic, `Tick()`'s permanent-powerup handling), re-pickup/refresh semantics
  (`HandlePickup`'s four branches and the `BLINKTHRESHOLD`-gated silent-discard trap),
  death/level-change destruction paths, and why `PowerStrength`'s permanence is a `Tick()`
  override, not a `Powerup.Duration 1` special case.
- [RandomSpawner](classes/randomspawner.md) — tier A. Built-in actor class that spawns one
  randomly-selected actor from a weighted `DropItem` list; **boss-death tracking** only activates
  when the spawner's own class declares `replaces <BossClass>` (verified against `A_BossDeath`'s
  species-resolution mechanism); item-respawn interaction (a rolled Inventory item's identity is
  fixed at spawn time and never re-rolled on respawn); a Zandronum-only infinite-loop bug on a
  `DropItem "None"` entry.
- [SwitchableDecoration](classes/switchabledecoration.md) — tier A. Built-in actor class for
  toggling between `Active`/`Inactive` state sequences via `Thing_Activate`/`Thing_Deactivate`;
  a missing target state destroys/hides the actor rather than leaving it unchanged; covers the
  one-way `SwitchingDecoration` variant.
- [TeleportFog](classes/teleportfog.md) — tier A. Special-effect actor spawned on teleportation
  and morphing/unmorphing; **wiki divergence:** the `target` pointer is set only during regular
  teleportation, not during morphing; Zandronum-specific spectator suppression and invasion-mode
  spawning.

## Actions

### Prose (tier A/B)

- [A_AlertMonsters](actions/a_alertmonsters.md) — tier A. Alerts monsters within range to a
  target actor; **server-side only**; `maxdist` parameter specifies 2D distance check (**0 =
  unlimited range**, not zero-distance); three `AMF_*` flags (all functional in Zandronum);
  **wiki's "already have a target" statement clarified** — function operates on target-selection
  precedence, not caller's current target state.
- [A_BossDeath](actions/a_bossdeath.md) — tier A. Triggers boss-death special effects (MAPINFO
  actions and hardcoded level specials) when all monsters of the caller's type are dead; **checks
  exact class identity** (not species or replacee); **server-side only in multiplayer**;
  **class-replacement caveat**: two classes both replacing the same boss can cause
  double-triggering while both are alive.
- [A_ChangeFlag](actions/a_changeflag.md) — tier A. Changes an actor flag and sets it to a
  given value; **special handling for blockmap/sector relinking (MF_NOBLOCKMAP/MF_NOSECTOR)**
  and monster/item/secret counting flags; **server-authoritative in multiplayer**.
- [A_ChangeVelocity](actions/a_changevelocity.md) — tier A. Changes an actor's velocity on any
  or all axes; can add to or replace existing velocity and can be made relative to actor angle;
  **Zandronum divergence: does not support the `ptr` parameter the ZDoom wiki describes; modifies
  only the calling actor**.
- [A_Chase](actions/a_chase.md) — tier A. Core monster chase-and-attack action driving target
  acquisition, melee/missile attack decisions, and pathing (and the thin `A_FastChase`/
  `A_VileChase`/`A_ExtChase` wrappers around it); **only 5 of the wiki's 11 `CHF_*` flags exist in
  Zandronum** (`CHF_NORANDOMTURN`, `CHF_NODIRECTIONTURN`, `CHF_NOPOSTATTACKTURN`,
  `CHF_STOPIFBLOCKED`, `CHF_DONTIDLE`, `CHF_DONTTURN` are wiki/GZDoom-only and compile as inert
  integers).
- [A_CheckBlock](actions/a_checkblock.md) — tier A. Checks if an actor pointer would be blocked
  at a specified position relative to the caller's angle/position; jumps to a target state if
  blocked. **UZDoom/GZDoom-family only** — does not exist in Zandronum.
- [A_CheckCeiling](actions/a_checkceiling.md) — tier A. Jumps to a target state if the actor is
  touching or submerged into the ceiling; the check includes actor height in the calculation
  (z + height vs. ceilingz).
- [A_CheckFlag](actions/a_checkflag.md) — tier A. Checks if an actor has a flag set and jumps to
  a state if set; **null pointer resolves silently (no jump)**; **unknown flag names print
  console errors every tic**; supports dot notation for class-specific flags; no explicit network
  synchronization (relies on client flag-state mirroring).
- [A_CheckFloor](actions/a_checkfloor.md) — tier A. Jumps to a target state if the calling actor
  is standing on or submerged into the floor; verified across Zandronum 3.2.1 (C++ action
  function) and UZDoom 4.15pre (ZScript native); uses position-only check (no velocity test),
  allowing submerged actors.
- [A_CheckLOF](actions/a_checklof.md) — tier A. Line-of-fire hitscan test; jump on target
  reachability or intercepting actors. **Zandronum-specific caveat:** missing 10th parameter
  `offsetforward` and flags `CLOFF_SETTARGET`/`CLOFF_SETMASTER`/`CLOFF_SETTRACER` from ZDoom wiki.
- [A_CheckRange](actions/a_checkrange.md) — tier A. Jumps if out of distance range of all
  players; distance measured in 3D from player eye position; **no optional 2d_check or offset
  parameters in Zandronum** (wiki describes unsupported variants).
- [A_CheckReload](actions/a_checkreload.md) — tier A. Checks the ready weapon's ammunition
  sufficiency and switches weapons if out of ammo; automatically adapts to primary or alternate
  fire mode; server-replicated ammo-switch with client-mode contingencies; unguarded
  `ReadyWeapon` NULL dereference in non-weapon inventory contexts flagged as open question.
- [A_CheckSight](actions/a_checksight.md) — tier A. Jumps to a target state if no player can see
  the calling actor; checks all active (non-spectating) players' line of sight including cameras
  and co-op spy; server-authoritative for non-CLIENTSIDEONLY actors (client-side sight check
  disabled, result received via server broadcast).
- [A_CheckSightOrRange](actions/a_checksightorrange.md) — tier A. Jumps if actor is beyond range
  and out of sight of all players; **Zandronum has only 2 parameters (no 2d_check), runs on both
  client and server (unlike A_Look), and measures distance to eye height and actor bounds, not
  centers**.
- [A_CheckSpecies](actions/a_checkspecies.md) — tier A. Checks whether a target actor has a
  specified species and jumps to a state if the check passes; **does not exist in Zandronum at
  all** — species-checking in Zandronum requires conditional ACS logic or DECORATE expressions,
  as the ZScript standard library action is UZDoom/GZDoom-family only.
- [A_ClearTarget](actions/a_cleartarget.md) — tier A. Clears the actor's target, sound target,
  and last target pointers; used to make monsters "give up" pursuit and return to idle searching.
- [A_Countdown](actions/a_countdown.md) — tier A. Decrements ReactionTime until it reaches 0,
  then destroys the actor; **intended for missile-type actors only**.
- [A_CountdownArg](actions/a_countdownarg.md) — tier A. Decrements one of an actor's argument
  counters and destroys or state-changes the actor when countdown reaches zero; **countdown takes
  N+1 calls for arg of N** (post-decrement semantic); **`state` parameter is silently ignored for
  MISSILE and SHOOTABLE actors**.
- [A_CustomBulletAttack](actions/a_custombulletattack.md) — tier A. Customizable hitscan attack
  for monsters that fires multiple bullets with configurable spread, damage, and impact puff;
  **Zandronum's 7-parameter version lacks the `ptr`, `missile`, `Spawnheight`, `Spawnofs_xy`
  parameters and the `CBAF_PUFFTARGET`/`CBAF_PUFFMASTER`/`CBAF_PUFFTRACER` flags the upstream
  ZDoom wiki describes** (code using those parameters will not compile); only 5 of the 8
  wiki-listed flags are defined; the spread/damage RNG rolls run unconditionally on both server
  and client even though the downstream `P_LineAttack` call is itself client-gated.
- [A_CustomComboAttack](actions/a_customcomboattack.md) — tier A. Customizable combo attack for
  monsters; chooses melee or projectile based on range; **wiki type mismatch: signature declares
  string/string/string (missiletype/meleesound/damagetype) but Zandronum implements
  class<Actor>/sound/name**; **facing before network gate** (client-side facing, rest
  server-only); **`damagetype="none"` silently defaults to `"Melee"`**.
- [A_CustomMeleeAttack](actions/a_custommeleeattack.md) — tier A. Customizable melee attack for
  monsters; **Zandronum server-side only** (returns immediately on clients unless actor has
  `+CLIENTSIDEONLY`); **`damagetype="none"` is silently converted to `"Melee"`**.
- [A_CustomMissile](actions/a_custommissile.md) — tier A. Customizable projectile attack for
  monsters; **fork divergence: Zandronum has 6 parameters (no `ptr` parameter like the GZDoom wiki
  describes); not deprecated in Zandronum**.
- [A_CustomPunch](actions/a_custompunch.md) — tier A. Customizable melee attack for weapons with
  ammo consumption, puff spawning, and health-steal; **fork divergence: Zandronum's 6-parameter
  version is significantly simpler than the wiki's GZDoom version** (missing parameters
  `lifestealmax`, `armorbonustype`, `MeleeSound`, `MissSound`; no `CPF_NOTURN`/`CPF_STEALARMOR`
  flags; unconditional facing turn on hit; server-authoritative).
- [A_CustomRailgun](actions/a_customrailgun.md) — tier A. Customizable rail beam attack for
  monsters; **fork divergence: Zandronum's 16-parameter version lacks the `spiraloffset`,
  `limit`, and `veleffect` parameters; spiral always starts at 270°, pierce limit is binary (all
  or first-only), and velocity lead is hardcoded to 3.0**; aim parameter (`0`=look direction,
  `1`=aim with velocity leading, `2`=direct leading aim); five `RGF_*` flags (SILENT, NOPIERCING,
  EXPLICITANGLE, FULLBRIGHT, CENTERZ); **player color override: when `color1==0` and
  `color2==0`, engine substitutes player's team/individual railgun color, not random blue/gray
  shades**; unlagged client-side rail drawing supported.
- [A_DamageChildren](actions/a_damagechildren.md) — tier A. Damages all child actors (those with
  `master == self`) by a specified amount; **Zandronum 2-parameter version only** (drastically
  simplified vs. GZDoom/UZDoom's 7-parameter variant with flags and filters); negative amounts
  heal instead — **but a loop bug means only the first healed child actually heals; every
  subsequent child in the same call is damaged instead**, since `amount` is negated in place and
  the sign flip persists across iterations.
- [A_DamageMaster](actions/a_damagemaster.md) — tier A. Damages the calling actor's master by a
  specified amount; negative amounts heal instead. **Zandronum's 2-parameter version is
  drastically simplified compared to GZDoom/UZDoom**, which support flags (`DMSS_*`) and
  actor/species filters; damage factors apply (unlike `A_KillMaster`), armor is bypassed,
  invulnerability blocks the damage, and 1,000,000+ damage forces a kill via `TELEFRAG_DAMAGE`.
- [A_DamageSelf](actions/a_damageself.md) — tier A. Damages the calling actor by a specified
  amount; negative amounts heal. **UZDoom/GZDoom-family only, does not exist in Zandronum** —
  supports flags, actor/species filters, and configurable damage source/inflictor pointers;
  Zandronum has only the simpler 2-parameter `A_DamageMaster`/`A_DamageChildren`/
  `A_DamageSiblings` variants for specific pointer targets.
- [A_DamageSiblings](actions/a_damagesiblings.md) — tier A. Damages all actors sharing the
  caller's master; **drastically simplified 2-parameter Zandronum version** (no `DMSS_*` flags,
  filters, or pointer configuration); **critical bug: negative `amount` parameter is mutated
  inside the sibling loop, causing every sibling after the first healed one to be damaged
  instead**; full thinker-list scan per call (O(n) cost).
- [A_DamageTarget](actions/a_damagetarget.md) — tier A. Damages the calling actor's target
  pointer by a specified amount; **UZDoom/GZDoom-family only** — does not exist in
  Zandronum. Supports extended flags (`DMSS_*`), class/species filters, and source/inflictor
  control pointers; Zandronum provides only 2-parameter Master/Children/Siblings damage variants
  without filtering or control pointers.
- [A_DamageTracer](actions/a_damagetracer.md) — tier A. Damages the calling actor's tracer actor
  by a specified amount; negative amounts heal. **UZDoom/GZDoom-family only** — does not
  exist in Zandronum; the `tracer` pointer is available in Zandronum (used by `A_Tracer2`) but no
  damage-family action targets it.
- [A_DeQueueCorpse](actions/a_dequeuecorpse.md) — tier A. Removes actor from corpse queue with
  asymmetric cleanup semantics: frees the queue slot while leaving the actor alive, unlike
  overflow eviction which destroys the actor; used in raise/resurrection states to prevent
  queued corpses from being destroyed.
- [A_Die](actions/a_die.md) — tier A. Kills the calling actor if it is not already dead, setting
  its health to 0 and transitioning to its Death state; has an effect only if the actor has the
  SHOOTABLE or VULNERABLE flag set; server-side only in multiplayer (a `+CLIENTSIDEONLY` actor
  calling `A_Die` will never actually die).
- [A_Explode](actions/a_explode.md) — tier A. Radius attack (explosion) with optional nail
  hitscan attacks; **fork divergence: returns nothing** (ZDoom-wiki describes return value),
  supports only two flags (`XF_HURTSOURCE`, `XF_NOTMISSILE`) vs. the wiki's seven, and uses the
  actor's DamageType property.
- [A_FadeIn](actions/a_fadein.md) — tier A. Increases an actor's alpha by a specified amount each
  tic; **wiki describes optional `FTF_*` flags (FTF_REMOVE, FTF_CLAMP) that do not exist in
  Zandronum** — only `increase_amount` parameter is supported; second parameter causes parse
  error; alpha is not clamped by the function.
- [A_FadeOut](actions/a_fadeout.md) — tier A. Decreases an actor's alpha by a specified amount
  each tic; **Zandronum uses a boolean `remove` parameter, not the wiki's `FTF_*` flags** —
  `FTF_CLAMP` does not exist (no alpha-clamping support), and `FTF_REMOVE` is the default
  behavior.
- [A_FadeTo](actions/a_fadeto.md) — tier A. Gradually adjusts an actor's alpha toward a target
  value; **Zandronum uses a boolean `remove` parameter (default `false`), not the wiki's `FTF_*`
  flags** — `remove` defaults to `false` (wiki says `true`); `FTF_CLAMP` does not exist.
- [A_Fire](actions/a_fire.md) — tier A. Repositions the calling actor around its `tracer` at 24
  units forward with optional height offset; **Zandronum's server-side-only implementation with
  mandatory line-of-sight checks differs from the ZDoom-wiki ZScript version, which has no
  netcode**.
- [A_FireBullets](actions/a_firebullets.md) — tier A. Custom hitscan weapon attack with optional
  spread and impact puff; **Zandronum's 7-parameter version differs significantly from the wiki's
  ZScript 10-parameter one** (no missile spawning; missing `FBF_PUFFTARGET`/`FBF_PUFFMASTER`/
  `FBF_PUFFTRACER` flags; `numbullets == -1` behavior and spread math divergence).
- [A_FireCustomMissile](actions/a_firecustommissile.md) — tier A. Fires a projectile from a
  player weapon; **Zandronum parameter 5 is a single `aimatangle` bool instead of the wiki's
  `FPF_*` flags** (which do not exist and produce silent behavioral errors if passed as
  integers); function is player-only; deprecation warning is GZDoom-family only and does not
  apply to Zandronum.
- [A_GiveInventory](actions/a_giveinventory.md) — tier A. Gives inventory items to an actor;
  **special Health item handling** (amount multiplied by item's own `Amount` value);
  **Zandronum-specific early-return on non-client-handled actors** with no explicit result-slot
  update.
- [A_GiveToTarget](actions/a_givetotarget.md) — tier A. Gives inventory items to the calling
  actor's current target; **special Health item handling** (amount multiplied by item's own
  `Amount` value); **third parameter uses target as context** (e.g., `AAPTR_MASTER` refers to
  target's master, not caller's); **Zandronum-specific early-return on non-client-handled actors**
  with no explicit result-slot update.
- [A_GunFlash](actions/a_gunflash.md) — tier A. Displays a weapon muzzle flash or other firing
  effect in the fixed `ps_flash` sprite layer; **Zandronum's fixed five-slot sprite system** (not
  the arbitrary-layer `A_Overlay`); **`GFF_NOEXTCHANGE` flag prevents player state change**;
  **server-replicated in multiplayer**; player state change gated on `health > 0`.
- [A_Jump](actions/a_jump.md) — tier A. Randomly branches to one of several target states with a
  specified probability; server-authoritative actors never touch the RNG client-side (client-mode
  check precedes the roll) so there's no alignment concern there, and `+CLIENTSIDEONLY` actors'
  independent per-machine `pr_cajump` rolls are confirmed **not** to be seed-synced (the legacy
  `rngseed`-transmitting handshake is dead code in the Zandronum engine fork) but that's inconsequential since such
  actors are documented as visuals-only with no cross-machine consistency requirement; a parser
  limitation affects multi-frame offset jumps on a single state line.
- [A_JumpIf](actions/a_jumpif.md) — tier A. Conditional state jump on a DECORATE expression;
  **network caveat**: unlike A_Jump, the expression is evaluated *before* the client-mode check, so
  an RNG-bearing condition can desync a non-clientside actor between server and client.
- [A_JumpIfArmorType](actions/a_jumpifarmortype.md) — tier A. Checks if equipped armor matches a
  specified type; jumps if the type and minimum amount threshold (default 1 point) are met.
  **Wiki divergence:** default `amount` value not documented in wiki.
- [A_JumpIfCloser](actions/a_jumpifcloser.md) — tier A. Jumps to a state if the calling actor's
  target is closer than a specified distance; **Zandronum divergence: the optional `noz`
  parameter from the ZDoom wiki does not exist and causes a parse error**; vertical distance
  checking is always performed; **network-aware**: clients receive position sync updates after
  jumps.
- [A_JumpIfHealthLower](actions/a_jumpifhealthlower.md) — tier A. Jumps to a state if the calling
  actor's health is lower than a specified value; **pointer parameter described in the wiki does
  not exist in Zandronum 3.2.1**.
- [A_JumpIfInTargetInventory](actions/a_jumpifintargetinventory.md) — tier A. Checks the calling
  actor's target for a specific inventory item and conditionally jumps to a state if a certain
  amount is present; equivalent to `A_JumpIfInventory` with `AAPTR_TARGET` but more concise.
- [A_JumpIfInTargetLOS](actions/a_jumpifintargetlos.md) — tier A. Jumps if the calling actor is
  in the target's field of view and line of sight; **wiki divergence: FOV cone is centered on the
  target's facing direction, not the caller's** — this function tests whether the target sees the
  caller, not the reverse. Only 7 of 12 defined `JLOSF_*` flags are functional in this function; 5
  additional flags compile but are inert (`JLOSF_TARGETLOS`, `JLOSF_FLIPFOV`, `JLOSF_ALLYNOJUMP`,
  `JLOSF_COMBATANTONLY`, `JLOSF_NOAUTOAIM`). Server-authoritative in multiplayer (client-side
  returns immediately without evaluation).
- [A_JumpIfInventory](actions/a_jumpifinventory.md) — tier A. Checks an actor's inventory and
  conditionally jumps to a state if a certain amount of an item is present; supports both
  positive-amount thresholds and zero/negative "at max capacity" checks; can check another
  actor's inventory via actor pointers; **network caveat**: only executes on client in
  weapon/flash states or for `+CLIENTSIDEONLY` actors; silently no-ops on unresolvable class
  names or NULL actor pointers.
- [A_JumpIfMasterCloser](actions/a_jumpifmastercloser.md) — tier A. Jumps to a state if the
  calling actor's master is closer than a specified distance; **Zandronum divergence: the
  optional `noz` parameter from the ZDoom wiki does not exist and causes a parse error**;
  vertical distance checking is always performed; **critical network caveat: unlike
  A_JumpIfCloser, there is no client-mode guard, so clients evaluate the jump using their own
  (unreliably replicated) master pointer**, creating potential server/client desync on
  non-clientside actors.
- [A_JumpIfNoAmmo](actions/a_jumpifnoammo.md) — tier A. Jumps if the player's ready weapon lacks
  sufficient ammunition for the current firing mode; **never jumps if infinite-ammo flags or
  cheats are active**; **weapon with +WEAPON.AMMO_OPTIONAL flag will still report empty ammo**,
  overriding that flag's normal behavior; executes on both server and client with client-ammo-
  information synchronization (exception to the typical server-authoritative `A_JumpIf*` pattern).
- [A_JumpIfTargetInLOS](actions/a_jumpiftargetinlos.md) — tier A. Jumps if the calling actor can
  see its target, optionally subject to FOV cones and distance checks; behavior differs between
  monsters and weapons/inventory items. **Wiki divergence: `JLOSF_CHECKTRACER` flag is not
  supported in Zandronum** (not in the constants table, will compile but have no effect).
  **Network synchronization differs from A_JumpIfInTargetLOS** — this function sends position
  updates for non-player callers; A_JumpIfInTargetLOS is server-authoritative. Parameter
  encodings are `ANGLE` (not float) for FOV and `FIXED` (not float) for distances.
- [A_JumpIfTargetInsideMeleeRange](actions/a_jumpiftargetinsidemeleerange.md) — tier A. Jumps if
  the calling actor's target is within melee range, including line-of-sight check and vertical
  constraints. Melee range includes the target's radius and uses octagonal approximation. **Wiki
  divergence: note about anonymous functions does not apply to Zandronum** (anonymous action
  blocks are a ZScript feature not available in DECORATE).
- [A_JumpIfTargetOutsideMeleeRange](actions/a_jumpiftargetoutsidemeleerange.md) — tier A. Jumps to
  a state if the calling actor's target is outside melee range; **also jumps if target is null,
  friendly, or not in line of sight**; melee range measured as `meleerange + target.radius`;
  vertical range checked unless `MF5_NOVERTICALMELEERANGE` flag is set; **server-authoritative in
  multiplayer**.
- [A_JumpIfTracerCloser](actions/a_jumpiftracercloser.md) — tier A. Jumps to a state if the
  calling actor's tracer is closer than a specified distance; **Zandronum divergence: the optional
  `noz` parameter from the ZDoom wiki does not exist and causes a parse error**; vertical distance
  checking cannot be disabled in Zandronum's implementation.
- [A_KillChildren](actions/a_killchildren.md) — tier A. Destroys all spawned children (actors
  whose master pointer references the calling actor); **wiki divergence: Zandronum's
  single-parameter version is substantially simpler than the extended multi-parameter ZDoom
  version** (no `flags`, `filter`, `species`, `src`, or `inflict` parameters; no `KILS_*`
  filtering options); respects `INVULNERABLE` flag; uses `DMG_NO_ARMOR`/`DMG_NO_FACTOR` damage
  suppression.
- [A_KillMaster](actions/a_killmaster.md) — tier A. Kills the calling actor's master via
  P_DamageMobj with the master's health as damage; **Zandronum-only simplified version: single
  `damagetype` parameter vs. GZDoom/UZDoom's 6-parameter form with KILS_* flags and filters;
  INVULNERABLE masters survive; no network synchronization gate in the action function itself**.
- [A_KillSiblings](actions/a_killsiblings.md) — tier A. Kills all actors sharing the calling
  actor's master, excluding the caller; **Zandronum-only simplified version: single `damagetype`
  parameter vs. GZDoom/UZDoom's 6+ parameters with KILS_* flags and filters; INVULNERABLE
  siblings survive; explicit server-side-only gate with +CLIENTSIDEONLY exception** (unlike
  A_KillMaster and A_KillChildren, which have no network check).
- [A_KillTarget](actions/a_killtarget.md) — tier A. Kills the calling actor's target pointer with
  optional class/species filtering and configurable damage source/inflictor pointers.
  **UZDoom/GZDoom-family only** — does not exist in Zandronum.
- [A_KillTracer](actions/a_killtracer.md) — tier A. Kills the calling actor's tracer with
  configurable filters, damage type, and invulnerability bypass. **UZDoom/GZDoom-family only** —
  does not exist in Zandronum; tracer-kill variants missing entirely in the Zandronum engine fork alongside
  missing `A_DamageTracer` and `A_RemoveTracer`.
- [A_Look](actions/a_look.md) — tier A. Default `Spawn`-state target-acquisition action;
  **server-authoritative in Zandronum** (early-returns in client mode except for one stealth-
  monster `visdir` update that runs on both sides); early-outs on `MF5_INCONVERSATION` and
  `CF_NOTARGET`; `MF_AMBUSH` requires line-of-sight before entering `See` state; consumes
  `Thing_SetGoal` map special on first call; friendly monsters use `P_LookForPlayers` before
  falling back to `A_Wander`; extended by `A_LookEx` and `A_Look2`.
- [A_Look2](actions/a_look2.md) — tier A. Sound-based target-acquisition action for Strife actors;
  wakes on sound but falls back to visual search for friendly targets; **Zandronum-specific RNG
  frame desync** on server broadcast vs. local state (visual-only issue, untraced whether two
  state-actions fire per tic).
- [A_LookEx](actions/a_lookex.md) — tier A. Customizable target-acquisition action for monsters;
  parameterizes sight/sound range, minimum sight distance, field-of-view angle, and target state,
  with all six `LOF_*` flags available (`LOF_NOSIGHTCHECK`, `LOF_NOSOUNDCHECK`,
  `LOF_DONTCHASEGOAL`, `LOF_NOSEESOUND`, `LOF_FULLVOLSEESOUND`, `LOF_NOJUMP`); server-authoritative
  (early-returns in client mode except for stealth-monster `visdir` update).
- [A_LoopActiveSound](actions/a_loopactivesound.md) — tier A. Plays the actor's ActiveSound as a
  seamless loop on the voice channel, restarting when finished; does not work as expected on
  weapons due to self-pointer semantics in weapon states; can be stopped with `A_StopSound()`.
- [A_Lower](actions/a_lower.md) — tier A. Lowers weapon off-screen during deselect; **critical
  fork divergence: ZDoom wiki describes optional `lowerspeed` parameter, but Zandronum function
  takes no arguments** — use multiple calls or fewer state tics to lower faster; null-pointer
  safety asymmetry vs. `A_Raise`.
- [A_MonsterRefire](actions/a_monsterrefire.md) — tier A. Checks whether a monster should abort its
  attack sequence based on target visibility and death; **probability-driven continue-vs-abort**
  (`chance` parameter: 0–255 chance to keep attacking if target lost); **jumps if no target, hit
  ally, target dead, or out of sight**; **server-side only in multiplayer**, client update sent on
  jump.
- [A_NoBlocking / A_Fall](actions/a_noblocking.md) — tier A. Actor unblocking and dialogue/drop-
  item spawning; **multiplayer caveat: in Zandronum, the solid-flag clear is server-side only**
  until the server replicates it to clients via `SERVERCOMMANDS_SetThingFlags`, so actors remain
  locally solid until synchronization arrives.
- [A_Overlay](actions/a_overlay.md) — tier A. Creates a new weapon/player sprite layer and sends
  it to a state sequence; **does not exist in Zandronum at all** — Zandronum's layer system is
  fixed to five hardcoded sprites (`ps_weapon`, `ps_flash`, `ps_targetcenter`, `ps_targetleft`,
  `ps_targetright`), while this function requires arbitrary-layer `DPSprite` support.
  UZDoom/GZDoom-family only; see `A_GunFlash` for the Zandronum equivalent.
- [A_Pain](actions/a_pain.md) — tier A. Plays pain sounds in response to damage; **for players,
  synthesizes health-tiered `*pain25`/`*pain50`/`*pain75`/`*pain100` sounds with damage-type
  fallback chain**; for monsters, plays the `PainSound` property; **morphed players without
  `+NOMORPHLIMITATIONS` use the monster branch**; **runs on both client and server with no
  replication guard**.
- [A_PlaySound](actions/a_playsound.md) — tier A. Plays a sound from an actor with optional
  looping, attenuation, and channel selection; **engine divergence: Zandronum lacks the `local`
  and `pitch` parameters the GZDoom-family version added**; two looping paths (parameter vs. flag)
  with different re-entry guards; server-replicated in multiplayer.
- [A_PlaySoundEx](actions/a_playsoundex.md) — tier A. Plays a sound from an actor on a named
  channel; **not deprecated in Zandronum** (deprecation is upstream-only; `A_StartSound` does not
  exist in Zandronum); no volume parameter (hardcoded 1.0); older interface, use `A_PlaySound`
  for new code.
- [A_PlayWeaponSound](actions/a_playweaponsound.md) — tier A. **Deprecated.** Plays a sound on
  the weapon sound channel with hardcoded volume and attenuation; use `A_PlaySound` for new code.
- [A_Quake](actions/a_quake.md) — tier A. Earthquake with per-tic damage and tremor effects;
  **Zandronum lacks sound default** (wiki's "world/quake" not used); **A_QuakeEx unavailable**
  (GZDoom-only).
- [A_QueueCorpse](actions/a_queuecorpse.md) — tier A. Adds the calling actor to the corpse
  queue, limited by the `sv_corpsequeuesize` cvar; a silent no-op when the queue is disabled
  (`sv_corpsequeuesize <= 0`); real queue overflow eviction destroys the corpse actor.
- [A_RadiusGive](actions/a_radiusgive.md) — tier A. Gives inventory items to all eligible actors
  within a radius; **Zandronum supports only 4 parameters** (item, distance, flags, amount), and
  several RGF_* flags/parameters from the wiki do not exist.
- [A_RadiusThrust](actions/a_radiusthrust.md) — tier A. Applies radial thrust (knockback) to
  nearby actors without damage; **Zandronum lacks the 5th `species` parameter the wiki
  describes, and only 3 of the wiki's 5 `RTF_*` flags (`RTF_AFFECTSOURCE`, `RTF_NOIMPACTDAMAGE`,
  `RTF_NOTMISSILE`) exist in the Zandronum engine fork** (`RTF_THRUSTZ` and `RTF_CIRCULARTHRUST` are
  GZDoom-family only); **server-side only**; triggers the same `P_CheckSplash` terrain-splash
  check as `A_Explode`.
- [A_RailAttack](actions/a_railattack.md) — tier A. Hitscan piercing beam attack with particle
  trail; **wiki describes ZDoom/GZDoom with 19 parameters and `RGF_NORANDOMPUFFZ` flag not
  present in Zandronum's 16-parameter version** (missing `spiraloffset`, `limit`); **only works
  on player weapons, not monsters**.
- [A_Raise](actions/a_raise.md) — tier A. Raises a weapon onto-screen during Select state; fixed
  `FRACUNIT*6` movement per call; **Zandronum lacks the optional raisespeed parameter the wiki
  describes**.
- [A_RaiseChildren](actions/a_raisechildren.md) — tier A. Resurrects spawned children (actors
  whose master pointer references the calling actor); **Zandronum version takes no parameters**
  — the ZDoom Wiki's optional `flags` parameter and `RF_TRANSFERFRIENDLINESS`/
  `RF_NOCHECKPOSITION` flag constants do not exist in the Zandronum engine fork and will cause compile errors if
  passed.
- [A_RaiseMaster](actions/a_raisemaster.md) — tier A. Resurrects the calling actor's master
  (spawner) from a corpse; **server-authoritative** (early-returns on network clients);
  **Zandronum takes no parameters**, unlike the ZDoom Wiki which describes GZDoom/UZDoom flags
  RF_TRANSFERFRIENDLINESS and RF_NOCHECKPOSITION.
- [A_RaiseSelf](actions/a_raiseself.md) — tier A. Resurrects the calling actor from death;
  **UZDoom/GZDoom-family only — does not exist in Zandronum**; optional `flags` parameter
  supports `RF_NOCHECKPOSITION` (skip position check) and `RF_TRANSFERFRIENDLINESS` (copy raiser
  alignment, meaningless when raiser == target).
- [A_RaiseSiblings](actions/a_raisesiblings.md) — tier A. Resurrects all actors sharing the
  calling actor's master (spawner) from corpses; **Zandronum-only simplified version with no
  parameters** (wiki describes unsupported `RF_*` flags); **server-authoritative with
  unconditional server-side-only gate** (unlike `A_KillSiblings`, which allows `+CLIENTSIDEONLY`
  actors to manage themselves).
- [A_RearrangePointers](actions/a_rearrangepointers.md) — tier A. Reassigns the calling actor's
  target, master, and tracer pointers to any of its current pointers or NULL; with optional
  loop-safeguard flags to prevent infinite pointer chains; **caveat: setting target to NULL does
  not perform all actions of A_ClearTarget**.
- [A_Recoil](actions/a_recoil.md) — tier A. Pushes the calling actor opposite to its facing
  direction with horizontal recoil; **pitch-unaware** (wiki's pitch-adjustment workaround is
  viable via `cos(pitch)` in expressions); **network split: players apply locally, non-player
  actors receive server resync**.
- [A_ReFire](actions/a_refire.md) — tier A. Checks whether the fire button is held after an
  attack; jumps to a follow-up state (`Hold`/`AltHold` by default) if held, otherwise resets
  refire counter and performs ammo-check weapon-switch. **Engine-family divergence: ZDoom 4.14.2+
  `autoSwitch` parameter does not exist in Zandronum** — ammo checking is unconditional, always
  executed on button release.
- [A_Remove](actions/a_remove.md) — tier A. Removes an actor pointed to by a given actor pointer
  selector, optionally filtered by class and/or species. The `filter` match is exact class
  identity, **not** `IsKindOf` — a subclass of the named class is not removed.
  **UZDoom/GZDoom-family only** — does not exist in Zandronum. `A_RemoveMaster`/`A_RemoveChildren`/
  `A_RemoveSiblings` exist in both engines with simpler signatures and no filtering; UZDoom also
  adds `A_RemoveTarget`/`A_RemoveTracer`.
- [A_RemoveChildren](actions/a_removechildren.md) — tier A. Removes spawned children; **critical
  fork divergence: Zandronum has only 1 parameter (removeall bool) vs. the ZDoom wiki's advanced
  version with flags/filter/species parameters that do not exist in Zandronum** and cause parse
  errors if attempted.
- [A_RemoveMaster](actions/a_removemaster.md) — tier A. Removes the calling actor's master;
  **critical fork divergence: Zandronum has no parameters (unconditional removal) vs. the ZDoom
  wiki's advanced version with flags/filter/species parameters that do not exist in Zandronum**.
- [A_RemoveSiblings](actions/a_removesiblings.md) — tier A. Removes sibling actors; **critical
  fork divergence: Zandronum has only 1 parameter (removeall bool) vs. the ZDoom wiki's advanced
  version with flags/filter/species parameters that do not exist in Zandronum** and cause parse
  errors if attempted. **Unlike A_KillSiblings, A_RemoveSiblings has no explicit server-side-only
  network gate** — netcode handling is implicit in P_RemoveThing.
- [A_RemoveTarget](actions/a_removetarget.md) — tier A. Removes the calling actor's target
  pointer from the map. **UZDoom/GZDoom-family only** — does not exist in Zandronum.
- [A_RemoveTracer](actions/a_removetracer.md) — tier A. Removes the actor in the calling actor's
  tracer pointer, with optional filtering by type, class, and species.
  **UZDoom/GZDoom-family only** — does not exist in Zandronum.
- [A_ScaleVelocity](actions/a_scalevelocity.md) — tier A. Multiplies an actor's velocity on all
  axes by a scale factor; **Zandronum divergence: does not support the `ptr` parameter the ZDoom
  wiki describes; modifies only the calling actor**.
- [A_Scream](actions/a_scream.md) — tier A. Plays an actor's death sound on the voice channel;
  **wiki incorrectly claims FULLVOLDEATH flag enables full volume** — only the +BOSS flag does so
  in Zandronum (FULLVOLDEATH exists but is honored elsewhere, not here).
- [A_SentinelBob](actions/a_sentinelbob.md) — tier A. Applies upward or downward vertical
  acceleration for smooth bobbing; **velocity-based accelerator** requiring repeated calls; bob
  envelope constrained by floor (96 map units) and ceiling (16 units below); **server-side only
  in multiplayer**.
- [A_SeekerMissile](actions/a_seekermissile.md) — tier A. Configurable homing missile with
  optional target acquisition; **wiki misstates distance units (128-map-unit blocks, not 64),
  conflates MaxTargetRange (weapon spawn) with SMF_LOOK distance parameter**.
- [A_SetAngle](actions/a_setangle.md) — tier A. Sets an actor's facing angle in degrees with
  optional sub-tic interpolation; **Zandronum has 2 parameters (angle, flags), not the wiki's
  3-parameter form with `ptr`** — no actor pointer support; `SPF_INTERPOLATE` flag (value 2)
  smooths player view rotation.
- [A_SetArg](actions/a_setarg.md) — tier A. Changes an actor's argument counter at a specified
  index to a value; **no network replication — values set on client vs. server diverge in
  multiplayer**; out-of-range indices silently no-op.
- [A_SetBlend](actions/a_setblend.md) — tier A. Screen tint/blend effect that fades over tics;
  **engine-family divergence: Zandronum always fades to fully transparent (no `alpha2`
  parameter), while UZDoom/GZDoom allow persistent tints via `alpha2`**; only active when called
  on PlayerPawn-based actors.
- [A_SetPitch](actions/a_setpitch.md) — tier A. Sets actor pitch (vertical angle) with optional
  interpolation; **Zandronum has 2 parameters only (no `ptr` like the wiki describes), and pitch
  clamping for players uses `player->MinPitch`/`MaxPitch` (typ. −32° to +56°), not fixed
  [−90°, 90°]**.
- [A_SetScale](actions/a_setscale.md) — tier A. Sets an actor's visual scale (sprite rendering
  only, not collision box); **Zandronum has only 2 parameters, not the wiki's 4** — lacks `ptr`
  and `usezero`, so using the wiki form causes a parse error; scaleY=0 is unreachable (silently
  becomes scaleX); server-authoritative with change-gated replication.
- [A_SetTranslucent](actions/a_settranslucent.md) — tier A. Sets an actor's alpha and render
  style mode; **Zandronum has no A_SetRenderStyle** (wiki's supersession note does not apply to
  the Zandronum engine fork); **STYLE_* enum constants unavailable** (pass raw integers 0/1/2).
- [A_SetUserArray](actions/a_setuserarray.md) — tier A. Sets an array element of an integer user
  variable; validates that the variable exists and is of type `int[]`, and that the index is in
  bounds; required `user_` prefix; special weapon and CustomInventory item caveats.
- [A_SetUserVar](actions/a_setuservar.md) — tier A. Sets a user variable on the calling actor to
  an integer value; validates that the variable exists and is of type `int`; required `user_`
  prefix; special weapon and CustomInventory item caveats.
- [A_SetUserVarFloat](actions/a_setuservarfloat.md) — tier A. Set a floating-point user variable
  (**UZDoom/GZDoom-family only**; Zandronum does not support float user variables).
- [A_SkullAttack](actions/a_skullattack.md) — tier A. Charging attack that sets the
  `MF_SKULLFLY` flag and velocity vectors to move toward the target in a straight line; impact
  deals melee damage and transitions to the See/Idle state; server-side only (will desync if
  used on a `+CLIENTSIDEONLY` actor).
- [A_SpawnDebris](actions/a_spawndebris.md) — tier A. Spawns debris actors around the calling
  actor; **multiplayer caveat: debris velocity is never replicated to clients** (server-correct
  trajectories vs. zero-velocity falls on clients).
- [A_SpawnItem](actions/a_spawnitem.md) — tier A. Simple angular-distance spawner with optional
  ammo consumption and master/minion relationship; **wiki describes two return values (bool +
  Actor pointer) but Zandronum only returns a boolean**.
- [A_SpawnItemEx](actions/a_spawnitemex.md) — tier A. Spawns an actor at specified offsets with
  controllable velocity and flag-driven property inheritance; **only 19 of the wiki's ~28 `SXF_*`
  flags exist in Zandronum** (`SXF_TRANSFERALPHA`, `SXF_TRANSFERRENDERSTYLE`, `SXF_SETTARGET`/
  `SETTRACER`/`NOPOINTERS`, `SXF_ORIGINATOR`, `SXF_TRANSFERSPRITEFRAME`, `SXF_TRANSFERROLL`,
  `SXF_ISTARGET`/`ISMASTER`/`ISTRACER` are GZDoom additions); **return value is boolean-only**, not
  bool+Actor as shown in the wiki.
- [A_Stop](actions/a_stop.md) — tier A. Zeros actor velocity; **conditionally transitions players
  from See state to Spawn** (not unconditional fallback as wiki suggests).
- [A_StopSound](actions/a_stopsound.md) — tier A. Stops the sound currently playing on the
  specified channel for the calling actor; **only stops sounds with an actor source** (GZDoom's
  A_PlaySound `local` parameter does not exist in Zandronum); wiki's "See also" lists
  `A_StartSound` which does not exist in Zandronum.
- [A_TakeFromTarget](actions/a_takefromtarget.md) — tier A. Removes inventory items from the
  calling actor's current target; includes `TIF_NOTAKEINFINITE` flag to prevent taking infinite
  ammo.
- [A_TakeInventory](actions/a_takeinventory.md) — tier A. Removes inventory items from an actor;
  **critical crash on non-player actors when `TIF_NOTAKEINFINITE` flag is set and map's
  `DF_INFINITE_AMMO` is off** (unguarded `receiver->player` NULL dereference); returns true if
  item existed with non-zero amount before removal, regardless of whether removal was suppressed;
  server-authoritative inventory change in multiplayer.
- [A_Teleport](actions/a_teleport.md) — tier A. Actor teleportation to SpecialSpot-derived
  targets; **Zandronum has only 2 flags (TF_TELEFRAG, TF_RANDOMDECIDE) vs. the wiki's ~12**,
  lacks the `ptr` parameter, and always zeros velocity and floors the actor after teleporting.
- [A_Tracer](actions/a_tracer.md) — tier A. Aggressive homing function for Revenant missiles;
  **time-gated to every 4th tic**, creating spawn-phase-dependent behavior depending on call
  interval (odd calls always home; even non-multiple-of-4 calls home only on matching spawn
  parity; multiples of 4 home only on 4-tic-aligned spawns); spawns trailing smoke and puff;
  requires `SEEKERMISSILE` flag.
- [A_Tracer2](actions/a_tracer2.md) — tier A. Strife homing missile action; **fork divergence:
  SEEKERMISSILE flag not required** (it's the convention that *populates* the tracer field, not a
  precondition the function checks); runs on every call (no gametic gate like A_Tracer), doesn't
  spawn puffs, uses larger seeking angle (~19.7° vs ~16.9° per call), and broadcasts full
  position/angle/velocity to clients on each server call.
- [A_TransferPointer](actions/a_transferpointer.md) — tier A. Transfers a pointer (target,
  master, or tracer) between actors with optional circular-reference safeguards; **wiki
  divergences**: `recipientfield` can be `AAPTR_DEFAULT` (writes to same field as sourcefield),
  and `PTROP_NOSAFEGUARDS` = 3 (not 4); self-reference check is unconditional.
- [A_TurretLook](actions/a_turretlook.md) — tier A. Sound-detection action for Strife actors;
  **does not exist in UZDoom/GZDoom-family**; **runs on both server and client in multiplayer
  without netcode guards** (unlike `A_Look`/`A_Look2`), and **does not perform random state
  animation** (unlike `A_Look2`).
- [A_Wander](actions/a_wander.md) — tier A. Makes an actor wander aimlessly without attacking or
  pursuing targets; **Zandronum version takes no parameters, while the GZDoom-family version the
  wiki describes supports an optional `int flags` parameter with `CHF_*` modifiers**.
- [A_Warp](actions/a_warp.md) — tier A. Warps the calling actor to another actor's position via
  actor pointer; originally designed as a versatile A_Fire analog; **significant wiki/fork
  divergence: Zandronum's 7-parameter version lacks the `heightoffset`, `radiusoffset`, `pitch`
  parameters and several flags** (`WARPF_ABSOLUTEPOSITION`, `WARPF_BOB`, `WARPF_MOVEPTR`,
  `WARPF_USETID`, `WARPF_COPYVELOCITY`, `WARPF_COPYPITCH`) present in the ZDoom Wiki's
  GZDoom/UZDoom-family description.
- [A_WeaponReady](actions/a_weaponready.md) — tier A. Prepares a weapon for firing, bobbing, or
  deselection by setting weapon-state flags; flags persist for the entire state duration until the
  next state transition. **Zandronum-specific: `WRF_ALLOWUSER#` flags and User# weapon states do
  not exist** — see file for details.
- [A_Weave](actions/a_weave.md) — tier A. Generalized sinusoidal weave on two independent axes
  (the `A_BishopMissileWeave`/`A_CStaffMissileSlither` generalization); **the wiki's amplitude is
  off by 8×** — `horzdist`/`vertdist` are scaled by the fixed-point sine math, so `1.0` is ±8 map
  units; XY is collision-checked via `P_TryMove` but Z is a direct write, the phase index advances
  even when the XY move is blocked, and there is no client-mode guard.
- [A_XScream](actions/a_xscream.md) — tier A. Plays a hardcoded gibbed sound (`*gibbed` for
  players, `misc/gibbed` otherwise) on the voice channel; multiplayer-aware with body-queue
  player restoration.
- [A_ZoomFactor](actions/a_zoomfactor.md) — tier A. Per-weapon field-of-view adjustment for zoom
  effects; FOV is **divided by `scale`, not multiplied** (so `scale=2` zooms in 2×); silently
  clamped to `[0.1, 50]`; `ZOOM_NOSCALETURNING` implemented via a negative-value sentinel to
  disable turn-input scaling while preserving the FOV effect; always operates on
  `player->ReadyWeapon`.

### Signature-only

Unlike ACS's flat bulleted tier-C list (one line per name, no other columns), the ~596 DECORATE
action functions are numerous enough, and varied enough in what's worth recording per one (owning
class, whether it takes DECORATE arguments, per-engine presence), that they're tracked as a
generated table instead — see [Actor actions](inventory/actor-actions.md) below. Every row
defaults to tier C until an `actions/<name>.md` file (like `a_look.md`) or a `families/*.md`
promotes it out.

## Inventory tables (generated)

- [Actor flags](inventory/actor-flags.md) — every `DEFINE_FLAG`/`DEFINE_FLAG2`/
  `DEFINE_DEPRECATED_FLAG`/`DEFINE_DUMMY_FLAG` entry across Zandronum's five flag tables
  (`ActorFlags`, `InventoryFlags`, `WeaponFlags`, `PlayerPawnFlags`, `PowerSpeedFlags`).
- [Actor properties](inventory/actor-properties.md) — every `DEFINE_PROPERTY`/
  `DEFINE_CLASS_PROPERTY`/`DEFINE_CLASS_PROPERTY_PREFIX` entry.
- [Actor actions](inventory/actor-actions.md) — every `DEFINE_ACTION_FUNCTION`/
  `DEFINE_ACTION_FUNCTION_PARAMS` entry tree-wide. `A_Look` above is documented as a normal
  archetype-1 file, not as a row here, once it earns one — the table entry stays for the "which
  engine has this action" record but the interesting behavior lives in `actions/a_look.md`.

## Notes (curated, per inventory row)

- [radiusdamagefactor](notes/radiusdamagefactor-actor.md) — per-victim multiplier on radius-attack
  damage that (unlike `DamageFactor`) also scales thrust proportionally, since both derive from
  the same pre-`DamageFactor` value inside `P_RadiusAttack`.
- [powerup.duration](notes/powerup.duration-inventory.md) — sign changes the unit: non-negative is
  raw tics, negative is seconds (`-i * TICRATE`). Easy to set the wrong sign and get a ~0-second
  effect with no compiler warning.
- [+POWERSPEED.NOTRAIL](notes/powerspeed-notrail-flag.md) — a flag, not a property (a natural but
  wrong guess). `APowerSpeed::DoEffect` never reads `Speed`, so even a `Speed 1.0` no-op subclass
  spawns trails and can hijack another `PowerSpeed`'s trail-arbitration slot without this flag. No
  `cl_speedtrails`-style cvar exists as an alternative.
- [NOAUTOFIRE](notes/noautofire.md) — weapon flag. Suppresses **continuous** firing while fire is
  held through consecutive tics in which the weapon is already ready, but does **not** suppress a
  single shot fired the instant the weapon transitions into its ready state with fire already
  down. `P_CheckWeaponFire` is its sole consumer.
- [damagefactor](notes/damagefactor.md) — `P_DamageMobj` applies `DamageFactor`/`DamageFactors`
  unconditionally, with no floor on the incoming damage value — including `TELEFRAG_DAMAGE`. A
  `DamageFactor "<type>", 0` entry genuinely blocks a telefrag-magnitude hit of that type, unlike
  `+INVULNERABLE`, whose own check is explicitly gated on `damage < TELEFRAG_DAMAGE`.
- [maxdropoffheight](notes/maxdropoffheight.md) — only gates `P_Move`'s deliberate AI-stepping
  call into `P_TryMove`; `P_XYMovement` (ordinary momentum-driven movement — knockback, thrust,
  explosions) calls `P_TryMove` with a hardcoded `dropoff=true`, which skips the check entirely
  regardless of the property's configured value.
