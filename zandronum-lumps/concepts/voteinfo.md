# The `VOTEINFO` lump

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki [VOTEINFO](https://wiki.zandronum.com/w/index.php?title=VOTEINFO&oldid=2235)
(retrieved 2026-09-09); verified and expanded against the Zandronum source's `src/callvote.cpp`
(`CALLVOTE_ReadVoteInfo`, `CALLVOTE_GetCustomVotes`, `CALLVOTE_GetCustomVoteTypeDefinition`,
`CALLVOTE_ConvertCustomVoteParameter`, and the `VOTETYPE_s` struct in `src/callvote.h`).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

`VOTEINFO` declares custom in-game vote types on top of the engine's built-in set (`kick`, `map`,
`fraglimit`, and the rest of `callvote.h`'s `VOTECMD_*` enum). Unlike the Skulltag-era `key =
value` lumps in this section, it is a modern `FScanner` C-mode parser: the grammar is a sequence
of named, brace-delimited blocks, `votetype Name { ... }`, each holding `;`-terminated key
statements rather than bare `key = value` pairs. Custom vote types are invoked via the `callvote`
console command.

## Grammar

```text
votetype MyCustomVote
{
    Action = CallACS("MyVoteScript");
    PreflightAction = CallACS("MyPreflightScript");
    ForbidCVar = sv_disablemyvote;
    Arg = int;
    DisplayName = "My Custom Vote";
    Menu = OptionsMenuName, "My Custom Vote";
}
```

`CALLVOTE_ReadVoteInfo` (the Zandronum source's `src/callvote.cpp:124`) loops every loaded
archive's `VOTEINFO` lump (`Wads.FindLump`), and for each one repeatedly expects the `votetype`
keyword, an identifier naming the vote type, then a `{`-delimited body. A new vote type's name is
checked case-insensitively against every vote type the engine already knows about before it's
accepted - not just other custom vote types, but every built-in command name (`kick`, `map`,
`fraglimit`, ...) and every cvar that passes the flag-vote target check (a flag cvar of `dmflags`,
`dmflags2`, `compatflags`, `zadmflags` or `zacompatflags`), since the duplicate check reuses the
same lookup the engine uses to resolve a vote command at call time. That check is structural, so
it applies whether or not flag votes are currently allowed on the server. A collision with any of those
is a fatal parse error, so distinct vote-type names are cumulative across every loaded `VOTEINFO`
lump, but a same-named redefinition is rejected outright rather than merged (unlike `ANCRINFO`'s
merge-into-`Default` special case). Inside a block, keys are matched case-insensitively and each
statement ends in `;`; an unrecognized key is also a fatal error ("Unknown key ... in ...").

Because this is a modern `FScanner` C-mode parser using `sc.ScriptError`, any malformed statement
anywhere in the lump throws through `I_Error` (the Zandronum source's `src/sc_man.cpp`'s
`FScanner::ScriptError`) and aborts engine startup outright with a fatal "Script error" message,
rather than skipping just the bad entry. `CALLVOTE_ReadVoteInfo` runs unconditionally during
startup (`src/d_main.cpp:2913`), before any map loads, so a broken `VOTEINFO` lump in any loaded
archive prevents the engine from starting at all.

## The six keys

### `Action` and `PreflightAction`

Both are parsed by the same code path and both require their right-hand side to look exactly like
`CallACS("scriptname")`: after the `=`, the parser demands an identifier that must literally read
`CallACS` (case-insensitive), then a literal `(`, a string constant, `)`, and `;`. This is not a
general expression evaluator - it is a fixed three-token shape the parser pattern-matches. Any
other shape (a bare string, a different function name, a numeric literal) is a fatal error
("Action must be CallACS" / "PreflightAction must be CallACS"), never silently ignored. One
asymmetry worth noting: `Action` is recognized via a genuine reserved keyword token (`TK_Action`,
the `action` keyword shared with other `FScanner` grammars in this engine family), while
`PreflightAction` is matched as a plain identifier compared case-insensitively - the two keys read
as parallel in the lump text but are tokenized differently under the hood.

- `Action = CallACS("script")` sets the vote type's `scriptName` and is mandatory: if a `votetype`
  block ends without ever setting it, `CALLVOTE_ReadVoteInfo` raises a fatal "does not have
  ScriptName" error. When the vote passes, the engine runs this script by name (`-FName(scriptName)`,
  i.e. a named rather than numbered ACS script) via `P_StartScript` with `ACS_ALWAYS`, passing the
  vote's single converted argument (see `Arg` below) if it has one.
- `PreflightAction = CallACS("script")` sets `preflightScript` and is optional. When present, the
  server runs this script by name as part of validating the vote before it's allowed to begin
  (`ACS_ALWAYS | ACS_WANTRESULT`), and the vote is only allowed to proceed if the script's result
  is truthy.

Neither key's string argument is checked against any real ACS script at lump-load time; it is
stored verbatim, so a typo in the script name only surfaces later, when the vote is actually called
or resolved.

### `ForbidCVar`

`ForbidCVar = cvarname;` names an existing cvar, given as a bare identifier rather than a string,
that gates whether the vote can be called at all. The cvar must already exist when `VOTEINFO` is
parsed - if `FindCVar` can't find it, loading is fatal, with an error message that even suggests
the fix (declare `server bool <name> = false;` in a `CVARINFO` lump). At vote-call time, an empty
`ForbidCVar` always allows the vote; a non-empty one reads the named cvar as a bool and blocks the
vote - printing "`<display name>` votes are disabled on this server." - whenever that cvar is
currently `true`. The check doesn't verify the cvar is actually boolean-typed; it reads whatever
cvar was named through its generic `CVAR_Bool` representation regardless of the cvar's real type.

### `Arg`

`Arg = <type>;` declares the vote's single parameter type, chosen from a small fixed set: the
reserved keywords `int`, `float`, and `map`, or the bare identifiers `Str` and `Player` (matched
case-insensitively, not as string constants). Anything else is a fatal "Unknown vote parameter
type" error. Omitting `Arg` entirely leaves the parameter type at its default, "none," meaning the
vote takes no parameter at all. This type drives two things downstream: whether the vote command
requires a parameter to be typed at all, and how the raw string a voter typed gets converted before
being handed to the vote's ACS script - `map` cross-checks the input against the level list and can
rewrite a numeric map-list index into a map name, `player` resolves a name to a player index,
`float` gets reformatted, and `int`/`str` pass through with minimal conversion.

### `DisplayName`

`DisplayName = "text";` sets a human-readable name shown instead of the vote type's own internal
name - for example in the "votes are disabled on this server" message above, and as the fallback
label for `Menu`'s submenu entry (below). It's optional, but if present must be a non-empty string
constant (fatal otherwise); if omitted, it defaults to the vote type's own internal name once the
block finishes parsing.

### `Menu`

`Menu = MenuClassName[, "Submenu label"];` is the only key whose right-hand side can carry two
tokens. The first, a bare identifier, names a MENUDEF `OptionMenu` definition; every vote type that
sets this gets a submenu entry added to the engine's built-in call-vote option menu, pointing at
that named menu. The identifier is not checked against any real MENUDEF block at `VOTEINFO`-load
time - an entry pointing at a menu that doesn't exist would only fail later, when a player actually
tries to open it. An optional trailing `, "label"` sets that submenu entry's own display text, and
must be non-empty if given (fatal otherwise); left off, the label falls back to `DisplayName` (or,
if that was also omitted, the vote type's internal name). Omitting `Menu` entirely leaves the vote
type reachable only by typing its vote command directly, with no menu entry generated for it at
all.

## Wiki/engine divergence

The Zandronum Wiki's documentation has two errors:

1. **Menu key name**: The wiki's template shows `MenuName = <menuName>;`, but the actual key in the engine parser is `Menu` (not `MenuName`). Users copying the wiki example directly will get the fatal "Unknown key 'MenuName'" error. The correct syntax is `Menu = OptionMenuName[, "Label"];`.

2. **Argument type description**: The wiki's `Arg` section description incorrectly ends with "The value must correspond to a valid existing cvar" — this sentence belongs in the `ForbidCVar` section, not in the argument type documentation. The cvar requirement applies only to `ForbidCVar`, not to vote arguments.

## Engine-family divergence

UZDoom/GZDoom-family engines have no vote-calling subsystem of this shape at all and do not parse
`VOTEINFO`.
