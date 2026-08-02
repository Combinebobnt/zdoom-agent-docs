# `Powerup`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki Classes:Powerup (retrieved 2026-08-01, oldid=53729) + verified against Zandronum source `src/g_shared/a_artifacts.h:10` (native C++ class `APowerup : public AInventory`) and `src/g_shared/a_artifacts.cpp`.
**Bucket:** `src/g_shared/a_artifacts.h:10–37` (native C++ class `APowerup : public AInventory`, implementation in `src/g_shared/a_artifacts.cpp`); see also `APowerupGiver` at `a_artifacts.h:40–56` for the related pickup-giver mechanism.

A built-in actor class representing a timed effect that is applied to a player's inventory. Powerups track how long they remain active via an `EffectTics` countdown, and each powerup subclass defines custom behavior when activated (`InitEffect()`), during each game tick (`DoEffect()`), and when expiring (`EndEffect()`). Powerups are always granted to the player through a separate `PowerupGiver` class or through ACS/BCS scripts — they cannot be placed as pickups in the world directly.

## Activation and lifecycle

When a player acquires a powerup (either by picking up a `PowerupGiver` or receiving one through a script), the powerup is created and `CreateCopy()` is called. This method is the critical path for activation:

1. `CreateCopy()` temporarily assigns `Owner = other` (the player) 
2. Calls the virtual `InitEffect()` method, where subclasses apply their startup logic (e.g., setting flags, playing sounds)
3. Clears `Owner` again unless the subclass sets the `IF_CREATECOPYMOVED` flag (used by morph powerups that change the player's physical form)
4. Returns the powerup instance to the inventory system

During each game tick, if `EffectTics > 0`, it decrements by 1. When `EffectTics` reaches 0, the powerup is destroyed, which triggers `Destroy()`. The `Destroy()` method calls `EndEffect()` to allow cleanup (e.g., removing colormap effects) before the powerup is removed.

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

**This page documents Zandronum's implementation, which differs from the ZScript definition shown on the ZDoom wiki:**

- **`Tick()` behavior:** Zandronum only checks `if (EffectTics > 0 && --EffectTics == 0) Destroy()`. A powerup with `EffectTics == 0` (permanent/indefinite duration) will **not** self-destroy on tick — the wiki's ZScript version adds `EffectTics == 0 ||` to that condition. This means Zandronum permanent powerups require explicit removal, not automatic timeout.
- **No `MaxEffectTics` field:** Zandronum's `APowerup` has only `EffectTics`, `BlendColor`, `Mode`, and `Strength` fields. The wiki mentions `MaxEffectTics` and uses it in `HandlePickup()` to track the maximum duration seen — this does not exist in Zandronum.
- **Blink logic is not virtual:** Zandronum does not provide `isBlinking()`, `GetPowerupIcon()`, or `bNoScreenBlink` as virtual methods or flags. The wiki's entire "Methods" section describes ZScript-only features unavailable in Zandronum's DECORATE. The blink threshold is open-coded inline in `GetBlend()`, `DoEffect()`, and the HUD-icon drawing routine (`DrawPowerup()`).
- **No ZScript overrides from DECORATE:** `InitEffect()`, `DoEffect()`, and `EndEffect()` are `protected` virtual methods in the C++ class, but they cannot be overridden from DECORATE — only C++ subclasses (like `APowerInvulnerable`) can override them. DECORATE definitions cannot customize these lifecycle hooks; customization happens only through subclassing in C++.
- **`HandlePickup()` chains to parent:** Zandronum's implementation falls through to `Inventory->HandlePickup(item)` if no matching powerup instance is found in the inventory, whereas the wiki's version returns `false`. This affects how duplicate powerups interact with other inventory items.
- **Teardown via `Destroy()`:** `EndEffect()` is only called from `Destroy()`, which is reached via three paths: `Tick()` timeout, `OwnerDied()` (player death), or explicit destruction. `EndEffect()` is not a separate entry point — understanding that the three paths all converge at `Destroy()` is critical for tracing cleanup logic.
- **Zandronum-specific features:** `IsActiveRune()` checks if this powerup is the player's current rune (used by the Skulltag rune system); `APowerupGiver::PowerupGranted()` and `APowerupGiver::ModifyPowerup()` are extension hooks (empty by default) for giver subclasses; `DoEffect()` and `EndEffect()` also manage `Owner->FixedColormap` (the player body's colormap in addition to the view colormap).

## Properties

See `Powerup.Duration`, `Powerup.Color`/`Colormap`, `Powerup.Mode`, and `Powerup.Strength` in the DECORATE section's `inventory/actor-properties.md` table (curated notes may be in `notes/powerup-*.md` files if documentation earns further detail).

## See also

- `PowerupGiver` class (the world pickup mechanism)
- Built-in powerup subclasses: `PowerInvulnerable`, `PowerInvisibility`, `PowerIronFeet`, `PowerSpeed`, `PowerStrength`, `PowerFlight`, `PowerLightAmp`, etc.
