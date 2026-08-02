# `A_SetScale(float scalex, float scaley = 0)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_SetScale` (retrieved 2026-07-31, oldid=52084) + verified against
the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3167` and native declaration
`wadsrc/static/actors/actor.txt:229`.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_SetScale)` — actor action on AActor.

Sets an actor's visual scale (affects sprite rendering only, not the collision box). Commonly used
with `A_FadeOut` to create shrinking/expanding visual effects like dissipating puffs or projectile trails.

## Parameters

- **scalex**: The actor's new horizontal scale. Negative values mirror the sprite horizontally
  (wiki-claimed; not explicitly verified in the Zandronum renderer). Internally stored as fixed-point.

- **scaley**: The actor's new vertical scale. If omitted or set to exactly 0, the value of **scalex**
  is used instead. Internally stored as fixed-point. Unlike upstream ZDoom, Zandronum has no way
  to set scaleY to 0 independently of scaleX (upstream ZDoom added a fourth `usezero` parameter
  for this case).

## Engine scope

**Zandronum has only 2 parameters, not the 4 parameters shown in the upstream ZDoom Wiki.** If you
attempt to use the wiki's 4-parameter form (`A_SetScale(scalex, scaley, ptr, usezero)`), you will
get a DECORATE parse error (arity mismatch). There is no `ptr` parameter to redirect to a different
actor (the action always affects the calling actor), and no `usezero` parameter to distinguish
between "scaley = 0 omitted" and "scaley = 0 explicit."

## Behavior

Server-authoritative: in multiplayer, changes are made server-side and only replicated to clients if
both X and Y scales actually changed (guarded by change detection). Client-handled actors skip the
change entirely (returns early if `NETWORK_InClientModeAndActorNotClientHandled`).

## Example

A projectile-trail effect, shrinking and fading simultaneously:

```
ACTOR TrailSmoke
{
  States
  {
    Spawn:
      TNT1 A 0 A_SetScale(1.0)
      SMOK AAAAAAAA 1 A_FadeOut(0.125)
      SMOK A 1 A_SetScale(0.5) A_FadeOut(0.125)
      SMOK A 1 A_SetScale(0.25) A_FadeOut(0.125)
      wait
  }
}
```
