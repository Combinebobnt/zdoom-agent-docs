# `sv_coop_damagefactor`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes — the exact `sv_coop_damagefactor` cvar and its `ApplyCoopDamagefactor()` gate don't exist on UZDoom, but a differently-shaped set of cvars covers similar ground; see the divergence section below.
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Zandronum source `src/p_interaction.cpp` (CUSTOM_CVAR declaration and ApplyCoopDamagefactor implementation), verified against engine behavior.

Damage multiplier applied to damage **dealt to players by monsters**. Higher values increase monster damage; lower values reduce it. Default 1.0 leaves monster damage unchanged. Despite the `coop_` in its name, the multiplier is not itself gated on cooperative game mode — `ApplyCoopDamagefactor()` is called unconditionally from `P_DamageMobj()`'s player-target branch and only checks that the damage source is a monster, not what game mode is active; in practice it matters most in coop because that's where monsters are commonly damaging players, but the cvar has no `GMF_COOPERATIVE` check of its own.

## Application and direction

This cvar only affects damage **from monsters to players**, not player-to-player or player-to-monster damage. It is applied via the `ApplyCoopDamagefactor()` function (`src/p_interaction.cpp:1138-1142`): `damage = int(damage * sv_coop_damagefactor)`.

For example:
- `sv_coop_damagefactor 2.0` doubles all damage dealt to players by monsters.
- `sv_coop_damagefactor 0.5` halves monster damage to players.

**Correction:** `sv_coop_damagefactor 0.0` does *not* prevent monster-to-player damage. The cvar's own `CUSTOM_CVAR` callback (`src/p_interaction.cpp:1128-1135`) clamps any attempted value `<= 0` back up to `1.0f` (the default, unscaled) — so trying to set `0` (or a negative value) silently resets the cvar to `1.0` instead of zeroing out damage. To reduce monster damage toward (but not to) zero, use a small positive fraction such as `0.01`.

The multiplier applies only when the damage source (`source`) is flagged with `MF3_ISMONSTER` (`src/p_interaction.cpp:1140`).

## Network and storage

Marked `CVAR_SERVERINFO | CVAR_GAMEPLAYSETTING`, so the value is replicated to clients and affects gameplay balance.

## Related cvars and flags

- **`sv_forcerespawn`** / **`sv_forcerespawntime`** — control respawn behavior independently of damage scaling.
- **`sv_defaultdmflags`** — sets baseline deathmatch/cooperative flags, affecting monster spawning and other gameplay.

## Engine-family divergence: no direct UZDoom equivalent, but overlapping cvars exist

`sv_coop_damagefactor` and `ApplyCoopDamagefactor()` do not exist on UZDoom under that name or shape — confirmed absent from source, not merely undocumented. UZDoom instead carries three separate damage-scaling cvars declared together (`src/playsim/p_interaction.cpp`, near the top of the file): `sv_damagefactorplayer`, `sv_damagefactormobj`, and `sv_damagefactorfriendly`, each `Float`, defaulting to `1.0`, flagged `CVAR_SERVERINFO | CVAR_CHEAT` (Zandronum's cvar is flagged `CVAR_SERVERINFO | CVAR_GAMEPLAYSETTING` instead — no `CVAR_CHEAT`).

The shape differs from Zandronum's single monster-to-player multiplier in several ways:
- UZDoom's `sv_damagefactorplayer` scales **any** damage dealt to a player, regardless of the source's type — it is not restricted to monster-sourced damage the way Zandronum's `MF3_ISMONSTER` check restricts `sv_coop_damagefactor`.
- It's applied multiplicatively together with the current skill's `DamageFactor` property (via `G_SkillProperty(SKILLP_DamageFactor)`, `src/playsim/p_interaction.cpp:1179`), so skill-level tuning and this cvar compound rather than one being independent of the other.
- `sv_damagefactormobj` and `sv_damagefactorfriendly` cover the opposite direction (damage dealt *to* non-player targets, split by whether the target itself is `MF_FRIENDLY`) — a case Zandronum's `sv_coop_damagefactor` doesn't touch at all, since it only ever scales damage to players.
- Like Zandronum's cvar, none of UZDoom's three are gated on cooperative game mode specifically; they apply in any game mode.

A modder porting a Zandronum-side coop damage-scaling setup to UZDoom needs `sv_damagefactorplayer` (not a same-named `sv_coop_damagefactor`), and should account for it also affecting player-vs-player damage and stacking with skill's `DamageFactor` — behavior Zandronum's cvar doesn't have.
