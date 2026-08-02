# `int GetPlayerInfo(int playernumber, int playerinfo)`

Retrieves a property of a player. Compiler builtin (`PCD_GETPLAYERINFO`,
the Zandronum source's `src/p_acs.cpp:12665-12692`).

**Bucket:** compiler builtin.

- `playernumber` — player index (0–`MAXPLAYERS-1`). **If the player is not in the game
  (`!playeringame[playernumber]`), returns `-1`** — indistinguishable from a legitimate value in
  some error contexts.
- `playerinfo` — property selector, one of the `PLAYERINFO_*` constants defined in
  the zt-bcc source's `lib/zcommon.bcs:358-367`. **Unknown property returns `0`** — indistinguishable
  from several legitimate zero values (see below). **The wiki documents 11 constants, but only 10
  are actually implemented in this fork** (see "Missing FVIEWBOB" section).

## Return value and sentinel ambiguity

- **Invalid player (`playernumber` out of range or `!playeringame[playernumber]`):** returns `-1`.
- **Unknown property:** returns `0`.
- **Known property, legitimate zero value:** also returns `0` — so `0` cannot be used as an
  error check. Affected properties: `PLAYERINFO_AIMDIST` (when `dmflags2 & DF2_NOAUTOAIM`),
  `PLAYERINFO_GENDER` (0 = male), `PLAYERINFO_TEAM` (0 = blue).

## Implemented properties — return types and gotchas

All properties below are implemented and verified except `PLAYERINFO_FVIEWBOB` (see next section).

1. **`PLAYERINFO_TEAM`** — team index: 0=blue, 1=red, 2=green, 3=gold, 4=black, 5=white,
   6=orange, 7=purple (this is the hardcoded team list default, not a TEAMINFO-defined list).
   **If the player is not on a team (`!pl->bOnTeam`), returns `TEAM_None` (255), not `NO_TEAM`
   (2).** The two constants are often confused — `GetPlayerInfo(p, PLAYERINFO_TEAM) == NO_TEAM`
   is a wrong-but-compiles comparison that will never be true, and should be replaced with
   `GetPlayerInfo(p, PLAYERINFO_TEAM) == 255` or `!= [0-7]`. (See `functions/getcontrolpointinfo.md`
   for the same `TEAM_None`/`NO_TEAM` trap in a different function.)

2. **`PLAYERINFO_AIMDIST`** — autoaim distance, returned in "angle" units (ANGLE_1 = 1/360 full
   turn = 0x06E93334 raw). This is **not** a player preference alone — it respects the server's
   `dmflags2 & DF2_NOAUTOAIM` setting: if enabled, always returns `0` regardless of the player's
   `autoaim` cvar. Clamped at 35° even if the cvar is higher. Cannot be used to detect
   autoaiming capability on a per-player basis when the server has autoaim globally disabled.

3. **`PLAYERINFO_COLOR`** — player color as `0xRRGGBB` packed hex (plain `int`).

4. **`PLAYERINFO_GENDER`** — gender index: 0=male, 1=female, 2=neutral, 3=object (plain `int`).

5. **`PLAYERINFO_NEVERSWITCH`** — **despite its name, reads `userinfo.switchonpickup`, not
   `neverswitchonpickup`.** Returns the engine's `switchonpickup` cvar (plain `int`, clamped
   0–3), which the wiki does not document. The four-state setting changed from the original
   binary "on/off" to allow three distinct modes (default 1). Exact semantics per value (0, 1, 2,
   3) are not exposed via ACS and must be inferred from non-ACS documentation.

6. **`PLAYERINFO_MOVEBOB`** — player's move-bob setting from the `movebob` cvar, returned as
   **`fixed_t` (fixed-point with `FRACUNIT`=65536=1.0), not plain `int`** — must be stored in a
   `fixed` variable or treated as fixed-point, or the value will be off by 65536×. The underlying
   cvar is a float, and the return path goes through `FLOAT2FIXED`.

7. **`PLAYERINFO_STILLBOB`** — player's still-bob setting from the `stillbob` cvar, returned as
   **`fixed_t` (fixed-point)**, same as `PLAYERINFO_MOVEBOB`.

8. **`PLAYERINFO_PLAYERCLASS`** — player's selected class number. In Hexen, 0=fighter, 1=cleric,
   2=mage. Plain `int`. (This is the *selected* class, not the *current* morphed class — use
   `PlayerClass()` builtin for the latter.)

9. **`PLAYERINFO_FOV`** — player's current field-of-view, returned as `(int)pl->FOV` — truncated
   from a `float` field, so 90.5° becomes 90 (plain `int`, not fixed-point despite being float-derived).

10. **`PLAYERINFO_DESIREDFOV`** — player's preferred field-of-view from the `fov` setting, returned
    as `(int)pl->DesiredFOV` — same truncation as `PLAYERINFO_FOV` (plain `int`).

## Missing `PLAYERINFO_FVIEWBOB` — wiki/fork divergence

The ZDoom wiki lists `PLAYERINFO_FVIEWBOB` (first-person view bob) as the 8th property. **This
constant is not defined in this fork's `zcommon.bcs`** (enum stops at `PLAYERINFO_DESIREDFOV` —
`zcommon.bcs:366`), and **the engine switch has no case for it either** (`p_acs.cpp:12674-12689`
implements only the 10 above) — calling it silently falls through to `default: return 0;` and
does nothing. Use a workaround from upstream ZDoom documentation or skip this property entirely
in Zandronum mods.

## Spectators

Spectators are included in the validity check — they pass the `playeringame[n]` gate and return
real values. There is no special handling for spectators as distinct from ordinary players.

**Example — warn a player if they're not on a team:**

```
int team = GetPlayerInfo(PlayerNumber(), PLAYERINFO_TEAM);
if (team > 7)  // Use > 7 instead of checking NO_TEAM or == 255
{
    Print(s: "You are not on a team!");
}
```

**Example — read a fixed-point property correctly (movebob):**

```
fixed bob = GetPlayerInfo(playernumber, PLAYERINFO_MOVEBOB);
Log(s: "Move bob: ", f: bob);  // Correct — bob is fixed-point
int bob_wrong = GetPlayerInfo(playernumber, PLAYERINFO_MOVEBOB);
// Wrong — bob_wrong is off by 65536× if bob isn't 1.0 exactly
```

**Provenance:** wiki page `GetPlayerInfo - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`oldid=54371`) + source-verified against `p_acs.cpp:12665-12692`, `d_player.h:362-432` (userinfo_t
getters), `zt-bcc/lib/zcommon.bcs:358-367`. Wiki/fork discrepancies: `PLAYERINFO_FVIEWBOB` is
documented on the wiki but absent from both `zcommon.bcs` and the engine switch; `PLAYERINFO_TEAM`
returns `TEAM_None` (255) when the player is not on a team, contrasting with `NO_TEAM` (2) constant.
TEAM_None behavior confirmed as an ancestor of the 3.2.1 version-bump commit. **Engine:** Zandronum
3.2.1. **Tier:** A.
