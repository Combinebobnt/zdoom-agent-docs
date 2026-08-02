# Crash-and-bug checklist for ACS/BCS review

**Tier:** A (every claim here is a pointer to an independently source-verified finding; this file adds no new unverified claims of its own).
**Engine:** Zandronum 3.2.1 (inherits each linked finding's own `Engine:` stamp; check the individual file if a future engine retarget is in question).
**Provenance:** Cross-referenced from this repo's own verified `functions/`/`families/` docs (compiled 2026-07-29) — not a wiki-intake page, no new source reading beyond what's cited in each linked file.

A running, checklist-style index of **verified, recurring** crash/bug-causing patterns in this
fork's ACS/BCS layer — not a tutorial, not exhaustive. Each entry is one sentence of "what to
grep for" plus a link to the `functions/*.md`/`families/*.md` file with the full verified
mechanism (exact source lines, the fix/guard, any contrast with the wiki). Read *this* file to
know what to look for in a diff; read the linked file before acting on a hit, since the detail
(exact conditions, which argument, which script types are affected) lives there, not here.

## How to use this during a review

- Skim the category headers below against the diff being reviewed. Most entries are one specific
  function or a small family, not a whole subsystem — a hit usually means "check this one call
  site," not "audit everything."
- Follow the link for the actual verified mechanism before flagging or fixing anything — this
  file intentionally compresses each finding to a sentence, which is not enough to safely patch
  from.
- **If you verify a new crash-causing pattern anywhere in this tree, add a line here too.** This
  file is a routing index over findings that already live in their own doc file, not a second
  source of truth — it only stays useful if newly-verified patterns get folded in when they're
  found, the same session they're found, not on some later cleanup pass.

## Confirmed crash-causing patterns (verified against the Zandronum source)

1. **NULL actor pointer dereferenced with no guard.** `PlayActorSound(tid=0, ...)` called from a
   script with no activator (`OPEN`/`ENTER`/`RESPAWN`/`DISCONNECT`, etc.) crashes the engine: the
   shared `PlaySound`/`PlayActorSound` case sets `spot = activator` with no NULL check
   (`p_acs.cpp:6501-6505`), and `PlayActorSound`'s extra `GetActorSound(spot, ...)` call
   dereferences it unconditionally (`p_acs.cpp:5332-5348`) — no equivalent to `PlaySound`'s later
   `S_Sound(AActor*,...)` NULL check exists on this path. See
   [PlayActorSound](../functions/playactorsound.md). **The identical-looking `tid=0` convention on
   sibling functions is not uniformly safe** — see the "looks risky but isn't" section below for
   which siblings *are* guarded.

2. **NULL `char*` from a getter appended/measured with no guard (`strlen(NULL)`).**
   `GetTeamProperty(team, TPROP_TeamItem|TPROP_WinnerTheme|TPROP_LoserTheme)` with an invalid
   `team` crashes the caller: the underlying getters (`TEAM_GetTeamItemName`,
   `TEAM_GetIntermissionTheme`) `return NULL;` for an invalid team, and
   `FString::operator+=(const char*)` calls `strlen(tail)` with no NULL check
   (`zstring.cpp:326-333`) — a real fork bug, not fail-safe like the sibling `TPROP_Name`. See
   [GetTeamProperty](../functions/getteamproperty.md).

3. **Lookup-miss pointer dereferenced with no guard (unresolved name/number).**
   `RequestScriptPuke`/`NamedRequestScriptPuke` with a typo'd or nonexistent script name/number
   crashes the client: `StaticFindScript`'s result is dereferenced (`scriptdata->Flags` at
   `p_acs.cpp:1718`) with no NULL check, unlike sibling checks (`ACS_IsScriptPukeable`,
   `ACS_IsScriptClientSide`) which do NULL-check their own lookup first. See
   [RequestScriptPuke](../functions/requestscriptpuke.md).

4. **Unvalidated index passed straight into an engine array/lookup.** `LumpGetInfo` with
   `infoType` `SIZE`/`NAMESPACE`/`WAD` passes `lumpNum` directly into
   `Wads.LumpLength`/`GetLumpNamespace`/`GetWadnumFromLumpnum` with no range check
   (`p_acs.cpp:8489-8517`) — only the `NAME` branch bounds-checks first. An out-of-range lump
   number can crash the game; this corroborates (doesn't just repeat) the wiki's own warning. See
   [Lump I/O family](../families/lump-io.md).

5. **A raw int result misused as a string-table index.** `GetActorSectorLocation(tid, point=true)`
   returns a bare `unsigned int`/`-1` index — it never registers anything in
   `GlobalACSStrings` on that branch, despite the wiki implying a string comes back. Treating the
   result as `str` (e.g. logging it directly) reads whatever the engine's string table happens to
   hold at that raw index — undefined, possibly a crash. See
   [GetActorSectorLocation](../functions/getactorsectorlocation.md).

6. **NULL activator pointer dereferenced with no guard, `LineAttack` edition.** `LineAttack(tid=0,
   ...)` called from a script with no activator (`CLIENTSIDE`/`UNLOADING`, etc.) crashes the
   engine: `tid=0` resolves to the activator with no NULL check before `P_LineAttack` dereferences
   it (`t1->z` at `p_map.cpp:4231`). Same family of bug as pattern 1 (`PlayActorSound`), different
   function — **the `tid=0`-means-activator convention keeps being unsafe on some functions and
   safe on others; there is no shortcut, check each one.** See [LineAttack](../functions/lineattack.md).

## Patterns that look risky but are verified NOT to crash

Flagging these during review is a false positive — useful to know so review time goes to the
categories above instead.

- **A `tid=0`/no-activator call is not automatically unsafe.** `ActivatorSound`,
  `LocalAmbientSound`, `SoundSequenceOnActor`, `SoundSequence`, `PlaySound`, and `StopSound` all
  either explicitly guard `activator == NULL` in the engine source, or their entire downstream
  call chain only does pointer-identity comparisons that never dereference. Only
  `PlayActorSound` (pattern 1 above) actually crashes on this input — **don't pattern-match
  "sibling function, same `tid=0` convention" into an assumed guard or an assumed crash; check the
  specific function's own engine source.** See [ActivatorSound](../functions/activatorsound.md),
  [LocalAmbientSound](../functions/localambientsound.md),
  [SoundSequenceOnActor](../functions/soundsequenceonactor.md),
  [SoundSequence](../functions/soundsequence.md), [PlaySound](../functions/playsound.md),
  [StopSound](../functions/stopsound.md).
- **Divide-by-zero / modulus-by-zero terminate the script, not the engine.** Both print a console
  message and remove only that script instance (`SCRIPT_PleaseRemove`) — no engine crash, no
  corrupted state. See [Operators](operators.md), [Integer arithmetic](integer-arithmetic.md),
  [FixedDiv](../functions/fixeddiv.md) (which additionally saturates instead of dividing by
  zero at all).
- **An invalid/expired string handle degrades safely, it doesn't crash.** `StrCmp`/`StrIcmp`
  substitute `""` for an invalid handle (`p_acs.cpp:6624-6626`, comment: `// Don't crash on
  invalid strings.`); `StrLen` returns `0` with a one-time console warning. See
  [StrCmp](../functions/strcmp.md), [StrLen](../functions/strlen.md).
- **Deep/runaway recursion doesn't crash the engine in this fork, contrary to the ZDoom wiki's own
  claim.** The shared 4096-word VM stack has a bounds check that catches overflow first, prints a
  console message, and removes only the offending script instance — the wiki's "will eventually
  crash the game" does not hold here. See [User-defined functions](user-functions.md).

## Declared-but-unimplemented extension functions (compile fine, silently no-op — not a crash, but a very common footgun)

Not a crash pattern, but the single most commonly hit "why isn't this working" bug in this fork:
`zt-bcc`'s `zcommon.bcs` declares an ACSF index for a function that upstream ZDoom has, `bcc`
compiles a call to it without complaint, but Zandronum's `EACSFunctions` enum/`CallFunction`
switch never got the matching `case` — so at runtime it falls through to `default: return 0;`
with **no compiler error, no console warning, no crash**. The call looks exactly like a
successful "0 actors affected"/"nothing to do" result. Several of these cluster in the same
never-backported index ranges (92-99 and 200-209), so if a review turns up one gap in a range,
check the neighboring indices too.

- **`SetActorFlag` (-202, `int SetActorFlag(int, str, bool)`) — silently does nothing.** No
  `ACSF_SetActorFlag` case exists on Zandronum's `master` branch (the 3.2.1 target); the implementing
  commit was written for upstream but only merged into unrelated Zandronum branches
  (`g2.2`/`gz-zscript`), never `master`/3.2.1. **This one in particular gets reached for often** —
  it's the obvious-looking way to flip a named actor flag from ACS, and there's no working
  replacement for the general case (`CheckFlag` only reads). **Verified workaround:** a
  `CustomInventory`-derived DECORATE item with only a `Pickup:` state calling `A_ChangeFlag`,
  given via `GiveActorInventory`/`GiveInventory` — see [SetActorFlag](../functions/setactorflag.md)'s
  "Verified workaround" section for why this specific call chain (not a general DECORATE-pickup
  pattern) actually applies the flag to the target actor rather than the item.
- **`SpawnParticle` (-96) and `GetMaxInventory` (-93)** — same never-backported ZDoom 92-99
  extension-function range. See [Spawning family](../families/spawning.md),
  [Inventory family](../families/inventory.md).
- **`CheckClass` (-200, `bool CheckClass(str)`) — silently always returns `false`.** No
  `ACSF_CheckClass` case exists on Zandronum's `master` branch (the 3.2.1 target) — same
  never-backported 200-203 range as `SetActorFlag` above (its immediate neighbors `DamageActor`
  (-201) and `SetTranslation` (-203) are dead for the same reason). Use `CheckActorClass` (-27)
  instead, which is implemented and working. See [CheckClass](../functions/checkclass.md).
- **`ZDoom_Floor`/`ZDoom_Round`/`ZDoom_Ceil` (-207/-208/-209), `StrArg` (-206), and
  `SetSectorDamage` (-94)** — same pattern, different never-backported ranges (200-209, and -94
  again). See [ZDoom math-function stubs](../families/zdoom-math-stubs.md),
  [StrArg](../functions/strarg.md), [SetSectorDamage](../functions/setsectordamage.md).

## Implemented functions that silently drop a parameter under specific conditions (not a crash, not dead — just conditionally wrong)

Different from the "declared-but-unimplemented" list above: the function is real and does
something, but one parameter is silently ignored on a subset of call patterns instead of every
call — easy to miss in testing if the tested case happens to be one where it works.

- **`LineAttack`'s `pufftid` (index -60) is dropped whenever the hitscan doesn't produce a
  persistent puff — most commonly, hitting a normal actor that bleeds.** `P_LineAttack` only
  returns a puff pointer `pufftid` can attach to when hitting a wall/floor, hitting nothing (with
  an `MF3_ALWAYSPUFF` puff type), or hitting an actor that's `MF_NOBLOOD`/`MF2_INVULNERABLE`/
  `MF2_DORMANT`, or whose puff class sets `MF3_PUFFONACTORS` (`p_map.cpp:4425-4435`). Otherwise —
  the default case of a normal bleeding actor hit by a puff type without `MF3_PUFFONACTORS` (e.g.
  the default `BulletPuff`) — the only puff spawned is a `PF_TEMPORARY` one created solely to serve
  as the damage inflictor, which gets `Destroy()`ed and nulled out before `P_LineAttack` returns
  (`p_map.cpp:4464-4472, 4546-4554`); the caller's `pufftid` guard (`if (puff != NULL && ...)`,
  `p_acs.cpp:6453, 6467`) then sees `NULL` and never assigns it. No error, no warning — the same
  call silently works or doesn't depending on the target's flags and the puff class's own flags.
  See [LineAttack](../functions/lineattack.md).

## Functions that silently revert their own effect and return a bool nobody checks

1. **`SetActorPosition`'s call-site result is very commonly discarded, and a failed call is
   silent by design.** `P_MoveThing` moves the actor immediately, validates the destination via
   `P_TestMobjLocation`, and on failure calls `SetOrigin` a second time to put the actor back
   exactly where it started — no error message, no partial move, no network message either way on
   failure (the `SERVERCOMMANDS_MoveThing` replication only fires on success). A call site that
   doesn't capture and check the return value has no way to tell "moved" from "silently did
   nothing," and in a co-op/multiplayer context specifically, "blocked by another actor" does
   **not** mean "blocked by another player" if `sv_unblockplayers`/`sv_unblockallies` are set —
   `P_CheckUnblock` only excludes player-vs-player (or ally-vs-ally) collision, so a monster or any
   other solid non-player actor occupying the destination still silently fails the move. See
   [SetActorPosition](../functions/setactorposition.md)'s "Success/failure semantics" section.

## When you find a new one

Add a line under the relevant list above (or a new numbered pattern if it doesn't fit an existing
category) with a one-sentence mechanism and a link — and make sure the full verified detail lives
in the linked `functions/*.md`/`families/*.md` file, not only here. This file should never be the
only place a claim exists. Keep the entry project-agnostic per `../../shared/AUTHORING.md`'s "Stay project-agnostic"
rule: describe the mechanism in terms of the function/engine call involved (as the entries above
do), never the project code that happened to surface it.
