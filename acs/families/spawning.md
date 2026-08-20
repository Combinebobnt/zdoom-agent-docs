# Spawning family

**Tier:** A for all nine.
**Applies to:** UZDoom=yes, Zandronum=yes — file-level claim for eight of nine; `SpawnParticle`
is the outlier, implemented on UZDoom and absent on Zandronum (source-read, not
`tools/engine_matrix.py`-derived — see its own section below)
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** wiki pages `Spawn - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=Spawn&oldid=52107`), `SpawnForced - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=SpawnForced&oldid=40373`), `SpawnSpot - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=SpawnSpot&oldid=38909`), `SpawnSpotForced - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=SpawnSpotForced&oldid=43870`), `SpawnSpotFacing - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=SpawnSpotFacing&oldid=37428`), `SpawnSpotFacingForced -
ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=SpawnSpotFacingForced&oldid=43872`), `SpawnProjectile - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=SpawnProjectile&oldid=49273`), `SpawnDecal
- ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=SpawnDecal&oldid=48760`), `SpawnParticle - ZDoom Wiki.html` (`https://zdoom.org/w/index.php?title=SpawnParticle&oldid=54779`) (all
`_intake/`) + source-verified against `p_acs.cpp:4170-4271,5397,6336-6337,11652-11665`; see each
function's own section below for its full source citations.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `Spawn`, `SpawnSpot`, `SpawnSpotFacing`, `SpawnProjectile` are compiler builtins
(`zt-bcc/src/builtin.c`, opcodes `PCD_SPAWN`/`PCD_SPAWNSPOT`/`PCD_SPAWNSPOTFACING`/
`PCD_SPAWNPROJECTILE` — none of these four have a `zcommon.bcs` entry, since builtins are baked
into the compiler rather than declared as external functions). `SpawnForced` (-36),
`SpawnSpotForced` (-20), `SpawnSpotFacingForced` (-21), `SpawnDecal` (-72), and `SpawnParticle`
(-96) are extension functions declared in `zt-bcc/lib/zcommon.bcs`.

`Spawn`, `SpawnForced`, `SpawnSpot`, `SpawnSpotForced`, `SpawnSpotFacing`, `SpawnSpotFacingForced`,
`SpawnProjectile`, `SpawnDecal`, `SpawnParticle` — grouped into one file because six of the nine
are not independent implementations: `Spawn`/`SpawnForced` (coordinate-based) and all four
`SpawnSpot*` variants (spot-TID-based) funnel into the same two shared C++ helpers,
`DLevelScript::DoSpawn` (`p_acs.cpp:4170-4225`) and `DLevelScript::DoSpawnSpot`/`DoSpawnSpotFacing`
(`p_acs.cpp:4227-4271`, which themselves call `DoSpawn`). Reading any one of those six against
`p_acs.cpp` in isolation is misleading — the differences between them are a `force` bool and a
"resolve position from a spot TID instead of literal x/y/z" step bolted onto identical core logic.
`SpawnProjectile`, `SpawnDecal`, and `SpawnParticle` are included here for discoverability (same
naming family, same wiki-intake batch) but are genuinely different subsystems — see their sections
below. `SpawnParticle` in particular is **not implemented at all on Zandronum, but is fully
implemented on UZDoom** — see its section.

All nine are documented below regardless of real-world usage — see the family-coverage rule in
`../../shared/AUTHORING.md`'s Authoring rule section (a family's less-used members are exactly the ones nobody
has figured out yet), and the shared-mechanics writeup below is load-bearing for `SpawnForced`
regardless.

**Shared traits across the `DoSpawn`-based six** (`Spawn`, `SpawnForced`, `SpawnSpot`,
`SpawnSpotForced`, `SpawnSpotFacing`, `SpawnSpotFacingForced`; established once here instead of
repeated per function below):

- Class name resolution is always `PClass::FindClass(FBehavior::StaticLookupString(...))` — FName
  lookup, case-insensitive. An unknown class name is a **silent no-op**: no actor is created, no
  console message, the call just contributes 0 to the return count.
- `z` is an absolute map-unit coordinate, never floor-relative.
- `angle` is a byte-angle (0-255), stored into the engine's BAM field as `angle << 24`.
- `tid` is assigned directly to `actor->tid` — plain "no tid" default of 0, normal Doom convention.
- Placement is validated by `P_TestMobjLocation(actor)` (XY blocking-collision check via
  `P_CheckPosition`, plus a Z-bounds check `z < floorz || z+height > ceilingz`) — **unless
  `force` is true**, which unconditionally keeps the actor regardless of what that check finds.
  This one bool is the *entire* difference a "Forced" suffix makes; it does not bypass class-name
  resolution failure or the initial engine-level `Spawn()` call itself failing.
- Return value is a **spawn count**, not the new actor's tid — 0 or 1 for the non-spot variants,
  0-or-more for the spot variants (see below). There is no distinct error code; every failure mode
  collapses to the same "0 spawned" result.
- No teleport fog is ever auto-spawned — scripts that want one spawn `TeleportFog` themselves at
  the same location, a pattern the wiki's own examples show.
- Zandronum adds network-replication side effects on top of identical spawn logic (not in vanilla
  ZDoom, and not a contradiction of any wiki claim): the server broadcasts
  `SERVERCOMMANDS_SpawnThing`/`SetThingAngle`/`SetThingTID` to clients; if a client performs the
  spawn itself the actor is flagged `NETFL_CLIENTSIDEONLY`.

**Additional shared traits across the four `*Spot*` variants** (`SpawnSpot`, `SpawnSpotForced`,
`SpawnSpotFacing`, `SpawnSpotFacingForced`):

- Position comes from an existing "spot" actor found by TID (`FActorIterator`), not literal
  coordinates. **If `spottid == 0`, this does not mean "no spot"** — it spawns at the
  **activator's** own position instead. This is a real, non-obvious behavior the wiki pages don't
  call out.
- If `spottid` is nonzero, the iterator walks **every** actor sharing that TID and spawns one
  clone per match — the return count can exceed 1 (the wiki's "returns 1" framing only holds for
  the single-target `Spawn`/`SpawnForced` pair).
- A spot actor (or the activator, in the `spottid==0` fallback) flagged
  `STFL_HIDDEN_INSTEAD_OF_DESTROYED` is skipped entirely, contributing nothing. This flag is a
  **Zandronum-only** addition (`[RK]`-tagged in source) with no equivalent in vanilla ZDoom — none
  of the four wiki pages mention it.

**Additional shared trait across the two `*Facing` variants** (`SpawnSpotFacing`,
`SpawnSpotFacingForced`): no explicit `angle` argument exists — the spawned actor's angle is
computed internally as the spot's (or activator's) own current BAM angle, `>> 24` to convert to
the byte-angle `DoSpawn` expects. Confirmed genuinely implemented, not a wiki-only claim. **UZDoom
confirmed (2026-08-17):** same mechanic, different internal representation — UZDoom's
`DoSpawnSpotFacing` (`src/playsim/p_acs.cpp:3859-3878`) assigns `aspot->Angles.Yaw` (or
`activator->Angles.Yaw`) straight into the spawned actor's angle with no bit-shift, since UZDoom
stores facing as a float `DAngle` rather than a Zandronum-style BAM fixed-point field. Observable
behavior is identical; only the underlying angle representation differs.

## Engine-family divergence: `nomonsters`/`DF_NO_MONSTERS` gate exists on UZDoom's `DoSpawn`, absent on Zandronum's

Read fresh on both sides this pass (2026-08-17). UZDoom's `DoSpawn` (`src/playsim/p_acs.cpp:3789-3806`)
resolves the spawned class's DECORATE/ZScript replacement first (`info->GetReplacement(Level)`)
and then, if the *replaced* class is a monster (`flags3 & MF3_ISMONSTER`), unconditionally refuses
to spawn it at all when `dmflags & DF_NO_MONSTERS` or `Level->flags2 & LEVEL2_NOMONSTERS` is set —
returning `0` before `Spawn()` is even called, the same silent-failure shape as an unresolved class
name. **Zandronum's `DoSpawn` (`src/p_acs.cpp:4170-4225`, re-read fresh this pass) has no such
check anywhere in the function**, and neither does the generic `Spawn()`/`AActor::StaticSpawn` path
it calls into. A full-tree `grep -rn "DF_NO_MONSTERS\|LEVEL2_NOMONSTERS" src/` finds it only in
`p_things.cpp` (backing `SpawnProjectile`, see below), `p_setup.cpp`'s map-thing loader,
`a_randomspawner.cpp`, and two Hexen-specific decoration classes — none of them in `DoSpawn`'s or
`StaticSpawn`'s own call chain. The one near-miss, `p_mobj.cpp:6156`, sits inside a
`/* ... */`-commented-out block in `SpawnMapThing` (closes at `:6186`) — genuinely dead code, and
`SpawnMapThing` isn't in the ACS spawn path regardless (it's the map-load thing-placement function,
unrelated to `DoSpawn`). A monster class spawned via `Spawn`/`SpawnForced`/any `SpawnSpot*` variant
always spawns on Zandronum regardless of the nomonsters dmflag or level flag; the same call is a
silent no-op on UZDoom under those settings.

This is a genuine asymmetry *within* Zandronum itself, not just a cross-engine gap: Zandronum's own
`P_Thing_Projectile` (backing `SpawnProjectile`, see that section below) **does** carry this exact
`DF_NO_MONSTERS`/`LEVEL2_NOMONSTERS` gate (`src/p_things.cpp:268-271`) — so on Zandronum,
`SpawnProjectile` respects nomonsters settings for a monster class while `Spawn`/`SpawnForced`/
`SpawnSpot*` do not, even though all of them ultimately call the same underlying `Spawn()`. UZDoom's
`EV_Thing_Projectile` (`src/playsim/p_things.cpp:250-279`) carries the identical gate, so on UZDoom
all six `DoSpawn`-based members and `SpawnProjectile` agree with each other; only Zandronum's
`DoSpawn`-based six are the outlier, engine-wide. Applies uniformly to `Spawn`, `SpawnForced`,
`SpawnSpot`, `SpawnSpotForced`, `SpawnSpotFacing`, and `SpawnSpotFacingForced` — see each member's
own section below for a one-line pointer back to this finding rather than six repeated writeups.

---

## `int Spawn(str classname, fixed x, fixed y, fixed z [, int tid [, int angle]])`

The baseline of the family — literal coordinates, `force=false`. Dispatch: `p_acs.cpp:11652`
(`case PCD_SPAWN:`) → `DoSpawn(...)`.

No divergence from the ZDoom wiki found: coordinates, tid/angle semantics, the obstruction-retry
idiom in the wiki's example script, and the "no auto teleport fog" behavior all match this
Zandronum checkout exactly. **UZDoom confirmed (2026-08-17):** `DoSpawn` at
`src/playsim/p_acs.cpp:3789-3835` implements the same coordinate/tid/angle semantics and no-fog
behavior — the one behavioral delta found is the nomonsters gate, which applies to this function
on UZDoom but not on Zandronum; see "Engine-family divergence" above.

**Provenance:** wiki page `Spawn - ZDoom Wiki.html` (`_intake/`, `https://zdoom.org/w/index.php?title=Spawn&oldid=52107`) + source-verified
against `p_acs.cpp:11652`, `DoSpawn` at `p_acs.cpp:4170-4225`.

---

## `int SpawnForced(str classname, fixed x, fixed y, fixed z [, int tid [, int angle]])`

Typically the most-used member of this family in practice. `ACSF_SpawnForced`
(`p_acs.cpp:5397`), dispatch `p_acs.cpp:6336-6337`: `DoSpawn(args[0..3], args[4], args[5], true)`.

- The C++ side reads `args[4]`/`args[5]` (`tid`/`angle`) unconditionally, with no `argCount`
  guard unlike many neighboring `ACSF_` cases — it relies on `zcommon.bcs`'s optional-arg
  declaration always padding these with 0 at compile time when omitted. Not a fork bug, just a
  detail worth knowing if anyone ever hand-encodes a call to this opcode.
- "Forced" here means exactly what the shared-traits section above says: `P_TestMobjLocation` is
  skipped, so a forced spawn can end up embedded in walls/floors/other actors or outside sector
  bounds. This is an accepted tradeoff of the function, not a bug to guard against.
- No divergence from the ZDoom wiki's description of semantics/arg-list/return-value found; the
  only thing the wiki omits is Zandronum's added networking side effects (see shared traits).

**UZDoom confirmed (2026-08-17):** `ACSF_SpawnForced` (`src/playsim/p_acs.cpp:5873-5875`) dispatches
to the same `DoSpawn(..., true)` read above — identical semantics, same nomonsters-gate delta from
Zandronum (see "Engine-family divergence" above). UZDoom's `argCount`-guarded optional-arg handling
(`argCount > 4 ? args[4] : 0`) is the more defensive counterpart to Zandronum's unconditional
`args[4]`/`args[5]` read noted above — a difference in compiler-generated call-site safety, not in
observable behavior, since `zcommon.bcs` already pads omitted args with 0 either way.

**Project-facing note (119 call sites):** the return value is only ever 0 or 1 spawned — never
the new actor's tid. Any call site that wants to act on the spawned actor afterward must pass an
explicit `tid` argument and look the actor up by that tid; the call itself gives back nothing but
a spawn count.

**Provenance:** wiki page `SpawnForced - ZDoom Wiki.html` (`_intake/`, `https://zdoom.org/w/index.php?title=SpawnForced&oldid=40373`) +
source-verified against `p_acs.cpp:5397,6336-6337`, `DoSpawn` at `p_acs.cpp:4170-4225`.

---

## `int SpawnSpot(str classname, int spottid [, int tid [, int angle]])`

Dispatch: `p_acs.cpp:11662-11665` (`PCD_SPAWNSPOT`) → `DoSpawnSpot` at `p_acs.cpp:4227-4248`
(`force=false`), which calls `DoSpawn`. Unlike `SpawnSpotFacing`, the caller's `angle` argument is
used as-is (`angle << 24`) — the spawned actor does **not** inherit the spot's own facing; that's
the entire delta between this function and `SpawnSpotFacing`.

No divergence from the ZDoom wiki found beyond the two Zandronum-only/undocumented behaviors
already covered in the shared `*Spot*` traits above (`spottid==0` → activator fallback,
`STFL_HIDDEN_INSTEAD_OF_DESTROYED` skip) — worth calling out since neither is stated on the wiki
page at all, for any engine.

**UZDoom confirmed (2026-08-17):** `DoSpawnSpot` at `src/playsim/p_acs.cpp:3838-3857` has no
`STFL_HIDDEN_INSTEAD_OF_DESTROYED`-equivalent check at all (grepped absent tree-wide), confirming
the shared-traits claim that flag is genuinely Zandronum-only rather than a vanilla-ZDoom-lineage
feature UZDoom simply hasn't been checked against before now. The `spottid==0` activator fallback
and multi-spot iteration both match. Same nomonsters-gate delta as `Spawn` (see "Engine-family
divergence" above) applies here too, since `DoSpawnSpot` calls `DoSpawn` internally on both engines.

**vs plain `Spawn`:** trades literal x/y/z coordinate precision for spot-based (and potentially
one-to-many) placement.

**Provenance:** wiki page `SpawnSpot - ZDoom Wiki.html` (`_intake/`, `https://zdoom.org/w/index.php?title=SpawnSpot&oldid=38909`) +
source-verified against `p_acs.cpp:11662-11665`, `DoSpawnSpot` at `p_acs.cpp:4227-4248`.

---

## `int SpawnSpotForced(str classname, int spottid [, int tid [, int angle]])`

Literally the intersection of `SpawnSpot` and `SpawnForced`: identical spot-resolution/iteration
logic as `SpawnSpot`, combined with `SpawnForced`'s `force=true` placement-check bypass. `zcommon.
bcs:1648` declares `classname`/`spottid` required and `tid`/`angle` optional — `ACSF_SpawnSpotForced`
(`p_acs.cpp:6095-6096`) → `DoSpawnSpot(args[0..3], true)`.

**Divergence found:** the ZDoom wiki lists all 4 parameters as mandatory; in this toolchain only
`classname`/`spottid` are required, `tid`/`angle` default to 0 if omitted (per the `;` split in
`zcommon.bcs`). No other behavioral divergence found.

**UZDoom confirmed (2026-08-17):** `ACSF_SpawnSpotForced` (`src/playsim/p_acs.cpp:5613-5615`)
dispatches to the same `DoSpawnSpot(..., true)` read above — identical semantics, including the
optional-arg defaulting (compiler-level, so it applies the same regardless of engine). Same
nomonsters-gate delta as `Spawn` applies here too (see "Engine-family divergence" above).

**Provenance:** wiki page `SpawnSpotForced - ZDoom Wiki.html` (`_intake/`, `https://zdoom.org/w/index.php?title=SpawnSpotForced&oldid=43870`) +
source-verified against `zcommon.bcs:1648`, `p_acs.cpp:6095-6096`, `DoSpawnSpot` at
`p_acs.cpp:4227-4248`.

---

## `int SpawnSpotFacing(str classname, int spottid [, int tid])`

Dispatch: `p_acs.cpp:11672-11675` (`PCD_SPAWNSPOTFACING`) → `DoSpawnSpotFacing` at
`p_acs.cpp:4250-4271` (`force=false`). Drops the explicit `angle` argument entirely in favor of
copying the spot's (or activator's, at `spottid==0`) own current angle — confirmed genuinely
implemented (`aspot->angle >> 24`, or `activator->angle >> 24`), not just a wiki claim.

No divergence from the ZDoom wiki found beyond the same Zandronum-only `STFL_HIDDEN_INSTEAD_OF_
DESTROYED` skip covered in the shared traits above.

**UZDoom confirmed (2026-08-17):** `DoSpawnSpotFacing` at `src/playsim/p_acs.cpp:3859-3878` copies
`aspot->Angles.Yaw`/`activator->Angles.Yaw` directly (see the shared `*Facing*` trait note above for
the representation difference from Zandronum's BAM shift) — same observable facing-copy behavior,
same absence of the hidden-flag skip. Same nomonsters-gate delta as `Spawn` applies here too.

**vs `SpawnSpot`:** the only behavioral delta is angle — `SpawnSpotFacing` always uses the spot's
own facing; everything else (spot resolution, tid assignment, multi-spot iteration, `force`
semantics) is identical.

**Provenance:** wiki page `SpawnSpotFacing - ZDoom Wiki.html` (`_intake/`, `https://zdoom.org/w/index.php?title=SpawnSpotFacing&oldid=37428`) +
source-verified against `p_acs.cpp:11672-11675`, `DoSpawnSpotFacing` at `p_acs.cpp:4250-4271`.

---

## `int SpawnSpotFacingForced(str classname, int spottid [, int tid])`

The `SpawnSpotFacing` + `SpawnSpotForced` intersection: `ACSF_SpawnSpotFacingForced`
(`p_acs.cpp:6098-6099`) → `DoSpawnSpotFacing(args[0..2], true)` — angle-copy behavior identical to
`SpawnSpotFacing`, placement-check bypass identical to the other `Forced` variants. No other
behavioral differences exist in this Zandronum checkout.

**Divergence found:** the ZDoom wiki lists all 3 parameters as mandatory; `zcommon.bcs:1649`
declares `tid` optional (defaults to 0). No other divergence found.

**UZDoom confirmed (2026-08-17):** `ACSF_SpawnSpotFacingForced` (`src/playsim/p_acs.cpp:5617-5619`)
dispatches to the same `DoSpawnSpotFacing(..., true)` read above — identical semantics. Same
nomonsters-gate delta as `Spawn` applies here too (see "Engine-family divergence" above).

**Provenance:** wiki page `SpawnSpotFacingForced - ZDoom Wiki.html` (`_intake/`, `https://zdoom.org/w/index.php?title=SpawnSpotFacingForced&oldid=43872`) +
source-verified against `zcommon.bcs:1649`, `p_acs.cpp:6098-6099`, `DoSpawnSpotFacing` at
`p_acs.cpp:4250-4271`.

---

## `void SpawnProjectile(int tid, str type, int angle, int speed, int vspeed, int gravity, int newtid)`

Not part of the `DoSpawn` family at all — it's direction/speed-based, mirroring the line-special
`Thing_Projectile2`'s argument shape rather than the coordinate-based `Spawn` family. All 7 args
are required (`zt-bcc/src/builtin.c:134`, format `";isiiiii"` — no `;` before the return-type
slot means **void**, and all 7 params sit before the optional-marking `;`, i.e. none are
optional). Dispatch is in `p_acs.cpp` (`PCD_SPAWNPROJECTILE`, `p_acs.h:847`), which delegates to
`bool P_Thing_Projectile(...)` in `p_things.cpp:239-467` — note `SpawnProjectile` has **no**
`zcommon.bcs` entry (it's a pure compiler builtin) and **no** "Forced" variant.

- `tid` — `0` means spawn from the activator; a nonzero value fires **once from every actor
  matching that TID** (`FActorIterator`, `p_things.cpp:281-464`), not just the first — a
  multi-spawn side effect the wiki doesn't mention.
- `angle` — byte-angle 0-255 (`angle_t((a)<<24)`), the same convention as the rest of the family;
  matches the `BYTEANGLE()` macro used by the line-special `Thing_Projectile`.
- `speed`/`vspeed` — shifted `<< (FRACBITS - 3)` (`FRACBITS = 16`), i.e. the raw int argument is in
  **1/8 map-unit-per-tic** units, not literal map-units-per-tic. The wiki documents no units at
  all for these; its own example (`speed of 20` against a native `Speed 10` actor) reads as
  misleading if taken as literal map units.
- `gravity` — **not a bitfield**, despite looking like one: `0` forces `MF_NOGRAVITY` on; `1`
  clears `MF_NOGRAVITY` and additionally applies light gravity (`FRACUNIT/8`) for non-monster
  classes; any other nonzero value clears `MF_NOGRAVITY` only, leaving the class's own gravity
  default. No named enum/flags exist for this parameter in `zcommon.bcs`.
- `newtid` — assigned identically to **every** actor spawned in one call (when `tid` matched
  multiple sources) — not made unique per spawn.
- **Always void, always silent on failure** — no console message for unknown class, unresolved
  `tid`/null activator, `DF_NO_MONSTERS`-blocked monster class, or a blocked spawn location
  (`P_CheckMissileSpawn` explodes it in place, or `P_TestMobjLocation` destroys it). There is no
  way to observe whether the spawn actually happened.

**Divergence found:** none against Zandronum's actual behavior — the wiki's signature and angle
encoding both check out. The gap is the wiki's own lack of units/gravity documentation, not a
fork-specific mismatch; this doc fills that gap.

**UZDoom confirmed (2026-08-17):** dispatches to `FLevelLocals::EV_Thing_Projectile`
(`src/playsim/p_things.cpp:250-279` for the header/class-resolution; the gravity switch at
`:316-327`), the direct counterpart of Zandronum's `P_Thing_Projectile`. Every behavior documented
above matches exactly, verified line-for-line: the `speed`/`vspeed` ÷8 units-per-tic conversion
(UZDoom does `STACK(4)/8.`/`STACK(3)/8.` as a plain double division, `p_acs.cpp:9902-9906` —
arithmetically identical to Zandronum's `<< (FRACBITS-3)` fixed-point shift, just expressed in
floating point instead of 16.16 fixed); the `gravity` tri-state semantics (`0` → force
`MF_NOGRAVITY` on, `1` → clear it plus light gravity for non-monsters, any other nonzero → clear it
only — byte-identical `if(gravity)`/`gravity==1` structure on both engines); and the multi-target
`tid` iteration. One difference worth noting for the family as a whole (not `SpawnProjectile`
itself, which is consistent both ways): UZDoom's `EV_Thing_Projectile` carries the same
`DF_NO_MONSTERS`/`LEVEL2_NOMONSTERS` gate Zandronum's `P_Thing_Projectile` already has — so
`SpawnProjectile` agrees with itself across engines, while it's `Spawn`/`SpawnForced`/`SpawnSpot*`
that disagree with `SpawnProjectile` *within* Zandronum specifically (see "Engine-family
divergence" above for the full asymmetry).

**Provenance:** wiki page `SpawnProjectile - ZDoom Wiki.html` (`_intake/`, `https://zdoom.org/w/index.php?title=SpawnProjectile&oldid=49273`) +
source-verified against `zt-bcc/src/builtin.c:134`, `p_acs.h:847`, `p_things.cpp:239-467,281-464`.

---

## `int SpawnDecal(int tid, str decalname [, int flags [, fixed angle [, int zoffset [, int distance]]]])`

Not an actor-spawning function at all, despite the name — it fires a line-trace from an existing
actor and stamps a `DECALDEF`-defined texture onto whatever wall/flat the trace hits. "Success"
means "the trace hit a surface," not "a new `AActor` was created," and `decalname` indexes a
completely separate decal-definition namespace, not an actor class. `ACSF_SpawnDecal`
(`p_acs.cpp:5433`), dispatch `p_acs.cpp:6696-6727`, helper `DoSpawnDecal` (`p_acs.cpp:5812-5836`),
decal lookup `FDecalLib::GetDecalByName` (`decallib.cpp:958-968`), flag values at
`p_acs.cpp:203-205`.

- `tid` — `0` uses the script activator as the trace origin; nonzero walks **every** actor sharing
  that TID via `FActorIterator` and fires one trace per match (same multi-target pattern as the
  `*Spot*` variants above, despite this not being part of that family).
- `decalname` — looked up via `DecalLibrary.GetDecalByName()` (a `DECALDEF` name-tree lookup, not
  a lump or actor-class lookup). Unresolved name → `tpl == NULL` → returns `0` immediately.
- `flags` — bitmask, default 0. **Zandronum only implements `SDF_ABSANGLE` (1) and
  `SDF_PERMANENT` (2)** (`p_acs.cpp:203-204`).
- `angle` — a `fixed` fraction-of-circle, relative to the origin actor's current facing unless
  `SDF_ABSANGLE` is set; converted to BAM internally (`<< FRACBITS`).
- `zoffset`, `distance` — declared `fixed` but the shift logic (`args[n] << FRACBITS`) treats the
  incoming stack value as a plain integer map-unit count, then scales it into the engine's 16.16
  `fixed_t` internally. `distance` defaults to 64 map units if omitted.
- **Return value:** count of decals actually placed — one per matching actor whose trace
  (`ShootDecal`) hit a wall within `distance`; not a plain success bool.
- **Failure modes, all silent (return `0`, no console message):** unresolved `decalname`, `tid`
  resolves to no actor, `tid==0` with no activator, or the trace not hitting a wall within
  `distance` for a given actor (that actor just doesn't add to the count).

**Divergence found (real, not upstream-vs-fork noise):** the ZDoom wiki's flag list also documents
`SDF_FIXED_ZOFF` and `SDF_FIXED_DISTANCE` (GZDoom additions that let `zoffset`/`distance` be
declared as `fixed` instead of plain `int` map-units). **Neither flag exists in this Zandronum
checkout** — only `SDF_ABSANGLE`/`SDF_PERMANENT` are defined (`#define SDF_ABSANGLE 1` /
`#define SDF_PERMANENT 2`, re-grepped fresh this pass, no other `SDF_*` define anywhere in
`src/p_acs.cpp`). A script written against the wiki's full flag set using either missing flag will
silently do nothing useful with it on Zandronum. Everything else the wiki describes (signature
shape, `decalname`/`DECALDEF` semantics, the `tid==0` activator fallback, return-value-is-a-count)
matches this Zandronum checkout's source.

**Provenance:** wiki page `SpawnDecal - ZDoom Wiki.html` (`_intake/`, `https://zdoom.org/w/index.php?title=SpawnDecal&oldid=48760`) +
source-verified against `p_acs.cpp:203-205,5433,6696-6727,5812-5836`, `decallib.cpp:958-968`.

## Engine-family divergence: `SpawnDecal`'s `SDF_FIXED_ZOFF`/`SDF_FIXED_DISTANCE` flags exist on UZDoom, not on Zandronum

**UZDoom confirmed (2026-08-17):** unlike Zandronum, UZDoom implements the full 4-flag set the wiki
documents — `#define SDF_ABSANGLE 1` / `SDF_PERMANENT 2` / `SDF_FIXED_ZOFF 4` / `SDF_FIXED_DISTANCE
8` (`src/playsim/p_acs.cpp:566-569`), and `ACSF_SpawnDecal`'s argument parsing actually branches on
both new flags: `zoffset`/`distance` are read as `ACSToDouble(args[n])` (fixed-point conversion)
when the corresponding flag is set, or as a plain integer otherwise (`src/playsim/p_acs.cpp:
6190-6191`). So a script relying on `SDF_FIXED_ZOFF`/`SDF_FIXED_DISTANCE` per the wiki works
correctly on UZDoom and does nothing useful on Zandronum — the wiki's flag list describes UZDoom's
lineage accurately; Zandronum is the outlier that never backported the two newer flags. Everything
else (`DoSpawnDecal`'s relative-vs-absolute angle logic, `SDF_PERMANENT` gating decal persistence,
the `tid==0`/multi-tid trace-per-actor pattern) matches line-for-line between
`src/playsim/p_acs.cpp:5106-5115` (UZDoom) and Zandronum's `DoSpawnDecal` — see shared traits above.

---

## `void SpawnParticle(int color [, bool fullbright [, int lifetime [, int size [, fixed x [, fixed y [, fixed z [, fixed velx [, fixed vely [, fixed velz [, fixed accelx [, fixed accely [, fixed accelz [, int startalpha [, int fadestep]]]]]]]]]]]]]])` — **dead on Zandronum, live on UZDoom**

**This is the ZDoom-wiki trap by name, not just by caveat, on Zandronum specifically: the call
compiles cleanly and does absolutely nothing at runtime on this engine.** `zcommon.bcs:1726`
declares it as extension function `-96` (`ACSF_SpawnParticle` in ZDoom's own numbering), but
Zandronum's `EACSFunctions` enum (`p_acs.cpp:5360-5449`) jumps straight from `ACSF_Warp = 92` to a
comment block reading `// [BB] Out of order ZDoom backport.` and then to Zandronum's own
`ACSF_ResetMap = 100` — **ACSF numbers 93-99 (`GetMaxInventory`, `SetSectorDamage`,
`SetSectorTerrain`, `SpawnParticle`, `SetMusicVolume`, `CheckProximity`, `CheckActorState` in
ZDoom's numbering) have no enum member and no `case` in `DLevelScript::CallFunction`'s switch at
all** (checked the full switch body, `p_acs.cpp:5899-9059`). A call with `funcIndex == 96` falls
through to the switch's own `default: break;` (`p_acs.cpp:9058-9059`) and the function returns `0`
unconditionally (`p_acs.cpp:9060`) — no particle, no console warning, no distinguishable failure
signal versus a "successful" call, since the function is `void` on the BCS side anyway. **This is
the exact same reserved-range gap `acs/families/inventory.md` documents for `GetMaxInventory` at
-93** — same enum jump, same dead range, same silent no-op shape.

- On Zandronum, every parameter the wiki documents (`color`, `fullbright`, `lifetime`, `size`,
  `x`/`y`/`z`, `velx`/`vely`/`velz`, `accelx`/`accely`/`accelz`, `startalpha`, `fadestep`) is
  irrelevant — they're pushed onto the stack and never read by anything, since there's no case
  body to read them.
- This is **not**, on Zandronum, a case of "documented differently" or "one flag missing" like
  `SpawnDecal`'s `SDF_FIXED_ZOFF`/`SDF_FIXED_DISTANCE` gap above — the entire function body is
  absent there. Don't spend time trying to work around a parameter-level quirk on Zandronum; there
  is no partial functionality to work around on that engine.
- If particle effects are needed on Zandronum specifically, they don't exist via ACS on that engine
  at all — the nearest working alternatives are actor-based (spawning a real `AActor` with a
  particle-like sprite/`+MISSILE`/short lifetime via `Spawn`/`SpawnForced` above) rather than the
  engine's native non-actor particle system. **On UZDoom this whole workaround is unnecessary — see
  below.**

**UZDoom confirmed (2026-08-17):** unlike Zandronum, UZDoom's `EACSFunctions` enum never dropped the
upstream 93-99 range — `ACSF_SpawnParticle` sits at index 96 exactly as ZDoom's numbering expects
(`src/playsim/p_acs.cpp:4744-4820`, contiguous run from `ACSF_Warp = 92` through
`ACSF_CheckActorState // 99`), and `case ACSF_SpawnParticle:` (`src/playsim/p_acs.cpp:6576-6607`) is
a real, working implementation: it reads every wiki-documented parameter (with `argCount`-guarded
defaults — `lifetime` defaults to `TICRATE`, `startalpha` to `0xFF`, `fadestep` to `-1`), clamps
`startalpha`/`lifetime`/`fadestep` to byte range, and calls the engine's real `P_SpawnParticle` with
the position/velocity/acceleration vectors converted via `ACSToDouble`. UZDoom's C++ implementation
actually accepts a 16th parameter, `fixed endsize` (default `-1.`, `src/playsim/p_acs.cpp:6594`),
that isn't in the wiki's documented signature at all — but `zt-bcc/lib/zcommon.bcs:1726-1727`'s
compiler-level declaration caps the callable signature at the 15 wiki-documented parameters, so no
BCS script compiled against this toolchain can ever pass `endsize`; it's permanently defaulted to
`-1.` regardless of engine. Net effect: on UZDoom, every documented parameter of `SpawnParticle`
does exactly what the wiki says, and the "nearest working alternative" workaround above is
Zandronum-only advice — a UZDoom-targeted script can call `SpawnParticle` directly.

**Divergence found (real, not upstream-vs-fork noise):** the ZDoom wiki describes a fully working
function; this Zandronum checkout (`master` HEAD, target 3.2.1) has never implemented ACSF 93-99
at all, `SpawnParticle` included. Confirmed by reading the enum and the full switch body, not just
grepping for the name (a plain `grep -rn SpawnParticle` over the Zandronum source's `src/` returns zero hits,
which is itself the tell — every other implemented `ACSF_*` name appears at least in the enum
declaration). **This is now also an engine-family divergence, not just a wiki/engine one:** UZDoom
matches the wiki's description fully (confirmed above), so the gap is specifically Zandronum never
having backported this range, not the wiki describing a feature neither fork implements.

**Provenance:** wiki page `SpawnParticle - ZDoom Wiki.html` (`_intake/`, `https://zdoom.org/w/index.php?title=SpawnParticle&oldid=54779`) +
source-verified against `zt-bcc/lib/zcommon.bcs:1726`, `p_acs.cpp:5360-5449` (enum),
`p_acs.cpp:5899-9060` (full `CallFunction` switch and its terminal `default`/`return 0`).
