# `A_FaceConsolePlayer` (turn toward the local player)

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-22); Zandronum 3.3-alpha @bdd0f7beb (2026-09-22)
**Provenance:** engine source only. Zandronum, read at upstream `master` @bdd0f7beb (line numbers are that commit's): `src/thingdef/thingdef_codeptr.cpp:4896-4924`, `wadsrc/static/actors/actor.txt:188`, `wadsrc_st/static/actors/skulltagmisc.txt:16-18` (Hissy, the only stock user). Introduced by cfc3a6993 (2012-06-24), an ancestor of the 3.2.1 commit 28f736fb3; the body was not diffed against 3.2.1. UZDoom: `wadsrc/static/zscript/actors/actor.zs:1157`.
**Bucket:** Zandronum: `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_FaceConsolePlayer)` in `src/thingdef/thingdef_codeptr.cpp`. UZDoom: an empty, deprecated `Actor` method in ZScript.

Zandronum only in effect. Turns the calling actor to face the local machine's own player. UZDoom
accepts the call and does nothing.

## Signature

```text
A_FaceConsolePlayer(float MaxTurnAngle = 0)
```

## Parameters

- **`MaxTurnAngle`** (degrees, default `0`): the most the actor may turn in one call. `0` means
  no limit: the actor snaps straight to face the player. With a positive value, if the player is
  within `MaxTurnAngle` either side of the actor's current facing, the actor snaps exactly onto
  the player; otherwise it turns by `MaxTurnAngle` in the shorter direction. Called every tic, a
  value of `5` turns at 5 degrees per tic.

## Zandronum

- **It watches `consoleplayer`, not the actor's target.** The target is the player controlling
  this copy of the game. Nothing touches `target`, `tracer` or any other pointer. If that player
  isn't in the game or has no body, the call does nothing.
- **No network gate and no sync.** Every machine runs it against its own local player, so in an
  online game each client sees the actor turn toward itself, and the actor's angle differs per
  client. Treat it as purely cosmetic. Anything that depends on the actor's angle afterwards (a
  following `A_CustomMissile` fired along the actor's facing, say) will not agree between
  machines. What a dedicated server does depends on its own
  `consoleplayer` slot, which is normally not a player in the game (not traced further).
- **Spying doesn't redirect it.** It follows `consoleplayer`, not the player currently being
  viewed, so while spying on another player the actor still faces your own body.
- Yaw only. Pitch is untouched, and the function doesn't set an action result.
- The stock Skulltag `Hissy` decoration calls `A_FaceConsolePlayer(5)` every tic in its Spawn
  loop.

## Engine-family divergence

UZDoom declares `A_FaceConsolePlayer(double MaxTurnAngle = 0)` on `Actor` with an empty body,
marked deprecated since ZScript version 2.3 as existing only for Zandronum compatibility. A
DECORATE or ZScript call resolves and does nothing: the actor never turns. Use `A_Face`-family
functions with an explicit pointer for anything that must work on UZDoom, and note that UZDoom has
no concept of "the player on this machine" that is safe to act on inside game logic.

## Example

```decorate
ACTOR WatchingStatue
{
  +SOLID
  States
  {
  Spawn:
    STAT A 1 A_FaceConsolePlayer(10)
    Loop
  }
}
```
