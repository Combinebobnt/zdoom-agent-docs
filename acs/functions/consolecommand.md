# `void ConsoleCommand(str consolecommand [, int, int])`

Runs a single console command as if typed at the local console. Compiler builtin
(`PCD_CONSOLECOMMAND`), implementation in `p_acs.cpp:11284-11291`.

**Bucket:** compiler builtin.

- **The two optional trailing ints are dead.** `zt-bcc`'s own signature (`builtin.c:77`:
  `{ "consolecommand", ";s;ii" }`) accepts up to 2 extra int args and they compile fine, but
  `PCD_CONSOLECOMMAND`'s handler only ever reads `STACK(3)` (the string) and pops all 3 stack
  slots (`sp -= 3`) without looking at the other two — there is no code path that uses them for
  anything. Confirmed this isn't a stub for some other command: `PCD_CONSOLECOMMANDDIRECT`
  (`consolecommand`'s inline-string variant, same opcode family) is a separate 3-operand opcode
  and doesn't touch the trailing-int path either.
- **Not a static blacklist checked in one place.** The wiki's list of disallowed commands
  (`unbindall`, `unbind`, `bind`, `quit`, `exit`, `logfile`, `alias`/alias commands, `screenshot`,
  `dumpmap`, `say`, `say_team`, `sv_banfile`, `sv_banexcemptionfile`, `sv_adminlistfile`, `error`,
  `error_fatal`, `crashout`, `wait`) is enforced piecemeal: each `CCMD`'s own handler calls
  `ACS_IsCalledFromConsoleCommand()` (`p_acs.cpp:13648`, true only during this function's `C_DoCommand`
  call, via a static bool the engine flips around the call at `p_acs.cpp:11286-11289`) and returns
  early if true. Spot-verified for `quit`/`exit` (`c_cmds.cpp:173-189`), key binding commands
  (`c_bind.cpp:534`, `:702`, `:717` — covers `bind`/`unbind`/`unbindall`), and `wait`
  (`c_dispatch.cpp:792-793`, specifically called out in-source as closing an exploit: `wait` would
  otherwise let a queued command run *after* the ACS-command context ends, bypassing these checks).
  **Practical implication: this list is not exhaustive by construction** — any new `CCMD` added to
  this fork is console-callable via `ConsoleCommand` from ACS unless its author remembered to add
  the same guard. Don't assume a command is safe against `ConsoleCommand` just because it's absent
  from the wiki's list.
- **Aliases are blocked as a category, not by name.** `c_dispatch.cpp:673-677`:
  `if (ACS_IsCalledFromConsoleCommand() && com->IsAlias()) return;` — *every* alias (KEYCONF- or
  runtime-defined via the `alias` CCMD) is silently rejected, matching the wiki's "including any
  alias commands" note.
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
  `c_cvars.cpp:194-224`) its pre-change value is stashed in a `SavedValues` list, and restored
  (`c_cvars.cpp:1749-1760`) once `cl_protectcvars` is checked at exit — i.e. the change is visibly
  in effect for the rest of the session but does not persist into the saved config, matching the
  wiki's "will not be saved permanently... restored upon exiting the game." A cvar can opt out of
  even the temporary set by carrying `CVAR_NOSETBYACS` itself (`c_cvars.cpp:198-199`), independent
  of `cl_protectcvars`.
- **CVARINFO/`archivecvar` interaction is narrower than the wiki implies.** The actual mechanism
  (`c_cvars.cpp:1892-1896`) is: a mod cvar created via the `set`/`archivecvar` CCMDs is initially
  flagged `CVAR_IGNORE` (invisible to ACS); the *first* time it's set through `ConsoleCommand`,
  that flag is cleared so ACS can subsequently read it. This makes such a cvar usable from ACS —
  it does not mean CVARINFO silently "redefines" the cvar's identity as the wiki phrasing
  suggests.
- If called from a `CLIENTSIDE` script, the command runs on that client's local machine (matches
  the wiki) — this is just normal `C_DoCommand` execution context, no ACS-specific machinery
  beyond what's documented above.

**Example:**

```
ConsoleCommand("sv_survivalcountdowntime 3");
```

**Returns:** nothing (`void`).

**Provenance:** wiki page `ConsoleCommand - Zandronum Wiki.html` (`_intake/`, retrieved
2026-07-28, `oldid=1620`) + source-verified (`p_acs.cpp:11284-11291,13648`, `c_dispatch.cpp:673-677,749,792-793,1160-1168`,
`c_cmds.cpp:173-189,965,982,1009`, `c_bind.cpp:534,702,717`, `p_writemap.cpp:36`,
`c_cvars.cpp:95,194-224,1749-1760,1892-1896`, `builtin.c:77`). The wiki's command-denylist and
`cl_protectcvars` claims hold; the dead trailing-int params, the "no single blacklist" mechanism,
and the `UNSAFE_CCMD`-vs-`ACS_IsCalledFromConsoleCommand` distinction are this doc's
source-verified additions, not wiki-sourced. **Engine:** Zandronum 3.2.1 (verified against
the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.
