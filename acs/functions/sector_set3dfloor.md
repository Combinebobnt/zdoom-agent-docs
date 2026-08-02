# Sector_Set3dFloor

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Extracted from ZDoom Wiki (https://zdoom.org/w/index.php?title=Sector_Set3dFloor&oldid=51021); Zandronum implementation verified against `p_3dfloors.cpp` and `p_lnspec.cpp`.

**⚠ CRITICAL FORK DIVERGENCE:** In Zandronum, this special is **only implemented as a linedef type** (processed at map load via `P_Spawn3DFloors()`). As an **ACS action special** (callable via `ACS_ExecuteAlways`, `ActionSpecial`, etc.), special 160 maps to `LS_NOP` and silently returns `false` — the 3D floor is never created. The ZDoom wiki assumes this can be called dynamically from ACS; in Zandronum, it cannot.

**Signature**

```
Sector_Set3dFloor(int tag, int type, int flags, int alpha, int hi_tag_or_line_id) -> int
```

**Parameters**

- **tag**: Sector tag of affected sectors (the sectors that will have the 3D floor).
- **type**: Type of 3D floor (see Types below). If bit 3 (value 8) is set, `hi_tag_or_line_id` is treated as a line ID; otherwise it's a high byte for the tag.
- **flags**: Flags controlling behavior (see Flags below).
- **alpha**: Translucency (0 = invisible, 255 = opaque).
- **hi_tag_or_line_id**: Either a high byte for multi-sector tags (Doom/Hexen format) or a line ID (if type has 8 added to it); unused in UDMF.

**Types**

(From ZDoom wiki — behavior unverified in Zandronum, since the ACS special does not execute.)

- **0**: Vavoom-style (control sector's ceiling is 3D floor's bottom, floor is top; control sector needs negative height).
- **1**: Solid.
- **2**: Swimmable.
- **3**: Non-solid.
- **+4**: Render inside as well (normally only for liquids).
- **+16**: Invert visibility rules (opposite of default).
- **+32**: Invert shootability rules (opposite of default).

**Flags**

(From ZDoom wiki — behavior unverified in Zandronum.)

- **1**: Disable lighting effects.
- **2**: Restrict lighting to between floor and ceiling only.
- **4**: GZDoom only; "fog" effect (unverified if it exists in Zandronum).
- **8**: Ignore bottom height; draw floor and ceiling at control sector's ceiling.
- **16**: Use sidedef upper texture instead of linedef mid texture.
- **32**: Use sidedef lower texture instead of linedef mid texture.
- **64**: Additive translucency.
- **512**: Apply control sector's fade color to area below.
- **1024**: Reset lighting from 3D floors above.

**Return Value**

`0` (false) in Zandronum (special does nothing). ZDoom wiki suggests true on success, but this cannot be verified here.

**Behavior**

*In Zandronum ACS:* Returns 0 immediately. No 3D floor is created.

*In Zandronum linedefs:* If a map linedef has special 160, it is processed during `P_Spawn3DFloors()` at map load and creates the 3D floor. This is the only way 3D floors work in Zandronum.

**See Also**

- `Transfer_Heights` (special 209) — also a NOP in Zandronum ACS; also works only as a linedef special at map load.
- Zandronum renderer 3D floor subsystem (`p_3dfloors.cpp`, `r_3dfloors.cpp`).
