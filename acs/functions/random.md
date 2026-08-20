# `int Random(int min, int max)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-28)
**Provenance:** wiki page `Random - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-28,
`https://zdoom.org/w/index.php?title=Random&oldid=54552`) + source-verified against the Zandronum source (`p_acs.cpp:183,3884-3892,10501-10513`,
`m_random.h:56-61`, `m_random.cpp` header comments) and the zt-bcc source's `src/builtin.c:37`. The
wiki's core inclusive-range description holds; the argument-order tolerance, shared-stream/demo-sync
nature, clientside-sync caveat, fixed-point/modulo notes, and the `compat_oldrandom` non-effect
are this doc's source-verified additions (not on the wiki page, which is written for vanilla ZDoom
single-player/demo context without Zandronum's client/server split in mind).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin. There is no BCS-side declaration for it in `zcommon.bcs` (nothing
matches `\brandom\b` there) — unlike an extension function or action special, this name is wired
straight into the compiler's own builtin table, not textually declared as ordinary BCS source.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Returns a pseudo-random integer in `[min, max]` inclusive. Compiler builtin (`g_funcs[]` entry
`"random"`, the zt-bcc source's `src/builtin.c:37`), implementation in `DLevelScript::Random`
(the Zandronum source's `src/p_acs.cpp:3884-3892`), invoked from `case PCD_RANDOM:`
(`p_acs.cpp:10501-10503`) when both arguments are runtime values, or `PCD_RANDOMDIRECT`/
`PCD_RANDOMDIRECTB` (`p_acs.cpp:10505-10513`) when the compiler can encode one/both arguments as
immediates — all three opcodes call the same `Random(min, max)` function, so there is no behavior
difference between them, just a bytecode-size optimization.

```cpp
int DLevelScript::Random (int min, int max)
{
	if (max < min)
	{
		swapvalues (max, min);
	}

	return min + pr_acs(max - min + 1);
}
```

- **Argument order doesn't matter.** If `max < min`, the engine silently swaps them before
  drawing — `Random(10, 1)` behaves identically to `Random(1, 10)`. The wiki page only describes
  the `min, max` (ascending) case; Zandronum (and, per this same function existing verbatim
  upstream, ZDoom generally) tolerates the reversed order without error.
- **Inclusive on both ends**, confirmed by the arithmetic: `pr_acs(max - min + 1)` draws a
  uniform value in `[0, max-min]` (`FRandom::operator()(int mod)`, `m_random.h:56-61`, is
  `GenRand32() % mod`), then `min` is added back — so `max` itself is a reachable result, not
  exclusive as a naive half-open reading of "a range" might suggest.
- **Not true entropy — a single shared, deterministic PRNG stream for the entire game
  instance.** The generator is `FRandom pr_acs("ACS")` (`p_acs.cpp:183`), one `static`/global
  object seeded once per game instance and shared by *every* `Random()` call from *every* script
  and *every* map for that instance's lifetime — not a fresh or independently-seeded stream per
  script, per map, or per call. `m_random.cpp`'s header explains why: this is Killough/BOOM-style
  per-source RNG bookkeeping, kept specifically for demo-sync and backward-compatibility
  reasons (each named source, e.g. `"ACS"`, gets isolated, reproducible state independent of other
  RNG consumers like monster AI). Practical effect: the *n*-th call to `Random()` since the level
  (or demo) was seeded depends on every prior `Random()` draw across the whole script ecosystem,
  not just calls local to the script or function doing the reasoning — there's no way to get an
  independent/isolated random stream for just one subsystem.
- **No *per-draw* client/server sync for `pr_acs` — but it does feed the network consistency
  check.** `pr_acs` has four references in Zandronum's `src`, not the two ("exactly one reader...
  one definition") this file previously claimed: `m_random.cpp:89` (`extern` declaration) and
  `:303` in addition to the definition (`p_acs.cpp:183`) and the `Random()` draw itself
  (`p_acs.cpp:3891`). The `:303` reference is inside `FRandom::StaticSumSeeds()`, whose own header
  comment states its purpose directly: producing a checksum "used to check the consistancy of
  network games between different machines," summing exactly four RNG streams
  (`pr_spawnmobj`/`pr_acs`/`pr_chase`/`pr_damagemobj`). It's called from `g_game.cpp:1658`, under a
  comment about including "random seeds and player stuff in the consistancy check." So `pr_acs`'s
  internal state *is* read by network-desync-detection code — just not synchronized per-draw the
  way an individual `Random()` result is. Server-executed (default) scripts are authoritative as
  usual and their *effects* (spawns, damage, etc.) replicate to clients normally, but a `CLIENTSIDE`
  script's own `Random()` calls run against that client's own local `pr_acs` instance, independently
  of the server's and of every other client's. Don't rely on `Random()` producing the same sequence
  across machines from inside a `CLIENTSIDE`
  script — it wasn't built for that, and nothing in Zandronum's source synchronizes it.
- **Fixed-point arguments work, but `Random` itself is int-only and doesn't know it.** The wiki's
  second example (`SetActorAngle(0, Random(0, 1.0))`) works only because ACS fixed-point literals
  are just raw ints under the hood (`1.0` compiles to `65536`) — `Random` draws a uniform integer
  over the *raw* range `[min, max]` (here `[0, 65536]`) and hands it back unchanged; it performs no
  fixed-point-aware scaling. Passing genuinely fixed values in only works because the caller
  (`SetActorAngle` here) reinterprets the returned int as fixed — `Random` contributes nothing
  fixed-point-specific itself.
- **Modulo-based draw, not rejection-sampled** — `GenRand32() % mod` has the usual small modulo
  bias when `mod` (`max - min + 1`) doesn't evenly divide 2^32. Negligible for the small ranges
  typical gameplay code actually uses (tens to low hundreds), not worth working around here.
- **`compat_oldrandom` (`ZACOMPATF_OLD_RANDOM_GENERATOR`) does NOT affect this function.** The
  flag (`d_main.cpp:846`, backing `zacompatflags`) is checked in exactly two places in
  `m_random.cpp`: the no-argument `FRandom::operator()()` (`m_random.cpp:234-241`, range
  `[0,255]`) and `FRandom::Random2()` (`m_random.cpp:244-251`) — both fall back to the legacy
  `P_Random()` table when the flag is set. `DLevelScript::Random` calls `pr_acs(max - min + 1)`,
  which resolves to the *single-argument* `operator()(int mod)` overload
  (`m_random.h:56-61`, inline) — that overload unconditionally does `GenRand32() % mod` with no
  `zacompatflags` check at all, and `GenRand32()` itself (`sfmt/SFMT.cpp:361`) is the raw SFMT
  generator, also compat-flag-agnostic. So toggling `compat_oldrandom` changes monster-AI-style
  `[0,255]`/`Random2()` draws elsewhere in the engine but has zero effect on ACS `Random(min,
  max)` — every mod using it draws from the same SFMT-backed `pr_acs` stream regardless of this
  cvar.

**Spelling:** BCS/ACS identifiers are case-insensitive — confirmed at the lexer level, which
lowercases every identifier character as it's read (the zt-bcc source's `src/parse/token/source.c:928,972,1055`)
before any name-table lookup — so `Random`, `random`, and `RANDOM` all compile to the exact same
builtin. The compiler's own internal table spells it lowercase (`"random"`,
`builtin.c:37`), which is what the current tier-C `INDEX.md` entry reflects, but either spelling
is equally correct to the compiler; this doc uses `Random` to match both the ZDoom wiki's own
title casing and this doc's heading.

**Returns:** `int` — uniformly-drawn pseudo-random integer in `[min, max]` inclusive (order of
`min`/`max` doesn't matter, see above).

## Engine-family divergence: draw method, PRNG algorithm, and clientside stream isolation

`DLevelScript::Random` still lives at the same call sites on UZDoom (`src/playsim/p_acs.cpp:3628-3636`,
reached from `case PCD_RANDOM:`/`PCD_RANDOMDIRECT`/`PCD_RANDOMDIRECTB` at `p_acs.cpp:8325-8338`,
all three still funneling through the one function) and keeps the argument-swap-on-reversed-order
and inclusive-both-ends behavior described above unchanged. Three things underneath it differ from
Zandronum:

- **Different PRNG algorithm entirely.** Zandronum's generator is SFMT-based (per the prose above);
  UZDoom's `FRandom` (`src/common/engine/m_random.h:35-71`) instead implements a PCG-XSH-RR
  generator with a single 64-bit state word — a different algorithm family, not a parameter change
  to the same one. The per-named-source bookkeeping Killough/BOOM design the file header describes
  (`m_random.cpp:24-45`) is explicitly kept for the same demo-sync/back-compat reasons; only the
  underlying bit-generation swapped.
- **Bounded draws are rejection-sampled, not modulo-reduced — no modulo bias.** Zandronum's
  `Random()` does `GenRand32() % mod` (naive modulo, biased whenever `mod` doesn't evenly divide
  2^32, as this doc's Zandronum-side bullet above notes). UZDoom's equivalent
  (`operator()(uint32_t bound)`, `m_random.h:121-123`, calling `GenRand32BoundExclusive`,
  `m_random.h:82-120`) instead discards draws that fall in a leftover partial range before taking
  the modulo, which its own comments describe as eliminating that bias entirely. So the "negligible
  small-range modulo bias" bullet above is a Zandronum-only property — on UZDoom, `Random(min, max)`
  is uniform with no such bias regardless of range size.
- **`CLIENTSIDE` scripts draw from a wholly separate stream, not a separately-seeded copy of the
  same one.** `DLevelScript::Random` picks between two distinct generator objects based on whether
  the running script is clientside: `pr_acs` (name `"ACS"`, `p_acs.cpp:537`) for ordinary scripts,
  or `pr_csacs` (name `"CSACS"`, `p_acs.cpp:538`, an `FCRandom` — a subclass of `FRandom` that
  registers itself in a separate client-only list, `m_random.h:218-226`) for clientside ones
  (`p_acs.cpp:3635`). This is a different design from what this doc found in Zandronum: there, every
  `Random()` call (clientside or not) reads the single `"ACS"`-named stream, so on a given client a
  `CLIENTSIDE` script's draws and that client's non-clientside draws interleave into the same
  sequence. On UZDoom they never interact at all — a `CLIENTSIDE` script's `Random()` calls consume
  only `"CSACS"` draws, completely independent of `"ACS"`-stream draws happening on the same client
  or server, rather than merely being a locally-seeded instance of the same named stream.
- **The `compat_oldrandom` mechanism has no UZDoom analog to not-affect.** Searching UZDoom's source
  for the compat-flags name and enum value this doc's Zandronum section cites (`zacompatflags`,
  `ZACOMPATF_*`) turns up nothing at all — the whole legacy-table compatibility path Zandronum keeps
  around for `Random2()`/no-arg draws doesn't exist in this engine family. That bullet's substance
  (nothing about `Random(min, max)` ever touched the legacy path) is trivially still true on UZDoom,
  but for a different reason: there is no legacy path left to not touch, not because this particular
  call site was carved out from a still-present one.
