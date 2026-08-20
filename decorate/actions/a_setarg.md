# `A_SetArg(int pos, int value)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_SetArg` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_SetArg&oldid=46120) + verified against
the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:5106-5117` and native declaration
`wadsrc/static/actors/actor.txt:300`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_SetArg)` — actor action on AActor.

Changes the calling actor's argument counter at a given index to a specified integer value.

## Parameters

- **pos**: Zero-based index into the actor's `args[5]` array. Valid range is 0–4. **Out-of-range
  values (negative or ≥ 5) are silently ignored** — the function returns without modifying
  anything (the (size_t) cast of a negative `pos` produces a very large unsigned value that
  fails the bounds check).

- **value**: The new integer value to store in the selected argument counter. No range limits are
  enforced; the value is stored as-is.

## Engine-family divergence

**No engine-family divergence in the function itself.** Both Zandronum and UZDoom/GZDoom have
this function with identical semantics and signature: same 0–4 bounds check on `pos` (out-of-range
values silently ignored, no error), same unrestricted storage of `value`.

**The surrounding netcode model does diverge**, which affects the scope of the caveat below.
UZDoom's source tree has no client/server authority split at all — no server-authoritative
broadcast mechanism and no clientside-vs-serverside execution distinction of the kind Zandronum
implements. UZDoom-family engines instead use a lockstep model where every peer runs the same
simulation from the same synchronized input stream, so `A_SetArg` writes `args[pos]` identically
and deterministically everywhere it runs — there is no "server's copy vs. client's copy" for it to
diverge between, and the desync risk described in the Zandronum-specific section below does not
exist on UZDoom.

## Zandronum-specific: multiplayer/netcode caveat

This entire section describes Zandronum's client/server architecture specifically and does not
apply to UZDoom — see "Engine-family divergence" above.

**No network replication.** Unlike functions such as `A_SetScale` or `A_ChangeFlag` that broadcast
changes to clients, `A_SetArg` modifies the local copy of `args[pos]` without any server-command
broadcast. In multiplayer:

- Server-side calls set the value on the server.
- Client-side calls set the value on the client (regardless of whether the actor is
  `+CLIENTSIDEONLY`).
- **The two copies can diverge** — subsequent reads of `args[pos]` may return different values on
  server vs. client if both sides have called `A_SetArg` with different values. This is
  particularly risky for conditionals like `A_JumpIf(Args[pos] > 0, ...)`, which can desynchronize
  behavior.

The server's copy is authoritative for actual gameplay and state changes; client-side reads are
cosmetic. Use `A_SetArg` carefully in networked actors (prefer server-authoritative actions for
shared state).

## Related functions

- **`A_CountdownArg(int arg[, str state])`** — operates on the same `args[5]` array, decrementing
  and checking for zero to trigger state changes or destruction; see that function's doc for how
  out-of-bounds args behave there.
- **`A_SetSpecial(int spec, int arg0, int arg1, int arg2, int arg3, int arg4)`** — sets the entire
  `special` field plus all five args in one call.

## Example

Setting an argument on entry to control actor behavior without map-editor intervention:

```text
ACTOR CustomDispenser : Actor
{
    Default
    {
        Radius 16;
        Height 32;
    }

    States
    {
    Spawn:
        DISP A 1
        {
            // Args[0] controls spawn count. Set to 10 on first call.
            A_SetArg(0, 10);
            A_SetArg(1, 5);  // Args[1] controls spawn interval in tics.
        }
        DISP A 5 A_SpawnItemEx("Ammo")
        Loop;
    }
}
```
