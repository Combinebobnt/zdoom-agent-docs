# `raw GetActorProperty(int tid, int property)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-24)
**Provenance:** wiki page `GetActorProperty - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-28,
`https://zdoom.org/w/index.php?title=GetActorProperty&oldid=36601`) + source-verified against `p_acs.cpp:4921-5014`/`12369-12372`, `p_acs.h:384-427`,
`actor.h`, `d_player.h`, `zt-bcc/lib/zcommon.bcs:266-320`. Wiki/fork discrepancy (seven
compile-but-dead `APROP_*` names) recorded below rather than silently trusted or overridden.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.

Reads a property off a single actor by TID. Compiler builtin (`PCD_GETACTORPROPERTY`,
the Zandronum source's `src/p_acs.cpp:12369-12372`), implementation in
`DLevelScript::GetActorProperty` (`p_acs.cpp:4921-5014`).

- `tid` — actor's thing ID. **`0` means "the activator"** (`SingleActorFromTID`, `p_acs.cpp:4445`:
  `if (tid == 0) return defactor;` where `defactor` is the activator) — matches the wiki, and is
  the same zero-means-activator convention as other actor-targeting builtins in this engine.
- `property` — one of the `APROP_*` constants already named in
  the zt-bcc source's `lib/zcommon.bcs:266-312`. **The tier-C signature-only entry gives no hint this
  enum exists at all**, which invites hardcoding raw integers unnecessarily — always use the
  named constant.
- **If `tid` doesn't resolve to an actor, or `property` isn't one Zandronum's switch handles,
  both cases silently return `0`** (the null-actor check at `p_acs.cpp:4925-4927`; the switch's
  `default: return 0;` at `p_acs.cpp:5014`) — indistinguishable from each other, and
  indistinguishable from a genuinely-zero property value.

## The three TID getters conflate "no such actor" with "that actor has TID 0"

`APROP_MASTERTID`, `APROP_TARGETTID` and `APROP_TRACERTID` each return the named actor's `tid`
field, or `0` when there is no such actor. Since `0` is also a perfectly ordinary TID value, and
most actors in a map carry no TID at all, a `0` result is genuinely ambiguous:

- the actor has no master/target/tracer, **or**
- it has one, and that actor's TID is `0`.

Nothing in the return distinguishes them, and the ambiguity is invisible at the call site because
the function's declared return type is `raw`. This is the same shape as the unsupported-property
conflation above, but it arises from a supported property returning a legitimate value, so it
cannot be avoided by checking the property is valid.

The workable test is to ask the pointer question directly instead of via a TID, using
[IsPointerEqual](ispointerequal.md) against `AAPTR_NULL`, which compares resolved actor pointers
and never routes through a TID. Only fall back to reading the TID when you specifically need the
number, and only in a context where you already know the actor is tagged.

For what actually sets `APROP_TARGETTID`'s underlying field during gameplay — damage retaliation,
and `AActor::Die`'s unconditional overwrite — see [Damage retaliation: what writes a monster's
`target` during
gameplay](../../shared/concepts/monster-target-retaliation.md).

**`APROP_MASTERTID` carries an extra wrinkle the other two do not.** Its getter is not a plain
field read: when `master` is null it falls back to the actor's `FriendPlayer` player pawn's TID
(`DoGetMasterTID` in `src/p_acs.cpp`, cited by symbol because that file is commonly patched
locally). So a non-zero result does not prove the actor has a master at all, since it may be
reporting a friend player, and a `0` result means "no master *and* no friend player". Do not read
it as a symmetrical counterpart to the other two.

**Provenance:** source-verified directly against the Zandronum source (no wiki starting point for
this section): the `APROP_MasterTID`/`TargetTID`/`TracerTID` cases in `GetActorProperty`'s switch
and `DoGetMasterTID`, both in `src/p_acs.cpp` and cited by symbol rather than line because that
file commonly carries local patches.

## The `raw` return type hides three different real types — this is the load-bearing gap

The declared return type is `raw`, and naively treating every result as a plain `int` is wrong for
most of the interesting properties. Cross-referencing the wiki's per-property types against the
actual field types in the Zandronum source's `src/actor.h`/`d_player.h`:

- **Plain `int`:** `APROP_HEALTH`, `APROP_DAMAGE` (`SDWORD`, `actor.h:1001`), `APROP_SPAWNHEALTH`,
  `APROP_SCORE` (`actor.h:1082`), `APROP_MASTERTID`/`TARGETTID`/`TRACERTID`, `APROP_WATERLEVEL`
  (`actor.h:1062`), `APROP_MASS` (`SDWORD`, `actor.h:1128`), `APROP_ACCURACY`/`STAMINA`
  (`actor.h:1058`), `APROP_REACTIONTIME` (`SDWORD`, `actor.h:1034`), `APROP_RENDERSTYLE` (a
  legacy-style index, not a fixed value), `APROP_STENCILCOLOR` (`DWORD fillcolor`, a packed color,
  not fixed-point despite being numeric), and all the boolean-flag properties (`APROP_AMBUSH`,
  `INVULNERABLE`, `DROPPED`, `CHASEGOAL`, `FRIGHTENED`, `FRIENDLY`, `NOTARGET`, `NOTRIGGER`,
  `DORMANT`) as `0`/`1`. `APROP_INVULNERABLE`'s *write* side (`SetActorProperty`) has an
  engine-cooperation gotcha of its own — see `functions/setactorproperty.md`'s
  "`APROP_Invulnerable`'s write path has no cooperating-source guard" section.
- **`fixed_t` (fixed-point, `FRACUNIT`=65536=`1.0`) — must be treated as `fixed`, not `int`, or
  the raw value is off by 65536×:** `APROP_SPEED` (`actor.h:1125`), `APROP_ALPHA` (`actor.h:980`),
  `APROP_DAMAGEFACTOR` (`actor.h:1133`), `APROP_GRAVITY` (`actor.h:1076`), `APROP_SCALEX`/`SCALEY`
  (`actor.h:975`), `APROP_HEIGHT`/`RADIUS` (`actor.h:996`), `APROP_MELEERANGE` (`actor.h:1068`),
  and the player-only `APROP_JUMPZ`/`VIEWHEIGHT`/`ATTACKZOFFSET` (`d_player.h:154-163`). None of
  this is discoverable from the `raw GetActorProperty(int, int)` signature — the wiki's per-property
  type column is the only source for it, and it does check out against every field above.
- **String handle (`GlobalACSStrings.AddString(...)`, `p_acs.cpp:5005-5011`) — must be assigned to
  a `str`, not `int`:** `APROP_SEESOUND`/`ATTACKSOUND`/`PAINSOUND`/`DEATHSOUND`/`ACTIVESOUND`,
  `APROP_SPECIES`, `APROP_NAMETAG`. (The engine's own enum comment, `p_acs.h:391`, says
  "Sounds can only be set, not gotten" — that note is about an inconsistency with
  `SetActorProperty`'s sibling switch; `GetActorProperty` does implement a read path for sounds
  regardless, confirmed by the case existing at `p_acs.cpp:5005`.)

## Wiki/engine divergence: properties Zandronum doesn't actually support

The wiki page for `GetActorProperty` (generic ZDoom/GZDoom target) additionally lists
`APROP_Friction`, `APROP_DamageMultiplier`, `APROP_DamageType`, `APROP_FriendlySeeBlocks`,
`APROP_MaxDropOffHeight`, `APROP_MaxStepHeight`, and `APROP_SoundClass`. **zt-bcc's `zcommon.bcs`
does define BCS-side names for all of these** (`APROP_FRICTION` through `APROP_FRIENDLYSEEBLOCKS`,
`zcommon.bcs:305-311`, immediately after `APROP_STENCILCOLOR`) — so they compile fine and look
legitimate — **but Zandronum's engine-side enum (`p_acs.h:384-427`) and `GetActorProperty`'s
switch (`p_acs.cpp:4921-5014`) stop at `APROP_StencilColor = 41` and never implement any of
them.** Calling `GetActorProperty` with any of these seven names, or the Eternity-only
`APROP_COUNTER0`-`COUNTER7` (`zcommon.bcs:313-320`, value `100`+), silently falls through to
`default: return 0;` — same as a typo'd property, with no compiler or runtime warning that the
name exists but does nothing in this engine build. Treat these eight names as **not usable in
Zandronum** despite compiling. (UZDoom differs — see the divergence section below.)

## Engine-family divergence: UZDoom implements all seven, plus an eighth

UZDoom's `GetActorProperty` switch (`src/playsim/p_acs.cpp:4372-4469`) implements every one of the
seven wiki-listed properties that Zandronum's switch leaves unhandled above — `APROP_FRICTION`,
`APROP_DAMAGEMULTIPLIER`, `APROP_DAMAGETYPE`, `APROP_FRIENDLYSEEBLOCKS`,
`APROP_MAXDROPOFFHEIGHT`, `APROP_MAXSTEPHEIGHT`, and `APROP_SOUNDCLASS` — plus an eighth,
`APROP_WATERDEPTH`, which isn't even in the original ZDoom wiki's property list. By return type:
`APROP_FRICTION`/`MAXSTEPHEIGHT`/`MAXDROPOFFHEIGHT`/`WATERDEPTH` come back as `fixed_t` (via
`DoubleToACS`, matching the fixed-point convention documented above for `APROP_SPEED` etc.);
`APROP_DAMAGETYPE`/`SOUNDCLASS` come back as string handles (`GlobalACSStrings.AddString`, same
convention as `APROP_SPECIES`/`APROP_NAMETAG`); `APROP_FRIENDLYSEEBLOCKS` comes back as a plain
`int`. The Eternity-only `APROP_COUNTER0`-`COUNTER7` names are still unimplemented on UZDoom too
(no matching `case` in the same switch) — so of the "eight names not usable in Zandronum" above,
seven now work on UZDoom and only the `APROP_COUNTER*` group remains dead on both engines.

## Which `APROP_*` names are actually DECORATE-settable

Reading a property with `GetActorProperty` doesn't imply a mod can set the same value back from
DECORATE — settability is a separate, per-property fact determined by whether a
`DEFINE_PROPERTY`/`DEFINE_CLASS_PROPERTY` macro exists for it in the Zandronum source's
`src/thingdef/thingdef_properties.cpp`. Grepping that file against the `APROP_*` names above turns
up several worth recording individually, beyond the `int`/`fixed_t`/string-handle taxonomy already
given:

- **`APROP_ACCURACY`/`APROP_STAMINA`** — both DECORATE-settable (`DEFINE_PROPERTY(accuracy, I,
  Actor)` at `thingdef_properties.cpp:1416-1419`, `DEFINE_PROPERTY(stamina, I, Actor)` at
  `:1425-1428`), plain `int` as already noted above. **A reusable finding beyond settability:**
  `accuracy` and `stamina` are Strife-lineage `AActor` fields, and grepping every non-`p_acs.cpp`
  read of `->accuracy`/`->stamina` in the engine shows every one of them is gated to a **player
  pawn** context — Strife weapon spread (`src/g_strife/a_strifeweapons.cpp`), Strife pickups
  (`src/g_strife/a_strifeitems.cpp`), HUD/SBARINFO display, max-health math
  (`src/g_shared/a_pickups.cpp`), the targeter powerup (`src/g_shared/a_artifacts.cpp`), and an
  old-savegame accuracy/stamina compatibility restore in `player_t::Serialize` (`src/p_user.cpp`).
  Nothing in the engine reads either field on a non-player actor. That makes both fields usable as generic free integer tags on a monster/non-player
  DECORATE definition with zero engine side effects — as long as the mod's own player class
  doesn't also rely on them for their original Strife-derived purpose.
- **`APROP_SCORE`** — **not** DECORATE-settable, despite being a perfectly ordinary ACS read
  (`p_acs.cpp:4973`, already covered above as plain `int`): no `DEFINE_PROPERTY(score, ...)` macro
  exists anywhere in Zandronum (only `ScoreIcon` is declarable on the class). Worth noting
  alongside this: `p_mobj.cpp:6278-6279` unconditionally does
  `if (mthing->score) mobj->Score = mthing->score;` at spawn time — so a map-editor Thing's own
  "Score" field silently overwrites `Score` regardless of whatever a DECORATE default would have
  been, if a declarative default even existed.
- **`APROP_MELEERANGE`** — settable (`thingdef_properties.cpp:936`), but per the type taxonomy
  above it's `fixed_t`, not plain `int` — and it's a live gameplay value actually read by
  melee-range checks (`p_enemy.cpp:1029`), not just a cosmetic/reporting field.
- **`APROP_SPAWNHEALTH`** — a non-player actor's read resolves to `actor->SpawnHealth()`; there is
  no dedicated DECORATE property for it, it's set indirectly via the ordinary `Health` property
  (`thingdef_properties.cpp:483`).
- **`APROP_GRAVITY`** — settable (`thingdef_properties.cpp:1301`), also `fixed_t` per the taxonomy
  above, and — like `APROP_MELEERANGE` — a live physics value, not inert bookkeeping.
- **`APROP_SPECIES`** — settable via the `Species` property (`thingdef_properties.cpp:1312`), but
  the read side is the string-handle case already noted above (`p_acs.cpp:5010`), not a plain
  `int`. It also **auto-derives from the class hierarchy when never explicitly set**
  (`p_mobj.cpp:7633-7652`): the engine walks up the actor's own ancestor chain while `MF3_ISMONSTER`
  holds, using the first non-monster ancestor's class name as the default species — so an unset
  `Species` isn't simply blank, it reflects the class hierarchy at spawn time.

**Provenance:** source-verified directly against the Zandronum source (no wiki starting point for
this section): `src/thingdef/thingdef_properties.cpp:483,936,1301,1312,1416-1419,1425-1428`
(`DEFINE_PROPERTY`/`DEFINE_CLASS_PROPERTY` macro presence), `src/p_acs.cpp:4973,5010` (the ACS-side
reads already cited above), `src/p_mobj.cpp:6278-6279,7633-7652`, `src/p_enemy.cpp:1029`, and a
full, non-`p_acs.cpp` grep of `->accuracy`/`->stamina` reads across
`src/g_strife/a_strifeweapons.cpp`, `src/g_strife/a_strifeitems.cpp`, `src/g_shared/a_pickups.cpp`,
`src/g_shared/a_artifacts.cpp`, and `src/p_user.cpp`. **Tier:** B (no wiki-sourced starting point
for this section specifically — see the file-level tier-A stamp below for the rest of this file).

**Example — print an actor's current health, found by TID 100:**

```text
int health = GetActorProperty(100, APROP_HEALTH);
Log(s: "Actor 100 health: ", i: health);
```

**Example — read a fixed-point property correctly (speed, as a float-equivalent):**

```text
fixed spd = GetActorProperty(tid, APROP_SPEED); // fixed_t under the hood — do NOT read as int
Log(s: "Speed: ", f: spd);
```
