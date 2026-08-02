# `con_scaletext` (console cvar)

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `CVARs:Messages` (retrieved 2026-08-02, oldid=48195) + verified against Zandronum source's `src/c_console.cpp:195`, `src/g_shared/shared_sbar.cpp:1456-1474`, and `src/c_console.cpp:1323`.

## Engine divergence: Zandronum uses Bool, GZDoom-family uses Int

**In Zandronum:** this cvar is a boolean (0 or 1 only). The Zandronum source declares it as `CUSTOM_CVAR(Bool, con_scaletext, 0, CVAR_ARCHIVE)`. The wiki page describes behavior for ZDoom/GZDoom-family (values 0–3, corresponding to no scaling, 1×, 2×, and 4× scaling) which does not apply to Zandronum's binary implementation.

**In UZDoom/GZDoom-family:** this cvar is an integer accepting values 0–3. The UZDoom source declares it as `CUSTOM_CVAR(Int, con_scaletext, 0, CVAR_ARCHIVE)`.

The Zandronum source contains a comment indicating this change: `// [BC] con_scaletext is back to being a bool.` Examine switch statements in the Zandronum codebase (e.g. `src/g_shared/shared_sbar.cpp`) for remnants of the previous multi-value design — the switch includes a commented `case 2:` noting "Zandronum doesn't support this", showing the code was originally structured for the GZDoom-family behavior before being simplified to a boolean toggle.

**Practical impact:** On Zandronum, `con_scaletext 1` enables text scaling at high resolutions; `con_scaletext 0` disables it. The 2× and 4× options described in the wiki do not exist. If a `con_scaletext` value greater than 1 is set, it will be treated as 1 (true).

## Related cvars

- `con_virtualwidth` / `con_virtualheight` — virtual screen dimensions when text scaling is enabled
- `con_scaletext_usescreenratio` — aspect ratio preservation during scaling
