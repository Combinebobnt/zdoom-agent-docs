# `RandomSpawner`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki Classes:RandomSpawner (retrieved 2026-07-31, oldid=52772) + verified against
Zandronum source `src/g_shared/a_randomspawner.cpp` and `src/p_enemy.cpp` (`CheckBossDeath`, `A_BossDeath`), and Zandronum's `src/g_shared/a_pickups.cpp` (Inventory respawn lifecycle). Pointer/flag/user-variable transfer behavior re-verified 2026-08-01 against the same file's `PostBeginPlay()`/`BeginPlay()` and `thingdef_parse.cpp`'s `ParseUserVariable`.
**Bucket:** `src/g_shared/a_randomspawner.cpp` (native C++ class `ARandomSpawner : public AActor`).

A built-in actor class that spawns exactly one randomly-selected actor from its `DropItem` list,
then removes itself from the game (or hides itself for potential map-reset restoration). The
RandomSpawner is meant to be subclassed, not used directly — define a new class inheriting from it
and populate the `DropItem` list with the actors to randomly choose from.

## Spawning mechanics

RandomSpawner resolves which actor to spawn in two separate phases for technical reasons (primarily
to ensure missile-spawned actors inherit their proper velocity):

### Phase 1: `BeginPlay()` — selection and configuration

When the RandomSpawner first initializes, it evaluates its `DropItem` list **once**, applying the
two optional per-item parameters: a spawn probability (0–255, defaulting to 255 "always") and a
weight (defaulting to 1) used to bias selection among all listed items. The selection process:

1. Sum all weights of eligible items (respecting `sv_nomonsters` / `level.nomonsters` filter).
2. Pick a random number from 0 to `total_weight - 1`.
3. Walk the list subtracting weights until reaching or passing the random number.
4. Roll the selected item's probability; if it fails, the spawner produces nothing (returns `'None'`).

If nested RandomSpawners reach a recursion depth of 32 (checked via `bouncecount`), the spawner
spawns an error-marker actor (`Unknown` class) instead and destroys itself.

**Zandronum bug (Infinite loop on `DropItem "None"`):** The weight-summing loop in Zandronum has a
brace-nesting bug: `di = di->Next` sits inside the `if (di->Name != NAME_None)` guard, so a
`DropItem "None"` entry in the list causes the iterator to hang on that item forever instead of
skipping it. This does not occur in UZDoom/GZDoom family, which refactored the loop with
unconditional iteration. Workaround: avoid listing `DropItem "None"` explicitly; omit it from the
list entirely or use the probability parameter to achieve near-zero spawn chance.

### Phase 2: `PostBeginPlay()` — spawning and boss tracking

Once the spawned actor's initial state is set up, RandomSpawner actually creates it at this point
(so missile-type spawns have proper velocity and target information). It transfers relevant state
to the spawned actor: angle/pitch/roll, SpawnPoint height offset, special/args, TID, velocity,
master/target/tracer pointers, and friendliness flags. The spawner then decides whether to keep
itself alive:

- **If the spawned actor has `MF2_BOSS` or `MF4_BOSSDEATH` flag set:** the spawner survives,
  stores the spawned actor in its `tracer` field, and monitors it in `Tick()`.
- **If the RandomSpawner's own class declares a `replaces` clause** (e.g., `actor BossReplacer :
  RandomSpawner replaces BaronOfHell`), the replaced class's default flags are checked — if those
  flags include `MF2_BOSS` or `MF4_BOSSDEATH`, the spawner survives for the same reason.
- Otherwise, the spawner calls `HideOrDestroyIfSafe()` and exits.

The second check is specifically the RandomSpawner subclass's own replacee (what *the spawner* is
replacing), not the spawned actor's replacee — this allows a RandomSpawner to be placed as a boss
replacement and automatically become a boss monitor even if it randomly chooses a non-boss spawn.

### Pointer, flag, and user-variable transfer to the spawned actor

Unlike `A_SpawnItemEx`, where pointer transfer is opt-in via `SXF_TRANSFERPOINTERS`, RandomSpawner
**unconditionally** copies `master`, `target`, and `tracer` from itself onto the spawned actor in
`PostBeginPlay()` (`newmobj->master = master; newmobj->target = target; newmobj->tracer = tracer;`),
plus `newmobj->CopyFriendliness(this, false)`. Practical implications:

- A minion spawned by RandomSpawner keeps whatever `master` the RandomSpawner itself had (`NULL`
  unless something set it beforehand via ACS, `A_SpawnItemEx`, etc.) — there is no equivalent of
  `A_SpawnItemEx`'s `SXF_SETMASTER` "walk up the missile's target chain to find an originator"
  logic; the raw pointer is copied as-is, with no originator resolution.
- For a missile-type spawn, `target`/`tracer` are already set correctly by `P_SpawnMissileXYZ` at
  construction time; the later unconditional copy re-assigns the same values, so there's no
  conflict for the missile case specifically.
- `health` is preserved only if it differs from the spawned class's own default
  (`if (health != SpawnHealth()) newmobj->health = health;`) — otherwise the spawned actor keeps
  its own class-default health.

**Actor-flag borrowing in `BeginPlay()` is onto the spawner itself, not the spawned actor.** Once
the drop item is selected, `BeginPlay()` does:
```
this->flags  |= (defmobj->flags  & MF_MISSILE);
this->flags2 |= (defmobj->flags2 & MF2_SEEKERMISSILE);
this->flags4 |= (defmobj->flags4 & MF4_SPECTRAL);
```
This borrows three flags from the *chosen class's defaults* onto the **RandomSpawner instance
itself** (`this`), not onto the eventual spawned actor — it exists purely so `PostBeginPlay()`'s
own `if (this->flags & MF_MISSILE ...)` check picks the missile-spawning path
(`P_SpawnMissileXYZ`) instead of a plain `Spawn()` call. The spawned actor gets its own
`MF_MISSILE`/`MF2_SEEKERMISSILE`/`MF4_SPECTRAL` flags from its own class definition regardless —
nothing needs to explicitly copy those three onto `newmobj`.

**User variables are never transferred.** `var int user_<name>;` fields are stored in per-class
extended memory (`PClass::Extend()`, an offset sized for *that specific class*), not in a registry
keyed by name. `PostBeginPlay()` copies known `AActor` fields by name (`target`, `tracer`,
`args[]`, etc.) — it does not, and structurally could not, generically copy a RandomSpawner
subclass's user-variable block onto an unrelated spawned class's differently-sized/offset
user-variable block. A user variable set on a RandomSpawner subclass instance (e.g. via
`A_SetUserVar` before it spawns, or a default in the subclass body) is simply lost when the
spawner replaces itself — it is never visible on the spawned actor. Note also that `ARandomSpawner`
itself is a **native** C++ class, so `var int user_<name>;` can only be declared on a
DECORATE-authored *subclass* of `RandomSpawner`, never on `RandomSpawner` directly — native classes
cannot declare user variables at all (`thingdef_parse.cpp`'s `ParseUserVariable` rejects this with
"Native classes may not have user variables").

### Boss-death tracking behavior (`Tick()`)

When a boss-tracking RandomSpawner's tracer dies (health ≤ 0), the spawner calls `A_BossDeath()`
with itself as the caller (`this`), then calls `HideOrDestroyIfSafe()` and exits.

**Critical detail on how `A_BossDeath` resolves the "boss type":** `A_BossDeath` internally uses
`self->GetClass()->ActorInfo->GetReplacee()` to determine which boss *species* the death counts as.
For a RandomSpawner:
- If it has a `replaces` clause, `GetReplacee()` returns the replaced class, so the death is
  attributed to that species (and classic Doom boss specials like `MAP07_SPECIAL` trigger correctly).
- If it has no `replaces` clause, `GetReplacee()` returns itself (the RandomSpawner class), so the
  death is attributed to the RandomSpawner species, not the spawned monster's type — classic
  hard-coded boss specials never match, and only MAPINFO `specialactions` entries that explicitly
  name the RandomSpawner subclass trigger.

The actual check for "all bosses dead" (`CheckBossDeath`) compares class identity **exactly** —
`other->GetClass() == actor->GetClass()` — so it counts living instances of the *spawner* class
itself, not the spawned monster species. This is appropriate because multiple RandomSpawner
subclasses placed in the map might each roll a different boss type, and the intended semantics are
"all spawner instances have dispatched their boss," not "all instances of this particular boss
type." **Zandronum addition:** The check excludes actors hidden via `HideOrDestroyIfSafe()` by
testing `STFL_HIDDEN_INSTEAD_OF_DESTROYED`, enabling map-reset game modes to temporarily hide
spawners without breaking the boss-death accounting.

## Interaction with item respawn (`sv_itemsrespawn`)

When a RandomSpawner rolls an `Inventory` actor (non-monster), the spawner destroys/hides itself
immediately after spawning. The spawned item is then a standalone actor whose own respawn cycle
(if applicable) will operate independently.

**The Inventory respawn cycle does not re-roll RandomSpawner selection.** When an item picked up
from the map is set to respawn, the engine calls `Hide()` on the same actor instance and later
`DoRespawn()`, which only randomizes position (via `SpawnPointClass`, not a re-roll of item
identity). The result: a map with a RandomSpawner that rolled "health potion" will respawn the
exact same health potion every time, never re-rolling to a different entry in the spawner's
DropItem list.

**Exception — dropped items never respawn:** Inventory items created by RandomSpawner have the
`MF_DROPPED` flag cleared during spawn (a RandomSpawner subclass that is *itself* spawned as
`MF_DROPPED` does not clear the flag on its item, preventing respawn). Items with `MF_DROPPED` set
return false from `GoAway()` and skip the `Hide()`/respawn path entirely, being destroyed instead
when picked up.

## Infinite recursion prevention

RandomSpawner can spawn other RandomSpawners. To prevent infinite nesting (e.g., a RandomSpawner
with `DropItem RandomSpawner` in its own list), the spawner tracks nesting depth via the
`bouncecount` field, incremented each time a RandomSpawner spawns another RandomSpawner. If depth
reaches 32 (the `MAX_RANDOMSPAWNERS_RECURSION` constant), `PostBeginPlay()` spawns an error
marker and destroys the spawner instead of continuing.

## Replacing a boss monster

To use a RandomSpawner subclass as a boss replacement (see "Boss-death tracking behavior" above),
declare it with the DECORATE `replaces` clause naming the boss class, e.g.
`actor BossReplacer : RandomSpawner replaces BaronOfHell { ... }`. This is what makes
`GetReplacee()` resolve to the boss class for `A_BossDeath`'s species check. Simply giving the
RandomSpawner subclass its own, unrelated DoomEd number does not establish this relationship —
`replaces` is the only mechanism that does.

## Zandronum-specific networking notes

The spawner itself is **server-side only** in networked games:
- `BeginPlay()` checks client mode and returns early, marking itself `NETFL_SERVERSIDEONLY` and
  freeing its network ID.
- `PostBeginPlay()` calls `SERVERCOMMANDS_SpawnThing()` to replicate the spawned actor to clients,
  plus angle/velocity sync if needed.

## See also

- [Creating monsters](../concepts/creating-monsters.md) — the `DropItem` property's general
  syntax and probability-roll mechanism, shared by every actor that can drop items.
