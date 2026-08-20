# `void A_Pain()`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_Pain` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_Pain&oldid=47251) + verified against Zandronum source's `src/p_enemy.cpp:3567` and UZDoom source's `src/playsim/p_enemy.cpp:3178`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** action function defined on `AActor` (callable from any actor's state table).

Plays a pain sound in response to damage. Behavior depends on whether the calling actor is a player or monster.

## No parameters

This action takes no parameters.

## Behavior

### For players (Zandronum)

Player pain sounds are **synthesized dynamically based on remaining health**, not read from a property:

1. **Health-tier selection**: Picks a base pain sound name by health threshold:
   - Health < 25: `*pain25`
   - Health < 50: `*pain50`
   - Health < 75: `*pain75`
   - Health >= 75: `*pain100`

2. **Three-step damage-type fallback chain**: Attempts to find a more specific sound based on the damage type that caused the pain:
   - First: `*pain<tier>-<LastDamageType>` (e.g., `*pain25-Fire` after fire damage)
   - Second: `*pain-<LastDamageType>` (e.g., `*pain-Fire` if the tier-specific variant doesn't exist)
   - Third: `*pain<tier>` (the base health-tier sound if no damage-type variant exists)

3. **Special morphing behavior**: Morphed players (those in a morphed form, e.g., via a morph power-up) fall through to the monster branch (see below) **unless** the morph actor has the `+NOMORPHLIMITATIONS` flag set. With `NOMORPHLIMITATIONS`, even a morphed player plays synthesized pain sounds based on the morphed form's health.

### For monsters and non-player actors

Monsters play the `PainSound` property — a single, statically-assigned sound per actor. There is no health-based variation or damage-type sensitivity. If `PainSound` is not set, no sound plays.

### Sound playback details

- **Channel**: `CHAN_VOICE` (interrupts any other voice-channel sound on the same actor, such as active sounds).
- **Volume**: 1.0 (full volume).
- **Attenuation**: `ATTN_NORM` (standard Doom distance falloff; audible beyond a certain range).
- **Client-side behavior**: Unlike several other combat actions, **A_Pain runs on both client and server with no early-return guard**. The function executes the same way in single-player, on the server in multiplayer, and on clients in multiplayer — with no special replication call to synchronize the sound across the network.

## Engine-family divergence

Both Zandronum and UZDoom implement the same core behavior (player health tiers, damage-type fallback chain, monster `PainSound` branch). However, the **player-branch gating condition differs**:

- **Zandronum**: Checks `self->player && (self->player->morphTics == 0 || (self->player->mo->PlayerFlags & PPF_NOMORPHLIMITATIONS))`. Morphed players (morphTics > 0) without `PPF_NOMORPHLIMITATIONS` use the monster branch.
- **UZDoom**: Checks `self->player && self->alternative == nullptr` (UZDoom's different morph representation). The `alternative` field is non-null only during morphing.

Additionally, **UZDoom calls `PlayerHurtMakeRumble()` as a virtual function for controller rumble feedback**, and passes the `CHANF_NORUMBLE` flag to suppress automatic rumble — neither mechanism exists in Zandronum. The actual sound selection and playback logic is otherwise identical.

## See also

- [`PainSound`](../notes/painsound.md) — the actor property that defines a monster's pain sound (not used for players, only for non-player actors or morphed players without `NOMORPHLIMITATIONS`).
- [Creating monsters](../concepts/creating-monsters.md) — monster-specific properties and state setup, including the `Pain:` reserved state called when an actor takes damage (in which `A_Pain` is typically invoked).
