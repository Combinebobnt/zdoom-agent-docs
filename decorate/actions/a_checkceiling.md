# `A_CheckCeiling`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** ZDoom Wiki `A_CheckCeiling` (retrieved 2026-07-29, https://zdoom.org/w/index.php?title=A_CheckCeiling&oldid=42394) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3722-3733`, `:695-753` (`DoJump`), `src/thingdef/thingdef_states.cpp:377-397` (jump offsets) and `src/thingdef/thingdef_expression.cpp:2740-2757` (label lookup).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Action function on `AActor` (`DEFINE_ACTION_FUNCTION_PARAMS` in `src/thingdef/thingdef_codeptr.cpp`).

Jumps to a target state if the calling actor is touching or submerged into the ceiling. The check includes the actor's height in the calculation (comparing `z + height` against `ceilingz`).

## Signature

```decorate
state A_CheckCeiling (state target)
state A_CheckCeiling (int offset)
```

## Parameters

**`target`** (state label or frame offset)  
The jump destination. An unqualified state label (e.g., `"Death"`, `"CancelMovement"`) is resolved at run time against the class of the actor that owns the calling state (for a weapon state, the weapon), so a subclass's override of that label wins. A `Super::` or `Class::` qualified label is resolved at load time instead. On Zandronum, an unqualified label that doesn't exist prints `Jump target '<label>' not found in <class>` every time the action runs (the label is evaluated before the height test), and no jump happens.

An integer must be a non-negative literal. Offset N targets the state N after the calling one, counting every frame letter of the following lines. `0` means no jump. A negative offset is a parse error ("Negative jump offsets are not allowed"), and so is a positive offset on a line that defines more than one frame.

## Behavior

- Checks whether the calling actor's **top** (calculated as `z + height`) is at or above the ceiling (`ceilingz`).
- If the actor is **not touching the ceiling**, returns without jumping. Execution continues to the next action or frame in the current state.
- If the actor **is touching or above the ceiling**, performs the jump to the target state.
- On Zandronum, the call always sets the result of a CustomInventory state chain to false (`ACTION_SET_RESULT(false)`), whether or not it jumps.
- Unlike `A_CheckFloor` (which checks only `z <= floorz`), this function must add the actor's height, because `z` is the actor's bottom and it is the top that meets the ceiling.

## Network considerations

On Zandronum, the jump passes no client-update flags, so the server never sends clients a frame update for it. Each client runs the check itself against its own copy of the actor's `z`, `height` and `ceilingz` (the source comment is `[BB] Clients have ceiling information.`). If a client's position for the actor differs from the server's, the two can take different branches. `A_Jump`, `A_JumpIfHealthLower` and `A_JumpIfCloser`, by contrast, do send a frame update when the server jumps from the actor's own state.

## Examples

This rocket does not explode when it hits the ceiling, instead looping in a cancel-movement state:

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
    MISL B 0 A_CheckCeiling("CancelMovement")
    MISL B 0 A_PlaySound("weapons/rocklx")
    MISL B 8 Bright A_Explode
    MISL C 6 Bright
    MISL D 4 Bright
    Stop
  }
}
```

## See also

- `A_CheckFloor` — the complementary check for floor contact, using the same parameter semantics.
- Jump functions (`A_Jump`, `A_JumpIf*`) — conditional state jumps based on RNG or other conditions.
