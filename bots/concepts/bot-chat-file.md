# The bot chat file / chat lump format

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the Zandronum source's `src/botcommands.h` (`CHATFILESECTION_t` and `CChatFile`, lines 225-276), `src/botcommands.cpp` (`CChatFile` loader, parsers and lookup, lines 353-590; `BOTCMD_DoChatStringSubstitutions`, lines 673-801; the chat commands `botcmd_Say` through `botcmd_ChatSectionExistsInFile`, lines 2047-2270, and `botcmd_SayFromLump` through `botcmd_ChatSectionExistsInChatLump`, lines 2608-2790), `src/bots.cpp` (`chatfile`/`chatlump` parsing, lines 1327-1338; `ulChatFrequency` default, line 1065; accessors, lines 1499-1534; `bot_allowchat`, line 331), `src/sc_man_scanner.re` (the Hexen-mode token rules a chat lump is read with), `src/w_wad.cpp` (`CheckNumForName`, lines 434-477; `CheckNumForFullName`, lines 542-565; full-name hash chain order, lines 706-718), `src/sdl/i_main.cpp` (`progdir`, lines 373-385), `src/v_text.cpp` (`V_ColorizeString`, line 367), `src/chat.cpp` (lines 1155-1172) and `src/sv_main.cpp` (`SERVER_SendChatMessage`, lines 1257-1297). Stock data: `wadsrc/static/botinfo.txt` and the 22 files in `wadsrc/static/bots/chatfiles/`; which chat commands and section names the five stock botscripts use was measured by disassembling `wadsrc/static/*bot.lump` with a decoder that walks each lump cleanly to its last byte. Nothing here was tested in a running game.

## Engine-family divergence

This format exists only to feed Zandronum's bot commands. UZDoom/GZDoom-family engines have no
`BOTINFO`, no botscript interpreter and no chat-file reader, so there is nothing to port; see
[botinfo-lump.md](botinfo-lump.md) and [botscript-lump-format.md](botscript-lump-format.md) for
the same conclusion on the other two halves of the bot surface.

## What it is and who reads it

A chat file is a plain text list of named sections, each holding candidate chat lines. A bot
says one line picked at random from a named section, but only when its botscript asks: eight
bot commands read this format, and nothing else in the engine does.

| Command | Source of the text | Section argument |
|---|---|---|
| `SayFromChatFile(section)` | the bot's `BOTINFO` `chatfile` | string |
| `ChatSectionExists(section)` | the bot's `BOTINFO` `chatfile` | string |
| `SayFromFile(file, section)` | a file named by the script | string |
| `ChatSectionExistsInFile(file, section)` | a file named by the script | string |
| `SayFromChatLump(section)` | the bot's `BOTINFO` `chatlump` | string |
| `ChatSectionExistsInChatLump(section)` | the bot's `BOTINFO` `chatlump` | string |
| `SayFromLump(lump, section)` | a lump named by the script | string |
| `ChatSectionExistsInLump(lump, section)` | a lump named by the script | string |

For the two-argument forms the file or lump name is pushed first and the section second (the
handler pops the section off the top of the string stack, then the name).

### `chatfile` is a disk path next to the executable, not an archive path

`LoadChatFile` concatenates the value onto `progdir`, the directory the Zandronum executable
lives in, and opens the result with a plain C `fopen` (`src/botcommands.cpp:372-387`). The
virtual filesystem is never consulted, so a `chatfile` can **not** be shipped inside a pk3 or
wad: the file has to be copied beside the executable on every machine that runs the bot. On a
server that means the server's own executable directory. An absolute path does not work either,
since it is always prefixed.

### `chatlump` is a lump, by short name or by full path

`LoadChatLump` first tries the value as an 8-character lump name (`CheckNumForName`), then as a
full archive path (`CheckNumForFullName`) (`src/botcommands.cpp:444-461`). `CheckNumForName`
refuses any name longer than 8 characters that contains `/` or `.`, so a path such as
`bots/chatfiles/mybot.txt` goes straight to the full-path lookup (`src/w_wad.cpp:448-453`).
Both lookups prefer the most recently loaded archive, so a mod can replace a stock chat lump by
shipping a file at the same path.

The stock roster uses full paths (`chatlump = "bots/chatfiles/soldier.txt"`). `BOTINFO`'s
31-character cap on `chatlump` is fatal when exceeded, and `bots/chatfiles/` alone spends 15 of
those characters.

**This is the only route a mod can distribute.** Every stock bot uses `chatlump`, and none of the
five stock botscripts calls a file-reading command at all (see "What makes a bot talk" below).

## Grammar

The same `[Section]` and `"entry"` shape is read by two separate parsers, one per route, and
they disagree on everything except the basics. A file written the way the stock files are
written (every entry double-quoted on its own line, no comments) parses identically under both.

```text
// A comment line. Content before the first header ends the parse, comments excepted.
[IntroStrings]
"Let's do this."
"Good luck, $player_random_notself."

[FragStrings]
"\cgGotcha!"
"That one was for you, $player_killed."
```

What both parsers share:

- A line or token starting with `[` opens a section. A trailing `]` is removed if present; the
  name is everything in between, and is matched **case-insensitively** at lookup.
- A line or token starting with `#` or `//` is a comment.
- **Any other content before the first section header ends the parse right there**, silently.
  The file or lump then loads with no sections, so every lookup fails as "section not found".
- Surrounding whitespace is trimmed, and a trimmed line or token of **one character** is
  dropped. In a file the quotes are still part of the line at that point, so `"k"` survives; in
  a lump the scanner has already removed them, so a one-character chat line can never be said.

Where they differ:

| | `chatfile` (line parser) | `chatlump` (token parser) |
|---|---|---|
| Unit | one line (`fgets`, 1024-byte buffer) | one `FScanner` token, Hexen mode |
| What becomes an entry | only a line starting with `"`; its trailing `"` is removed. Any other line is silently ignored | **every** token. Unquoted text is split into separate entries at whitespace and at `{` `}` `\|` `=` |
| Quoted text | the quotes are part of the line; whitespace inside them is kept | the scanner strips the quotes; whitespace just inside them is then trimmed |
| Comments | only a whole line beginning with `#` or `//` | the scanner's own `//`, `;` and `/* */` comments anywhere outside quotes, plus any token beginning with `#` or `//` |
| Escapes | none; a `\"` is kept literally | `\"` becomes `"`; every other backslash is kept |
| Over-long text | a line past 1023 bytes is split by `fgets`, and the remainder is usually ignored | no scanner limit, but the copy into the 1024-byte entry slot is unbounded (see Limits) |

Two lump-only traps follow from the token parser:

- **A `#` comment leaks its words.** `# greetings for the lobby` drops only the `#` token;
  `greetings`, `for`, `the` and `lobby` each become an entry of the current section (a
  one-letter word would be dropped as a one-character entry). Use `//` in a lump.
- **Unquoted lines become one entry per word.** `Nice shot!` unquoted is two entries, `Nice`
  and `shot!`. Quote every entry.

A `;` inside quotes is safe in both routes (the stock files use `;)` freely).

**Inferred from source, not tested:** the trim loops compare bytes against the space character
as a plain `char`. Where `char` is signed (the usual default for x86 compilers) any byte from
0x80 up also counts as whitespace, so in a lump, where the quotes are already gone before the
trim runs, leading and trailing non-ASCII letters of an entry would be cut off. Keep chat text
ASCII, or at least not starting or ending with a non-ASCII character. The stock files are pure
ASCII.

## Limits

`CChatFile` is a fixed array of 64 sections, each a 64-byte name, 64 entry slots of 1024 bytes
and a count (`src/botcommands.h:225-237`, `275`).

- **64 sections.** The 65th header gets no slot, and the next entry after it ends the whole
  parse, so everything from that header onwards is ignored. No warning.
- **64 entries per section.** Extra entries are silently dropped.
- **Section names under 64 characters.** The name is copied with an unbounded `sprintf`; a
  longer name overruns into that section's own entry storage, and once an entry is stored there
  the name no longer matches anything.
- **Entries under 1024 characters.** Same unbounded copy into the entry slot. The line parser's
  1024-byte read buffer keeps a `chatfile` just inside that; a lump token has no such guard.
- **Duplicate headers do not merge.** A second `[FragStrings]` opens a second section, and
  lookup always returns the first one, so the second one's entries are unreachable.
- **An empty header `[]` is not a section.** Its slot still reads as free, so the next header
  reuses it and inherits the entries collected under `[]`.

## How a line is picked

`ChooseRandomEntry` (`src/botcommands.cpp:567-581`) finds the first section whose name matches
case-insensitively, then takes a random byte from the `RandomBotChatSeed` generator modulo the
entry count. There is no memory of the previous pick, so the same line can repeat back to back,
and with a count that doesn't divide 256 the low-numbered entries are very slightly favoured.

- **A missing section and an empty section both come back as the literal string `NULL`,** and
  every `SayFrom*` handler treats a result equal to `NULL` (case-insensitive) as "not found". So
  a chat line that reads exactly `NULL` can never be said: it prints the not-found message
  instead.
- **`ChatSectionExists*` only checks the name.** A header with no entries under it returns
  `true`, yet the matching `SayFrom*` call on it prints "Couldn't find section".
- **Every call re-reads and re-parses the whole file or lump.** Each command allocates a fresh
  `CChatFile` (roughly 4 MB: 64 x 64 x 1024 bytes of entry slots), parses into it, and frees it.
  The stock scripts check a section and then say from it, so every stock bot line costs two full
  parses. Nothing is cached across calls, which also means an edited `chatfile` on disk takes
  effect on the very next call.

## Placeholders

Before the line is sent, `\c` colour escapes are converted (`V_ColorizeString`, which does
nothing else: `\n` and friends stay literal), and then `$` placeholders are expanded by
`BOTCMD_DoChatStringSubstitutions` (`src/botcommands.cpp:673-801`). Both steps also apply to the
plain `Say` command, not only to lines from a chat file or lump.

| Placeholder | Becomes | When the value is unset |
|---|---|---|
| `$player_damagedby` | the last player who damaged this bot | not expanded (see below) |
| `$player_enemy` | the bot's current player enemy | not expanded |
| `$player_killedby` | the player who last killed this bot | not expanded |
| `$player_killed` | the player this bot last killed | not expanded |
| `$player_inlead` | the in-game, non-spectating player with the most frags | always expands |
| `$player_lastplace` | the in-game, non-spectating player with the fewest frags | always expands |
| `$player_random_notself` | a random in-game player other than the bot | the bot itself when it is alone |
| `$player_random` | a random in-game player | always expands; may be the bot itself or a spectator |
| `$player_lastchat` | the name of whoever last chatted | not expanded |
| `$level_name` | the map's title (`level.LevelName`) | always expands |
| `$map_name` | the map lump name (`level.mapname`) | always expands |

How matching works, and what it means for chat authors:

- **Names are matched as case-insensitive prefixes, tested in the table's order.** Nothing
  checks what follows the name, so `$map_name_here` expands to the map name followed by `_here`.
- **An unset value falls through to the next test instead of stopping.** The dangerous case is
  `$player_killedby` when the bot has never been killed but has killed someone: the
  `player_killedby` test fails, the next test (`player_killed`) matches the first 13 characters,
  and the output is the victim's name followed by a literal `by`.
- The longer names are tested before their prefixes (`player_killedby` before `player_killed`,
  `player_random_notself` before `player_random`), which is the only reason the longer ones work.
- **No match emits a literal `$`** and carries on copying, so text such as `$50` or an unset
  `$player_enemy` comes out unchanged.
- `$player_inlead` and `$player_lastplace` start their search from player slot 0 whether or not
  that slot is in the game, so with slot 0 empty or spectating they can name that slot anyway
  when its stale frag count wins. They rank by frag count in every game mode.

## What makes a bot talk

**The engine never initiates bot chat.** No event, timer or kill produces a line on its own.
Only a botscript command does, and the script decides which section to use. `chatfrequency` in
`BOTINFO` (default 50) is read by nothing but the `GetChatFrequency` command, so it means only
what the script makes of it. The `bot_allowchat` cvar (default `true`) is the one engine-side
gate: when it is off, every `Say*` command still runs (and still prints its not-found messages)
but sends nothing.

The five stock botscripts use only the `chatlump` pair (`ChatSectionExistsInChatLump`, then
`SayFromChatLump`). Measured in `humanbot`, which uses all ten stock section names (the other
stock scripts use the same names; `dfultbot` omits `EnragedStrings` and `DemoralizedStrings`):

| Section | Said when (stock `humanbot`) | Gated on `chatfrequency` |
|---|---|---|
| `IntroStrings` | entering `stateSpawn`, after a short random delay | no, always said |
| `FragStrings` | entering `stateKilledEnemy`, reached on `BOTEVENT_ENEMY_KILLED` | `Rand(0, N) == 0`, N = `(100 - f) / 6`, at least 2 |
| `KilledStrings`, `EnragedStrings`, `DemoralizedStrings` | entering `stateKilled`, reached on the `BOTEVENT_KILLED_BY*` events; one of the three | same, N = `(100 - f) / 5`, at least 2 |
| `RoamingStrings`, `RareRoamingStrings`, `LosingRoamingStrings` | each pass of the main loops of `stateStandardRoam` and `statePathToGoal` | same, N = `(100 - f) * 7`, at least 35 |
| `WinStrings`, `LoseStrings` | entering `stateIntermission` or `stateDuelWinSequence`, and the global `BOTEVENT_LMS_WINSEQUENCE` handler; win or lose by the sign of `GetSpread` | no, always said |

Every gated line is also skipped when `chatfrequency` is 0. These formulas are conventions of the
stock scripts, not engine behavior, and a stock bot with `chatfrequency` 0 still greets and
still comments on the result.

A custom botscript is free to use any section name at any point, including in a
`BOTEVENT_PLAYER_SAY` handler to answer other players.

A bot's line goes through the ordinary chat path, so `GAMEEVENT_CHAT` event scripts see it and
can suppress it. In an offline game that path (`CHAT_PrintChatString`) also records the line for
`GetLastChatString`/`GetLastChatPlayer` and posts `BOTEVENT_PLAYER_SAY` to every other bot, so
bots can react to each other; the server path (`SERVER_SendChatMessage`) does neither.

## The stock chat lumps

The Zandronum source ships 22 chat files in `wadsrc/static/bots/chatfiles/`, all in the quoted
one-entry-per-line style that both parsers read the same way. Sections seen across them:

- The ten names the stock scripts use (above).
- `PissedStrings`, `FrustratedStrings` and `IntermissionStrings`, which no stock script ever
  asks for.
- Two misspelled headers whose entries are therefore dead: `[FragStrngs]` in `cygnus.txt` and
  `[LosingRoamingString]` in `massmouth.txt`.

Placeholders in actual use are `$player_killed`, `$player_killedby`, `$player_inlead`,
`$player_lastplace` and `$player_random_notself`, plus `\c` colour codes.

**Four `chatlump` targets in the stock `botinfo.txt` have no file in the source tree:**
`robot.txt` (10 bots), `demon.txt` (7 bots), `chexman.txt` and `doomcrate.txt` (one bot each).
Those 19 bots are silent: the lump lookup fails, `ChatSectionExistsInChatLump` returns `false`,
and the stock scripts skip the `SayFromChatLump` call. The files `cyborg.txt` and `rigel.txt`
exist but no stock bot points at them.

## Errors

Nothing about a chat file or lump is fatal, in sharp contrast to `BOTINFO`. The failures are:

- The `ChatSectionExists*` commands return `false` for a missing file or lump and print nothing.
- The `SayFrom*` commands print one console line and say nothing: `Couldn't open file <name>!`
  or `Couldn't open lump <name>!`, or `Couldn't find section <section> in file <name>!` / `in
  lump <name>!`. The prefix names the handler, except that `SayFromChatFile`'s missing-file
  message is labelled `botcmd_SayFromFile`.
- Malformed content is never reported. Everything in "Grammar" and "Limits" above fails silently.

The fatal failures around this format come from elsewhere: a `chatlump` value over 31 characters
in `BOTINFO`, or calling a two-argument command with fewer than two strings on the string stack
(`BOTCMD_RunCommand`).

## Version note

The chat reader, the chat commands, the substitution function, the scanner, the stock chat files
and the stock `botinfo.txt` are unchanged between the 3.2.1 version-bump commit (`28f736fb3`) and
the `3.3-alpha` checkout read here. `src/chat.cpp` and `src/v_text.cpp` are unchanged too, the
`src/bots.cpp` and `src/w_wad.cpp` changes don't touch the code cited, and the 3.2.1
`SERVER_SendChatMessage` already runs `GAMEEVENT_CHAT` without notifying bots. Everything above
therefore also holds for a 3.2.1 client.
