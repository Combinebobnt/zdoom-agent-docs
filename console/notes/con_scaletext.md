# `con_scaletext` (console cvar)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-16); Zandronum 3.2.1 @28f736fb3 (2026-08-02)
**Provenance:** ZDoom Wiki `CVARs:Messages` (retrieved 2026-08-02, https://zdoom.org/w/index.php?title=CVARs%3AMessages&oldid=48195) + verified against Zandronum source's `src/c_console.cpp:195`, `src/g_shared/shared_sbar.cpp:1456-1474`, and `src/c_console.cpp:1323`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

## Engine-family divergence: Zandronum uses Bool, GZDoom-family uses Int

**In Zandronum:** this cvar is a boolean (0 or 1 only). The Zandronum source declares it as `CUSTOM_CVAR(Bool, con_scaletext, 0, CVAR_ARCHIVE)`. The wiki page describes behavior for ZDoom/GZDoom-family (values 0–3, corresponding to no scaling, 1×, 2×, and 4× scaling) which does not apply to Zandronum's binary implementation.

**In UZDoom/GZDoom-family:** this cvar is an integer accepting values 0–3. The UZDoom source declares it as `CUSTOM_CVAR(Int, con_scaletext, 0, CVAR_ARCHIVE)`.

The Zandronum source contains a comment indicating this change: `// [BC] con_scaletext is back to being a bool.` Examine switch statements in the Zandronum codebase (e.g. `src/g_shared/shared_sbar.cpp`) for remnants of the previous multi-value design — the switch includes a commented `case 2:` noting "Zandronum doesn't support this", showing the code was originally structured for the GZDoom-family behavior before being simplified to a boolean toggle.

**Practical impact:** On Zandronum, `con_scaletext 1` enables text scaling at high resolutions; `con_scaletext 0` disables it. The 2× and 4× options described in the wiki do not exist. If a `con_scaletext` value greater than 1 is set, it will be treated as 1 (true).

## Engine-family divergence: UZDoom's actual range and scaling formula differ from the wiki's 0–3 description

The prose above (following the ZDoom Wiki's description of GZDoom-family behavior) states that GZDoom-family engines accept values 0–3 corresponding to no scaling / 1x / 2x / 4x. Verification against the current UZDoom source shows this does not hold: the cvar's callback only clamps negative input up to 0, with no upper bound enforced by the cvar itself. The options menu's scale slider for this setting allows 0 through 8 in steps of 1, and that is only a UI convenience — larger values can still be set from the console and remain meaningful.

The scaling arithmetic is also not a discrete no-scale/1x/2x/4x enum. Depending on which console/notify font is active, the raw cvar value is used either directly as an integer multiplier, or roughly halved (via a `(value+1)/2`-style computation, since the alternate font is drawn at double resolution) before being applied. In both cases the resulting multiplier is separately capped so it can never exceed what the current screen resolution can display, but that cap is derived from screen size at draw time, not from any fixed maximum on the cvar's stored value.

**Practical impact:** on UZDoom, values above 3 are legal and produce progressively larger scaling (e.g. 5 or 6 scale text more than 3 does, up to the screen-size cap), unlike the fixed no-scaling/1x/2x/4x set the wiki describes.

## Related cvars

- `con_virtualwidth` / `con_virtualheight` — virtual screen dimensions when text scaling is enabled
- `con_scaletext_usescreenratio` — aspect ratio preservation during scaling
