# `sv_dropstyle`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-16); Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02), enum values verified against raw wiki HTML.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Controls how items dropped by defeated monsters are scattered on the floor. Affects both the initial trajectory and spread pattern of dropped items.

## Value modes

| Value | Behavior |
|-------|----------|
| 0 | Leave the game's default behavior. The item-drop style is determined by the IWAD or map DECORATE definitions. |
| 1 | Standard Doom-style item drop. Items fall straight down or are scattered with moderate horizontal velocity. |
| 2 | Strife-style item drop. Items are tossed farther away from the monster's death location, creating a wider spread pattern. |

Default is 0 (use game default).

## Gameplay impact

- **Value 1** (Standard/Doom): items remain relatively near the monster's death point, making them easy to collect.
- **Value 2** (Strife): items scatter farther, requiring players to move to pick them all up. This adds complexity to item collection in combat situations.

## Network and storage

Marked `CVAR_SERVERINFO | CVAR_GAMEPLAYSETTING`, so it is replicated to clients and affects gameplay balance.

## Wiki/engine divergence: storage/network flags

The flag claim above doesn't hold on UZDoom: `sv_dropstyle` there is declared `CVAR_SERVERINFO | CVAR_ARCHIVE` (still replicated to clients, but auto-saved to the config file rather than tagged as a locked "gameplay setting"). UZDoom's cvar-flag set has no `CVAR_GAMEPLAYSETTING` equivalent at all — that flag is a Zandronum-only mechanism for locking specific settings during duel/Last Man Standing/Invasion modes. For context, current Zandronum source itself also declares this cvar `CVAR_SERVERINFO | CVAR_ARCHIVE`, not `CVAR_SERVERINFO | CVAR_GAMEPLAYSETTING` — so this flag claim doesn't match either engine's present-day source, not just UZDoom's. The value-mode semantics (0/1/2) and their trajectory/spread effects, covered elsewhere in this file, are identical between the two engines.

## Related cvars and properties

- **`sv_unlimited_pickup`** — allows picking up items beyond inventory limits (independent of drop style).
- **Actor property `DropItem`** (DECORATE/ZScript) — mods can override per-actor drop behavior independently of this server-wide setting.
