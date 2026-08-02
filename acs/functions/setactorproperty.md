# `void SetActorProperty(int tid, int property, raw value)`

Writes a property onto actor(s) by TID. Compiler builtin (`PCD_SETACTORPROPERTY`,
the Zandronum source's `src/p_acs.cpp:12365-12368`), implementation in
`DLevelScript::SetActorProperty` / `DoSetActorProperty` (`p_acs.cpp:4524-4919`).

**Bucket:** compiler builtin.

- `tid` — **`0` means "the activator"**, applied directly (`p_acs.cpp:4526-4529`). A **nonzero
  `tid` applies the write to every actor sharing that TID** — `SetActorProperty` loops a full
  `FActorIterator` (`while ((actor = iterator.Next()) != NULL) DoSetActorProperty(actor, ...)`,
  `p_acs.cpp:4530-4539`). This is asymmetric with `GetActorProperty`, which reads from only the
  *first* actor matching the TID (`SingleActorFromTID`, `p_acs.cpp:4445-4456`, one `iterator.Next()`
  call). In projects where a single TID is deliberately shared across many actors
  (e.g. a TID used to tag an entire spawned group), `SetActorProperty(group_tid, APROP_Speed, ...)` mutates
  *every* actor with that TID in one call, while `GetActorProperty(group_tid, APROP_Speed)` only
  ever sees one of them — not a bug, but easy to assume symmetric and get wrong.
- `value` — declared `raw` in the actual builtin (`builtin.c:108`, `";iir"` = void return, two
  ints, one raw), not three separate overloads. The wiki's three signatures
  (`int`/`float`/`str` value) don't correspond to distinct BCS entry points in this fork — there is
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
- **`APROP_Health` has a built-in "don't touch the dead" guard this fork added**: if
  `actor->health <= 0` or the actor is a dead player (`playerstate == PST_DEAD`), the whole case
  is a no-op (`p_acs.cpp:4560-4566`) — before ever reaching `actor->health = value`. The wiki's own
  "Do not do this" example (worrying about re-zeroing an already-dead monster's health) describes
  a mistake this fork's engine code already makes harmless; setting `<= 0` on a *live* actor still
  calls `actor->Die()` as documented.
- **`APROP_SpawnHealth` only takes effect on `APlayerPawn` actors** (`IsKindOf(RUNTIME_CLASS(APlayerPawn))`
  guard, `p_acs.cpp:4709-4726`) — calling it on a monster TID is a silent no-op, matching the
  wiki's "Only players may have their max health set this way" line. Verified as a real gotcha
  hit in practice: real-world code has called
  `SetActorProperty(mons_tid, APROP_SpawnHealth, new_health)` on a monster TID with an inline
  `// does nothing` comment. `APROP_JumpZ`, `APROP_ViewHeight`, and `APROP_AttackZOffset` have the
  same `APlayerPawn`-only guard (`p_acs.cpp:4665-4679, 4878-4901`) and are silent no-ops on
  non-player actors too, though the wiki doesn't call that out for those three.

## Wiki lists eight settable properties this fork's `SetActorProperty` switch doesn't implement

Cross-checking every property the wiki page lists against the actual `switch (property)` in
`DoSetActorProperty` (`p_acs.cpp:4558-4918`, `default: // do nothing; break;` at the end):
**`APROP_DamageMultiplier`, `APROP_DamageType`, `APROP_Friction`, `APROP_FriendlySeeBlocks`,
`APROP_MaxDropOffHeight`, `APROP_MaxStepHeight`, `APROP_SoundClass`, and `APROP_MeleeRange`** all
have BCS-side constants in `zt-bcc/lib/zcommon.bcs:266-314` (so they compile without complaint)
but no `case` in this switch — every one of them silently falls through to `default` and writes
nothing. This overlaps but isn't identical to the seven dead names `functions/getactorproperty.md`
found on the *read* side: `APROP_MeleeRange` is the odd one out — it **is** implemented for
`GetActorProperty` (`p_acs.cpp:4986`, read-only) but **not** for `SetActorProperty`, so
`GetActorProperty(tid, APROP_MELEERANGE)` works while
`SetActorProperty(tid, APROP_MELEERANGE, ...)` does nothing, with no error either way. Treat all
eight names above as **not usable to write** in this fork despite compiling.

(`APROP_TargetTID`, `APROP_TracerTID`, `APROP_WaterLevel`, `APROP_Dormant`, `APROP_Height`, and
`APROP_Radius` are also unimplemented in the Set switch, but the wiki's own `SetActorProperty`
page doesn't list them as settable either — they're documented as get-only by design, not a
wiki/fork divergence.)

**Example — the safe way to reduce a live actor's speed without accidentally reviving math on a dead one:**

```
SetActorProperty(mons_tid, APROP_Speed, GetActorProperty(mons_tid, APROP_Speed) - 4.0);
```

**Example — this looks like it should scale a monster's max health, but is a silent no-op on anything that isn't a player:**

```
SetActorProperty(mons_tid, APROP_SpawnHealth, new_health); // no-op: SpawnHealth is player-pawn-only in this fork
```

**Provenance:** wiki page `SetActorProperty - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`oldid=44527`) + source-verified against `p_acs.cpp:4445-4456, 4524-4919, 12365-12368`,
`zt-bcc/lib/zcommon.bcs:266-314`, `zt-bcc/src/builtin.c:108,256`, and real-world call sites
exhibiting the `APROP_SpawnHealth` gotcha documented above. Wiki/fork discrepancies (eight compile-but-dead `APROP_*` names for the
write path, plus the Health-on-dead-actor guard and the multi-actor-vs-single-actor TID asymmetry
with `GetActorProperty`) recorded above rather than silently trusted or overridden.
**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.
