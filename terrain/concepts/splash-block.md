# TERRAIN `splash` blocks

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/gamedata/p_terrain.cpp` and `p_terrain.h` (`FSplashDef`, `SplashKeywords`, `SplashParser`, `SetSplashDefaults`, `ParseSplash`, `GenericParse`), `src/common/engine/sc_man.cpp` (`ScriptError`), `src/common/engine/m_random.h` (`Random2`), `src/playsim/p_mobj.cpp` (`P_HitWater`, `P_HitFloor`, `FloorBounceMissile`, `P_ZMovement`, `UpdateWaterDepth`, `SplashCheck`), `src/playsim/p_enemy.cpp` (`NoiseMarkSector`, `P_NoiseAlert`, `A_Look` target choice), `src/playsim/p_map.cpp` (hitscan, rail and deep-water splash callers), `src/playsim/p_spec.cpp` and `src/maploader/specials.cpp` (`SECF_DMGTERRAINFX`), `src/common/objects/dobject.h` and `src/scripting/thingdef_data.cpp` (`CLIENTSIDE`, `DONTSPLASH`, `NOSPLASHALERT`), `wadsrc/static/zscript/actors/attacks.zs` (`CheckSplash`), `wadsrc/static/zscript/actors/player/player.zs` (`DoFootstep`), `wadsrc/static/zscript/actors/doom/doommisc.zs` and `wadsrc/static/terrain.txt`, and the Zandronum source's `src/p_terrain.cpp` and `p_terrain.h` (same parser functions), `src/sc_man.cpp`, `src/m_random.cpp`, `src/dobjtype.h` (`IsDescendantOf`, `IsAncestorOf`), `src/s_sound.h` and `src/s_advsound.cpp` (`FSoundID`, `S_FindSound`), `src/p_mobj.cpp` (`P_HitWater`, `P_HitFloor`, `P_CheckSplash`, `FloorBounceMissile`, `P_ZMovement`, `UpdateWaterLevel`), `src/p_enemy.cpp`, `src/p_map.cpp`, `src/p_spec.cpp` (`P_PlayerInSpecialSector`, `P_PlayerOnSpecialFlat`), `src/thingdef/thingdef_codeptr.cpp` (`A_Explode`, `A_RadiusThrust` callers), `wadsrc/static/actors/actor.txt`, `wadsrc/static/actors/doom/doommisc.txt` and `wadsrc/static/terrain.txt`. Keyword names cross-checked against UDB's `Build/Scripting/ZDoom_TERRAIN.cfg` and SLADE's `z_terrain` block in `dist/res/config/languages/zdoom.txt`.

A `splash` block names a set of actors and sounds that the engine spawns when something lands in,
falls into, or shoots into a floor whose terrain points at that splash. This page covers every
splash keyword, the defaults and units, and the runtime (`P_HitWater`) that decides whether a
splash spawns and which half of it. The outer grammar (block syntax, `modify`, load order, name
resolution) is in [the TERRAIN lump](terrain-lump.md); the terrain block that references a splash
with its own `splash` keyword is in [terrain blocks](terrain-block.md).

## Keywords

Both engines accept the same eleven splash keywords (UZDoom `src/gamedata/p_terrain.cpp:145-160`,
Zandronum `src/p_terrain.cpp:156-171`), in any order. A keyword may repeat; the later
occurrence overwrites the earlier one. The block ends at `}`.

| Keyword | Value | Meaning | Default | UZDoom storage | Zandronum storage |
|---|---|---|---|---|---|
| `smallclass` | actor class or `None` | Spawned alone for a **small** splash (see "Small or large"). | none | class pointer | class pointer |
| `smallclip` | number (fractions allowed) | Map units added to the `smallclass` actor's floorclip, sinking its sprite into the floor. | `12` | double | fixed point (1/65536 unit) |
| `smallsound` | sound name | Sound for a small splash. | none | sound ID | sound ID |
| `baseclass` | actor class or `None` | Spawned for a **large** splash, after the chunk. | none | class pointer | class pointer |
| `chunkclass` | actor class or `None` | Spawned for a large splash and thrown with a random velocity. | none | class pointer | class pointer |
| `chunkxvelshift` | integer, `-1` = leave alone | Scale of the chunk's random X velocity. | `8` | byte | byte |
| `chunkyvelshift` | integer, `-1` = leave alone | Scale of the chunk's random Y velocity. | `8` | byte | byte |
| `chunkzvelshift` | integer | Scale of the chunk's random upward velocity. | `8` | byte | byte |
| `chunkbasezvel` | number (fractions allowed) | Fixed upward velocity added to the chunk, map units per tic. | `1` | double | fixed point (1/65536 unit) |
| `sound` | sound name | Sound for a large splash. Terrain damage reuses it too. | none | sound ID | sound ID |
| `noalert` | flag, **no value** | A large splash from a player doesn't wake monsters. | off | bool | bool |

Defaults come from `SetSplashDefaults` (UZDoom `p_terrain.cpp:350-363`, Zandronum
`p_terrain.cpp:356-369`). A new splash with an empty block therefore has no actors and no sounds,
and spawns nothing audible or visible.

**Neither editor config has a gap in the splash keywords.** UDB's `ZDoom_TERRAIN.cfg` lists all
eleven, though it files `noalert` under its "Floor" comment, and it lacks `modify`. SLADE's
`z_terrain` lists all eleven and `modify`.

### Units

- **`smallclip` and `chunkbasezvel`** are read as floats. UZDoom keeps them as doubles (`GEN_Double`,
  `p_terrain.cpp:590-593`); Zandronum multiplies by 65536 and truncates to fixed point
  (`GEN_Fixed`, `p_terrain.cpp:539-542`), so any precision past 1/65536 is lost there. The
  difference is not visible in practice.
- **Velocity shifts** produce a velocity in 1/65536 map units per tic:
  - X and Y: a random integer from -255 to 255 (`Random2()`: UZDoom
    `src/common/engine/m_random.h:174-184`, Zandronum `src/m_random.cpp:244-250`) shifted left by
    the value. The default `8` gives up to about ±1 map unit per tic (±35 units per second, with
    TICRATE 35). Each step of 1 doubles the range: `9` is about ±2, `10` about ±4, `7` about ±0.5.
  - Z: `chunkbasezvel` plus a random integer from 0 to 255 shifted left by `chunkzvelshift`. The
    defaults give 1 to about 2 map units per tic upward.
  - **`-1` means "don't touch this axis" for X and Y only.** The shift is stored in a byte, so `-1`
    becomes 255, which both engines treat as a sentinel: the chunk keeps whatever X/Y velocity it
    spawned with (UZDoom `p_mobj.cpp:7480-7487`, Zandronum `p_mobj.cpp:6938-6945`). The stock
    `Lava` splash uses `-1` on both axes so its smoke rises straight up. **Z has no sentinel.**
  - Values outside 0 to 255 wrap silently into a byte (`GEN_Byte`, UZDoom `p_terrain.cpp:545-548`,
    Zandronum `p_terrain.cpp:556-559`). Large shifts (24 and up) overflow the velocity
    arithmetic. Keep shifts in the single digits to low teens.

### Class and sound names

- **Classes resolve when the splash is parsed.** TERRAIN is read after actor classes exist (see
  the lump page's "When it is read"), so any DECORATE class works, and on UZDoom any ZScript class. The spawn uses
  replacement, so a class that another actor `replaces` spawns the replacement.
- `None` (any case) leaves the slot empty on purpose. An unknown name also leaves it empty, with a
  console message (see "Errors").
- **Sound names resolve at parse time too**, against SNDINFO, which both engines load before
  TERRAIN. An unknown sound name is silently stored as "no sound"; the message for it is commented
  out in both parsers (UZDoom `p_terrain.cpp:533-543`, Zandronum `p_terrain.cpp:544-554`).

## `modify` and redefinition

The outer rules are the lump page's; the splash-specific consequences:

- `splash Water { ... }` for a name that already exists **resets that splash to the defaults
  above** before reading the block (UZDoom `p_terrain.cpp:390-397`, Zandronum
  `p_terrain.cpp:397-404`). Terrains that already point at it keep pointing at it, now with the
  new contents, because the splash keeps its slot.
- `splash Water modify { ... }` changes only the keywords listed. To give the stock `Water` splash
  a new sound without losing its actors, use `modify`.
- There is no way to clear a flag with `modify`: `noalert` can be turned on but not off again
  short of a full redefinition.

## Errors

| Condition | Both engines |
|---|---|
| Unknown keyword in the block, or a value where a keyword is expected (`noalert true`) | Fatal: the parser calls `ScriptError`, which ends in `I_Error` at startup (UZDoom `src/common/engine/sc_man.cpp:1063-1088`, Zandronum `src/sc_man.cpp:888-906`). TERRAIN's scanner never sets UZDoom's `NoFatalErrors`, so there is no soft path. |
| Missing `{` | Fatal: `Expected {` |
| Non-integer value for a shift (`chunkxvelshift 8.5`) | Fatal: `MustGetNumber` rejects it. |
| Unknown actor class | Console message; the slot is empty. **Message text differs**, see "Engine-family divergence". |
| Class that isn't an actor | Console message `... is not an Actor (in splash ...)`; the slot is empty. |
| Unknown sound name | Silent. The sound slot is empty. |
| A terrain's `splash` names a splash not defined yet | Console message `Splash ... is not defined yet`; the terrain has no splash (see the lump page). |

## Runtime: when a splash spawns

All splashing goes through `P_HitWater` (UZDoom `src/playsim/p_mobj.cpp:7364-7520`, Zandronum
`src/p_mobj.cpp:6808-6987`). It returns whether the surface counts as liquid, which some callers
use (a bouncing missile, for instance).

### What calls it

- **Landing.** `P_ZMovement` calls `P_HitFloor` when an actor reaches the floor with downward
  velocity, when a missile hits the floor (before it explodes), and when a `+NOEXPLODEFLOOR`
  missile lands (UZDoom `p_mobj.cpp:3060`, `3082`, `3106`; Zandronum `p_mobj.cpp:3094`, `3120`,
  `3156`). Floor-hugging missiles don't splash. `P_HitFloor` only splashes if the actor is exactly
  on a sector's floor plane or on top of a solid or swimmable 3D floor, and **never in a sector
  with Boom-style fake water** (`Transfer_Heights`), which is handled by the next case instead
  (UZDoom `p_mobj.cpp:7543-7618`, Zandronum `p_mobj.cpp:6996-7042`).
- **Bouncing.** A floor bounce calls `P_HitFloor`; if the surface is liquid, a `BOUNCE_ExplodeOnWater`
  actor explodes or dies, and one without `BOUNCE_CanBounceWater` is removed (UZDoom
  `p_mobj.cpp:2145-2161`, Zandronum `p_mobj.cpp:1760-1775`).
- **Falling into deep water.** When an actor's water level goes from 0 to above 0 in a
  `Transfer_Heights` sector or a non-solid 3D floor, it splashes at the water surface, with the
  "don't splash above the actor" check on (UZDoom `SplashCheck`, `p_mobj.cpp:5351-5362`;
  Zandronum `UpdateWaterLevel`, `p_mobj.cpp:4739-4743`). Which 3D floors count differs, see
  "Engine-family divergence".
- **Hitscans and rails.** A puff that hits a splash floor splashes, and a trace that crosses deep
  water or a 3D water surface splashes where it crosses (UZDoom `src/playsim/p_map.cpp:4865-4869`,
  `5606-5612`, `7222`; Zandronum `src/p_map.cpp:4372-4383`, `5035-5040`, `7074`). **The stock
  `BulletPuff` has `Mass 5` on both engines, so its splash is small.** A custom puff that doesn't
  set `Mass` inherits 100 and makes a large one.
- **Explosions.** `A_Explode` and similar splash the floor under the exploder, **never alerting**
  (UZDoom `CheckSplash`, `wadsrc/static/zscript/actors/attacks.zs:568-582`; Zandronum
  `P_CheckSplash`, `p_mobj.cpp:7052-7061`). On UZDoom this happens when the exploder is within
  the blast distance of the floor. On Zandronum only when it is at floor height, see
  "Engine-family divergence".
- **UZDoom only:** footsteps (every footstep of a `MakeFootsteps` player splashes, never alerting,
  `player.zs:1796-1797`), the ZScript `HitWater`/`HitFloor` methods, and sector damage with the
  `damageterraineffect` flag (see "Engine-family divergence").

### The checks, in order

1. **Which terrain.** A 3D floor whose top is at the splash height wins; then a
   `Transfer_Heights` control sector's floor if that sector clips fake planes; otherwise the sector's
   own floor. See [floor assignment](floor-assignment.md) for how a flat gets its terrain.
2. **No splash on that terrain:** stop; return whether the terrain is `liquid`.
3. **Already in water and touching the floor underneath** (`waterlevel` 1 or more): stop;
   return `liquid`.
4. **Monsters and players falling slowly:** an actor with `ISMONSTER` or a player whose vertical
   velocity is -6 or more (falling slower than 6 map units per tic, 210 per second) doesn't
   splash (UZDoom `p_mobj.cpp:7452`, Zandronum `p_mobj.cpp:6903`). Other actors (items, corpses,
   gibs, missiles, puffs) splash at any downward speed.
5. **Small or large.** The splash is small when the actor's `Mass` is **below 10** (UZDoom
   `p_mobj.cpp:7458`, Zandronum `p_mobj.cpp:6909`).
6. **`+DONTSPLASH`** stops here: nothing spawns, no sound, no alert. Where the check sits differs
   between engines, see "Engine-family divergence".
7. **Spawn.**
   - **Small, and `smallclass` is set:** spawn `smallclass` at the splash point and add `smallclip`
     to its floorclip. Nothing else spawns, and a small splash **never alerts**.
   - **Otherwise** (large, or small with no `smallclass`): spawn `chunkclass` with the random
     velocity above, then `baseclass`. Then, if the splashing actor is a **player**, the splash
     lacks `noalert`, and the caller allowed alerts, wake monsters as if the player had fired
     (`P_NoiseAlert` with the splash marker set; UZDoom `p_mobj.cpp:7499-7502`, Zandronum
     `p_mobj.cpp:6963-6966`). Monsters and non-player actors never alert by splashing.
8. **Sound.** `smallsound` if step 5 chose small, `sound` otherwise, at full volume on the item
   channel with idle attenuation. It plays from the last actor spawned (the base if there is one,
   else the chunk, else the small splash), or at the splash point if nothing spawned. **A small
   splash with no `smallclass` spawns the large actors but still plays `smallsound`.**
9. **Return value:** the terrain's `liquid`, except `false` for a `Transfer_Heights` sector, so
   deep water doesn't swallow missiles.

A splash with only a `sound` (every class `None`) is a pure sound effect; the stock `WaterSound`
splash is one, with `noalert`.

### `NOSPLASHALERT` and `noalert`

- **`noalert` (splash side)** stops the alert entirely for that splash.
- **`+NOSPLASHALERT` (monster side)** makes that one monster ignore splash alerts. It works by not
  setting the monster's own "last heard" target (UZDoom `src/playsim/p_enemy.cpp:135-139`,
  Zandronum `src/p_enemy.cpp:147-151`). The sector's sound target is still set by the splash, so a
  `+NOSPLASHALERT` monster **still wakes** when `compat_soundtarget` is on or the monster has
  `+NOSECTOR`, since those read the sector's target instead (UZDoom `p_enemy.cpp:1940-1941`,
  Zandronum `p_enemy.cpp:1969`).
- Both flags, `DONTSPLASH` and `NOSPLASHALERT`, exist on both engines (UZDoom
  `src/playsim/actor.h:215`, `267`; Zandronum `src/actor.h:206`, `256`). See their rows in
  [the DECORATE index](../../decorate/INDEX.md).

## Example

```text
splash MyOoze
{
    smallclass      MyOozeDrip
    smallclip       8
    smallsound      mymod/oozedrip

    chunkclass      MyOozeGlob
    chunkxvelshift  9       // up to about 2 units/tic sideways
    chunkyvelshift  9
    chunkzvelshift  8
    chunkbasezvel   3       // 3 to about 4 units/tic up
    baseclass       MyOozeRing
    sound           mymod/oozesplash
}

// Keep the stock splash's actors, change only its sound and stop it alerting.
splash Water modify
{
    sound           mymod/watersplash
    noalert
}

terrain MyOoze
{
    splash          MyOoze  // must come after the splash block
    liquid
}
```

## Engine-family divergence

The parsers are the same apart from float storage (see "Units") and one message. The runtime has
drifted more.

- **Unknown class message.** UZDoom prints `Unknown actor <name> in splash <splash>`
  (`p_terrain.cpp:558-563`). Zandronum tests "is it an actor" before "does it exist", so an unknown
  name prints `<name> is not an Actor (in splash <splash>)` instead (`p_terrain.cpp:569-580`). The
  outcome is the same on both: an empty slot, no abort.
- **`+DONTSPLASH` and the return value.** UZDoom only skips the spawn, sound and alert
  (`p_mobj.cpp:7461`); the terrain lookup still runs and the function still reports liquid. So a
  `+DONTSPLASH` bouncer with `BOUNCE_ExplodeOnWater` still explodes on water, and UZDoom's
  `damageonland` (which runs earlier in `P_HitWater`, `p_mobj.cpp:7438-7442`) still hurts a
  `+DONTSPLASH` player. Zandronum returns "not liquid" at once (`p_mobj.cpp:6810`, and again in
  `P_HitFloor` at `7009`), so the same bouncer bounces off water normally.
- **3D floors.** UZDoom takes the terrain from a 3D floor that is solid, swimmable, **or merely
  visible** (alpha above 0), and reads it from the control sector, so a per-sector terrain override
  on the control sector applies (`p_mobj.cpp:7401-7419`). Its deep-water entry check likewise counts
  visible non-swimmable 3D floors (`UpdateWaterDepth`, `p_mobj.cpp:5296-5306`). Zandronum counts only
  solid or swimmable 3D floors, uses the flat on the 3D floor's top (`p_mobj.cpp:6859-6874`), and
  only swimmable ones for the entry splash (`p_mobj.cpp:4710`).
- **Who the splash actors belong to.** UZDoom sets the spawned actors' `target` to the splashing
  actor for the small, chunk and base actors (`p_mobj.cpp:7463-7497`). Zandronum sets it only on the
  chunk (`p_mobj.cpp:6937`). A splash actor that reads its `target` works on both only if it is the
  `chunkclass`.
- **Forcing and flags (UZDoom only).** UZDoom's `P_HitWater` takes a `force` argument (use the
  sector's own terrain, skip 3D floors and the slow-fall check) and flags `THW_SMALL` (always small)
  and `THW_NOVEL` (skip the slow-fall check), exposed to ZScript as `HitWater`
  (`p_mobj.cpp:7358-7362`, `7522-7534`). Footsteps use `THW_NOVEL`, plus `THW_SMALL` unless the
  player's `Mass` is 200 or more (`player.zs:1796-1797`).
- **Hexen-style lava sectors.** UZDoom gives the stock lava sector specials the
  `damageterraineffect` flag, which forces a splash on every damage tick
  (`src/maploader/specials.cpp:535-543`, `src/playsim/p_spec.cpp:475-477`); UDMF sectors can set
  it too. Zandronum calls `P_HitFloor` for the same specials (`src/p_spec.cpp:631-645`), which the
  slow-fall check drops for a player standing still, so in practice no splash.
- **Explosion splash distance.** UZDoom's `CheckSplash` compares the exploder's height with the
  floor plus the blast distance in map units (`attacks.zs:568-582`). Zandronum's callers already
  convert the distance to fixed point (`src/thingdef/thingdef_codeptr.cpp:1056`, `1103`;
  `src/p_enemy.cpp:3643`), and `P_CheckSplash` shifts it by 16 bits a second time
  (`p_mobj.cpp:7054`). That overflows the 32-bit value, so in practice the distance term is lost
  and an explosion splashes only when the exploder is at or below its floor height. An airburst
  just above water splashes on UZDoom but not on Zandronum.
- **Client-side actors.** On UZDoom, an actor with `+CLIENTSIDE` (`src/common/objects/dobject.h:350`,
  `thingdef_data.cpp:406`) only spawns the splash classes that are themselves `+CLIENTSIDE`
  (`p_mobj.cpp:7465`, `7476`, `7493`). UZDoom accepts Zandronum's `+CLIENTSIDEONLY` but ignores it
  (`thingdef_data.cpp:458`). A predicting player never splashes on UZDoom (`p_mobj.cpp:7366`);
  Zandronum has that check commented out and uses the client/server rule below instead.

## Zandronum-specific: which machine's copy is used

Splashes are **decided by the server** (or the single-player game).

- **Clients skip `P_HitWater` entirely** unless the splashing actor is `+CLIENTSIDEONLY`
  (`p_mobj.cpp:6818`); the hitscan floor-splash path returns early on clients as well
  (`src/p_map.cpp:4374-4376`). A client-side-only actor splashes locally using the client's own
  TERRAIN copy.
- **Spectators never splash** (`p_mobj.cpp:6814`).
- **The server sends what it spawned:** each splash actor, the chunk's velocity, the small splash's
  floorclip change, and the sound (`p_mobj.cpp:6921-6929`, `6948-6953`, `6958-6961`, `6967-6983`).
  The client's own TERRAIN copy doesn't affect server-driven splashes; the classes and sound arrive
  by name. A point sound (nothing spawned) is sent at the splashing actor's position rather than
  the exact splash point (`p_mobj.cpp:6982`).
- **Version note:** syncing the small splash's floorclip to clients (commit `0c9dc4823b`,
  2025-10-24) postdates 3.2.1, so a 3.2.1 client online draws the `smallclass` actor without the
  `smallclip` sink. Single player is unaffected.
- Because a client's `P_HitWater` returns "not liquid", a client runs a `BOUNCE_ExplodeOnWater` actor
  as bouncing until the server's explode or destroy arrives.

## See also

- [The TERRAIN lump](terrain-lump.md) for the outer grammar, load order, `modify` and the
  overview of all block keywords.
- [Terrain blocks](terrain-block.md) for the `splash` keyword inside a terrain, `liquid`, and the
  terrain damage that reuses a splash's `sound`.
- [Floor assignment](floor-assignment.md) for how a flat or sector gets its terrain.
- [The DECORATE index](../../decorate/INDEX.md) for the `DONTSPLASH` and `NOSPLASHALERT` flag rows.
