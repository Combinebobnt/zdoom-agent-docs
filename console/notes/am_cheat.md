# `am_cheat`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Zandronum source `src/am_map.cpp:631` (CUSTOM_CVAR declaration) and consuming code throughout the file; verified against wiki description (ZDoom Wiki `CVARs:Automap`, https://zdoom.org/w/index.php?title=CVARs%3AAutomap&oldid=54516).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

Controls the level of detail and cheat features visible on the automap. Takes integer values 0–6, with each mode adding visibility beyond the previous.

## Mode behavior

- **0**: No cheat. Only architecture the player has seen is shown.
- **1**: All architecture is shown, regardless of whether the player has seen it. Equivalent to one `iddt` cheat code input.
- **2**: In addition to mode 1, all things in the map are shown as arrows pointing in the direction they face. Equivalent to two `iddt` inputs.
- **3**: In addition to mode 2, all things are wrapped in a bounding box showing their collision size. No vanilla equivalent (ZDoom extension).
- **4–6**: Same as modes 1–3 respectively, except lines flagged as "hidden" (`ML_DONTDRAW`) are not shown. This differs from the vanilla behavior where mode 1–3 always show hidden lines.

All of the above is confirmed identical on UZDoom: the same mode logic appears in `src/am_map.cpp` at the equivalent call sites (line-hiding at `am_map.cpp:2684-2778`, thing/arrow display at `am_map.cpp:2892-3057`, bounding boxes at `am_map.cpp:3158`, the thing-drawing gate at `am_map.cpp:3427`), and the `iddt` cheat handler in `src/st_stuff.cpp:468` advances `am_cheat` one step at a time and wraps back to 0 after reaching 2, on both engines — so mode 3 remains unreachable from the vanilla cheat code on UZDoom too.

## Storage behavior

This cvar is declared with no flags (`0`), meaning it does **not** persist to the config file when the game exits. Its value resets to the default (0) on every game start unless explicitly set via console, CVARINFO, or ACS script. For persistent automap cheat state across sessions, the config file must be manually edited. UZDoom declares the same cvar with the same no-persistence flag (`am_map.cpp:133`) and forces it back to 0 in networked play when cheats aren't enabled, matching Zandronum's behavior; the only difference is which network-state check gates that reset — plain `netgame` on UZDoom versus `NETWORK_InClientMode()` on Zandronum.

## Engine-family divergence: hidden-sector suppression in textured automap

The mode table above covers line visibility, but `am_cheat` also gates a second, unrelated suppression in the textured-automap (`am_textured`) subsector renderer, and the two engines disagree here. Both engines skip subsectors belonging to a MAPINFO/UDMF-hidden sector (`SECF_HIDDEN`/`SECMF_HIDDEN`) whenever `am_cheat == 0` (Zandronum `src/am_map.cpp:1935`; UZDoom `src/am_map.cpp:2092`). UZDoom additionally re-applies that suppression for `am_cheat >= 4` (`src/am_map.cpp:2098-2101`) — an addition documented in that codebase's own inline comments as deliberately keeping MAPINFO-hidden sectors hidden at the higher cheat tiers even though ordinary unseen-architecture tinting is turned off there — and at exactly `am_cheat == 4` also skips the "unseen architecture" desaturation tint that other modes apply, drawing those subsectors in their true color instead (`src/am_map.cpp:2229-2230`). Zandronum has no equivalent — once `am_cheat != 0`, its `AM_drawSubsectors` draws every hidden sector unconditionally at every mode 1–6, with no special-casing at 4–6 and no true-color exception at 4. In short: on UZDoom, modes 4–6 hide *both* `ML_DONTDRAW` lines and MAPINFO-hidden sectors in textured automap view; on Zandronum they only hide the lines.

## Related cvars

- **`am_showkeys`** — whether keys are highlighted with symbols
- **`am_showthingsprites`** — sprite display options for revealed things
