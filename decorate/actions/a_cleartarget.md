# `A_ClearTarget` (clear actor targeting fields)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_ClearTarget` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_ClearTarget&oldid=55260) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3915-3920`; network behavior per `src/p_enemy.cpp:1936-1945` (`A_Look`), `2470-2475` and `2571-2598` (`A_DoChase`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION(AActor, A_ClearTarget)` in `src/thingdef/thingdef_codeptr.cpp` — callable from any actor's state table.

Clears the calling actor's targeting references: target, sound target, and last target. Commonly used to make a monster "give up" pursuing its target after a period of time, allowing it to return to idle searching behavior.

## Signature

```text
void A_ClearTarget()
```

## Parameters

None.

## Behavior

When called, this action clears three actor fields:

1. **`target`** — The actor's current target, normally acquired via line-of-sight checks or direct damage. Cleared to `NULL`.
2. **`LastHeard`** — The actor's sound target, set when a noise alert reaches the actor (e.g., a player's weapon fire or `A_AlertMonsters`). Cleared to `NULL`.
3. **`lastenemy`** — The last enemy encountered, used by some AI logic for recent-threat awareness. Cleared to `NULL`.

After this call, the actor has no targeting pointers active. On the next state tic where an AI action (like `A_Look`) is called, the actor will resume searching for targets from scratch. `goal`, `tracer` and `master` are left alone, and the sector's own sound target is not cleared: under `COMPATF_SOUNDTARGET` or on a `+NOSECTOR` actor, `A_Look` reads `Sector->SoundTarget` instead of `LastHeard` (`src/p_enemy.cpp:1969-1970`), so the monster can hear the same noise-maker again at once.

## Typical usage

A common pattern is to use `A_ClearTarget` in a "give up" branch to reset monster aggression when a target has been out of range or sight for a set duration:

```text
Actor GiveUpImp : DoomImp
{
    var int user_chase;
    States
    {
    See:
        TROO A 0 A_SetUserVar("user_chase", user_chase + 1)
        TROO AABBCCDD 3 A_Chase
        TROO A 0 A_JumpIf(user_chase >= 20, "GiveUp")
        Loop
    GiveUp:
        TROO A 0 A_SetUserVar("user_chase", 0)
        TROO A 0 A_ClearTarget
        Goto Spawn
    }
}
```

The counter counts chase loops (24 tics each), not time out of sight, so this imp gives up after about 20 loops of chasing regardless of whether it can still see its target. The inherited `Spawn` state's `A_Look` can reacquire a target that is still visible straight away.

## Network behavior

**Zandronum multiplayer:** `A_ClearTarget` has no network-mode check and sends nothing to clients (`src/thingdef/thingdef_codeptr.cpp:3915-3920`). It clears the three fields on whichever side runs the state. Clients never track monster targets anyway: `A_Look` returns early in client mode (`src/p_enemy.cpp:1936-1945`), and `A_Chase` nulls `target` and `goal` on every client-side call (`src/p_enemy.cpp:2470-2475`). So only the server's call changes behavior. What clients do see is its consequence: on the server's next `A_Chase` with no target, a non-friendly monster looks for players all around, and if it finds none it drops to its idle (`Spawn`) state and the server sends that state change to clients (`src/p_enemy.cpp:2571-2598`).

## Engine-family divergence: Network behavior

**UZDoom has no client/server authority split for this action.** UZDoom's implementation (`wadsrc/static/zscript/actors/actor.zs:1169`) is a plain ZScript `A_ClearTarget()` method with no network-mode check at all — it unconditionally sets `target`, `lastheard`, and `lastenemy` to `null` on whichever peer runs it, every time. This mirrors the finding across this cohort: UZDoom's source tree has no client/server authority split anywhere (no `NETWORK_InClientMode`/`SERVERCOMMANDS_*` equivalents), unlike Zandronum's server-authoritative model described above. The three fields cleared are the same in both engines (UZDoom's `lastheard`/`lastenemy` correspond to Zandronum's `LastHeard`/`lastenemy`), so the core clearing behavior is unaffected. Only Zandronum's client/server split (clients never tracking monster targets, the server syncing the resulting idle state) is Zandronum-specific.

## Related actions

- **`A_Look`** — Searches for targets via sight checks; called after `A_ClearTarget` to resume idle searching.
- **`A_Chase`** — The main monster chase-and-attack action, which uses `target` and may reacquire it if line-of-sight is regained. Calling `A_ClearTarget` before a later `A_Chase` call forces the monster to look for a new target on the next chase decision; a non-friendly monster that finds none returns to its `Spawn` state.
- **`A_ClearLastHeard`** — Clears only `LastHeard`, leaving `target` and `lastenemy` alone.
- **`A_RearrangePointers`** — Can set `target` to null alone, without touching `LastHeard` or `lastenemy`.
