# Creating monsters

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** ZDoom Wiki "Creating new monsters or other complex items" (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=Creating_new_monsters_or_other_complex_items&oldid=52209), cross-checked against the Zandronum source's actor property definitions (`src/thingdef/thingdef_properties.cpp`), action-function implementations (`src/p_enemy.cpp`, `src/g_shared/a_action.cpp`), and shipped DECORATE definitions (`wadsrc/static/actors/doom/possessed.txt`). Flag semantics checked against `src/p_map.cpp`, `src/p_spec.cpp` and `src/p_things.cpp`; health, death-state and obituary handling against `src/p_interaction.cpp`; hitscan hit testing against `src/p_trace.cpp`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

This page covers what distinguishes a monster from other actors in DECORATE, the states and action functions that make one work, and how to create variations (shootable decorations, sound-triggered actors). It does not cover action-function semantics themselves — see the `actions/` directory for those — or the state-machine model, which is already covered in `state-machine.md`.

## What makes a monster: the Monster property

The DECORATE `Monster` property (not a flag, not a modifier — a keyword property recognized at actor-definition parse time) sets up a standardized flag bundle that characterizes the actor as a hostile monster in gameplay. It ORs the following flags into the actor's definition (from `thingdef_properties.cpp:1339-1346`):

**`flags` (first word):**
- `MF_SHOOTABLE` — the actor can be damaged by weapons and projectiles.
- `MF_COUNTKILL` — **this is the load-bearing flag**: kills of this actor count toward the level's kill count (visible in the automap, the "Kills" statistic, and any gameplay feature that tracks total monsters spawned/remaining). A friendly actor never counts, even with this flag (`actor.h:909`). A decoration that is shootable but should not count toward kills needs this flag off: define it *without* the `Monster` property (see "Creating shootable decorations" below), or clear the flag with `-COUNTKILL` after `Monster`.
- `MF_SOLID` — the actor blocks the movement of other solid actors and is blocked by them.

**`flags2` (second word):**
- `MF2_PUSHWALL` (DECORATE name `CANPUSHWALLS`) — the actor activates push-type line specials it bumps into. Whether a given line accepts a monster's push is decided by `P_TestActivateLine` (`p_spec.cpp:380-502`).
- `MF2_MCROSS` (DECORATE name `ACTIVATEMCROSS`) — the actor activates monster-cross line specials when it crosses them (`p_map.cpp:2192-2195`). It has nothing to do with `ML_BLOCKMONSTERS`. That line flag blocks non-projectile actors that lack `+NOBLOCKMONST`, monster or not (`p_map.cpp:731-741`). `PlayerPawn` sets `+NOBLOCKMONST`, so players pass.
- `MF2_PASSMOBJ` — height-aware actor collision: the actor can pass over or under another actor instead of being blocked by it at any height (`p_map.cpp:976-987`). The `compat_nopassover` compatibility option turns this off.

**`flags3` (third word):**
- `MF3_ISMONSTER` — marks the actor as a monster for engine checks such as the no-monsters spawn filter (`dmflags` "no monsters" or the map's no-monsters flag, `p_things.cpp:77-79`), the generic ice death fallback, and the `monster` console command's listing.

**`flags4` (fourth word):**
- `MF4_CANUSEWALLS` — the actor activates use-type line specials, subject to the same per-line check as pushes (`P_TestActivateLine`). A chasing monster that bumps into such a line tries to use it, which is how monsters open doors (`p_enemy.cpp:652-653`).

Removing or replacing the `Monster` property means losing all of these at once — which is why the alternative recipes (shootable decorations, sound-triggered markers) listed below explicitly set individual flags rather than relying on `Monster` to initialize them.

## Required and optional states

Monsters navigate a state machine; the engine looks up certain states by name and enters them based on events. See `state-machine.md` for the reserved label list and the generic dotted-label fallback — this section only covers what's specific to monsters.

### Required states

- **`Spawn:`** The idle/alert animation. **Must call `A_Look` or `A_Look2` repeatedly** to allow the monster to detect players. Without a call to one of these functions, the monster never transitions to the `See:` state and remains idle indefinitely. (See `actions/a_look.md` for action-function semantics.)
- **`See:`** The walking/pursuit animation, looping while the monster tracks a target. **Must call `A_Chase` or one of its variants (`A_FastChase`, `A_VileChase`, `A_ExtChase`)** to govern movement and target-loss detection. Without such a call, the monster cannot pathfind to or pursue its target. (`A_Wander` also moves the actor, but it roams without pursuing or attacking a target.)
- **At least one of `Missile:` or `Melee:`** — The attack sequence(s). A monster with no attack states cannot harm the player or other monsters. The attack sequence(s) typically call action functions like `A_FaceTarget`, `A_MeleeAttack`, `A_MissileAttack`, `A_CustomMissile`, or equivalent — see the `actions/` directory. After attacking, a `Goto See` is typical to return to pursuit.

### Optional but common states

- **`Pain:`** — Entered when the monster takes damage but does not die. Typically calls `A_Pain` and then `Goto See` to resume pursuit. If omitted, the monster takes damage silently and continues without interruption.
- **`Death:`** (or `Death.<damagetype>` for type-specific death animations) — Entered when the monster's health reaches zero. To leave a corpse, end the sequence on a frame with duration `-1`. That frame never advances, so the `Stop` after it is never reached (the shipped `ZombieMan` ends `POSS L -1` then `Stop`). A `Stop` reached after a finite-duration frame removes the actor. If `Death:` is omitted, the actor is removed by the engine with no visible animation.
- **`XDeath:` (the same label as `Death.Extreme:`)** — Alternate death sequence, typically for extreme means of death (e.g. gibbing). If omitted, the normal `Death:` sequence is used instead. The engine looks up `Death.Extreme` exactly and then looks up `Death` as a separate step (`p_interaction.cpp:898-903`).
- **`Raise:`** — Entered when the monster is resurrected by an Archvile or other resurrection mechanism. If omitted, the monster cannot be resurrected. See `state-machine.md`'s reserved-label list for the full set.

## Monster-specific properties and sounds

Beyond the `Monster` property itself, several properties are essential to a functional monster:

- **`Health`** — integer hit points. Should be positive. A monster spawned with `Health` 0 or less is not dead on spawn: it still spawns and runs its states, but damage code ignores any actor whose health is already at or below zero (`p_interaction.cpp:1190-1210`), so it can never be hurt or killed.
- **`Radius` and `Height`** — the actor's collision cylinder dimensions. Monsters should have these set correctly — they are used by collision detection, blocking checks, and weapon hit detection. A radius of 20 and height of 56 are typical for humanoid monsters.
- **`Speed`** — affects how fast the monster moves during pursuit (the actual rate depends on the action function used in `See:`). Speed 8 is a typical slow walk; higher values increase pursuit speed.
- **`PainChance`** — the probability (0–255) of entering the `Pain:` state on taking damage, or 0 to never enter Pain. Values like 200 are typical (entering Pain about 78% of the time).
- **`Mass`** — affects knockback from explosions and impacts (optional; defaults to a sensible value if not specified).
- **`SeeSound`, `AttackSound`, `PainSound`, `DeathSound`, `ActiveSound`** — sound lumps played at corresponding events. There is no engine default for a monster: an unset sound simply plays nothing (e.g. `A_Scream` does nothing without a `DeathSound`, `p_enemy.cpp:3331`), so omitting a line is a valid way to make that event silent.
- **`Obituary`** — the message shown when a player is killed by this monster (e.g. `"%o was killed by a zombieman."`). The `%o` token is replaced with the victim's name. `%k` means the killer's name only when the killer is a player; for a monster killer the engine substitutes the victim for the killer, so `%k` also prints the victim's name (`p_interaction.cpp:383`). If omitted, a generic message is used (`OB_DEFAULT`, `p_interaction.cpp:392`).
- **`DropItem "ItemType" [probability] [amount]`** — specifies an item the monster drops on death. `probability` defaults to 255 if omitted (`di->probability=255`, `thingdef_properties.cpp:775`) and is stored as a plain `int` with no clamp applied at parse time (`actor.h:691`, `thingdef_properties.cpp:780-781`). At drop time, `P_DropItem` rolls an 8-bit random value and drops the item if `pr_dropitem() <= chance` (`p_enemy.cpp:3471`) — since the roll can never exceed 255, **255 and 256 are functionally identical: both always drop**. This is the engine's own idiom (not a quirk to avoid); `256` is used for "always drop, no randomness" elsewhere in this source (e.g. weapon/ammo drops on player death pass `256` explicitly, `p_user.cpp:2113-2141`). **The wiki example's `DropItem "Clip" 256` is simply an unconditional drop, not an out-of-range value to be wary of.**

## Creating shootable decorations

A shootable decoration uses individual flags instead of the `Monster` property — allowing it to take damage without adding to the level's kill count:

```text
actor ExampleDecoration 9999
{
  Health 10
  Radius 16
  Height 32
  Speed 0
  +SHOOTABLE
  +SOLID
  +NOBLOOD
  States
  {
  Spawn:
    DECO A -1
    Stop
  Death:
    DECO B 5 A_Scream
    DECO C 5
    DECO D -1 A_Fall
    Stop
  }
}
```

`DECO` stands in for your own sprite. A sprite name must be exactly 4 characters, or the lump fails to parse (`thingdef_states.cpp:230-232`).

Key differences from a monster:
- **No `Monster` property** — you must use individual flags instead.
- **At least `+SHOOTABLE`** — allows the actor to be damaged.
- **No `+COUNTKILL`** — omitting this (the default) prevents kills from counting in statistics.
- **No `Spawn:`/`See:`/`Missile:` cycle** — shootable decorations typically have a simple idle state and a death state.
- **Optional `+NOBLOOD`** — prevents blood sprites from being spawned on impact.
- **Action functions are typically simpler** — `A_Scream`, `A_Fall`, `A_NoBlocking` (or the equivalent `A_Fall`, which does the same thing) for death sequences, rather than AI chase functions.

Note: `A_NoBlocking` and `A_Fall` are functionally identical in both engines — both are one-line wrappers calling `A_Unblock(self, true)` with no other logic (Zandronum: `g_shared/a_action.cpp:130-138`; UZDoom: `wadsrc/static/zscript/actors/actor.zs`). Either can be used; `A_NoBlocking` is common for monsters and `A_Fall` for decorations by convention only.

## Creating sound-triggered or conditional actors

An actor that reacts to seeing a player but does not become hostile — for example, an invisible marker that plays a sound — can be created by using a custom `See:` state that does *not* pursue or attack:

```text
actor SoundMarker 9998
{
  Health 1
  +NOBLOCKMAP
  +INVISIBLE
  States
  {
  Spawn:
    TNT1 A 2 A_Look
    Loop
  See:
    TNT1 A 1 A_PlaySound("custom/sound")
    Stop
  }
}
```

Key points:
- **`+NOBLOCKMAP`** — the actor is not placed on the blockmap and does not block anything.
- **`+INVISIBLE`** (optional) — the actor is never rendered. It is redundant here, since the `TNT1` sprite used in this example already draws nothing.
- **`See:` state without `A_Chase`** — the actor does not pursue when seen; it instead executes the custom action and returns to idle or stops.

This pattern is useful for one-off level effects (area triggers with sound, spawner markers) that detect players but take no hostile action.

## Open questions (unverified in this checkout — don't guess past these)

- How `Radius`/`Height` feed into weapon hit detection (as opposed to general movement/collision
  blocking, which is well-established) is traced on Zandronum only: a hitscan trace tests the
  actor's `Height` span and a square box of half-width `Radius` (`p_trace.cpp:541-574`). The
  UZDoom side wasn't traced for this page.

## Cross-references

- `state-machine.md` — covers the state block grammar, reserved label names, and the dotted-label fallback.
- `actor-definition-syntax.md` — covers the actor-definition header line and overall lump structure.
- `actions/a_look.md` — `A_Look` semantics and why it's essential in the `Spawn:` state.
- The `actions/` directory — individual action-function documentation for movement and behavior control (`A_Chase`, `A_Wander`, etc.).
