# `sv_dropstyle`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum Wiki "Server variables" (https://wiki.zandronum.com/w/index.php?title=Server_variables&oldid=2534, saved 2026-08-02), enum values verified against raw wiki HTML.

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

## Related cvars and properties

- **`sv_unlimited_pickup`** — allows picking up items beyond inventory limits (independent of drop style).
- **Actor property `DropItem`** (DECORATE/ZScript) — mods can override per-actor drop behavior independently of this server-wide setting.
