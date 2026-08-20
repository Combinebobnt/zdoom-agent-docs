# `int SetPlayerChasecam(int player, bool enable)`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-18)
**Provenance:** wiki page `SetPlayerChasecam - Zandronum Wiki.html` (retrieved `https://wiki.zandronum.com/w/index.php?title=SetPlayerChasecam&oldid=1330`) + source-verified (`p_acs.cpp:7674-7695`, `p_interaction.cpp` `PLAYER_IsValidPlayer`; `zt-bcc/lib/zcommon.bcs:1769`).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (index -136; dispatched as `ACSF_SetPlayerChasecam`).

Enables or disables a player's chasecam cheat (the same cheat toggled by the `chase` console command).

## Parameters

- `player`: the player index whose chasecam state to set. Invalid players (out-of-range index or not in-game) cause the function to fail (see "Return value" below).
- `enable`: `true` to enable the chasecam cheat, `false` to disable it. Toggling an already-enabled chasecam on (or an already-disabled one off) still succeeds and returns `1`.

## Return value

Returns `1` if the player is valid (passes `PLAYER_IsValidPlayer`), `0` otherwise. The return value reports player validity, not whether the function actually toggled the chasecam state; enabling an already-enabled chasecam or disabling an already-disabled one returns `1` with no change. Invalid player indices return `0` silently without error.

## Zandronum-specific: SetPlayerChasecam

This function exists only in Zandronum; **UZDoom has no ACS implementation.** The chasecam cheat itself (toggled by the `chase` console command, stored in `CF_CHASECAM` flag) exists in UZDoom's engine, but there is no ACS function to set it. A Zandronum-targeted script cannot control chasecam state portably without this function.

## Wiki/engine divergence

The wiki page states: "Returns true if the player's chasecam was successfully changed, false on failure." The actual source behavior is narrower — it returns `1` (true) if the player index is valid, `0` (false) if not. The function does *not* return whether a change occurred; enabling a player's already-enabled chasecam still returns `1`. The change-detection logic in the source (`players[ulPlayer].cheats != oldvalue`) exists but gates only the `SERVERCOMMANDS_SetPlayerCheats` server notification, not the return value.

## Return-type asymmetry

The paired getter, [GetPlayerChasecam](getplayerchasecam.md), is declared to return `bool` (in `zt-bcc/lib/zcommon.bcs:1770`), while this setter is declared to return `int` (line 1769). Both return the same VM int type at dispatch, but the declared signature differs — a discrepancy worth noting when scripts call them in the same context.
