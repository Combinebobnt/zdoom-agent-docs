# `cl_usecustombob`

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Source-derived (no wiki page consulted). Zandronum: `src/p_pspr.cpp:85-91`, `:104-110` (declarations), `:551-563` and `:642-651` (reads in `P_BobWeapon`), `wadsrc/static/menudef.za:672-680` (Weapon Setup menu); `cl_bobrangex`/`cl_bobrangey` added after 3.2.1 in commit `9cc8abac6` (not an ancestor of `28f736fb3`). UZDoom absence checked by grepping its `src/`/`wadsrc/` (zero hits). Shared mechanics: [Zandronum weapon still-bob, sway and pitch offset](../../decorate/concepts/zandronum-weapon-sway.md).

`Bool`, default `false`, `CVAR_ARCHIVE`. When on, the local client ignores the current weapon's
bob style, bob speed, bob range and still-bob properties and uses its own cvars instead:

| Weapon property | Replaced by | Cvar default |
|---|---|---|
| `Weapon.BobStyle` | `cl_bobstyle` (Int, clamped `0`-`6`) | `0` (`Normal`) |
| `Weapon.BobSpeed` | `cl_bobspeed` (Float) | `1.0` |
| `Weapon.BobRangeX` | `cl_bobrangex` (Float) | `1.0` |
| `Weapon.BobRangeY` | `cl_bobrangey` (Float) | `1.0` |
| `Weapon.StillBobRange` | `cl_stillbobrange` (Float) | `0.0` |
| `Weapon.StillBobSpeed` | `cl_stillbobspeed` (Float) | `0.0` |

- **All or nothing.** The switch swaps the whole group, so leaving any of the six at its
  default forces that default on every weapon. With all defaults, the result is a plain
  `Normal`-style bob at speed and range `1.0` and no still bob, whatever the mod set.
- **Bob range override is post-3.2.1.** `cl_bobrangex`/`cl_bobrangey` were added after 3.2.1
  in commit `9cc8abac6`. A 3.2.1 client has neither cvar, and there `cl_usecustombob` replaces
  only the other four properties, so the weapon's own `BobRangeX`/`BobRangeY` still applies.
- **`cl_bobstyle` integers** follow `AWeapon`'s enum order: `0` Normal, `1` Inverse, `2` Alpha,
  `3` InverseAlpha, `4` Smooth, `5` InverseSmooth, `6` Quake. Out-of-range values are clamped.
- **Presentation only.** Read by the renderer's `P_BobWeapon`; not userinfo, not replicated, and
  invisible to the server and to other players.

`cl_alwaysbob` (Bool, default `false`, same menu) is independent of this switch: it keeps both
the regular bob and the still bob running while the weapon is firing or otherwise not in a
bobbing state.

## Engine-family divergence

None of these cvars exist on UZDoom; setting one prints an unknown-command error. UZDoom weapon
bob is changed per mod in ZScript (see the concept doc's divergence section), not by a client
override.
