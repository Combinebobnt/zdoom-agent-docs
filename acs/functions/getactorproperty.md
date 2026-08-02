# `raw GetActorProperty(int tid, int property)`

Reads a property off a single actor by TID. Compiler builtin (`PCD_GETACTORPROPERTY`,
the Zandronum source's `src/p_acs.cpp:12369-12372`), implementation in
`DLevelScript::GetActorProperty` (`p_acs.cpp:4921-5007`).

**Bucket:** compiler builtin.

- `tid` — actor's thing ID. **`0` means "the activator"** (`SingleActorFromTID`, `p_acs.cpp:4445`:
  `if (tid == 0) return defactor;` where `defactor` is the activator) — matches the wiki, and is
  the same zero-means-activator convention as other actor-targeting builtins in this engine.
- `property` — one of the `APROP_*` constants already named in
  the zt-bcc source's `lib/zcommon.bcs:266-312`. **The tier-C signature-only entry gives no hint this
  enum exists at all**, which invites hardcoding raw integers unnecessarily — always use the
  named constant.
- **If `tid` doesn't resolve to an actor, or `property` isn't one this fork's switch handles,
  both cases silently return `0`** (`p_acs.cpp:4923-4926`, `default: return 0;` at the end of the
  switch) — indistinguishable from each other, and indistinguishable from a genuinely-zero
  property value.

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
  `DORMANT`) as `0`/`1`.
- **`fixed_t` (fixed-point, `FRACUNIT`=65536=`1.0`) — must be treated as `fixed`, not `int`, or
  the raw value is off by 65536×:** `APROP_SPEED` (`actor.h:1125`), `APROP_ALPHA` (`actor.h:980`),
  `APROP_DAMAGEFACTOR` (`actor.h:1133`), `APROP_GRAVITY` (`actor.h:1076`), `APROP_SCALEX`/`SCALEY`
  (`actor.h:975`), `APROP_HEIGHT`/`RADIUS` (`actor.h:996`), `APROP_MELEERANGE` (`actor.h:1068`),
  and the player-only `APROP_JUMPZ`/`VIEWHEIGHT`/`ATTACKZOFFSET` (`d_player.h:154-163`). None of
  this is discoverable from the `raw GetActorProperty(int, int)` signature — the wiki's per-property
  type column is the only source for it, and it does check out against every field above.
- **String handle (`GlobalACSStrings.AddString(...)`, `p_acs.cpp:4999-5005`) — must be assigned to
  a `str`, not `int`:** `APROP_SEESOUND`/`ATTACKSOUND`/`PAINSOUND`/`DEATHSOUND`/`ACTIVESOUND`,
  `APROP_SPECIES`, `APROP_NAMETAG`. (The engine's own enum comment, `p_acs.h:389`, says
  "Sounds can only be set, not gotten" — that note is about an inconsistency with
  `SetActorProperty`'s sibling switch; `GetActorProperty` does implement a read path for sounds
  regardless, confirmed by the case existing at `p_acs.cpp:4999`.)

## Wiki lists properties this fork doesn't actually support — verified discrepancy, not a doc bug in this file

The wiki page for `GetActorProperty` (generic ZDoom/GZDoom target) additionally lists
`APROP_Friction`, `APROP_DamageMultiplier`, `APROP_DamageType`, `APROP_FriendlySeeBlocks`,
`APROP_MaxDropOffHeight`, `APROP_MaxStepHeight`, and `APROP_SoundClass`. **This fork's `zcommon.bcs`
does define BCS-side names for all of these** (`APROP_FRICTION` through `APROP_FRIENDLYSEEBLOCKS`,
`zcommon.bcs:305-311`, immediately after `APROP_STENCILCOLOR`) — so they compile fine and look
legitimate — **but this fork's engine-side enum (`p_acs.h:384-421`) and `GetActorProperty`'s
switch (`p_acs.cpp:4921-5007`) stop at `APROP_StencilColor = 41` and never implement any of
them.** Calling `GetActorProperty` with any of these seven names, or the Eternity-only
`APROP_COUNTER0`-`COUNTER7` (`zcommon.bcs:313-320`, value `100`+), silently falls through to
`default: return 0;` — same as a typo'd property, with no compiler or runtime warning that the
name exists but does nothing in this engine build. Treat these eight names as **not usable in
this fork** despite compiling.

**Example — print an actor's current health, found by TID 100:**

```
int health = GetActorProperty(100, APROP_HEALTH);
Log(s: "Actor 100 health: ", i: health);
```

**Example — read a fixed-point property correctly (speed, as a float-equivalent):**

```
fixed spd = GetActorProperty(tid, APROP_SPEED); // fixed_t under the hood — do NOT read as int
Log(s: "Speed: ", f: spd);
```

**Provenance:** wiki page `GetActorProperty - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-28,
`oldid=36601`) + source-verified against `p_acs.cpp:4921-5007`/`12369-12372`, `p_acs.h:384-421`,
`actor.h`, `d_player.h`, `zt-bcc/lib/zcommon.bcs:266-320`. Wiki/fork discrepancy (seven
compile-but-dead `APROP_*` names) recorded above rather than silently trusted or overridden.
**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.
