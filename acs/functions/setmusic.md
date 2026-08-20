# SetMusic

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-06)
**Provenance:** ZDoom Wiki `SetMusic` (retrieved 2026-08-06, https://zdoom.org/w/index.php?title=SetMusic&oldid=38157) + verified against
the Zandronum source's `src/p_acs.cpp:11881-11893` (modified by ZandronumMCP patch) and `src/s_sound.cpp:2572-2770`, `src/cl_main.cpp:7534-7537`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Compiler builtin

---

```acs
void SetMusic(str song [, int order [, int unused]]);
```

Changes the music playing in the current map. The music change is broadcast to all clients if this is a network game.

## Parameters

**`song`** — A music lump name, path, or special marker.

- `"*"` — Restore the level's default music from MAPINFO. The `order` parameter is ignored and replaced with the level's configured `musicorder` in this case.
- A lump name (e.g., `"D_RUNNIN"`). Looked up first in the WAD's music namespace; if not found, checked as a filename on disk. See "Wiki-vs-source drift" below for lump-lookup precedence changes.
- A path containing `/` (e.g., `"music/custom.ogg"`). Treated as a relative path within the PK3 file or as a filesystem path; file extension required.
- A `$` prefix (e.g., `"$MUSIC_BOSS"`) triggers DEH-style string replacement via the GStrings table, with `D_` prepended to the looked-up name (e.g., `$MUSIC_BOSS` becomes `GStrings["MUSIC_BOSS"]` with `D_` prepended).
- `,CD,<track>[,<id>]` format — Play a CD audio track. `track` is a 0-based track number; `id` is an optional CD identifier (hexadecimal). Example: `",CD,2"` plays track 2.
- `file://...` prefix — Stripped before resolution (e.g., `"file:///path/to/song.ogg"` becomes `"/path/to/song.ogg"`).
- URLs (strings containing `://` after the first `/`) — passed to `I_RegisterURLSong()` for streaming (e.g., `"https://example.com/music.ogg"`). Requires network support; returns false on error.
- **Music alias lookup** (Zandronum-specific). Before checking the filesystem/WAD, the name is looked up in the `MusicAliases` table. If found and maps to `NAME_None`, the call silently succeeds without playing anything. Otherwise, plays the aliased name. This allows aliasing one music name to another, or to nothing.
- An empty string or NULL stops music (returns true, same as a successful unload).

**`order`** — Subsong or track index for multi-track or tracker-module music (e.g., MOD).

- If `song` is `"*"`, this parameter is ignored and replaced with the level's configured `musicorder`.
- If the music format doesn't support subsongs (e.g., MP3), this has no effect.
- If already playing the same music with the same `looping` flag (see below), a non-zero `order` will attempt to seek to that subsong via `SetSubsong()` instead of reloading. It does not restart the track from the beginning.
- Ignored if an active playlist is present or `snd_lockmusic` cvar is enabled.
- Default: `0` (first subsong/track).

**`unused`** — Third parameter. Present in the signature but not used by the engine. It is popped from the stack at runtime but ignored. Omit it (or pass any value).

## Behavior

### Failure and no-op cases

- **Server context in a network game:** The ACS opcode unconditionally calls through to `S_ChangeMusic()`. However, `S_ChangeMusic()` checks `if (NETWORK_GetState() == NETSTATE_SERVER) return false;` at its start — so the server process itself never actually plays music. Additionally, the `PCD_SETMUSIC` opcode unconditionally broadcasts the change to all connected clients via `SERVERCOMMANDS_SetMapMusic()` and `SERVER_SetMapMusic()` (the latter persists the change for late-joining clients). So in a network game: the server route/broadcasts the command but produces no local audio; clients receive the command and play the music. A listen/host server (one that is both server and client) routes the broadcast to other clients and also receives/plays its own copy.
- **Locked music:** If the `snd_lockmusic` cvar is enabled, or a playlist is currently active, `S_ChangeMusic()` returns false early (line 2579-2582). The music does not change (silent no-op in ACS, since the return value is discarded).
- **Volume muted:** If `snd_musicvolume <= 0`, the function returns `true` (success) without registering a music handle or playing anything. The music name is recorded internally but no audio backend is invoked. The next volume increase will not automatically resume; another `SetMusic()` call is needed.
- **No error return in ACS:** `S_ChangeMusic()` returns `bool` at the C++ level, indicating success or failure. However, `PCD_SETMUSIC` discards the return value. **An ACS script cannot detect whether the music change was ignored or failed**; calling this function is always a `void` operation from the perspective of the script.

### Overwriting order with "*"

If `song` is the literal string `"*"`, the `order` value passed to this function is **not used**. Instead, the function overwrites it with `level.musicorder` (the default track index for the current map). This is documented in the wiki but worth emphasizing: passing a non-zero `order` together with `"*"` does not skip ahead within the default music — it uses the level's configured default track.

### Looping flag and the same-music fast path

`S_ChangeMusic()` has an internal default of `looping=true`. When the ACS opcode calls through with only two arguments (song name and order), this default is used. The same-music fast path (seeking via `SetSubsong()` instead of reloading) requires not only that the song name matches, but also that `mus_playing.handle->m_Looping == looping` (i.e., the looping flag matches). If a song was previously started with a different looping setting, a subsequent `SetMusic()` call with the same name will do a full reload instead of a fast seek, even if only the order changed. In practice this is rarely observed (most music is played looping), but can occur when music is set from menu code or other non-default contexts.

### LocalSetMusic vs. SetMusic

A companion function `LocalSetMusic` exists, which changes music only for the player running the activating script (with `SVCF_ONLYTHISCLIENT` flag in netcode). Unlike `SetMusic`, `LocalSetMusic` does **not** call `SERVER_SetMapMusic`, so the change is not persisted for late joiners.

## Wiki/engine divergence: additional `song` forms undocumented in the wiki

The ZDoom Wiki page (oldid=38157) documents the basic parameter semantics (`song` as a lump/path, `order` for subsongs, `unused` ignored) and the `"*"` restore behavior. However, several `song` parameter forms discovered in the Zandronum source are absent from the wiki:

- The `$` prefix (DEH-style string replacement) is mentioned but not in parameter detail.
- The `,CD,<track>[,id]` format for CD audio is not documented at all in the wiki.
- The `file://` prefix strip is not documented.
- URL streaming via `I_RegisterURLSong()` is not documented.
- The `MusicAliases` table lookup (Zandronum-specific) is not mentioned.

These are documented here based on Zandronum source `src/s_sound.cpp:2640-2695`. The wiki's PK3 path handling (`song` containing `/` uses full path including `music/` and extension) is accurately documented and verified.

## Engine-family divergence: CD tracks, URL streaming, and the lock/broadcast layer are Zandronum-only

- **No CD-track support.** UZDoom's engine-specific song-name lookup still recognizes the
  `,CD,<track>[,<id>]` prefix, but only to reject it: it prints a one-time console warning that CD
  audio is no longer supported and treats the request as an empty song name from that point on.
  Because an empty song name is what makes `SetMusic` stop the currently playing music (see the
  "empty string or NULL stops music" bullet above), passing a CD-format string to `SetMusic` on
  UZDoom silently stops whatever is playing instead of starting a CD track.
- **No URL streaming.** UZDoom has no engine hook comparable to what the Zandronum-side prose
  above describes for a `scheme://` string. A URL-shaped `song` argument isn't special-cased at
  all here — it just falls through to the ordinary lump/file lookup, which fails to find it (logged
  as "not found") rather than being handed off to a streaming backend.
- **No `snd_lockmusic` cvar.** That cvar does not exist on UZDoom. Of the two "Locked music"
  no-op conditions described above, only the active-playlist one still applies; there is no
  separate lock-music setting layered on top of it.
- **No server/broadcast layer at all.** UZDoom's networking model has no analogue of Zandronum's
  dedicated non-rendering server process: there is no check comparable to "is this the server"
  gating the underlying music-change call, and no broadcast/persist-for-late-joiners step wrapped
  around it. The ACS opcode calls straight into the engine's music-change routine with no
  networking logic of its own. Practically, the entire "Server context in a network game" behavior
  described above for Zandronum — a non-audio-producing server that routes and persists the change
  for clients — does not exist as a concept on UZDoom; every machine running the map executes the
  same script and changes its own music locally and independently.
- **Correction to the "(Zandronum-specific)" alias-table label above:** the music-alias lookup it
  describes is not actually unique to Zandronum. UZDoom resolves the same kind of alias table
  (populated from the same SNDINFO-style declarations) during its own song-name lookup, with
  identical "maps to nothing → silently succeed without playing anything" semantics. That label is
  left exactly as originally written per this sweep's editing rules, but the alias-lookup behavior
  itself should be read as shared across both engines, not Zandronum-only.

## Example

```acs
Script 100 OPEN
{
   SetMusic("D_BOSS", 0);  // Start BOSS music (first subsong)
   
   // Do boss-fight logic...
   
   SetMusic("*", 0);  // Restore map's default music
}

Script 101 (int bossTID)
{
   // For MOD files, seek to a specific order:
   SetMusic("D_CUSTOM_MOD", 5);  // Play CUSTOM_MOD, start at order 5
}
```

## Notes

- Unlike ZDoom, Zandronum's implementation of `SetMusic` is tightly integrated with the netcode layer, immediately relaying the change to all clients and persisting it for late joiners.
- The server process in a network game does not produce audio output; it only routes and persists client-facing changes.
- **Likely causes a small client-side hitch when the change lands.** `ServerCommands::SetMapMusic::Execute()` (`cl_main.cpp:7534`) calls `S_ChangeMusic()` directly and synchronously — there's no background/async loading path. Inside `S_ChangeMusic` (`s_sound.cpp:2572`), any lump that isn't a plain uncompressed file on disk is fully read and decompressed into a scratch buffer (`musiccache`, via `Wads.ReadLump`) before being handed to `I_RegisterSong()`, which itself parses/initializes the chosen music backend (tracker-module parsing, MIDI device setup, or codec init). All of this runs inline in whatever tic the client processes the network command, with no yielding back to the render/tic loop in between — so a large or compressed music lump can produce a noticeable frame stall right when the music change takes effect. This is a local decode/IO cost on the receiving client, not a symptom of network latency.
