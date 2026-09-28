# `cl_usecustomsway`

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Source-derived (no wiki page consulted). Zandronum: `src/p_pspr.cpp:94-97`, `:113-119` (declarations), `:654-677` (reads in `P_BobWeapon`), `wadsrc/static/menudef.za:682-686` (Weapon Setup menu). UZDoom absence checked by grepping its `src/`/`wadsrc/` (zero hits). Shared mechanics: [Zandronum weapon still-bob, sway and pitch offset](../../decorate/concepts/zandronum-weapon-sway.md).

`Bool`, default `false`, `CVAR_ARCHIVE`. When on, the local client ignores the current weapon's
four sway properties and uses its own cvars instead:

| Weapon property | Replaced by | Cvar default |
|---|---|---|
| `Weapon.ViewSwaySpeed` | `cl_viewswayspeed` (Float) | `0.0` |
| `Weapon.MotionSwaySpeed` | `cl_motionswayspeed` (Float) | `0.0` |
| `Weapon.JumpSwaySpeed` | `cl_jumpswayspeed` (Float) | `0.0` |
| `Weapon.SwayStyle` | `cl_swaystyle` (Int, clamped `0`-`3`) | `0` (`Normal`) |

- **Turning it on alone disables sway.** All three speeds default to `0`, and sway only runs
  when at least one speed is non-zero, so a player can switch off a mod's sway with just this
  cvar.
- **All or nothing.** The whole group is swapped; there is no way to keep the weapon's speeds
  and override only the style.
- **`cl_swaystyle` integers** match `Weapon.SwayStyle`'s names: `0` Normal, `1` DownOnly, `2`
  UpOnly, `3` HorizontalOnly. See [swaystyle](../../decorate/notes/swaystyle.md).
- **Presentation only.** Not userinfo, not replicated, invisible to the server.

## Engine-family divergence

None of these cvars exist on UZDoom; setting one prints an unknown-command error.
