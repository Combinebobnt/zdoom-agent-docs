# `GetScreenHeight`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-07)
**Provenance:** ZDoom Wiki `GetScreenHeight` (https://zdoom.org/w/index.php?title=GetScreenHeight&oldid=37389, retrieved 2026-08-07) + original source-verified on 2026-08-05 against the Zandronum source's `src/p_acs.cpp:12446-12468` (PCD_GETSCREENHEIGHT case handler) and the UZDoom source's `src/playsim/p_acs.cpp:9889-9892` (same case handler). Re-verified against wiki 2026-08-07.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin — `zt-bcc/src/builtin.c:114` (`{ "getscreenheight", "i" }`, zero-arg, returns `int`), compiles to `PCD_GETSCREENHEIGHT`. Not a `zcommon.bcs` `special`-table entry.

Documented together with [`GetScreenWidth`](getscreenwidth.md) — identical handler shape on both engines (`PCD_GETSCREENHEIGHT` mirrors `PCD_GETSCREENWIDTH` byte-for-byte, substituting `CLIENT_s::ScreenHeight`/`SCREENHEIGHT` for `ScreenWidth`/`SCREENWIDTH`), same tier/engine/provenance, same practical consequence (works from a non-`CLIENTSIDE`, server-executed script with a player activator on Zandronum; always the local screen on UZDoom). See that file for the full writeup.

The same wiki-vs-fork divergence applies: Zandronum can query a specific player's real resolution via `SERVER_GetClient(...)->ScreenHeight`, contrary to the ZDoom wiki's statement that per-player resolution info "does not exist" in multiplayer.
