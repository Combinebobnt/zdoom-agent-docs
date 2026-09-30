# The `LANGUAGE` lump

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** ZDoom Wiki `LANGUAGE` (https://zdoom.org/w/index.php?title=LANGUAGE&oldid=55269, retrieved 2026-09-28) plus written from the UZDoom source's `src/common/engine/stringtable.cpp` (`LoadStrings`, `LoadLanguage`, `ParseLanguageCSV`, `GetID`, `ForEachLangID`, `CheckString`, `ProcessEscapes`, `RemapLegacyLanguages`), `src/common/engine/stringtable.h`, `src/common/engine/i_interface.cpp` (`language` cvar), `src/d_main.cpp` (`StrTable_ValidFilter`, the startup `LoadStrings` call), `src/d_iwad.cpp`, `src/gamedata/gi.cpp`, `src/playsim/p_interaction.cpp` (`ClientObituary`, the `Obituary_` LANGUAGE lookup), `wadsrc/static/language.def` and `wadsrc/CMakeLists.txt`, and the Zandronum source's `src/stringtable.cpp` (`LoadStrings`, `LoadLanguage`, `ProcessEscapes`), `src/doomstat.cpp` (`language` cvar), `src/d_main.cpp`, `src/sdl/i_system.cpp` and `src/win32/i_system.cpp` (`SetLanguageIDs`), `src/gi.h`, `src/gi.cpp`, `src/network.cpp` (connect-time lump authentication list), `src/p_acs.cpp` (`PCD_PRINTLOCALIZED`, `PCD_ENDPRINT`) and `wadsrc/static/language.*`. Neither UDB nor SLADE ships a LANGUAGE definition to cross-check against.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

LANGUAGE holds named text strings, optionally per language. Other lumps and scripts refer to a
string by its label, usually written `$LABEL` (MAPINFO level names, LOCKDEFS messages, DECORATE
`Inventory.PickupMessage`, ACS `l:`); the engine looks the label up in the string table built from
every LANGUAGE lump. How those consumer-side lookups work is a separate topic from the lump's own
syntax.

## When it is read

- **Every lump named `LANGUAGE` is parsed, in load order.** Later lumps can override earlier
  ones, but the rules for when they do differ sharply by engine (see "Override order" below).
- **Zandronum** parses them at startup (`D_DoomMain`) and again, from scratch, every time the
  `language` cvar changes. DeHackEd string replacements survive the reparse.
- **UZDoom** parses them once at startup (plus an earlier pass over the base resources for the
  IWAD picker). All languages stay in memory; changing `language` only reselects which tables are
  searched, it does not reparse.
- A LANGUAGE lump that is not text (an old binary-format lump) is skipped with the one-time console
  message `Skipping binary 'LANGUAGE' lump.` on both engines.

## Classic grammar

The lump uses the engine's script tokenizer in C mode: `//` and `/* */` comments, double-quoted
strings, and `[`, `]`, `=`, `;`, `(`, `)` as separate tokens. Labels are case-insensitive.

```text
[enu default]
MY_GREETING = "Hello, ";
MY_LONG     = "First line\n"
              "second line";     // adjacent strings are concatenated up to the ';'
$ifgame(heretic) MY_ITEM = "A wand";
$ifgame(doom)    MY_ITEM = "A pistol";

[fr]
MY_GREETING = "Bonjour, ";

[*]
MY_BRAND = "Always this text, in every language";
```

- **A section header** `[code code ...]` lists one or more language codes. Every string after it
  goes to those languages until the next header. A string before any header is an error (see
  "Errors" below).
- **`label = "text" ["text" ...] ;`**: the text is one or more string tokens, concatenated.
- **`$ifgame(<game>)`** before a label keeps the string only when the running game matches. Both
  engines compare case-insensitively against `Doom`, `Heretic`, `Hexen`, `Strife` or `Chex`; Chex
  Quest does not match `Doom`. UZDoom also accepts `strifeteaser` when running the Strife
  shareware IWAD, and accepts every name during the early IWAD-picker load, before a game is
  chosen. A string filtered out this way is still parsed, so it must still be well-formed.

### Language codes

| Code | Zandronum | UZDoom |
|---|---|---|
| `default` | Fallback table, searched last. | Remapped to `en-US`, which *is* the fallback table, and triggers the "delete earlier files" rule (below). |
| `*` | Searched **first**, ahead of the player's own language. | Same: the global table, searched ahead of every language-specific one. |
| 2- or 3-letter code (`en`, `enu`, `fr`, `ptb`) | Matched against the player's language ID (see below). | A fixed list of legacy codes is remapped to IETF tags (`enu` to `en-US`, `eng` to `en-GB`, `ptg` to `pt`, `jp` to `ja-JP`, and so on); any other code is taken as a bare language. Then matched by language, script and region with fallbacks. |
| Hyphenated tag (`en-GB`, `zh-Hant`) | Fatal error: the tokenizer splits off `-` as its own 1-character code, and `The language code must be 2 or 3 characters long.` | **Not usable in a classic header.** The tokenizer splits `[en-GB]` into `en`, `-` and `GB`, so the strings go to the bare `en` table plus two meaningless ones, never to `en-GB`. The underscore spelling (`[en_GB]`, `[pt_BR]`) is one token and does reach the tagged table, since `_` isn't a split character (`sc_man_scanner.re:69`). The hyphenated spelling works only in a CSV header cell or the `language` cvar. |
| `~` before a code | Suppresses the section for the one lookup pass whose code it names (see "Engine-family divergence"). | Deprecated and ignored, with a script warning. |

Because `enu` remaps to `en-US`, **on UZDoom `[enu]` and `[default]` name the same table**, and
both trigger the delete-earlier rule in a classic header. (In a CSV header only the literal word
`default` triggers it; see [the CSV format](csv-format.md).) The stock Zandronum lump heads its
English strings `[enu default]`. UZDoom's stock strings are a CSV-format `language.csv` generated at
build time from the source's `libraries/Translation/` tree into the engine pk3, next to a small
classic `language.def` (`[default]`, DeHackEd-only music and sprite names).

### Escapes

Inside the text, both engines translate `\n` (newline), `\c` (the text-color escape, so `\cD` or
`\c[Gold]` colors the following text), `\r`, `\t`, and a backslash before a line break (the break
is dropped). Any other backslash pair yields the second character, so `\\` is a backslash and `\"`
a quote. UZDoom adds `\xHH`, one or two hex digits giving a raw byte; `\x00`, or `\x` followed by
no hex digit, produces nothing.

## Which string wins

### The player's language

- **Zandronum:** the `language` cvar (default `auto`) holds a 2-3 letter code. On Windows, `auto`
  (or any value not 2-3 characters long) reads the user and system locale's abbreviated language
  names, such as `enu` or `fra`. **On non-Windows builds the language ID is hardcoded to `enu` and
  the cvar has no effect** other than forcing a reparse. That includes Linux dedicated servers.
- **UZDoom:** the `language` cvar (default `auto`, stored in the global config) takes a legacy code
  or a BCP 47 tag. `auto` reads the OS locale (on non-Windows: `LC_ALL`, `LC_MESSAGES`, then
  `LANG`; `C`/`POSIX` or unset mean `en-US`). A value shorter than 2 characters means `default`.

### Lookup order

**UZDoom** searches its tables in a fixed order and returns the first hit: the DeHackEd override
table, then `[*]`, then the player's exact region, its mapped fallback region, script, fallback
script, bare language, fallback language, and finally the default (`en-US`) table. A `[*]` string
therefore beats a string written for the player's own language. The fallback mappings are few and
fixed (for example `en-AU` and `en-CA` fall back to `en-GB`; `zh-TW` to `zh-Hant-TW`).

**Zandronum** gets the same effective priority from numbered passes. For each LANGUAGE lump it
parses the lump repeatedly: once for `*`, then for each of its four language IDs an exact-code
pass, a 2-letter-prefix pass (so `[en]` matches `enu`) and a same-prefix pass (so `[eng]` also
matches `enu`), and last once for `default`. A lower pass number is a more preferred match.
DeHackEd strings sit below all of them and are never replaced by LANGUAGE.

### Override order across lumps

This is the main behavioral split, and it decides whether a mod can replace a stock string with a
plain `[default]` section.

- **Zandronum:** a later lump's string replaces an existing one **only if it came from an equally
  or more preferred pass**. A later `[enu]` or `[*]` string replaces an earlier `[enu]` one, but a
  later `[default]`-only string does not. Since the stock English strings are under
  `[enu default]`, **a mod's `[default] LABEL = ...` does not override a stock string for an
  English player.** Write `[enu default]` (the stock header) to override for English and fall
  back everywhere else, or `[*]` to override every language.
- **UZDoom:** each string is stored per language table, and a later file's entry replaces the
  earlier one in that table. In addition, a string under `[default]` (or `[enu]`)
  **deletes that label from every language table where it came from an earlier file**. So a mod's
  `[default]` string replaces the stock English one and also removes stock translations of the
  same label, so players in any language see the mod's text, not a stale translation.

The practical rule that works on both engines: to replace a stock string, use `[enu default]`. On
UZDoom this behaves as `[default]`; on Zandronum it hits both the exact `enu` pass and the fallback.

## Errors

| Condition | Zandronum | UZDoom |
|---|---|---|
| String before any `[...]` header | Fatal: `Found a string without a language specified.` | Console message with the same text; **the rest of that lump is abandoned**, earlier strings kept. |
| Same, in a lump with any byte of 0x80 or above | `Skipping binary 'LANGUAGE' lump.` (once per process); the lump is ignored, not fatal | Same |
| Language code of the wrong length | Fatal (2-3 characters, `*` or `default` only) | Only an empty code is fatal. |
| `~` at the end of a header | Fatal: `You must specify a language after ~` | Warning only. |
| `$` not followed by `ifgame ( <name> )` | Fatal script error | Fatal script error |
| Missing `=` or `;` | Fatal script error | Fatal script error |

## Engine-family divergence

UZDoom-only, not parsed by Zandronum at all:

- **CSV format.** A LANGUAGE lump whose first bytes are `default,` or `identifier,` (any case) is
  read as a spreadsheet, where an **empty cell deletes** the string. See
  [The CSV LANGUAGE format](csv-format.md). On Zandronum a pure-ASCII CSV lump is a fatal startup
  error, and one with non-ASCII text is skipped as binary.
- **`LMACROS` and `@[name]`.** An `LMACROS` lump (a CSV: name, language, then male, female,
  neutral and object forms) defines macros; each one clears the macros of earlier ones. A string
  containing `@[name]` is stored in four gendered variants, and the variant shown follows the
  local player's `gender`. An undefined macro expands to nothing. Detail in
  [the CSV format](csv-format.md#lmacros-and-name).
- **`$$LABEL` redirects.** A stored string beginning with `$$` is looked up again under the label
  that follows.
- **`\xHH` escapes**, BCP 47 language tags (CSV headers, the `language` cvar, and the underscore
  spelling in a classic header) and region/script fallbacks (above).
- **Implicit obituary labels.** When a player is killed by another actor, a string labeled
  `Obituary_<AttackerClass>_<damagetype>`, then `Obituary_<AttackerClass>`, overrides the
  attacker's `Obituary`/`HitObituary` property (`src/playsim/p_interaction.cpp:250-255`). Zandronum
  has no such lookup. Full fallback chain: [String retrieval](string-retrieval.md).

Behavior both engines have, differently:

- **Override order across lumps** and the meaning of `[default]` (above).
- **`~`.** Zandronum still honors it, but narrowly: `~code` suppresses the section only during the
  lookup pass whose code it names. If another code in the same header matches a different pass
  for the same player (as `[en ~enu]` does for an `enu` player through the 2-letter pass), the
  strings still load. UZDoom ignores `~` entirely.
- **Error severity** (see "Errors").
- **The `language` cvar** is inert on non-Windows Zandronum.

## Zandronum-specific: which machine's copy is used

LANGUAGE is not among the lumps Zandronum checksums when a client connects
(`src/network.cpp`'s authentication list), so a client and server can run different LANGUAGE
contents with no connect error. Each machine resolves labels against its own table:

- **ACS `l:`** (`PCD_PRINTLOCALIZED`) resolves on whichever side runs the script. For a
  server-side script the server's own string table is used, and `Print`/`PrintBold`/`HudMessage`
  send clients the already-resolved text. A client's own translation is never consulted, and on a
  non-Windows server that text is always the `enu`/`default` one.
- Labels resolved on the client (menus, the HUD, a client-side script) use the client's copy and
  language.

## See also

- [Retrieving LANGUAGE strings](string-retrieval.md) for what each consumer does with a `$LABEL`,
  when it resolves it, what a missing label shows, and which machine resolves it on Zandronum.
- [The CSV LANGUAGE format](csv-format.md): detection, header columns, quoting, filter,
  empty-cell deletion, `LMACROS` (UZDoom only).
- [`../../acs/functions/strparam.md`](../../acs/functions/strparam.md) for ACS's `l:` print cast.
- [`../../lockdefs/concepts/lockdefs-lump.md`](../../lockdefs/concepts/lockdefs-lump.md) and
  [`../../mapinfo/concepts/map-block-and-inheritance.md`](../../mapinfo/concepts/map-block-and-inheritance.md)
  for two lumps whose `$`-prefixed values are LANGUAGE labels.
