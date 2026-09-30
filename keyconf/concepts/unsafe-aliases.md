# Unsafe aliases (KEYCONF-defined aliases)

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/common/console/c_dispatch.cpp`,
`c_dispatch.h`, `c_cvars.cpp`, `src/gameconfigfile.cpp` and `src/d_main.cpp`, and the Zandronum
source's `src/c_dispatch.cpp`, `c_dispatch.h`, `c_cvars.cpp`, `gameconfigfile.cpp` and
`d_main.cpp`. The slot, re-alias, `wait`, cvar-save and pre-existing-alias behavior below was
also observed live on both engines with a probe KEYCONF (DOOM2 MAP01, throwaway config file).

An `alias` line in KEYCONF does not create an ordinary alias. It creates an **unsafe alias**
(`FUnsafeConsoleAlias`), whose body runs inside an "unsafe execution context" every time it is
triggered later: from a key bind, the console, or another alias. That context refuses a fixed set
of dangerous commands and restricts cvar changes. It is the only way a mod can package commands
for the player from KEYCONF, since KEYCONF itself only accepts nine commands (see
[the lump concept](keyconf-lump.md)). Syntax and argument substitution are in
[`console/notes/alias.md`](../../console/notes/alias.md).

## How an alias is stored: two slots

Every alias, KEYCONF or not, holds two command strings (`m_Command[2]` in `c_dispatch.h`):

- **Slot 0 is saved** to the config file's `[<game>.ConsoleAliases]` section at exit.
- **Slot 1 is never saved.**
- **When the alias runs, slot 1 wins** if it is non-empty; otherwise slot 0 runs (UZDoom
  `c_dispatch.cpp:925`, Zandronum `c_dispatch.cpp:1556`).

A KEYCONF alias is created with its body in slot 1 and slot 0 empty (the `FUnsafeConsoleAlias`
constructor passes `noSave=true`; UZDoom `c_dispatch.h:158`, Zandronum `c_dispatch.h:175`). So
**a KEYCONF alias is never written to the player's config**: `FConsoleAlias::Archive` writes only
a non-empty slot 0 (UZDoom `c_dispatch.cpp:724-731`, Zandronum `c_dispatch.cpp:1351-1358`). It is
recreated from the lump on every startup instead.

Typing `alias` with no arguments lists both slots in different colors: slot 0 in yellow, slot 1 in
orange (`FConsoleAlias::PrintAlias`). A KEYCONF alias shows up orange.

"Unsafe" is a property of the alias **object**, not of the body text. The class is fixed when the
alias is first created; later re-aliasing changes the text in a slot but never the class. Most of
the surprises below follow from that.

## What the unsafe context restricts

`FUnsafeConsoleAlias::Run` sets the global `UnsafeExecutionContext` flag for the duration of the
body (a scope object that restores the previous value on exit; UZDoom `c_dispatch.cpp:980-984`,
Zandronum `c_dispatch.cpp:1612-1616`). While it is set:

### Unsafe CCMDs are refused

A command declared with `UNSAFE_CCMD` is an `FUnsafeConsoleCommand`, whose `Run` prints
`Cannot execute unsafe command <name>` (red text, name in gold) and returns without running
(UZDoom `c_dispatch.cpp:501-509`, Zandronum `c_dispatch.cpp:1160-1169`). The rest of the alias body
still runs.

Unsafe on both engines: `exec`, `logfile`, `error_fatal`, `crashout`, `unbindall`, `load`, `save`,
`writeini`, `atexit`, `playlist`, `open`, `timedemo`, `clearnodecache`, `writewave`, `writemidi`.
UZDoom only: `playdemo`, `screenshot`, `recordmap`, `setdate`, `debug_restart`. Zandronum only:
`restart`, `dumpmap`, `writeopl`.

Not on either list, so allowed from an unsafe alias: `bind`, `unbind`, `alias` itself, `set` and
the other cvar commands (restricted separately, below), and every ordinary gameplay command.

### Cvar changes

The two engines handle this differently. See "Engine-family divergence" below; in short,
Zandronum refuses the change, UZDoom applies it but keeps it out of the saved config. On both,
**a cvar flagged `CVAR_MOD` is exempt**. That flag is set on every cvar declared in a CVARINFO lump
(UZDoom `d_main.cpp:1844`, Zandronum `d_main.cpp:1726`), so a mod's own CVARINFO cvars can be set
freely from its KEYCONF aliases on both engines.

Only two paths are gated: `set` / the bare `<cvar> <value>` form (both go through
`FBaseCVar::CmdSet`) and `toggle`.

### What is not covered

- **Only the alias body is wrapped.** A key bound directly to a command string, for example via
  KEYCONF [`defaultbind`](../../console/notes/defaultbind.md), runs through the normal bind path
  (`AddCommandString`, no unsafe scope; UZDoom `c_bind.cpp:166-181`), so that string is not
  restricted. The same goes for a bind installed with `bind` from inside an unsafe alias body:
  `bind` is not an `UNSAFE_CCMD` on either engine, and bindings are saved to the config.
- **Nesting inherits the flag.** It is one global flag, so a normal alias called from inside an
  unsafe alias body is restricted too, and an unsafe alias called from a normal one sets it for its
  own body only.

## `wait` keeps the flag

A `wait` inside an alias body splits the line: the remainder is queued as a delayed command and
runs N tics later, after the alias has returned and the flag has been cleared. The queued command
records the flag's value when it was queued and restores it when it runs (UZDoom `FWaitingCommand`,
`c_dispatch.cpp:61-82`, queued at `:389`; Zandronum `DWaitingCommand`, `c_dispatch.cpp:248-270`,
queued at `:815`). So `alias x "wait 2; exec foo.cfg"` defined in KEYCONF still refuses the `exec`
two tics later. On Zandronum the flag is also serialized with the waiting command
(`DWaitingCommand::Serialize`, `c_dispatch.cpp:235-239`).

## Re-aliasing a KEYCONF alias

The `alias` CCMD, given a name that already exists as an alias, calls
`Realias(command, noSave)` with `noSave = ParsingKeyConf` (UZDoom `c_dispatch.cpp:829`, Zandronum
`c_dispatch.cpp:1460`). `Realias` then forces `noSave` on whenever slot 1 is already non-empty
(UZDoom `c_dispatch.cpp:954-965`, Zandronum `c_dispatch.cpp:1586-1597`). The consequences:

- **The player (or any runtime `alias` line) redefining a KEYCONF alias** overwrites slot 1. The
  new body replaces the mod's for this session, **still runs in the unsafe context** (the object is
  still an `FUnsafeConsoleAlias`), and **is not saved**. Next startup the mod's body is back.
- **Deleting it** with `alias <name>` (no command) deletes the object outright, whatever its
  class. A following `alias <name> "<cmd>"` then creates an ordinary alias: saved to slot 0, runs
  in the normal context. `clearaliases` removes KEYCONF aliases the same way.
- **A later KEYCONF lump redefining an earlier one's alias** overwrites slot 1; it stays unsafe.
- **A new alias created from inside an unsafe body is an ordinary alias.** The CCMD only builds
  an `FUnsafeConsoleAlias` while `ParsingKeyConf` is set, i.e. while the lump itself is running. A
  KEYCONF alias whose body runs `alias child "..."` creates a normal, saved `child`, which is
  unrestricted when the player later triggers it directly.

### Self-re-aliasing (toggle) aliases misfire

The classic toggle idiom, an alias whose body redefines itself, does not work when defined in
KEYCONF:

```text
alias kc_toggle "echo A; alias kc_toggle \"echo B\""
```

While an alias runs, its active slot (slot 1 here) is emptied temporarily so a self-redefinition
can be detected (`FConsoleAlias::Run`). The nested `alias kc_toggle "echo B"` therefore sees an
empty slot 1, keeps `noSave` off, and writes `echo B` into **slot 0**. When the body finishes,
slot 1 is still empty, so `Run` restores the original body there. Result: slot 1 still holds
`echo A`, which keeps winning, so the alias prints `A` every time and never toggles; and
`echo B` sits in slot 0, **which is saved to the player's config** as an ordinary alias. Observed
live on both engines.

To toggle from a KEYCONF alias, toggle something other than the alias itself (a CVARINFO cvar
read by a normal alias, for example), or have the body realias a *different* name.

## A pre-existing config alias defuses the wrapper

Startup order on both engines: the config's saved aliases are created first (plain
`FConsoleAlias` objects in slot 0, `C_SetAlias` from `FGameConfigFile::DoGameSetup`), then KEYCONF
runs (UZDoom `d_main.cpp:3450` then `:3659`; Zandronum `d_main.cpp:2824` then `:3000`). If the
config already holds an alias with the same name as a KEYCONF alias, KEYCONF's `alias` line
re-aliases that ordinary object: the mod's body goes into its slot 1, and it wins at run time,
**in the normal, unrestricted context**. The player's saved body stays in slot 0, keeps being
saved, and is shadowed. The listing shows both slots.

The two ways such a same-named saved alias gets into the config are the player deleting and
re-creating the name (above), and the toggle misfire (above), which saves one automatically. So
a mod whose KEYCONF alias toggles itself runs restricted on the first session and unrestricted from
the second on. Observed live on UZDoom: an `exec` body in a KEYCONF alias was refused in the first
session; the player then deleted and re-created that alias name at the console, and in the second
session the same KEYCONF `exec` body ran unrestricted.

`alias` lines in `autoexec.cfg` or on the command line (`+alias ...`) are different: `alias` is
not one of the commands run immediately during startup, so they are deferred until after KEYCONF
(UZDoom `c_dispatch.cpp:277-300` and `d_main.cpp:3828`; Zandronum `c_dispatch.cpp:680-702` and
`d_main.cpp:3131-3134`). They re-alias the KEYCONF object's slot 1 like a typed command.

## ACS `ConsoleCommand`

See [`acs/functions/consolecommand.md`](../../acs/functions/consolecommand.md). On Zandronum,
`ConsoleCommand` refuses every alias, KEYCONF or not, and the `alias` CCMD itself, so a script can
neither trigger nor redefine a KEYCONF alias. `ConsoleCommand` also never sets the unsafe context
itself; its restrictions are separate per-command guards. On UZDoom `ConsoleCommand` runs nothing
at all.

## Engine-family divergence

The alias classes, both slots, `Realias`, the `wait` carry-over, the startup order and the
`UNSAFE_CCMD` mechanism are the same code on both engines. The differences:

- **Cvar sets, Zandronum: refused.** `CmdSet` and `toggle` check a static `IsUnsafe` helper
  (`c_cvars.cpp:1836-1844`, used at `:1848` and `:1977`). A non-`CVAR_MOD` cvar is left unchanged
  and the console prints `Cannot set console variable <name> from unsafe command` in red with the
  name in gold. A `set` of a name that doesn't exist yet creates the new, empty cvar before being
  refused.
- **Cvar sets, UZDoom: applied, but not saved.** `CmdSet` and `toggle` call
  `FBaseCVar::MarkUnsafe` (`c_cvars.cpp:1026-1032`, used at `:1584` and `:1691`), which sets
  `CVAR_UNSAFECONTEXT` on a non-`CVAR_MOD` cvar. The new value takes effect for the session with
  **no console message**. Each cvar keeps a separate `SafeValue`, updated by `ForceSet` only for an
  archived cvar set *without* that flag (`c_cvars.cpp:251-264`). `C_ArchiveCVars` writes
  `SafeValue` unless the cvar is still at its default (`c_cvars.cpp:1551-1575`). So the saved value
  is the **last value assigned from a safe context**: normally the one loaded from the config at
  startup, or one the player typed since. Observed live: `screenblocks` typed as 11, then set to 5
  by a KEYCONF alias, was 5 for the rest of the session and saved as `screenblocks=11`.
  - **Edge case: nothing safe assigned yet.** `SafeValue` starts empty and is only filled by a
    safe `ForceSet`, such as loading the cvar from the config. If the config has no line for the
    cvar yet (first run, or a cvar new to this build), an unsafe set clears the at-default state
    and the config gets an **empty value** (`crosshair=`). On the next load an empty string parses
    as zero, not as the default. Observed live: `crosshair` (default 1) was saved empty and read
    back as 0.
  - **Latched cvars:** a `CVAR_LATCH` cvar set while a latch is required is queued rather than
    applied. The queue entry records the unsafe flag and clears it from the cvar
    (`SetGenericRep`, `c_cvars.cpp:266-292`); `UnlatchCVars` puts the flag back before applying
    the value (`c_cvars.cpp:1496-1511`). The latched value takes effect at the next map/game as
    usual and still never reaches `SafeValue`.
  - `resetcvar` (UZDoom only) is not gated, so it both applies and saves the default.
- **`wait 0`.** Zandronum accepts `wait 0` as a one-tic wait (`c_dispatch.cpp:803-817`). On UZDoom
  a zero count is ignored: nothing is queued and the rest of the line runs at once
  (`c_dispatch.cpp:381-393`). See [`console/notes/alias.md`](../../console/notes/alias.md).
- **Menus.** Not KEYCONF-specific, but the same context is entered for a MENUDEF `Command` item on
  both engines (Zandronum `FOptionMenuItemCommand::Activate`, `c_dispatch.cpp:746-751`; UZDoom
  `OptionMenuItemCommand.Activate` in `wadsrc/static/zscript/engine/ui/menu/optionmenuitems.zs`,
  through the `DoCommand` native in `src/common/scripting/interface/vmnatives.cpp`). A
  `SafeCommand` item runs its command in the normal context once the player confirms.
