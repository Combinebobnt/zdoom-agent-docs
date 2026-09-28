# `sv_fastweapons`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-16); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02), enum values and tic semantics verified against raw wiki HTML and Zandronum timing conventions. Zandronum source at 3.3-alpha @bdd0f7beb: declaration and clamping callback `src/p_pspr.cpp:70-79`, per-layer tic rule `src/p_pspr.cpp:238-243`, zero-tic advance loop `src/p_pspr.cpp:267`, psprite layers `src/p_pspr.h:44-53`, `CVAR_GAMEPLAYSETTING` `src/c_cvars.h:91`, lock check `src/c_cvars.cpp:283` and `src/gamemode.cpp:1661`, game-settings block eligibility `src/gamemode.cpp:230-232,309-313`, replication `src/sv_commands.cpp:2544`, `src/cl_main.cpp:6225-6227`, `src/sv_main.cpp:4788-4789`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Controls how quickly weapons cycle through their firing frames. Affects player weapon responsiveness and time-to-fire.

## Value modes

| Value | Behavior |
|-------|----------|
| 0 | Normal speed. Weapons cycle at their standard rate defined in DECORATE/ZScript. |
| 1 | Fast: 1 tic per weapon frame. Each frame of the weapon sprite is displayed for 1 server tic (approximately 1/35th of a second). Weapons fire noticeably faster than normal. |
| 2 | Very fast: on the primary weapon layer, a frame with an action function (any codepointer, including `A_WeaponReady`, `A_Raise` and `A_Lower`, not only firing ones) lasts 1 tic and a frame without one lasts 0 tics, so it is advanced through within the same tic. Other layers such as the muzzle flash get mode 1's 1 tic per frame. This is significantly faster than mode 1 and produces the fastest possible weapon firing. |

Default is 0 (normal speed).

## Tic precision

A single tic equals 1/35th of a second in standard Zandronum (35 ticks per second). Weapon firing speed is cumulative: if a weapon's firing sprite has 3 frames and `sv_fastweapons` is 1, the weapon takes 3 ticks (about 0.086 seconds) per shot. At mode 2, this can drop to 1 tic per shot if intermediate frames are skipped.

## Gameplay impact

Fast weapons make the game more action-oriented but can be disorienting or overpowering in balance-sensitive modes. Typically used in casual deathmatch or testing, not in competitive play.

## Network and storage

On Zandronum it is marked `CVAR_SERVERINFO | CVAR_GAMEPLAYSETTING`. The server sends its value to clients as one byte of the `SVC_SETGAMEMODELIMITS` command, and the cvar's change callback re-sends that command (and prints "sv_fastweapons changed to: N") whenever the server changes it. `CVAR_GAMEPLAYSETTING` makes it eligible for a GAMEMODE lump's `gamesettings`/`lockedgamesettings` blocks (and their `default*` variants). When the active game mode locks it, the console refuses changes with "sv_fastweapons cannot be changed in this game mode."

## Engine-family divergence: mode 3, layer scope, and cvar flags

UZDoom recognizes a fourth value, 3, that Zandronum does not implement as a distinct mode. Setting `sv_fastweapons 3` on UZDoom collapses every weapon-sprite frame with a nonzero native duration down to a single tic, across all sprite layers (not just the primary weapon layer), while frames whose native duration is already zero are left untouched. On Zandronum the cvar's change callback clamps any value of 3 or higher down to 2 and any negative value up to 0, so `sv_fastweapons 3` reads back as 2 and gets mode 2's "skip frames with no codepointer" behavior, restricted to the primary weapon layer. There is no equivalent "collapse-nonzero-durations-to-one-tic" mode reachable through this cvar on Zandronum.

Modes 0-2 behave the same on both engines: mode 1 forces every affected layer's frame duration to 1 tic, and mode 2 forces the primary weapon layer's frame duration to 0 or 1 tic depending on whether the frame carries an action function, while other layers (e.g. the muzzle flash) stay governed by mode 1's blanket rule instead.

UZDoom's weapon-sprite layers are individually flagged for whether they respond to `sv_fastweapons` at all — a per-layer opt-out exposed to ZScript that has no Zandronum counterpart, since Zandronum's DECORATE-only weapons only ever have the two fixed layers (weapon and flash), plus the Strife targeter's three fixed layers, with no mechanism to exempt any of them from the cvar. This only matters in practice for custom ZScript weapons that add extra overlay layers or deliberately clear the flag; the two standard layers keep it set by default, so ordinary DECORATE-style weapons behave the same under both engines.

Separately, UZDoom declares this cvar with only the `CVAR_SERVERINFO` flag — the `CVAR_GAMEPLAYSETTING` flag described in "Network and storage" above does not exist as a concept in UZDoom at all, so the GAMEMODE game-settings block and lock mechanism it enables is a Zandronum-specific detail, not present on UZDoom.

## Related cvars

- **`sv_aircontrol`** — affects player movement speed in air; orthogonal to weapon firing speed.
- **`sv_respawndelaytime`** — affects respawn delay, not weapon speed.
