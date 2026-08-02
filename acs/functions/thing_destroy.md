# Thing_Destroy

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki, verified against Zandronum 3.3-alpha source (`p_lnspec.cpp`, `FUNC(LS_Thing_Destroy)`)
**Bucket:** Action special (index 133)

**Signature:** `int Thing_Destroy(int tid, [int extreme, int tag])`

Destroys one or more actors. The specific actors targeted and whether they are gibbed depend on the parameters:

- `tid`: Thing ID(s) to destroy. Zero means "all monsters on the map" (optionally filtered by `tag`).
- `extreme`: If nonzero, the destroyed actor(s) enter their gib-death sequence (if one exists), using `TELEFRAG_DAMAGE` (1,000,000) to bypass any damage reduction. If zero, the actor is killed with damage equal to its current `health` value, which can be partially negated by armor (see below).
- `tag`: Sector tag filter. Only actors in sectors with this tag are destroyed. Zero means no tag filter (affects the specified tid regardless of sector). Only valid when `tid` is nonzero; when `tid == 0`, the tag filter is applied but if `tag == 0` as well, all monsters are killed globally via `P_Massacre()`.

**Return:** Always `true`.

**Limitations:**

- Only actors with the `MF_SHOOTABLE` flag can be destroyed (e.g., monsters and normal actors; non-shootable decorations and certain special actor types will not be affected).
- **Armor interaction bug (extreme = 0):** When `extreme` is zero, the function applies damage to the target equal to the target's current health value. For players, this assumes no armor; if the player has armor, the armor absorbs some or all of the damage, and the player may survive. This is the function's documented failure mode when `extreme == 0` — use `extreme = 1` to reliably gib, or apply explicit damage with `Thing_Damage` for more control.

**Examples:**

- `Thing_Destroy(0)` — kill all monsters.
- `Thing_Destroy(0, 1)` — kill all monsters and gib them.
- `Thing_Destroy(123)` — destroy the actor with TID 123.
- `Thing_Destroy(123, 1, 5)` — destroy the actor with TID 123 if it's in a sector with tag 5, gibbing it.
