# SetMusic

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki ("SetMusic"), verified against Zandronum 3.2.1 source (s_sound.cpp, p_acs.cpp)
**Bucket:** Compiler builtin

---

```c
void SetMusic(str song [, int order [, int unused]]);
```

Changes the music playing in the current map. The music change is broadcast to all clients if this is a network game.

## Parameters

**`song`** — A music lump name or path.

- To restore the level's default music (from MAPINFO), pass `"*"`. The `order` parameter is ignored and replaced with the level's configured `musicorder` in this case.
- To play a lump from the IWAD or a PK3, use its lump name (e.g., `"D_RUNNIN"`).
- A path containing `/` is treated as a relative path within the PK3, including the `music/` prefix and file extension (e.g., `"music/custom.ogg"`); lump names may exceed 8 characters when specified this way. *(Carried from ZDoom wiki; PK3 path resolution not traced in this fork.)*
- A prefix of `$` (e.g., `"$MUSIC_BOSS"`) triggers DEH-style string replacement using the GStrings table, with `D_` prepended to the looked-up name.
- An empty string or NULL stops music.

**`order`** — Subsong or track index for multi-track or tracker-module music (e.g., MOD).

- If `song` is `"*"`, this parameter is ignored and replaced with the level's configured `musicorder`.
- If the music format doesn't support subsongs (e.g., MP3), this has no effect.
- If already playing the same music, a non-zero `order` will attempt to seek to that subsong via `SetSubsong()`. It does not restart the track.
- Ignored if an active playlist is present or `snd_lockmusic` cvar is enabled.
- Default: `0` (first subsong/track).

**`unused`** — Third parameter. Present in the signature but not used by the engine. It is popped from the stack at runtime but ignored. Omit it (or pass any value).

## Behavior

### Failure and no-op cases

- **Server context:** In a network game, if this function is called by a script running on the server, the music change is broadcast to all clients via the netcode (`SERVERCOMMANDS_SetMapMusic` and `SERVER_SetMapMusic` — the latter also persists the change for late-joining clients), but the server process itself returns immediately without playing music. Only clients hear the change.
- **Locked music:** If the `snd_lockmusic` cvar is enabled, or a playlist is currently active, the call has no effect (silent no-op; the music does not change).
- **No error return in ACS:** `S_ChangeMusic()` returns `bool` at the C++ level, indicating success or failure. However, `PCD_SETMUSIC` discards the return value. **An ACS script cannot detect whether the music change was ignored or failed**; calling this function is always a `void` operation from the perspective of the script.

### Overwriting order with "*"

If `song` is the literal string `"*"`, the `order` value passed to this function is **not used**. Instead, the function overwrites it with `level.musicorder` (the default track index for the current map). This is documented in the wiki but worth emphasizing: passing a non-zero `order` together with `"*"` does not skip ahead within the default music — it uses the level's configured default track.

### LocalSetMusic vs. SetMusic

A companion function `LocalSetMusic` exists, which changes music only for the player running the activating script (with `SVCF_ONLYTHISCLIENT` flag in netcode). Unlike `SetMusic`, `LocalSetMusic` does **not** call `SERVER_SetMapMusic`, so the change is not persisted for late joiners.

## Example

```c
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
