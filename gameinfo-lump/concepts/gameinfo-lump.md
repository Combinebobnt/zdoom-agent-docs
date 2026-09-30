# The `GAMEINFO` lump

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** ZDoom Wiki `GAMEINFO` (https://zdoom.org/w/index.php?title=GAMEINFO&oldid=51315, retrieved 2026-09-28) + verified against the UZDoom source's `src/d_main.cpp` (`ParseGameInfo`, `CheckGameInfo`, `GetCmdLineFiles`, the startup loop, `AddAutoloadFiles`, the sprite rename pass), `src/d_main.h`, `src/d_iwad.cpp` (`IdentifyVersion`, `FindIWAD`), `src/common/utility/findfile.cpp` (`D_AddFile`), `src/common/engine/sc_man_scanner.re`, `src/common/startscreen/startscreen.cpp`, `src/d_main.cpp:2634`, `src/d_main.cpp:4110-4120`, `src/d_main.cpp:4342-4346`; and the Zandronum source's `src/d_main.cpp` (`ParseGameInfo`, `CheckGameInfo`, `GetCmdLineFiles`, `D_AddFile`), `src/d_iwad.cpp`, `src/w_wad.cpp:821`, `src/cmdlib.cpp:170-179`, `src/win32/st_start.cpp:280-292`, `src/sdl/st_start.cpp:107-111`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

GAMEINFO is a short `key = value` text lump that the engine reads at startup, before it has
picked an IWAD. It lets a mod name the IWAD it needs, pull in extra files, and style the startup
screen, so that launching the engine with just the mod's file does the right thing. It is not
MAPINFO's `GameInfo { ... }` block; that one is at
[`mapinfo/concepts/gameinfo-block.md`](../../mapinfo/concepts/gameinfo-block.md).

```text
// Example GAMEINFO (a pk3's gameinfo.txt, or a WAD lump named GAMEINFO)
IWAD = "doom2.wad"
LOAD = "mymod_music.pk3", "mymod_extras.wad"
STARTUPTITLE = "My Mod v1.0"
STARTUPCOLORS = "ff ff ff", "40 00 00"
LOADLIGHTS = 1
```

## When and where it is read

- **Only files passed with `-file` are searched**, including bare file arguments, which both
  engines fold into `-file` (`CollectFiles`, UZDoom `src/d_main.cpp:2241`, Zandronum
  `src/d_main.cpp:2416`). The IWAD, `-optfile` files, autoload directories, and the engine's own
  resource file are not searched. A GAMEINFO in any of those places is never read.
- **It is read before IWAD selection.** Both engines call `CheckGameInfo` at the top of the
  startup loop, right before `FindIWAD` (UZDoom `src/d_main.cpp:4110-4120`, Zandronum
  `src/d_main.cpp:2803-2812`). That is earlier than autoload, DEHACKED, and every other lump
  format, including MAPINFO.
- **Only one GAMEINFO is parsed; there is no merging.** UZDoom opens all `-file` files as a
  temporary file system and takes the last `GAMEINFO` lump in the global namespace
  (`src/d_main.cpp:2188-2207`). Zandronum walks the `-file` list from the last file backwards and,
  inside the first file that has one, takes the last `GAMEINFO` lump at the archive root
  (`src/d_main.cpp:2305-2361`). Both come to the same thing: the GAMEINFO in the latest-loaded
  file wins and every other one is ignored. A mod loaded after yours that has its own GAMEINFO
  silently replaces yours in full.
- **Root only.** The lump must be in the global namespace: a pk3's `gameinfo.txt` at the archive
  root, or a WAD lump named `GAMEINFO`. One inside a subfolder is not found.
- **Files pulled in by `LOAD` are not searched for GAMEINFO.** The scan has already finished by
  the time they are added to the list.
- **Restart.** On UZDoom the startup loop re-runs on the `restart` console command, so GAMEINFO
  is read again; the startup fields are reset first (`src/d_main.cpp:4342-4346`).

## Syntax

- One `key = value` entry after another. Line breaks don't matter; the parser works on tokens.
- **Keys are case-insensitive identifiers** and the `=` is mandatory.
- **Values are strings, quoted or bare.** `LOAD` takes a comma-separated list. `STARTUPCOLORS`
  takes exactly two comma-separated values.
- **Comments:** `//` to end of line and `/* ... */` both work.
- **Quote every value.** Values are read by the older Hexen-style string scanner, where `,` is
  not a delimiter. A bare value written directly against its comma (`LOAD = a.wad, b.wad`) is read
  as the string `a.wad,`, the comma is lost, and the next item is then parsed as a key, which
  fails with a script error. Quoted values (`"a.wad", "b.wad"`) or a space before the comma avoid
  this. (Scanner rules: UZDoom `src/common/engine/sc_man_scanner.re:55-77, 306-323`.)
- **No semicolons.** `;` is not a usable comment or terminator here: every value is followed by a
  read in key position, which expects an identifier, so a `;` between entries is a script error.
- **Unknown keys are skipped silently** on both engines, together with any comma-separated
  values after them (UZDoom `src/d_main.cpp:2167-2175`, Zandronum `src/d_main.cpp:2292-2300`).
  This is why UZDoom-only keys are harmless in a GAMEINFO that Zandronum also reads. Contrast
  MAPINFO's `GameInfo` block, where a UZDoom `intro { ... }` block is fatal on Zandronum.

## Key reference

Twelve keys on UZDoom (`src/d_main.cpp:2071-2166`), seven on Zandronum
(`src/d_main.cpp:2213-2291`). Key names are case-insensitive.

| Key | Value | UZDoom | Zandronum | What it does |
|---|---|---|---|---|
| `IWAD` | string | yes | yes | Names the IWAD to start with. `-iwad` on the command line overrides it on both engines. How the name is matched differs per engine (see below). |
| `LOAD` | string list | yes | yes | Extra files to load. Each is looked for beside the file holding the GAMEINFO first, then by its name as given. They load **before** the `-file` files, in the order listed. A missing file prints `Can't find '<name>'` and is skipped; it is not fatal. |
| `NOSPRITERENAME` | `true` or anything else | yes | yes | Despite the name, `true` **turns sprite renaming on for every file**, not off. See below. |
| `STARTUPTITLE` | string | yes | yes | Title text shown on the startup banner. Falls back to the IWAD's IWADINFO `Name`. |
| `STARTUPCOLORS` | two colors, `fg, bg` | yes | yes | Banner text and background colors. Each value uses the engine's usual color-string grammar (see the color bullet in [the MAPINFO GameInfo page](../../mapinfo/concepts/gameinfo-block.md#properties-with-typeformat-notes)). Falls back to IWADINFO `BannerColors` when both are 0 (black on black). |
| `STARTUPTYPE` | `DOOM`, `HERETIC`, `HEXEN` or `STRIFE` | yes | yes (Windows only) | Which graphical startup screen to show. Any other word means "default", which picks by game type. `DOOM` forces the generic screen even on a Hexen/Heretic/Strife IWAD. |
| `STARTUPSONG` | music name | yes | yes (Windows only) | Music played during startup. Only the **Hexen** startup screen plays music, so this does nothing with the other types. Default `orb`. |
| `LOADLIGHTS` | integer | yes | no | `1` loads the engine's `lights.pk3`, `0` suppresses it, unset follows IWADINFO and then the user's autoload setting. `1` still loses to `-noextras`, the matching `-nolights`/`-nobrightmaps`/`-nowidescreen` switch, and a shareware IWAD (`AddAutoloadFiles`, `src/d_main.cpp:2260-2279`). |
| `LOADBRIGHTMAPS` | integer | yes | no | Same, for `brightmaps.pk3`. |
| `LOADWIDESCREEN` | integer | yes | no | Same, for `game_widescreen_gfx.pk3`. |
| `DISCORDAPPID` | string | yes | no | Parsed and thrown away. Discord presence support is disabled in this checkout (the storing line is commented out, `src/d_main.cpp:2157-2161`). |
| `STEAMAPPID` | digit string | yes | no | Stored, falling back to IWADINFO `SteamAppId`. A value with any non-digit is cleared with the red console message `SteamAppId must be a numerical value!` (`src/d_main.cpp:4152-4168`). No code in this checkout reads the stored value. |

### `IWAD`

- **UZDoom** compares the value, case-insensitively, against the `IWadname` field of the IWADINFO
  entry of every IWAD it found in its search paths, and picks the highest-priority match
  (`src/d_iwad.cpp:750-763`). The value is an IWADINFO `IWADName` (for example `doom2.wad`), not
  a path. That is the canonical name of the game the engine *identified* from the IWAD's contents,
  not the file's name on disk: a re-release identified as its own edition carries its own name
  (the shipped IWADINFO lists `doom2bfg.wad`, `doom2kex.wad` and `doom2unity.wad` alongside
  `doom2.wad`), so `IWAD = "doom2.wad"` doesn't select it. An IWAD with its own embedded IWADINFO
  contributes its own `IWADName`. A match also suppresses the IWAD picker, unless the user holds the picker's query
  key. No match is not an error: selection carries on as if the key were absent. When
  `-showlauncher` is on the command line, the `IWAD` key is ignored entirely
  (`src/d_main.cpp:2071`).
- **Zandronum** substitutes the value for `-iwad` when no `-iwad` was given
  (`src/d_iwad.cpp:397-400`). It is then treated exactly like a `-iwad` argument: a path (relative
  to the current directory) or a bare name, `.wad` appended when there is no extension, searched
  in the current directory and then the IWAD search directories. It may also name a directory to
  search. If it isn't found, the normal IWAD choice runs. It is not resolved relative to the file
  holding the GAMEINFO.

### `LOAD`

- The directory of the file holding the GAMEINFO is tried first (`<that dir>/<name>`); if nothing
  is there, the name is used as given. Files are inserted at the front of the `-file` list in
  listed order (UZDoom `src/d_main.cpp:2076-2104`, Zandronum `src/d_main.cpp:2218-2253`), so
  they load before the mod that named them and the mod can override their contents.
- They count as `-file` files afterwards, including for the fatal refusal to load extra files
  with a shareware IWAD.
- Lookup details differ per engine; see the divergence section.

### `NOSPRITERENAME`

Some Heretic, Hexen and Strife sprite names collide with sprite names the engine's built-in
actors already use for another game, so on those games the engine renames a fixed set of sprites
at load time (one table per game). Normally only sprites that come from the IWAD are
renamed. `NOSPRITERENAME = true` sets the same internal flag as the `-oldsprites` command-line
switch, which makes the rename apply to **sprites in every loaded file** (UZDoom
`src/d_main.cpp:2634`, Zandronum `src/w_wad.cpp:821`). The name reads backwards relative to the
effect. It matters only for a mod carrying sprites that were made for the original
Heretic/Hexen/Strife names. On Doom there is no rename table, so it has no effect. The value
comparison is case-insensitive; any value other than `true` leaves the flag off.

### Startup screen keys

- **UZDoom** uses a cross-platform start screen (`src/common/startscreen/`). `STARTUPTITLE` and
  `STARTUPCOLORS` draw its header banner, and the title also feeds the window title when the
  friendly-window-title option is on. When `STARTUPTYPE` is unset or unrecognized, UZDoom first
  falls back to the IWAD's IWADINFO `StartupType` (`src/d_iwad.cpp:980`), then to the game type
  (`src/d_main.cpp:3537-3545`). `STARTUPSONG` falls back to IWADINFO `StartupSong`. No start
  screen is shown for `-host`/`-join` games, on `restart`, or with `-nostartup`.
- **Zandronum** uses these keys only in its Windows build: the startup title banner in
  `src/win32/i_main.cpp` and the graphical startup screens in `src/win32/st_start.cpp:280-292`.
  Non-Windows builds always use a text-mode startup (`src/sdl/st_start.cpp:107-111`) and ignore
  `STARTUPTYPE` and `STARTUPSONG`; the title and colors are not drawn anywhere there either.

## Errors

- A malformed entry is a **fatal startup error** on both engines: the scanner raises a script
  error, reported as `Script error, "GAMEINFO" line <n>: ...`, and the engine exits. Causes
  include a key that isn't an identifier, a missing `=`, a missing value at end of file,
  `STARTUPCOLORS` without the comma, and a non-numeric `LOADLIGHTS`/`LOADBRIGHTMAPS`/
  `LOADWIDESCREEN` (`LOADLIGHTS = true` fails with `Bad numeric constant "true"`).
- Things that are **not** errors: an unknown key, an `IWAD` that matches nothing, a `LOAD` file
  that can't be found, an unrecognized `STARTUPTYPE` word, a non-numeric `STEAMAPPID` (cleared
  with a message).

## Wiki/engine divergence

Where the ZDoom Wiki page says more than this checkout does:

- **`DISCORDAPPID`:** the wiki describes a Discord rich-presence ID with a "GZDoom" fallback. In
  this checkout the key is parsed and discarded (see the table above).
- **`STEAMAPPID`:** the wiki says the game appears under that ID in Discord's rich presence. The
  value is stored and digit-checked, but nothing reads it.
- **`LOADLIGHTS`, `LOADBRIGHTMAPS`, `LOADWIDESCREEN`:** the wiki says `1` "forcibly" loads the
  pk3. `1` still loses to the matching `-no*` switch, `-noextras`, and a shareware IWAD.
- **`NOSPRITERENAME`:** the wiki only says renaming happens. `true` widens renaming from IWAD
  sprites to every loaded file's sprites, the same as `-oldsprites`.

## Engine-family divergence

- **Five UZDoom-only keys:** `LOADLIGHTS`, `LOADBRIGHTMAPS`, `LOADWIDESCREEN`, `DISCORDAPPID`,
  `STEAMAPPID`. Zandronum skips them silently, so a shared GAMEINFO may carry them.
- **`IWAD` matching.** UZDoom matches the IWADINFO `IWadname` of an IWAD it has already found and
  ignores the key under `-showlauncher`. Zandronum treats the value as a `-iwad` path or name. A
  plain name such as `doom2.wad` works on both when it is both the file's name and its IWADINFO
  name; a relative path only works on Zandronum, and on UZDoom the value must equal an
  `IWADName` the engine knows, built-in or from the IWAD's own IWADINFO.
- **`LOAD` on Zandronum clients.** A Zandronum client started with `-connect` skips every `LOAD`
  entry (`src/d_main.cpp:2241-2242`); per the source comment, the client relies on
  the launcher, which learns a server's full file list (including its `LOAD` files), to pass
  them on the command line instead.
- **`LOAD` lookup beside the file.** UZDoom accepts a file or a directory there
  (`DirEntryExists`); Zandronum accepts only a regular file (`FileExists`,
  `src/cmdlib.cpp:170-179`), so a directory next to the mod falls through to the name as given.
  UZDoom also splits the mod's path at `:` when it has no `/`, for Windows drive-relative names.
- **`LOAD` fallback search on UZDoom Linux builds.** When a `LOAD` name isn't found beside the
  mod, it goes through `D_AddFile`. On UZDoom's `__unix__` builds that function first retries the
  name case-insensitively within its own directory and returns failure if that doesn't find it,
  before reaching the engine's file search paths (`src/common/utility/findfile.cpp:65-109`). A
  bare `LOAD` name that is neither beside the mod nor in the current directory is therefore
  dropped with only a developer-level warning, where Windows builds and Zandronum would still
  search the configured file paths. Keep `LOAD` targets next to the file that names them.
- **Startup screen keys are Windows-only on Zandronum**; UZDoom honors them on every platform.
- **IWADINFO fallback.** UZDoom fills every unset startup field (title, colors, type, song, the
  three `LOAD*` switches, Steam id) from the chosen IWAD's IWADINFO (`src/d_iwad.cpp:967-983`).
  Zandronum falls back only for the title and colors (`src/d_iwad.cpp:620-625`); an unset
  `STARTUPTYPE` there picks by game type directly.

## Tooling note

UDB's GAMEINFO highlighting config (`Build/Scripting/ZDoom_GAMEINFO.cfg`) lists only six keys as
keywords (`IWAD`, `LOAD`, `STARTUPTITLE`, `STARTUPCOLORS`, `STARTUPTYPE`, `STARTUPSONG`) and puts
`NOSPRITERENAME` under constants. It has none of the five UZDoom-only keys.
