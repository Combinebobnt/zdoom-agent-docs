# `int SetMapUsedStatus(int position, bool used)`

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-06-06)
**Provenance:** Zandronum Wiki `SetMapUsedStatus` (retrieved 2026-08-18, https://wiki.zandronum.com/w/index.php?title=SetMapUsedStatus&oldid=2509); verified against the Zandronum source's `src/p_acs.cpp:5552` (`EACSFunctions` enum) and `:8998` (dispatch `case ACSF_SetMapUsedStatus`).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (value 187 in the `EACSFunctions` enum; dispatched as `ACSF_SetMapUsedStatus`).

Controls whether a map in the server's map rotation is marked as used (i.e., whether it shouldn't be used again until the rotation is complete). Only callable from `NET` (server-side) scripts; client scripts are silently rejected.

## Parameters

- `position` — The position of the map in the rotation, **1-based**. Position 1 is the first rotation entry. Must be between 1 and `GetMapRotationSize()` to be valid; internally the engine does `ulPosition = args[0] - 1` to convert to the 0-based `g_MapRotationEntries` index. Passing `0` or a negative value causes the function to treat it as an out-of-range index (unsigned underflow).
- `used` — The used status to set. `true` marks the map as played this rotation cycle; `false` marks it as not yet played.

## Return value

Returns `1` on success (the operation completed and changed the used status), `0` otherwise.

The function returns `0` if:
- The calling script is running on the client (not the server) — see "Client-mode rejection" below.
- `position` is out of range (outside the bounds of the rotation list).
- The current `used` value already matches what you're trying to set — no-op writes return `0`, even though the state is correct. This differs from the documentation, which implies failure only when the position is invalid.

## Client-mode rejection (undocumented by the wiki)

Unlike read-only functions like `GetMapRotationInfo`, which return default values on the client, `SetMapUsedStatus` does not allow client-side invocation at all. The engine source checks `NETWORK_InClientMode()` at the start and immediately returns `0` if the script is running in client mode, without attempting to modify anything. This is enforced regardless of position or used-value validity — a client calling this function always gets `0` back.

## Zandronum-specific: uncallable from zt-bcc

This function exists in the Zandronum engine (`ACSF_SetMapUsedStatus` in `src/p_acs.cpp:5552`, with a dispatch `case` at `:8998`), but is not exposed by the zt-bcc compiler. It does not appear in `zt-bcc`'s `lib/zcommon.bcs` special table or `src/builtin.c` function table at any numeric index — the special table runs to extension function index -185 (`IsPlayerContestingControlPoint`), then jumps to the Q-Zandronum block at -141, skipping the -186 through -200 range where `SetMapUsedStatus` would be (as index -187).

Scripts in Zandronum that need to control map-rotation used status must do so through this engine function directly, but **there is no way to call it from BCS source when targeting this engine via zt-bcc**. The Zandronum engine accepts the call at runtime (`PCD_CALLFUNC` dispatch), but the BCS compiler provides no way to generate the bytecode for this specific function's index.

## Version note

This function was added after the Zandronum 3.2.1 release. It is only available in development builds of Zandronum 3.3-alpha and newer, not in 3.2.1. Does not exist in any version of UZDoom.

## See also

- `GetMapRotationInfo` — reads properties of map-rotation entries (name, lump name, used status, player limits). Same client-side read restriction as this function's client-mode rejection, but returns default values rather than being a no-op.
- `GetMapRotationSize` — returns the number of entries in the current map rotation.
- `GetMapPosition` — gets the current or next position in the rotation, separate from querying a specific entry's properties.
