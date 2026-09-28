# `A_SetArg(int pos, int value)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_SetArg` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_SetArg&oldid=46120) + verified against
the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:5106-5117` and native declaration
`wadsrc/static/actors/actor.txt:300`; netcode section also from `src/sv_main.cpp:2887-2901`
(full-update args) and `src/thingdef/thingdef_codeptr.cpp:3523-3537` (`A_JumpIf` client guard).
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

**No broadcast on the call.** Unlike functions such as `A_SetScale` or `A_ChangeFlag` that
broadcast changes to clients, `A_SetArg` modifies the local copy of `args[pos]` without any
server-command broadcast. It also has no client-mode guard. In multiplayer:

- It runs on whichever side executes the state: the server, and a client too whenever the
  client's copy of the actor runs that state (regardless of whether the actor is
  `+CLIENTSIDEONLY`).
- **The two copies can diverge.** This happens when the written value depends on data the two
  sides don't share, or when the state runs on only one side.
- Nothing resends args because of `A_SetArg`. A client that joins later does receive the
  server's current args in its full update, for non-missile actors with any nonzero arg. A
  client already in the game never learns of a server-only `A_SetArg` unless some other path
  (e.g. ACS `SetThingSpecial`) sends the args again.

A divergent client copy does not change branching through `A_JumpIf(Args[pos] > 0, ...)` for a
normal actor. On a client, `A_JumpIf` returns without jumping unless the actor is
client-side only (`+CLIENTSIDEONLY`, or spawned by the client itself, e.g. via
`SXF_CLIENTSIDE`), and the server's jump sends clients the new frame. The client copy matters
for client-side-only actors and for any other client-side read of `args`. Keep state that clients
must agree on in server-authoritative actions.

## Related functions

- **`A_CountdownArg(int argnum[, state targstate])`** — operates on the same `args[5]` array, decrementing
  and checking for zero to trigger state changes or destruction; see that function's doc for how
  out-of-bounds args behave there.
- **`A_SetSpecial(int spec, int arg0, int arg1, int arg2, int arg3, int arg4)`** — sets the entire
  `special` field plus all five args in one call.

## Example

Setting an argument on spawn so the actor works without map-editor args. Plain DECORATE: no
`Default { }` block (that is ZScript) and one action per frame, since Zandronum's DECORATE has
no `{ }` action blocks. The first Spawn frame needs `NoDelay`, or its action is skipped when the
actor spawns.

```text
ACTOR CustomDispenser
{
    Radius 16
    Height 32
    States
    {
    Spawn:
        DISP A 0 NoDelay A_SetArg(0, 9)    // A_CountdownArg fires on the 10th call
    Dispense:
        DISP A 35 A_SpawnItemEx("Clip", 0, 0, 16)
        DISP A 0 A_CountdownArg(0, "Empty")
        Loop
    Empty:
        DISP B -1
        Stop
    }
}
```
