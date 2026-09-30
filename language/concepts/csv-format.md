# The CSV LANGUAGE format

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28)
**Provenance:** written from the UZDoom source's `src/common/engine/stringtable.cpp` (`LoadStrings`, `parseCSV`, `readMacros`, `ParseLanguageCSV`, `LoadLanguage`, `DeleteString`, `DeleteForLabel`, `InsertString`, `ProcessEscapes`, `GetID`, `ExtractComponents`, `RemapLegacyLanguages`, `CheckString`), `src/common/engine/stringtable.h` (table IDs), `src/common/engine/sc_man.cpp` and `sc_man_scanner.re` (BOM strip, `isText`, C-mode tokens), `src/common/utility/tarray.h`, `src/d_main.cpp` (`StrTable_ValidFilter`, `SetDefaultGender`), `src/gamedata/gi.cpp` (`GameNames`), `src/d_netinf.h` (gender values), `src/playsim/p_interaction.cpp`, `CMakeLists.txt` (`generate_language_files`), `wadsrc/CMakeLists.txt`, `wadsrc_extra/CMakeLists.txt`, `wadsrc/static/lmacros.csv` and `libraries/Translation/scripts/compile.py` and `config.py`; and, for the Zandronum section, the Zandronum source's `src/stringtable.cpp` (`LoadStrings`, `LoadLanguage`), `src/sc_man.cpp` (`isText`, `ScriptError`), `src/zstring.h`, `src/sdl/i_system.cpp` (`I_Error`) and `src/sdl/i_main.cpp`. No wiki page was used.

UZDoom can read a LANGUAGE lump as a spreadsheet instead of the classic `[code] LABEL = "text";`
syntax. It is how the engine ships its own translations, and the only LANGUAGE form in which a
string can be deleted rather than overwritten. The classic grammar, the lookup order between
language tables and the cross-lump override rules live in the
[LANGUAGE lump](language-lump.md) page; this page covers only what is specific to CSV. A bare
`:line` citation below is into the UZDoom source's `src/common/engine/stringtable.cpp`.

## Detection

A lump named `LANGUAGE` is read as CSV when **its first bytes are `default,` or `identifier,`,
compared case-insensitively, and it is at least 11 bytes long**
(`src/common/engine/stringtable.cpp:500-501`). Otherwise it goes to the classic parser.

- The test is on byte 0. A UTF-8 byte-order mark, a leading blank line or space, or a quoted
  first cell (`"identifier",...`) all fail it, as does a header that starts with any other
  column (`filter,identifier,...`).
- The file name's extension plays no part. In a pk3, `language.csv`, `language.txt` and
  `language.enu` are all lumps named `LANGUAGE`, and each is sniffed on its own content.
- A CSV file that fails detection reaches the classic parser, whose first token is then not
  `[`. The lump is dropped with one console line and startup continues (see "Errors").

## Layout

Row 1 is the header. Every later row is one label.

```text
default,identifier,filter,fr,pt_BR pt
"Hello, world",MY_GREETING,,"Bonjour, le monde",
Pick up the wand,MY_ITEM,heretic,Ramassez la baguette,Pegue a varinha
Pick up the pistol,MY_ITEM,doom chex,,
"Line one\nLine two, ""quoted""",MY_MULTI,,,
```

| Header cell | Meaning |
|---|---|
| `identifier` | The label column. Its cells are trimmed of surrounding whitespace (`:566`). Labels are case-insensitive, as in the classic format. |
| `filter` | Optional. Space-separated game names; see "The `filter` column". |
| `remarks` | Ignored (`:522-525`). Only since UZDoom 5.0.0 (commit `9bac149a7c`); earlier engines took it as a language column, which is harmless but useless. |
| Anything else | A language column. The cell is split on spaces and each token is a language code, so one column can feed several tables. An empty header cell makes an ignored column. |

The three keyword cells are matched against the **whole, untrimmed cell**, case-insensitively
(`:514-525`). ` identifier` with a leading space is a language column, not the label column.
Column order is free: the stock file puts `default` first, which is what lets it pass detection.

**There must be an `identifier` column**, even though a file can pass detection by starting with
`default,`. Without one the parser indexes the row with column -1 (see "Errors").

### Language codes in a header cell

Each token goes through the same `GetID` mapping as the `language` cvar (`:261-353`):

- **`default`** (exactly that word, any case) is the default table, `en-US`, and turns on the
  delete-earlier rule for every row of the file (`:531-535`; see "Empty cells and the `default`
  column").
- **BCP 47 tags work, with `-` or `_`**: `en-GB`, `en_GB`, `pt_BR`, `zh-Hant-TW`. The tag is
  lowercased, every non-alphanumeric character becomes a separator, and it is split into
  language, optional 4-letter script and optional 2-letter region (`:204-253`). Apart from the
  `language` cvar, this is the only place the hyphenated spelling works: a classic header splits `[en-GB]` into three tokens
  (see [Language codes](language-lump.md#language-codes)). The underscore spelling is one token
  in a classic header too, so `[pt_BR]` also reaches the `pt-BR` table there
  (`src/common/engine/sc_man_scanner.re:69` leaves `_` out of the split characters).
- **Legacy codes are remapped first**, exactly as in a classic header (`enu` to `en-US`, `eng`
  to `en-GB`, `ptg` to `pt`, and so on, `:78-149`). Any other code is a bare language.
- **`enu` or `en-US` lands in the default table but does not turn on the delete-earlier rule.**
  Only the literal word `default` does. A classic `[enu]` header does trigger it, because the
  classic parser tests the resulting table rather than the spelling (`:632-637`).
- **`*` does not reach the global table.** The classic parser special-cases `[*]`; the CSV
  parser does not, so `*` normalizes to a `*-*-*` table that no lookup ever searches
  (`stringtable.h:69` defines the global table as a different ID). CSV has no equivalent of
  `[*]`; write those strings in a classic lump.

## Quoting and escapes

UZDoom uses its own small reader, written for spreadsheet exports (`parseCSV`, `:392-463`):

- A `"` **opens a quoted cell only when it is the cell's first character.** Inside a quoted
  cell, commas and line feeds are literal, and `""` is one literal quote. The next lone `"`
  closes the quote; any text after it still belongs to the cell.
- A `"` anywhere else in an unquoted cell is **silently dropped**. So is a `"` preceded by a
  space: ` "a,b"` becomes two cells, ` a` (leading space kept) and `b`.
- Every carriage return is dropped, even inside quotes, so CRLF files work. A line feed outside
  quotes ends the row.
- The last line needs no trailing newline.
- **After unquoting, every cell goes through the same backslash-escape pass as a classic
  string** (`:427`, `:443`, `:458`), header and identifier cells included. So `\n`, `\c`,
  `\xHH` and the rest behave as described in
  [Escapes](language-lump.md#escapes). A literal backslash is `\\`.
- **`\"` does not give a quote in CSV.** The reader sees the `"` before the escape pass runs: it
  closes a quoted cell or is dropped from an unquoted one, so `"a\"b"` ends up as `ab`. Use `""`
  inside a quoted cell.
- Nothing else is trimmed. A cell holding only spaces is stored as spaces, not treated as empty.

There is no comment syntax, no `$ifgame` and no string concatenation. A row is a row.

## The `filter` column

A non-empty `filter` cell restricts its row to the listed games (`:544-564`):

- The cell is split on spaces. The row is kept if **any** name matches, through the same game
  test the classic `$ifgame` uses (`StrTable_ValidFilter`, `src/d_main.cpp:2975-2979`): a
  case-insensitive compare against `Doom`, `Heretic`, `Hexen`, `Strife` or `Chex`
  (`src/gamedata/gi.cpp:73-76`), plus `strifeteaser` on the Strife shareware IWAD. Chex Quest
  does not match `doom`.
- During the early load for the IWAD picker, before any game is chosen, every name matches.
- An unknown name never matches and is not an error. A cell such as `doom harmony` works because
  `doom` matches; `harmony` is inert.
- **A filtered-out row is skipped entirely**: it neither inserts nor deletes anything, in any
  column (`:562`).
- An empty filter cell, or no filter column, keeps the row for every game.

Several rows may share one identifier. Within a file, rows are applied top to bottom and a later
row replaces an earlier one table by table. The working pattern is an unfiltered row first, then
game-specific rows below it, as `MY_ITEM` does in the example above.

## Empty cells and the `default` column

**An empty cell deletes the label from that column's language tables** (`DeleteString`,
`:579-581`, `:714-717`). There is no file check: it removes the string whichever earlier lump,
classic or CSV, put it there. Lookup then falls through to the next table in the chain (usually
the default one; see [Lookup order](language-lump.md#lookup-order)). This is what
"untranslated" means in CSV: in the example above, `MY_GREETING` is deleted from the `pt-BR` and
`pt` tables, so those players
get the default text rather than a stale translation from an earlier file. It differs from
a classic `LABEL = "";`, which stores an empty string that wins the lookup.

When the header has a `default` column, **every row that survives its filter first runs the
delete-earlier rule** (`DeleteForLabel`, `:568-571`, `:726-740`): the label is removed from every
table where it came from an **earlier resource file**. Then the row's own cells are applied, so
non-empty cells insert and empty cells delete.

- "Earlier" compares resource files (the IWAD, the engine pk3, each `-file` archive), not lumps
  (`LoadStrings` passes the container index, `:377`). Two LANGUAGE lumps inside one pk3 never
  delete each other's strings this way; the later one only overwrites table by table.
- A row whose language cells are all empty, under a `default` column, removes the label from
  every earlier file's tables and adds nothing. It is the only way to unset a stock string
  entirely, after which `$LABEL` lookups miss and show the label name.

## Load order and precedence against classic lumps

CSV and classic lumps share one string store and are processed in a single pass in lump order
(`LoadStrings`, `:373-381`). Each lump is sniffed independently, so a mod can mix a CSV
`language.csv` with a classic `language.txt`, and the rules in
[Override order across lumps](language-lump.md#override-order-across-lumps) apply unchanged: a
later lump's string replaces an earlier one in the same table. The CSV-specific differences are
the ones above:

- An empty cell **deletes** instead of storing an empty string.
- Only the word `default` triggers delete-earlier; an `enu` column does not, unlike `[enu]`.
- There is no `[*]` global table.
- Hyphenated region and script tags (`en-GB`) reach their own tables. In a classic header only
  the underscore spelling (`en_GB`) does.

All `LMACROS` lumps are read before any LANGUAGE lump, and macros are expanded as each string is
stored, so macro expansion does not depend on where LANGUAGE lumps sit relative to `LMACROS`
(`:367-371`).

## `LMACROS` and `@[name]`

`LMACROS` is a separate CSV lump of gendered text fragments. Any stored LANGUAGE string (CSV or
classic) may contain `@[name]`; the string is then kept in four variants, one per gender.

```text
macro,lang,m,f,n,o
my_e_fr,fr,,e,,
```

```text
default,identifier,fr
%o fell.,MY_OB_FALL,%o est tombé@[my_e_fr].
```

- **Columns** (`readMacros`, `:471-490`): row 1 is skipped unread, so its text is arbitrary and
  only column position matters. Column 1 is the macro
  name, column 3 onward the four forms in gender order: male, female, neutral, object
  (`GENDER_MALE` to `GENDER_OBJECT`, values 0-3, `src/d_netinf.h:30-33`). **Column 2 (language)
  is read but ignored**: macros are global, so a macro meant for one language needs a name that
  says so, as the stock file does with a language suffix.
- **Only the last `LMACROS` lump counts.** Each `LMACROS` lump clears every macro read before it
  (`:475`). A mod that ships its own `LMACROS` therefore removes the engine's stock macros from
  `wadsrc/static/lmacros.csv`. The stock non-English translations use `@[...]` heavily, so the
  symptom is missing word endings in translated obituaries and messages. Copy every stock row you
  still need into your own `LMACROS`.
- **Expansion happens once, at load** (`InsertString`, `:748-772`). Every `@[name]` is replaced in
  all four variants. The name match is case-insensitive. An undefined macro expands to nothing.
  An `@[` with no closing `]` prints `Bad macro in ...` to the console and leaves the rest of that
  string unexpanded.
- **Which variant is shown.** A plain `$LABEL` lookup uses the console player's `gender`, copied
  into the string table every frame of the main loop (`src/d_main.cpp:1453`). Obituaries instead
  ask for the **dying player's** gender (`src/playsim/p_interaction.cpp:275-294`); see
  [string retrieval](string-retrieval.md).
- `LMACROS` goes through the same CSV reader and escape pass as LANGUAGE, and its cells are not
  trimmed either: a trailing space in a form is part of the form.

## The stock `language.csv`

UZDoom's own strings are not kept as CSV in the source tree. The build runs
`libraries/Translation/scripts/compile.py` over gettext `.po` files (the `generate_language_files`
macro, `CMakeLists.txt:161-172`), writing `language.csv` into the engine pk3 from the `ENGINE`
recipe (`engine/meta`, `engine/common`, `engine/zdoom`; `wadsrc/CMakeLists.txt:3`). The
`game_support.pk3` build gets its own `language.csv` from the per-game `.po` trees, plus
filter-directory copies for Harmony and Hacx (`wadsrc_extra/CMakeLists.txt:3-6`).

What that means for the file a mod overrides:

- The header is `default`, then `Identifier`, then `Filter`, then one column per shipped
  language, spelled with underscores as in the `.po` metadata (`fr`, `pt_BR`, `nb_NO`). The
  remarks column is stripped at build time.
- The `default` column is the `en_US` source text, so every stock row runs delete-earlier. That
  is harmless, since the engine pk3 loads first.
- A language is included once enough of it is translated, or when it is on a fixed allow list
  (`libraries/Translation/scripts/config.py`).
- **A translation identical to the default text is written as an empty cell**, so those
  languages fall through to the default table. Stock empty cells are "use the fallback", never
  "blank".
- The `Filter` cells come from each `.po` entry's context string and use game names as above.

## Errors

The CSV path prints no diagnostics of its own. Malformed input is either silently accepted or
undefined behavior.

| Condition | Result |
|---|---|
| File fails detection (BOM, leading blank line, other first column) | Parsed as classic. The first token is not `[`, so the lump is abandoned with `Found a string without a language specified.` (`:647-666`). Earlier lumps' strings are kept; not fatal. |
| Same, but the file contains any byte of 0x80 or above (any accented text) | The classic parser's binary-lump check reads bytes as signed `char` on x86 builds, so it prints `Skipping binary 'LANGUAGE' lump.` instead (`src/common/engine/sc_man.cpp:311-319`). Same outcome. |
| No `identifier` column | Every row is indexed at column -1. Undefined behavior; observed live as a startup crash (SIGSEGV during `GStrings.LoadStrings`, before the bridge came up) with a two-column `default,fr` file. |
| A row with fewer cells than the header needs, including a blank line in mid-file or an extra blank line at the end (each yields a one-cell row) | Reads past the end of the row. `TArray`'s index operator only asserts in debug builds (`src/common/utility/tarray.h:320-324`), so a release build has undefined behavior. Observed live as the same startup crash, with a file holding both a mid-file blank line and trailing ones (the probe didn't separate the two). Keep every row padded to the header's width. |
| A cell ending in a single `\` | The escape pass reads past the cell's terminator (`:878-883`). Undefined behavior; write `\\`. |
| Unknown game name in `filter` | Never matches; no message. |
| Unknown language code in the header | Creates a table that the lookup chain may never search; no message. |
| `@[` without `]` | Console message `Bad macro in ...`; rest of that string unexpanded. |
| A macro whose male form contains its own `@[name]` | Expansion never terminates (`:753-770`); startup hangs. Observed live: the log stops after `S_Init`, with no crash and no error, and the process had to be killed. |

The three "observed live" results above are from 2026-09-29 on a UZDoom local test build
(5.1.0-pre), DOOM2.WAD, one probe PK3 per case, and a well-formed control file that
loaded and resolved normally.

## Zandronum

Zandronum has no CSV parser; every LANGUAGE lump goes through its classic parser, several times
per lump (once per lookup pass, `src/stringtable.cpp:113-139`). For a CSV lump the first token
is `default` or `identifier`, not `[`, so no language is active and the parser checks whether
the lump is binary (`src/stringtable.cpp:214-226`):

- **CSV with any byte of 0x80 or above** (accented text, a UTF-8 BOM, which Zandronum's scanner
  does not strip): `isText` reads bytes as signed `char` on x86 builds, so the lump counts as
  binary. `Skipping binary 'LANGUAGE' lump.` is printed once per process (the guard flag is
  `static`, `src/stringtable.cpp:143`), the lump contributes no strings, and startup continues.
- **Pure-ASCII CSV:** `ScriptError("Found a string without a language specified.")`, which is
  `I_Error` (`src/sc_man.cpp:888-906`). At startup that exception reaches `main`, which prints
  it and exits (`src/sdl/i_main.cpp:391-396`). **Zandronum refuses to start.**

Either way no CSV string ever reaches Zandronum's table, and a label defined only in a CSV lump
resolves as missing there. A mod that targets both engines needs its strings in a classic lump,
which UZDoom also reads (write `[enu default]` headers; see
[Override order across lumps](language-lump.md#override-order-across-lumps)). A CSV lump added
for UZDoom's region tags is harmless on Zandronum only if it contains non-ASCII text; a pure-ASCII
one must not be in any file Zandronum loads.

## See also

- [The LANGUAGE lump](language-lump.md): classic grammar, language codes, lookup order,
  override order across lumps.
- [Retrieving LANGUAGE strings](string-retrieval.md): what looks a `$LABEL` up, including the
  obituary gender rule.
