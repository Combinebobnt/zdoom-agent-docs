# Zandronum-vs-UZDoom ACS bytecode compatibility

**Tier:** A (every claim traced directly to the relevant opcode-dispatch source in both engines
and to `zt-bcc`'s own extension binding, not inferred or wiki-sourced).
**Applies to:** UZDoom=yes, Zandronum=yes — UZDoom is a GZDoom-family fork, checkout currently
behind its own `origin/trunk`; see `../../shared/AUTHORING.md`'s "Engine scope" caveats before
treating any UZDoom-side line number here as stable upstream.
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** derived directly from the Zandronum source (`src/p_acs.h`, `src/p_acs.cpp`), the
UZDoom source (`src/playsim/p_acs.cpp`, `src/playsim/p_acs.h`), and the `zt-bcc` compiler source
(`src/codegen/pcode.h`, `lib/zcommon.bcs`, `src/main.c`) while investigating why an ACS object
file compiled for Zandronum, loaded under UZDoom, produces wrong behavior with no error message —
found while scoping a real project's Zandronum-to-UZDoom port.

Compiling an ACS/BCS source file for Zandronum and loading the resulting object under UZDoom does
not fail to load, and does not crash. It silently produces wrong behavior at exactly the call
sites that use a Zandronum-only extension, with zero diagnostic output — which is a much more
dangerous failure mode than either a compile error or a crash, and worth understanding before
assuming a "no errors in the log" run is correct.

**Re-verified 2026-08-17** against the pinned checkouts in `Verified against:` above. What was
actually re-checked against current source, not just re-read as prose: the full `PCD_*` enum on
both engines, extracted and diffed index-by-index (0–117 identical, 118/129/130/381 diverge exactly
as the section below describes, 131–380 identical — confirmed by a full positional diff, not a
spot check); the `PCD_ISMULTIPLAYER`/`PCD_ISNETWORKGAME` case bodies' actual semantics (Zandronum's
server-or-client-mode check vs. UZDoom's plain `netgame` push); the `CallFunction` dispatcher's
`default: break;`/`return 0` and the `PCD_CALLFUNC` handler's unconditional stack rebalance; all
three `SFLG` bits' definitions on both engines; the 18 chunk tags `zt-bcc` emits and their presence
in UZDoom's loader (`ALIB` absent from both, as already noted); `LOADACS`'s per-map-load scan on
both engines; and that `#nocompact` is a real `zt-bcc` pragma. All of it held exactly as already
written below — this pass found no divergence, only confirmation. See `../../shared/AUTHORING.md`'s
Engine scope caveats for the local Zandronum checkout's known working-tree drift.

## Base PCD opcodes: numerically identical, with one live collision

Comparing the two engines' `PCD_*` enums (Zandronum `src/p_acs.h`, UZDoom
`src/playsim/p_acs.cpp`) index-by-index: everything below index 118 and from 131 to 380 lines up
exactly. Three narrow exceptions:

- **Index 118**: Zandronum's `PCD_ISMULTIPLAYER` vs. UZDoom's `PCD_ISNETWORKGAME` — same opcode
  number, different semantics. Zandronum pushes whether the game is running in server *or*
  networked-client mode; UZDoom pushes the plain `netgame` flag. Both compile from the same
  `zcommon.bcs` name (`IsMultiplayer()`/`IsNetworkGame()` are exposed as separate BCS calls
  mapping to this one opcode), so a script using either one runs on both engines without erroring,
  but can read a different truth value in an edge case (e.g. a networked client that isn't itself
  hosting).
- **Indices 129/130**: Zandronum's `PCD_GETINVASIONWAVE`/`PCD_GETINVASIONSTATE` have no
  corresponding case in UZDoom's interpreter at all — calling either from a Zandronum-compiled
  object hits UZDoom's **unknown-PCD path**, which is loud (see below), not silent. **Reachable
  from ordinary `zt-bcc` compilation, not just hand-assembled bytecode: `zt-bcc/src/codegen/pcode.h`
  declares `PCD_GETINVASIONWAVE`/`PCD_GETINVASIONSTATE` at these exact slots (matching Zandronum's
  numbering, not UZDoom's — the one place `pcode.h` doesn't follow UZDoom numbering at every index
  it defines), and `zt-bcc/src/builtin.c`'s `g_funcs[]` table binds the ordinary source-level calls
  `getinvasionwave()`/`getinvasionstate()` straight to them, unconditionally, in the same table
  that binds `delay()`/`random()`/`thingcount()`.** A plain BCS script calling either function (a
  real Invasion-gametype status query, not a contrived example) compiles via normal `bcc` and hits
  this path — no hand-assembly required. UZDoom's own `PCD_LSPEC6`/`PCD_LSPEC6DIRECT` enum entries
  at these slots carry a source comment reading "These are never used," confirming the gap is real
  and permanent, not a build artifact of this checkout.
- **Index 381**: Zandronum's `PCD_GETTEAMPLAYERCOUNT` vs. UZDoom's `PCD_LSPEC5EX` — latent between
  the engines but unreachable from `zt-bcc`-compiled output, same as 129/130, **but a third,
  worse failure mode if this opcode is ever hand-assembled: not a loud unknown-PCD termination.**
  UZDoom *does* have a `case PCD_LSPEC5EX:` at this index (`src/playsim/p_acs.cpp`), unlike
  129/130's genuinely-missing cases, so a Zandronum-compiled `PCD_GETTEAMPLAYERCOUNT` instruction
  runs UZDoom's `PCD_LSPEC5EX` handler instead of hitting the unknown-PCD path. The two opcodes'
  operand shapes don't match: Zandronum's version reads one stack value (a team index) and no
  inline operand; UZDoom's reads an inline `NEXTWORD` immediately following the opcode (the line
  special number) plus five stack values. The result is silent and doubly wrong — `NEXTWORD`
  misinterprets whatever bytecode word comes next as a special number, five stack slots get
  popped when the calling script only pushed one (pulling in unrelated values left on the stack by
  earlier instructions as "arguments"), and `P_ExecuteSpecial` then actually runs a line special
  with that garbage special number and those garbage args — a real side-effecting engine action,
  not just a wrong return value, and the corrupted instruction-stream read means the interpreter
  is now desynced from the following bytecode too.

## Extension functions (ACSF/CALLFUNC): the real divergence, and it's silent

This is the mechanism that actually matters for a Zandronum→UZDoom port, and it's a design
choice on UZDoom's side, not an oversight: **ZDoom reserved ACSF (CALLFUNC) index range 100–199
for Zandronum's own extensions and implements none of them.** UZDoom's own ACSF enum jumps from
its own function at index 99 straight to unrelated functions starting at 200, with a comment
(not reproduced here — GPL-3.0, see `../../shared/AUTHORING.md`) explicitly noting the gap exists
because Zandronum's extensions live there and must be skipped.

Zandronum's own extension functions are bound in `zt-bcc/lib/zcommon.bcs` as raw negative-numbered
externs (`-100:ResetMap():bool`, `-101:PlayerIsSpectator(int):int`, `-102:ConsolePlayerNumber():int`,
and so on through the 100–186 range) — a plain, unconditional list with no `#ifdef` gate. Calling
one of these from BCS compiles straight to `PCD_CALLFUNC` with that absolute index as the function
number (`zt-bcc/src/codegen/expr.c`'s `c_pcd(codegen, PCD_CALLFUNC, argc, impl->id)`).

**What happens when a Zandronum-compiled object calls one of these under UZDoom:** UZDoom's
`CallFunction` dispatcher is a plain `switch` over the ACSF index with a `default: break;`
falling through to `return 0` — no error, no log line, nothing. The `PCD_CALLFUNC` handler that
invokes it unconditionally rebalances the interpreter stack around the call regardless of which
branch fired, so the script's stack stays consistent and execution just continues with a `0`
result in place of whatever `PlayerIsSpectator`/`ConsolePlayerNumber`/etc. was supposed to return.
**Contrast this with an unknown *PCD*** (a base opcode UZDoom's interpreter has no `case` for at
all, e.g. `GetInvasionWave()`/`GetInvasionState()` above): that path prints `"Unknown P-Code %d in
%s"` naming the script and terminates it. The two failure modes look similar from the "Zandronum-
only function" description but are opposite in observability — an unknown ACSF is invisible, an
unknown PCD is loud and fatal to that script. Which one a given Zandronum extension hits depends
entirely on whether it's bound as a base opcode or a CALLFUNC index. The overwhelming majority of
Zandronum-specific functionality is reserved as CALLFUNC indices (silent) — the 100-199 ACSF block
above is nearly 90 functions wide — but **that's a Zandronum-side numbering choice, not a `zt-bcc`
compiler-table limitation**: `zt-bcc`'s own PCD table does have room for (and does declare)
Zandronum-numbered base opcodes at 129/130 (see above) and 381 (see "Index 381" above), so the
"almost everything goes through CALLFUNC" pattern is empirical, not structurally guaranteed — don't
assume a not-yet-audited Zandronum extension is silent without checking which mechanism it uses.

**No compiler-side fix exists.** `zt-bcc` has no engine-target flag at all — `src/main.c`'s
option parser has no `--target`/`--engine` switch, and `zcommon.bcs`'s Zandronum extension block
has no conditional guard around it. Every `zt-bcc` compile emits code that *can* call these
functions if the source does; whether that's safe is purely a function of what engine the
resulting object gets loaded into. A source-level `#ifdef`/build-define split (`zt-bcc` does
support `-D`/`#ifdef`) is the only way to keep one source tree portable — the compiler itself
won't stop you from shipping a silently-wrong UZDoom build.

**Which specific functions land where** (checked for a real project's actual call sites, not
exhaustive over all ~87 Zandronum extensions): `PlayerIsSpectator`, `ConsolePlayerNumber`,
`GetPlayerLivesLeft`, `RequestScriptPuke`/`NamedRequestScriptPuke`, `SystemTime`, `Strftime` are
all in the reserved-and-unimplemented 100–199 CALLFUNC range — every one of these silently
returns 0 under UZDoom. `GetUserCVar`, `PlayerIsBot`, `GetPlayerInput` (including the
`MODINPUT_*` argument enum) and `ConsoleCommand` are **not** Zandronum-specific despite living
alongside Zandronum-only code in some projects' call sites — they're ordinary ZDoom-family
opcodes/ACSF entries present and correct on both engines. `ConsoleCommand` specifically is
recognized on both but is a deliberate no-op on UZDoom (prints a "doesn't support execution of
console commands from scripts" message every call) rather than silent — worth knowing since it
looks like it belongs in the silent-failure group but isn't.

**A silent-0 return can be coincidentally correct.** In a singleplayer context specifically,
`ConsolePlayerNumber()` → 0 is the right answer (the console player *is* player 0), and
`PlayerIsSpectator(n)` → 0 (false) is right too (no spectators exist in SP). This can make a
Zandronum-authored script that never touches multiplayer paths look like it "just works" under
UZDoom even though every one of those calls is silently wrong in general — don't take "looks fine
in a quick SP test" as evidence the port is clean; audit each reserved-range call site instead of
relying on the coincidence.

## The SFLG script-flag bit that means opposite things

Both engines parse the `SFLG` chunk into a per-script flags word with no validation of unknown
bits, but two of the three bits Zandronum defines carry different meaning on UZDoom:

- Bit `0x0001` (`SCRIPTF_Net`, "safe to puke in multiplayer") and bit `0x0004`
  (`SCRIPTF_Busy`, "not subject to the runaway-script instruction limit") agree bit-for-bit and
  semantically between the two engines.
- Bit `0x0002` is Zandronum's `SCRIPTF_ClientSide` (marks a script as running only on the client
  that triggered it — see [Client-side scripting](clientside-scripting.md)). UZDoom defines the
  same bit as `SCRIPTF_Ignored`, with an explicit comment that the flag has no meaning on that
  engine. A `CLIENTSIDE` script compiled for Zandronum therefore just runs as an ordinary script
  under UZDoom — not an error, but a behavior change worth knowing about deliberately rather than
  discovering by observing a script run server-side that was written assuming client-only
  execution.

## Everything else that loads cleanly

Spot-checked while investigating a real port and worth recording so it isn't re-derived: all 19
chunk types `zt-bcc` emits (`SPTR`, `SVCT`, `SFLG`, `SNAM`, `FUNC`, `FNAM`, `STRL`, `STRE`, `MINI`,
`ARAY`, `AINI`, `LOAD`, `MIMP`, `AIMP`, `SARY`, `MEXP`, `MSTR`, `ASTR`, `ATAG`; `ALIB` is written
empty and read by neither engine) are handled by UZDoom's object-loading code — including `STRE`,
the encrypted counterpart of `STRL` emitted instead of it when `encrypt_str` is set
(`zt-bcc/src/codegen/chunk.c`), found missing from this count during the 2026-08-17 audit; the
`ACSE`/`ACSe` object formats and `#nocompact` large-object layout are both accepted; `LOADACS` is
fully supported with the same unconditional-per-map-load semantics as Zandronum.

## See also

- [Client-side scripting](clientside-scripting.md) — the `CLIENTSIDE`/`NET` mechanism whose SFLG
  bit meaning diverges above.
- [Crash-and-bug checklist](crash-and-bug-checklist.md) — this file's silent-CALLFUNC-return-0
  finding is exactly the shape of bug that checklist exists to catch; worth cross-linking if a
  future pass indexes cross-engine-port findings there too.
