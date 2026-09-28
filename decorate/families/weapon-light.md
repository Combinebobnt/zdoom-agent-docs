# Weapon light actions

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** ZDoom Wiki `A_Light` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_Light&oldid=42814) and `A_Light0` (retrieved
2026-08-01, https://zdoom.org/w/index.php?title=A_Light0&oldid=47264 — this single wiki page also documents `A_Light1`, `A_Light2`, and
`A_LightInverse`) + verified against the Zandronum source's `src/p_pspr.cpp:1353-1385` (`A_Light0`,
`A_Light1`, `A_Light2`, `A_Light`), `src/g_strife/a_strifeweapons.cpp:1082-1088` (`A_LightInverse`),
`src/r_bsp.cpp:1068` (extralight-to-render scaling), `src/r_main.cpp:569-572` (inverse-colormap
sentinel handling), `src/gl/scene/gl_scene.cpp:855-858` (GL sentinel handling),
`src/r_utility.cpp:901` (per-frame copy of the player's value), and
`wadsrc/static/actors/shared/inventory.txt:15-19` (DECORATE declarations, all on `Inventory`); `A_Light` additionally cross-checked against UZDoom's
`wadsrc/static/zscript/actors/actor.zs:895`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Shared implementation. In Zandronum, all five are declared with `action native` on
the `Inventory` class (`wadsrc/static/actors/shared/inventory.txt:15-19`), so all five are
callable only from `Inventory`-derived actors. `A_Light0`, `A_Light1`, `A_Light2` (`DEFINE_ACTION_FUNCTION`)
and the parameterized `A_Light` (`DEFINE_ACTION_FUNCTION_PARAMS`) are thin wrappers in
`src/p_pspr.cpp` that all assign directly to the owning player's `extralight` field.
`A_LightInverse` is grouped with them because the wiki and both source files treat it as a sibling
of the same "weapon light" family, but it is defined separately (`DEFINE_ACTION_FUNCTION(AActor, ...)`
in `src/g_strife/a_strifeweapons.cpp`) and repurposes the same field via an `INT_MIN` sentinel to
trigger an inverted-colormap render effect rather than a brightness offset. See "Wiki/engine
divergence: `A_LightInverse`" below. The `AActor` in its C++ macro only names the function's
descriptor and does not widen its DECORATE callability. In UZDoom, all five are ordinary ZScript methods
declared directly on the base `Actor` class (`wadsrc/static/zscript/actors/actor.zs:891-895`), so
none is restricted. See "Engine-family divergence: class restriction" below.
**Family rationale:** Shared implementation — four of the five members are interchangeable
brightness-level wrappers around one field; the fifth shares the field and the wiki's own grouping
but not the underlying mechanism, which is why its divergence gets its own section instead of
being silently folded in as identical.

All five actions manipulate a player's `extralight` field, most commonly from a weapon's `Flash`
state to briefly illuminate the surroundings during a muzzle flash.

## `void A_Light0()`

Sets `extralight` to `0`, restoring standard/default brightness. Typically called at the end of a
`Flash` state sequence to cancel a brightness bonus set by `A_Light1`, `A_Light2`, or `A_Light`.

## `void A_Light1()`

Sets `extralight` to `1`, one brightness level above normal: +16 light in the software renderer,
+8 in the GL renderer at the default `gl_weaponlight` of 8 (see "Scaling" below).

## `void A_Light2()`

Sets `extralight` to `2`, two brightness levels above normal: +32 light in the software renderer,
+16 in the GL renderer at the default `gl_weaponlight`. This is the standard/brightest level used
by vanilla weapon flashes.

## `void A_Light(int extralight)`

A customizable variant of `A_Light0`/`A_Light1`/`A_Light2` that accepts an arbitrary intensity
instead of a fixed 0/1/2. Positive values brighten, negative values darken.

### `extralight` parameter

Clamped to the range `[-20, 20]`; out-of-range values are silently clamped rather than rejected
(`A_Light(100)` behaves as `A_Light(20)`). `0`, `1`, and `2` are equivalent to calling
`A_Light0`/`A_Light1`/`A_Light2` respectively; `3`–`20` and `-1`–`-20` step one brightness level
brighter/darker per unit.

## `void A_LightInverse()`

Applies an inverted-greyscale colormap effect to the player's view — the visual feedback used by
Strife's Sigil weapon on firing. The effect lasts until another weapon light action overwrites the
field. See "Wiki/engine divergence: `A_LightInverse`" below; this is a distinct mechanism from the
brightness-offset behavior of the other four members, not just another brightness level.

## Behavior common to `A_Light0`/`A_Light1`/`A_Light2`/`A_Light`

- **Scaling.** In the software renderer the `extralight` value is multiplied by 16
  (`src/r_bsp.cpp:1068`) and **added** to the sector's baseline light level during rendering. It
  stacks with dynamic lights and sector brightness rather than overriding them. The software
  renderer drops it to 0 for foggy geometry (a sector with a fog color, or a level with a fade
  color or fade table). UZDoom's software renderer applies the same 16x scaling with the same fog exception
  (`src/rendering/swrenderer/scene/r_light.h:91`). Its separate hardware (OpenGL) renderer path
  scales by the `gl_weaponlight` cvar instead
  (`src/rendering/hwrenderer/scene/hw_lighting.h:53`), but this is not a UZDoom-only difference.
  Zandronum's own GL renderer has the identical `gl_weaponlight` cvar, defaulting to the same value
  of 8 on both engines (`src/gl/renderer/gl_lightdata.cpp:72` in Zandronum), so the two engines
  agree here too.
- **Persistence.** The brightness adjustment persists until explicitly changed. It is not reset
  every frame or every state tic. A `Flash` state that sets a brightness level without a later
  `A_Light0` (or equivalent, such as `Goto LightDone`) leaves the player's view bright
  indefinitely. Zandronum resets it to 0 on player death (`src/p_interaction.cpp:815`), on player
  spawn (`P_SpawnPlayer`, `src/p_mobj.cpp:5566`), at end of level (`G_PlayerFinishLevel`,
  `src/g_game.cpp:2058`), and in its client-side player reset and spectator paths
  (`src/cl_main.cpp:3275`, `src/cl_main.cpp:3875`, `src/p_interaction.cpp:2730`). Lowering or
  switching weapons does not reset it on either engine. UZDoom matches: `extralight` is reset to 0 on
  player death (`src/playsim/p_interaction.cpp:663`), on player (re)spawn
  (`FLevelLocals::SpawnPlayer`, `src/playsim/p_mobj.cpp:6402`), and at end-of-level
  (`PlayerInfo.PlayerFinishLevel`, `wadsrc/static/zscript/actors/player/player.zs:2234`, whose
  comment says it cancels gun flashes). On both engines a player-struct copy carries the current
  value through rather than resetting it (`PlayerInfo.CopyFrom`, `src/playsim/p_user.cpp:594` in
  UZDoom; `player_t::operator=`, `src/p_user.cpp:459` in Zandronum).
- **Class restriction (Zandronum only).** In Zandronum, all five members, `A_LightInverse`
  included, are declared on `Inventory` (`wadsrc/static/actors/shared/inventory.txt:15-19`). They
  only compile in state tables for `Inventory`-derived actors (weapons, items). In a monster's,
  player class's or other plain actor's state table, loading stops with "Invalid state parameter"
  (`src/thingdef/thingdef_states.cpp:443`). Each action also checks at runtime that `self` has a
  player and does nothing otherwise. That guard does fire in valid code: an item's own states (for
  example a pickup's `Spawn` state) run with the item itself as `self`, which has no player. In a
  weapon's `Fire`/`Flash` states `self` is the owning player's actor, so the call takes effect.
  UZDoom has no such restriction for any of the five members. See "Engine-family divergence: class
  restriction" below.

## Wiki/engine divergence: `A_LightInverse`

The wiki presents `A_LightInverse` as an interchangeable sibling of `A_Light0`/`A_Light1`/
`A_Light2`, but source verification turns up differences it doesn't mention:

- **Class.** Zandronum's C++ definition of `A_LightInverse` (`src/g_strife/a_strifeweapons.cpp:1082`)
  names `AActor` where the other four name `AInventory`, which reads as if it were callable from
  any actor. It is not. That macro argument only names the function's descriptor; DECORATE
  callability comes from where the `action native` line sits, which is `Inventory` for all five
  (`wadsrc/static/actors/shared/inventory.txt:15-19`). On Zandronum it is exactly as restricted as
  the other four, and a monster's state table calling it fails to load. On UZDoom all five members
  are equally unrestricted. See "Engine-family divergence: class restriction" below.
- **Mechanism.** Rather than writing a small brightness-level integer, `A_LightInverse` sets the
  player's `extralight` to `INT_MIN` as a sentinel value. Each frame the renderer copies the
  player's value into its own per-frame variable (`src/r_utility.cpp:901`). When that copy holds the
  sentinel, the renderer swaps in the `INVERSECOLORMAP` special colormap (a per-pixel
  invert-and-desaturate effect) instead of treating it as a light level, and zeroes only its
  per-frame copy. Zandronum does this in both renderers: software (`src/r_main.cpp:569-572`) and
  GL (`src/gl/scene/gl_scene.cpp:855-858`). The player's own field keeps the sentinel, so the
  effect persists until another weapon light action overwrites it, just like the brightness
  levels. Strife's Sigil flash ends it with `A_Light1` six tics later (see the example below). The
  software renderer applies the sentinel only when no powerup fixed colormap (such as
  invulnerability) is active; the GL renderer checks the sentinel first. This is *not* the current
  game's invulnerability palette: other games' invulnerability effects (e.g. Heretic's gold
  palette) are not shown when using this function. On Zandronum it is the same special colormap
  Doom's invulnerability sphere selects (`Powerup.Color InverseMap`,
  `wadsrc/static/actors/doom/doomartifacts.txt:15`), reached through a different trigger. UZDoom
  matches the mechanism: `A_LightInverse` stores the same `INT_MIN` bit pattern in the player's
  field (`wadsrc/static/zscript/actors/actor.zs:895`), the renderer copies it per frame
  (`src/rendering/r_utility.cpp:1155`), and both renderer backends detect the sentinel with the
  same precedence, the software path at `src/rendering/swrenderer/scene/r_light.cpp:88-92` and the
  hardware path at `src/rendering/hwrenderer/scene/hw_drawinfo.cpp:313-317`. UZDoom swaps in
  `REALINVERSECOLORMAP` for it, a separate slot from the sphere's `INVERSECOLORMAP`, which the
  `cl_customizeinvulmap` option can recolor (`src/r_data/colormaps.cpp:203-224`). The Sigil effect
  ignores that option.

## Engine-family divergence: class restriction

Zandronum restricts all five members to `Inventory`-derived actors. Their `action native`
declarations all sit on `Inventory` (`wadsrc/static/actors/shared/inventory.txt:15-19`), and
DECORATE only resolves an action name against the calling class and its ancestors (see "Class"
above and the "Class restriction" bullet earlier in this file). UZDoom has no such restriction:
all five are declared as ordinary methods directly on the base `Actor` class
(`wadsrc/static/zscript/actors/actor.zs:891-895`), with no overriding declaration anywhere under
`wadsrc/static/zscript/actors/inventory/`. Any actor's state table (weapon, item, or monster) can
call any of the five on UZDoom. Each still does nothing when `self` has no player, exactly as
Zandronum's runtime guard does, but nothing prevents the call from compiling in the first place.
A practical consequence: a monster or player class that calls a weapon light action loads on
UZDoom but fails to load on Zandronum, whichever of the five it calls.

## Examples

A weapon flash that dims the surroundings, using the parameterized form (adapted from the
`A_Light` wiki page). It ends with `Goto LightDone`, the state every `Weapon` inherits, which
calls `A_Light0`:

```decorate
ACTOR DimmingBFG : BFG9000
{
	States
	{
	Flash:
		BFGF A 4 Bright A_Light(-1)
		BFGF A 4 Bright A_Light(-2)
		BFGF B 1 Bright A_Light(-3)
		BFGF B 3 Bright A_Light(-5)
		Goto LightDone
	}
}
```

Strife's Sigil flash sequence, showing all four fixed-level members together (from the `A_Light0`
wiki page), here on a pistol whose inherited `Fire` state reaches `Flash` through `A_FirePistol`:

```decorate
ACTOR SigilFlashPistol : Pistol
{
	States
	{
	Flash:
		SIGF A 4 Bright A_Light2
		SIGF B 6 Bright A_LightInverse
		SIGF C 4 Bright A_Light1
		SIGF C 0 Bright A_Light0
		Stop
	}
}
```
