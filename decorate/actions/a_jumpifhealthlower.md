# `A_JumpIfHealthLower (int health, state label)` / `A_JumpIfHealthLower (int health, int offset)`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `A_JumpIfHealthLower` (retrieved 2026-07-31, oldid=44128) + verified against Zandronum source's `src/thingdef/thingdef_codeptr.cpp:792-808`.
**Bucket:** AActor — callable from any actor's state table.

Jumps to a target state (or forward by an offset) if the calling actor's health is lower than a specified value.

## Parameters

- **`health`** (int) — Threshold health value. The jump occurs if the calling actor's `health` field is strictly less than this value (e.g., `A_JumpIfHealthLower(5000, "low")` jumps when health < 5000).
- **`label` or `offset`** — Target state label or state offset to jump to if the condition is met. Two overloads: pass a string (quoted in DECORATE) to jump to a named state, or an integer offset to jump forward by that many frame states from the current one.

## Wiki/engine divergence

The source ZDoom wiki describes an optional third parameter, `pointer` (int), to check a different actor's health instead of the calling actor (e.g., `AAPTR_TARGET`, `AAPTR_MASTER`). **This parameter does not exist in Zandronum 3.2.1** — attempting to pass it causes a parse error. Health is always checked on the calling actor (`self`) in Zandronum's implementation.

## Behavior notes

- **Health threshold comparison is strictly less-than.** The jump occurs when `self->health < health`, not `<=`. A boss at exactly 5000 health will not trigger `A_JumpIfHealthLower(5000, "label")`.
- **Network synchronization.** In multiplayer, the jump decision is server-authoritative. In client-mode (when `NETWORK_InClientMode()` is true), the function's early-return gate checks `NETFL_CLIENTSIDEONLY` on the actor's network flags — if the actor is not client-side only, the function returns without executing, deferring the jump decision to the server. The comment in the source notes "Clients don't know what the actor's health is," so this is correct server-only behavior.
- **Health field semantics.** The `health` field is signed integer; actors can have negative health. The comparison is performed with standard integer semantics (e.g., an actor at -10 health will trigger the jump against any positive threshold).

## See also

- `A_JumpIf` — a more general conditional jump based on an ACS expression.
- `A_Jump` — unconditional jump to a state or offset (no condition).
