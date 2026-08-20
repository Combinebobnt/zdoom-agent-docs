# `A_SetScale(float scalex, float scaley = 0)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `A_SetScale` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_SetScale&oldid=52084) + verified against
the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3167` and native declaration
`wadsrc/static/actors/actor.txt:229`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
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

## Engine-family divergence

**Zandronum has only 2 parameters, not the 4 parameters shown in the upstream ZDoom Wiki.** If you
attempt to use the wiki's 4-parameter form (`A_SetScale(scalex, scaley, ptr, usezero)`), you will
get a DECORATE parse error (arity mismatch). There is no `ptr` parameter to redirect to a different
actor (the action always affects the calling actor), and no `usezero` parameter to distinguish
between "scaley = 0 omitted" and "scaley = 0 explicit."

## Engine-family divergence: UZDoom implements the wiki's 4-parameter form

Unlike Zandronum's 2-parameter version described above, UZDoom's `A_SetScale` matches the ZDoom
Wiki's 4-parameter signature exactly: `A_SetScale(double scalex, double scaley = 0, int ptr =
AAPTR_DEFAULT, bool usezero = false)`. UZDoom does support a `ptr` parameter to redirect the scale
change to a different actor (defaulting to the calling actor via `AAPTR_DEFAULT`), and does support
`usezero` to explicitly set scaleY to 0 independently of scaleX - the exact case the Parameters
section above says Zandronum has no way to express. Also unlike Zandronum's fixed-point storage,
UZDoom stores scale as a `vector2` of doubles (native `DVector2 Scale` field), so there is no
fixed-point precision/rounding behavior to consider on this engine.

## Engine-family divergence: no server/client authority split on UZDoom

UZDoom's `A_SetScale` is an unconditional field assignment with no server-authoritative guard or
change-detection/replication step - unlike the Zandronum behavior described below, it does not skip
or gate the change based on client/server role. This matches a broader pattern: UZDoom's engine tree
has no client/server authority split anywhere (no `NETWORK_InClientMode`/`SERVERCOMMANDS_*`
mechanism), so there is nothing analogous to Zandronum's "client-handled actors skip the change"
early-return.

## Behavior

Server-authoritative: in multiplayer, changes are made server-side and only replicated to clients if
both X and Y scales actually changed (guarded by change detection). Client-handled actors skip the
change entirely (returns early if `NETWORK_InClientModeAndActorNotClientHandled`).

## Example

A projectile-trail effect, shrinking and fading simultaneously:

```text
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
