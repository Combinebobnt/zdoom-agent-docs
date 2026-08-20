# `LevelLocals` struct

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki `Structs:LevelLocals` (retrieved 2026-08-03, https://zdoom.org/w/index.php?title=Structs%3ALevelLocals&oldid=55483) + verified against UZDoom stdlib (`wadsrc/static/zscript/doombase.zs:501-673`); re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — no behavioral drift found.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** ZScript stdlib (`doombase.zs:501-673`; struct and method declarations; native implementations in the UZDoom engine's level code).

The `LevelLocals` struct contains information and methods about the current level. All members are accessed through the global `level` variable. The struct provides both static methods (called via `LevelLocals` or `Level`, e.g., `LevelLocals.MakeScreenShot()`) and dynamic instance methods (called on the global `level` pointer, e.g., `Level.Vec3Diff(...)`).

## Static methods

Called via `LevelLocals` or `Level` name.

- `void MakeScreenShot()` — Takes a screenshot of the current game window.
- `void MakeAutoSave()` — Requests an autosave (sets `gameaction = ga_autosave`; the actual save
  happens on a later game-loop tic, via the same code path a manual save uses). Declared with no
  scope qualifier, so — unlike the `ui`-only `SavegameManager` API — this is callable from
  ordinary **play-scope** ZScript. The resulting save's description/filename are hardcoded, not
  parameterized by this call. See [Autosave and quicksave/quickload
  triggers](../concepts/autosave-triggers.md) for the full mechanism, the other two ways an
  autosave can fire, and the unified save path shared with manual saves.
- `bool IsPointInMap(vector3 p)` — **Deprecated as of 3.8; use `Level.IsPointInLevel(vector3 p)` instead.** Tests whether a point is within level boundaries.
- `static bool WorldPaused(bool checkLag = false)` — Returns true if the world/game is paused, optionally checking for lag-pauses. **UZDoom-specific extension.** Declared `static`, so it must be called via the `LevelLocals`/`Level` class name, not on the `level` instance pointer.

## Dynamic instance methods (called on `level` pointer)

### Geometry and coordinate transformation

These methods perform vector calculations accounting for portal transitions:

- `vector3 Vec3Diff(vector3 v1, vector3 v2)` — Computes the difference `v2 - v1`, accounting for portals.
- `vector2 Vec2Diff(vector2 v1, vector2 v2)` — Computes the 2D difference `v2 - v1` (XY only), accounting for portals.
- `vector3 Vec3Offset(vector3 pos, vector3 dir [, bool absolute = false])` — Applies an offset `dir` from position `pos`, accounting for portals. If `absolute` is true, offset is in absolute world space; otherwise it's in the local coordinate frame at `pos`.
- `vector2 Vec2Offset(vector2 pos, vector2 dir [, bool absolute = false])` — 2D version of `Vec3Offset` (XY only).
- `vector3 Vec2OffsetZ(vector2 pos, vector2 dir, double atz [, bool absolute = false])` — 2D offset with an explicit Z coordinate. Results in a 3D vector with Z = `atz`.
- `vector3 SphericalCoords(vector3 viewpoint, vector3 targetPos [, vector2 viewAngles = (0, 0)] [, bool absolute = false])` — Converts the displacement from `viewpoint` to `targetPos` into spherical coordinates (yaw, pitch, distance). Returns a vector where X = yaw angle, Y = pitch angle, Z = distance.
- `Vector2 GetDisplacement(int pg1, int pg2)` — Gets the displacement vector between two portal groups.

All geometry methods are `clearscope` and account for portal transitions to give correct results across portal boundaries.

### Point/line/box containment tests

- `clearscope bool IsPointInLevel(vector3 p)` — Returns true if the point `p` is within level boundaries, false if in the void.
- `clearscope Sector PointInSector(vector2 pt)` — Returns a pointer to the sector containing the 2D point `pt`.
- `clearscope int PointOnLineSide(Vector2 pos, Line l, bool precise = false)` — Returns which side of a linedef a point is on (0 or 1, with respect to the linedef's direction vector). If `precise` is true, performs more accurate calculations.
- `clearscope int ActorOnLineSide(Actor mo, Line l)` — Returns which side of a linedef an actor's center is on.
- `clearscope int BoxOnLineSide(Vector2 pos, double radius, Line l)` — Returns which side of a linedef a box (circle in 2D) is on, accounting for the box's radius.

### Level state and properties

- `int IsFrozen()` — Returns a positive value (1 or above) if the level is frozen, 0 if not.
- `void SetFrozen(bool on)` — Freezes the level if `on` is true, unfreezes it if false. **Divergence:** The ZDoom Wiki claims this method returns `bool`, but the actual implementation returns `void`.
- `bool IsJumpingAllowed()` — Returns true if jumping is allowed in the current level.
- `bool IsCrouchingAllowed()` — Returns true if crouching is allowed in the current level.
- `bool IsFreelookAllowed()` — Returns true if freelook is allowed in the current level.
- `string GetChecksum()` — Retrieves the MD5 checksum of the current map.

### Sky and lighting

- `void ChangeSky(TextureID sky1, TextureID sky2)` — Changes the two-layer sky, accepting ZScript TextureIDs. Similar to the ACS `ChangeSky` function but with type-safe texture references.
- `void ChangeSkyMist(TextureID skymist [, bool usemist = true] [, float skymistyscale = 1.0])` — Changes the skymist texture used for sky fog tinting. `usemist` enables/disables skymist rendering (true by default). `skymistyscale` (default 1.0, clamped 0.002–544.0) vertically scales the skymist texture about the zero-pitch horizon.
- `void SetSkyFog(int fogdensity)` — Sets the sky-specific fog density (1–255), separate from regular level fog.
- `void SetThickFog(float distance, float multiplier)` — Sets thick fog distance and multiplier for fog intensification beyond that distance. Pass a negative distance to disable thick fog. Regular fog density must be nonzero for the multiplier to take effect.
- `void ForceLightning(int mode = 0, sound tempSound = "")` — Forces a lightning strike with the given mode (same values as the `Light_ForceLightning` special). Optionally plays a custom sound for that strike instead of the map's default `LightningSound`.

### Iterators and searching

- `SectorTagIterator CreateSectorTagIterator(int tag, line defline = null)` — Creates an iterator to find all sectors with a given tag.
- `LineIdIterator CreateLineIdIterator(int tag)` — Creates an iterator to find all linedefs with a given linedef ID (tag).
- `ActorIterator CreateActorIterator(int tid, class<Actor> type = "Actor" [, bool clientSide = false])` — Creates an iterator to find actors by TID and optionally by actor class. **Divergence:** The wiki omits the `clientSide` parameter (UZDoom adds this). The `clientSide` parameter (default false) is a **UZDoom-specific extension** and may not exist in mainline GZDoom.

### Level flow and intermission

- `void ExitLevel(int position, bool keepFacing)` — Exits the level at the specified player start spot (`position`) in the next map defined in MAPINFO. If `keepFacing` is true, the player retains their facing direction.
- `void SecretExitLevel(int position)` — Exits to the secret map defined for the current map in MAPINFO, at the specified player start spot.
- `void ChangeLevel(string levelname, int position = 0, int flags = 0, int skill = -1)` — Changes to a given map (by lump name). Accepts position (player start spot), game flags, and optional skill level (–1 = keep current).
- `void GiveSecret(Actor activator, bool printmsg = true, bool playsound = true)` — Awards a secret to an actor. `printmsg` enables the "A secret is revealed!" message; `playsound` plays the secret sound.
- `void StartSlideshow(Name whichone)` — Starts a Strife-style slideshow by name.
- `void SetInterMusic(String nextmap)` — Overrides the map's intermission music with the music of another map (by lump name).
- `void StartIntermission(Name type, int state)` — Manually starts an intermission sequence of the given type.

### Texture and geometry replacement

- `void ReplaceTextures(String from, String to, int flags)` — Replaces all instances of a texture (by name) with another throughout the level. The `flags` parameter controls exceptions (e.g., excluding certain texture classes or linedef/sector types).

### Sector/line/actor spawning and manipulation

- `bool CreateCeiling(sector sec, int type, line ln, double speed, double speed2, double height = 0, int crush = -1, int silent = 0, int change = 0, int crushmode = 0)` — Creates a ceiling mover in a sector with specified parameters. Similar to the ACS `Ceiling_Raise` family of specials.
- `bool CreateFloor(sector sec, int floortype, line ln, double speed, double height = 0, int crush = -1, int change = 0, bool crushmode = false, bool hereticlower = false)` — Creates a floor mover in a sector with specified parameters.
- `Thinker CreateThinker(class<Thinker> type, int statnum = Thinker.STAT_DEFAULT)` — Creates a new Thinker of the given class (play-scoped, executes on all clients). **UZDoom-specific extension:** not verified in mainline GZDoom.
- `Thinker CreateClientSideThinker(class<Thinker> type, int statnum = Thinker.STAT_DEFAULT)` — Creates a clientside-only Thinker (renders on the calling client only). **UZDoom-specific extension.**
- `bool SpawnParticle(FSpawnParticleParams p)` — Spawns a particle with parameters from an `FSpawnParticleParams` struct. **Divergence:** The wiki claims this returns `bool`, but the actual implementation is `void`.
- `VisualThinker SpawnVisualThinker(Class<VisualThinker> type)` — Spawns a VisualThinker of the given class and returns a pointer to it.
- `VisualThinker SpawnClientSideVisualThinker(Class<VisualThinker> type)` — Spawns a clientside-only VisualThinker. **UZDoom-specific extension.**

### UDMF data access

- `String GetUDMFString(int type, int index, Name key)` — Retrieves a string UDMF property. `type` is one of the `EUDMF` enum values (`UDMF_Line`, `UDMF_Side`, `UDMF_Sector`).
- `int GetUDMFInt(int type, int index, Name key)` — Retrieves an integer UDMF property.
- `double GetUDMFFloat(int type, int index, Name key)` — Retrieves a floating-point UDMF property.

### Miscellaneous methods

- `play int ExecuteSpecial(int special, Actor activator, line linedef, bool lineside, int arg1 = 0, int arg2 = 0, int arg3 = 0, int arg4 = 0, int arg5 = 0)` — Manually triggers a linedef special by its number. Returns the result code as defined by that special.
- `void WorldDone()` — Signals the level/world is complete (used for clustering/hub behavior).
- `ui Vector2 GetAutomapPosition()` — Retrieves the automap's current pan position (UI-scoped).
- `String FormatMapName(int mapnamecolor)` — Formats the level name for display in intermission screens, with optional color codes.
- `int FindUniqueTid(int start = 0, int limit = 0 [, bool clientSide = false])` — Finds an unused TID within a range, useful for spawning actors with guaranteed unique identifiers. **Divergence:** The wiki omits the `clientSide` parameter. **UZDoom-specific extension.**
- `uint GetSkyboxPortal(Actor actor)` — Returns the skybox portal ID associated with an actor.
- `clearscope HealthGroup FindHealthGroup(int id)` — Retrieves a HealthGroup by ID.
- `vector3, int PickDeathmatchStart()` — Returns a deathmatch player start position and index.
- `vector3, int PickPlayerStart(int pnum, int flags = 0)` — Returns a cooperative player start position and index for player number `pnum`.
- `string LookupString(uint index)` — Looks up a string by its index (for localization/string tables).
- `String GetClusterName()` — Retrieves the episode/cluster name for the current map.
- `String GetEpisodeName()` — Retrieves the episode name for the current map.
- `clearscope int GetPortalGroupCount()` — Returns the total number of portal groups in the level.
- `int isFrozen()` — Alias query for frozen state; identical to `IsFrozen()`.
- `play SpotState GetSpotState(bool create = true)` — Retrieves the level's spot state (player spawn tracking). If `create` is true, creates it if it doesn't exist.
- `int PlayerNum(PlayerInfo player)` — Returns the player number (0-based) for a given `PlayerInfo`.

## Variables

Variables are accessed as properties on the `level` global, e.g., `level.Gravity`, `level.MapTime`.

### Geometry arrays

- `Array<@Sector> Sectors` — Writable array of all sectors in the level.
- `Array<@Line> Lines` — Writable array of all linedefs in the level.
- `Array<@Side> Sides` — **Divergence:** The wiki marks this as `ReadOnly`, but the actual implementation is writable. Array of all sidedefs in the level.
- `readonly Array<@Vertex> Vertexes` — Read-only array of all vertices in the level.
- `readonly Array<@LinePortal> LinePortals` — Read-only array of all line portals in the level.
- `Array<@SectorPortal> SectorPortals` — **Internal (not accessible from mod code).** Array of all sector portals in the level (UZDoom stdlib marks this `internal readonly`).

### Level data

Time tracking:

- `readonly int Time` — Tics elapsed in the current hub.
- `readonly int MapTime` — Tics elapsed since the current map started.
- `readonly int TotalTime` — Total tics elapsed in the game (across all hubs).
- `readonly int StartTime` — Tic count at which the current map began.

Map identification and metadata:

- `readonly int LevelNum` — The level's numeric ID, used by `Teleport_NewMap` special.
- `readonly String LevelName` — The "nice" display name of the level (shown in intermission).
- `readonly String MapName` — The lump or file name of the map (e.g., "MAP01").
- `readonly String AuthorName` — The map's author.

Progression:

- `readonly int ParTime` — Par time for the level, in seconds.
- `readonly int SuckTime` — Suck time, in hours. (Engine-specific; rarely used.)
- `readonly int Cluster` — The episode/cluster number the level belongs to.
- `readonly int ClusterFlags` — Bit flags for cluster behavior. Includes `CLUSTER_HUB` (0x00000001) for hub-style level connections.
- `String NextMap` — Name of the next map defined in MAPINFO (writable).
- `String NextSecretMap` — Name of the secret-exit map (writable).
- `readonly String F1Pic` — Name of the graphic shown when the player presses F1 (help).

Combat and secrets tracking:

- `int Total_Secrets` — Total number of secrets on the map.
- `int Found_Secrets` — Number of secrets discovered so far.
- `int Total_Items` — Total number of items on the map.
- `int Found_Items` — Number of items picked up so far.
- `int Total_Monsters` — Total monster count on the map.
- `int Killed_Monsters` — Number of monsters killed so far.

Physics and movement:

- `double Gravity` — Level-wide gravity (mapunits/tic²). Default: 800.0.
- `double AirControl` — In-air movement control factor. Default: 0.00390625.
- `double AirFriction` — In-air friction/momentum retention. **Divergence (prose), corrected against source:** the wiki's claimed default of "65321 (99.67% of momentum is retained)" is wrong. `AirFriction` is not an independently-set default; it is derived from `AirControl` by a formula recomputed whenever air control changes (at level start, and via the ACS air-control special). Below a low `AirControl` threshold, friction is disabled outright (`AirFriction` = 1.0, i.e., no momentum loss); above that threshold it decreases roughly linearly as `AirControl` increases. The default `AirControl` value (0.00390625) sits exactly at that threshold, so the effective default `AirFriction` is 1.0. Assigning to `level.AirFriction` directly from ZScript is possible (it's a writable `play` field, not `readonly`) but is a one-way override — it is not read back into `AirControl` and will itself be overwritten the next time something recomputes it from `AirControl`.
- `int AirSupply` — Underwater breath duration before drowning, in seconds.

Rendering and sky:

- `readonly TextureID SkyTexture1` — TextureID of the primary (foreground) sky layer.
- `readonly TextureID SkyTexture2` — TextureID of the secondary (background) sky layer.
- `readonly TextureID SkyMistTexture` — TextureID of the skymist texture (sky fog tint).
- `float SkySpeed1` — Scroll speed of the primary sky layer. Default: 0.0.
- `float SkySpeed2` — Scroll speed of the secondary sky layer. Default: 0.0.
- `float SkyMistSpeed` — Scroll speed of the skymist layer.
- `float SkyMistYScale` — **Divergence:** The wiki omits this variable. Vertical scale factor for the skymist texture (same as the `skymistyscale` parameter to `ChangeSkyMist`). Default: 1.0, clamped 0.002–544.0.
- `int MapType` — Map type flags (engine-internal classification). **Poorly documented** ("Need more info" in wiki and source docs); content varies by engine.

Sound and music:

- `readonly String Music` — Name of the currently playing music (lump or file).
- `readonly int MusicOrder` — Track index within a multi-track music file (0 if single-track).
- `String LightningSound` — Sound played when lightning strikes on this map. Default: "world/thunder". Writable.
- `readonly float MusicVolume` — Volume multiplier for the map's music. Default: 1.0. **Divergence, corrected against source:** the field itself is not clamped to 1.0 — ACS's `SetMusicVolume` special function (and the save/restore path) can push it above 1.0. Only the final audio output volume derived from it is clamped downstream (to 0.0–2.0), not the field value read back through this property.

Fog and visual effects:

- `readonly int FogDensity` — Level-wide fog density (0–255, or 0 for no fog).
- `readonly int OutsideFogDensity` — Fog density applied outside enclosed sectors (0–255).
- `readonly int SkyFog` — Sky-only fog density, separate from level fog.
- `readonly double ThickFogDistance` — Distance beyond which "thick fog" (intensified fog) begins.
- `readonly double ThickFogMultiplier` — Multiplier for fog intensity in the thick-fog zone.
- `readonly double PixelStretch` — Aspect ratio correction factor. Default: 1.2 (emulating classic Doom's 4:3 non-square pixels).

Behavioral flags:

- `readonly bool NoInventoryBar` — If true, the inventory bar is hidden.
- `readonly bool MonsterTelefrag` — If true, monsters can telefrag each other and players (except `NOTELESTOMP` monsters).
- `readonly bool ActOwnSpecial` — If true, an actor dying with a special becomes its own activator instead of being activated by its killer.
- `readonly bool SndSeqTotalCtrl` — If true, sound sequences are controlled by sequence ID 0 instead of the sector-movement special.
- `bool Allmap` — Toggles automap discovery of unexplored lines. Writable (e.g., by `MapRevealer` pickups).
- `readonly bool MissilesActiveImpact` — If true, a missile hitting a line becomes the activator instead of its shooter.
- `readonly bool MonsterFallingDamage` — If true, monsters take falling damage.
- `readonly bool CheckSwitchRange` — If true, a height check prevents players from activating switches far above their hitbox.
- `readonly bool PolyGrind` — If true, polyobjects gib monster and player corpses when crossing them.
- `readonly bool NoMonsters` — If true, no monsters spawn in the map.
- `readonly bool AllowRespawn` — If true, players respawn on death like in cooperative mode.
- `bool Frozen` — **Deprecated as of 3.8; use `isFrozen()`/`setFrozen()` methods instead.** Legacy property for freezing the level.
- `readonly bool Infinite_Flight` — If true, flight powerups last indefinitely.
- `readonly bool No_Dlg_Freeze` — Dialogue state flag (purpose not documented in available sources).
- `readonly bool KeepFullInventory` — If true, players retain full inventory when exiting the map (outside hubs).
- `readonly bool RemoveItems` — If true, players lose all items on exit except those flagged `INVENTORY_UNDROPPABLE`.
- `readonly bool UsePlayerStartZ` — **Divergence (wiki omits).** If true, player start spots' Z coordinates are used instead of floor height.

Compatibility and miscellaneous:

- `readonly int CompatFlags` — Map-specific compatibility flags (first word).
- `readonly int CompatFlags2` — **Divergence:** The wiki lists `CompatFlags` twice, but the source has a separate `CompatFlags2` (second word of compatibility flags). **Note:** The wiki omits this variable entirely.
- `name DeathSequence` — The intermission sequence shown on player death. Writable.
- `readonly LevelInfo info` — Pointer to the level's `LevelInfo` struct for accessing MAPINFO properties.

## Constants

- `CLUSTER_HUB` (0x00000001) — Cluster flag indicating hub-style level progression (players retain inventory/stats across maps in the cluster).

## Implementation notes

- **Scope qualifiers:** Many methods are marked `clearscope` (accessible from UI and play scopes) or `play` (play-scope only). A few are `ui` (UI-scope only, e.g., `GetAutomapPosition`). The clientside variants (`CreateClientSideThinker`, `SpawnClientSideVisualThinker`) and the `clientSide` parameter on `FindUniqueTid` and `CreateActorIterator` are **UZDoom-specific extensions** and are unlikely to exist in mainline GZDoom. `WorldPaused` is a separate UZDoom-specific extension (a `static` method, not a clientside variant of anything).
- **Deprecations:** `frozen` property and `IsPointInMap()` method are deprecated in 3.8 in favor of `isFrozen()`/`setFrozen()` methods and `IsPointInLevel()` respectively.
- **Verification scope:** Method/variable declarations and scope qualifiers are verified against UZDoom stdlib source. Behavioral descriptions of individual methods come from the ZDoom Wiki and have not all been exhaustively traced into the native C++ implementations; a representative sample (including the `SetFrozen`/`SpawnParticle` return-type divergences, the `Sides`/`CompatFlags2`/`SkyMistYScale` array-and-field divergences, the `AirFriction` default and the `MusicVolume` clamp claim above, and the `WorldPaused` static-vs-instance placement) has been traced into native C++ and confirmed or corrected as noted inline.
