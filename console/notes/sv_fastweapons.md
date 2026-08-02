# `sv_fastweapons`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02), enum values and tic semantics verified against raw wiki HTML and Zandronum timing conventions.

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

## Related cvars

- **`sv_aircontrol`** — affects player movement speed in air; orthogonal to weapon firing speed.
- **`sv_respawndelaytime`** — affects respawn delay, not weapon speed.
