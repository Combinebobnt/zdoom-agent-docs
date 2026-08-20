# Sector_SetFriction

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2025-07-29)
**Provenance:** Sector_SetFriction - ZDoom Wiki (https://zdoom.org/w/index.php?title=Sector_SetFriction&oldid=44656), verified against Zandronum source 2025-07-29.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

**Signature:** `int Sector_SetFriction(int tag, int amount)`

## Behavior

Sets the friction override for all sectors with the matching tag using the BOOM friction formula. The script-side behavior differs from the static map-initialization path for Boom linedef type 223 in multiple ways: script calls always replicate to clients and update flags (init-path never touches flags); `amount == 0` has a different meaning; and `amount` is unvalidated on the script path (clamped to 200 max at init time).

## Parameters

- **`tag`**: Sector tag. Tag `0` applies the friction override to all untagged sectors in the map (every sector with literal tag 0), **with no fallback to the triggering line's back sector** (unlike `GetSectorFloorZ`/`Floor_MoveToValue`). A tag matching zero sectors is a silent no-op; the function still returns `true`.
- **`amount`**: Friction value that drives an internal fixed-point friction calculation (via the BOOM formula). The effective friction and movefactor plateau at both ends:
  - `amount == 100`: Friction equals `ORIG_FRICTION` (0xE800 fixed), interpreted as "normal" — **clears the `FRICTION_MASK` flag, disabling the override entirely**. The stored value is consulted only if no terrain friction applies, but this change is **not replicated to late-joining clients** (the flag gate in `sv_main.cpp:3549` blocks it).
  - `amount` ≤ 54 (approximately): Movefactor clamps to its floor of 32, making these values effective but indistinguishable from each other in how fast actors decelerate.
  - `amount < 100` (range 55–99 primarily): Friction below normal; actors move more sluggishly (increased friction, "sludgy").
  - `amount > 100` (range 101–199): Friction above normal; actors move more freely (decreased friction, "icy").
  - **`amount >= 200`: Friction saturates to frictionless (0x10000 fixed)**; all values in range 200–255 are identical.
  - No validation on `amount`; the formula applies to any input. `amount == 0` produces `friction = 0xD001` (maximum sludge), not BOOM 223's line-length behavior — see Fork divergence.

Zandronum-specific: On a server, script calls that change friction trigger `SERVERCOMMANDS_SetSectorFriction` to broadcast to all connected clients. Late-joiner replication via the full-state-update path (`sv_main.cpp:3548–3551`) is gated on both friction-differs-from-`SavedFriction` *and* the `FRICTION_MASK` flag being set — so `Sector_SetFriction(tag, 100)` (which clears the flag) never reaches clients who join after the call.

## Return value

Always returns `true`, unconditionally. A tag matching zero sectors or a server-side rejection (impossible for this function) is indistinguishable from success.

## Wiki/engine divergence: `amount == 0` behavior

The ZDoom wiki describes `Sector_SetFriction(tag, 0)` as equivalent to setting friction from the triggering linedef's length, following Boom linedef type 223. **This is only true at map-initialization time** (static linedef property). When called from a script at runtime, `amount == 0` has no special handling — the BOOM formula applies normally, producing `friction = 0xD001` (maximum sludge). If you want friction to depend on a line's length, you must do that computation yourself in the script and pass the result. This holds identically on both engine families — neither branches the script-callable action special's `amount == 0` case back to a line-length lookup; only the separate static map-init path (which the script call never goes through) does that.

## Related

- [Plane-trigger family](families/plane-trigger.md) — shares the same `tag == 0` no-fallback behavior (unlike `GetSectorFloorZ`/`Floor_MoveToValue`, which do have a fallback).
- Sector_SetColor, Sector_SetFade, Sector_Set3dFloor — other sector-modifier specials, unrelated to friction mechanics (no shared code paths).
- `Floor_MoveToValue` (action special 37) — has a fallback to triggering line's back sector when `tag == 0`, the opposite of this function.
