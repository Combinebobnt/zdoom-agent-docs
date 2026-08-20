# `sv_fastweapons`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-16); Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02), enum values and tic semantics verified against raw wiki HTML and Zandronum timing conventions.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Controls how quickly weapons cycle through their firing frames. Affects player weapon responsiveness and time-to-fire.

## Value modes

| Value | Behavior |
|-------|----------|
| 0 | Normal speed. Weapons cycle at their standard rate defined in DECORATE/ZScript. |
| 1 | Fast: 1 tic per weapon frame. Each frame of the weapon sprite is displayed for 1 server tic (approximately 1/35th of a second). Weapons fire noticeably faster than normal. |
| 2 | Very fast: 1 tic per frame, but frames without codepointers are skipped. Only frames that execute weapon-firing code are counted; intermediate animation-only frames are bypassed. This is significantly faster than mode 1 and produces the fastest possible weapon firing. |

Default is 0 (normal speed).

## Tic precision

A single tic equals 1/35th of a second in standard Zandronum (35 ticks per second). Weapon firing speed is cumulative: if a weapon's firing sprite has 3 frames and `sv_fastweapons` is 1, the weapon takes 3 ticks (about 0.086 seconds) per shot. At mode 2, this can drop to 1 tic per shot if intermediate frames are skipped.

## Gameplay impact

Fast weapons make the game more action-oriented but can be disorienting or overpowering in balance-sensitive modes. Typically used in casual deathmatch or testing, not in competitive play.

## Network and storage

Marked `CVAR_SERVERINFO | CVAR_GAMEPLAYSETTING`, so it is replicated to clients and affects gameplay balance.

## Engine-family divergence: mode 3, layer scope, and cvar flags

UZDoom recognizes a fourth value, 3, that Zandronum does not implement as a distinct mode. Setting `sv_fastweapons 3` on UZDoom collapses every weapon-sprite frame with a nonzero native duration down to a single tic, across all sprite layers (not just the primary weapon layer), while frames whose native duration is already zero are left untouched. Zandronum treats any value of 2 or higher identically to mode 2 (the "skip frames with no codepointer" behavior, restricted to the primary weapon layer) — there is no equivalent "collapse-nonzero-durations-to-one-tic" mode reachable through this cvar on Zandronum.

Modes 0-2 behave the same on both engines: mode 1 forces every affected layer's frame duration to 1 tic, and mode 2 forces the primary weapon layer's frame duration to 0 or 1 tic depending on whether the frame carries an action function, while other layers (e.g. the muzzle flash) stay governed by mode 1's blanket rule instead.

UZDoom's weapon-sprite layers are individually flagged for whether they respond to `sv_fastweapons` at all — a per-layer opt-out exposed to ZScript that has no Zandronum counterpart, since Zandronum's DECORATE-only weapons only ever have the two fixed layers (weapon and flash) with no mechanism to exempt either from the cvar. This only matters in practice for custom ZScript weapons that add extra overlay layers or deliberately clear the flag; the two standard layers keep it set by default, so ordinary DECORATE-style weapons behave the same under both engines.

Separately, UZDoom declares this cvar with only the `CVAR_SERVERINFO` flag — the `CVAR_GAMEPLAYSETTING` flag described in "Network and storage" below does not exist as a concept in UZDoom at all, so the client-side gameplay-settings categorization it implies is a Zandronum-specific detail, not present on UZDoom.

## Related cvars

- **`sv_aircontrol`** — affects player movement speed in air; orthogonal to weapon firing speed.
- **`sv_respawndelaytime`** — affects respawn delay, not weapon speed.
