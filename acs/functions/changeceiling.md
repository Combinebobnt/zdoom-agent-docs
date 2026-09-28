# `void ChangeCeiling(int tag, str flatname)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** wiki page `ChangeCeiling - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`https://zdoom.org/w/index.php?title=ChangeCeiling&oldid=27562`) + source-verified against the Zandronum source (`p_acs.cpp:3990-4013,10575-10583`,
`textures/texturemanager.cpp:308-328`, `sv_main.cpp:3494-3495`,
`g_game.cpp:3665-3672`) and `zt-bcc/src/builtin.c:42`. The wiki's signature,
tag/flatname semantics, and any-texture-namespace claim all hold exactly against Zandronum's
source; the unknown-name fallback-texture behavior, the string-index-`NULL` silent no-op, the
`TEXMAN_TryAny`-is-forced-by-`GetTexture`-not-by-the-call-site mechanism, the Zandronum netcode
sync (and its floor+ceiling coupling), and the `bFlatChange` bookkeeping flag are this doc's
source-verified additions, not mentioned on the ZDoom wiki page.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.

Changes the ceiling texture of every sector matching `tag` to `flatname`. Compiler builtin
(`PCD_CHANGECEILING`, `zt-bcc/src/builtin.c` `g_funcs[]` entry `"changeceiling"`), semantics in
the Zandronum source's `src/p_acs.cpp` (`case PCD_CHANGECEILING:`, line 10575, calling
`DLevelScript::ChangeFlat`, line 3990). `ChangeCeiling` is `ChangeFloor`'s direct sibling —
both compile to the exact same `ChangeFlat(tag, name, floorOrCeiling)` engine function, differing
only in the `floorOrCeiling` argument (`1` for `ChangeCeiling` vs `0` for `ChangeFloor`,
`p_acs.cpp:10566` vs `10576`).

- `tag` — a normal sector tag; every sector currently matching it (via `P_FindSectorFromTag`,
  looped until no more matches) gets its ceiling changed. Zero or more sectors, no error if none
  match.
- `flatname` — looked up with `TexMan.GetTexture(flatname, FTexture::TEX_Flat,
  FTextureManager::TEXMAN_Overridable)` (`p_acs.cpp:3999`) — note the call site itself passes
  only `TEXMAN_Overridable`, *not* `TEXMAN_TryAny`. However `FTextureManager::GetTexture`
  unconditionally ORs `TEXMAN_TryAny` into the flags it forwards to `CheckForTexture`
  (`textures/texturemanager.cpp:318`, `i = CheckForTexture(name, usetype, flags | TEXMAN_TryAny)`)
  regardless of what the caller passed. So the wiki's "you may also use any texture, pname,
  sprite, or internal graphic (e.g. TITLEPIC)" claim still holds in the Zandronum engine fork, but the mechanism
  is `GetTexture`'s own unconditional behavior, not an explicit `TEXMAN_TryAny` at the
  `ChangeFlat` call site.
- **Unknown/unresolvable name does not silently no-op and does not abort the script** — if
  `flatname` doesn't resolve to any texture at all, `FTextureManager::GetTexture`
  (`textures/texturemanager.cpp:321-326`) logs `Unknown texture: "<name>"` to console and
  substitutes the engine's default texture (`-NOFLAT-`, `texturemanager.cpp:988`), which then gets applied to every matching
  sector's ceiling. A typo'd flat name is visible as a console message plus a visibly wrong
  ceiling texture, not a thrown error and not a no-op.
- **A resolved empty string is a distinct, more dangerous case, undocumented by the wiki.**
  `GetTexture` special-cases `name[0] == 0` (`texturemanager.cpp:312-315`) and returns
  `FTextureID(0)` directly — the engine's reserved "no texture" sentinel — *before* the
  unknown-name path runs, so there's no console warning at all. `ChangeCeiling(tag, "")` silently
  repaints every matching sector's ceiling with the "no texture" dummy (same failure mode
  documented for [ReplaceTextures](replacetextures.md)'s `newtexturename`/blank-wall case and for
  [ChangeFloor](changefloor.md)). This differs from the *invalid string index* case below, which
  never reaches `GetTexture` at all.
- **A bad string index, as opposed to a bad string value, *is* a silent no-op.** `flatname` is
  resolved via `FBehavior::StaticLookupString(name)`; if that returns `NULL` (invalid
  string index — shouldn't happen from normal BCS string-literal usage, but is reachable if
  `name` comes from adversarial input such as a raw string-table index), `ChangeFlat` returns
  immediately before touching any sector (`p_acs.cpp:3996-3997`) — no console message, no texture
  change, no sector touched at all.
- **Zandronum-specific netcode addition not in the ZDoom wiki source:** on a network server
  (`NETWORK_GetState() == NETSTATE_SERVER`), every matched sector triggers
  `SERVERCOMMANDS_SetSectorFlat(secnum)` (`p_acs.cpp:4007-4008`) to sync the change to clients.
  This command sends **both** the sector's current floor and ceiling flat names to clients in one
  message, regardless of which one this call actually changed. So calling `ChangeCeiling` also
  re-sends the sector's current floor flat (and vice versa for `ChangeFloor`), which is harmless.
  Callers don't need to do anything extra for the change to reach clients. Offline, and when a
  client runs the call itself (e.g. from a `CLIENTSIDE` script), the change applies locally only.
- Each affected sector also gets `sectors[secnum].bFlatChange = true` set (`p_acs.cpp:4011`).
  ACS/BCS code can't read it back, but it has two visible effects on Zandronum. A client that
  connects later is sent `SetSectorFlat` for every sector carrying the flag
  (`SERVER_UpdateSectors`, `sv_main.cpp:3494-3495`), so late joiners see the changed ceiling.
  And `GAME_ResetMap` (the round reset used by e.g. Last Man Standing, Survival, Duel and
  Invasion) restores both of the sector's flats to their map-load values and clears the flag
  (`g_game.cpp:3665-3672`), so the change does not survive a round reset. The flag is also
  saved in savegames (`p_saveg.cpp:455`).
- The wiki's power-of-2-dimensions caveat ("only graphics whose dimensions are powers of 2 ...
  will display correctly") is a general classic-renderer flat-wrapping quirk, not something
  specific to this function's own code path — not independently re-verified here against
  Zandronum's renderer, so treat it as plausible but unconfirmed for Zandronum's software/hardware
  renderers specifically.

## Engine-family divergence: `bFlatChange` bookkeeping flag

UZDoom's equivalent code path (`DLevelScript::ChangeFlat`, `src/playsim/p_acs.cpp`, calling
`sector_t::SetTexture`, `src/gamedata/r_defs.h`) has no equivalent of Zandronum's
`sectors[secnum].bFlatChange` flag — `SetTexture` only stores the new `FTextureID` (and, for the
floor plane specifically, adjusts floor clipping); it sets no dirty/change-tracking bit at all.
ACS/BCS code can't read `bFlatChange` on either engine. On Zandronum the flag drives the
late-joiner sync and the `GAME_ResetMap` round-reset revert described above; both are
Zandronum-only mechanisms. The
Zandronum-specific netcode paragraph above (`SERVERCOMMANDS_SetSectorFlat`)
is a separate, already-labeled Zandronum-only mechanism — UZDoom's GZDoom-family networking model
has no equivalent client-server sync command to trigger here at all.

**Example (wiki's, unchanged — argument order and behavior both check out):**

```text
script "Example" (void)
{
    ChangeCeiling(4, "RROCK13");
}
```
