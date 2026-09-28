# `RuneGiver`

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** engine source only. Read at the Zandronum `master` HEAD checkout (`bdd0f7beb`, reporting `3.3-alpha`); every line number below is HEAD's: the Zandronum source's `src/g_shared/a_artifacts.h:40-56,311-318`, `src/g_shared/a_artifacts.cpp:62-97,120-130,152-159,243-247,271-307,351-380,2294-2322`, `src/g_shared/a_pickups.cpp:745-757,1140-1185,1536,1587-1718`, `src/thingdef/thingdef_properties.cpp:2033-2050,2203-2243`, `src/thingdef/thingdef_parse.cpp:849`, `src/dobjtype.cpp:227-252`, `src/dobject.h:291-298,343-390`, `src/actor.h:1169-1170`, `src/p_interaction.cpp:484-489` (`AActor::Die`), `src/g_game.cpp:2009-2038` (`G_PlayerFinishLevel`), `src/p_setup.cpp:3554,3610,3652-3659` (`P_RemoveThings`), `src/g_shared/sbarinfo_commands.cpp:302-306`, `src/g_doom/doom_sbar.cpp:675-678`, `src/cl_main.cpp:7565-7667` (`client_GiveInventory`), `src/cl_main.cpp:7765-7833` (`client_GivePowerup`), `src/sv_commands.cpp:4054-4073`, `src/sv_main.cpp:2590,2635-2641,4211,4260-4273`, `wadsrc/static/actors/shared/inventory.txt:350-356`, `wadsrc_st/static/actors/skulltagrunes.txt:1-70`. UZDoom absence checked at 5.1.0-pre @98b16b78fc (see "Engine-family divergence").
**Bucket:** native C++ class `ARuneGiver : APowerupGiver` in `src/g_shared/a_artifacts.h:311-318`, implementation `src/g_shared/a_artifacts.cpp:2294-2322`, `IMPLEMENT_CLASS` at `src/g_shared/a_pickups.cpp:1536`; DECORATE declaration `ACTOR RuneGiver : PowerupGiver native` at `wadsrc/static/actors/shared/inventory.txt:350` (always loaded, in `zandronum.pk3`).

A Skulltag-era [`PowerupGiver`](powerup.md) subclass that hands out a **rune**: a powerup that
lasts until the owner dies or picks up a different rune, with at most one rune held at a time. The
class itself is always available; the stock runes built on it are not (see "`Rune.Type`" below).
The individual effect classes (`PowerDrain`, `PowerSpread`, `PowerReflection`, ...) are covered in
[Skulltag powers](../families/skulltag-powers.md); this page covers only what `RuneGiver` adds on
top of `PowerupGiver`.

## What it overrides

`ARuneGiver` overrides exactly two empty hooks that `APowerupGiver::Use` (`a_artifacts.cpp:62-97`)
calls, and inherits everything else from `PowerupGiver`. `Use` runs in this order:

1. Spawn the `PowerupType` power; copy the giver's non-zero `EffectTics`/`BlendColor`/`Mode`/`Strength` onto it.
2. `ModifyPowerup(power)`, the first rune hook.
3. OR the giver's `+INVENTORY.ALWAYSPICKUP`/`+INVENTORY.ADDITIVETIME` onto the power.
4. `power->CallTryPickup(Owner)`. On success, `PowerupGranted(power)`, the second rune hook. On failure the power is discarded and `Use` returns false.

**`ModifyPowerup`** (`a_artifacts.cpp:2317-2322`):

- Sets the power's `EffectTics` to `INT_MAX - 1`. This runs after step 1, so `Powerup.Duration` on
  the giver or on the power class is silently ignored: runes are never timed. This is a huge
  counter that still ticks down (about 710 days at 35 tics/s), not the `EffectTics == 0`
  permanent case described in [`Powerup`](powerup.md). It also stays far above `BLINKTHRESHOLD`,
  so a rune never blinks.
- Sets `+INVENTORY.PERSISTENTPOWER` on the power (see "Death and level change").
- Clears `+INVENTORY.ALWAYSPICKUP` on the power. Step 3 then re-applies the giver's own flag, so
  this only strips a flag declared on the power class. `ALWAYSPICKUP` on the `RuneGiver` subclass
  survives (see the trap below).
- Copies the giver's `Inventory.Icon` onto the power, for the HUD rune slot.

**`PowerupGranted`** (`a_artifacts.cpp:2302-2309`): if the owner's `Rune` pointer is set, destroys
that powerup (running its `EndEffect`), then points `Rune` at the new power. This is the whole
"one rune at a time" rule. It only runs when the power's pickup succeeded.

The `Rune` pointer is a field on `AActor` (`actor.h:1169-1170`, a `TObjPtr<APowerup>`), not on
the player, and nothing in `RuneGiver`'s code checks for a player owner. A destroyed rune reads
back as null through `TObjPtr`'s read barrier (`GC::ReadBarrier`, `dobject.h:291-298`, called by `TObjPtr`'s pointer operators at `dobject.h:368-390`), which is how `Rune` clears
itself when the rune dies without anything writing to it.

## Pickup behavior

`inventory.txt:350-356` gives the base class `Inventory.DefMaxAmount`, `+INVENTORY.INVBAR`,
`+INVENTORY.FANCYPICKUPSOUND` and pickup sound `misc/p_pkup`. So a bare subclass is an
**inventory-bar artifact**: touched, it goes into the inventory, and the rune is granted when the
player uses it. The stock runes (`skulltagrunes.txt`) instead set `Inventory.MaxAmount 0` and
`+INVENTORY.AUTOACTIVATE`, which takes `AInventory::TryPickup`'s zero-`MaxAmount` branch
(`a_pickups.cpp:1606-1627`): the giver joins the inventory just long enough for `Use(true)`, and the
pickup fails (item stays in the world) if `Use` fails.

```decorate
ACTOR MyRuneGiver : RuneGiver
{
	+COUNTITEM
	+INVENTORY.AUTOACTIVATE
	Inventory.MaxAmount 0
	Inventory.Icon "MYRNA0"
	Powerup.Type "MyRunePower"   // any Powerup subclass, see below
	Powerup.Color "Blue", 0.1    // there is no Rune.Color
	States
	{
	Spawn:
		MYRN A -1
		Stop
	}
}
```

What happens when the owner touches a rune (all traced from source, not run in-engine):

| Situation | Result |
|---|---|
| No rune held | Rune granted. |
| Holding a rune of a **different** power class | Old rune destroyed, new one granted. |
| Holding a rune of the **same** power class, giver without `ALWAYSPICKUP` | The held rune's `APowerup::HandlePickup` (`a_artifacts.cpp:271-307`) sees `EffectTics > BLINKTHRESHOLD` and rejects the new power. `Use` fails; an autoactivating giver stays in the world, an inventory-bar one is not consumed. |
| Holding a rune of the **same** power class, giver **with** `+INVENTORY.ALWAYSPICKUP` | **The player loses the rune.** See the trap below. |

**Trap: `+INVENTORY.ALWAYSPICKUP` or `+INVENTORY.ADDITIVETIME` on a `RuneGiver`.** Either flag
makes the held rune's `HandlePickup` accept the duplicate power: it refreshes (or, with
`ADDITIVETIME`, adds `INT_MAX - 1` to, overflowing the signed counter) its own `EffectTics` and
marks the pickup good. `TryPickup` then disposes of the new power object via `GoAwayAndDie`
without attaching it (`a_pickups.cpp:1595-1604`), and `CallTryPickup` reports success. Back in
`Use`, `PowerupGranted` destroys the held rune (it is `Owner->Rune`) and points `Rune` at the
discarded, ownerless copy, which `APowerup::Tick` destroys on its next tic (`Owner == NULL`,
`a_artifacts.cpp:123-126`). Net result: the rune is gone and the giver is consumed. Don't put
either flag on a `RuneGiver`.

**Trap: sharing a power class with an ordinary `PowerupGiver`.** The same `HandlePickup` merge
applies when the rune's power class is also handed out by a timed sphere. Inferred from the same
trace: a rune touched while that sphere's power is active and not yet blinking is rejected; touched
while it is blinking, the existing timed power absorbs the `INT_MAX - 1` tics (becoming effectively
permanent, but not flagged as the rune or `PERSISTENTPOWER`), any previously held rune is
destroyed, and `Rune` ends up pointing at the discarded copy. This is why the stock runes use
dedicated thin subclasses (`RuneDoubleDamage : PowerDamage`, etc.) rather than the `Power*`
classes directly. Give each rune its own power class.

## `Rune.Type`

`Rune.Type <name>` (`thingdef_properties.cpp:2224-2243`, accepted only on `RuneGiver` descendants)
formats `"Rune" + name`, looks the class up with `PClass::FindClass`, and sets the giver's
`PowerupType`. Two fatal parse-time errors:

- `Unknown rune type '<name>' in '<class>'` (`I_Error`) if no class `Rune<name>` exists.
- `Invalid rune type '<name>' in '<class>'` (`I_Error`) if `Rune<name>` exists but is not a
  `Powerup` descendant.

The source comment above it says the property "now only exists for compatibility". Two
consequences worth knowing:

- **The stock `Rune<Name>` classes are not in the base pk3.** `RuneDoubleDamage`,
  `RuneDoubleFiringSpeed`, `RuneDrain`, `RuneSpread`, `RuneHalfDamage`, `RuneRegeneration`,
  `RuneProsperity`, `RuneReflection`, `RuneHighJump`, and `RuneSpeed25` are defined only in
  `wadsrc_st/static/actors/skulltagrunes.txt`, i.e. `skulltag_actors.pk3`, which the engine never
  autoloads (see [Skulltag legacy classes](../concepts/skulltag-legacy-classes.md)). A mod's own
  `RuneGiver` writing `Rune.Type DoubleDamage` is therefore a fatal startup error unless that pk3
  is loaded, even though `RuneGiver` itself is always present.
- **`FindClass` is an immediate lookup, not a tentative one.** `PClass::FindClass`
  (`dobjtype.cpp:227-252`) is a plain hash lookup, so `Rune<name>` must already have been parsed
  when the giver's `Rune.Type` line is parsed. Defining the power class later in the same lump, or
  in a later lump, still hits `Unknown rune type`. (Traced, not run.)

**Workarounds.** Either define your own `Rune<Name>` `Powerup` subclass *before* the giver, or,
simpler, skip `Rune.Type` and use `Powerup.Type` (`thingdef_properties.cpp:2203-2218`). It is
registered on `PowerupGiver`, so it applies to `RuneGiver` subclasses, accepts any `Powerup`
class (trying a `Power` prefix if the bare name doesn't resolve to one), and resolves tentatively.
Declaration order only stops mattering when the power class's name starts with `Power`: for a
not-yet-declared `Rune<Name>` it creates a `PowerRune<Name>` placeholder and startup aborts with
"Class ... referenced but not defined", so declare such a class before the giver. The rune behavior comes from `ARuneGiver`'s two hooks, not from
the power class's name.

## `Rune.Color` does not exist

The only `rune.*` property is `rune.type`. `Rune.Color` fails with the parser's fatal
`"<property>" is an unknown actor property` script error (`thingdef_parse.cpp:849`). Use
`Powerup.Color` on the giver instead: it accepts `PowerupGiver` descendants
(`thingdef_properties.cpp:2033-2050`), `Use` copies a non-zero giver blend onto the power, and
`ModifyPowerup` leaves it alone. `Powerup.Mode`/`Powerup.Strength` pass through the same way;
`Powerup.Duration` does not (see above).

## Death and level change

- **Death:** `AActor::Die` calls `OwnerDied` on every inventory item (`p_interaction.cpp:484-489`),
  and `APowerup::OwnerDied` destroys the powerup (`a_artifacts.cpp:364-367`). The rune is lost,
  not dropped: `APowerup::CreateTossable` returns null (`a_artifacts.cpp:351-354`), and no
  rune-dropping code exists anywhere in `src/`.
- **Level change:** `G_PlayerFinishLevel` (`g_game.cpp:2009-2038`) destroys every powerup in
  deathmatch. Outside deathmatch it keeps `+INVENTORY.PERSISTENTPOWER` powerups, so a rune
  survives a map change in co-op/single player. (Only this function was traced for travel.)
- **`sv_norunes`** (`DF2_NO_RUNES`, `dmflags2` bit 2): `P_RemoveThings` (`p_setup.cpp:3652-3659`)
  removes every map thing descending from `RuneGiver` at map load, but only inside the
  `deathmatch || teamgame || alwaysapplydmflags` block (`p_setup.cpp:3610`). It does not affect
  runes given by scripts or spawned later.

## HUD

`APowerup::IsActiveRune` (`a_artifacts.cpp:377-380`) is true for the owner's current `Rune`, and
`APowerup::DrawPowerup` returns early for it (`a_artifacts.cpp:245-247`), so a rune never appears
in the ordinary powerup-icon row. It is drawn instead through the dedicated rune slot: SBARINFO's
`drawimage runeicon` (`sbarinfo_commands.cpp:302-306`, draws `mo->Rune`'s `Icon`) and Doom's
built-in fullscreen HUD (`doom_sbar.cpp:675-678`). That icon is the giver's `Inventory.Icon`, copied
by `ModifyPowerup`, so set `Inventory.Icon` on the `RuneGiver`, not on the power class.

## Netcode

- **Live pickup:** the server sends `SVC_GIVEINVENTORY` for the *giver* class
  (`a_pickups.cpp:1165-1171`), and the client's `client_GiveInventory` (`cl_main.cpp:7565-7667`)
  spawns it and runs `CallTryPickup` locally. The client therefore re-runs `Use`, `ModifyPowerup`
  and `PowerupGranted` itself and sets its own `Rune` pointer.
- **Full update / inventory reset** (`SERVER_SendFullUpdate`, `sv_main.cpp:2635-2641`;
  `SERVER_ResetInventory`, `sv_main.cpp:4260-4273`): powerups are resent with `SVC_GIVEPOWERUP`,
  which carries an is-rune byte and omits `EffectTics` for a rune (`sv_commands.cpp:4054-4073`).
  `client_GivePowerup` (`cl_main.cpp:7765-7833`) then sets that client's copy to `EffectTics = 0`
  and assigns `Rune`. The icon is sent separately (`SetInventoryIcon`) because it came from the
  giver, not the power class.
- Inferred from that: on a client that received the rune this way, `EffectTics` is 0 rather than
  `INT_MAX - 1`. `Tick` treats 0 as never-expire, so the rune persists, but `APowerup::GetBlend`
  (`a_artifacts.cpp:152-159`) returns no blend at 0 tics and `DoEffect`'s colormap branch needs
  `EffectTics > 0`. A rune's `Powerup.Color` screen tint may therefore be missing for a player who
  joined or was resynced after picking it up. Not tested in-engine.

## Engine-family divergence

UZDoom has no rune system. Checked at 5.1.0-pre @98b16b78fc: there is no `RuneGiver` class in
DECORATE or ZScript, no `Rune.Type` property, no owner-side current-rune pointer, and
`PowerupGiver` has no granted/modify hooks for a subclass to override. The only trace is the
`DF2_NO_RUNES` dmflag, left commented out in `src/doomdef.h`. A mod that needs one-rune-at-a-time
behavior on UZDoom has to implement it itself (for example in a ZScript `PowerupGiver` subclass).

## See also

- [`Powerup`](powerup.md): the `PowerupGiver`/`Powerup` split, `HandlePickup`'s refresh rules and
  the lifecycle this class reuses.
- [Skulltag powers](../families/skulltag-powers.md): the `Power*` classes the stock runes wrap.
- [Skulltag legacy classes](../concepts/skulltag-legacy-classes.md): where the stock runes live and
  what else needs `skulltag_actors.pk3`.
