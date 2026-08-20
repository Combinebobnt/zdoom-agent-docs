# `int SetPlayerProperty(int who, int set, int which)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `SetPlayerProperty - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`https://zdoom.org/w/index.php?title=SetPlayerProperty&oldid=52943`) + source-verified against `p_lnspec.cpp:2987-3216`, `d_player.h:227-251`,
`doomdef.h:539`, `compatibility.cpp:108`, `zt-bcc/lib/zcommon.bcs:119-138,1530`.
`BCOMPATF_LINKFROZENPROPS`-introducing commit (`5af1e6f734b`, 2013-07-02) confirmed to predate the
3.2.1 version-bump commit (`28f736fb3`). `PROP_BUDDHA2`/`PROP_GODMODE2` confirmed absent from
`d_player.h`'s cheat enum (not just unwired) by direct grep, distinguishing them from
`PROP_FRIGHTENING`/`PROP_NOCLIP`/`PROP_NOCLIP2`/`PROP_GODMODE` (bit exists, switch case doesn't).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** action special (positive index).

Action special (index 191, the zt-bcc source's `lib/zcommon.bcs:1530`), implementation in
`FUNC(LS_SetPlayerProperty)` (the Zandronum source's `src/p_lnspec.cpp:2987-3216`).

- `who` — `0` affects only the activator, nonzero affects every in-game, non-spectating player.
- `set` — nonzero turns the property on / gives it, `0` turns it off / takes it away. Exception:
  for `PROP_INVULNERABILITY` specifically, `set == 1` gives invulnerability *with* the inverted
  greyscale palette, `set == 2` (or any other nonzero) gives it *without* the palette change —
  both still count as "on" for every other property.
- `which` — one of the `PROP_*` constants (`zt-bcc/lib/zcommon.bcs:119-138`). Spectators are
  always skipped, both for the single-activator and the all-players branch.

## The wiki's deprecation note is real, but only covers part of the enum — verify per-value, not as a blanket rule

The wiki page carries a top-level note: *"Using this special to grant powerup effects to players
has been deprecated. Consider using the GiveInventory function for this purpose instead."* That
note applies specifically to the sub-range the engine implements as literal powerup give/take
(`arg2 >= PROP_INVULNERABILITY && arg2 <= PROP_SPEED`, `p_lnspec.cpp:2996`) — it does **not** apply
to the flag-style properties (`PROP_FROZEN`, `PROP_NOTARGET`, `PROP_INSTANTWEAPONSWITCH`,
`PROP_FLY`, `PROP_TOTALLYFROZEN`, `PROP_BUDDHA`), which set/clear a `cheats` bitmask directly and
have no `GiveInventory` equivalent — those remain the normal, non-deprecated way to do this in
Zandronum. Splitting the full enum by actual engine behavior:

- **Flag-style, fully functional, not deprecated:** `PROP_FROZEN` (0, `CF_FROZEN`), `PROP_NOTARGET`
  (1, `CF_NOTARGET`), `PROP_INSTANTWEAPONSWITCH` (2, `CF_INSTANTWEAPSWITCH`), `PROP_FLY` (3,
  `CF_FLY`, plus directly toggles `MF2_FLY`/`MF_NOGRAVITY` on the actor), `PROP_TOTALLYFROZEN` (4,
  `CF_TOTALLYFROZEN`), `PROP_BUDDHA` (16, `CF_BUDDHA`).
- **Powerup give/take, functional but wiki-deprecated — prefer `GiveActorInventory`/
  `TakeActorInventory`:** `PROP_INVULNERABILITY` (5, `APowerInvulnerable`), `PROP_STRENGTH` (6,
  `APowerStrength`), `PROP_INVISIBILITY` (7, `APowerInvisibility`), `PROP_RADIATIONSUIT` (8,
  `APowerIronFeet`), `PROP_INFRARED` (10, `APowerLightAmp`), `PROP_WEAPONLEVEL2` (11,
  `APowerWeaponLevel2`), `PROP_FLIGHT` (12, `APowerFlight`), `PROP_SPEED` (15, `APowerSpeed`).
- **`PROP_ALLMAP` (9) is a special case inside the powerup range**, not a real powerup: it
  toggles `level.flags2 & LEVEL2_ALLMAP` (the automap-revealed flag), but only when the acting
  player's index equals the engine's global `consoleplayer` (`p_lnspec.cpp:3060`,`3081`) — i.e. it
  only visibly does anything for whichever player happens to be the local console player on the
  machine running the check. In the `who != 0` ("all players") branch this makes it effectively a
  no-op for every player except that one, which is easy to misread as "broadcast the automap to
  everyone" from the wiki description alone.
- **`PROP_UNUSED1`/`PROP_UNUSED2` (13, 14) are explicitly guarded no-ops** — the `powers[]` lookup
  table has `NULL` at both indices and the function returns `false` before doing anything
  (`p_lnspec.cpp:3005-3008`). Matches the wiki's own "Does nothing. Do not use."
- **`PROP_BUDDHA2` (17) and `PROP_GODMODE2` (22) don't exist in Zandronum at all** — there is no
  `CF_BUDDHA2`/`CF_GODMODE2` bit anywhere in `d_player.h`'s cheat enum. These are newer upstream
  ZDoom values the wiki documents that Zandronum never implemented; passing them falls through
  the property switch with no matching `case`, so `mask` stays `0` and the call is a **silent
  no-op returning `false`**, with no compiler or runtime indication that the name is meaningless
  in this engine.
- **`PROP_FRIGHTENING` (18), `PROP_NOCLIP` (19), `PROP_NOCLIP2` (20), `PROP_GODMODE` (21) are a
  different, sharper trap: the underlying cheat bits (`CF_FRIGHTENING`, `CF_NOCLIP`,
  `CF_NOCLIP2`, `CF_GODMODE`) *do* exist and work elsewhere in the engine (console `god`/`noclip`
  commands, netevent cheats) — but `LS_SetPlayerProperty`'s `switch (arg2)` (`p_lnspec.cpp:3006-3024`)
  simply has no `case` for any of them.** Same silent-no-op outcome as `PROP_BUDDHA2`/`PROP_GODMODE2`,
  but this one isn't "feature doesn't exist in Zandronum" — the feature exists, this specific
  action special just never wires it up. There is no substitute call in this special for setting
  these from ACS.

## Engine-family divergence: the "these five PROP_* values are dead" claims above are Zandronum-only

UZDoom wires up every property this doc lists above as a Zandronum-only no-op or Zandronum-absent
value. Its `LS_SetPlayerProperty` switch (UZDoom's `src/playsim/p_lnspec.cpp`, function starting
around line 2911) has explicit cases for `PROP_BUDDHA2` and `PROP_GODMODE2` mapping to their own
cheat-flag bits, and separate explicit cases for `PROP_FRIGHTENING`, `PROP_NOCLIP`, `PROP_NOCLIP2`,
and `PROP_GODMODE`, each mapping to the matching cheat-flag bit (`PROP_NOCLIP2` sets both the
regular and "2" noclip bits together, mirroring how the console `noclip2` cheat works). All of the
underlying bits this doc names as "exist elsewhere but never wired here" (`src/playsim/d_player.h`
in UZDoom) are present and are reachable through this special on UZDoom:

- `SetPlayerProperty(who, set, PROP_BUDDHA2)` and `SetPlayerProperty(who, set, PROP_GODMODE2)`
  actually toggle the "absolute" buddha/god cheat variants (the ones no voodoo-doll damage can
  bypass), not a silent no-op.
- `SetPlayerProperty(who, set, PROP_FRIGHTENING)`, `PROP_NOCLIP`, `PROP_NOCLIP2`, and `PROP_GODMODE`
  actually toggle the same cheat state the equivalent console commands (`god`, `noclip`) drive, not
  a silent no-op.

Only `PROP_UNUSED1` (13) and `PROP_UNUSED2` (14) remain genuine no-ops on UZDoom, for the same
reason as Zandronum: they fall inside the powerup-give/take index range but the lookup table has
no class name at those slots, so the function bails out before doing anything. A script gated on
"these five properties are always inert, only `PROP_UNUSED1`/`PROP_UNUSED2` are dead" — reasonable
on Zandronum — silently starts having real, cheat-granting effects for five of those values the
moment the same script runs on UZDoom.

Separately, the "Spectators are always skipped" claim above doesn't transfer either — UZDoom has no
spectator concept anywhere in its player/level state (nothing named "spectator" appears in UZDoom's
source at all), so the all-players branch simply affects every player the engine considers
in-game; there's no spectator state left for it to skip.

## `who != 0` has an extra compat-flag interaction that `who == 0` doesn't

In the "all players" branch only, if the server compat flag `BCOMPATF_LINKFROZENPROPS` is set
(`ib_compatflags`, `doomdef.h:539`, "Clearing PROP_TOTALLYFROZEN or PROP_FROZEN also clears the
other"), clearing either `PROP_FROZEN` or `PROP_TOTALLYFROZEN` clears both
(`p_lnspec.cpp:3188-3192`). The single-activator (`who == 0`) branch has no equivalent check —
calling `SetPlayerProperty(0, 0, PROP_FROZEN)` on just the activator never links to
`PROP_TOTALLYFROZEN`, regardless of the compat flag. This asymmetry predates the 3.2.1 version
bump (`28f736fb3`), so it's present at the current target engine, not a 3.3-alpha-only change.

**Example — the wiki's own toggle-freeze pattern, still idiomatic (`PROP_TOTALLYFROZEN` is not
deprecated):**

```text
void PlayerFreeze (bool isOn)
{
    if (isOn)
    {
        Thing_Stop(0);
        SetPlayerProperty(0, 1, PROP_TOTALLYFROZEN);
    }
    else
    {
        SetPlayerProperty(0, 0, PROP_TOTALLYFROZEN);
    }
}
```
