# `void ChangeFloor(int tag, str flatname)`

Changes the floor texture of every sector matching `tag` to `flatname`. Compiler builtin
(`PCD_CHANGEFLOOR`, `zt-bcc/src/builtin.c` `g_funcs[]` entry `"changefloor"`), semantics in
the Zandronum source's `src/p_acs.cpp` (`case PCD_CHANGEFLOOR:`, line 10565, calling
`DLevelScript::ChangeFlat`, line 3990).

**Bucket:** compiler builtin.

- `tag` — a normal sector tag; every sector currently matching it (via `P_FindSectorFromTag`,
  looped until no more matches) gets its floor changed. Zero or more sectors, no error if none
  match.
- `flatname` — looked up with `TexMan.GetTexture(flatname, FTexture::TEX_Flat,
  TEXMAN_Overridable)` (`p_acs.cpp:3999`). The call site itself only passes `TEXMAN_Overridable`;
  `FTextureManager::GetTexture` (`textures/texturemanager.cpp:308-311`) unconditionally ORs in
  `TEXMAN_TryAny` before delegating to `CheckForTexture`, regardless of what the caller passed —
  that's the actual source of the wiki's "you may also use any texture, pname, sprite, or internal
  graphic (e.g. TITLEPIC)" claim holding true in this fork too; the lookup isn't restricted to the
  flat namespace no matter which caller-supplied flags omit `TryAny`.
- **Unknown/unresolvable name does not silently no-op and does not abort the script** — if
  `flatname` is a non-empty string that doesn't resolve to any texture at all, `GetTexture`
  (`textures/texturemanager.cpp:317-322`) logs `Unknown texture: "<name>"` to console and
  substitutes the engine's built-in default texture, which then gets applied to every matching
  sector's floor. So a typo'd flat name is visible as a console message plus a visibly wrong floor
  texture, not a thrown error and not a no-op.
- **A resolved empty string is a distinct, more dangerous case, undocumented by the wiki.**
  `GetTexture` special-cases `name[0] == 0` (`texturemanager.cpp:308-311`) and returns
  `FTextureID(0)` directly — the engine's reserved "no texture" sentinel — *before* the
  unknown-name path runs, so there's no console warning at all. `ChangeFloor(tag, "")` silently
  repaints every matching sector's floor with the "no texture" dummy (same failure mode
  documented for [ReplaceTextures](replacetextures.md)'s `newtexturename`/blank-wall case).
  This differs from the *invalid string index* case below, which never reaches `GetTexture` at
  all.
- **A bad string index, as opposed to a bad string value, *is* a silent no-op.** `flatname` is
  resolved server-side via `FBehavior::StaticLookupString(name)`; if that returns `NULL` (invalid
  string index — shouldn't happen from normal BCS string-literal usage, but is reachable if
  `name` comes from adversarial input such as a raw string-table index), `ChangeFlat` returns
  immediately before touching any sector (`p_acs.cpp:3996-3997`) — no console message, no texture
  change, no sector touched at all. This is a different failure mode from the "known bad name"
  case above.
- **Zandronum-specific netcode addition not in the ZDoom wiki source:** on a network server
  (`NETWORK_GetState() == NETSTATE_SERVER`), every matched sector triggers
  `SERVERCOMMANDS_SetSectorFlat(secnum)` (`p_acs.cpp:4007-4008`) to sync the change to clients.
  This command (`sv_commands.cpp:3125`) sends **both** the sector's current floor and ceiling
  flat names to clients in one message, regardless of which one this call actually changed — so
  calling `ChangeFloor` also happens to re-sync the ceiling flat (and vice versa for
  `ChangeCeiling`), which is harmless but explains why you won't see a client desync even if only
  one of the pair is ever driven from ACS. Callers don't need to do anything extra for the change
  to reach clients.
- Each affected sector also gets `sectors[secnum].bFlatChange = true` set (`p_acs.cpp:4011`),
  an internal bookkeeping flag (e.g. for save-game serialization of dynamically-changed flats);
  not something ACS/BCS code can read back.
- The wiki's power-of-2-dimensions caveat ("only graphics whose dimensions are powers of 2 ...
  will display correctly") is a general classic-renderer flat-wrapping quirk, not something
  specific to this function's own code path — not independently re-verified here against this
  fork's renderer, so treat it as plausible but unconfirmed for Zandronum's software/hardware
  renderers specifically.

**Example (wiki's, unchanged — argument order and behavior both check out):**

```
script "Drain_Waterfall" (void)
{
    ChangeFloor(4, "RROCK13");
}
```

**Provenance:** wiki page `ChangeFloor - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`oldid=36010`) + source-verified against the Zandronum source (`p_acs.cpp:3990-4013,10565-10568`,
`textures/texturemanager.cpp:308-328`, `sv_commands.cpp:3125-3135`) and
`zt-bcc/src/builtin.c:41,189`. The wiki's signature, tag/flatname semantics, and
any-texture-namespace claim all hold exactly against this fork's source; the unknown-name
fallback-texture behavior, the string-index-`NULL` silent no-op, the Zandronum netcode sync (and
its floor+ceiling coupling), and the `bFlatChange` bookkeeping flag are this doc's
source-verified additions, not mentioned on the ZDoom wiki page.
**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.
