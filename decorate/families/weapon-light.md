# Weapon light actions

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `A_Light` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_Light&oldid=42814) and `A_Light0` (retrieved
2026-08-01, https://zdoom.org/w/index.php?title=A_Light0&oldid=47264 — this single wiki page also documents `A_Light1`, `A_Light2`, and
`A_LightInverse`) + verified against the Zandronum source's `src/p_pspr.cpp:1353-1385` (`A_Light0`,
`A_Light1`, `A_Light2`, `A_Light`), `src/g_strife/a_strifeweapons.cpp:1082-1088` (`A_LightInverse`),
`src/r_bsp.cpp:1068` (extralight-to-render scaling), and `src/r_main.cpp:569-572` (inverse-colormap
sentinel handling); `A_Light` additionally cross-checked against UZDoom's
`wadsrc/static/zscript/actors/actor.zs:895`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Shared implementation — in Zandronum, `A_Light0`, `A_Light1`, `A_Light2`, and the
parameterized `A_Light` are thin `AInventory`-class wrappers that all assign directly to the
owning player's `extralight` field. `A_LightInverse` is grouped with them because the wiki and
both source files treat it as a sibling of the same "weapon light" family, but it is an
`AActor`-class action (defined separately in `src/g_strife/a_strifeweapons.cpp`) that repurposes
the same field via an `INT_MIN` sentinel to trigger an inverted-colormap render effect rather than
a brightness offset — see "Wiki/engine divergence: `A_LightInverse`" below. In UZDoom, all five are ordinary ZScript methods
declared directly on the base `Actor` class (`wadsrc/static/zscript/actors/actor.zs:891-895`), not
split across an `AInventory`/`AActor` pair — see "Engine-family divergence: class restriction"
below.
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

Sets `extralight` to `1` — one brightness level (+16 light) above normal.

## `void A_Light2()`

Sets `extralight` to `2` — two brightness levels (+32 light) above normal; the standard/brightest
level used by vanilla weapon flashes.

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
Strife's Sigil weapon on firing. See "Wiki/engine divergence: `A_LightInverse`" below; this is a distinct mechanism from the
brightness-offset behavior of the other four members, not just another brightness level.

## Behavior common to `A_Light0`/`A_Light1`/`A_Light2`/`A_Light`

- **Scaling.** The `extralight` value is applied with a 16x scaling factor
  (`src/r_bsp.cpp:1068`: `r_actualextralight = foggy ? 0 : extralight << 4`) and **added** to the
  sector's baseline light level during rendering — it stacks with dynamic lights and sector
  brightness rather than overriding them. UZDoom's software renderer applies the identical 16x
  formula (`src/rendering/swrenderer/scene/r_light.h:91`: `viewport->viewpoint.extralight << 4`);
  its separate hardware (OpenGL) renderer path scales by the `gl_weaponlight` cvar instead
  (`src/rendering/hwrenderer/scene/hw_lighting.h:53`), but this is not a UZDoom-only difference —
  Zandronum's own GL renderer has the identical `gl_weaponlight` cvar, defaulting to the same value
  of 8 on both engines (`src/gl/renderer/gl_lightdata.cpp:72` in Zandronum), so the two engines
  agree here too.
- **Persistence.** The brightness adjustment persists until explicitly changed — it is not reset
  every frame or every state tic. A `Flash` state that sets a brightness level without a later
  `A_Light0` (or equivalent) leaves the player's view bright indefinitely. The value is reset to 0
  on player death, respawn, weapon lower, and client state synchronization, so it does not carry
  across lives or survive putting the weapon away. UZDoom matches: `extralight` is reset to 0 on
  player death (`src/playsim/p_interaction.cpp:663`), on player (re)spawn
  (`FLevelLocals::SpawnPlayer`, `src/playsim/p_mobj.cpp:6402`), and at end-of-level
  (`PlayerInfo.PlayerFinishLevel`, `wadsrc/static/zscript/actors/player/player.zs:2234`, commented
  `// cancel gun flashes`); a separate player-struct copy path (`PlayerInfo.CopyFrom`,
  `src/playsim/p_user.cpp:594`) carries the current value through rather than resetting it, the
  UZDoom equivalent of the Zandronum client-sync case.
- **Class restriction — Zandronum only.** In Zandronum, these four are defined on `AInventory`, not
  `AActor` — they only compile in state tables for `Inventory`-derived actors (weapons, items), and
  fail to compile in a monster's or other plain actor's state table. A runtime guard
  (`if (self->player != NULL)`) additionally makes the call a silent no-op if `self` somehow has no
  player owner at runtime, though DECORATE's compile-time class restriction should prevent that
  guard from ever firing in correctly-written code. UZDoom has no such restriction for any of the
  five members — see "Engine-family divergence: class restriction" below.

## Wiki/engine divergence: `A_LightInverse`

The wiki presents `A_LightInverse` as an interchangeable sibling of `A_Light0`/`A_Light1`/
`A_Light2`, but source verification turns up two real differences it doesn't mention:

- **Class (Zandronum only).** `A_LightInverse` is defined on `AActor`
  (`src/g_strife/a_strifeweapons.cpp`), not `AInventory` — it compiles in *any* actor's state
  table, including monsters, unlike the other three. A monster calling it has no `player` field
  and the call silently no-ops, but the compile-time restriction that prevents this mistake for
  `A_Light0/1/2` does not apply here. This class split does not exist on UZDoom, where all five
  members are equally unrestricted — see "Engine-family divergence: class restriction" below.
- **Mechanism.** Rather than writing a small brightness-level integer, `A_LightInverse` assigns
  `extralight = INT_MIN` — a sentinel value. During frame render setup, the engine detects this
  sentinel and swaps in the `INVERSECOLORMAP` special colormap (a per-pixel invert-and-desaturate
  effect) instead of treating it as a light-level multiplier (`src/r_main.cpp:569-572`), then
  resets `extralight` back to `0` so the effect doesn't persist across frames the way
  `A_Light0/1/2`'s brightness levels do. This is *not* the invulnerability palette — other games'
  invulnerability effects (e.g. Heretic's gold palette) are not shown when using this function, and
  it uses a different colormap path than Doom's own invulnerability sphere. UZDoom matches this
  mechanism: `A_LightInverse` assigns `player.extralight = 0x80000000`
  (`wadsrc/static/zscript/actors/actor.zs:895`, the same `INT_MIN` bit pattern), and both of its
  renderer backends detect the sentinel and swap in the `REALINVERSECOLORMAP` special colormap —
  the software path at `src/rendering/swrenderer/scene/r_light.cpp:88-92` and the hardware path at
  `src/rendering/hwrenderer/scene/hw_drawinfo.cpp:313-317`, mirroring the software-only check
  Zandronum has.

## Engine-family divergence: class restriction

Zandronum splits this family across two base classes — `AInventory` for `A_Light0`/`A_Light1`/
`A_Light2`/`A_Light`, `AActor` for `A_LightInverse` — enforced by DECORATE's compile-time
class-of-action-function check (see "Class" above and the "Class restriction" bullet earlier in
this file). UZDoom has no such split: all five are declared as ordinary methods directly on the
base `Actor` class (`wadsrc/static/zscript/actors/actor.zs:891-895`), with no overriding
declaration anywhere under `wadsrc/static/zscript/actors/inventory/`. Any actor's state table —
weapon, item, or monster — can call any of the five on UZDoom; each still no-ops silently via its
own `if (player)` guard when `self` has no player owner, exactly as Zandronum's runtime guard
does, but nothing prevents the call from compiling in the first place. A practical consequence:
`A_LightInverse`'s "available to any actor, not just inventory items" trait, which the wiki and
Zandronum's source single it out for among the five, is not a distinguishing property on UZDoom —
none of the five are restricted there.

## Examples

A weapon flash that dims the surroundings, using the parameterized form (adapted from the
`A_Light` wiki page):

```decorate
Flash:
	BFGF A 4 Bright A_Light(-1)
	BFGF A 4 Bright A_Light(-2)
	BFGF B 1 Bright A_Light(-3)
	BFGF B 3 Bright A_Light(-5)
	Goto LightDone
LightDone:
	BFGF A 0 A_Light0
	Stop
```

Strife's Sigil flash state, showing all four fixed-level members together (from the `A_Light0`
wiki page):

```decorate
Flash:
	SIGF A 4 Bright A_Light2
	SIGF B 6 Bright A_LightInverse
	SIGF C 4 Bright A_Light1
	SIGF C 0 Bright A_Light0
	Stop
```
