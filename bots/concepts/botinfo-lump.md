# The `BOTINFO` lump

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** Zandronum Wiki `BOTINFO` (retrieved 2026-09-09, https://wiki.zandronum.com/w/index.php?title=BOTINFO&oldid=2586) + verified against the Zandronum source's `src/bots.cpp` (`BOTS_ParseBotInfo`, lines 504-518, which feeds every `BOTINFO` lump to `bots_ParseBotInfoLump`, lines 1047-1347; defaults at lines 1058-1077; `CLEARBOTS` at lines 1081-1083 calling `BOTS_Destruct`, lines 448-468), and `src/bots.h` (`BOTINFO_s` struct, lines 400-462; `BOTSKILL_e` enum, lines 105-120). Loose-directory loading: `src/d_main.cpp` (`D_AddFile`'s `DirEntryExists` check, line 1864), `src/w_wad.cpp` (`FWadCollection::AddFile`, `OpenDirectory` at line 317) and `src/resourcefiles/resourcefile.cpp` (`FResourceLump::LumpNameSetup`, lines 97-104). Re-checked for UZDoom in the same session: no occurrence of `BOTINFO` anywhere under `src/`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

`BOTINFO` declares a bot: its name, its cosmetic identity, its six skill ratings, and which
compiled botscript lump drives it (see [botscript-lump-format.md](botscript-lump-format.md)). It
is a plain text lump of brace-delimited blocks, one per bot, each holding `key = value` pairs.

## Lumps are additive, not replacing

The engine scans **every loaded archive**, in load order, for a lump named `BOTINFO` and appends
the bots each one declares. By default a mod therefore adds bots to the stock roster (the stock
bots come from the engine's own `botinfo.txt`) rather than overriding it, and two mods declaring
bots do not conflict. There is no need to restate the stock bots.

The one replace form is a bare `CLEARBOTS` token placed outside any braces. While looking for the
next `{`, the parser checks each token against `CLEARBOTS` (case-insensitive) and, on a match,
calls `BOTS_Destruct`, which empties every bot defined so far: the stock bots and any earlier
lump's alike. It also deletes the skull-bot state of any player that currently has one and clears
that player's bot flag (`bots.cpp:455-467`). Bots declared after it in the same lump, and in later-loaded lumps, are added as
usual. Any other stray token outside braces is skipped silently.

## Keys

**An unrecognized key is fatal, not ignored.** The parser's terminal `else` is
`I_Error( "BOTS_ParseBotInfo: Unknown BOTINFO property, \"%s\"!" )`, so a typo in a key name takes
the whole process down at load time rather than leaving that property at its default. The same
goes for a missing `=` between key and value. This lump is unusually strict compared to most
ZDoom-family text lumps, which tend to skip what they don't recognize — do not assume a property
borrowed from a newer Zandronum version will be politely ignored by an older one.

| Key | Value | Cap |
|---|---|---|
| `name` | Display name. | 63 chars |
| `script` | **Lump** name of the compiled botscript, not a filename. | 8 chars, hard error |
| `accuracy`, `intellect`, `evade`, `anticipation`, `reactiontime`, `perception` | Skill rating, `-2` to `6`. | hard error outside range |
| `favoriteweapon` | Weapon class name. | 31 chars |
| `class` | Player class name. | 31 chars |
| `color` | Player color. | 15 chars |
| `colorset` | Named color set. | 31 chars |
| `gender` | Gender string. | 15 chars |
| `skin` | Skin name. | 31 chars |
| `railcolor` | A name (`blue`, `red`, `yellow`, `black`, `silver`, `gold`, `green`, `white`, `purple`, `orange`, `rainbow`) or a raw number. | — |
| `chatfrequency` | `0` to `100`. | hard error above 100 or below 0 |
| `revealed` | `true`/`false`, or any number (nonzero is true). A runtime `reveal` is lost at a normal quit; see [skininfo.md](../../zandronum-lumps/concepts/skininfo.md#revealing-a-hidden-skin-lasts-only-the-session). | — |
| `chatfile` | Chat file path, on disk beside the executable (not in an archive). Format: [bot-chat-file.md](bot-chat-file.md). | 127 chars |
| `chatlump` | Chat lump name or full archive path. Format: [bot-chat-file.md](bot-chat-file.md). | 31 chars, hard error |

Any value token is truncated to 127 characters before the per-key cap is applied.

### The skill scale is offset, and `-2..6` covers nine values

The six skill keys accept `-2` through `6` and store the value offset by `BOTSKILL_LOW`, which is
`2`. So the accepted range maps onto the whole `BOTSKILL_e` enum, and `0` is not the midpoint —
it's the third-lowest rating:

| Value | Resulting skill |
|---|---|
| `-2` | `BOTSKILL_VERYPOOR` |
| `-1` | `BOTSKILL_POOR` |
| `0` | `BOTSKILL_LOW` |
| `1` | `BOTSKILL_MEDIUM` |
| `2` | `BOTSKILL_HIGH` |
| `3` | `BOTSKILL_EXCELLENT` |
| `4` | `BOTSKILL_SUPREME` |
| `5` | `BOTSKILL_GODLIKE` |
| `6` | `BOTSKILL_PERFECT` |

A value outside `-2..6` is a fatal `I_Error` naming the offending field, not a clamp or a warning.
Note that the parse uses `atoi`, so a non-numeric value reads as `0` and silently becomes
`BOTSKILL_LOW` rather than erroring.

### `intelect` is accepted as a misspelled alias

The parser matches `intelect` **or** `intellect` for the same field. The single-`l` spelling is not
a typo to fix in an existing lump — both are equally valid input, and only the correctly-spelled
one is worth using in new material.

## `script` names a lump and is capped at 8 characters

The value is a lump name resolved with `Wads.OpenLumpName`, so any loaded archive can supply the
botscript. A value longer than 8 characters is a fatal error at parse time, which in practice ties
the botscript's lump name to the 8-character ceiling even where the containing archive would allow
a longer one.

Omitting `script` entirely is legal, unlike misspelling it: the field defaults to empty and the
spawn path guards on `szScriptName[0]` before opening any lump, so the bot simply runs with no
compiled behavior driving it.

## A loose directory is a valid bot package

Zandronum's `-file` accepts a plain directory as well as an archive. `d_main.cpp`'s `D_AddFile`
accepts any existing directory entry, and `w_wad.cpp`'s `FWadCollection::AddFile` mounts a
directory with `FResourceFile::OpenDirectory`. Each root-level file's lump name is derived by
stripping the extension, uppercasing, and truncating to 8 characters. So a directory holding `botinfo.txt`
and `mybot.lmp` loads as a complete bot package with no zip step: those become the lumps `BOTINFO`
and `MYBOT`, and a `script = "mybot"` line resolves against the latter.

This is worth knowing for iteration specifically — editing a loose file and relaunching is a much
shorter loop than repacking an archive between attempts.

## Wiki/engine divergence

The Zandronum Wiki page cites several ranges that do not match the actual parser source:

**Skill rating ranges.** The wiki states each of the six skill keys (accuracy, intellect, evade, anticipation, reactiontime, perception) accepts `0` to `4`. The actual parser accepts `-2` through `6` (nine values), which map onto the full `BOTSKILL_e` enum via offset-by-`BOTSKILL_LOW` (2). A value outside `-2..6` is fatal; a non-numeric value reads as `0` and silently becomes `BOTSKILL_LOW` rather than erroring.

**`chatfrequency` range.** The wiki states `1` to `100`; the parser accepts `0` to `100`. It only tests for a value above `100`, but the field is unsigned (`ULONG`), so a negative value wraps to a huge number and is fatal too.

**`script` property.** The wiki lists five specific allowed values: `CRASHBOT`, `DFULTBOT`, `FATBOT`, `HUMANBOT`, `SAUSGBOT`. The parser actually accepts any lump name up to 8 characters — those five are simply the stock botscript lumps in the Zandronum source's `wadsrc/static/`, not a closed set. Custom botscripts with other names work identically.

**`chatfile` long-filename caveat.** The wiki mentions "long filenames may cause a crash"; the parser clamps the path to 127 characters via `strncpy` before any downstream processing. Current source has no crash path for a long name after that either: the chat-file loader copies it into 1024-byte buffers (`src/botcommands.cpp:2143`, `:2210`) and prefixes the executable's directory in another 1024-byte buffer (`:372-377`). The warning likely predates the clamp.

## Engine-family divergence: no counterpart outside Zandronum

UZDoom/GZDoom-family engines do not parse `BOTINFO` at all. Their bot support is an unrelated
subsystem that takes no such lump, so this file describes a Zandronum-only mechanism with nothing
to port to — see [botscript-lump-format.md](botscript-lump-format.md)'s divergence section for the
same conclusion on the bytecode half.
