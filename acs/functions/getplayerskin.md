# `int GetPlayerSkin(int player, int type)`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-28)
**Provenance:** Zandronum Wiki `GetPlayerSkin` (retrieved 2026-08-18, https://wiki.zandronum.com/w/index.php?title=GetPlayerSkin&oldid=2249) + verified against Zandronum source's `src/p_acs.cpp:3355-3408` (ACSF_GetPlayerSkin case).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (index -176; dispatched as `ACSF_GetPlayerSkin`).

Returns a player's current skin index based on the specified retrieval type.

## Parameters

- `player`: The player number (0-based index) to query. Must be a valid connected player.
- `type`: The type of skin to retrieve. Valid types are:
  - `PLAYERSKIN_USERINFO` (0): The player's personal skin setting from their skin cvar, subject to cvars and class restrictions.
  - `PLAYERSKIN_WEAPON` (1): The preferred skin of the player's currently held weapon (if any), as defined by `Weapon.PreferredSkin`.
  - `PLAYERSKIN_ACS` (2): The skin explicitly set via `SetPlayerSkin()`.
  - `PLAYERSKIN_VISIBLE` (3): The skin currently displayed to others — uses weapon preference first if available, then personal skin, with fallback to the player's class base skin.

## Return value

Returns the numeric index of the player's skin in the current game's skin list. Returns `-1` if the player index is invalid, the player is not connected, or the requested skin does not exist.

## Behavior notes

- If a player's skin is forced to their class base (via `cl_skins` cvar restrictions, the `NOSKIN` flag on their class, or morphing), queries of `PLAYERSKIN_USERINFO` return their base class skin instead of their personal preference.
- The `PLAYERSKIN_VISIBLE` type synthesizes the final displayed skin by checking, in order: weapon preference override, ACS override, personal skin setting, and class base skin fallback.
- Skin indices correspond to the order in the `SKININFO` lump; the "Base" skin is always available at index 0 but the actual index returned may differ.

## Zandronum-specific

This function exists only in Zandronum. UZDoom has no equivalent skin query mechanism.

## See also

- `SetPlayerSkin()` — set a player's skin override
- `GetSkinProperty()` — query skin properties like display name
