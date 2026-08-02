# FadeTo

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki (saved 2026-07-29, revision 47784), verified against the Zandronum source's `src/p_acs.cpp` lines 4273–4352 and 11949–11952
**Bucket:** Compiler builtin (`PCD_FADETO`)

**Signature:** `void FadeTo(int red, int green, int blue, fixed amount, fixed seconds)`

## Behavior

Initiates a screen-tint fade for the activator (or all players if no activator), transitioning to the specified color and intensity. The fade animates over the specified duration.

### Color and intensity

- **`red`, `green`, `blue`** (0–255): RGB components of the target color. Out-of-range values are silently clamped.
- **`amount`** (0.0–1.0): Intensity/alpha of the target color. Internally stored as a fixed-point value in the range `[0, FRACUNIT]` where `FRACUNIT = 65536`. Values outside this range are silently clamped. The actual fade begins from the activator's current screen-tint state (or transparent if none is active); FadeTo does not take a "from" color as a parameter.

### Duration and animation

- **`seconds`** (fixed, in seconds): Duration of the fade animation.
  - **0 or negative**: Fade is applied instantly (no transition).
  - **Positive**: A gradual fade is initiated over the specified duration; the engine creates an internal `DFlashFader` thinker to animate the transition frame-by-frame.

### Activator semantics

The function's behavior depends on how it is called:

- **With a valid player activator** (e.g., called from a `CROSS` special, a script explicitly bound to a player): The fade applies only to that player's view.
- **With an activator that is not a player** (e.g., called from an actor/monster, or after `SetActivator()` on a non-player thing): The function silently returns without effect — this is **not** documented on the ZDoom wiki.
- **With no activator** (e.g., called from an `OPEN` script, or after `SetActivator(0)`): The fade applies to all active players simultaneously.

### Multiplayer/netcode (Zandronum-specific)

- **On a server**: Instant fades (`seconds ≤ 0`) are synchronized to clients via `SERVERCOMMANDS_SetPlayerBlend`. Gradual fades are handled by an internal `DFlashFader` thinker that manages its own client replication.
- **On a client or in single-player**: Works locally without network overhead.

### The "decimal literal" requirement

The ZDoom wiki states that both `amount` and `seconds` "REQUIRE a decimal, or it will not work." This is imprecise but practically important:

- **At compile time**: The BCS compiler (`bcc`) accepts both integer and decimal literals for `fixed` parameters — `FadeTo(255, 0, 0, 1, 2)` compiles without error.
- **At runtime**: An integer literal like `1` is interpreted as a fixed-point value with no fractional part, i.e., `1 / 65536 ≈ 0.0000153`, effectively zero. The desired behavior (e.g., `amount = 1.0`, `seconds = 2.0`) requires explicit decimal notation in the source code.

Real-world usage typically employs decimal literals (`1.0`, `0.5`, `0.1`, etc.).

## Examples

```acs
script 100 ENTER
{
   // Fade to full-intensity red over 2 seconds
   FadeTo(255, 0, 0, 1.0, 2.0);
   Delay(35 * 2);

   // Fade to half-intensity black (darkening) over 2 seconds
   FadeTo(0, 0, 0, 0.5, 2.0);
}

script 101 NET
{
   // Instant full-screen red for all players
   FadeTo(255, 0, 0, 1.0, 0.0);
}
```

## See also

- `CancelFade` — cancels any active fade for the activator or all players.
- `FadeRange` — a two-color variant that fades *from* one color to another.
