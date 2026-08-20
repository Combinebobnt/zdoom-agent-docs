# Using a `Powerup` subclass as an inert countdown timer

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes — the trick (a `PowerSpeed` subclass with `Speed 1.0` used
purely as a self-expiring, side-effect-free duration gate) works on both engines; UZDoom requires
closing one extra side-effect channel absent from Zandronum, see the divergence section below.
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Source-derived (no wiki page consulted) — verified against `src/g_shared/
a_artifacts.cpp` (`APowerSpeed::DoEffect`, `APowerSpeed::GetSpeedFactor`, `APowerup::CreateCopy`),
`src/thingdef/thingdef_properties.cpp` (`Speed`, `Inventory.Icon`), and `src/thingdef/
thingdef_data.cpp` (the `PowerSpeed.NoTrail` flag).

A common DECORATE trick: define a `Powerup` subclass purely so `A_JumpIfInventory` has something
to check with a self-expiring duration, without wanting any of the powerup's actual gameplay
effect. Example: gating a temporary bonus (a faster reload animation, a scripted buff window) on a
timer, where the timer itself should have zero side effects of its own.

`PowerSpeed` is the usual base for this, since `Speed 1.0` is an exact no-op:

```text
ACTOR MyInertTimer : PowerSpeed
{
  Speed 1.0
  Powerup.Duration -60
  Inventory.Icon ""
  +POWERSPEED.NOTRAIL
}
```

## Why `Speed 1.0` is safe

**On Zandronum:** `Speed` is a fixed-point actor property (`DEFINE_PROPERTY(speed, F, Actor)`,
`thingdef_properties.cpp`), so `1.0` parses to exactly `FRACUNIT` with no rounding. All three
consumers of `APowerSpeed::GetSpeedFactor()` treat `FRACUNIT` as strict identity:

- `p_user.cpp` — `forward = FixedMul(forward, factor)`; `FixedMul(a, FRACUNIT) == a` bit-exactly.
- `g_game.cpp` — an anti-cheat "turbo" movement threshold that only widens when
  `Inventory->GetSpeedFactor() > FRACUNIT`, so exactly 1.0 never touches it.
- `p_teleport.cpp` — the post-teleport input-freeze is skipped only when
  `Inventory->GetSpeedFactor() <= FRACUNIT`, so 1.0 keeps stock (frozen) behavior.

`APowerSpeed::GetSpeedFactor()` also chains multiplicatively across every active `PowerSpeed` the
player holds (`FixedMul(Speed, Inventory->GetSpeedFactor())`, a recursive walk down the inventory
list), so a `Speed 1.0` instance multiplies any other active speed powerup by 1.0 — it cannot
interfere with a real speed boost stacked alongside it.

**On UZDoom:** the same `Speed 1.0` value is safe, but by a differently-shaped mechanism —
`PowerSpeed::GetSpeedFactor()` is a ZScript `override` that just returns `Speed` (`powerups.zs`,
class `PowerSpeed`); the multiplicative chaining happens one level up, in the player-movement code
(`actors/player/player.zs`), which walks the whole inventory list starting from a factor of `1` and
multiplies in each item's own `GetSpeedFactor()` result in turn — not inside `PowerSpeed` itself.
The net effect is identical — a factor of exactly `1` is the multiplicative identity either way, so
an inert timer still cannot perturb a real speed boost stacked alongside it. UZDoom's turbo-cheat
check (`g_game.cpp`, gated on the `turbo` cvar) is unrelated to `GetSpeedFactor()` entirely — it
compares raw `forwardmove` against a fixed threshold and only logs a console message, so the
Zandronum-specific "anti-cheat threshold"
concern above has no UZDoom analog to worry about at all. The teleport-freeze mechanism, however,
changed shape enough on UZDoom that it opens a new channel the Zandronum trick doesn't have to
close — see the divergence section below.

## Three side-effect channels that must each be closed independently

None of these are implied by `Speed 1.0` — each is a separate mechanism that fires regardless of
the speed value, and each must be silenced on its own:

1. **Speed trail.** On both engines, the base `DoEffect` never reads `Speed` at all — it spawns
   `PlayerSpeedTrail` afterimages purely based on player velocity, and an arbitration loop means
   only the *last* `PowerSpeed` without the no-trail marker in the inventory actually draws a
   trail — an inert timer that leaves it unset can silently suppress or hijack a legitimate speed
   powerup's trail. **On Zandronum**, the flag to suppress this is **`+POWERSPEED.NOTRAIL`** — a
   flag only (`PSF_NOTRAIL`, registered via `DEFINE_FLAG(PSF, NOTRAIL, APowerSpeed, SpeedFlags)`);
   there is no `PowerSpeed.NoTrail` property on Zandronum, so writing it as a property is a
   natural and wrong guess there. **On UZDoom**, this is inverted: `NoTrail` is now declared as a
   plain `int` field with a `NoTrail` property declared as the primary form, and the old
   `+POWERSPEED.NOTRAIL` flag syntax is kept only as a compatibility `FlagDef` over that same field
   — the source's own comment on the `FlagDef` line notes it exists purely for backward
   compatibility with the pre-ZScript flag-only form (`powerups.zs`, class `PowerSpeed`). Both
   spellings still work on UZDoom and are equivalent — but `PowerSpeed.NoTrail 1` is the form
   UZDoom's own class actually declares as canonical, so a DECORATE file aimed at both engines
   should keep using the flag form (`+POWERSPEED.NOTRAIL`) for portability rather than switching
   to the UZDoom-preferred property form. No `cl_speedtrails`-style cvar exists on either
   engine to suppress trails client-side instead; the class-level marker is the only lever on both.
2. **HUD icon.** `PowerSpeed` sets `Inventory.Icon "SPBOOT0"` by default on both engines, drawn
   whenever the icon is valid. Set **`Inventory.Icon ""`** — an empty string is the supported way
   to null it on both: Zandronum maps `""` to `Icon.SetNull()` in `thingdef_properties.cpp`, and
   UZDoom's `Powerup`/`Inventory` `Icon` property (a plain `TextureID` field, `inventory.zs`)
   resolves the same way through its own texture-lookup path.
3. **Screen blend.** Only relevant if the subclass declares a `Powerup.Color` — leaving it unset
   means `BlendColor == 0` and `DoEffect`'s blend application is a no-op on both engines. Simply
   don't add one.

## Engine-family divergence: a fourth side-effect channel on UZDoom (teleport-freeze suppression)

On Zandronum, whether a teleporting player gets the usual half-second input freeze is decided
purely by the *aggregate* `GetSpeedFactor()` value at the moment of teleport (`p_teleport.cpp`,
`Inventory->GetSpeedFactor() <= FRACUNIT` → freeze applies). An inert `Speed 1.0` timer never moves
that aggregate away from `1.0`, so it is invisible to this check by construction — no fourth
channel to close.

On UZDoom this mechanism was rebuilt as a per-item flag rather than a speed-value threshold:
`Powerup`/`PowerupGiver` expose a `+INVENTORY.NOTELEPORTFREEZE` flag (backed by `bNoTeleportFreeze`,
read through the virtual `GetNoTeleportFreeze()`), and `PlayerPawn::GetTeleportFreezeTime()`
(`actors/player/player.zs`) skips the freeze if *any* held item's `GetNoTeleportFreeze()` returns
true — an OR across the whole inventory, unrelated to `Speed`'s numeric value. Critically,
`PowerSpeed`'s own `Default` block on UZDoom sets `+INVENTORY.NOTELEPORTFREEZE` unconditionally
(`powerups.zs`, class `PowerSpeed`) — every `PowerSpeed` subclass inherits it, including an inert
timer with `Speed 1.0`. This means the identical DECORATE definition that is teleport-freeze-neutral
on Zandronum will unconditionally suppress the post-teleport freeze on UZDoom, purely as a side
effect of subclassing `PowerSpeed` — independent of the `Speed` value chosen to neutralize the
movement effect. A timer meant to be fully inert on UZDoom needs to close this fourth channel
explicitly, by clearing the inherited flag: add `-INVENTORY.NOTELEPORTFREEZE` to the subclass.

(This lines up with — and is a more specific, `PowerSpeed`-level instance of — the
`+INVENTORY.NOTELEPORTFREEZE` propagation divergence already documented in
[`Powerup`](../classes/powerup.md)'s "DECORATE vs. ZScript — Zandronum differences" section; that
entry covers the flag existing at all and `PowerupGiver` propagating it, this entry covers the fact
that `PowerSpeed` specifically bakes the flag into its own class default, so the channel is open
even when the timer is given directly with no `PowerupGiver` involved.)

## Giving it directly, no `PowerupGiver` needed

`A_GiveInventory("MyInertTimer")` activates the powerup directly and the held item keeps its own
class name on both engines: Zandronum's `APowerup::CreateCopy` returns `this`, and UZDoom's ZScript
`Powerup::CreateCopy` override (`powerups.zs`) equivalently returns the instance itself, rather
than either one spawning/re-homing a different instance — so `A_JumpIfInventory("MyInertTimer", 1,
...)` finds it under the exact name given on both. A `PowerupGiver` wrapper is not required — and
if one is used anyway, the item that ends up in the player's inventory is the **`Powerup.Type`
class**, not the giver's own class (confirmed identical on UZDoom's `PowerupGiver::Use()`,
`powerups.zs`), so
`A_JumpIfInventory` must check the `Powerup.Type` name either way.

## Re-pickup / refresh semantics

See the "Re-pickup and refresh semantics" section of [`Powerup`](../classes/powerup.md) for how a
second grant while the timer is still running is handled — by default it is silently discarded
unless `+INVENTORY.ALWAYSPICKUP` or `+INVENTORY.ADDITIVETIME` is set on the timer class. For a
timer meant to refresh to full duration on every re-trigger, `+INVENTORY.ALWAYSPICKUP` is the
correct flag.

If the timer is granted from inside a `CustomInventory`'s `Pickup:` state chain (e.g. alongside an
existing effect on a berserk-style item), a discarded re-give does not block the surrounding
pickup — see [`CustomInventory`](../classes/custominventory.md)'s `CallStateChain` OR-aggregation
section and its `+INVENTORY.ALWAYSPICKUP` backstop note.

## See also

- [`Powerup`](../classes/powerup.md) — base class lifecycle, re-pickup semantics.
- [`powerup.duration`](../notes/powerup.duration-inventory.md) — sign convention for the duration value.
- [`PowerSpeed.NoTrail` flag](../notes/powerspeed-notrail-flag.md).
