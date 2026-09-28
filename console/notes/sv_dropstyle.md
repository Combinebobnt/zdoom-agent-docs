# `sv_dropstyle`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-16); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02), enum values verified against raw wiki HTML. Zandronum source: `src/p_enemy.cpp:3461` (declaration), `src/p_enemy.cpp:3463-3533` (`P_DropItem` spawn height), `src/p_enemy.cpp:3541-3565` (`P_TossItem` velocities), `src/gi.cpp:367` and `wadsrc/static/mapinfo/*.txt` (`defaultdropstyle`), `src/gamemode.cpp:309-322` and `src/c_cvars.cpp:283` (`CVAR_GAMEPLAYSETTING`).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Controls how dropped items are tossed when spawned: monster `DropItem` drops, player death drops, `A_DropItem` and ACS `DropItem` all go through the same engine drop routine. It sets both the spawn height and the initial velocity. Nothing is tossed at all when `compat_notossdrops` is on; the item then spawns at the dropper's feet.

## Value modes

| Value | Behavior |
|-------|----------|
| 0 | Use the game's default style, the MAPINFO `GameInfo` key `defaultdropstyle` (2 for Strife, 1 for the other stock games). DECORATE has no say in it. |
| 1 | Doom-style drop. The item spawns at half the dropper's height and pops upward (5 to about 9 units/tic) with under 1 unit/tic of random horizontal drift. |
| 2 | Strife-style drop. The item spawns 24 units above the dropper's base and gets up to 7 units/tic of random horizontal velocity per axis, no upward push, so it lands farther from the death point. |

Default is 0 (use game default).

## Gameplay impact

- **Value 1** (Standard/Doom): items remain relatively near the monster's death point, making them easy to collect.
- **Value 2** (Strife): items scatter farther, requiring players to move to pick them all up. This adds complexity to item collection in combat situations.

## Network and storage

Declared `CVAR_SERVERINFO | CVAR_ARCHIVE`: replicated to clients and saved to the config file. In Zandronum, drops are spawned server-side only (clients return early), so the server's value is the one that matters.

## Wiki/engine divergence: storage/network flags

The Zandronum Wiki lists this cvar as `CVAR_SERVERINFO | CVAR_GAMEPLAYSETTING`. Neither engine's source matches that. Both UZDoom and Zandronum declare it `CVAR_SERVERINFO | CVAR_ARCHIVE`. UZDoom's cvar-flag set has no `CVAR_GAMEPLAYSETTING` equivalent at all. In Zandronum that flag marks the cvars a GAMEMODE lump's `gamesettings`/`lockedgamesettings` blocks may set or lock, so `sv_dropstyle` cannot appear in those blocks.

The value-mode semantics (1 and 2) are the same in both engines. One small difference at value 0: Zandronum picks the spawn height from whether the game is Strife, while UZDoom uses `defaultdropstyle` for both spawn height and velocity. They only differ for a custom `GameInfo` that sets `defaultdropstyle` against its game type.

## Related cvars and properties

- **`sv_unlimited_pickup`** — allows picking up items beyond inventory limits (independent of drop style).
- **Actor property `DropItem`** (DECORATE/ZScript) chooses what an actor drops and how often. It does not change the toss style, which still follows this cvar.
