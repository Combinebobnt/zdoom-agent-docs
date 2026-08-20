# `int SetNextMapPosition(int position, bool ignoreLimits)`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-18)
**Provenance:** wiki page `SetNextMapPosition - Zandronum Wiki.html` (retrieved 2026-08-18, `https://wiki.zandronum.com/w/index.php?title=SetNextMapPosition&oldid=2476`) + source-verified against the Zandronum source (`src/p_acs.cpp:8883-8897`, `src/maprotation.cpp:158-165`, `src/maprotation.h`, `zt-bcc/lib/zcommon.bcs:1806`).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (index -178; dispatched as `ACSF_SetNextMapPosition`).

Sets which entry in the server's map rotation will play next. Zandronum-only. Extension function (`ACSF_SetNextMapPosition`, index -178 in `zt-bcc/lib/zcommon.bcs:1806`), implementation in the Zandronum source's `src/p_acs.cpp:8883-8897`.

## Parameters

- `position` — 1-based index into the map rotation, valid range `1..GetMapRotationSize()` inclusive. **Note: position 0 is not treated as "current map" here** (unlike `GetMapRotationInfo`, where `position <= 0` has special meaning) — position 0 is simply out of range. Underflows (`args[0] - 1` with `args[0]=0`) silently fail the bound check.
- `ignoreLimits` — if `true`, the next map ignores its configured player count limits (`sv_maprotation` min/max players) when determining whether it can be loaded; if `false`, limits are enforced normally.

## Return value

Returns `1` on success, `0` on failure. Failure occurs when:

- The given `position` is out of range (`>= GetMapRotationSize()`).
- The given `position` is already the next map in rotation (calling `SetNextMapPosition(GetMapPosition(MAPPOSITION_NEXT))` always returns `0`). The rationale: there's no work to do if the rotation's next-position field already points where you're trying to set it.

## Clientside behavior and replication

The ACS call always mutates local rotation state (`g_NextMapInList` and `g_NextMapIgnoresLimits`), regardless of whether the calling script runs on client or server. The broadcast to other players (via `SERVERCOMMANDS_SetNextMapPosition()`) is gated to server-only execution (`NETWORK_GetState() == NETSTATE_SERVER`), so a client-side ACS call locally changes its own `g_NextMapInList` variable but does not replicate to the server or other clients. To change the next map for all players, call this from a server-executed (non-`CLIENTSIDE`) script on the server itself.

## See also

- `GetMapPosition(MAPPOSITION_NEXT)` — returns the 1-based position of the next map; useful as an argument to this function to query before setting.
- `GetMapRotationSize()` — returns the number of entries in the rotation; `position` must be `<= GetMapRotationSize()` to succeed.
- `GetMapRotationInfo()` — reads individual properties (name, lump name, player limits) of rotation entries. **Note the 1-based position numbering is the same, but position 0 has special meaning there** (means "current map"), while position 0 is simply out of range here.

**Related but not merged into one file:** `GetMapPosition`/`GetMapRotationSize`/`GetMapRotationInfo`/`SetNextMapPosition` are all part of the server's map-rotation subsystem and could plausibly be folded into a single `families/map-rotation.md` file in a future consolidation pass — flagging this rather than doing it unilaterally, since several were processed concurrently in the same intake batch.

## Engine-family divergence

`SetNextMapPosition` is bound as ACSF (CALLFUNC) index 178, inside the 100–199 range UZDoom's own ACSF enum reserves for Zandronum's extensions and implements none of. UZDoom's `CallFunction` dispatcher is a plain `switch` with `default: break;` falling through to `return 0` — no error, no log line, script execution continues normally. A Zandronum-compiled object calling `SetNextMapPosition` under UZDoom silently gets `0` back rather than mutating any rotation state. See [Zandronum/UZDoom compatibility](../concepts/zandronum-uzdoom-compat.md) for the general mechanism.

This is a less acute trap than some reserved-range functions: `0` is already this function's documented failure return, so the "didn't work" signal is consistent between genuine failure on Zandronum and "feature doesn't exist" on UZDoom. Unlike `GetMapRotationSize` (whose `0` can mean either "no rotation" or "feature missing"), the *intent* of a `SetNextMapPosition` call is to mutate state, and receiving `0` reliably signals "the mutation didn't happen," even if the reason differs.
