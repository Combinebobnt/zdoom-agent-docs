# `void SetActorProperty(int tid, int property, raw value)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-24)
**Provenance:** wiki page `SetActorProperty - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`https://zdoom.org/w/index.php?title=SetActorProperty&oldid=44527`) + source-verified against `p_acs.cpp:4445-4456, 4524-4919, 12365-12368`,
`zt-bcc/lib/zcommon.bcs:266-314`, `zt-bcc/src/builtin.c:108,256`, and real-world call sites
exhibiting the `APROP_SpawnHealth` gotcha documented above. Wiki/fork discrepancies (eight compile-but-dead `APROP_*` names for the
write path, plus the Health-on-dead-actor guard and the multi-actor-vs-single-actor TID asymmetry
with `GetActorProperty`) recorded above rather than silently trusted or overridden.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.

Writes a property onto actor(s) by TID. Compiler builtin (`PCD_SETACTORPROPERTY`,
the Zandronum source's `src/p_acs.cpp:12365-12368`), implementation in
`DLevelScript::SetActorProperty` / `DoSetActorProperty` (`p_acs.cpp:4524-4919`).

- `tid` — **`0` means "the activator"**, applied directly (`p_acs.cpp:4526-4529`). A **nonzero
  `tid` applies the write to every actor sharing that TID** — `SetActorProperty` loops a full
  `FActorIterator` (`while ((actor = iterator.Next()) != NULL) DoSetActorProperty(actor, ...)`,
  `p_acs.cpp:4530-4539`). This is asymmetric with `GetActorProperty`, which reads from only the
  *first* actor matching the TID (`SingleActorFromTID`, `p_acs.cpp:4445-4456`, one `iterator.Next()`
  call). In projects where a single TID is deliberately shared across many actors
  (e.g. a TID used to tag an entire spawned group), `SetActorProperty(group_tid, APROP_Speed, ...)` mutates
  *every* actor with that TID in one call, while `GetActorProperty(group_tid, APROP_Speed)` only
  ever sees one of them — not a bug, but easy to assume symmetric and get wrong.
- **A missing target is a silent no-op on both engines, and there's no return value to detect
  it.** A nonzero `tid` matching no actor just runs the iterator loop zero times. `tid` `0` with
  no activator (e.g. an `OPEN` script) passes a NULL actor to `DoSetActorProperty`, which returns
  immediately (Zandronum `p_acs.cpp:4544-4547`; UZDoom `src/playsim/p_acs.cpp:4132-4135`). The
  function is void at the VM level too: `PCD_SETACTORPROPERTY` pops its three arguments and pushes
  nothing (Zandronum `p_acs.cpp:12365-12368`; UZDoom `src/playsim/p_acs.cpp:9826-9829`). To tell
  whether a write can land, check beforehand with
  [`ClassifyActor`](classifyactor.md) (`ACTOR_NONE` for an unmatched nonzero TID, `ACTOR_WORLD`
  for TID 0 with no activator).
- `value` — declared `raw` in the actual builtin (`builtin.c:108`, `";iir"` = void return, two
  ints, one raw), not three separate overloads. The wiki's three signatures
  (`int`/`float`/`str` value) don't correspond to distinct BCS entry points in zt-bcc — there is
  no `zcommon.bcs`-side overload set for `SetActorProperty` at all (checked; it isn't declared
  there), just the one raw-third-arg builtin. It works anyway because `fixed` values and string
  handles already share the same bit representation as `int` at the BCS level — a `fixed`
  expression or string literal passed as `value` arrives with the correct bits for whichever
  property interprets them, with no runtime type tag or conversion involved. Passing the wrong
  *kind* of value for a property (e.g. a bare int where a fixed-point scale factor is expected)
  silently produces a nonsensical fixed-point value rather than an error — same failure mode
  `functions/getactorproperty.md` documents for the read side.
- **Spectators are unconditionally excluded**: `DoSetActorProperty` returns immediately if
  `actor->player && actor->player->bSpectating` (`p_acs.cpp:4549-4551`) — a Zandronum
  multiplayer-specific guard with no equivalent in single-player ZDoom, not mentioned on the wiki
  page at all.
- **`APROP_Health` has a built-in "don't touch the dead" guard the engine added**: if
  `actor->health <= 0` or the actor is a dead player (`playerstate == PST_DEAD`), the whole case
  is a no-op (`p_acs.cpp:4560-4566`) — before ever reaching `actor->health = value`. The wiki's own
  "Do not do this" example (worrying about re-zeroing an already-dead monster's health) describes
  a mistake the engine already makes harmless; setting `<= 0` on a *live* actor still
  calls `actor->Die()` as documented. Confirmed identical (same two conditions, same order) in
  UZDoom's `DoSetActorProperty` (`src/playsim/p_acs.cpp:4138-4154`) — not a Zandronum-only
  addition, both engine families guard this the same way.
- **`APROP_SpawnHealth` only takes effect on `APlayerPawn` actors** (`IsKindOf(RUNTIME_CLASS(APlayerPawn))`
  guard, `p_acs.cpp:4709-4726`) — calling it on a monster TID is a silent no-op, matching the
  wiki's "Only players may have their max health set this way" line. Verified as a real gotcha
  hit in practice: real-world code has called
  `SetActorProperty(mons_tid, APROP_SpawnHealth, new_health)` on a monster TID with an inline
  `// does nothing` comment. `APROP_JumpZ`, `APROP_ViewHeight`, and `APROP_AttackZOffset` have the
  same `APlayerPawn`-only guard (`p_acs.cpp:4665-4679, 4878-4901`) and are silent no-ops on
  non-player actors too, though the wiki doesn't call that out for those three.

## Wiki/engine divergence: eight settable properties Zandronum's `SetActorProperty` switch doesn't implement

Cross-checking every property the wiki page lists against the actual `switch (property)` in
Zandronum's `DoSetActorProperty` (`p_acs.cpp:4558-4918`, `default: // do nothing; break;` at the end):
**`APROP_DamageMultiplier`, `APROP_DamageType`, `APROP_Friction`, `APROP_FriendlySeeBlocks`,
`APROP_MaxDropOffHeight`, `APROP_MaxStepHeight`, `APROP_SoundClass`, and `APROP_MeleeRange`** all
have BCS-side constants in `zt-bcc/lib/zcommon.bcs:266-314` (so they compile without complaint)
but no `case` in Zandronum's switch — every one of them silently falls through to `default` and
writes nothing. This overlaps but isn't identical to the seven dead names `functions/getactorproperty.md`
found on the *read* side: `APROP_MeleeRange` is the odd one out — it **is** implemented for
`GetActorProperty` (`p_acs.cpp:4986`, read-only) but **not** for `SetActorProperty`, so
`GetActorProperty(tid, APROP_MELEERANGE)` works while
`SetActorProperty(tid, APROP_MELEERANGE, ...)` does nothing, with no error either way. Treat all
eight names above as **not usable to write in Zandronum** despite compiling. (UZDoom differs — see
the divergence section below.)

## Engine-family divergence: UZDoom implements all eight

UZDoom's `DoSetActorProperty` switch (`src/playsim/p_acs.cpp:4130-4370`) implements every one of
the eight properties Zandronum's `SetActorProperty` switch leaves unhandled above —
`APROP_MeleeRange`, `APROP_Friction`, `APROP_MaxStepHeight`, `APROP_MaxDropOffHeight`,
`APROP_DamageType`, `APROP_SoundClass`, `APROP_FriendlySeeBlocks`, and `APROP_DamageMultiplier` —
each writing straight into the corresponding actor field (`actor->meleerange`, `actor->Friction`,
`actor->MaxStepHeight`, `actor->MaxDropOffHeight`, `actor->DamageType`, `actor->friendlyseeblocks`,
`actor->DamageMultiply`), using the same fixed-point/string-handle conventions as the rest of the
switch. `APROP_SoundClass` additionally carries the same player-pawn-only guard `APROP_SpawnHealth`
has above — setting it on a non-player TID is a no-op even on UZDoom. Practical effect: the
`APROP_MeleeRange` get/set asymmetry documented above is Zandronum-only — on UZDoom,
`SetActorProperty(tid, APROP_MELEERANGE, ...)` actually changes the actor's melee range, so BCS
written and tested against UZDoom that relies on any of these eight properties will silently stop
working (writes become no-ops, with no compiler or runtime error) if the same object is later run
on Zandronum, and vice versa: code that assumes these eight are permanently inert (safe to pass a
wrong/placeholder value without consequence) is only safe under Zandronum.

(`APROP_TargetTID`, `APROP_TracerTID`, `APROP_WaterLevel`, `APROP_Dormant`, `APROP_Height`, and
`APROP_Radius` are also unimplemented in the Set switch, but the wiki's own `SetActorProperty`
page doesn't list them as settable either — they're documented as get-only by design, not a
wiki/engine divergence. Confirmed unimplemented in UZDoom's Set switch too, for the same reason.)

## `APROP_Invulnerable`'s write path has no cooperating-source guard

Both engines write `APROP_Invulnerable` the same way: an unconditional bit set/clear on
`MF2_INVULNERABLE` (Zandronum's `flags2` word; UZDoom's `bInvulnerable` ZScript property), with no
check for whether some other source also wants the flag held (Zandronum:
`DoSetActorProperty`'s `case APROP_Invulnerable:`, `p_acs.cpp:4645-4655`, which does
`actor->flags2 |= MF2_INVULNERABLE` / `&= ~MF2_INVULNERABLE` and, only on a listen server, notifies
clients of the change; UZDoom: the equivalent `case` in `src/playsim/p_acs.cpp:4187-4189`, the same
unconditional set/clear with no networking layer).

That matters because the engine's own [`PowerInvulnerable`](../../decorate/classes/powerup.md)
powerup class tears itself down the same unconditional way: its `EndEffect` override clears the
flag directly with no check for whether the actor's invulnerability came from anywhere else
(Zandronum: `Owner->flags2 &= ~MF2_INVULNERABLE`, `src/g_shared/a_artifacts.cpp:478`; UZDoom:
`Owner.bInvulnerable = false` in its ZScript `EndEffect` override,
`wadsrc/static/zscript/actors/inventory/powerups.zs`). Contrast this with
[`PowerProtection`](../../decorate/classes/powerprotection.md)'s own `InitEffect`/`EndEffect` pair
(see its "Flag-transfer half" section), which explicitly transfers flags only when the owner
doesn't already have them set and reverts only what it itself granted — `PowerInvulnerable` has no
equivalent guard for `MF2_INVULNERABLE`.

Practical consequence: if a script sets `APROP_Invulnerable` directly on an actor that separately
holds, or later receives, one of the engine's invulnerability-granting powerups — or the reverse, a
powerup-driven invulnerability is layered onto an actor whose flag was already set some other way
— whichever effect's teardown runs first clears the flag out from under the other source, silently
and with no way for the surviving source to detect its own state was undone. This follows from
`EndEffect`'s unconditional clear, so it isn't specific to one powerup subclass or one call site.

**Provenance:** source-verified directly against both engines (no wiki page covers this
interaction): Zandronum's `DoSetActorProperty` `case APROP_Invulnerable:` (`src/p_acs.cpp:4645-4655`)
and UZDoom's equivalent (`src/playsim/p_acs.cpp:4187-4189`); `PowerInvulnerable::EndEffect` in
Zandronum's `src/g_shared/a_artifacts.cpp:469-479` and UZDoom's
`wadsrc/static/zscript/actors/inventory/powerups.zs`.
**Tier:** B (no wiki-sourced starting point for this specific finding — see the file-level tier-A
stamp above for the rest of this file).

## Zandronum-specific: native respawn invulnerability's teardown only guards against other powerups

Zandronum additionally grants a `PowerInvulnerable` subclass, `PowerRespawnInvulnerable`,
automatically on respawn — in `P_SpawnPlayer`, whenever a player enters or respawns (`PST_REBORN`,
`PST_ENTER`, and their `NOINVENTORY` variants) and `dmflags2` does not have `DF2_NO_RESPAWN_INVUL`
set and the game is `deathmatch`, `teamgame`, or run with `alwaysapplydmflags`
(`src/p_mobj.cpp:5688-5692`) — in a plain coop game with none of those conditions true, this grant
never happens at all. Its duration is a hardcoded `3 * TICRATE` (`PowerRespawnInvulnerable::InitEffect`,
`src/g_shared/a_artifacts.cpp:2174`), with no cvar to change it. `PowerRespawnInvulnerable` overrides
`EndEffect` rather than inheriting the base class's version unchanged: it still calls
`Super::EndEffect()` first, which does the same unconditional `MF2_INVULNERABLE` clear documented
above, but then checks whether the owner holds another `APowerInvulnerable`-family inventory item
and, if so, re-sets the flag (`src/g_shared/a_artifacts.cpp:2233-2243`). That guard only covers
another *powerup*-granted invulnerability. It has no way to detect a bare `MF2_INVULNERABLE` state
set directly through `APROP_Invulnerable` with no backing inventory item, so a script-managed flag
with no `PowerInvulnerable`-family item behind it is still clobbered when respawn invulnerability
ends. That makes it a second, independent source that can undo a script's own `APROP_Invulnerable`
write in that narrower case. **No `PowerRespawnInvulnerable` class, or any automatic
respawn-invulnerability grant, exists anywhere in the UZDoom source** — this entire section is
Zandronum-only.

See [`A_Raise`](../../decorate/actions/a_raise.md)'s "Respawn invulnerability disabling" note for
the other end of this same mechanism: the engine's own code cancels this native respawn protection
early once a player finishes raising any weapon but the pistol/fists — a third, independent event
that can end up clearing the same flag.

See [`PowerProtection`](../../decorate/classes/powerprotection.md)'s "Engine-family divergence:
telefrag-magnitude damage" section for a related but separate fact: regardless of which source set
it, `MF2_INVULNERABLE` is only honored below `TELEFRAG_DAMAGE` on either engine — a hit at or above
that magnitude bypasses it entirely, independent of the teardown-ordering gotcha documented above.

**Provenance:** source-verified directly against both engines (no wiki page covers this): the
native respawn-invulnerability grant in Zandronum's `P_SpawnPlayer` (`src/p_mobj.cpp:5688-5692`),
its duration in `PowerRespawnInvulnerable::InitEffect` (`src/g_shared/a_artifacts.cpp:2170-2195`),
and its `EndEffect` override's other-powerup guard (`src/g_shared/a_artifacts.cpp:2233-2243`,
confirmed present unchanged as far back as the 3.2.1 version-bump commit `28f736fb3`); confirmed
absent from the UZDoom source by grepping for `PowerRespawnInvulnerable` tree-wide (no match).
**Tier:** B (no wiki-sourced starting point for this specific finding — see the file-level tier-A
stamp above for the rest of this file).

**Example — the safe way to reduce a live actor's speed without accidentally reviving math on a dead one:**

```text
SetActorProperty(mons_tid, APROP_Speed, GetActorProperty(mons_tid, APROP_Speed) - 4.0);
```

**Example — this looks like it should scale a monster's max health, but is a silent no-op on anything that isn't a player:**

```text
SetActorProperty(mons_tid, APROP_SpawnHealth, new_health); // no-op: SpawnHealth is player-pawn-only (both engines)
```
