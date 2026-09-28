# `am_cheat`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** Zandronum source `src/am_map.cpp:631` (CUSTOM_CVAR declaration) and consuming code throughout the file; storage corrections from `src/d_main.cpp:1791-1800`, `src/p_acs.cpp:5795`, `src/p_acs.cpp:11284-11298`, `src/gameconfigfile.cpp:505-536`, `src/gameconfigfile.cpp:561-564`, `src/cl_main.cpp:590`; verified against wiki description (ZDoom Wiki `CVARs:Automap`, https://zdoom.org/w/index.php?title=CVARs%3AAutomap&oldid=54516).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

Controls the level of detail and cheat features visible on the automap. Takes integer values 0–6, with each mode adding visibility beyond the previous.

## Mode behavior

- **0**: No cheat. Only architecture the player has seen is shown.
- **1**: All architecture is shown, regardless of whether the player has seen it. Equivalent to one `iddt` cheat code input.
- **2**: In addition to mode 1, all things in the map are shown as arrows pointing in the direction they face. Equivalent to two `iddt` inputs.
- **3**: In addition to mode 2, all things are wrapped in a bounding box showing their collision size. No vanilla equivalent (ZDoom extension).
- **4–6**: Same as modes 1–3 respectively, except lines flagged as "hidden" (`ML_DONTDRAW`) are not shown. This differs from the vanilla behavior where mode 1–3 always show hidden lines. Modes 4–6 also skip two-sided lines with no floor or ceiling height change, which only modes 1–3 draw (Zandronum `src/am_map.cpp:2382`), so those lines look as they do in mode 0. Secret doors (`ML_SECRET` lines with a back sector) differ by engine: Zandronum draws them in the secret-wall color at every mode 1–6 (`src/am_map.cpp:2290`), while UZDoom does so only at modes 1–3 and draws them as plain walls at 4–6 (`src/am_map.cpp:2716`).

All of the above is confirmed identical on UZDoom: the same mode logic appears in `src/am_map.cpp` at the equivalent call sites (line-hiding at `am_map.cpp:2684-2778`, thing/arrow display at `am_map.cpp:2892-3057`, bounding boxes at `am_map.cpp:3158`, the thing-drawing gate at `am_map.cpp:3427`), and the `iddt` cheat handler in `src/st_stuff.cpp:468` advances `am_cheat` one step at a time and wraps back to 0 after reaching 2, on both engines — so mode 3 remains unreachable from the vanilla cheat code on UZDoom too.

## Storage behavior

This cvar is declared with no flags (`0`), meaning it does **not** persist to the config file when the game exits. Its value resets to the default (0) on every game start unless set again, e.g. from the console, an autoexec file or a `+am_cheat` command-line argument. CVARINFO cannot set it: declaring an engine cvar's name there is a fatal "cvar 'am_cheat' already exists" error on both engines (Zandronum `src/d_main.cpp:1791-1800`). ACS `SetCVar` refuses it on both engines because it is not a mod-created cvar (Zandronum `src/p_acs.cpp:5795`). On Zandronum, ACS `ConsoleCommand("am_cheat 2")` does reach the console dispatcher (`src/p_acs.cpp:11284-11298`) and sets the cvar in whichever process runs the script. On UZDoom, ACS `ConsoleCommand` is unsupported, so no ACS path can set it. A hand-added `am_cheat` line in the config file is applied at startup, since the config reader sets any existing cvar it finds (Zandronum `src/gameconfigfile.cpp:505-536`). It lasts one session only: on exit the section is cleared and rewritten with archived cvars alone (`src/gameconfigfile.cpp:561-564`). UZDoom declares the same cvar with the same no-persistence flag (`am_map.cpp:133`) and forces it back to 0 in networked play when cheats aren't enabled, matching Zandronum's behavior. The reset is gated by plain `netgame` on UZDoom and by `NETWORK_InClientMode()` on Zandronum. Zandronum clients additionally zero `am_cheat` when connecting to a server (`src/cl_main.cpp:590`) and re-run the check once the server's `sv_cheats` value arrives (`src/cl_main.cpp:6221`).

## Engine-family divergence: hidden-sector suppression in textured automap

The mode table above covers line visibility, but `am_cheat` also gates a second, unrelated suppression in the textured-automap (`am_textured`) subsector renderer, and the two engines disagree here. Both engines skip subsectors belonging to a MAPINFO/UDMF-hidden sector (`SECF_HIDDEN`/`SECMF_HIDDEN`) whenever `am_cheat == 0` (Zandronum `src/am_map.cpp:1935`; UZDoom `src/am_map.cpp:2092`). UZDoom additionally re-applies that suppression for `am_cheat >= 4` (`src/am_map.cpp:2098-2101`) — an addition documented in that codebase's own inline comments as deliberately keeping MAPINFO-hidden sectors hidden at the higher cheat tiers even though ordinary unseen-architecture tinting is turned off there — and at exactly `am_cheat == 4` also skips the "unseen architecture" desaturation tint that other modes apply, drawing those subsectors in their true color instead (`src/am_map.cpp:2229-2230`). Zandronum has no equivalent — once `am_cheat != 0`, its `AM_drawSubsectors` draws every hidden sector unconditionally at every mode 1–6, with no special-casing at 4–6 and no true-color exception at 4. In short: on UZDoom, modes 4–6 hide *both* `ML_DONTDRAW` lines and MAPINFO-hidden sectors in textured automap view; on Zandronum they only hide the lines.

## Related cvars

- **`am_showkeys`** — whether keys are highlighted with symbols
- **`am_showthingsprites`** — sprite display options for revealed things
