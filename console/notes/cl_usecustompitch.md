# `cl_usecustompitch`

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Source-derived (no wiki page consulted). Zandronum: `src/p_pspr.cpp:100-101`, `:122-128` (declarations), `:739-743` (reads in `P_BobWeapon`), `wadsrc/static/menudef.za:688-690` (Weapon Setup menu). UZDoom absence checked by grepping its `src/`/`wadsrc/` (zero hits). Shared mechanics: [Zandronum weapon still-bob, sway and pitch offset](../../decorate/concepts/zandronum-weapon-sway.md).

`Bool`, default `false`, `CVAR_ARCHIVE`. When on, the local client ignores the current weapon's
pitch-offset properties and uses its own cvars instead:

| Weapon property | Replaced by | Cvar default |
|---|---|---|
| `Weapon.ViewPitchOffset` | `cl_viewpitchoffset` (Float) | `0.0` |
| `Weapon.ViewPitchStyle` | `cl_viewpitchstyle` (Int, clamped `0`-`4`) | `0` (`Full`) |

- **Turning it on alone disables the pitch offset.** The offset only applies when the
  multiplier is non-zero, and `cl_viewpitchoffset` defaults to `0`.
- **`cl_viewpitchstyle` integers** follow the pitch-style enum, whose order differs from
  `cl_swaystyle`'s. See [viewpitchstyle](../../decorate/notes/viewpitchstyle.md) for the names.
- **Presentation only.** Not userinfo, not replicated, invisible to the server.

## Engine-family divergence

None of these cvars exist on UZDoom; setting one prints an unknown-command error.
