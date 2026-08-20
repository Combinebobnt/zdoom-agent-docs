# ZScript spawn flags

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki "ZScript spawn flags" (retrieved 2026-08-03, https://zdoom.org/w/index.php?title=ZScript_spawn_flags&oldid=54250) + verified against UZDoom 4.15pre source's `wadsrc/static/zscript/constants.zs` and `src/playsim/p_mobj.cpp:HandleSpawnFlags()`; re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — no behavioral drift found
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

Every actor has a `SpawnFlags` field recording how it was spawned: whether it came from a map, a console command, or a script; whether it's friendly to the player; and other mapthing-specific properties. Unlike actor flags (which are synthesized as `b<FlagName>` boolean fields), spawn flags are accessed through **direct bitwise operations** on the `SpawnFlags` uint — there is no `b`-prefix field for these.

## Accessing spawn flags in code

Spawn flags are stored in the `uint SpawnFlags` property and checked/set using bitwise AND (`&`) and bitwise OR (`|`) operators:

```text
virtual override BeginPlay()
{
  // Check if spawned as friendly
  if (SpawnFlags & MTF_FRIENDLY)
  {
    // ...
  }

  // Check multiple conditions
  if (!(SpawnFlags & (MTF_SINGLE | MTF_COOPERATIVE)))
  {
    // Spawned in deathmatch mode
  }

  // Modifying spawn flags (example: copy flags to a new actor)
  NewActor.SpawnFlags = SpawnFlags & ~MTF_SECRET;  // Keep all flags except SECRET
}
```

The `&` operator tests whether a flag is set; `|` combines flags (primarily used when copying spawn flags between actors). Clear individual flags with `&` followed by `~` (bitwise NOT).

## Spawn flag definitions

The flag enums are defined in `EMapThingFlags`:

| Flag Name | Value | Meaning |
|-----------|-------|---------|
| `MTF_AMBUSH` | 0x0008 | Actor is deaf (ignores enemy sounds; monsters will not react until player/enemy is in sight). |
| `MTF_DORMANT` | 0x0010 | Actor spawns dormant/inert and will not act until activated. |
| `MTF_SINGLE` | 0x0100 | Actor only spawns in single-player games. |
| `MTF_COOPERATIVE` | 0x0200 | Actor only spawns in cooperative multiplayer games. |
| `MTF_DEATHMATCH` | 0x0400 | Actor only spawns in deathmatch/team deathmatch games. |
| `MTF_SHADOW` | 0x0800 | Actor spawns as a shadow: sets SHADOW flag, render style translucent, alpha 0.25. |
| `MTF_ALTSHADOW` | 0x1000 | Actor spawns invisible: render style set to STYLE_None, so it is never drawn by the renderer. ² |
| `MTF_FRIENDLY` | 0x2000 | Actor spawns friendly to the player; adjusts kill counter. |
| `MTF_STANDSTILL` | 0x4000 | Actor spawns with the STANDSTILL flag set (will not move). |
| `MTF_STRIFESOMETHING` | 0x8000 | Unused legacy flag; does nothing. |
| `MTF_SECRET` | 0x080000 | Actor is a secret pickup and increments the level's secret count. |
| `MTF_NOINFIGHTING` | 0x100000 | Actor spawns with NOINFIGHTING flag (monsters ignore it as infighting target). ¹ |
| `MTF_NOCOUNT` | 0x200000 | Actor does not count toward kill or item percentages. |
| `MTF_MAPTHING` | 0x400000 | Actor was spawned by the map. ¹ |
| `MTF_CONSOLETHING` | 0x800000 | Actor was spawned via console (e.g., `summon` CCMD). ¹ |
| `MTF_NONSPAWNTHING` | 0xC00000 | Composite: `(MTF_MAPTHING \| MTF_CONSOLETHING)`. Used to detect actors spawned by neither map nor console (spawned from ZScript or ACS). ¹ |

¹ Verified in UZDoom 4.15pre checkout. The ZDoom Wiki flags `MTF_NOINFIGHTING`, `MTF_MAPTHING`, `MTF_CONSOLETHING`, and `MTF_NONSPAWNTHING` as development-version-only; stable GZDoom releases may not include them yet — verify availability in your target engine version.

² `STYLE_None` also fails `P_CheckSight()`'s stealth-monster check (`FRenderStyle::IsVisible()` returns false when `BlendOp == STYLEOP_None`), which is what actually gates whether another actor can detect this one by sight — not just "player vs. monster." That check applies to whichever actor is being looked *at* (the target, not the looker) regardless of who's doing the looking, and it isn't an absolute block: it fails sight most of the time but leaves a small per-call chance of detecting the actor anyway (`pr_checksight() > 50` fails sight, so roughly a fifth of calls succeed despite the invisibility). Because monster AI (`A_Look`/`A_Chase`) reruns sight checks every few tics, a nearby monster will tend to detect an `MTF_ALTSHADOW` actor eventually even though it's never drawn — while the player has no equivalent repeated-check path, since on-screen visibility is suppressed outright by the renderer rather than gated by this probabilistic check. Separately, the flag does not affect the actor's own sight of others: `P_CheckSight` only tests the target's render style, never the looker's, so a monster spawned with this flag can still spot and chase the player normally.

### Wiki errata

The ZDoom Wiki inconsistently names the composite flag: the heading and main section call it `MTF_NOTSPAWNTHING`, but the inline code example and the actual source use the correct name `MTF_NONSPAWNTHING` (all three MTF_* names, not two). The source has the authoritative value — use `MTF_NONSPAWNTHING`.

## Configuring spawn behavior at map load: skill filters

The `SpawnFilter` MAPINFO skill property controls which mapthing-flag actors spawn on each skill level. See `../../mapinfo/concepts/skill-block.md` for how to use it to filter actors by skill.

## HandleSpawnFlags() and automatic application

Automatic application is narrower than it might sound: only actors spawned **from a map** get `HandleSpawnFlags()` called for them automatically. `FLevelLocals::SpawnMapThing()` calls `AActor::LevelSpawned()` right after `BeginPlay()`, and `LevelSpawned()` is what sets `MTF_MAPTHING` on `SpawnFlags` and then calls `HandleSpawnFlags()` to process it — setting actor flags, adjusting render style, incrementing counters, etc.

Console-spawned actors (`summon` and its variants) do **not** get this treatment: that path only OR's `MTF_CONSOLETHING` into `SpawnFlags` directly, and separately replicates the friendly/foe-related effects inline — it never calls `HandleSpawnFlags()`. Any other `SpawnFlags` bits set on a summoned actor (`MTF_AMBUSH`, `MTF_SHADOW`, `MTF_SECRET`, etc.) are inert unless something calls `HandleSpawnFlags()` for it explicitly. `RandomSpawner`'s replacement-actor logic is the standard example: it copies `SpawnFlags` onto the actor it spawns and then calls `newmobj.HandleSpawnFlags()` itself (masking out `MTF_SECRET` first, since the secret count was already credited to the spawner) — because nothing else will do it for a non-map spawn. The function is exposed to ZScript for exactly this kind of case, and more generally whenever an actor's spawn flags need to be (re)processed manually:

```text
HandleSpawnFlags();  // Reprocess current actor's spawn flags
```

## Relationship to actor flags

Standard actor flags (SOLID, FRIENDLY, NOGRAVITY, INVULNERABLE, etc.) are separate from spawn flags and are accessed via the `b<FlagName>` boolean-field syntax. Spawn flags control *how* an actor was created and filter spawning by game mode; actor flags control *how* the engine treats an actor during gameplay (collision, visual rendering, physics). See `actor-flags.md` for the actor flag table and access syntax.

## See also

- DECORATE and ZScript: `actor-flags.md` — the actor flag table (names, syntax differences in Default blocks vs. code, engine presence).
- `zscript-engine-availability.md` — ZScript is UZDoom/GZDoom-family only; absent from Zandronum entirely.
- MAPINFO skill filtering: `../../mapinfo/concepts/skill-block.md#skill-properties` — using `SpawnFilter` to control which skill levels spawn which actors.
