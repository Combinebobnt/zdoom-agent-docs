# `A_JumpIfHealthLower (int health, state label)` / `A_JumpIfHealthLower (int health, int offset)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `A_JumpIfHealthLower` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_JumpIfHealthLower&oldid=44128) + verified against Zandronum source's `src/thingdef/thingdef_codeptr.cpp:792-808`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** AActor — callable from any actor's state table.

Jumps to a target state (or forward by an offset) if the calling actor's health is lower than a specified value.

## Parameters

- **`health`** (int) — Threshold health value. The jump occurs if the calling actor's `health` field is strictly less than this value (e.g., `A_JumpIfHealthLower(5000, "low")` jumps when health < 5000).
- **`label` or `offset`** — Target state label or state offset to jump to if the condition is met. Two overloads: pass a string (quoted in DECORATE) to jump to a named state, or an integer offset to jump forward by that many frame states from the current one.

## Wiki/engine divergence

The source ZDoom wiki describes an optional third parameter, `pointer` (int), to check a different actor's health instead of the calling actor (e.g., `AAPTR_TARGET`, `AAPTR_MASTER`). **This parameter does not exist in Zandronum 3.2.1** — attempting to pass it causes a parse error. Health is always checked on the calling actor (`self`) in Zandronum's implementation.

## Engine-family divergence: pointer parameter

UZDoom implements the third parameter the wiki describes, unlike Zandronum. UZDoom's `A_JumpIfHealthLower` (declared in the ZScript stdlib's `actors/checks.zs` as an `action state` function on `Actor`) takes `(int health, statelabel label, int ptr_selector = AAPTR_DEFAULT)`: it resolves `ptr_selector` to an actor via `GetPointer()` and compares *that* actor's `health` field against the threshold, jumping only if the resolved pointer is non-null and its health is lower. With the default `AAPTR_DEFAULT`, `GetPointer()` resolves to the calling actor itself, so single- and two-argument calls behave the same as Zandronum's self-only check; passing `AAPTR_TARGET`, `AAPTR_MASTER`, or another `AAPTR_*` selector lets the jump condition check a different actor's health, which Zandronum's implementation has no way to do.

## Zandronum-specific: network synchronization

UZDoom's implementation has no server/client authority split anywhere in its source tree — no `NETWORK_InClientMode` equivalent, no client-side/server-side actor-network-flag gate. `A_JumpIfHealthLower` runs the same health comparison and jump decision on every instance of the game unconditionally; there is no "clients don't know the actor's health so defer to the server" gate the way Zandronum's `NETFL_CLIENTSIDEONLY`/`NETWORK_InClientMode` check implements. The server-authoritative behavior described below under "Behavior notes" is Zandronum-only and does not apply on UZDoom.

## Behavior notes

- **Health threshold comparison is strictly less-than.** The jump occurs when `self->health < health`, not `<=`. A boss at exactly 5000 health will not trigger `A_JumpIfHealthLower(5000, "label")`.
- **Network synchronization.** In multiplayer, the jump decision is server-authoritative. In client-mode (when `NETWORK_InClientMode()` is true), the function's early-return gate checks `NETFL_CLIENTSIDEONLY` on the actor's network flags — if the actor is not client-side only, the function returns without executing, deferring the jump decision to the server. The comment in the source notes "Clients don't know what the actor's health is," so this is correct server-only behavior.
- **Health field semantics.** The `health` field is signed integer; actors can have negative health. The comparison is performed with standard integer semantics (e.g., an actor at -10 health will trigger the jump against any positive threshold).

## See also

- `A_JumpIf` — a more general conditional jump based on an ACS expression.
- `A_Jump` — unconditional jump to a state or offset (no condition).
