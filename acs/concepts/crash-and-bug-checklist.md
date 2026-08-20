# Crash-and-bug checklist for ACS/BCS review

**Tier:** A (every claim here is a pointer to an independently source-verified finding; this file adds no new unverified claims of its own).
**Applies to:** UZDoom=yes, Zandronum=yes — this file indexes findings from many other doc files
whose per-engine status varies rather than making one claim of its own, so the file-level `yes` on
each engine means "this checklist is worth reading against that engine," not "every entry below
reproduces there." Most indexed patterns do reproduce on both. The exceptions are now verified
rather than assumed: four crash patterns name functions that don't exist in UZDoom at all, and the
whole "declared-but-unimplemented extension functions" section is inverted (Zandronum-only — UZDoom
implements every function it lists, no exceptions, including the `ZDoom_*` math trio), and the
CLIENTSIDE ordering hazard has no UZDoom counterpart. See "Engine-family divergence" below for the
per-entry map, and check each linked file's own `Applies to:` field before acting on an entry.
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** Cross-referenced from this repo's own verified `functions/`/`families/` docs (compiled 2026-07-29) — not a wiki-intake page, no new source reading beyond what's cited in each linked file.

A running, checklist-style index of **verified, recurring** crash/bug-causing patterns in the
ACS/BCS layer of this tree's target engines (UZDoom and Zandronum) and of the `zt-bcc` compiler
that feeds them — not a tutorial, not exhaustive. Each entry is one sentence of "what to
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
   (`zstring.cpp:326-333`) — a real Zandronum engine bug, not fail-safe like the sibling
   `TPROP_Name`. See
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

7. **A script's own activator being destroyed mid-`Delay()` does not stop the script, and every
   `tid=0` getter afterward silently returns as if `tid=0` meant "nothing" rather than "the
   activator is gone."** The script's `activator` field is a GC-tracked `TObjPtr<AActor>`
   (`p_acs.h:1070`, `DECLARE_POINTER(activator)` at `p_acs.cpp:3714`) that gets nulled out by the
   pointer-substitution pass when the referenced actor is destroyed — but nothing then calls
   `FBehavior::StaticStopMyScripts` (`p_acs.cpp:3481-3489`) for it. Every real call site of that
   function is player-specific — disconnect (`sv_main.cpp:3288`, `d_net.cpp:635`, `bots.cpp:602`,
   `cl_main.cpp:4811,5461`), morph (`p_user.cpp:2618`), spectate (`p_interaction.cpp:2546,2781`),
   voodoo-doll respawn (`p_mobj.cpp:5528`) — there is no general "an actor died, stop scripts that
   were activated by it" path. So a script whose activator is a plain (non-player) actor that gets
   destroyed simply **resumes on the next tic with a NULL activator**. Every `tid=0`-means-activator
   getter (`GetActorZ`, `GetActorFloorZ`, `GetActorVelX/Y/Z`, etc.) then silently returns `0` —
   indistinguishable from "activator legitimately at position/velocity 0" — and `PlayActorSound(0,
   ...)` (pattern 1 above) crashes on the same NULL pointer. **The correct guard, verified
   sufficient:** `IsPointerEqual(AAPTR_DEFAULT, AAPTR_NULL, 0, 0)` resolves the `tid=0`/
   `AAPTR_DEFAULT` pointer and compares it against `AAPTR_NULL` — wrap any activator-touching call
   after a `Delay`/`Suspend`/polling loop with `if (!IsPointerEqual(AAPTR_DEFAULT, AAPTR_NULL, 0,
   0)) { ... }`, and re-check every iteration of a polling loop, not just once at the top. See
   [PlayActorSound](../functions/playactorsound.md), [IsPointerEqual](../functions/ispointerequal.md).

## Computed TIDs that silently hit unrelated actors (no crash, no error — just wrong actors)

TIDs are not unique and are not bounds-checked: nothing stops two actors from holding the same
one ([Thing_ChangeTID](../functions/thing_changetid.md) never checks for a collision before
assigning). So any TID built by *arithmetic* rather than taken from a literal is a place where a
wrong input silently addresses some other subsystem's actors instead of erroring.

1. **A TID computed as `BASE + index` where `index` can fall outside the range reserved for
   `BASE`.** The usual shape is a script that derives `index` from an actor TID (`some_tid -
   FIRST_PLAYER_TID` to get a player slot, and similar) on a code path where that actor is *not*
   the kind of actor the arithmetic assumed — the subtraction then goes negative or overruns, and
   `BASE + index` lands in a neighbouring TID block. Nothing reports it. Grep for TID bases used
   with `+` and confirm the offset's proven range fits the gap to the next allocated base;
   whichever guard establishes "this actor is a player" (or whatever the index assumes) must
   dominate *every* path reaching the arithmetic, not just the one it was written for.

2. **`Thing_Remove(computed_tid)` deletes every actor holding that TID, not one.** This turns
   pattern 1 from "addresses the wrong actor" into "silently destroys live, unrelated actors."
   `LS_Thing_Remove` (`p_lnspec.cpp:1310-1326`) drives an `FActorIterator` over the whole chain
   and calls `P_RemoveThing` on each match — so the common "tag a temporary actor with a scratch
   TID, then `Thing_Remove` that TID to clean it up" idiom removes the intended actor **plus**
   anything else that happens to share the TID. Live player bodies are the only things exempt
   (`P_RemoveThing`, `p_things.cpp:504-519`). Note that on Zandronum a "removed" actor may only be
   *hidden* and keeps its TID — see [Thing_Remove](../functions/thing_remove.md) for that fork
   divergence and the full semantics. Severity of a hit here scales with how densely the TID space
   is populated at the moment of the call, which is why this can be invisible in a short test and
   damaging in a long-running session.

3. **A sequential TID allocator whose counter can rewind while actors allocated under the old
   counter still exist.** Mods that hand out TIDs as `BASE + counter++` must never reset that
   counter mid-map (on a "last player left" event, a round transition that doesn't actually
   remove actors, etc.): every allocation after the reset re-issues a TID that may still be
   attached to a live actor, a corpse, or a hidden pickup, producing pattern-2 style collisions
   that surface minutes later (e.g. when something resurrects the corpse and two live actors
   share one TID and one slot of mod-side per-TID state). Reset counters only where the actor
   population itself resets (map load/unload), or track per-TID liveness explicitly.

4. **[ThingCount](../functions/thingcount.md) is not an "is this TID free" test.** Its loop
   skips actors with `health <= 0` (corpses), actors hidden by `HideOrDestroyIfSafe()`
   (picked-up respawnable items), spectating players, and inventory items with an owner — see
   that doc's exclusion list. An allocator that probes candidates with
   `while(ThingCount(0, tid)) ++tid;` will happily assign a TID still held by any of those, and
   the collision stays invisible until the hidden holder re-materializes (item respawn, corpse
   raise). [IsTidUsed](../functions/istidused.md) is the existence-only check that has none of
   these exclusions.

**Why the "spawn, `SetActivator(tid)`, clear the TID" idiom usually survives a collision anyway,
and when it stops:** the most recently spawned actor sits at the head of the TID hash chain
(`AActor::AddToHash` inserts at the head, `p_mobj.cpp:3575-3593`) and every first-match lookup
returns the head (`FActorIterator::Next`, `actor.h:1278-1304`), so the just-spawned actor wins.
That guarantee holds only while nothing yields — a `Delay`/`Suspend` between the spawn and the
lookup lets another actor take the head and lets other scripts observe the collision. See
[SetActivator](../functions/setactivator.md)'s "Which actor wins when several share the TID".

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
- **Deep/runaway recursion doesn't crash the engine on either UZDoom or Zandronum, contrary to the
  ZDoom wiki's own claim.** The shared 4096-word VM stack has a bounds check that catches overflow
  first, prints a console message, and removes only the offending script instance — the wiki's
  "will eventually crash the game" does not hold on either engine. See [User-defined functions](user-functions.md).

## Declared-but-unimplemented extension functions (compile fine, silently no-op — not a crash, but a very common footgun)

Not a crash pattern, but the single most commonly hit "why isn't this working" bug on the
Zandronum engine specifically — this whole section is Zandronum-only, see "Engine-family
divergence" below:
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

## Operators that compile fine and silently produce the wrong answer

1. **`==`/`!=` between a compiled string literal and any runtime-built `str` (`StrParam`,
   concatenation, or a `ScriptCall`-bridged function returning a ZScript/C++ string) is always
   false/true respectively, regardless of text content.** `str` comparison compiles to a raw
   integer `PCD_EQ`/`PCD_NE` with no string-content awareness; a literal's index carries its
   compiled module's real library ID while every runtime-built string is unconditionally tagged
   with a reserved sentinel library ID (`STRPOOL_LIBRARYID_OR`) that can never match a real one —
   the two sides live in permanently disjoint integer ranges. Grep for `==`/`!=` against a `str`
   where one side is a bound/extension-function call and the other a literal; printing both sides
   (e.g. via `Log`) can show identical text while the comparison still silently fails. See
   [String literal vs. pool equality](string-literal-vs-pool-equality.md) for the full mechanism
   and the fix (`StrCmp`/`StrIcmp`).

2. **`str + str` silently does raw integer addition instead of concatenation, unless BOTH operands
   are literal constants.** `"abc" + "def"` (two literals) correctly constant-folds into a real
   concatenated string at compile time - but `chunk + chunk` (a `str` variable, or any operand
   that isn't itself compile-time-constant) compiles to a plain `ADD` opcode on the two operands'
   raw pool-index integers, never reaching the print-based concatenation codegen path at all. The
   result is a bogus index that almost always reads back as an empty string, with no compile
   error, no runtime error, no warning - `zt-bcc`'s own source has a working `concat_str()`
   function that looks like it should handle this, but it's only reached by the constant-folding
   path. This is a **compiler bug** (`zt-bcc`, confirmed via raw opcode disassembly, not an engine
   bug), so it isn't engine-specific. See
   [String `+` operator variable bug](string-concat-operator-variable-bug.md) for the full
   evidence and the fix (`StrParam`'s format-item list instead of `+`).

## Cross-machine ordering hazards (no crash, no error — client state silently diverges from server)

1. **Server-triggered `CLIENTSIDE` script executions batched into one client tic run in REVERSE
   send order.** The client creates each puked script at packet-parse time, `DLevelScript::Link()`
   prepends to the thinker list, and `DACSThinker::Tick()` runs head→tail — so a coalesced batch
   (always within one packet; multiple server tics' worth under lag) applies newest-first even
   though delivery is reliable and in-order. Any per-field absolute-write sync protocol that
   writes the same client-side location twice in quick succession can end with the *older* value,
   persistently, on the client only — latency-dependent, invisible in singleplayer. Grep for
   mods pumping `ACS_NamedExecuteWithResult` at `CLIENTSIDE` "syncer" scripts in loops. See the
   "run in REVERSE order" section of [Client-side scripting](clientside-scripting.md) for the
   verified mechanism and the version-stamp / reorder-queue / resync-on-open fixes.

## Engine-family divergence

Per-entry map of which patterns above reproduce on UZDoom. Verified by reading UZDoom's own source
for each mechanism named directly in this file (not merely inherited from the linked files' own
engine claims). Entries not listed here reproduce identically on both engines.

**Absent on UZDoom — the function itself does not exist.** No `ACSF_` case, enum entry, or
implementation anywhere in the UZDoom tree, so the crash cannot be reached at all; the pattern is
Zandronum-only, not "unverified on UZDoom":

- Pattern 2 (`GetTeamProperty` returning `NULL` into `FString::operator+=`) — UZDoom has no team
  API of this shape at all.
- Pattern 3 (`RequestScriptPuke`/`NamedRequestScriptPuke` dereferencing a failed lookup).
- Pattern 4 (`LumpGetInfo` passing an unvalidated index into the wad lookup) — and see the linked
  [Lump I/O family](../families/lump-io.md), which is `UZDoom=no` for all five callable members.
- Pattern 5 (`GetActorSectorLocation`'s raw int misused as a string index).

**Inverted on UZDoom — the "declared-but-unimplemented extension functions" section is
Zandronum-only, with no exceptions.** Every function that section lists as a silent no-op is
*implemented* on UZDoom: `SetActorFlag`, `CheckClass`, `SpawnParticle`, `GetMaxInventory`, `StrArg`,
`SetSectorDamage`, and the `ZDoom_Floor`/`ZDoom_Round`/`ZDoom_Ceil` trio all have real `ACSF_` cases
there, which is exactly the point of that section's framing (Zandronum never backported what
UZDoom's ZDoom-descended codebase already had). Do not carry that section's workarounds over to a
UZDoom target — `SetActorFlag` works directly and needs no `CustomInventory` bridge, and
`ZDoom_Floor`/`ZDoom_Round`/`ZDoom_Ceil` need no bit-trick fallback (see
[ZDoom math functions](../families/zdoom-math-stubs.md) for the corrected per-engine writeup — a
prior version of this bullet claimed the trio was dead on both engines, traced to a now-fixed
`tools/engine_matrix.py` name-matching bug).

**No UZDoom counterpart — the cross-machine ordering hazard.** The reverse-order `CLIENTSIDE`
batch hazard depends on Zandronum's server→client script-puke path, which UZDoom has no equivalent
for. Worth knowing *why*, since a grep alone is misleading: UZDoom's tree does contain a
`ClientSideACSThinker` and the surrounding plumbing, but its `IsClientSideScript` predicate is
hardcoded to return false, disabled behind a source comment saying a new flag is needed for
UZDoom's own style of client-side handling and that the previous behavior broke existing
`CLIENTSIDE` scripts. So no script is actually treated as client-side on UZDoom today, and the
ordering hazard cannot arise.

**Narrower on UZDoom — same pattern, smaller blast radius:**

- Computed-TID entry 4 ([ThingCount](../functions/thingcount.md) is not an "is this TID free"
  test): still true on UZDoom, but with a shorter exclusion list. Corpses (`health <= 0`) and
  inventory items with an owner are still skipped; the hidden-actor skip and the
  spectating/dead-spectator skip are Zandronum-only, so a UZDoom allocator probing with
  `ThingCount` has fewer invisible holders to collide with. [IsTidUsed](../functions/istidused.md)
  remains the correct existence-only check on both.
- Computed-TID entry 2's parenthetical about a "removed" actor being only *hidden* and keeping its
  TID is already labelled Zandronum-only above, and that is verified correct: UZDoom's
  `P_RemoveThing` has no hide-vs-destroy fork, so a removed actor is genuinely destroyed and drops
  out of the TID hash. UZDoom adds its own narrowing instead — an owned inventory item is skipped
  rather than removed. The rest of entry 2 (fan-out over every actor sharing the TID, live player
  bodies exempt) holds on both.
- The `SetActorPosition` entry: the silent-revert-and-return-false core holds on UZDoom, but the
  co-op caveat does not — `sv_unblockplayers`/`sv_unblockallies` and the `P_CheckUnblock`
  player-vs-player exclusion have no UZDoom counterpart, so on UZDoom *any* solid actor at the
  destination blocks the move with no special case. The "no network message either way on failure"
  clause is likewise Zandronum-specific; UZDoom has no server-side replication call on this path
  to omit.

**Confirmed to reproduce on UZDoom** (stated affirmatively so the list above isn't read as "the
rest is unchecked"):

- Pattern 1 (`PlayActorSound(0, ...)` with no activator). UZDoom's shared `PlaySound`/
  `PlayActorSound` case assigns the activator to the sound spot with no NULL check and then calls
  the same per-actor sound getter, which dereferences the actor in every case but `default` — the
  identical unguarded path, including the same accidental safety for an out-of-range `sound` value.
  `PlaySound` is still safe for the same reason it is on Zandronum.
- Pattern 6 (`LineAttack(0, ...)` with no activator) — see
  [LineAttack](../functions/lineattack.md), which records the unguarded NULL dereference as holding
  on both engines. UZDoom additionally lets a ZScript event handler veto the whole attack, which is
  a separate concern documented there.
- Pattern 7 (activator destroyed mid-`Delay()`). UZDoom's script activator is the same GC-tracked
  object pointer, nulled by the same pointer-substitution pass, and the "stop scripts started by
  this actor" helper is called from even fewer places than on Zandronum (player disconnect and
  voodoo-doll respawn only) — so the finding holds *more* strongly there: there is still no
  general "an actor died, stop scripts it activated" path. The `IsPointerEqual(AAPTR_DEFAULT,
  AAPTR_NULL, 0, 0)` guard is verified on UZDoom too.
- Every entry in "Patterns that look risky but are verified NOT to crash": the sound siblings'
  guards, divide/modulus-by-zero terminating only the offending script instance via the same
  console-message-then-remove path, invalid string handles degrading safely (UZDoom carries the
  same "don't crash on invalid strings" substitution), and the 4096-word VM stack's bounds check
  ahead of a user-function call.
- Both entries under "Operators that compile fine and silently produce the wrong answer": UZDoom
  uses the same reserved string-pool library ID that can never match a compiled literal's real
  one, so literal-vs-runtime `str` equality fails identically; and the `str + str` bug is a
  `zt-bcc` code-generation bug, engine-independent by construction.
- The `LineAttack` `pufftid` silent-drop entry, which the linked file records as agreeing between
  the two engines.

## When you find a new one

Add a line under the relevant list above (or a new numbered pattern if it doesn't fit an existing
category) with a one-sentence mechanism and a link — and make sure the full verified detail lives
in the linked `functions/*.md`/`families/*.md` file, not only here. This file should never be the
only place a claim exists. Keep the entry project-agnostic per `../../shared/AUTHORING.md`'s "Stay project-agnostic"
rule: describe the mechanism in terms of the function/engine call involved (as the entries above
do), never the project code that happened to surface it.
