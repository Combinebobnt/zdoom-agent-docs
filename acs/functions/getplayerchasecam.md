# `bool GetPlayerChasecam(int player)`

**Tier:** A.
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-18)
**Provenance:** wiki page `GetPlayerChasecam - Zandronum Wiki.html` (retrieved `https://wiki.zandronum.com/w/index.php?title=GetPlayerChasecam&oldid=1331`) + source-verified (`p_acs.cpp:7697-7705`, `p_interaction.cpp` `PLAYER_IsValidPlayer`; `zt-bcc/lib/zcommon.bcs:1770`).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (index -137; dispatched as `ACSF_GetPlayerChasecam`).

Checks whether a given player is currently using the chasecam cheat (toggled by the `chase` console command).

## Parameters

- `player`: the player index to check. Invalid players (out-of-range index or not in-game) return `false`.

## Return value

Returns `true` if the player has the chasecam cheat enabled, `false` otherwise. Invalid player indices (index ≥ `MAXPLAYERS` or `playeringame[player]` false) silently return `false` rather than erroring.

## Zandronum-specific: GetPlayerChasecam

This function exists only in Zandronum; **UZDoom has no implementation.** The chasecam cheat itself (toggled by the `chase` console command, stored in `CF_CHASECAM` flag) exists in UZDoom, but there is no ACS accessor for it. A Zandronum-targeted script cannot check chasecam state portably without this function.

## Paired setter

[SetPlayerChasecam](setplayerchasecam.md) sets a player's chasecam state; note the return-type divergence — `GetPlayerChasecam` returns `bool`, while `SetPlayerChasecam` returns `int`.
