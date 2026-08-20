# `terminate;`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `Terminate - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=Terminate&oldid=35855`), verified against
the Zandronum source's `src/p_acs.cpp` and the zt-bcc source's `src` on 2026-07-29.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** none of the three — a **compiler statement/keyword**, not a callable function, same
grammar production as `restart`/`suspend` (see [restart](restart.md) for the shared background).
`terminate` never appears in `zt-bcc/src/builtin.c`'s `g_funcs[]` or `zcommon.bcs`'s `special`
table; it's tokenized as `TK_TERMINATE` (`zt-bcc/src/parse/token/info.c:112`) and parsed by
`read_script_jump()` (`zt-bcc/src/parse/stmt.c:200,567-580`), which is also where `restart`/
`suspend` are routed (`SCRIPT_JUMP_TERMINATE` is in fact the reading's default `stmt->type`,
overridden only if the token was `TK_RESTART`/`TK_SUSPEND` — `stmt.c:569-577`). No parentheses, no
arguments, bare `terminate;`. Compiles to the zero-operand opcode `PCD_TERMINATE`
(`zt-bcc/src/codegen/pcode.h:6`, emitted at `zt-bcc/src/codegen/stmt.c:1078` for the
explicit-statement case).

Ends the currently-running script immediately. Unlike `restart`, there's no re-lookup or jump —
it just flips the interpreter's `state` field, which is enough to end everything.

- **Compile-time restriction (matches the wiki's implicit "no example outside a script"):**
  legal only directly inside a script body, never inside a function and never inside a string
  message-building block — the exact same `test_script_jump()` check documented for `restart`
  (`zt-bcc/src/semantic/stmt.c:867-880`), since `terminate`/`restart`/`suspend` share one semantic
  test. `bcc` rejects a bare `terminate;` inside a user function with `"terminate statement
  outside script"`.
- **Mechanism:** `PCD_TERMINATE` (`p_acs.cpp:9254-9257`) does one thing —
  `state = SCRIPT_PleaseRemove;` — no lookup, no stack unwind, no pointer/local cleanup. The
  interpreter's main loop is `while (state == SCRIPT_Running)` (`p_acs.cpp:9226`), so this
  unconditionally exits that loop on the next iteration check; no code after the `terminate;`
  statement ever runs, in contrast to a plain `return;`/falling off a function's closing brace,
  which can still have deferred/epilogue work.
- **Actual removal happens synchronously, same call:** back in `RunScript()`'s post-loop cleanup
  (`p_acs.cpp:13026-13032`), `state == SCRIPT_PleaseRemove` triggers an immediate `Unlink()` and
  removal from `controller->RunningScripts` before `RunScript()` even returns to its caller — a
  terminated script is fully gone (not just flagged) by the time the statement that triggered it
  finishes executing.
- **The wiki's "no need to add `terminate` at the very end of a script" claim is verified true
  in this toolchain, and stronger than the wiki implies:** `write_script()`
  (`zt-bcc/src/codegen/dec.c:110-121`) unconditionally appends its own `PCD_TERMINATE` right after
  the compiled script body (`c_pcd(codegen, PCD_TERMINATE);` at `dec.c:121`), regardless of
  whether the script's source ever wrote one. A bare `return;` inside a script (not a function)
  also compiles to the identical `PCD_TERMINATE` opcode (`zt-bcc/src/codegen/stmt.c:1078`,
  `visit_return`'s `!stmt->is_func` branch) — so `terminate;`, a value-less `return;`, and
  falling off the closing brace are three spellings of exactly the same effect in a script.
- **Return value shares this file's "always true" footgun by a different route:** this bare
  statement only ends the *calling* script and has no return value of its own. The *other*
  Terminate mechanism the wiki cross-references — `ACS_Terminate`/`Acs_NamedTerminate`, which
  target an arbitrary *other* script by number/name and route through action special
  `LS_ACS_Terminate` — is a completely different call with its own always-`true`-regardless-of-
  outcome quirk; see [ACS_NamedTerminate](acs_namedterminate.md) rather than assuming anything
  here applies to it.
- **Cross-reference:** `terminate`/`restart`/`suspend` are the same grammar production
  (`SCRIPT_JUMP_TOTAL` triple, `semantic/stmt.c:869`) and share the identical "outside script" /
  "inside msgbuild block" restrictions. Not consolidated into a `families/script-jump.md` here —
  left for a later pass per the wiki-intake batch's family-collision guard.
