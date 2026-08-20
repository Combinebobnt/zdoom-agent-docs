# ChangeSky

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** ZDoom Wiki (`_intake/ChangeSky - ZDoom Wiki.html`, retrieved from `https://zdoom.org/w/index.php?title=ChangeSky&oldid=37572`), verified against the Zandronum source.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

Compiler builtin (`PCD_CHANGESKY`; `zt-bcc/src/builtin.c` declares it `void ChangeSky(str sky1, str sky2)`,
matching the wiki's signature exactly — no arg-count or type divergence). The opcode itself is a base
Hexen-era ACS instruction implemented by both engines' VMs — Zandronum `src/p_acs.cpp`, UZDoom
`src/playsim/p_acs.cpp` — with the storage/sync differences described below.

## Behavior (`case PCD_CHANGESKY`)

- Each of `sky1`/`sky2` is applied **independently and only if non-empty**: the engine checks
  `sky1name[0] != 0` / `sky2name[0] != 0` before touching that slot at all. Passing `""` for either
  argument is not "clear it" or "same as the other slot" — it's a genuine **no-op for that slot**,
  leaving whatever sky was previously set (MAPINFO default or an earlier `ChangeSky` call)
  completely untouched. The wiki's second example ("the second parameter is redundant here because
  the water will tile over whatever is chosen") is true for that example but for an unrelated
  reason (visual tiling), not because empty/matching second args are interchangeable at the engine
  level — don't pass `""` expecting a no-op-to-default; it's a no-op-to-*previous*. UZDoom's ACS VM
  performs the identical non-empty check before touching either slot (`src/playsim/p_acs.cpp:9966,
  9970`) — clean agreement.
- Both slots are stored via `strncpy(level.skypic1/skypic2, name, 8)` — **silently truncated to 8
  characters**, the classic Doom lump-name limit (`level.skypic1`/`skypic2` are `char[9]` per
  `g_level.h`). Not mentioned by the wiki. The 9th byte is never touched by this opcode; it stays
  `0` from level setup (`g_level.cpp:2104`), so the field is always still a valid C string even
  when the source name is 8+ chars — no overflow risk, just silent truncation. **This whole
  string-storage mechanism is Zandronum-specific — UZDoom has no equivalent field at all; see the
  divergence section below.**
- Texture resolution is `TexMan.GetTexture(name, FTexture::TEX_Wall, TEXMAN_Overridable |
  TEXMAN_ReturnFirst)`. `FTextureManager::GetTexture` unconditionally ORs in `TEXMAN_TryAny`
  internally (`texturemanager.cpp:318`), which is what actually makes the wiki's "any flat, pname,
  sprite, or internal graphic" claim true — confirmed, not just asserted by the wiki. `TEX_Wall` is
  only the *preferred* search type; `TryAny` falls through to every other usetype if no wall
  texture matches that name. UZDoom's renamed `TexMan.GetTextureID(...)` does the same unconditional
  `TEXMAN_TryAny` OR before resolving (`src/common/textures/texturemanager.cpp:327-347`) — same
  fallback behavior under a new name; see the divergence section below for why the name changed.
- **An unresolvable texture name is not a script error** — `GetTexture` prints a console line
  (`"Unknown texture: \"%s\"\n"`) and substitutes the engine's built-in default texture, but the
  call still returns normally and `level.skypic1`/`skypic2` (the *string* field, used for
  save-game/re-lookup and for the client-sync diff below) is still updated to the bogus name
  regardless of whether the texture itself resolved. Undocumented by the wiki. The "prints a
  console line and substitutes the default texture, call still returns normally" part is identical
  on UZDoom (`FTextureManager::GetTextureID`, same file/lines as above); the "string field keeps the
  bogus name" part is Zandronum-only — UZDoom has no string field to hold a bogus value in the first
  place, see below.
- Always calls `R_InitSkyMap()` after applying both slots, then unconditionally
  `sp -= 2` (pops both string args — a `void` builtin, no return value pushed, matching the
  declared signature). `sp -= 2` is identical on UZDoom; which `InitSkyMap` variant gets called
  differs — see the divergence section below.
- **Zandronum-only netcode, absent from the ZDoom wiki page (which predates any client/server
  split):** if the caller is the server, `SERVERCOMMANDS_SetMapSky()` broadcasts the new
  `skypic1`/`skypic2` to every connected client (`ulPlayerExtra` defaults to `MAXPLAYERS` =
  broadcast, no `SVCF_ONLYTHISCLIENT`). A **late-joining client is also correctly caught up**:
  `sv_main.cpp:3001-3008` diffs the live `level.skypic1`/`skypic2` against the MAPINFO-declared
  `level.info->skypic1`/`skypic2` on connect and unicasts `SetMapSky` only if they differ — so a
  `ChangeSky` call made before a player joins is not lost, unlike some other per-script transient
  state in Zandronum. This entire mechanism has no UZDoom counterpart — see the divergence section
  below for why.

## Engine-family divergence: sky state storage and multiplayer sync

- **Storage.** Zandronum keeps two representations in parallel: a truncated-to-8-char name string
  (`level.skypic1`/`skypic2`, `char[9]`, set via the `strncpy` above) that persists across
  `ChangeSky` calls independent of texture-resolution success, and a separately-resolved texture
  handle (`sky1texture`/`sky2texture`) that the renderer actually uses. UZDoom's `FLevelLocals`
  collapses this to a single `FTextureID skytexture1`/`skytexture2` pair
  (`src/g_levellocals.h:678-679`); `ChangeSky` (`src/playsim/p_acs.cpp:9960-9977`) sets only that
  resolved ID via `TexMan.GetTextureID(...)`, with **no persisted name string at all**. Two
  consequences follow: no 8-character truncation exists on UZDoom (the full name is used for the
  lookup and nothing is stored back as a fixed-length string), and on an unresolvable name
  UZDoom's `skytexture1`/`skytexture2` ends up holding the *actual fallback texture's ID*
  (`FTextureManager::DefaultTexture`, set at `src/common/textures/texturemanager.cpp:340-345`),
  not "the bogus name" the way Zandronum's string field is — there's no string field to hold a
  bogus value in the first place.
- **`TexMan.GetTexture` → `TexMan.GetTextureID`: renamed, not rebehaved.** The rename tracks
  UZDoom's `FTextureID`-based texture-manager rewrite, not a semantic change: `GetTextureID`
  (`src/common/textures/texturemanager.cpp:327-347`) still unconditionally ORs in `TEXMAN_TryAny`
  before calling `CheckForTexture`, and still prints the identical `"Unknown texture: \"%s\"\n"`
  line and substitutes the default texture on failure.
- **`R_InitSkyMap` split into per-level and all-levels variants.** `ChangeSky` on UZDoom calls
  `InitSkyMap(Level)` (`src/rendering/r_sky.cpp:57-111`), the single-level form, not the
  argument-less `R_InitSkyMap()` that loops every loaded level (`src/rendering/r_sky.cpp:113-119`,
  used at engine startup and by the `r_skymode` cvar callback). Zandronum has no multi-level
  concept and only one global `R_InitSkyMap()` (`src/r_sky.cpp:67`), so this split doesn't exist
  there. Functionally, the call still only ever affects the level `ChangeSky` ran in on either
  engine. Incidentally, the two engines' double-sky-height-mismatch fallback (triggered separately,
  only when `LEVEL_DOUBLESKY` is set and the two sky textures' heights don't match) assigns in
  opposite directions — Zandronum sets `sky2texture = sky1texture` (`src/r_sky.cpp:81`); UZDoom
  sets `Level->skytexture1 = Level->skytexture2` (`src/rendering/r_sky.cpp:89`) — not something a
  `ChangeSky` caller can observe unless it also relies on that specific fallback.
- **No `SERVERCOMMANDS_*`-style server-authoritative sky broadcast or late-join catch-up was found
  on UZDoom.** No `SERVERCOMMANDS_SetMapSky`-equivalent or any `SERVERCOMMANDS_*` name exists
  anywhere in the checkout (grepped tree-wide) — UZDoom is not architected around Zandronum's
  server-authoritative-state-push model for this kind of data. It does still have its own
  client/server vocabulary for connection bookkeeping (e.g. host/client ack tracking,
  `src/d_net.cpp:1037`), but nothing playing the role Zandronum's `SetMapSky` broadcast plays.
  Consistent with that, UZDoom runs a ticcmd-lockstep peer model where every peer executes the same
  ACS VM from the same synced input, and code elsewhere explicitly guards against **desync**, the
  lockstep failure mode (e.g. `src/p_tick.cpp:49`, `src/d_net.cpp:1001`) — a `ChangeSky` call inside
  a script reaches every peer as part of already-synced game state without needing its own explicit
  sync message, unlike Zandronum's server-push model. Whether a UZDoom game can be joined after
  start at all wasn't traced beyond a narrow grep (`src/*.cpp src/*/*.cpp`, not exhaustive — it
  doesn't reach `src/common/**` or `src/rendering/*/*.cpp`) turning up no `latejoin`-named code; if
  a late-join path exists deeper in the tree, the specific catch-up mechanics for sky state on it
  are untraced, not confirmed absent.

## See also

- `SetSkyScrollSpeed` (wiki's own cross-reference; not yet documented in this tree).
