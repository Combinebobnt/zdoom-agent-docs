# `int GetPlayerSkin(int player, int type)`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-24)
**Provenance:** Zandronum Wiki `GetPlayerSkin` (retrieved 2026-08-18, https://wiki.zandronum.com/w/index.php?title=GetPlayerSkin&oldid=2249) + verified against Zandronum source's `src/p_acs.cpp:8766-8831` (ACSF_GetPlayerSkin case), `src/p_interaction.cpp:3271-3333` (`PLAYER_GetOverrideSkin`/`PLAYER_ShouldForceBaseSkin`), and `src/r_data/sprites.cpp:1026-1045` (`R_FindSkin`).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (index -176; dispatched as `ACSF_GetPlayerSkin`).

Returns a player's current skin index based on the specified retrieval type.

## Parameters

- `player`: The player number (0-based index) to query. Must be a valid connected player.
- `type`: The type of skin to retrieve. Valid types are:
  - `PLAYERSKIN_USERINFO` (0): The player's personal skin setting from their skin cvar, subject to cvars and class restrictions.
  - `PLAYERSKIN_WEAPON` (1): The preferred skin of the player's currently held weapon (if any), as defined by `Weapon.PreferredSkin`.
  - `PLAYERSKIN_ACS` (2): The skin explicitly set via `SetPlayerSkin()`.
  - `PLAYERSKIN_VISIBLE` (3): The skin currently displayed to others. Resolves an ACS-set skin against the current weapon's preferred skin (the weapon's skin wins by default when both exist, unless `SetPlayerSkin()`'s optional third argument asked the ACS skin to take priority instead), then falls back to the personal skin setting and finally the class base skin.

## Return value

Returns the numeric index of the player's skin in the current game's skin list. Returns `-1` if the player index is invalid, the player is not connected, or the requested skin does not exist.

## Behavior notes

- If a player's skin is forced to their class base (via `cl_skins` cvar restrictions on non-server clients, or the `NOSKIN` flag on their current class), queries of `PLAYERSKIN_USERINFO` return their base class skin instead of their personal preference. Morphing does not force the base skin by itself; a morphed player keeps their skin unless the morphed class itself carries `NOSKIN`.
- The `PLAYERSKIN_VISIBLE` type resolves an ACS-set skin against the equipped weapon's preferred skin: the weapon's skin wins by default when both exist, unless `SetPlayerSkin()`'s optional third argument set the ACS skin to override the weapon skin instead. Whichever of those two applies (or the only one present) is used; if neither is set, it falls back to the personal skin setting, then the class base skin.
- Skin indices below the number of player classes are each class's own reserved "Base" pseudo-skin slot, at an index equal to that class's own index; named skins from the `SKININFO` lump occupy the indices after that, in lump order. The "Base" skin therefore is not a fixed index like 0. It resolves to the querying player's own class index.

## Zandronum-specific: no UZDoom counterpart

This function exists only in Zandronum. UZDoom has no equivalent skin query mechanism.

## See also

- `SetPlayerSkin()` — set a player's skin override
- `GetSkinProperty()` — query skin properties like display name
