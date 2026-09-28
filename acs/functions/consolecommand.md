# `void ConsoleCommand(str consolecommand [, int, int])`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** wiki page `ConsoleCommand - Zandronum Wiki.html` (`_intake/`, retrieved
2026-07-28, `https://wiki.zandronum.com/w/index.php?title=ConsoleCommand&oldid=1620`) + source-verified (`p_acs.cpp:11284-11291,13648`, `c_dispatch.cpp:673-677,749,792-793,1160-1168`,
`c_cmds.cpp:173-189,965,982,1009`, `c_bind.cpp:534,702,717`, `p_writemap.cpp:36`,
`c_cvars.cpp:95,194-224,1749-1760,1892-1896`, `builtin.c:77`; corrections at
`bdd0f7beb` also read `c_dispatch.cpp:587-743,753-832,1647,1719-1724`, `c_expr.cpp:740,744`,
`c_cmds.cpp:743-756`, `c_cvars.cpp:1738,1915`, `gameconfigfile.cpp:463-476,505-518`,
`sv_ban.cpp:113,126`, `sv_main.cpp:300`). The wiki's command-denylist and
`cl_protectcvars` claims hold; the dead trailing-int params, the "no single blacklist" mechanism,
and the `UNSAFE_CCMD`-vs-`ACS_IsCalledFromConsoleCommand` distinction are this doc's
source-verified additions, not wiki-sourced.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.

Runs a single console command on the local machine. Compiler builtin
(`PCD_CONSOLECOMMAND`), implementation in `p_acs.cpp:11284-11291`. The string goes straight to
`C_DoCommand` (`c_dispatch.cpp:587-743`), not through `AddCommandString` like typed console
input. So `;` does not separate commands (the rest of the line becomes arguments of the first
command), and `wait` is not intercepted: `ConsoleCommand("wait 5")` just prints `Unknown command
"wait"`.

- **The two optional trailing ints are dead.** `zt-bcc`'s own signature (`builtin.c:77`:
  `{ "consolecommand", ";s;ii" }`) accepts up to 2 extra int args and they compile fine, but
  `PCD_CONSOLECOMMAND`'s handler only ever reads `STACK(3)` (the string) and pops all 3 stack
  slots (`sp -= 3`) without looking at the other two — there is no code path that uses them for
  anything. Confirmed this isn't a stub for some other command: `PCD_CONSOLECOMMANDDIRECT`
  (`consolecommand`'s inline-string variant, same opcode family) is a separate 3-operand opcode
  and doesn't touch the trailing-int path either.
- **Not a static blacklist checked in one place.** The wiki's list of disallowed commands
  (`unbindall`, `unbind`, `bind`, `quit`, `exit`, `logfile`, `alias`/alias commands, `screenshot`,
  `dumpmap`, `say`, `say_team`, `sv_banfile`, `sv_banexemptionfile`, `sv_adminlistfile`, `error`,
  `error_fatal`, `crashout`, `wait`) is enforced piecemeal. Most entries are `CCMD`s whose own
  handler calls `ACS_IsCalledFromConsoleCommand()` (`p_acs.cpp:13648`, true only during this
  function's `C_DoCommand` call, via a static bool the engine flips around the call at
  `p_acs.cpp:11286-11289`) and returns early if true. Spot-verified for `quit`/`exit`
  (`c_cmds.cpp:173-189`) and key binding commands (`c_bind.cpp:534`, `:702`, `:717`, covering
  `bind`/`unbind`/`unbindall`). The rest use other checkpoints. `sv_banfile`,
  `sv_banexemptionfile` and `sv_adminlistfile` are cvars flagged `CVAR_NOSETBYACS`
  (`sv_ban.cpp:113,126`, `sv_main.cpp:300`), refused in `SetGenericRep` (`c_cvars.cpp:198-199`).
  Aliases are refused by the dispatcher (next bullet). `wait` is guarded in `AddCommandString`
  (`c_dispatch.cpp:792-793`), which `ConsoleCommand` itself never calls. That guard matters when a
  command run this way feeds text back through `AddCommandString`, e.g. `test` (`c_expr.cpp:740,744`)
  or `exec`. Without it the rest of that line would be queued and run after the flag clears,
  bypassing these checks (the in-source comment names this exploit).
  **Practical implication: this list is not exhaustive by construction.** Any new `CCMD` added to
  the Zandronum engine fork is console-callable via `ConsoleCommand` from ACS unless its author
  remembered to add the same guard. For example, `exec` has no such guard (`c_cmds.cpp:743-756`).
  Don't assume a command is safe against `ConsoleCommand` just because it's absent from the
  wiki's list.
- **Aliases are blocked as a category, not by name.** `c_dispatch.cpp:673-677`: when the matched
  command is an alias and the call comes from `ConsoleCommand`, the dispatcher returns without
  running it. So *every* alias (KEYCONF- or runtime-defined via the `alias` CCMD) is silently
  rejected, matching the wiki's "including any alias commands" note.
- **`UNSAFE_CCMD`-flagged commands (e.g. `crashout`, `error_fatal`, `dumpmap`) are not blocked by
  the unsafe-execution-context mechanism** (`c_dispatch.cpp:1160-1168`,
  `FUnsafeConsoleCommand::Run`) **when called this way** — that mechanism only fires when
  `UnsafeExecutionContext` is explicitly set (e.g. by menu-triggered commands via
  `UnsafeExecutionScope`, `c_dispatch.cpp:749`), and `p_acs.cpp` never sets it around
  `PCD_CONSOLECOMMAND`. These three are still blocked, but via the same
  per-command `ACS_IsCalledFromConsoleCommand()` guard as everything else in the wiki's list
  (`c_cmds.cpp:965`/`:982`/`:1009` for `error`/`error_fatal`/`crashout`, `p_writemap.cpp:36` for
  `dumpmap`), not by the `UNSAFE_CCMD` wrapper — don't assume marking a future `CCMD` as
  `UNSAFE_CCMD` alone is sufficient to also block it from `ConsoleCommand`.
- **`cl_protectcvars` (confirmed real, `c_cvars.cpp:95`, `CVAR_ARCHIVE | CVAR_NOSETBYACS`,
  default `true`):** when a cvar is set via `ConsoleCommand` (`FBaseCVar::SetGenericRep`,
  `c_cvars.cpp:194-224`) its pre-change value is stashed in a `SavedValues` list. When the config
  is written (`C_ArchiveCVars`, `c_cvars.cpp:1738`, normally at exit) and `cl_protectcvars` is on,
  the cvar is force-set back to that value before it is saved (`c_cvars.cpp:1749-1760`). So the
  change is in effect for the rest of the session but does not persist into the saved config, matching the
  wiki's "will not be saved permanently... restored upon exiting the game." A cvar can opt out of
  even the temporary set by carrying `CVAR_NOSETBYACS` itself (`c_cvars.cpp:198-199`), independent
  of `cl_protectcvars`.
- **CVARINFO/`archivecvar` interaction is narrower than the wiki implies.** After CVARINFO is
  parsed, the engine reads the config file's `.Mod` sections, and any saved key that no loaded
  CVARINFO declares becomes a dummy string cvar flagged `CVAR_MOD | CVAR_IGNORE`
  (`gameconfigfile.cpp:463-476,505-518`), which ACS cannot see. A cvar freshly created by the
  `set` CCMD is not flagged this way (`c_cvars.cpp:1915`). The *first* time such a dummy is set
  through `ConsoleCommand`, `CmdSet` clears `CVAR_IGNORE` (`c_cvars.cpp:1892-1896`) so ACS can
  read it afterwards. That is what keeps mods that manage their own cvars with `set`/`archivecvar`
  working. It does not mean CVARINFO silently "redefines" the cvar's identity as the wiki phrasing
  suggests.
- If called from a `CLIENTSIDE` script, the command runs on that client's local machine (matches
  the wiki) — this is just normal `C_DoCommand` execution context, no ACS-specific machinery
  beyond what's documented above.

## Engine-family divergence: not implemented at all on UZDoom

Everything documented above — the per-`CCMD` denylist mechanism, alias blocking, the
`UNSAFE_CCMD`-vs-`ACS_IsCalledFromConsoleCommand()` distinction, `cl_protectcvars`, and the
CVARINFO/`archivecvar` interaction — is Zandronum-only and does not carry over. UZDoom's script
interpreter (`DLevelScript::RunScript`, `src/playsim/p_acs.cpp`) handles both `PCD_CONSOLECOMMAND`
and `PCD_CONSOLECOMMANDDIRECT` as a shared no-op case: it prints a console message stating that the
engine doesn't support running console commands from scripts, then discards the opcode's stack
arguments (or skips its inline operand bytes, for the direct-string variant) without executing
anything. No command ever runs, no cvar is ever set, and none of the Zandronum-side
denylist/`cl_protectcvars`/alias-blocking machinery is reachable because there's nothing left for
it to guard. The two optional trailing ints (dead on Zandronum too, see above) are equally inert
here.

**Example:**

```text
ConsoleCommand("sv_survivalcountdowntime 3");
```

**Returns:** nothing (`void`).
