# `restart;`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `restart - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=Restart&oldid=38214`), verified against
the Zandronum source's `src/p_acs.cpp` and the zt-bcc source's `src` on 2026-07-29. The wiki page is a
two-sentence stub (usage + one example); everything below "Mechanism" comes from reading
`PCD_RESTART`'s implementation and the `DLevelScript` constructor directly, because the wiki
never mentions the one thing that actually matters here: **local variables are not reset.**
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** none of the three — this is a **compiler statement/keyword**, not a callable function
at all. `restart` never appears in `zt-bcc/src/builtin.c`'s `g_funcs[]` (compiler-builtin bucket)
or `zcommon.bcs`'s `special` table (action-special/extension-function buckets); it's tokenized as
`TK_RESTART` (`zt-bcc/src/parse/token/info.c:110`) and parsed directly by the statement grammar
(`read_script_jump()` in `zt-bcc/src/parse/stmt.c:567-580`, alongside `terminate`/`suspend` —
`semantic/stmt.c:869`'s `SCRIPT_JUMP_TOTAL` triple). No parentheses, no arguments, bare
`restart;`. Compiles straight to the zero-operand opcode `PCD_RESTART`
(`zt-bcc/src/codegen/pcode.h:74`, emitted at `zt-bcc/src/codegen/stmt.c:1149-1150`).

Jumps execution back to the top of the currently-running script, in place — it is a `goto`, not a
fresh re-invocation.

- **Compile-time restriction (not on the wiki):** legal only directly inside a script body,
  never inside a function and never inside a string message-building block (`test_script_jump()`,
  `zt-bcc/src/semantic/stmt.c:867-880`) — `bcc` rejects it with `"restart statement outside
  script"` otherwise, same restriction as bare `terminate;`/`suspend;`.
- **Mechanism:** `PCD_RESTART` (`p_acs.cpp:10585-10592`) does exactly two things: looks up the
  running script's own `ScriptPtr` via `activeBehavior->FindScript(script)` and resets `pc` to
  `GetScriptAddress(scriptp)`. Nothing else in the interpreter's state — `localvars`, `activator`,
  `activationline`, `backSide`, delay/wait state, etc. — is touched.
- **Local variables and script arguments are *not* reinitialized — this is the part the wiki
  omits entirely.** `localvars` is only zeroed and populated from the caller's `args[]` once, in
  the `DLevelScript` constructor (`p_acs.cpp:13083-13090`, `memset(localvars, 0, ...)` followed by
  copying in `args[i]`), which runs when the script is first spawned — not on `restart`. A script
  declared `Script 1 (int arg1) { ... restart; ... }` keeps whatever value `arg1` (and every other
  local) held at the moment of the `restart`, not the value it was originally called with. Any
  local mutated before the `restart` carries its mutated value into the next pass; a script relying
  on "restart re-runs from a clean slate" will silently read stale state instead.
- **Runaway-loop interaction matches the wiki's caution, mechanically:** the wiki says you need
  "at least one delay ... or you will get the runaway error." The actual guard is
  `RunScript()`'s per-invocation instruction counter (`p_acs.cpp:9226-9230`,
  `++runaway > 2000000` prints `"Runaway <script> terminated"` and force-removes the script) —
  it counts bytecode instructions executed inside one call to `RunScript()`, and `PCD_RESTART`
  does not exit that call (unlike `Delay`/`TagWait`/`ScriptWait`/`PolyWait`/`Suspend`, which set
  `state` away from `SCRIPT_Running` and return control to the caller). A tight
  `restart;`-only loop with no intervening blocking call burns through the 2,000,000-instruction
  budget in the same tic and gets force-terminated; a `Delay(N>=1)` (or other latent call) before
  the `restart` is what actually yields and resets the counter on the next tic — see
  [Delay](delay.md) for the `Delay(0)`-is-not-a-safe-no-op trap that defeats this same guard.
- **Cross-reference for a future family consolidation:** `restart`/`terminate`/`suspend` are
  literally the same grammar production in `bcc` (`SCRIPT_JUMP_*`, `semantic/stmt.c:869`) and
  share the identical "outside script" / "inside msgbuild block" restrictions — a natural
  `families/script-jump.md` candidate if/when `terminate.md`/`suspend.md` exist. Not created here
  per this batch's family-collision guard — left for a later pass to consolidate if warranted.
