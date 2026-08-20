# Sector_Set3dFloor

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Extracted from ZDoom Wiki (https://zdoom.org/w/index.php?title=Sector_Set3dFloor&oldid=51021); Zandronum implementation verified against `p_3dfloors.cpp` and `p_lnspec.cpp`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

## Wiki/engine divergence: this special is a no-op when invoked dynamically from ACS, on both engines

This is not a Zandronum-only quirk — a from-scratch re-check of the UZDoom source found the exact
same architecture. On **both** UZDoom and Zandronum, `Sector_Set3DFloor` is **only implemented as
a linedef type**, processed once at map load (Zandronum's `P_Spawn3DFloors()` in `p_3dfloors.cpp`;
UZDoom's equivalent `MapLoader::Spawn3DFloors()` in `src/maploader/specials.cpp`). As an **ACS
action special** (callable via `ACS_ExecuteAlways`, `ActionSpecial`, etc.), special 160 maps to
`LS_NOP` in both engines' line-special dispatch table (Zandronum's `src/p_lnspec.cpp:3760`; UZDoom's
`src/playsim/p_lnspec.cpp:3707`) and silently returns `false` — the 3D floor is never created. ACS
in both engines reaches this same table via `P_ExecuteSpecial()`, so there is no separate ACS-only
code path that could behave differently from the linedef-time NOP. The ZDoom wiki page this entry
was extracted from assumes the special can be called dynamically from ACS; on neither engine
checked here can it.

**Signature**

```text
Sector_Set3dFloor(int tag, int type, int flags, int alpha, int hi_tag_or_line_id) -> int
```

**Parameters**

- **tag**: Sector tag of affected sectors (the sectors that will have the 3D floor).
- **type**: Type of 3D floor (see Types below). If bit 3 (value 8) is set, `hi_tag_or_line_id` is treated as a line ID; otherwise it's a high byte for the tag.
- **flags**: Flags controlling behavior (see Flags below).
- **alpha**: Translucency (0 = invisible, 255 = opaque).
- **hi_tag_or_line_id**: Either a high byte for multi-sector tags (Doom/Hexen format) or a line ID (if type has 8 added to it); unused in UDMF.

**Types**

Verified identical on both engines — Zandronum's `P_Set3DFloor()` (`p_3dfloors.cpp`) and UZDoom's
`MapLoader::Set3DFloor()` (`src/maploader/specials.cpp`) build the flags word from `type` (masked
to drop the line-ID bit) via the same `defflags[type & 3]` table plus the same `+4`/`+16`/`+32`
modifier checks:

- **0**: Vavoom-style (control sector's ceiling is 3D floor's bottom, floor is top; control sector needs negative height).
- **1**: Solid.
- **2**: Swimmable.
- **3**: Non-solid.
- **+4**: Render inside as well (normally only for liquids).
- **+16**: Invert visibility rules (opposite of default).
- **+32**: Invert shootability rules (opposite of default).

**Flags**

Verified against `P_Set3DFloor()` (Zandronum) / `MapLoader::Set3DFloor()` (UZDoom) — both build the
same flags word from the `flags` argument bit-for-bit, up through bit 512. Bits 1024 and 2048
diverge between the two engines; see the divergence section below.

- **1**: Disable lighting effects (`FF_NOSHADE`). Same on both engines.
- **2**: Restrict lighting to between floor and ceiling only (`FF_DOUBLESHADOW`). Same on both engines.
- **4**: "Fog" effect (`FF_FOG`). Exists and behaves the same on both engines — the old "GZDoom only, unverified if it exists in Zandronum" hedge was wrong; Zandronum's `p_3dfloors.cpp` handles `flags & 4` identically to UZDoom's.
- **8**: Thin floor (`FF_THINFLOOR`) — makes the 3D floor's bottom plane track the control sector's *ceiling* instead of its floor, so the floor renders as a zero-thickness slab sitting at the control sector's ceiling height rather than spanning floor-to-ceiling. Same on both engines.
- **16**: Use sidedef upper texture instead of linedef mid texture (`FF_UPPERTEXTURE`). Same on both engines.
- **32**: Use sidedef lower texture instead of linedef mid texture (`FF_LOWERTEXTURE`). Same on both engines.
- **64**: Additive translucency (`FF_ADDITIVETRANS | FF_TRANSLUCENT`). Same on both engines.
- **128**: Flood-fill towards the next lowest flooding/solid 3D floor or the sector bottom (`FF_FLOOD`, plus `FF_SEETHROUGH | FF_SHOOTTHROUGH`); only takes effect if the floor isn't solid. Present and identical on both engines but missing from the original wiki-derived list here — added from source, not wiki-attested.
- **512**: Apply control sector's fade color to area below / walls (`FF_FADEWALLS`). Same on both engines.
- **1024**: Reset lighting from 3D floors above (`FF_RESET`). **UZDoom only** — see the divergence section below.
- **2048**: No damage transfer (`FF_NODAMAGE`) — the 3D floor's own damage-type/amount doesn't apply to things inside it. **UZDoom only**, and wasn't in the original wiki-derived list here at all — added from source. See the divergence section below.

**Return Value**

`0` (false) on both engines — the special is dispatched to `LS_NOP`, whose body is `return false;`
verbatim in both `p_lnspec.cpp` files. The ZDoom wiki suggests true on success for the (unreachable,
on these engines) dynamic-ACS case; that claim was never checkable here and still isn't.

**Behavior**

*Invoked from ACS (either engine):* Returns 0 immediately. No 3D floor is created.

*As a map linedef (either engine):* If a linedef has special 160, it is processed once at map load —
Zandronum's `P_Spawn3DFloors()`, UZDoom's `MapLoader::Spawn3DFloors()` — and creates the 3D floor.
This is the only way 3D floors get created from this special on either engine.

## Engine-family divergence: flags 1024 and 2048 don't exist on Zandronum

UZDoom's `src/playsim/p_3dfloors.h` defines `FF_RESET = 0x80000000` ("light effect is completely
reset, once interrupted") and `FF_NODAMAGE = 0x100000` ("no damage transfers"), and its
`Set3DFloor()` sets them from `flags & 1024` and `flags & 2048` respectively. Zandronum's
`src/p_3dfloors.h` defines neither constant at all — its enum stops at `FF_THISINSIDE`, and its
`P_Set3DFloor()` in `p_3dfloors.cpp` stops checking flag bits after `flags & 512` (`FF_FADEWALLS`).
Setting bit 1024 or 2048 on a `Sector_Set3DFloor` linedef is therefore a real behavioral no-op on
Zandronum — the bits are silently ignored, not merely undocumented — while on UZDoom they engage
`FF_RESET`/`FF_NODAMAGE`. A map or mod relying on either bit for cross-engine behavior needs a
Zandronum-side fallback (e.g. a different lighting/damage design for that build).

**See Also**

- `Transfer_Heights` (special 209) — also a NOP when invoked from Zandronum ACS; also works only as a linedef special at map load. (Not re-verified against UZDoom this pass — out of scope for this entry.)
- 3D floor subsystem source: Zandronum's `src/p_3dfloors.cpp`/`src/p_lnspec.cpp`/`src/r_3dfloors.cpp`; UZDoom's `src/playsim/p_3dfloors.cpp`/`src/playsim/p_lnspec.cpp`.
