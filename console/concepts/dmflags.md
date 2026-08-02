# DMFlags: Bitfield cvars and their mechanics

**Tier:** A
**Engine:** Zandronum 3.2.1 (with some flags post-3.2.1; see below)
**Provenance:** Zandronum source `src/doomdef.h:243-527` verified against actual flag-checking code in `src/*.cpp`. Cross-checked against ZDoom Wiki `DMFlags` page (https://zdoom.org/w/index.php?title=DMFlags&oldid=54806, saved 2026-08-02) to identify ZDoom/Zandronum dmflags divergence; see "Engine-family divergence" section below.

The `dmflags`, `dmflags2`, `zadmflags` (and their counterparts `compatflags`, `compatflags2`, `zacompatflags`) are bitfield cvars that control gameplay rules, compatibility behavior, and network-replication settings. This page explains critical distinctions that the engine source and wiki do not make explicit, plus gotchas that can cause unexpected behavior if misunderstood.

## Critical: Multi-bit fields, not independent bits

**Three flag groups use 2-bit encodings where the two "opposite" values are mutually exclusive**, not additive bitwise-OR operations. The wiki's rendering of these is misleading.

### Falling damage modes (dmflags bits 3-4)

The falling damage system is encoded in bits 3-4 as a 2-bit selector:

| Bits 3-4 | Decimal | Constant | Effect |
|---|---|---|---|
| 00 | 0 | (neither set) | Falling damage disabled (default) |
| 01 | 8 | `DF_FORCE_FALLINGZD` | ZDoom-style falling damage (less aggressive) |
| 10 | 16 | `DF_FORCE_FALLINGHX` | Hexen-style falling damage (stronger) |
| 11 | 24 | `DF_FORCE_FALLINGST` | Strife-style falling damage (strongest; 52 damage minimum) |

**Wiki note:** The ZDoom Wiki lists three separate falling damage flags (values 8, 16, 24) without explaining that they are mutually exclusive modes of a 2-bit field. Documentation that presents the decimal values 8 and 16 separately might mislead readers into thinking they should be combined semantically ("add them together"), but the correct mechanism is that bits 3-4 form a 2-bit selector—setting both bits simultaneously creates mode 3 (both bits set), but this is bit-level composition, not semantic addition. The modes are mutually exclusive states.

### Jump control (dmflags bits 16-17)

Bits 16-17 form a 2-bit selector for jump behavior:

| Bits 16-17 | Decimal | Constant | Effect |
|---|---|---|---|
| 00 | 0 | (neither set) | Jump controlled by MAPINFO NoJumping flag (default) |
| 01 | 65536 | `DF_NO_JUMP` | Jumping disabled server-wide |
| 10 | 131072 | `DF_YES_JUMP` | Jumping enabled, override MAPINFO NoJumping |

Note: `DF_YES_JUMP = 2 << 16`, which is bit 17. Setting both bits simultaneously (value 196608) is not a defined mode.

### Crouch control (dmflags bits 22-23)

Bits 22-23 form a 2-bit selector for crouch behavior, analogous to jump:

| Bits 22-23 | Decimal | Constant | Effect |
|---|---|---|---|
| 00 | 0 | (neither set) | Crouch controlled by MAPINFO NoCrouch flag (default) |
| 01 | 4194304 | `DF_NO_CROUCH` | Crouching disabled server-wide |
| 10 | 8388608 | `DF_YES_CROUCH` | Crouching enabled, override MAPINFO NoCrouch |

## Non-functional flags

### `DF_NO_ITEMS` (dmflags bit 1, value 2)

**This flag is declared but not implemented.** The source code at `src/p_mobj.cpp:6173-6177` has the check present but the actual logic is commented out:

```c
if (dmflags & DF_NO_ITEMS)
{
//  if (i->IsDescendantOf (RUNTIME_CLASS(AArtifact)))
//      return;
}
```

The enum comment explains why: "[RC] Currently not implemented (no easy way to find if it's an object, like AArtifact)." Setting this flag has no effect on gameplay. (This non-functionality is documented in the Zandronum source code comment; the ZDoom wiki does not discuss this flag.)

## Source code comment inversions

**Three dmflags2 flags have comments in the source that describe the opposite of what their names indicate.** When setting these flags in scripts or documentation, use the flag *name*, not the *comment*, as the authoritative source.

| Flag | Source Comment | Actual Behavior |
|---|---|---|
| `DF2_NO_AUTOMAP` (bit 18) | "Players are allowed to see the automap." | When set, the automap is **disabled** (`src/am_map.cpp:1469-1470` returns early) |
| `DF2_NO_AUTOMAP_ALLIES` (bit 19) | "Allies can been seen on the automap." | When set, allies are **hidden** on the automap |
| `DF2_DISALLOW_SPYING` (bit 20) | "You can spy on your allies." | When set, spying is **disallowed** (`src/g_game.cpp:1072-1074` returns early) |

The flag *names* accurately describe the intended effect; the comments are simply wrong in the source. This does not affect gameplay (the code checks the bit, not the comment), but it can confuse modders reading the source.

## Interaction with `alwaysapplydmflags` (Zandronum-specific)

`alwaysapplydmflags` is a Zandronum-specific cvar (not in ZDoom) that controls whether dmflags apply outside of deathmatch game modes:

- **DF_FORCE_RESPAWN** requires `alwaysapplydmflags = true` to function in non-deathmatch modes.
- **DF2_BARRELS_RESPAWN** only works in non-deathmatch modes if `alwaysapplydmflags = true`.

Check the `alwaysapplydmflags` cvar notes for full semantics.

## Version gates for Zandronum-specific dmflags

The Zandronum dmflags (ZADF_*) were added incrementally across versions. **The following flags were added *after* Zandronum 3.2.1** and should not be documented as 3.2.1-stable:

- `ZADF_DONT_HIDE_STATS` (zadmflags bit 24, value 16777216) — added 2022-08-20
- `ZADF_NO_ALLY_ICONS` (zadmflags bit 27, value 134217728) — added 2024-07-14
- `ZADF_NO_ENEMY_ICONS` (zadmflags bit 28, value 268435456) — added 2024-07-14

The remaining Zandronum dmflags (bits 0-23, 25-26) predate or coincide with 3.2.1. See individual flag documentation for current version stamps.

## Engine-family divergence: ZDoom vs. Zandronum

Zandronum is based on an old ZDoom snapshot (2.8pre-441); the following dmflags and dmflags2 bits exist in **only one** engine:

**ZDoom flags not in Zandronum:**
- dmflags2 bit 27 (134217728): "Big powerups respawn" — controls respawn of items with the `Inventory.BIGPOWERUP` flag (ZDoom only).
- dmflags2 bit 30 (1073741824): "Allow vertical bullet spread" — controls whether vertical spread is applied to weapon bullet shots (ZDoom/GZDoom only).

**Zandronum flags not in ZDoom wiki:**
- dmflags2 bit 2 (4): `DF2_NO_RUNES` — rune items (Skulltag Flag game).
- dmflags2 bit 3 (8): `DF2_INSTANT_RETURN` — instant-return flags/skulls on carrier death (ST/CTF).
- dmflags2 bit 5 (32): `DF2_NO_TEAM_SELECT` — server-assigned teams (ZDoom has no counterpart).
- dmflags2 bit 11 (2048): `DF2_SHOTGUNSTART` — all players start with shotgun (Zandronum extension).

ZDoom and Zandronum also use inverted semantics for many flags (e.g., ZDoom's "Allow Autoaim" vs. Zandronum's `DF2_NOAUTOAIM`); this table uses Zandronum semantics throughout.

## Flag enumeration by cvar

### dmflags (32-bit, bits 0-30)

| Bit(s) | Value | Flag | Effect | Notes |
|---|---|---|---|---|
| 0 | 1 | `DF_NO_HEALTH` | Health items don't spawn | Deathmatch only |
| 1 | 2 | `DF_NO_ITEMS` | Powerup items don't spawn | **Non-functional** |
| 2 | 4 | `DF_WEAPONS_STAY` | Weapons remain after pickup | Deathmatch only |
| 3-4 | 8, 16, 24 | `DF_FORCE_FALLING*` | Select falling damage mode | See section above |
| 5 | 32 | (unused) | — | — |
| 6 | 64 | `DF_SAME_LEVEL` | Don't advance maps on exit | Deathmatch only |
| 7 | 128 | `DF_SPAWN_FARTHEST` | Spawn away from other players | Deathmatch only |
| 8 | 256 | `DF_FORCE_RESPAWN` | Auto-respawn after death | Deathmatch only; requires `alwaysapplydmflags` in other modes |
| 9 | 512 | `DF_NO_ARMOR` | Armor items don't spawn | Deathmatch only |
| 10 | 1024 | `DF_NO_EXIT` | Kill any player who exits | Deathmatch only |
| 11 | 2048 | `DF_INFINITE_AMMO` | Infinite ammunition | — |
| 12 | 4096 | `DF_NO_MONSTERS` | Monsters don't spawn | — |
| 13 | 8192 | `DF_MONSTERS_RESPAWN` | Monsters respawn after death | — |
| 14 | 16384 | `DF_ITEMS_RESPAWN` | Items respawn (except invuln/invisibility) | — |
| 15 | 32768 | `DF_FAST_MONSTERS` | Monsters use FastSpeed property | — |
| 16-17 | 65536, 131072 | `DF_NO_JUMP` / `DF_YES_JUMP` | Control jump behavior | See section above; 2-bit field |
| 18 | 262144 | `DF_NO_FREELOOK` | Freelook disabled | — |
| 19 | 524288 | `DF_RESPAWN_SUPER` | Mega powerups respawn (needs `sv_itemrespawn = true`) | — |
| 20 | 1048576 | `DF_NO_FOV` | FOV locked to default (90) | — |
| 21 | 2097152 | `DF_NO_COOP_WEAPON_SPAWN` | Multiplayer-only weapons don't spawn in coop | Coop only |
| 22-23 | 4194304, 8388608 | `DF_NO_CROUCH` / `DF_YES_CROUCH` | Control crouch behavior | See section above; 2-bit field |
| 24 | 16777216 | `DF_COOP_LOSE_INVENTORY` | Lose all inventory on death | Coop only |
| 25 | 33554432 | `DF_COOP_LOSE_KEYS` | Lose keys on death | Coop only |
| 26 | 67108864 | `DF_COOP_LOSE_WEAPONS` | Lose weapons on death | Coop only |
| 27 | 134217728 | `DF_COOP_LOSE_ARMOR` | Lose armor on death | Coop only |
| 28 | 268435456 | `DF_COOP_LOSE_POWERUPS` | Lose powerups on death | Coop only |
| 29 | 536870912 | `DF_COOP_LOSE_AMMO` | Lose all ammo on death | Coop only |
| 30 | 1073741824 | `DF_COOP_HALVE_AMMO` | Lose half ammo on death (minimum start amount) | Coop only |

### dmflags2 (32-bit, bits 0-26)

| Bit | Value | Flag | Effect |
|---|---|---|---|
| 0 | 1 | (unused) | Formerly `DF2_YES_IMPALING` (removed) |
| 1 | 2 | `DF2_YES_WEAPONDROP` | Drop weapon on death |
| 2 | 4 | `DF2_NO_RUNES` | Rune items don't spawn (ST/CTF) |
| 3 | 8 | `DF2_INSTANT_RETURN` | Flags return instantly on carrier death (ST/CTF) |
| 4 | 16 | `DF2_NO_TEAM_SWITCH` | Players cannot change teams |
| 5 | 32 | `DF2_NO_TEAM_SELECT` | Server assigns teams automatically |
| 6 | 64 | `DF2_YES_DOUBLEAMMO` | Double ammo from items |
| 7 | 128 | `DF2_YES_DEGENERATION` | Slow health loss above 100% (Quake-style) |
| 8 | 256 | `DF2_YES_FREEAIMBFG` | BFG can be aimed vertically |
| 9 | 512 | `DF2_BARRELS_RESPAWN` | Barrels respawn (non-deathmatch requires `alwaysapplydmflags = true`) |
| 10 | 1024 | `DF2_NO_RESPAWN_INVUL` | No invulnerability on respawn |
| 11 | 2048 | `DF2_SHOTGUNSTART` | All players start with shotgun |
| 12 | 4096 | `DF2_SAME_SPAWN_SPOT` | Respawn at death location (Coop) |
| 13 | 8192 | `DF2_YES_KEEPFRAGS` | Frags don't reset between maps |
| 14 | 16384 | `DF2_NO_RESPAWN` | Players cannot respawn once killed |
| 15 | 32768 | `DF2_YES_LOSEFRAG` | Lose a frag when killed |
| 16 | 65536 | `DF2_INFINITE_INVENTORY` | Using items doesn't consume them |
| 17 | 131072 | `DF2_KILL_MONSTERS` | Must kill all monsters to advance (Coop) |
| 18 | 262144 | `DF2_NO_AUTOMAP` | Automap disabled (source comment is inverted) |
| 19 | 524288 | `DF2_NO_AUTOMAP_ALLIES` | Allies hidden on automap (source comment is inverted) |
| 20 | 1048576 | `DF2_DISALLOW_SPYING` | Spying disabled (source comment is inverted) |
| 21 | 2097152 | `DF2_CHASECAM` | Chasecam enabled |
| 22 | 4194304 | `DF2_NOSUICIDE` | Kill command disabled |
| 23 | 8388608 | `DF2_NOAUTOAIM` | Autoaiming disabled server-wide (see `compat_autoaim`). |
| 24 | 16777216 | `DF2_DONTCHECKAMMO` | Weapon switching doesn't require ammo |
| 25 | 33554432 | `DF2_KILLBOSSMONST` | Killing BossBrain kills all its spawns |
| 26 | 67108864 | `DF2_NOCOUNTENDMONST` | Don't count end-sector monsters toward kill quota |

### zadmflags (Zandronum-specific, 32-bit, bits 0-28)

| Bit | Value | Flag | Effect | Version |
|---|---|---|---|---|
| 0 | 1 | `ZADF_NO_IDENTIFY_TARGET` | cl_identifytarget behavior forced to 0 | 3.2.1 |
| 1 | 2 | `ZADF_ALWAYS_APPLY_LMS_SPECTATORSETTINGS` | Apply LMS spectator settings in all modes | 3.2.1 |
| 2 | 4 | `ZADF_NO_COOP_INFO` | cl_drawcoopinfo forced to 0 | 3.2.1 |
| 3 | 8 | `ZADF_NOUNLAGGED` | Disable backwards-reconciliation for hitscans | 3.2.1 |
| 4 | 16 | `ZADF_UNBLOCK_PLAYERS` | Players pass through each other | 3.2.1 |
| 5 | 32 | `ZADF_NO_MEDALS` | cl_medals forced to 0 | 3.2.1 |
| 6 | 64 | `ZADF_SHARE_KEYS` | Keys shared among all players (Coop/Survival) | 3.2.1 |
| 7 | 128 | `ZADF_YES_KEEP_TEAMS` | Teams persist across map changes | 3.2.1 |
| 8 | 256 | `ZADF_FORCE_VIDEO_DEFAULTS` | Enforce GL rendering defaults (gl_texture=1, gl_lightmode=3, etc.) | 3.2.1 |
| 9 | 512 | `ZADF_NO_ROCKET_JUMPING` | Disable rocket jump thrust | 3.2.1 |
| 10 | 1024 | `ZADF_AWARD_DAMAGE_INSTEAD_KILLS` | Award points for damage, not just kills | 3.2.1 |
| 11 | 2048 | `ZADF_FORCE_ALPHA` | r_drawtrans forced to 1 | 3.2.1 |
| 12 | 4096 | `ZADF_COOP_SP_ACTOR_SPAWN` | Spawn actors as if single-player (Coop) | 3.2.1 |
| 13 | 8192 | `ZADF_MAX_BLOOD_SCALAR` | Force max blood brightness | 3.2.1 |
| 14 | 16384 | `ZADF_UNBLOCK_ALLIES` | Teammates pass through each other | 3.2.1 |
| 15 | 32768 | `ZADF_NODROP` | Players cannot drop items | 3.2.1 |
| 16 | 65536 | `ZADF_SURVIVAL_NO_MAP_RESET_ON_DEATH` | Don't reset map if all players die (Survival) | 3.2.1 |
| 17 | 131072 | `ZADF_DEAD_PLAYERS_CAN_KEEP_INVENTORY` | Dead spectators keep inventory (Survival) | 3.2.1 |
| 18 | 262144 | `ZADF_NOUNLAGGED_BFG_TRACERS` | Disable BFG backwards-reconciliation | 3.2.1 |
| 19 | 524288 | `ZADF_NODOORCLOSE` | Doors cannot be manually closed | 3.2.1 |
| 20 | 1048576 | `ZADF_FORCE_SOFTWARE_PITCH_LIMITS` | Pitch limited to software renderer range | 3.2.1 |
| 21 | 2097152 | `ZADF_SHOOT_THROUGH_ALLIES` | Hitscans/projectiles pass through teammates | 3.2.1 |
| 22 | 4194304 | `ZADF_DONT_PUSH_ALLIES` | Attacks don't thrust teammates | 3.2.1 |
| 23 | 8388608 | `ZADF_DONT_KEEP_JOIN_QUEUE` | Clear join queue between maps | 3.2.1 |
| 24 | 16777216 | `ZADF_DONT_HIDE_STATS` | Reveal player health/armor in PVP | **post-3.2.1** |
| 25 | 33554432 | `ZADF_DONT_OVERRIDE_PLAYER_COLORS` | Prevent cl_overrideplayercolors | 3.2.1 |
| 26 | 67108864 | `ZADF_NO_SPAWN_TELEFOG` | Teleport fog disabled on spawn | 3.2.1 |
| 27 | 134217728 | `ZADF_NO_ALLY_ICONS` | Ally icons hidden | **post-3.2.1** |
| 28 | 268435456 | `ZADF_NO_ENEMY_ICONS` | Enemy icons hidden | **post-3.2.1** |

## Compatibility flags

The `compatflags`, `compatflags2`, and `zacompatflags` cvars control emulation of older engine bugs and quirks. These are separate from the dmflags system but follow the same bitfield encoding. They are typically set per-map via `MAPINFO`'s `compat` block rather than globally via console, but they can be queried and set like any cvar. See `src/doomdef.h:414-527` for full enumeration. Most compatibility flags are documented individually elsewhere; this page addresses only dmflags-specific mechanics.

## Related documentation

- **Console cvar notes:** See `autoaim`, `fov`, and others under `console/notes/` for cvars that interact with specific dmflags.
- **Server variables:** The `sv_*` cvars in the console inventory often shadow individual flags; for example, `sv_degeneration` maps directly to `DF2_YES_DEGENERATION`.
- **MAPINFO:** Compatibility flags can be set per-map via the `compat` block in MAPINFO lumps.

## Engine scope note: dmflags3

**GZDoom and UZDoom forks include a `dmflags3` cvar for additional flags.** Zandronum does not have a `dmflags3` cvar; it instead uses `zadmflags` (Zandronum-specific dmflags) and `zacompatflags` (Zandronum-specific compatibility flags) for extensions. If a wad or documentation refers to `dmflags3`, it is GZDoom-family only and will not function on Zandronum.
