# `A_GivePlayerMedal` (award a MEDALDEF medal)

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-22)
**Provenance:** engine source only. Zandronum, read at upstream `master` @bdd0f7beb: `src/thingdef/thingdef_codeptr.cpp:2217-2238`, `wadsrc/static/actors/actor.txt:190`, `src/medal.cpp:412-495` (`MEDAL_GiveMedal`, both overloads), `src/actorptrselect.h:85` (`COPY_AAPTR_NOT_NULL`). Introduced by acbe8686f (2023-12-08, together with the ACS `GivePlayerMedal`), an ancestor of the 3.2.1 commit 28f736fb3. UZDoom source @98b16b78fc has no declaration of this name.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_GivePlayerMedal)` in `src/thingdef/thingdef_codeptr.cpp`; declared on `Actor`, so any actor's states can use it.

Awards a medal to a player, picked through one of the calling actor's pointers. The DECORATE
twin of ACS [`GivePlayerMedal`](../../acs/functions/giveplayermedal.md); both end in the same
`MEDAL_GiveMedal` call.

## Signature

```text
A_GivePlayerMedal(name medal, bool silent, int giveto = AAPTR_DEFAULT)
```

## Parameters

- **`medal`**: the medal's name as defined in [MEDALDEF](../../zandronum-lumps/concepts/medaldef.md)
  (stock or mod-defined). An unknown name awards nothing.
- **`silent`**: required, no default. `true` records the medal without queueing its on-screen
  icon, announcer sound or above-head display.
- **`giveto`**: an `AAPTR_*` selector for the receiver. `AAPTR_DEFAULT` is the calling actor
  itself, which suits a player's own states or a `CustomInventory` item (whose states run with
  the owner as `self`). `AAPTR_TARGET`, `AAPTR_MASTER`, `AAPTR_PLAYER1`.. and the rest work too.
  The resolved actor must be a player's body.

## Behavior

The action result is true only when the medal was actually awarded. In order:

1. The pointer is resolved. If it's null, the function returns without setting a result.
2. On a client it stops here with result false. Only a server or an offline game awards medals;
   the server then tells clients. Unlike the ACS function's wording suggests, single player is
   not excluded by this check.
3. The receiver must be a player. A monster or other non-player gives false.
4. `MEDAL_GiveMedal` then refuses, returning false, if:
   - the game is in a countdown, or the current game mode doesn't have players earning medals
     (`GMF_PLAYERSEARNMEDALS`);
   - the player has no body, or the medal name isn't defined;
   - the `ZADF_NO_MEDALS` dmflag is on;
   - a `GAMEEVENT_MEDALS` event script returns 0 for this award (see
     [Event scripts](../../acs/concepts/event-scripts.md)). The script sees the player as
     activator and the medal name as its first argument.
5. Otherwise the player's count for that medal goes up by one. Unless `silent` is set (or the
   local `cl_medals` is off), the medal joins that player's display queue, replacing its
   lower-tier medal if that one is still queued. A bot receiving a medal gets
   `BOTEVENT_RECEIVEDMEDAL`. A server broadcasts the award to clients.

Because the result follows the award, it works as a success check in `CustomInventory` pickup
and use chains.

## Zandronum-specific: absent on UZDoom

UZDoom has no medal system: no `A_GivePlayerMedal`, no ACS `GivePlayerMedal`, no MEDALDEF. A
state table calling it doesn't resolve on UZDoom.

## Example

```decorate
ACTOR MedalToken : CustomInventory
{
  Inventory.PickupMessage "Bonus!"
  States
  {
  Spawn:
    TOKN A -1
    Stop
  Pickup:
    TNT1 A 0 A_GivePlayerMedal("Excellent", false)
    Stop
  }
}
```
