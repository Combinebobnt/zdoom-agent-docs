# `void A_Fire(float spawnheight = 0)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_Fire` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_Fire&oldid=52463) + verified against the Zandronum source's `src/g_doom/a_archvile.cpp:44` and `wadsrc/static/actors/actor.txt:90`; corrections re-verified at `src/g_doom/a_archvile.cpp:32-42,52-80,112-115`, `src/network.cpp:1552-1555`, `wadsrc/static/actors/actor.txt:89,91` and `wadsrc/static/actors/doom/archvile.txt:68-86`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_Fire)` at `src/g_doom/a_archvile.cpp:44`.

Moves the calling actor to a point 24 map units in front of its `tracer` (along the tracer's own facing angle), with an optional vertical offset. Used by the Arch-Vile's flame (`ArchvileFire`) to keep the flame in front of the attack victim.

**Engine-family divergence: on Zandronum the reposition is server-side only.** Both engines do the same pointer and line-of-sight checks. Zandronum additionally returns early on clients and has the server send the new position to clients; UZDoom has no netcode here.

## Parameters

- **`float spawnheight`** — Vertical (Z-axis) offset in map units, added to the tracer's `z` (its bottom). Default: 0. Positive values move the actor upward, negative downward. Converted to `fixed_t` on Zandronum.

## Behavior

The function reads two pointers on the calling actor. When `A_VileTarget` spawns the flame it sets the flame's `tracer` to the victim and the flame's `target` to the Arch-Vile.

1. **`tracer`** — the actor the caller is placed in front of (the victim, for `ArchvileFire`).
2. **`target`** — the actor whose line of sight is checked (the Arch-Vile, for `ArchvileFire`). If `target` cannot see `tracer`, the function returns without moving.
3. **Offset calculation** — the caller is placed 24 map units along `tracer`'s angle from `tracer`'s position, at `tracer`'s `z` plus `spawnheight`.
4. **Silent early-returns** — the function returns immediately (no side effects, no error flag) if:
   - (Zandronum) The game is a network client or is playing back a client demo (`NETWORK_InClientMode()`). There is no `+CLIENTSIDEONLY` exception: even a client-side-only actor is never moved by `A_Fire` on a client.
   - Either `tracer` or `target` is null.
   - `target` cannot see `tracer` (`P_CheckSight(target, tracer, 0)` on Zandronum).

## Network behavior

On Zandronum the repositioning is **server-side only**. After moving the actor, a server sends its new x/y/z to all clients with `SERVERCOMMANDS_MoveThingExact`. Clients never compute the position themselves.

## Related functions

**`A_StartFire` and `A_FireCrackle`** are separate parameterless DECORATE actions (both engines) that play a sound and then run the same reposition with a height offset of 0:

- `A_StartFire` plays `vile/firestrt` on the body channel, then repositions.
- `A_FireCrackle` plays `vile/firecrkl` on the body channel, then repositions.

On Zandronum the sound is not behind the client-mode check, but it is also not sent over the network. Clients hear it because their own copy of the flame runs the action on state entry. The sound therefore plays even when the reposition is skipped (on a client, or when the sight check fails).

## Example

Zandronum's native `ArchvileFire` actor:

```text
actor ArchvileFire
{
    +NOBLOCKMAP +NOGRAVITY
    RenderStyle Add
    Alpha 1
    States
    {
    Spawn:
        FIRE A 2 Bright  A_StartFire
        FIRE BAB 2 Bright  A_Fire
        FIRE C 2 Bright  A_FireCrackle
        FIRE BCBCDCDCDEDED 2 Bright  A_Fire
        FIRE E 2 Bright  A_FireCrackle
        FIRE FEFEFGHGHGH 2 Bright  A_Fire
        Stop
    }
}
```

The flame spawns at the victim and is moved every frame to 24 units in front of the victim, along the victim's own facing angle (`tracer->angle`). If the Arch-Vile loses line-of-sight to the victim, the flame stops moving but keeps animating.

## See also

- **`A_Warp`** — more versatile repositioning action with per-axis offset control, collision checks, and interpolation options. Originally designed as a generalization of `A_Fire`'s orbit behavior.
- **`A_VileStart` / `A_VileTarget` / `A_VileAttack`** — the Arch-Vile's attack sequence. `A_VileTarget` spawns the flame, sets the Arch-Vile's `tracer` to it, and sets the flame's `tracer` (victim) and `target` (Arch-Vile) that `A_Fire` reads.
