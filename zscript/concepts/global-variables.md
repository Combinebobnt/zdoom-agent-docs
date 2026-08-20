# Global variables in ZScript

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki `ZScript global variables` (retrieved 2026-08-03, https://zdoom.org/w/index.php?title=ZScript_global_variables&oldid=55242); verified against UZDoom source's `wadsrc/static/zscript/doombase.zs` and `LevelLocals` struct; re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — no behavioral drift found.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

ZScript provides access to several engine-level global variables (most readonly, some writable — see each entry below), plus two design patterns for creating custom global state that persists across actors or levels.

## Built-in global variables

The following variables are accessible throughout ZScript code as global namespace members, via the `struct _` declaration and the `extend struct _` block that adds to it (see "Two-file split" below). Each carries a scope qualifier affecting where it can be accessed:

- `play` — accessible only within play-scope code (the level-running context); not available in UI, menu, or console scopes.
- `ui` — accessible only within UI-scope code (menus, HUD displays); not available during level play.
- No scope qualifier — accessible everywhere.

**Note on wiki discrepancy:** The ZDoom Wiki claims approximately 60 global variables, and a combined count across the two files below (see next paragraph) lands close to that figure — an earlier pass of this document checked only one of the two and concluded roughly two-thirds of the wiki's claimed names were missing, which was a scope error rather than a real gap. Three names genuinely don't exist anywhere in the local ZScript API: `deathmatch`, `teamplay`, and a standalone `skill` variable (difficulty data is exposed only via the `AllSkills` array and the `G_SkillPropertyInt`/`G_SkillPropertyFloat` accessor functions, not a plain global). **No entry for tier-A verification is possible without exhaustively tracing all ~60 claimed names against both UZDoom and GZDoom source, and the local checkout is described as behind current GZDoom upstream** (see `shared/AUTHORING.md`'s "The local UZDoom checkout is behind its own upstream").

**Two-file split:** the global-variable struct isn't declared in one place. `wadsrc/static/zscript/engine/base.zs` defines the base struct (roughly 40 members — mostly UI/menu/console-facing: fonts, screen-scaling factors, menu and console state, key bindings, and game-mode/game-state flags), and `doombase.zs` (cited in Provenance) only *extends* it with roughly 20 further members — mostly play-scope: players, level data, actor-class lists. A verification pass that reads only `doombase.zs` will wrongly conclude that the `engine/base.zs` members don't exist.

### Verified present in UZDoom 5.0.0-pre — declared in `doombase.zs`

- `Array<class<Actor> > AllActorClasses` (readonly) — all Actor-derived classes currently loaded. Note: this is distinct from `AllClasses` (all classes of any kind, not just actors) — see the `engine/base.zs` section below; both exist as separate variables, contrary to an earlier pass of this doc that treated `AllActorClasses` as the "actual name" for the wiki's `AllClasses`.
- `Array<@PlayerClass> PlayerClasses` (readonly) — all player class definitions.
- `Array<@PlayerSkin> PlayerSkins` (readonly) — all player skin definitions.
- `Array<@Team> Teams` (readonly) — team information in a multiplayer game.
- `Array<@TerrainDef> Terrains` (readonly) — terrain definitions.
- `Array<@EpisodeInfo> AllEpisodes` (readonly) — all available episodes.
- `Array<@SkillInfo> AllSkills` (readonly) — all difficulty levels.
- `int validcount` (readable and writable) — internal variable to avoid redundant actor processing within a single frame; commonly incremented to tag processed actors, then checked the next frame to see whether an actor was already handled.
- `int gametic` (readonly) — number of tics elapsed since game start.
- `int Net_Arbitrator` (readonly) — player number of the net-game host (multiplayer only).
- `int LocalViewPitch` (readable and writable) — pitch change applied by player input this tic; modified during input events and player-camera code.
- `@DehInfo deh` (play-scope) — DeHackEd parsing state (rarely used from user code).
- `bool automapactive` (ui-scope, readonly) — whether the player's automap overlay is active.
- `bool viewactive` (ui-scope, readonly) — within an active automap display, distinguishes the main map view (`true`) from overlay mode (`false`); absent from wiki table.
- `TextureID skyflatnum` (readonly) — the flat texture ID used for sky-mapping in maps.
- `BaseStatusBar StatusBar` (ui-scope) — reference to the current status bar; readable and writable.
- `Weapon WP_NOCHANGE` (readonly) — sentinel constant signifying "no weapon change requested" (used in `PlayerInfo.PendingWeapon`).
- `bool globalfreeze` (readonly, deprecated in 3.8) — **not visible in wiki table; deprecated; use `Actor.isFrozen()` or `Level.isFrozen()` instead**.
- `@PlayerInfo[] players` (play-scope) — all players in the level, indexed by player number (0 to `MAXPLAYERS - 1`).
- `bool[] playeringame` (readonly) — parallel array indicating which `players[]` slots are occupied; check this before accessing `players[i]`.
- `LevelLocals Level` (play-scope) — the current level's data, geometry, and methods. While technically writable, mutation is unusual and error-prone; treat as logically readonly. Contains hundreds of level-specific properties and methods — see `doombase.zs:501-673` for the full definition (was `501-650`; grew slightly in the 2026-08-01 pull, which added a `skymistyscale` field, but the shape/count of the top-level global variables below is unaffected).

### Verified present in UZDoom 5.0.0-pre — declared in `engine/base.zs`

The base `struct _` declaration (`native unsafe(internal)`) lives here, not in `doombase.zs`; `doombase.zs`'s block above is an `extend struct _` on top of it. Most of the wiki names an earlier pass of this doc marked "not verified" turn out to live in this file instead:

- `Array<class> AllClasses` (readonly) — every loaded class of any kind, not just actors (compare `AllActorClasses` above).
- `bool multiplayer` (readonly) — whether the current game involves more than one player.
- `@KeyBindings Bindings`, `@KeyBindings DoubleBindings`, `@KeyBindings AutomapBindings` (all readable and writable) — key-binding lookup tables for normal input, double-tap input, and automap-mode input respectively.
- `@GameInfoStruct gameinfo` (readonly) — MAPINFO-driven engine/game-mode configuration.
- `bool netgame` (ui-scope, readonly) — whether the game is running networked.
- `uint gameaction` and `int gamestate` (both readonly) — the engine's top-level state-machine values.
- `int consoleplayer` (readonly) — the local client's player-array index.
- `int paused` (readonly) — nonzero while the game is paused.
- `int menuactive` (ui-scope, readable and writable) — menu visibility, with distinct nonzero values for different menu sub-states rather than a plain bool.
- `bool demoplayback` (readonly) — whether a demo is currently playing back.
- `int BackbuttonTime` and `float BackbuttonAlpha` (both ui-scope, readable and writable) — menu back-button fade/animation state.
- `@MusPlayingInfo musplaying` (readonly) — metadata for the currently playing music track.
- `bool generic_ui` (readonly) — whether the generic UI font set is in use.
- `int GameTicRate` (readonly) — the engine's configured tics-per-second rate.
- `@FOptionMenuSettings OptionMenuSettings` (readonly) — options-menu configuration state.
- `uint8 ConsoleState` (ui-scope, readonly) — the console's visibility/animation state (open, closed, rising, falling).
- `MenuDelegateBase menuDelegate` (readable and writable, no scope qualifier) — the active menu delegate object, if any.
- `double NotifyFontScale` (readonly) — scale factor applied to on-screen notification text.
- Eleven `Font` fields (`smallfont`, `smallfont2`, `bigfont`, `confont`, `NewConsoleFont`, `NewSmallFont`, `AlternativeSmallFont`, `AlternativeBigFont`, `OriginalSmallFont`, `OriginalBigFont`, `intermissionfont`; all readonly) — the engine's built-in font set.
- Eight `int` screen-scaling factors (`CleanXFac`, `CleanYFac`, `CleanWidth`, `CleanHeight`, `CleanXFac_1`, `CleanYFac_1`, `CleanWidth_1`, `CleanHeight_1`; all readonly) — precomputed HUD/menu scaling values at two different scale tiers.
- `Map<Name, Service> AllServices` (`internal readonly`) — present in source but marked `internal`, so it isn't meant for use from ordinary mod ZScript.

### Confirmed absent: claimed in wiki but not in UZDoom

The following names appear in the ZDoom Wiki table and were confirmed absent by grepping both `doombase.zs` and `engine/base.zs` in full, plus a tree-wide search of `wadsrc/static/zscript/` (not just the two global-variable structs):

- `deathmatch`, `teamplay` (game-mode flags — `multiplayer` is a distinct name and is confirmed present above).
- `skill` as a standalone global (difficulty level is reachable instead via `AllSkills[...]` or the `G_SkillPropertyInt`/`G_SkillPropertyFloat` static functions).

Before relying on any of these in code targeting a different UZDoom/GZDoom checkout or version, re-verify with a grep for `struct _` (both the base declaration in `engine/base.zs` and the `extend struct _` block in `doombase.zs`) rather than assuming this list still holds unchanged.

## Creating custom global variables

For persistent state shared across actors or between map loads, two design patterns are available; choose based on whether the state needs to survive savegame loads and how frequently it's accessed.

### Pattern 1: StaticEventHandler (fast, single-initialization)

A `StaticEventHandler` persists for the entire session and is **not** saved to savegames. Use this when global data only needs initialization once at game launch, regardless of how many maps are loaded.

```zscript
class MyStaticGlobals : StaticEventHandler
{
    int myCounter;
    Array<Actor> importantActors;
    
    override void NetworkProcess(ConsoleEvent e)
    {
        // Handle network events if needed
    }
}

// Elsewhere, to access the handler:
class MyActor : Actor
{
    override void PostBeginPlay()
    {
        super.PostBeginPlay();
        
        // Find the handler by class name
        let globals = MyStaticGlobals(StaticEventHandler.Find("MyStaticGlobals"));
        if (globals)
        {
            globals.myCounter++;
        }
    }
}
```

**Advantages:**
- Initializes once; no re-computation per map load.
- `StaticEventHandler.Find()` is fast O(n) lookup.
- Access from any scope (play or ui).

**Disadvantages:**
- State is lost on new game or engine restart.
- Not serialized to savegames; can't be restored on load.
- One handler instance per class name; not suitable for multiple independent instances.

### Pattern 2: Thinker (slow, savegame-persistent)

A `Thinker` — especially one with `statnum` of `STAT_STATIC` — persists across map loads and is saved and restored with savegames. Use this for state that must survive saves or span multiple maps.

```zscript
class MyGlobalVariables : Thinker
{
    int testVar;
    
    static MyGlobalVariables Get()
    {
        // Search for an existing instance
        ThinkerIterator it = ThinkerIterator.Create("MyGlobalVariables", STAT_STATIC);
        let p = MyGlobalVariables(it.Next());
        
        // If not found, create one
        if (!p)
        {
            p = new("MyGlobalVariables");
            p.ChangeStatNum(STAT_STATIC);  // STAT_STATIC persists between maps
        }
        
        return p;
    }
}

// Access from an actor:
class MyActor : Actor
{
    override void PostBeginPlay()
    {
        super.PostBeginPlay();
        
        let globals = MyGlobalVariables.Get();
        if (globals)
        {
            globals.testVar++;
        }
    }
}
```

**Advantages:**
- Saved and loaded with savegames.
- Persists across map loads if `STAT_STATIC` is used.
- No limit on number of instances (one per created object).

**Disadvantages:**
- `ThinkerIterator` search is slower than `StaticEventHandler.Find()` (iterates all thinkers).
- Overhead of per-frame `Tick()` calls if the class inherits thinker behavior.
- Persistence across map loads requires explicit `STAT_STATIC` (other stats default to per-map lifetime).

### Comparison

| Aspect | StaticEventHandler | Thinker |
|--------|---|---|
| Lifetime | Session (lost on restart) | Session or per-map (configurable via statnum) |
| Savegame persistence | Never | Yes (if registered) |
| Lookup speed | Fast (`Find()`) | Slower (iterator scan) |
| Suitable for | One-time setup, cached computations | Map-spanning data, saved progress |
