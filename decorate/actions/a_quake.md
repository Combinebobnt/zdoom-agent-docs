# `A_Quake(int intensity, int duration, int damrad, int tremrad [, sound sfx])`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_Quake` (retrieved 2026-07-31, oldid=50609) + verified against
the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:5308` and `src/g_shared/a_quake.cpp`.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_Quake)`, defined in `src/thingdef/thingdef_codeptr.cpp:5308` and implemented via `P_StartQuake` in `src/g_shared/a_quake.cpp:170`.

Creates an earthquake effect centered on the calling actor, dealing damage and applying tremor over a specified duration.

## Parameters

- **`intensity`** — Strength of the quake. The parameter accepts an integer (unlike the ZDoom 4.11.0+ wiki which changed it to float), and is clamped to the range 1–9 internally (0 is treated as 1). The intensity value is used to calculate thrust force applied to players caught in the damage radius.
- **`duration`** — How long the quake lasts, in tics.
- **`damrad`** — Radius of the damage effect in map units (not 64-unit tiles — see notes below). If 0, no damage is dealt, but the tremor effect still occurs at `tremrad` distance.
- **`tremrad`** — Radius of the tremor effect in map units. All actors (primarily used for camera shake in players) within this radius feel the quake's intensity, regardless of line-of-sight or other checks.
- **`sfx`** — Sound effect to play during the quake. **Unlike the ZDoom wiki's stated default of `"world/quake"`**, this parameter has no fallback in Zandronum — if omitted, the call produces no sound at all. The sound loops for the entire duration and stops when the quake ends.

## Behavior

**Damage and thrust:** Each tic that the quake is active, for each player in the game:
- If the player is within `damrad` of the quake center *and* is standing on solid ground (floor), there is a 50/256 (roughly 19.5%) chance per tic of taking 1d6 damage.
- Simultaneously, the player is thrust away from the quake center with a force proportional to intensity (internally `intensity << (FRACBITS-1)`), simulating knockback.

**Tremor:** The tremor radius determines which actors feel the quake for effects like screen shaking. The combined intensity from all overlapping quakes near an actor is calculated; if multiple quakes affect one actor, the highest intensity takes precedence (not additive).

**Networking:** In multiplayer, the quake is server-authoritative. When a server creates a quake via `A_Quake`, it broadcasts `SERVERCOMMANDS_Earthquake` to all clients, ensuring synchronized quake effects across the network.

## Comparison with `Radius_Quake` (map special)

The `Radius_Quake` line special (Action 120) is similar but uses 64-unit tiles for its radius arguments — it internally multiplies the supplied radii by 64 before passing to `P_StartQuake`. `A_Quake` takes map units directly, so a quake that should affect a 400-unit radius uses `A_Quake(..., 400)`, whereas `Radius_Quake` would use argument `400 / 64 = 6.25` (rounded as needed). This is the key difference mentioned in the ZDoom wiki's "Comparison" note.

## Engine-family divergence

- **A_QuakeEx** — The ZDoom wiki references a more advanced `A_QuakeEx` action with additional parameters for customizing quake behavior. This action **does not exist in Zandronum**; it is a GZDoom/UZDoom-family extension only.
- **Intensity parameter type** — ZDoom 4.11.0+ made intensity a float; Zandronum accepts only integers.
- **Sound default** — ZDoom wiki describes a `"world/quake"` default; Zandronum has no default (omitting the parameter results in silent quake).

## See also

- `Radius_Quake` (line special, Action 120) — creates a quake effect via map trigger
- `Radius_Quake2` (ACS function) — ACS-callable variant
- The related `StaticGetQuakeIntensity()` function, which calculates combined tremor intensity for an actor affected by overlapping quakes (primarily used by the engine for camera effects)
