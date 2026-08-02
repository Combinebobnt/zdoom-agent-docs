# `A_CheckCeiling`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_CheckCeiling` (retrieved 2026-07-29, oldid=42394) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3722-3733`.
**Bucket:** Action function on `AActor` (`DEFINE_ACTION_FUNCTION_PARAMS` in `src/thingdef/thingdef_codeptr.cpp`).

Jumps to a target state if the calling actor is touching or submerged into the ceiling. The check includes the actor's height in the calculation (comparing `z + height` against `ceilingz`).

## Signature

```decorate
state A_CheckCeiling (state target)
state A_CheckCeiling (int offset)
```

## Parameters

**`target`** (state label or frame offset)  
The jump destination. If a state label (e.g., `"Death"`, `"CancelMovement"`), the name is resolved in the calling actor's derived class's state table (virtual resolution). If an integer, the offset counts **frames in the current state line**, not instruction lines.

## Behavior

- Checks whether the calling actor's **top** (calculated as `z + height`) is at or above the ceiling (`ceilingz`).
- If the actor is **not touching the ceiling**, returns without jumping. Execution continues to the next action or frame in the current state.
- If the actor **is touching or above the ceiling**, performs the jump to the target state.
- The jump does not set any result value for inventory-pickup state chains (`ACTION_SET_RESULT(false)` is always called, per the source).
- Unlike `A_CheckFloor` (which checks only `z <= floorz`), this function must account for the actor's height because actors can be submerged into the ceiling from above.

## Network considerations

Unlike jump functions like `A_Jump` or `A_JumpIf*`, this action function's behavior depends only on static actor properties (`z`, `height`, `ceilingz`) that are replicated across the network, so ceiling state is consistent between server and clients. The source includes a comment `// [BB] Clients have ceiling information`, confirming that clients have the data needed to perform the check independently without waiting for server synchronization.

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
