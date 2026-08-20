# `int SetPlayerSkin(int player, str skin[, bool overrideWeaponPreferredSkin])`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-28)
**Provenance:** Zandronum Wiki `SetPlayerSkin` (retrieved 2026-08-18, https://wiki.zandronum.com/w/index.php?title=SetPlayerSkin&oldid=2267) + verified against Zandronum source's `src/p_acs.cpp:8740-8762` (ACSF_SetPlayerSkin case); UZDoom has no `SetPlayerSkin` in `src/playsim/actionspecials.h` or `src/playsim/p_acs.cpp`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (index -175; dispatched as `ACSF_SetPlayerSkin`).

Sets an ACS-driven skin override for a player. Only exists in Zandronum; UZDoom has no equivalent mechanism.

## Parameters

- `player`: The player number (0-based index) whose skin to override. Must be a valid connected player.
- `skin`: Name of the skin to apply. An empty string `""` clears the ACS-side override instead of setting a skin. Unknown skin names do not cause failure — name-to-index resolution is deferred to the getter side (see `GetPlayerSkin()` for why that matters).
- `overrideWeaponPreferredSkin` (optional): If `true`, this ACS-set skin takes precedence over a weapon's `PreferredSkin` setting. Defaults to `false` if omitted. **Important:** omitting this parameter or passing `false` will reset a previously-set `true` value to `false` on that player — there is no way to query or preserve the current override state.

## Return value

Returns `1` on success, `0` on failure. The only failure case is an invalid or unconnected player index; a successfully-set unknown skin name returns `1`.

## Behavior notes

- Skin name validation happens only when the skin is queried via `GetPlayerSkin()`, not when `SetPlayerSkin()` sets it. A player can be assigned a non-existent skin; `GetPlayerSkin()` will return `-1` for it.
- The internal state `ACSSkinOverridesWeaponSkin` is written every call, so a 2-argument call silently changes an earlier 3-argument `true` override to `false`.
- On a server, the change is broadcast to other clients via `SERVERCOMMANDS_SetPlayerACSSkin()`. Clientside behavior is not verified here.
- Behavior after player respawn or class-change events is not verified here.

## Zandronum-specific: absence from UZDoom

This function exists only in Zandronum. No equivalent skin-assignment mechanism exists in UZDoom/GZDoom-family engines.

## Wiki/engine divergence

The wiki page's "Usage" section states "Returns a player's skin," which is copy-pasted from the `GetPlayerSkin()` documentation. This function **sets** a player's skin; it does not retrieve one. The actual return value (1 or 0) is documented correctly in the "Return value" section.

## See also

- `GetPlayerSkin()` — retrieve a player's current skin by type (personal, weapon-preferred, ACS-set, or visible)
- `GetSkinProperty()` — query properties of a skin like its display name
