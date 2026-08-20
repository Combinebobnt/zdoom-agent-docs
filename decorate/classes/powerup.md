# `Powerup`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki Classes:Powerup (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=Classes%3APowerup&oldid=53729) + verified against Zandronum source `src/g_shared/a_artifacts.h:10` (native C++ class `APowerup : public AInventory`) and `src/g_shared/a_artifacts.cpp`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** native C++ class in Zandronum (`src/g_shared/a_artifacts.h:10–37`; `APowerup : public AInventory`, implementation in `src/g_shared/a_artifacts.cpp`; see also `APowerupGiver` at `a_artifacts.h:40–56` for the related pickup-giver mechanism); ZScript class in UZDoom (`wadsrc/static/zscript/actors/inventory/powerups.zs:84-328`; `class Powerup : Inventory`, an ordinary scripted class with no native backing beyond what `Inventory` itself provides; `PowerupGiver` at `powerups.zs:20-82`).
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

A built-in actor class representing a timed effect that is applied to a player's inventory. Powerups track how long they remain active via an `EffectTics` countdown, and each powerup subclass defines custom behavior when activated (`InitEffect()`), during each game tick (`DoEffect()`), and when expiring (`EndEffect()`). Powerups are always granted to the player through a separate `PowerupGiver` class or through ACS/BCS scripts — they cannot be placed as pickups in the world directly.

## Activation and lifecycle

When a player acquires a powerup (either by picking up a `PowerupGiver` or receiving one through a script), the powerup is created and `CreateCopy()` is called. This method is the critical path for activation:

1. `CreateCopy()` temporarily assigns `Owner = other` (the player) 
2. Calls the virtual `InitEffect()` method, where subclasses apply their startup logic (e.g., setting flags, playing sounds)
3. Clears `Owner` again unless the subclass sets the `IF_CREATECOPYMOVED` flag (used by morph powerups that change the player's physical form)
4. Returns the powerup instance to the inventory system

During each game tick, if `EffectTics > 0`, it decrements by 1. When `EffectTics` reaches 0, the powerup is destroyed, which triggers `Destroy()`. The `Destroy()` method calls `EndEffect()` to allow cleanup (e.g., removing colormap effects) before the powerup is removed. (This is Zandronum's `Tick()` condition specifically — UZDoom's differs; see "DECORATE vs. ZScript — Zandronum differences" below.)

A powerup also expires immediately if its owner dies (the `OwnerDied()` method calls `Destroy()`), ensuring powerups don't persist beyond the player they were applied to.

## Powerup vs. PowerupGiver

A common point of confusion: the **powerup itself** is not a pickup. `PowerupGiver` (a separate class at `a_artifacts.h:40`) is the world item (like a radiation suit, soul sphere, or invulnerability sphere). When a player picks up a `PowerupGiver`, its `Use()` method is called, which:

1. Spawns an instance of the powerup class named in `PowerupType`
2. Optionally overrides the powerup's `EffectTics`, `BlendColor`, `Mode`, and `Strength` fields with values from the giver itself
3. Tries to give the powerup to the player via `CallTryPickup(Owner)`

If the pickup succeeds, the powerup goes into the player's inventory and `CreateCopy()` is invoked. If it fails, the spawned powerup is destroyed. **Powerups themselves cannot be placed in the world or picked up directly** — a modder must define both a `PowerupGiver` (the pickup) and a `Powerup` subclass (the effect).

In DECORATE, all fields and flags that affect a powerup's behavior (`Powerup.Duration`, `Powerup.Color`, `Powerup.Mode`, `Powerup.Strength`) can be declared on either class — if declared on the giver, they transfer to the powerup when spawned. This transfer is conditional: if the giver's field is zero or `NAME_None`, it does not override the powerup's own default (e.g., a `PowerupGiver` with `Powerup.Duration 0` does not force a 0-tic override; the powerup's own duration is used).

## Timed behavior and color blending

Each powerup carries `EffectTics` (remaining duration in game tics, where 1 tic = 1/35 second by default), `BlendColor` (a color+alpha to blend onto the screen), and optional `Mode` and `Strength` fields for subclass-specific tuning.

The base `DoEffect()` method (called each tick while the powerup is active) applies the colormap/blend effect from `BlendColor` to the player's view. If `EffectTics <= BLINKTHRESHOLD` (a hardcoded engine constant), the blend blinks on and off (toggled each 8 tics) to signal the powerup is about to expire — this is used to show invulnerability or invisibility blinking, for example. `EndEffect()` clears any applied colormap when the powerup expires.

Subclasses override `InitEffect()` and/or `DoEffect()` to apply their own effects — `APowerInvulnerable` sets `MF2_INVULNERABLE`, `APowerInvisibility` modifies rendering, `APowerIronFeet` overrides damage absorption, etc.

## DECORATE vs. ZScript — Zandronum differences

**This section documents where Zandronum's native-C++ implementation differs from the ZScript-based implementation** — originally written up against the ZDoom wiki's ZScript description, and now independently re-verified against UZDoom's actual current source (`wadsrc/static/zscript/actors/inventory/powerups.zs`, UZDoom 5.0.0-pre @5a9b0ec511): every bullet below holds true for UZDoom's real `Powerup`/`PowerupGiver` classes, not just for the wiki's account of them.

- **`Tick()` behavior:** Zandronum only checks `if (EffectTics > 0 && --EffectTics == 0) Destroy()`. A powerup with `EffectTics == 0` (permanent/indefinite duration) will **not** self-destroy on tick — the wiki's ZScript version adds `EffectTics == 0 ||` to that condition. This means Zandronum permanent powerups require explicit removal, not automatic timeout.
- **No `MaxEffectTics` field:** Zandronum's `APowerup` has only `EffectTics`, `BlendColor`, `Mode`, and `Strength` fields. The wiki mentions `MaxEffectTics` and uses it in `HandlePickup()` to track the maximum duration seen — this does not exist in Zandronum.
- **Blink logic is not virtual:** Zandronum does not provide `isBlinking()`, `GetPowerupIcon()`, or `bNoScreenBlink` as virtual methods or flags. The wiki's entire "Methods" section describes ZScript-only features unavailable in Zandronum's DECORATE. The blink threshold is open-coded inline in `GetBlend()`, `DoEffect()`, and the HUD-icon drawing routine (`DrawPowerup()`).
- **No overrides from DECORATE:** `InitEffect()`, `DoEffect()`, and `EndEffect()` are `protected` virtual methods in the C++ class, but they cannot be overridden from DECORATE — only C++ subclasses (like `APowerInvulnerable`) can override them. DECORATE definitions cannot customize these lifecycle hooks; customization happens only through subclassing in C++. See "Engine-family divergence: subclassing `Powerup`'s lifecycle hooks" below for how this same restriction, and its one escape hatch, plays out on UZDoom.
- **`HandlePickup()` chains to parent:** Zandronum's implementation falls through to `Inventory->HandlePickup(item)` if no matching powerup instance is found in the inventory, whereas the wiki's version returns `false`. This affects how duplicate powerups interact with other inventory items.
- **Teardown via `Destroy()`:** `EndEffect()` is only called from `Destroy()`, which is reached via three paths: `Tick()` timeout, `OwnerDied()` (player death), or explicit destruction. `EndEffect()` is not a separate entry point — understanding that the three paths all converge at `Destroy()` is critical for tracing cleanup logic.
- **Zandronum-specific features:** `IsActiveRune()` checks if this powerup is the player's current rune (used by the Skulltag rune system); `APowerupGiver::PowerupGranted()` and `APowerupGiver::ModifyPowerup()` are extension hooks (empty by default) for giver subclasses; `DoEffect()` and `EndEffect()` also manage `Owner->FixedColormap` (the player body's colormap in addition to the view colormap). Confirmed absent from UZDoom's source: no `IsActiveRune`, `PowerupGranted`, `ModifyPowerup`, or separate actor-level `FixedColormap` field exists anywhere in the UZDoom tree — UZDoom's `DoEffect()`/`EndEffect()` only ever touch `Owner.player.fixedcolormap`.
- **`PowerupGiver::Use()` flag propagation — clean agreement, with one UZDoom-only addition:** both engines copy `+INVENTORY.ALWAYSPICKUP`/`+INVENTORY.ADDITIVETIME` from the giver onto the freshly-spawned powerup before the pickup attempt (Zandronum: `power->ItemFlags |= ItemFlags & (IF_ALWAYSPICKUP|IF_ADDITIVETIME);`; UZDoom: an equivalent bitwise-OR of the giver's `bAlwaysPickup`/`bAdditiveTime` fields onto the spawned powerup's own fields) — so the "Trap" note under "Re-pickup and refresh semantics" below applies identically to a `PowerupGiver`-driven re-give on either engine. UZDoom additionally propagates a third flag, `+INVENTORY.NOTELEPORTFREEZE` (`bNoTeleportFreeze`, read back via `Powerup::GetNoTeleportFreeze()`), which suppresses `PlayerPawn::GetTeleportFreezeTime()`'s post-teleport input-freeze while the powerup is held — this mechanism (`TeleportFreezeTime`/`GetTeleportFreezeTime`/`GetNoTeleportFreeze`) does not exist anywhere in Zandronum's source at all, not just on `Powerup`.

## Engine-family divergence: subclassing `Powerup`'s lifecycle hooks

On Zandronum, `APowerup` is a native C++ class, and `InitEffect()`/`DoEffect()`/`EndEffect()` are C++ virtual methods — a DECORATE actor definition can never override them, and adding a new override means patching the engine itself (as `APowerInvulnerable`, `APowerInvisibility`, etc. do).

On UZDoom, `Powerup` is an ordinary ZScript class (`wadsrc/static/zscript/actors/inventory/powerups.zs`) with no native backing beyond what `Inventory` provides, and `InitEffect()`/`DoEffect()`/`EndEffect()` are declared `virtual` in ZScript. This means a mod's **own** ZScript class — shipped in a pk3, no engine rebuild required — can subclass `Powerup` and override these hooks directly, the same way `PowerInvulnerable` etc. do internally. DECORATE itself still cannot override them on UZDoom either (DECORATE has no virtual-override syntax on either engine), so a DECORATE-only mod sees no change in capability — but a project that ports (or partly ports) to ZScript on UZDoom gains a customization path that has no Zandronum equivalent short of engine-side C++.

## Re-pickup and refresh semantics

When a player who already holds an active instance of a powerup class receives another one (via a
second `PowerupGiver` touch or a second `A_GiveInventory`), `APowerup::HandlePickup`
(`a_artifacts.cpp`) decides what happens, reading flags off the **incoming** freshly-spawned
instance:

1. If the incoming item's `EffectTics == 0`, the pickup is a no-op that still reports success.
2. If the incoming item has `+INVENTORY.ADDITIVETIME`, its `EffectTics` is **added** to the
   existing instance's remaining time — unbounded, no cap.
3. Otherwise, if the existing instance's remaining `EffectTics` is greater than `BLINKTHRESHOLD`
   (128 tics, ~3.66s at 35 tics/sec) **and** the incoming item does not have
   `+INVENTORY.ALWAYSPICKUP`, the re-give is **silently discarded** — `HandlePickup` returns
   `true` (so the surrounding pickup doesn't outright fail) but without setting `IF_PICKUPGOOD`,
   which in turn makes `AInventory::TryPickup` return `false` for this specific give. The
   remaining duration is left untouched.
4. Otherwise (little time left, or `+INVENTORY.ALWAYSPICKUP` set), `EffectTics` is refreshed to
   the incoming item's value — but only if that value is *greater* than what remains; this branch
   never shortens an existing timer.

**Trap:** a re-give with more than ~3.66s remaining is silently discarded unless the powerup class
carries `+INVENTORY.ALWAYSPICKUP` or `+INVENTORY.ADDITIVETIME`. This surprises modders who expect
"pick it up again" to always refresh to full duration.

This `HandlePickup` failure does **not** propagate up to block a `CustomInventory`'s or
`PowerupGiver`'s overall pickup succeeding — see [`CustomInventory`](custominventory.md)'s
`CallStateChain` OR-aggregation section and its `+INVENTORY.ALWAYSPICKUP` backstop note for why a
chain containing a discarded re-give still consumes the world item normally.

**Clean agreement on UZDoom.** `Powerup::HandlePickup` in `powerups.zs` implements the identical
four-step logic (same `EffectTics == 0` no-op, same unbounded `bAdditiveTime` add, same
`BLINKTHRESHOLD` discard-unless-`bAlwaysPickup` gate, same "only refresh if strictly greater"
rule) — `BLINKTHRESHOLD` is `4*32 = 128` tics on UZDoom too. The only structural difference is
bookkeeping: UZDoom additionally tracks `MaxEffectTics = Max(EffectTics, MaxEffectTics)` on the
additive-time and refresh branches (see "No `MaxEffectTics` field" above), which records the
largest duration seen but does not change the "unbounded, no cap" or "never shortens" behavior
described above. The Trap applies identically on both engines.

## Destruction paths — no leak across death or level change

A `Powerup` cannot outlive the player session it was granted in:

- **Player death:** `OwnerDied()` unconditionally calls `Destroy()` for every `APowerup` the
  player holds (invoked from the inventory-notification loop in `AActor::Die`,
  `p_interaction.cpp`).
- **Level change:** `G_PlayerFinishLevel` (`g_game.cpp`) destroys every `APowerup` in the
  traveling inventory unless `(!deathmatch) && (mode == FINISH_SameHub) && (IF_HUBPOWER ||
  IF_PERSISTENTPOWER)` — i.e. a powerup persists across a level transition only within the same
  hub, in non-deathmatch, and only if it explicitly opts in with `+INVENTORY.HUBPOWER` or
  `+INVENTORY.PERSISTENTPOWER`.
  - **UZDoom:** the equivalent check lives in `PlayerPawn::PlayerFinishLevel`
    (`wadsrc/static/zscript/actors/player/player.zs:2187-2225`, itself headed by a comment
    crediting it as the `G_PlayerFinishLevel` counterpart) and reads `deathmatch ||
    ((mode != FINISH_SameHub || !item.bHUBPOWER) && !item.bPERSISTENTPOWER)` — the same
    expression Zandronum's `src/g_game.cpp:2032-2033` actually contains. Worked out as a plain
    boolean, a powerup survives iff `!deathmatch && (bPERSISTENTPOWER || (bHUBPOWER && mode ==
    FINISH_SameHub))` — `+INVENTORY.PERSISTENTPOWER` alone survives *any* non-deathmatch level
    transition, hub or not, while `+INVENTORY.HUBPOWER` alone only survives a same-hub one. Player
    death is handled the same way as Zandronum: `Powerup::OwnerDied()` unconditionally calls
    `Destroy()`.
- **Belt-and-braces:** `Tick()` also self-destroys if `Owner == NULL` — true on UZDoom's `Tick()`
  too (`if (Owner == NULL) Destroy();`, checked before the `EffectTics` condition).

## `PowerStrength`'s permanence is not a duration special case

`PowerStrength` (vanilla Doom's berserk effect) is granted with `Powerup.Duration 1` — genuinely 1
tic, not a magic "permanent" sentinel value; there is no special-casing of small or positive
duration values anywhere in the property parser or in `Tick()`. Its apparent permanence comes
entirely from `APowerStrength::Tick()` overriding the countdown:

```c
EffectTics += 2;
Super::Tick();   // decrements EffectTics by 1
```

Net effect: `EffectTics` rises by 1 every tic and never reaches 0, so the base `Tick()`'s
`if (EffectTics > 0 && --EffectTics == 0) Destroy()` condition never fires. The same rising
counter also drives `APowerStrength::GetBlend()`'s berserk-red fade. A modder reading
`Powerup.Duration 1` on `PowerStrength` and inferring "1 = permanent" as a general convention
would be wrong — the mechanism is specific to this one subclass's `Tick()` override, not a
property-level convention.

**Clean agreement on UZDoom.** `PowerStrength::Tick()` in `powerups.zs` is `EffectTics += 2;
Super.Tick();` — structurally identical to the Zandronum excerpt above. This also means UZDoom's
own `Tick()` divergence noted above (the `EffectTics == 0 ||` self-destroy clause) never comes
into play for berserk: by the time `Super.Tick()` runs each frame, `EffectTics` has already been
incremented past 0, so the `EffectTics == 0` branch never fires for this subclass on either
engine.

## Properties

See `Powerup.Duration`, `Powerup.Color`/`Colormap`, `Powerup.Mode`, and `Powerup.Strength` in the DECORATE section's `inventory/actor-properties.md` table (curated notes may be in `notes/powerup-*.md` files if documentation earns further detail).

## See also

- `PowerupGiver` class (the world pickup mechanism)
- Built-in powerup subclasses: `PowerInvulnerable`, `PowerInvisibility`, `PowerIronFeet`, `PowerSpeed`, `PowerStrength`, `PowerFlight`, `PowerLightAmp`, etc.
