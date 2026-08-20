# `DynamicLight` class

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki "Controlling dynamic lights" (retrieved 2026-08-03, https://zdoom.org/w/index.php?title=Controlling_dynamic_lights&oldid=50043) + verified against UZDoom stdlib (`wadsrc/static/zscript/actors/shared/dynlights.zs`) and native light implementation (`src/playsim/a_dynlight.h`); re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — no drift in documented args/flags/radius behavior; blending note corrected against `src/rendering/hwrenderer/hw_dynlightdata.cpp` (pre-existing error, not caused by the pull).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** ZScript stdlib (`dynlights.zs`; class definitions), UZDoom native playsim (`src/playsim/a_dynlight.h`; radius calculation and flag semantics), and UZDoom hardware renderer (`src/rendering/hwrenderer/hw_dynlightdata.cpp`, `src/common/rendering/hwrenderer/data/hw_dynlightdata.h`; blending bucket semantics).

Dynamic lights are actors that emit light into the rendered scene. The `DynamicLight` base class and its subclasses (`PointLight`, `PointLightPulse`, `PointLightFlicker`, `SpotLight`, and their variants) allow spawned ZScript actors to control light color, intensity, type, and rendering behavior via actor arguments and flags. Unlike property-based lights attached via the `Light()` actor property, manually spawned dynamic lights persist until explicitly destroyed.

## Light parameter arguments (args array)

Dynamic light behavior is controlled through the actor's `args[]` array. The `DynamicLight` class defines named constants for these indices (accessible as `LIGHT_RED`, `LIGHT_GREEN`, etc., or with the `DynamicLight.` prefix from outside the class):

| Argument | Constant | Range | Purpose |
|----------|----------|-------|---------|
| args[0] | `LIGHT_RED` | 0-255 | Red channel intensity |
| args[1] | `LIGHT_GREEN` | 0-255 | Green channel intensity |
| args[2] | `LIGHT_BLUE` | 0-255 | Blue channel intensity |
| args[3] | `LIGHT_INTENSITY` (alias: `LIGHT_SCALE`) | 0+ | Light radius size and 50% falloff point |
| args[4] | `LIGHT_SECONDARY_INTENSITY` | 0+ | Secondary size for flicker and pulse light types |

**Radius calculation:** The actual mapunit radius of the light is **double the `args[3]` value**, so `args[3]` represents the 50% falloff point rather than the full light radius. A light with `args[3] = 128` illuminates to a full radius of 256 mapunits.

## Light type subclasses

`DynamicLight` provides several subclasses for different light animation types:

- **`PointLight`** — static, non-animated light
- **`PointLightPulse`** — light that pulses between full intensity and zero (controlled by the `args[4]` secondary size)
- **`PointLightFlicker`** — light that flickers irregularly
- **`PointLightFlickerRandom`** — random flicker pattern
- **`SectorPointLight`** — sector light type (special sector-based light behavior)
- **`SpotLight`** — spotlight in a cone pattern (controlled by `SpotInnerAngle` and `SpotOuterAngle` properties)

Each type also has `-Additive`, `-Subtractive`, and `-Attenuated` variants (e.g., `PointLightAdditive`, `PointLightSubtractive`, `SpotLightFlickerRandomAttenuated`) for different blending/falloff modes.

## Flags

Light flags control rendering behavior. They are accessible as actor flags (e.g., `+DYNAMICLIGHT.SUBTRACTIVE` in a Default block) or as named constants in the engine's `LightFlag` enum:

| Flag | Effect |
|------|--------|
| `DYNAMICLIGHT.SUBTRACTIVE` | Light darkens (subtracts from) surfaces instead of brightening them |
| `DYNAMICLIGHT.ADDITIVE` | Light is rendered via a distinct additive-blend path with a reduced color-intensity scale (rather than the default full-intensity contribution); still cumulative with other lights, as all dynamic lights are |
| `DYNAMICLIGHT.DONTLIGHTSELF` | The actor carrying the light does not receive its own light |
| `DYNAMICLIGHT.DONTLIGHTACTORS` | Light does not affect actors (only affects map geometry) |
| `DYNAMICLIGHT.DONTLIGHTMAP` | Light does not affect map geometry (only affects actors) |
| `DYNAMICLIGHT.ATTENUATE` | Light applies angle attenuation for more realistic falloff on angled surfaces (slightly dimmer) |
| `DYNAMICLIGHT.NOSHADOWMAP` | Light does not cast shadow maps (geometric shadows from map features) |
| `DYNAMICLIGHT.SPOT` | Light is a spotlight (cone-shaped, angle controlled by `SpotInnerAngle` and `SpotOuterAngle`) |
| `DYNAMICLIGHT.DONTLIGHTOTHERS` | Light affects only its own owning actor, excluding all other actors (semantic inverse of `DONTLIGHTSELF`, not of `DONTLIGHTACTORS`) |

**Note:** The wiki page on this topic omits `DONTLIGHTOTHERS` and provides incomplete information on `ADDITIVE`; both are documented above per engine source verification. Correction (2026-08-03): `ADDITIVE` and `SUBTRACTIVE` are not enforced as mutually exclusive by the engine — the two flag bits are independent, and nothing rejects setting both (if both are set, the hardware renderer's subtractive path wins since it is evaluated after the additive one). The default when neither flag is set is a distinct "normal" contribution (full-intensity color, no additive-specific attenuation), not the `ADDITIVE` mode itself — the hardware renderer buckets lights into three separate categories (normal/subtractive/additive) rather than treating "neither flag" as additive. **Error found and corrected in the 2026-08-15 re-verification pass:** `DONTLIGHTOTHERS` was previously (mis)described here as the inverse of `DONTLIGHTACTORS`. Per `FDynamicLight::ShouldLightActor()` (`src/playsim/a_dynlight.h`), `DONTLIGHTACTORS` suppresses the light's effect on actors entirely (map geometry only), while `DONTLIGHTSELF` and `DONTLIGHTOTHERS` are the actual inverse pair: `DONTLIGHTSELF` excludes just the owning actor from the light's effect, and `DONTLIGHTOTHERS` excludes every actor except the owner. `DONTLIGHTOTHERS` has no direct relationship to `DONTLIGHTACTORS`.

## Usage and lifecycle

Unlike actor-property lights attached via the `Light()` property (which disappear when the actor changes sprite/frame or is removed), manually spawned `DynamicLight` actors persist independently until explicitly destroyed. This allows for:

- **Dynamic color changes** — modifying `args[]` values at runtime immediately affects the rendered light color and intensity
- **Independent lifetime control** — the light survives actor sprite changes and manual removal of the parent actor
- **Complex lighting patterns** — multiple light types can be spawned and controlled independently

**Bookkeeping consideration:** Because manually spawned lights do not automatically clean up with their parent actor (if any), code responsible for spawning lights should also handle their cleanup, either by destroying the light actor explicitly or by anchoring it to a persistently-tracked parent.

**Note (added 2026-08-03):** The native `Light()`-property attachment path (`AttachLight`/`AttachLightDef`/`AttachLightDirect`) now silently no-ops when called on an actor already flagged for destruction (`OF_EuthanizeMe`), instead of attaching a light to a dying actor. This doesn't change any behavior documented above for manually spawned `DynamicLight` actors.

## Implementation note

This documentation covers behavior visible in UZDoom 5.0.0-pre's ZScript stdlib and native light implementation. The rendering backend (shadow maps, angle attenuation, subtractive blending) is GPU-dependent and may vary across hardware and renderer configurations.
