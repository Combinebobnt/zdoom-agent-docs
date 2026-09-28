# StringsAreEqual

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** written from the Zandronum source's `src/botcommands.cpp` (`botcmd_StringsAreEqual`). No wiki page covers this command. Two-string-arg rows: `src/botcommands.cpp:217,269,274,311,314`; field order in `BOTCMD_s` at `src/botcommands.h:214-218`.

## Engine-family divergence

`StringsAreEqual` is a bot command, not an ACS/BCS function — it lives in Zandronum's bot-command
dispatcher (`botcommands.cpp`), which UZDoom/GZDoom-family engines don't have at all. There is no
UZDoom counterpart to diverge from; see `../AGENTS.md`.

Compares its two string arguments **case-insensitively** (`stricmp`), not exact byte-for-byte
equality — the name alone doesn't say which, and a caller expecting case-sensitive comparison
(e.g. matching a case-sensitive-looking item class name) will see `"Foo"` and `"foo"` reported
equal.

Its bot command table row takes `0` int args and `2` string args (`lNumArgs`, `lNumStringArgs`).
It is not unique in that. Four other rows share the shape, all chat file/lump commands:
`SayFromFile`, `ChatSectionExistsInFile`, `SayFromLump` and `ChatSectionExistsInLump`. Only 13 of
the table's 114 rows take any string argument at all. Most take none (64 rows are `0, 0`), so a
transposed pair (`2, 0` instead of `0, 2`) would look like an ordinary int-arg row.

## The overflow check runs after the copy, not before it

Both strings are copied into fixed 256-byte local buffers via `sprintf( szString1, "%s", ... )` —
`sprintf` has no bounds checking, so this is a plain unguarded copy, not a truncating one. Only
*after* both copies does the function check `strlen(szString1) >= 256 || strlen(szString2) >= 256`
and, if so, print a bare `"CRAP\n"` to the console/log (`Printf( "CRAP\n" )` — genuinely the literal
message in the shipped source) before still proceeding to compare and return a real result. In
practice this path looks unreachable rather than a live overflow: both string arguments come off
`CSkullBot::m_ScriptData.aszStringStack`, itself declared as `MAX_STRING_LENGTH` (256)-byte
elements (`src/bots.h`), the same size as this function's own local buffers, so a value already on
that stack can't exceed the length this check is guarding against. Worth knowing anyway if
`MAX_STRING_LENGTH` or these buffers ever change size independently: the check as written couldn't
prevent an overflow even if one became reachable, since it runs after the unbounded copy has
already happened.
