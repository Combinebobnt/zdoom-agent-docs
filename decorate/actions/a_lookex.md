# `void A_LookEx(int flags = 0, fixed minseedist = 0, fixed maxseedist = 0, fixed maxheardist = 0, double fov = 0, state label = null)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_LookEx` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_LookEx&oldid=53757) + verified against the Zandronum source's `src/p_enemy.cpp:2068-2277` (`DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_LookEx)`), `src/p_enemy.cpp:1317-1323` (`P_IsVisible` FOV/close-range override), `src/p_enemy.cpp:1463,1537,1713,1895-1899` (`LOF_DONTCHASEGOAL` handling), `src/p_enemy.cpp:1951` (`A_Look`'s `Thing_SetGoal` handling), `wadsrc/static/actors/actor.txt:274` (declaration).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `src/p_enemy.cpp:2068` (`DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_LookEx)`).

Customizable target-acquisition action for monsters, similar to `A_Look` but allowing parameterized conditions for sight/sound detection, minimum/maximum ranges, and a custom state to jump to. If the target the monster heard is one it counts as a friend (`IsFriend()`, typically a friendly monster hearing its allied player), it does not stay idle. Failing a sight search for an enemy, it jumps to `label`, else its `SeeState`, and calls `A_Wander` only if it has neither. The `+STANDSTILL` flag suppresses this whole branch.

## Zandronum-specific: server-authoritative, same netcode gate as A_Look

**This is handled server-side and returns almost immediately in client mode** — before any target-finding logic runs, `A_LookEx` checks `NETWORK_InClientMode()` and, if true, does exactly one thing (update `visdir` for a stealth monster) and returns. On a listen/dedicated server or in single-player, the function runs its full target-acquisition logic every call, identical to vanilla ZDoom-family behavior.

The one line that *does* run on both server and client is the stealth-monster `visdir` update (`self->visdir = -1` when `MF_STEALTH` is set), duplicated in both the early client-mode branch and the normal server-side path further down. A review assuming "client mode = full no-op" would miss that stealth-monster facing state is intentionally touched on clients.

## Parameters

- **`int flags`** — Combination of zero or more `LOF_*` flags (combined with `|`). **All six flags defined in Zandronum** are available:
  - `LOF_NOSIGHTCHECK` (1) — Skip sight-based target detection; makes the monster blind to line-of-sight targets (sound-based targets still work unless `LOF_NOSOUNDCHECK` is also set).
  - `LOF_NOSOUNDCHECK` (2) — Skip sound-based target detection; makes the monster deaf to player noise. **Note:** This is different from the `AMBUSH` flag. An `AMBUSH` monster still hears, but a heard target only wakes it if it has a clear line of sight to that target (facing is not checked; `minseedist`/`maxseedist` apply). This flag disables sound checks entirely.
  - `LOF_DONTCHASEGOAL` (4) — Do not break idle animation to chase a patrol goal set by `Thing_SetGoal`. The monster can still acquire a target and transition to the see state. On Zandronum the flag only takes effect for an actor with a hate target set by `Thing_Hate` (the `P_LookForTID` path). Zandronum's rewritten `P_LookForPlayers` reads the flag but still falls back to the goal unconditionally. UZDoom honors it in both paths.
  - `LOF_NOSEESOUND` (8) — Do not play the actor's `SeeSound` when acquiring a target from this call.
  - `LOF_FULLVOLSEESOUND` (16) — Play the see sound at full volume globally (like a boss alert), instead of at normal distance-attenuated volume.
  - `LOF_NOJUMP` (32) — Acquire a target but do not transition to the see state; allows checking for a valid target and manually jumping based on conditions without automatically entering the see animation.

- **`fixed minseedist`** — Minimum sight distance in map units. If greater than 0, the monster will not see a player who is closer than this distance. Additionally, a nonzero value disables the close-range override that otherwise lets a monster notice a target outside its `fov` cone (see the distance divergence section below for that range per engine). So a value smaller than the actor's radius leaves a "blind spot" behind the monster. Default: 0 (no minimum).

- **`fixed maxseedist`** — Maximum sight distance in map units. The monster will not see any players farther away than this. Default: 0 (interpreted as unlimited, same as vanilla Doom). **Friendly monsters have a hard-coded cap of 1280 map units for performance reasons.**

- **`fixed maxheardist`** — Maximum hearing range in map units. The monster will not react to sounds from players farther away than this. Default: 0 (interpreted as unlimited).

- **`double fov`** — Field of view angle in degrees. Controls how wide an angle the monster must see the player within. Default: 0 (interpreted as 180°, the front half-circle, 90° to either side of facing). Smaller values create a narrower cone (player must be more centered). 360 produces all-around vision. An actor with `MF4_LOOKALLAROUND` skips the FOV test entirely, whatever value is passed. Internally stored and converted to angle units; fractional degrees are allowed.

- **`state label`** — The state to jump to when a valid target is acquired. If null or 0 (the default), falls back to the actor's `SeeState`. In the friendly wander branch (only without `+STANDSTILL`), a non-null label is jumped to in preference to `SeeState` and the `A_Wander` fallback.

## Behavior notes

- **`CF_NOTARGET` early-out.** If the heard sound target is a player with the `CF_NOTARGET` cheat flag set, the function returns without acquiring the target or changing state. That return also skips the sight search for that call. Players with `CF_NOTARGET` are separately skipped by the sight search itself.
- **`Thing_SetGoal` special case.** If the actor's map `special` field is `Thing_SetGoal` with `args[0] == 0`, the function consumes the special on its first call (`self->special = 0`) and sets up a patrol goal. `A_Look` does the same. The `LOF_DONTCHASEGOAL` flag can suppress the transition away from the current state (on Zandronum only for a `Thing_Hate` actor; see the flag above).
- **Friendly-monster path.** When the heard sound target passes `IsFriend()` and the actor lacks `+STANDSTILL`, the function first runs a `P_LookForPlayers` sight search. Zandronum always runs it all-around, ignoring facing. UZDoom runs it all-around only if `MF4_LOOKALLAROUND` is set. If that finds nothing, it jumps to `label`/`SeeState` or falls back to `A_Wander`. This branch ignores `LOF_NOJUMP`.

## Zandronum vs. ZDoom-wiki differences

The ZDoom wiki page uses modern GZDoom/UZDoom syntax (`double` parameters, named arguments like `label: "WakeUp"`, `class X : Parent` syntax, and ZScript-level structs) that is not valid in Zandronum DECORATE. Zandronum declares the four numeric parameters as `float` in `actor.txt` (DECORATE has no `fixed` type keyword); the engine reads the three distances as 16.16 fixed-point and `fov` as a double. Callers just pass numbers. Zandronum does not support named arguments in action calls. The wiki's example actors (`ImpairedZombie : ZombieMan`, `SecuritySoul : LostSoul`) would require rewriting with Zandronum DECORATE's `actor classname : parent {}` syntax and positional parameters to compile on this engine. The "See also" section referencing `Structs:LookExParams` and `LookForEnemies` describes ZScript-only constructs not available in Zandronum DECORATE.

## Engine-family divergence: no client/server authority split in UZDoom

The "Zandronum-specific: server-authoritative, same netcode gate as A_Look" section above
describes Zandronum's client/server authoritative model. UZDoom's `DEFINE_ACTION_FUNCTION(AActor,
A_LookEx)` (the UZDoom source's `src/playsim/p_enemy.cpp:2031-2213`) has no equivalent split: there
is no `NETWORK_InClientMode()`-style check anywhere in the function, nor anywhere in UZDoom's
source tree at all (GZDoom-family netcode does not use Zandronum's server-authoritative AI model).
`A_LookEx` runs its full target-acquisition logic — sound-target lookup, `Thing_SetGoal` handling,
friendly-monster wandering, `P_LookForPlayers`, state transitions and `SeeSound` playback — on
every machine in a UZDoom multiplayer session, not just a server/single-player instance. The one
behavior the existing Zandronum-specific section calls out as running unconditionally (the
stealth-monster `visdir` update) is simply part of that same unconditional execution on UZDoom,
not a special case carved out of a client-mode early return.

## Engine-family divergence: true Euclidean distance, not the octagonal approximation

Zandronum's `P_IsVisible` and the sound-target/`AMBUSH` distance checks inside `A_LookEx` itself
compute `dist` via `P_AproxDistance` — an octagonal approximation of 2D distance (`max(|dx|,|dy|) +
min(|dx|,|dy|)/2`), applied to every `minseedist`/`maxseedist`/`maxheardist` comparison. UZDoom's
equivalents (`P_IsVisible` and `A_LookEx`'s own sound-target/`AMBUSH` checks, both in the UZDoom
source's `src/playsim/p_enemy.cpp`) use `Distance2D()`, true Euclidean distance, throughout. The
two metrics agree exactly on the cardinal axes and diverge off-axis (the octagonal approximation
over-estimates true distance by up to about 11.8%, peaking around 26.6° off-axis rather than at
the 45° diagonal itself, where the over-estimate is a smaller ~6.1%), so a `minseedist`/
`maxseedist`/`maxheardist` value tuned to a specific in-game distance on Zandronum can trigger at a
measurably different true range on UZDoom depending on the target's approach angle.

A related, narrower difference in the same area: the FOV "react anyway if real close" override
(used when a target falls outside the `fov` cone but is close enough to notice regardless) compares
`dist` against the fixed constant `MELEERANGE` on Zandronum, but against the actor's own
`meleerange + radius` fields on UZDoom (`src/playsim/p_enemy.cpp:1284`, `an > (fov / 2)` branch) —
so an actor with a non-default `MeleeRange` or `Radius` gets a different close-range override
threshold on UZDoom than the same actor gets on Zandronum.

## See also

- [A_Look](a_look.md) — the non-parameterized default target-acquisition action.
- [Jump functions and network synchronization](../concepts/network-jump-synchronization.md) — network-aware strategies for state transitions triggered by target detection.
