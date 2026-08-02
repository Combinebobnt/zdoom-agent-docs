# ChangeSky

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki (`_intake/ChangeSky - ZDoom Wiki.html`, retrieved from `https://zdoom.org/w/index.php?title=ChangeSky&oldid=37572`), verified against the Zandronum source.

Compiler builtin (`PCD_CHANGESKY`; `zt-bcc/src/builtin.c` declares it `void ChangeSky(str sky1, str sky2)`, matching the wiki's signature exactly — no arg-count or type divergence).

## Behavior (`p_acs.cpp`, `case PCD_CHANGESKY`)

- Each of `sky1`/`sky2` is applied **independently and only if non-empty**: the engine checks
  `sky1name[0] != 0` / `sky2name[0] != 0` before touching that slot at all. Passing `""` for either
  argument is not "clear it" or "same as the other slot" — it's a genuine **no-op for that slot**,
  leaving whatever sky was previously set (MAPINFO default or an earlier `ChangeSky` call)
  completely untouched. The wiki's second example ("the second parameter is redundant here because
  the water will tile over whatever is chosen") is true for that example but for an unrelated
  reason (visual tiling), not because empty/matching second args are interchangeable at the engine
  level — don't pass `""` expecting a no-op-to-default; it's a no-op-to-*previous*.
- Both slots are stored via `strncpy(level.skypic1/skypic2, name, 8)` — **silently truncated to 8
  characters**, the classic Doom lump-name limit (`level.skypic1`/`skypic2` are `char[9]` per
  `g_level.h`). Not mentioned by the wiki. The 9th byte is never touched by this opcode; it stays
  `0` from level setup (`g_level.cpp:2104`), so the field is always still a valid C string even
  when the source name is 8+ chars — no overflow risk, just silent truncation.
- Texture resolution is `TexMan.GetTexture(name, FTexture::TEX_Wall, TEXMAN_Overridable |
  TEXMAN_ReturnFirst)`. `FTextureManager::GetTexture` unconditionally ORs in `TEXMAN_TryAny`
  internally (`texturemanager.cpp:318`), which is what actually makes the wiki's "any flat, pname,
  sprite, or internal graphic" claim true — confirmed, not just asserted by the wiki. `TEX_Wall` is
  only the *preferred* search type; `TryAny` falls through to every other usetype if no wall
  texture matches that name.
- **An unresolvable texture name is not a script error** — `GetTexture` prints a console line
  (`"Unknown texture: \"%s\"\n"`) and substitutes the engine's built-in default texture, but the
  call still returns normally and `level.skypic1`/`skypic2` (the *string* field, used for
  save-game/re-lookup and for the client-sync diff below) is still updated to the bogus name
  regardless of whether the texture itself resolved. Undocumented by the wiki.
- Always calls `R_InitSkyMap()` after applying both slots, then unconditionally
  `sp -= 2` (pops both string args — a `void` builtin, no return value pushed, matching the
  declared signature).
- **Zandronum-only netcode, absent from the ZDoom wiki page (which predates any client/server
  split):** if the caller is the server, `SERVERCOMMANDS_SetMapSky()` broadcasts the new
  `skypic1`/`skypic2` to every connected client (`ulPlayerExtra` defaults to `MAXPLAYERS` =
  broadcast, no `SVCF_ONLYTHISCLIENT`). A **late-joining client is also correctly caught up**:
  `sv_main.cpp:3001-3008` diffs the live `level.skypic1`/`skypic2` against the MAPINFO-declared
  `level.info->skypic1`/`skypic2` on connect and unicasts `SetMapSky` only if they differ — so a
  `ChangeSky` call made before a player joins is not lost, unlike some other per-script transient
  state in this fork.

## See also

- `SetSkyScrollSpeed` (wiki's own cross-reference; not yet documented in this tree).
