# A TID reclaimed by a spawned actor's Spawn state becomes visible one tic late

**Tier:** B — the *behavior* below is directly measured in-engine and reproducible; the *mechanism*
behind it is explicitly **not** established (see "Why, is open" below). Stated as tier B rather
than A precisely because the causal reading is unresolved, per `../../shared/AUTHORING.md`'s tier-B
carve-out for a claim not exhaustively traced in one pass.
**Applies to:** UZDoom=unknown, Zandronum=yes — measured on Zandronum only. The same test has not
been run on UZDoom, and nothing here should be assumed to carry over without repeating it.
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-08-26)
**Provenance:** Direct in-engine measurement — `Log(d:Timer())` instrumentation at four call sites,
5+ independent observations, plus a controlled parity sweep. No wiki page; not derived from source
reading (a source-order derivation was attempted and **contradicted** by the measurement).

## The measurement

A common pattern: a script frees a TID and immediately spawns an actor whose own DECORATE Spawn
state calls back into ACS to re-claim that same TID (`Thing_ChangeTID(0, tid)`), so the TID always
names "the current one of these". The question that matters is **when the reclaim becomes visible
to other scripts**.

Measured tic sequence, where `T` is the tic the freeing script runs on:

| tic | what runs |
|---|---|
| `T` | the script: `Thing_Remove(tid)`, then a spawn call (e.g. `LineAttack` spawning a puff) |
| `T+1` | the spawned actor's Spawn-state chain, including its `ACS_NamedExecuteAlways` callback that re-claims `tid` |
| `T+2` | a script started *by* that callback runs its first instruction |

Two consequences, both stable across every observation:

- **`ThingCount(T_NONE, tid) == 0` is observably true for exactly one tic** — tic `T` only. The
  reclaim lands on the following tic, not the same one.
- **Within tic `T+1`, the Spawn-state callback runs before the ordinary ACS script pass.** Both log
  the same `Timer()` value, with the callback first. So a script polling on `T+1` already sees the
  TID reclaimed; the window is **not** two tics wide.

Note also that a script started via `ACS_NamedExecuteAlways` does not execute any of its own
instructions on the tic it is started — its first instruction runs on the following tic. A
`scriptstat` snapshot taken in between shows it as `Running`, not `Delayed`, with no side effects
yet performed.

## Why this bites: a polling loop turns a one-tic window into a parity bug

If another script watches for that TID to disappear using `delay(N)` with `N > 1`, its polls sit at
a **fixed parity** relative to whatever started it. Against a window exactly one tic wide, the
outcome is then fully determined — not probabilistic:

- If `(freeing tic - poll-loop start tic)` is congruent to the loop's phase, a poll lands on `T` and
  observes the gap.
- Otherwise every poll straddles it: one lands on `T-1` (TID still present, not yet freed) and the
  next on `T+1` (TID already re-claimed).

A measured `delay(2)` loop showed a clean alternating pass/fail across consecutive one-tic offsets —
50% of attempts, deterministic per offset, looking exactly like a flaky race while being nothing of
the kind. The user-visible symptom was intermittent and self-healing on retry, because ordinary
human timing re-rolls the parity on each attempt.

**Fix shape:** guard on a **level-persistent counter** bumped by the freeing script, not on the
actor's existence. A counter cannot be missed by any polling phase. Shrinking the poll to `delay(1)`
only narrows the window — it does not remove the dependence on where the poll lands, and it doubles
the poll cost.

## Why, is open

A source-order reading predicts the **opposite** of the measurement, and that discrepancy is
deliberately left unresolved here rather than papered over:

- `statnums.h` places `STAT_DEFAULT` (ordinary actors, including a freshly spawned puff) at 100,
  below `STAT_SCRIPTS` (the ACS thinker) at 103.
- `dthinker.cpp`'s `DThinker::RunThinkers()` ticks the main lists in ascending statnum order, then
  drains `FreshThinkers` repeatedly until no new thinkers appear.

Both of those were re-checked directly and are accurate. Taken together they predict that an actor
spawned during tic `T`'s ACS pass runs its Spawn chain in that same tic's fresh-thinker drain — i.e.
the reclaim should be visible at `T`, giving no window at all. **It is not.** Something between
console/net command processing, `P_StartScript` scheduling, and the fresh-thinker drain accounts for
the offset, and this file does not claim to know which.

Recorded as measured-behavior-with-open-cause on purpose. This exact subsystem has a track record of
confidently-wrong theories derived from source order alone; a plausible-sounding mechanism written
here would be worse than none, because the next reader would build on it instead of measuring.
**If you resolve the cause, measure it — don't derive it.**
