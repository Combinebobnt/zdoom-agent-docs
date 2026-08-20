# `bool RemoveBot([str name])`

**Tier:** A.
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-28)
**Provenance:** Zandronum Wiki `RemoveBot` (retrieved 2026-08-18, `https://wiki.zandronum.com/w/index.php?title=RemoveBot&oldid=2552`) + source-verified against the Zandronum source's `src/p_acs.cpp:8583-8649`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (index -169; dispatched as `ACSF_RemoveBot`).

Removes a bot from the game.

## Parameters

- `name` (optional `str`): The name of the bot to remove. If left unspecified or an empty string is provided, a bot is selected for removal based on the other criteria (see "Behavior" below). **Empty string handling is version-gated; see "Zandronum-specific: version gates" below.**

## Return value

Returns `1` if a bot was successfully removed, or `0` on error.

## Behavior

The function searches for and removes a bot matching the specified criteria:

- **Name-based removal.** If a name is provided (non-empty string), the function searches all connected players for a bot whose name matches the provided name (case-insensitive, after removing color codes). The first matching bot is removed.
- **Random removal.** If no name is provided (or an empty string, in 3.3-alpha and above), a random bot is selected from all connected players and removed.
- **Index parameter (3.3-alpha and above only).** When both name and index are provided, only a bot matching **both** name and player index is removed. If only index is provided, the player at that index (if a bot) is removed. **See "Zandronum-specific: version gates" below.**

## Failure conditions

The function returns `0` if any of the following conditions are met:

- **Called clientside.** RemoveBot can only be called from server-side scripts. Calling from a `CLIENTSIDE` script always fails.
- **Bot not found.** No bot with the specified name/index combination exists in the game, or no bots exist at all.
- **Invalid player index (3.3-alpha and above only).** When an index parameter is provided, it must be a valid player index (0 to MAXPLAYERS-1). An out-of-range index causes the function to fail immediately. **See "Zandronum-specific: version gates" below.**
- **Bot nodes disabled.** The current map has bot nodes disabled via the `nobotnodes` MAPINFO property.

## Zandronum-specific: version gates

RemoveBot exists in stable Zandronum 3.2.1 and earlier, but the wiki page documents features specific to the 3.3-alpha development version:

- **Two-parameter form (3.3-alpha and above only).** The development version accepts an optional second parameter `int index` to specify the player index of the bot to remove. Stable 3.2.1 does not support this parameter — only single-parameter calls are available. Attempting to call the two-parameter form on 3.2.1 results in a compile error.
- **Empty string random-removal behavior (3.3-alpha and above only).** In 3.3-alpha and above, passing an empty string as the `name` parameter is equivalent to passing no name, triggering random bot removal. In stable 3.2.1, the behavior for empty strings is not confirmed as matching this description.

The compiler-generated signature in `zt-bcc`'s `lib/zcommon.bcs` currently declares `RemoveBot(;str):bool` (single optional parameter, no index form), reflecting the stable baseline.

## See also

- `AddBot` (the counterpart function that adds a bot to the game)
