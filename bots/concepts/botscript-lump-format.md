# The compiled botscript lump format

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** written from the Zandronum source's `src/bots.h` (`DATAHEADERS_e`, `BOTEVENT_e`, buffer size limits), `src/bots.cpp` (`CSkullBot::GetStatePositions`, `CSkullBot::ParseScript`) and `src/botcommands.cpp` (`g_BotCommands[]`, `BOTCMD_RunCommand`); cross-checked by round-tripping all five stock lumps in `wadsrc/static/` byte-for-byte through an independent decoder/encoder. The UZDoom=no claim was checked directly against a UZDoom checkout: its `src/playsim/bots/` holds an unrelated bot implementation with no `DATAHEADERS_e`, no `BOTINFO` reference anywhere under `src/`, and no `ACS_`/`P_StartScript` reference in any of its files. No wiki page covers this format. The "Interpreter state that persists" and "Event dispatch order" sections were added 2026-08-24 from a separate read of `CSkullBot::Tick`, `CSkullBot::ParseScript` and `CSkullBot::PostEvent` at Zandronum `@bdd0f7beb`. The whole page was re-read at that revision on 2026-09-25. The stock-lump-naming paragraph above the "Shape" section was added 2026-09-09, confirmed directly against the checkout's `wadsrc/static/` directory listing and `botinfo.txt`'s `script =` values.

A `BOTINFO` entry's `script =` property names a lump holding **compiled** bot behavior bytecode.
No compiler for this format ships with Zandronum or is known to exist anywhere else, so a lump is
either one of the five stock ones or something a third-party tool produced by targeting the
parser directly. This page describes the format that parser accepts.

The five stock lumps are the engine's own shipped instances of this format, at
`wadsrc/static/{crashbot,dfultbot,fatbot,humanbot,sausgbot}.lump` — the same five names `BOTINFO`'s
stock entries reference via `script = "..."` (see `botinfo-lump.md`'s 8-character `script` cap).
They are not five unrelated or unknown formats; every `BOTINFO` entry in the stock `botinfo.txt`
points at one of them.

Where the parser source and the stock lumps could disagree, the measurement is noted inline — see
`../AGENTS.md`'s "Verifying a claim about the bytecode format" for why the lumps are the tiebreaker.

## Shape

A lump is a **flat stream of little-endian signed 32-bit words**. There is no file header, no
magic number, no version, no directory, and no terminator — the engine simply reads until a read
comes up short. There is no explicit container structure either: states and their sections are
delimited purely by marker words appearing inline in the stream.

The engine parses it twice:

1. `GetStatePositions` walks the whole lump once at bot spawn, recording the byte offset of every
   state and section into fixed-size tables. This pass must size every instruction correctly, or
   everything after a mistake is garbage.
2. `ParseScript` then executes from a recorded offset, running until it is told to stop.

Consequently a lump's structure is only discoverable by walking it from byte 0. There is no way to
seek to a state without parsing everything before it.

## Bot command ordinals are validated at load, so a lump is version-locked to an engine

`GetStatePositions` validates every `DH_COMMAND` operand against the running engine's
`NUM_BOTCMDS` during that first walk, and `I_Error`s on one it does not have:

```text
GetStatePositions: Unknown command 113, in state stateSpawn!
```

Three properties make this the sharpest compatibility edge in the format:

- **It aborts the whole game, not just the bot.** `I_Error` is a fatal exit, so a single unknown
  ordinal anywhere in the lump takes the process down.
- **It happens when the lump is READ**, before a single instruction executes — so there is no
  runtime feature-test a lump can perform to avoid it. A guard like "call this only if the engine
  is new enough" cannot work, because the guard's own presence in the stream is already fatal.
  The ordinal simply must not appear in a lump shipped to that engine.
- **`BOTCMD_e` is append-only across releases**, so the failure is always "newer lump on older
  engine", never a silently-wrong meaning. Verified by comparing the 3.2.1 release commit
  (`28f736fb3`) with the 3.3-alpha checkout: 3.2.1 has 108 commands (ordinals 0 to 107, ending at
  `ACS_NamedExecuteWithResult`) and 3.3-alpha has 114, and the 108 are an exact prefix of the 114.
  The six were all added after 3.2.1, so a 3.2.1 client rejects every one of them:
  `BeginMoveUp`, `StopMoveUp`, `BeginMoveDown`, `StopMoveDown` (ordinals 108 to 111, commit
  `5d8d041ab`), `QuitJoinQueue` (112, `f4c70f3f2`) and `SetGoalTID` (113, `86e33a32d`). The
  example error above is `SetGoalTID` on a 3.2.1 client.

Practical consequences for anyone building a lump:

- Take `NUM_BOTCMDS` from `src/botcommands.h` **at the release commit**, not from a development
  checkout, and not from the parent of whichever commit added the command you care about — with
  several appends in flight those differ.
- Do **not** derive it by running `strings` on a shipped binary. Linker tail-merging folds names
  that are suffixes of longer ones (`SetGoal` into `Thing_SetGoal`, `Roam` into `A_MinotaurRoam`),
  so a hit proves the command is present but a **miss proves nothing**.
- Testing against a development checkout is not evidence about a release client. This is a live
  trap rather than a theoretical one: a lump can be exercised extensively on a `master` build that
  has the command and crash instantly on the stable client that does not.

## Instructions

Each instruction is a data header word — an ordinal into `DATAHEADERS_e` — followed by however
many operand words that header declares. Most headers are bare opcodes with no operands: the
arithmetic and comparison operators, the section markers, and the stack operations.

Headers that carry operands:

| Header | Operands |
| --- | --- |
| `DH_COMMAND` | command ordinal, then a declared argument count |
| `DH_STATENAME` | a length-prefixed string |
| `DH_STATEIDX` | state index |
| `DH_EVENT` | event ordinal |
| `DH_GOTO`, `DH_IFGOTO`, `DH_IFNOTGOTO` | absolute byte offset |
| `DH_CASEGOTO` | match value, then absolute byte offset |
| `DH_PUSHNUMBER`, `DH_PUSHSTRINGINDEX`, `DH_PUSHGLOBALVAR`, `DH_PUSHLOCALVAR` | one index or literal |
| every global/local variable and global array mutator | one index |
| `DH_SCRIPTVARLIST` | a count |
| `DH_STRINGLIST` | a count, then that many length-prefixed strings |

### Jump targets are absolute byte offsets

`DH_GOTO` and friends assign their operand straight into the script position and seek there.
Nothing is relative and nothing is an instruction index, so any tool that edits a lump has to
recompute every jump whenever a byte moves.

This is the single hardest constraint on writing an assembler for this format. The practical
answer is to store jump targets symbolically and re-derive the byte offsets at encode time.

### Strings are length-prefixed and unpadded

A string is a count word followed by exactly that many raw bytes. The count **excludes** any
terminator — measured across all five stock lumps, where `WinStrings` is stored with count 10 and
no trailing nul. The engine writes its own terminator at `buffer[length]` after reading.

Because the byte payload is not padded to a word boundary, **a string can push everything after it
off word alignment**, and a lump's total size need not be a multiple of four — none of the five
stock lumps is. Combined with absolute jump offsets, this means inserting a single character into
a string shifts every later jump target by exactly one byte.

In practice the stock lumps sidestep this by putting the only string list at the very end, leaving
all executable code aligned. That is a convention of whatever produced them, not a requirement of
the format.

### `DH_COMMAND`'s argument count is advisory

`BOTCMD_RunCommand` reads the declared count and then ignores it: the check against the command
table's real arity is commented out in the engine. What *is* enforced is that the stack holds at
least as many entries as the command needs. A wrong count is therefore harmless at runtime, but
indicates the lump was built against a different command table.

## The execution model

A stack machine. `DH_PUSHNUMBER` and friends push, commands consume, and a command with a return
value pushes its result — so an unused result must be explicitly dropped. There are two
independent stacks, one for integers and one for strings. Popping past zero aborts the game.

Both stacks are declared as 8 entries but hold **7** in practice: the push routines write first
and bounds-check afterwards with `>=`, so the write that fills the last slot is in-bounds yet
still trips the error. Nothing warns about this; a script that pushes eight values aborts the
game on the eighth.

`DH_PUSHSTRINGINDEX` pushes onto the *string* stack, indexing the string list; it does not touch
the integer stack.

## States and sections

A state is introduced by `DH_STATENAME` immediately followed by `DH_STATEIDX`. The index is what
`changestate` refers to; the name is used for exactly two things — error messages, and the spawn
lookup below.

A bare `DH_STATEIDX` with no preceding `DH_STATENAME` is legal (the engine has its own case for
it) and leaves the state unnamed. None of the stock lumps use it.

Within a state, three optional sections are delimited by marker words:
`DH_ONENTER`/`DH_ENDONENTER`, `DH_MAINLOOP`/`DH_ENDMAINLOOP`, and `DH_ONEXIT`/`DH_ENDONEXIT`.
`DH_EVENT`/`DH_ENDEVENT` blocks may appear inside a state or, before any state has been
introduced, at global scope.

Rules the engine enforces at runtime, each fatal to the whole process:

- **A state named `stateSpawn` must exist** (matched case-insensitively). It is where a freshly
  added bot starts. Its absence aborts the game at `addbot`, not at load — so a malformed lump can
  load silently and only kill the process when a bot is actually added.
- `DH_ENDONENTER` must be immediately followed by `DH_MAINLOOP`.
- A state being entered must have either an `onenter` or a `mainloop` section.
- `DH_ENDMAINLOOP` seeks back to the recorded `mainloop` offset *and stops parsing for the tic*, so
  a main loop runs at most one iteration per tic even with no `delay` in it. The interpreter's
  separate 8192-operations-per-tic guard catches a `goto` loop that never reaches `endmainloop`.

Changing state from inside a state runs that state's `onexit` section first, if it has one, and
then enters the target.

## Interpreter state that persists

Three pieces of interpreter state outlive the tic that set them. Each one is load-bearing for
writing a lump by hand, and none of them is checked at runtime.

### The script position is a persisted member, so `delay` suspends rather than restarts

`delay` sets a stop-parsing flag for the current tic but does not touch the script position, which
is a member of the interpreter's own state. `Tick` early-returns *without* parsing at all while the
delay counter is non-zero, and when parsing does resume `ParseScript` seeks to that saved position
at the top of every iteration. Execution therefore resumes at the instruction **after** the
`delay`, not at the top of the enclosing `mainloop`.

This is what makes a `delay N` followed by more instructions work as a periodic action inside a
main loop, rather than spinning forever on its own delay. `changestate` clears the delay outright.

An `onenter`/`onexit`/event section and a `mainloop` share the same position, so the same rule
applies inside an event block, which uses a separate delay counter.

### The stack position is reset only at script init, never per tic

Both stack positions are zeroed once, in the bot's spawn-state initialization, and never again.
Nothing re-zeroes them at a tic boundary, at `endmainloop`, or on a state change. So a section
that leaves the stack one entry deeper than it found it does not fail on that pass — it fails
after enough passes to reach the 7-entry ceiling, at which point the overflow aborts the whole
process.

The engine originally checked for this and the checks are commented out in the source: a
`lStackPosition != 0` assertion at both `DH_ENDONENTER` and `DH_ENDMAINLOOP`, plus an expected
stack position local in `ParseScript`, all disabled. There is consequently **no diagnostic at all
for an unbalanced section**, and a lump that runs fine for several seconds can still be
structurally wrong.

Two details that make hand-balancing tractable:

- **A conditional jump pops its operand on both branches.** `DH_IFGOTO` and `DH_IFNOTGOTO` test
  the top entry in place, seek only if the test passes, and then pop unconditionally. The
  not-taken path does not leak a slot, so the two branches of a conditional start at equal depth.
- **Assigning to a variable pops.** The local- and global-variable assignment headers read the top
  entry and then pop it, so a command's return value can be consumed by an assignment instead of
  an explicit drop.

### State variables are indexed per state, not per script

Local variables are stored as `[current state index][variable index]`, so variable 0 in one state
and variable 0 in another are separate storage. They do not carry a value across a `changestate`,
and two states cannot communicate through them.

The limit is 16 per state, and **the index is not bounds-checked** in the engine. An out-of-range
index writes into the adjacent state's variables rather than erroring, which is silent both at
assemble time and at runtime. Script variables (the `scriptvarlist` block) are the per-script,
128-entry storage that does persist across state changes.

## Event dispatch order: global events are matched before state-local ones

`PostEvent` scans the global event table first and returns on the first match, falling through to
the current state's own event table only if nothing matched. So a global event block fires from
every state, and a state-local block for the same event is unreachable while a global one for it
exists.

Dispatch saves the current script position before jumping to the event body, so an event that does
not change state returns to where the main loop left off.

## Limits

From `src/bots.h`. Several are fixed-size buffers the engine `sprintf`s into without bounds
checking, so exceeding them corrupts memory rather than producing a diagnostic.

| Limit | Value |
| --- | --- |
| States | 256 |
| Events per state | 32 |
| Global events | 32 |
| Script variables | 128 |
| State variables | 16 per state |
| Strings in the string list | 128 |
| String length (including terminator) | 256 |
| State name length (including terminator) | 64 |
| Integer stack depth | 8 declared, 7 usable |
| String stack depth | 8 declared, 7 usable |
| Operations per tic | 8192 |

## Reaching ACS from a botscript

The command table includes `ACS_NamedExecuteWithResult`, so a botscript can call a named ACS
script directly and use its return value. This is the bridge that makes a botscript useful as a
thin shim over logic written in ACS rather than as the whole bot AI.

Calling an ACS script that does not exist is non-fatal: `P_StartScript` prints
`P_StartScript: Unknown script "<name>"` and returns 0. That makes it a usable end-to-end probe —
if the message appears, the botscript executed the command, built its string argument, and reached
ACS, which is most of the integration path.

## Engine-family divergence: no counterpart outside Zandronum

Nothing in this page applies to UZDoom/GZDoom-family engines. They have no botscript interpreter,
no `DATAHEADERS_e` bytecode, and no `BOTINFO` parsing — their bot support is an unrelated and much
smaller subsystem, with no path from bot code into ACS at all. A mod that drives bots through this
format is Zandronum-only by construction, and porting it means replacing the mechanism rather than
adapting it.
