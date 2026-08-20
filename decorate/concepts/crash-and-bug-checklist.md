# Crash-and-bug checklist for DECORATE review

**Tier:** A (every claim here is a pointer to an independently source-verified finding; this file
adds no new unverified claims of its own beyond what the linked network-synchronization concept
file already states as architectural reasoning, not fact).
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** Cross-referenced from this repo's own verified `actions/`/`classes/`/`concepts/`
docs (compiled 2026-07-31, extended 2026-08-01) — not a wiki-intake page, no new source reading
beyond what's cited in each linked file.

A running, checklist-style index of **verified, recurring** crash/bug-causing patterns in Zandronum's
DECORATE layer — not a tutorial, not exhaustive. Each entry is one sentence of "what to
grep for" plus a link to the `actions/*.md`/`families/*.md`/`concepts/*.md` file with the full
verified mechanism (exact source lines, the fix/workaround, any contrast with the wiki). Read
*this* file to know what to look for in a diff; read the linked file before acting on a hit, since
the detail lives there, not here. Consult each linked file's divergence section for where UZDoom
behavior differs — several crash patterns in this checklist are Zandronum-specific.

## How to use this during a review

- Skim the category headers below against the diff being reviewed. Most entries are one specific
  action function or a small, related group — a hit usually means "check this one call site," not
  "audit everything."
- Follow the link for the actual verified mechanism before flagging or fixing anything — this file
  intentionally compresses each finding to a sentence, which is not enough to safely patch from.
- **If you verify a new crash-causing or behavioral-divergence pattern anywhere in this tree, add a
  line here too.** This file is a routing index over findings that already live in their own doc
  file, not a second source of truth — it only stays useful if newly-verified patterns get folded
  in the same session they're found, not on some later cleanup pass.

## Confirmed crash-causing patterns (verified against the Zandronum source)

1. **Zandronum-specific: A NULL-actor-pointer dereference hidden behind short-circuit `&&`/`||` evaluation order,
   `A_TakeInventory`/`A_TakeFromTarget` edition.** The shared take-inventory helper's infinite-ammo
   check reads `flags & TIF_NOTAKEINFINITE && ((dmflags & DF_INFINITE_AMMO) || (receiver->player
   ->cheats & CF_INFINITEAMMO)) && inv->IsKindOf(RUNTIME_CLASS(AAmmo))`. Whenever the
   `TIF_NOTAKEINFINITE` flag bit is set and the map's `DF_INFINITE_AMMO` dmflag is off, the `||`'s
   left operand is false, forcing evaluation of the right operand — `receiver->player->cheats` —
   *before* the trailing `inv->IsKindOf(AAmmo)` check even runs, and with no NULL guard on
   `receiver->player`. Calling either action with that flag on any non-player actor (a monster, a
   projectile, an actor reached via an `AAPTR_*` pointer redirect) crashes the engine, independent
   of what item is being taken. On UZDoom, the guard condition uses `player &&` before the
   `PowerInfiniteAmmo` check, preventing the dereference. See [A_TakeInventory](../actions/a_takeinventory.md).

2. **A bare-identifier read of a user variable (`var int user_<name>;`) declared on a `Weapon` or
   `CustomInventory` subclass, referenced from that same class's own state code.** Weapon and
   `CustomInventory` states run their action functions and inline expressions with `self` set to
   the *player pawn or receiving actor*, not the weapon/item itself (`state->CallAction(player->mo,
   player->ReadyWeapon)` in `src/p_pspr.cpp:257`; `State->CallAction(actor, this, ...)` in
   `ACustomInventory::CallStateChain`, `src/thingdef/thingdef_codeptr.cpp:135-181`, where `actor` is
   the toucher/Owner/dropper). A bare identifier's byte offset is resolved at *compile time* against
   the class whose DECORATE body is being parsed (the weapon/item class itself), but evaluated at
   *runtime* against whatever `self` actually is — so a `user_`-field declared on the weapon/item and
   read via a bare identifier in its own states reads memory at the pawn/receiver's address plus an
   offset sized for the weapon/item's own (differently-sized) class layout: unrelated/uninitialized
   data at best, an out-of-bounds heap read at worst if the weapon/item class's own size exceeds the
   pawn/receiver's. The write side (`A_SetUserVar`/`A_SetUserArray`) does not share this bug — it
   re-resolves the symbol at runtime against `self`'s actual class and fails safely (console message,
   no write) if that class lacks the field. See
   [User variables](user-variables.md#conditions-for-weapon-and-custominventory) for the full trace.

The action functions audited so far otherwise (`A_Chase`, `A_Jump`, `A_JumpIf`) turned up
behavioral/network bugs (see below) but no unguarded-crash pattern — don't treat the entries
above as exhaustive, only as what's been found *so far*.

## Patterns that look risky but are verified NOT to crash

1. **`A_Chase`'s target-pointer access in the fast-chase strafe block looks like an unguarded NULL
   dereference but isn't.** `actor->target` is read again inside the `CHF_FASTCHASE` strafing block
   (`src/p_enemy.cpp`) after the function's own earlier target-reacquisition block already returns
   on every NULL-target code path, and `CheckMeleeRange()` independently null-guards its own target
   argument too. See [A_Chase](../actions/a_chase.md).

## Wiki-documented flags that don't exist in Zandronum (silently inert, not a compile error)

1. **Zandronum-only: 6 of the 11 ZDoom-wiki `CHF_*` flags for `A_Chase` aren't defined anywhere in Zandronum's own
   DECORATE constants** (`CHF_NORANDOMTURN`, `CHF_NODIRECTIONTURN`, `CHF_NOPOSTATTACKTURN`,
   `CHF_STOPIFBLOCKED`, `CHF_DONTIDLE`, `CHF_DONTTURN` — only `CHF_FASTCHASE`, `CHF_NOPLAYACTIVE`,
   `CHF_NIGHTMAREFAST`, `CHF_RESURRECT`, and `CHF_DONTMOVE` are). Since `A_Chase`'s flags parameter
   is a bare `int`, nothing stops a mod from defining its own same-named constant (or passing a raw
   literal) to set one of the missing bits anyway — it will compile and run, but Zandronum's chase
   code has no case for that bit, so it's silently a no-op. All six of these flags are real and
   functional on UZDoom, fully implementing their wiki-documented behavior. A ZDoom-wiki page
   describing a DECORATE feature is not proof the feature exists in Zandronum — see
   [A_Chase](../actions/a_chase.md) for the exact bit values and the general engine-family-gate
   reminder in `../../shared/AUTHORING.md`'s "Engine scope" for why this class of gap keeps
   recurring across every ZDoom-wiki intake, not just this one flag set.

2. **Zandronum-only: A bitflag-parameter action function's wiki-documented constant list includes names Zandronum
   never defines.** `A_SpawnItemEx`'s `flags` parameter is the second confirmed case of this
   pattern (`A_Chase`'s `CHF_*` set above was the first): the ZDoom wiki lists `SXF_TRANSFERALPHA`,
   `SXF_TRANSFERRENDERSTYLE`, `SXF_SETTARGET`, `SXF_SETTRACER`, `SXF_NOPOINTERS`, `SXF_ORIGINATOR`,
   `SXF_TRANSFERSPRITEFRAME`, `SXF_TRANSFERROLL`, `SXF_ISTARGET`, `SXF_ISMASTER`, and `SXF_ISTRACER`
   — none of these are declared in Zandronum's `wadsrc/static/actors/constants.txt`, so passing one compiles
   and runs as an inert integer with no matching `case`/`if` in `InitSpawnedItem`. All eleven of
   these flags are real and wired on UZDoom, matching the wiki's documented behavior. See
   [A_SpawnItemEx](../actions/a_spawnitemex.md) for the full present/absent flag lists. **General
   reminder, not specific to either function:** any DECORATE action function whose parameter is a
   bitflag `int` (an `SXF_*`, `CHF_*`, `RGF_*`, `WARPF_*`, etc. family) needs its constant list
   checked against Zandronum's `wadsrc/static/actors/constants.txt` (or the matching native `enum` in the
   implementing `.cpp`) directly — never assume a wiki's flag table is Zandronum's flag table, even
   for a flag that "sounds like" a natural extension of ones already confirmed present.

## Non-obvious pointer/master transfer behavior in spawn functions

1. **Zandronum-only: `A_SpawnItemEx`'s `SXF_TRANSFERPOINTERS`-assigned `target` can be silently overwritten.** For
   a monster-based spawned actor whose "originator" (the calling actor, or — if the calling actor
   is a missile — whatever non-missile actor is at the end of its `target` chain) is a player-type
   actor with a live `player->attacker`, Zandronum's `InitSpawnedItem` unconditionally sets
   `mo->target = attacker` *after* `SXF_TRANSFERPOINTERS` already ran, with no flag to suppress it.
   On UZDoom, the `SXF_NOPOINTERS` flag can be passed to prevent this override entirely. A monster spawned 
   on Zandronum this way only keeps a `SXF_TRANSFERPOINTERS`-assigned `target` if the
   originating player currently has no attacker. See
   [A_SpawnItemEx](../actions/a_spawnitemex.md)'s `SXF_TRANSFERPOINTERS` and "Originator" sections.
2. **Zandronum-specific: `A_SpawnItemEx`'s `SXF_SETMASTER` behavior varies by engine.** On Zandronum,
   the flag sets `master` to the *originator*, not literally the calling actor, and does nothing at all
   when the originator is a player. A minion spawned from a projectile gets the projectile's shooter as its master (not the projectile itself); if the originator resolves to a player rather than a monster, `SXF_SETMASTER` has no effect on `master` on Zandronum — that code path only touches friendliness and `target`. On UZDoom, the flag is unconditional: `mo.master` is set to the originator regardless of whether the spawned actor is a monster or the originator is a player. See
   [A_SpawnItemEx](../actions/a_spawnitemex.md)'s `SXF_SETMASTER` entry for full details on both engines.
3. **`RandomSpawner` copies `master`/`target`/`tracer` unconditionally, with no opt-in flag and no
   originator resolution** — the raw pointers are copied as-is, unlike `A_SpawnItemEx`'s
   opt-in-plus-originator-aware model. It also **never transfers user variables** (`var int
   user_<name>;`) to the actor it spawns — per-class extended memory has no generic cross-class
   copy path, so a user variable set on a RandomSpawner subclass is lost when the spawner replaces
   itself. See [RandomSpawner](../classes/randomspawner.md)'s "Pointer, flag, and user-variable
   transfer" section.

## Network synchronization footguns in jump functions (`A_Jump`/`A_JumpIf*`)

Full background, all four causes, and the reasoning behind each fix live in
[Jump functions and network synchronization](network-jump-synchronization.md) — the four items
below are the reviewable, grep-for-this-in-the-diff form of that file's causes 1–4, kept here so a
DECORATE review doesn't need to open a second file to be reminded of them.

1. **RNG inside an `A_JumpIf` (or similar non-`A_Jump`) condition, on an actor that isn't
   `+CLIENTSIDEONLY`.** `A_JumpIf` evaluates its expression — including any embedded
   `random()`/`frandom()`/`random2()` call — *before* checking `NETWORK_InClientMode()`, the
   opposite order from `A_Jump`. Because unnamed random calls all draw from the single shared
   `pr_exrandom` stream, a wasted roll offsets every later unnamed-RNG expression evaluated on that
   client. **Fix/avoidance:** don't embed a random call in `A_JumpIf`'s (or a sibling
   `A_JumpIf*`'s) condition directly — split it into a pure state check via `A_JumpIf` landing in a
   target state that then calls `A_Jump` for the probability roll; `A_Jump`'s own gate is correctly
   ordered, so the roll only happens once server-authority is already confirmed. Not a crash and
   not a hard gameplay desync (no RNG-state consistency check exists between server and client in
   Zandronum) — the real cost is quietly less-reproducible `+CLIENTSIDEONLY` cosmetic randomness on
   that client. See [A_JumpIf](../actions/a_jumpif.md) for the full source trace.
2. **A `+CLIENTSIDEONLY` actor's `A_Jump`/`A_JumpIf*`-gated behavior affecting anything other than
   its own local visuals.** `rngseed` is never synchronized between server and client in live play
   (verified: the one mechanism that would, `D_ArbitrateNetStart`'s `NCMD_SETUP` handshake, has its
   only call site commented out), so a `+CLIENTSIDEONLY` actor's jump-driven RNG rolls are
   guaranteed to diverge from every other machine's copy of "the same" actor. **Fix/avoidance:**
   flag any diff where a `+CLIENTSIDEONLY` actor's jump outcome grants items, deals damage, affects
   score, or otherwise needs to look the same to more than one player — that decision has to be
   made server-side and broadcast instead. Purely cosmetic divergence (particle/debris variety,
   idle-animation branching) is fine and expected. See
   [A_Jump](../actions/a_jump.md)'s "Network considerations" section.
3. **A position/LOS/inventory-gated jump (`A_JumpIfCloser`, `A_JumpIfTargetInLOS`,
   `A_JumpIfInventory`, and siblings — not individually source-traced the way `A_Jump`/`A_JumpIf`
   were) whose design assumes the server and a client evaluate the same condition at the exact same
   tic.** The client's copy of another actor's position/inventory/etc. can lag the server's true
   value by up to one round-trip under Zandronum's predict-and-correct model, so an exact-tic
   assumption is inherently fragile, not a specific bug to patch. **Fix/avoidance:** design for a
   tic of visible lag on the client instead of an instantaneous jump the moment a networked value
   changes.
4. **A `+CLIENTSIDEONLY` actor spawned from inside a non-`+CLIENTSIDEONLY` actor's `A_JumpIf`-gated
   "skip" branch shows up unconditionally on every client, ignoring the gate entirely.** `A_JumpIf`
   not jumping means state advancement just continues to the next state — any action function
   between the (inert-on-client) jump and its target still runs there. `A_SpawnItemEx`/`A_SpawnItem`
   let a `+CLIENTSIDEONLY` spawn *type* through regardless of whether the *caller* is
   `+CLIENTSIDEONLY` (`NETWORK_ShouldActorNotBeSpawned` checks the spawn type's own flag too), so a
   parent's velocity/health/distance-gated cosmetic spawn fires on every client for the actor's
   entire lifetime, while the server (and singleplayer) correctly gate it. **Fix:** move the
   condition into the spawned `+CLIENTSIDEONLY` actor's own `Spawn:` state chain, passing whatever
   data the check needs (e.g. via `A_SpawnItemEx`'s `xvel`/`yvel`/`zvel` params) — a check on `self`
   there is on a genuinely `+CLIENTSIDEONLY` actor, so its own `A_JumpIf` gate evaluates correctly.
   See [Jump functions and network synchronization](network-jump-synchronization.md#cause-4-a-not-taken-branchs-own-side-effects-still-execute-on-every-client-verified-a_jumpif).
5. **Same wasted-roll shape as #1 above, outside the jump-function family: an attack action function
   with no `NETWORK_InClientMode()` guard of its own, whose per-shot spread/damage RNG rolls
   (`Random2()`/`%`-based rolls on a *named* `FRandom` stream, not just the shared `pr_exrandom`)
   execute unconditionally on both server and client before ever reaching the engine call that
   actually applies the effect.** `A_CustomBulletAttack` is the confirmed case: it calls
   `pr_cwbullet.Random2()`/`pr_cabullet()` for every bullet's spread and damage with no client-mode
   check, then hands the result to `P_LineAttack` (`src/p_map.cpp`), which has its *own* internal
   `NETWORK_InClientMode()` guard and silently returns `NULL` on a client (aside from the
   `cl_hitscandecalhack`/puff-prediction exceptions) — so the attack itself never double-applies,
   but the client has still burned rolls from those named streams that the server didn't need to
   make identically. Same low-severity shape as jump-function item #1 (no crash, no hard desync,
   just a quietly-diverged RNG stream on that client) but worth checking for on any action function
   that rolls RNG before an engine call, not only on jump/branch functions. See
   [A_CustomBulletAttack](../actions/a_custombulletattack.md)'s "Behavior" section.

## Position changes inside a pickup's touch handler get silently discarded

1. **A `Pickup:` chain (or any other code reached from `Touch()`) that moves the toucher via
   `SetActorPosition`/`P_MoveThing`-family calls, when the touch was triggered by the toucher
   walking into the item.** `P_TryMove` captures its destination `x`/`y` as locals before running
   `P_CheckPosition` (which is what invokes the touch, nested many frames deep), and unconditionally
   stamps `thing->x = x; thing->y = y;` back to that pre-touch destination once the check returns —
   discarding any position change made mid-touch, regardless of whether the pickup itself succeeded
   or failed (items are non-solid, so `P_CheckPosition` returns `true` either way). Only applies to
   movement-triggered touches, not `Use:` (reached from ticcmd handling, never from inside
   `P_TryMove`). See
   [Position change during pickup touch](position-change-during-pickup-touch.md) for the full
   call-stack trace and avoidance options.

## Confirmed replication bugs (not a crash, but a verified server/client desync)

1. **`A_SpawnDebris`'s spawned-actor velocity never reaches clients.** The server sets the debris
   actor's velocity locally, then syncs it to clients via `SERVERCOMMANDS_MoveThing(self, ...)` —
   which replicates the *calling* actor, not the newly-spawned debris — while the debris itself
   was only ever announced via `SERVERCOMMANDS_SpawnThing(mo)`, which carries type/position but no
   velocity. Debris follows a correct trajectory on the server and falls straight down (or sits
   still) on every client. See [A_SpawnDebris](../actions/a_spawndebris.md).
2. **`A_JumpIfMasterCloser`/`A_JumpIfTracerCloser` have no client-mode guard, unlike their sibling
   `A_JumpIfCloser`.** All three route through the shared `DoJumpIfCloser()` helper, but only
   `A_JumpIfCloser` early-returns under `NETWORK_InClientMode()`; the master/tracer variants
   evaluate the jump locally on clients using their own copy of the `master`/`tracer` pointer,
   which Zandronum does not reliably replicate. A client can reach a different jump decision than
   the server in the same tic on a non-`+CLIENTSIDEONLY` actor. See
   [A_JumpIfMasterCloser](../actions/a_jumpifmastercloser.md) and
   [A_JumpIfTracerCloser](../actions/a_jumpiftracercloser.md).

## When you find a new one

Add a line under the relevant list above (or a new category if it doesn't fit an existing one)
with a one-sentence mechanism and a link — and make sure the full verified detail lives in the
linked `actions/*.md`/`families/*.md`/`concepts/*.md` file, not only here. This file should never
be the only place a claim exists. Keep the entry project-agnostic per
`../../shared/AUTHORING.md`'s "Stay project-agnostic" rule: describe the mechanism in terms of the
function/engine call involved (as the entries above do), never the project code that happened to
surface it.

## Engine-family divergence

This file inherits each linked finding's own engine claim rather than making one of its own — check
the individual linked file if a future engine retarget calls a specific entry into question. Two
groups of entries diverge from each other in how well they generalize to UZDoom:

- **The "Network synchronization footguns" and "Confirmed replication bugs" sections have no UZDoom
  counterpart at all.** Every mechanism in those two sections is keyed to Zandronum's
  authoritative-server netcode — `NETWORK_InClientMode()`, the `SERVERCOMMANDS_*` replication calls,
  and the client/server split those imply. UZDoom's source has neither of those: no
  `NETWORK_InClientMode()` function and no `SERVERCOMMANDS_*` family exist anywhere in its
  codebase. UZDoom's own multiplayer model is architecturally different (peer-to-peer, not a
  distinguished authoritative server broadcasting to thin clients), so these entries' crash/desync
  *mechanisms* don't carry over — not because the underlying action functions are missing (most
  exist on both engines), but because the specific client-vs-server code path each entry describes
  isn't there to go wrong.
- **The remaining non-networking entries have divergent verification status on UZDoom.** 
  The `A_TakeInventory` NULL-actor-pointer dereference does not reproduce on UZDoom due to an explicit `player &&` guard in the infinite-ammo check, preventing the crash before it occurs. The `A_SpawnItemEx` pointer-transfer findings (both `SXF_TRANSFERPOINTERS` and `SXF_SETMASTER`) have been re-verified on UZDoom and found to diverge (UZDoom has `SXF_NOPOINTERS` to suppress the attacker override, and `SXF_SETMASTER` is unconditional on originator type). The six CHF_* and eleven SXF_* flags missing from Zandronum are all present and functional on UZDoom, fully implementing their wiki-documented behavior.
  The bare-identifier user-variable offset bug has not been re-verified for UZDoom, but UZDoom's compile-time detection of unsafe state calls (action functions accessing user variables in weapon/pickup states) prevents the crash from occurring by marking functions as unsafe at compile time and then detecting these in weapon/inventory-item states at load time, generating an error message and aborting the DECORATE load (via `CheckForUnsafeStates` in `src/scripting/thingdef.cpp`). This is an error-and-abort mechanism, not a warn-and-continue one. The `RandomSpawner` pointer-transfer findings have now been re-verified on UZDoom and confirmed to match: `master`/`target`/`tracer` are still copied unconditionally with no opt-in flag and no originator resolution, and user variables are still never transferred — though on UZDoom this is because `RandomSpawner` is itself a ZScript class (not the native C++ class it is on Zandronum) whose `PostBeginPlay()` copies only a fixed, explicit set of named fields, not because native classes categorically can't declare user variables. See [RandomSpawner](../classes/randomspawner.md#engine-family-divergence-randomspawner-is-a-zscript-class-on-uzdoom-not-native-c) for the full trace. Treat each entry as documented: link to the specific action/concept file for the current verification status.
