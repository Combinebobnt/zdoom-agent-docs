# `int SetPlayerSkin(int player, str skin[, bool overrideWeaponPreferredSkin])`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** Zandronum Wiki `SetPlayerSkin` (retrieved 2026-08-18, https://wiki.zandronum.com/w/index.php?title=SetPlayerSkin&oldid=2267) + verified against Zandronum source's `src/p_acs.cpp:8740-8762` (ACSF_SetPlayerSkin case), `src/sv_commands.h:172` and `src/sv_commands.cpp:663-673` (broadcast to all clients), `src/cl_main.cpp:4638-4642` (client apply), `src/sv_main.cpp:2690` (full update), `src/g_game.cpp:2196-2197,2261-2262` (`G_PlayerReborn` carry-over), `src/p_interaction.cpp:3271-3301,3336-3375` and `src/r_data/sprites.cpp:1026-1045` (per-class resolution and fallback); UZDoom has no `SetPlayerSkin` in `src/playsim/actionspecials.h` or `src/playsim/p_acs.cpp`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (index -175; dispatched as `ACSF_SetPlayerSkin`).

Sets an ACS-driven skin override for a player. Only exists in Zandronum; UZDoom has no equivalent mechanism.

## Parameters

- `player`: The player number (0-based index) whose skin to override. Must be a valid connected player.
- `skin`: Name of the skin to apply. An empty string `""` clears the ACS-side override instead of setting a skin. Unknown skin names do not cause failure. The name is stored as-is and only resolved to a skin index each time it is used (rendering, `GetPlayerSkin()`).
- `overrideWeaponPreferredSkin` (optional): If `true`, this ACS-set skin takes precedence over a weapon's `PreferredSkin` setting. Defaults to `false` if omitted. **Important:** omitting this parameter or passing `false` will reset a previously-set `true` value to `false` on that player — there is no way to query or preserve the current override state.

## Return value

Returns `1` on success, `0` on failure. The only failure case is an invalid or unconnected player index; a successfully-set unknown skin name returns `1`.

## Behavior notes

- Skin name validation happens only when the skin is queried via `GetPlayerSkin()`, not when `SetPlayerSkin()` sets it. A player can be assigned a non-existent skin; `GetPlayerSkin()` will return `-1` for it.
- The internal state `ACSSkinOverridesWeaponSkin` is written every call, so a 2-argument call silently changes an earlier 3-argument `true` override to `false`.
- The name is resolved against the player's current class each time. A skin that doesn't exist, or that the current class can't use, is skipped when the player is drawn: the weapon's `PreferredSkin` (if valid) or the player's personal skin shows instead.
- Offline and on a server the call sets the fields locally. On a server it then sends `SetPlayerACSSkin` to every client, including the target player's own. Clients apply it unconditionally, and clients joining later receive the current value in their full update.
- A client that runs it locally (e.g. from a `CLIENTSIDE` script) changes only its own copy, which the server's next `SetPlayerACSSkin` overwrites.
- The override persists across respawns: player rebirth carries both the skin name and the override flag over. After a class change the same name is re-resolved for the new class.

## Zandronum-specific: absence from UZDoom

This function exists only in Zandronum. No equivalent skin-assignment mechanism exists in UZDoom/GZDoom-family engines.

## Wiki/engine divergence

The wiki page's "Usage" section states "Returns a player's skin," which is copy-pasted from the `GetPlayerSkin()` documentation. This function **sets** a player's skin; it does not retrieve one. The actual return value (1 or 0) is documented correctly in the "Return value" section.

## See also

- `GetPlayerSkin()` — retrieve a player's current skin by type (personal, weapon-preferred, ACS-set, or visible)
- `GetSkinProperty()` — query properties of a skin like its display name
