# `int Random(int min, int max)`

Returns a pseudo-random integer in `[min, max]` inclusive. Compiler builtin (`g_funcs[]` entry
`"random"`, the zt-bcc source's `src/builtin.c:37`), implementation in `DLevelScript::Random`
(the Zandronum source's `src/p_acs.cpp:3884-3892`), invoked from `case PCD_RANDOM:`
(`p_acs.cpp:10501-10503`) when both arguments are runtime values, or `PCD_RANDOMDIRECT`/
`PCD_RANDOMDIRECTB` (`p_acs.cpp:10505-10513`) when the compiler can encode one/both arguments as
immediates — all three opcodes call the same `Random(min, max)` function, so there is no behavior
difference between them, just a bytecode-size optimization.

**Bucket:** compiler builtin. There is no BCS-side declaration for it in `zcommon.bcs` (nothing
matches `\brandom\b` there) — unlike an extension function or action special, this name is wired
straight into the compiler's own builtin table, not textually declared as ordinary BCS source.

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
  the `min, max` (ascending) case; this fork (and, per this same function existing verbatim
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
- **No explicit client/server or client/client netcode sync found for `pr_acs`.** Searching
  the Zandronum source's `src` turns up exactly one reader (`p_acs.cpp:3891`) and one definition
  (`p_acs.cpp:183`) for `pr_acs` — no network replication code references it. Server-executed
  (default) scripts are authoritative as usual and their *effects* (spawns, damage, etc.)
  replicate to clients normally, but a `CLIENTSIDE` script's own `Random()` calls run against that
  client's own local `pr_acs` instance, independently of the server's and of every other client's.
  Don't rely on `Random()` producing the same sequence across machines from inside a `CLIENTSIDE`
  script — it wasn't built for that, and nothing in this fork's source synchronizes it.
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

**Provenance:** wiki page `Random - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-28,
`oldid=54552`) + source-verified against the Zandronum source (`p_acs.cpp:183,3884-3892,10501-10513`,
`m_random.h:56-61`, `m_random.cpp` header comments) and the zt-bcc source's `src/builtin.c:37`. The
wiki's core inclusive-range description holds; the argument-order tolerance, shared-stream/demo-sync
nature, clientside-sync caveat, fixed-point/modulo notes, and the `compat_oldrandom` non-effect
are this doc's source-verified additions (not on the wiki page, which is written for vanilla ZDoom
single-player/demo context without Zandronum's client/server split in mind). **Engine:** Zandronum 3.2.1 (verified against
the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.

**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.
