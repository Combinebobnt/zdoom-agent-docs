# `void SetAmmoCapacity(str typename, int maxamount)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `SetAmmoCapacity (ACS) - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29, `https://zdoom.org/w/index.php?title=SetAmmoCapacity_%28ACS%29&oldid=52592`) + source-verified against `p_acs.cpp:11843-11879`, `g_shared/a_pickups.h:240` (`AAmmo : public AInventory`), `zt-bcc/src/builtin.c:132`. Wiki/fork divergence (direct-parent-only `Ammo` check, activator-only targeting, item-creation-on-first-use with `Amount` zeroed, Zandronum-only server-sync packet) recorded above rather than silently trusted or omitted.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.

Sets the max-carry amount of an ammo type on the **activator only**. Compiler builtin
(`PCD_SETAMMOCAPACITY`, the zt-bcc source's `src/builtin.c:132`), implementation in
`DLevelScript::RunScript`'s big switch, the Zandronum source's `src/p_acs.cpp:11843-11879`.

- No `tid`/actor parameter exists at all — unlike `SetActorProperty`/`GetActorProperty`, this
  function can only ever affect `activator`. **If `activator == NULL`** (e.g. called from a
  script type with no natural activator, or `ACS_ExecuteAlways` from a non-actor source), the
  whole call is a **silent no-op** — no error, nothing pushed/changed (`p_acs.cpp:11844`, the
  entire body is gated on `activator != NULL`).
- `typename` — a class name string looked up with `PClass::FindClass`. The check is
  **`type->ParentClass == RUNTIME_CLASS(AAmmo)`** (`p_acs.cpp:11849`) — this requires the class's
  **immediate** parent to be exactly `Ammo`, not merely "somewhere in its ancestry". A class two
  levels deep (e.g. a custom ammo subclassing `ClipAmmo` rather than `Ammo` directly) would fail
  this check and be silently ignored even though it's a "derived type from Ammo" in the loose
  sense. The wiki's phrasing — "Any item from the list Ammo is accepted, as well as derived types
  from Ammo" — reads as if any descendant works; the actual fork behavior is narrower (direct
  children of `Ammo` only). Not confirmed whether this is a Zandronum-specific narrowing or matches
  upstream ZDoom (no ZDoom source available locally to check) — flagging as a fork/wiki divergence
  either way since it's not discoverable from the wiki text. `GetAmmoCapacity` uses the identical
  check, so the same restriction applies symmetrically to the getter.
- If `type` doesn't resolve, or resolves but isn't a direct `Ammo` subclass, the call is a
  **silent no-op** — matches the wiki's "silently ignored" for non-ammo items, but note the same
  silent-ignore also covers a not-found class name and the narrower-than-expected inheritance
  check above.
- **If the activator doesn't already have the item, one is created:** `GiveInventoryType(type)` is
  called, then `MaxAmount` is set to the requested value and **`Amount` (current ammo) is
  explicitly zeroed** (`p_acs.cpp:11862-11867`). This is not just "raise the cap for an ammo type
  the player doesn't hold" — it actually grants the inventory item outright, with zero current
  ammo. If the item **does** already exist, only `MaxAmount` is touched; current `Amount` is left
  alone.
- No clamping or validation on `maxamount` — a negative value or an absurdly large one is written
  straight into `item->MaxAmount` with no bounds check.
- **Zandronum-specific netcode path, not present in vanilla ZDoom semantics:** if the activator is
  a player and this is running as a network server (`NETWORK_GetState() == NETSTATE_SERVER`), and
  the resulting `MaxAmount` actually differs from what it was before the call (`oldMaxAmount`,
  captured before the change — `-1` if the item didn't exist yet), the server sends
  `SERVERCOMMANDS_SetPlayerAmmoCapacity` to sync the change to clients (`p_acs.cpp:11869-11875`).
  If the "before" and "after" `MaxAmount` are equal (including the edge case of creating a new
  item whose requested cap happens to equal `-1`, which can't happen in practice since `-1` isn't
  a sane cap), no packet is sent — this is purely a bandwidth-avoidance check, not a gameplay
  difference.

**Example — grow max ammo capacity on pickup (from the wiki, semantics verified against this
fork):**

```text
if (GetAmmoCapacity("Clip") < 800)
{
    SetAmmoCapacity("Clip", GetAmmoCapacity("Clip") + 100);
}
```
