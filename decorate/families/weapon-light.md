# Weapon light actions

**Tier:** A
**Engine:** Zandronum 3.2.1 (`A_Light` additionally verified against UZDoom 4.15pre)
**Provenance:** ZDoom Wiki `A_Light` (retrieved 2026-07-31, oldid=42814) and `A_Light0` (retrieved
2026-08-01, oldid=47264 — this single wiki page also documents `A_Light1`, `A_Light2`, and
`A_LightInverse`) + verified against the Zandronum source's `src/p_pspr.cpp:1353-1385` (`A_Light0`,
`A_Light1`, `A_Light2`, `A_Light`), `src/g_strife/a_strifeweapons.cpp:1082-1088` (`A_LightInverse`),
`src/r_bsp.cpp:1068` (extralight-to-render scaling), and `src/r_main.cpp:569-572` (inverse-colormap
sentinel handling); `A_Light` additionally cross-checked against UZDoom's
`wadsrc/static/zscript/actors/actor.zs:895`.
**Bucket:** Shared implementation — `A_Light0`, `A_Light1`, `A_Light2`, and the parameterized
`A_Light` are thin `AInventory`-class wrappers that all assign directly to the owning player's
`extralight` field. `A_LightInverse` is grouped with them because the wiki and both source files
treat it as a sibling of the same "weapon light" family, but it is an `AActor`-class action
(defined separately in `src/g_strife/a_strifeweapons.cpp`) that repurposes the same field via an
`INT_MIN` sentinel to trigger an inverted-colormap render effect rather than a brightness offset —
see "Key divergence" below.
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
Strife's Sigil weapon on firing. See "Key divergence" below; this is a distinct mechanism from the
brightness-offset behavior of the other four members, not just another brightness level.

## Behavior common to `A_Light0`/`A_Light1`/`A_Light2`/`A_Light`

- **Scaling.** The `extralight` value is applied with a 16x scaling factor
  (`src/r_bsp.cpp:1068`: `r_actualextralight = foggy ? 0 : extralight << 4`) and **added** to the
  sector's baseline light level during rendering — it stacks with dynamic lights and sector
  brightness rather than overriding them.
- **Persistence.** The brightness adjustment persists until explicitly changed — it is not reset
  every frame or every state tic. A `Flash` state that sets a brightness level without a later
  `A_Light0` (or equivalent) leaves the player's view bright indefinitely. The value is reset to 0
  on player death, respawn, weapon lower, and client state synchronization, so it does not carry
  across lives or survive putting the weapon away.
- **Class restriction.** These four are defined on `AInventory`, not `AActor` — they only compile
  in state tables for `Inventory`-derived actors (weapons, items), and fail to compile in a
  monster's or other plain actor's state table. A runtime guard (`if (self->player != NULL)`)
  additionally makes the call a silent no-op if `self` somehow has no player owner at runtime,
  though DECORATE's compile-time class restriction should prevent that guard from ever firing in
  correctly-written code.

## Key divergence: `A_LightInverse`

The wiki presents `A_LightInverse` as an interchangeable sibling of `A_Light0`/`A_Light1`/
`A_Light2`, but source verification turns up two real differences it doesn't mention:

- **Class.** `A_LightInverse` is defined on `AActor` (`src/g_strife/a_strifeweapons.cpp`), not
  `AInventory` — it compiles in *any* actor's state table, including monsters, unlike the other
  three. A monster calling it has no `player` field and the call silently no-ops, but the
  compile-time restriction that prevents this mistake for `A_Light0/1/2` does not apply here.
- **Mechanism.** Rather than writing a small brightness-level integer, `A_LightInverse` assigns
  `extralight = INT_MIN` — a sentinel value. During frame render setup, the engine detects this
  sentinel and swaps in the `INVERSECOLORMAP` special colormap (a per-pixel invert-and-desaturate
  effect) instead of treating it as a light-level multiplier (`src/r_main.cpp:569-572`), then
  resets `extralight` back to `0` so the effect doesn't persist across frames the way
  `A_Light0/1/2`'s brightness levels do. This is *not* the invulnerability palette — other games'
  invulnerability effects (e.g. Heretic's gold palette) are not shown when using this function, and
  it uses a different colormap path than Doom's own invulnerability sphere.

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
