# `A_CheckFloor`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki `A_CheckFloor` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_CheckFloor&oldid=43633) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3702-3713` (jump-offset parsing: `src/thingdef/thingdef_states.cpp:377-397`; `A_JumpIfHealthLower`'s jump: `src/thingdef/thingdef_codeptr.cpp:805`) and UZDoom's `wadsrc/static/zscript/actors/checks.zs:172-175`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Action function on `AActor` (`DEFINE_ACTION_FUNCTION_PARAMS` in Zandronum `src/thingdef/thingdef_codeptr.cpp`; ZScript native in UZDoom `wadsrc/static/zscript/actors/checks.zs`).
**Source excerpt:** This file quotes Zandronum engine source verbatim; see [LICENSE](../../LICENSE) §3 for Zandronum's license terms.

Jumps to a target state if the calling actor is standing on or submerged into the floor.

## Signature

```decorate
state A_CheckFloor (state target)
state A_CheckFloor (int offset)
```

## Parameters

**`target`** (state label or frame offset)  
The jump destination. If a state label (e.g., `"CancelMovement"`, `"DeathFade"`), the name is resolved in the calling actor's derived class's state table (virtual resolution). An integer must be a non-negative literal: `N` jumps to the state `N` after the calling one (each frame is one state), and `0` means no jump. A negative offset is a parse error ("Negative jump offsets are not allowed"), and so is a positive offset on a line that defines more than one frame.

## Behavior

- Compares the actor's Z position against the `floorz` (the floor surface height at the actor's current XY location).
- If `self->z <= self->floorz`, the actor is either resting on the floor or submerged *below* the floor surface — the jump is performed.
- If `self->z > self->floorz`, the actor is above the floor (in the air, or in water above floor level). Execution continues without jumping. An actor standing on a raised sector floor has `z == floorz` there, so it does jump.
- On Zandronum the function always sets the state-call result to false (`ACTION_SET_RESULT(false)`), so in a CustomInventory state chain the call never counts as success, whether or not it jumps.

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

The `ACTION_JUMP(jump, 0)` call passes no client-update flags, so the server never sends clients a frame update for this jump. The function also has no client-mode early return, so a client that runs the state evaluates the check against its own copy of the actor. The source comment's reasoning is that clients have floor information. By contrast, `A_JumpIfHealthLower` returns early on clients (unless the actor is client-side only) and passes `CLIENTUPDATE_FRAME`, because clients don't know the actor's health. With that flag, a jump from the actor's own state sends a frame update and a jump from a weapon or flash state sends a weapon state jump; a CustomInventory chain sends nothing.

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
- **`A_CheckSolidFooting`** — listed in the ZDoom wiki's "See also" section but **does not exist in Zandronum**. UZDoom's source has no such function either.
