# `A_CheckFloor`

**Tier:** A
**Engine:** Zandronum 3.2.1, UZDoom 4.15pre
**Provenance:** ZDoom Wiki `A_CheckFloor` (retrieved 2026-08-01, oldid=43633) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3702-3713` and UZDoom's `wadsrc/static/zscript/actors/checks.zs:153-156`.
**Bucket:** Action function on `AActor` (`DEFINE_ACTION_FUNCTION_PARAMS` in Zandronum `src/thingdef/thingdef_codeptr.cpp`; ZScript native in UZDoom `wadsrc/static/zscript/actors/checks.zs`).

Jumps to a target state if the calling actor is standing on or submerged into the floor.

## Signature

```decorate
state A_CheckFloor (state target)
state A_CheckFloor (int offset)
```

## Parameters

**`target`** (state label or frame offset)  
The jump destination. If a state label (e.g., `"CancelMovement"`, `"DeathFade"`), the name is resolved in the calling actor's derived class's state table (virtual resolution). If an integer, the offset counts **frames in the current state line**, not instruction lines.

## Behavior

- Compares the actor's Z position against the `floorz` (the floor surface height at the actor's current XY location).
- If `self->z <= self->floorz`, the actor is either resting on the floor or submerged *below* the floor surface — the jump is performed.
- If `self->z > self->floorz`, the actor is above the floor (in the air, on a raised platform, or in water above floor-level) — execution continues to the next action without jumping.
- The jump does not set any result value for inventory-pickup state chains (`ACTION_SET_RESULT(false)` is always called, per the source).

## Network considerations

```c
DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_CheckFloor)
{
	ACTION_PARAM_START(1);
	ACTION_PARAM_STATE(jump, 0);

	ACTION_SET_RESULT(false);	// Jumps should never set the result for inventory state chains!
	if (self->z <= self->floorz)
	{
		ACTION_JUMP(jump, 0);	// [BC] Clients have floor information.
	}

}
```

**Source excerpt:** This file quotes Zandronum engine source verbatim; see [LICENSE](../../LICENSE) §3 for Zandronum's license terms.

The `ACTION_JUMP(jump, 0)` call passes a `0` flags argument, which means clients are **not notified** of the state jump by the server. This is safe because clients maintain their own floor-height data locally (per-client terrain information is reliable) — each client can independently check whether its own actor copy is on the floor and execute the jump without waiting for server confirmation. By contrast, checks that depend on server-side-only knowledge (like `A_CheckHealth`) pass `CLIENTUPDATE_FRAME` to explicitly notify all clients of the jump.

## Examples

The following rocket will not explode when landing, instead entering a silent loop:

```decorate
ACTOR Useless_Rocket: Rocket Replaces Rocket
{
  DeathSound "None"
  States
  {
  Spawn:
    MISL A 1 Bright
    Loop
  CancelMovement:
    MISL A 1 Bright
    Loop
  Death:
    MISL B 0 A_CheckFloor("CancelMovement")
    MISL B 0 A_PlaySound("weapons/rocklx")
    MISL B 8 Bright A_Explode
    MISL C 6 Bright
    MISL D 4 Bright
    Stop
  }
}
```

## Related functions and wiki notes

- **`A_CheckCeiling`** — the inverse: jumps if the actor touches the ceiling (uses the same implementation strategy, as evidenced by the source comment "[GZ] Totally copied on A_CheckFloor").
- **`A_CheckSolidFooting`** — listed in the ZDoom wiki's "See also" section but **does not exist in Zandronum**. This is a ZDoom/GZDoom-family extension not present in the version this document targets.
