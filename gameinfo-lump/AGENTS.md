# gameinfo-lump/: the standalone GAMEINFO lump

GAMEINFO is a small `key = value` lump the engine reads at startup, before the IWAD is chosen,
from the files given on the command line. It can name the IWAD to use, pull in extra files, and
style the startup screen. **Read `../shared/AUTHORING.md` and `../shared/ARCHETYPES.md` first.**

**Naming note.** This section is called `gameinfo-lump` to keep it apart from MAPINFO's
`GameInfo { ... }` block, which is a different thing entirely: a MAPINFO sub-block of game-wide
defaults (menus, intermission, weapon slots), parsed much later. That block is documented at
[`../mapinfo/concepts/gameinfo-block.md`](../mapinfo/concepts/gameinfo-block.md). The two share a
name and nothing else.

**Both engines parse GAMEINFO**, with the same parser shape. UZDoom accepts five keys Zandronum
doesn't, and the two engines resolve the `IWAD` key differently. Every file here stamps
`Applies to: UZDoom=yes, Zandronum=yes` plus a `Verified against:` pair, and carries an
`## Engine-family divergence` heading wherever the two differ.

If your agent harness has the `zdoom-docs-lookup` subagent registered (adapters for several
harnesses ship in `../agents/`), prefer delegating a lookup question to it instead of reading
this tree by hand. See the root [`AGENTS.md`](../AGENTS.md)'s "Subagents" section.

## Layout

- `INDEX.md`: this section's router.
- `concepts/<topic>.md`: Archetype 3. The lump itself, with its full key reference as an inline
  table.

**No `inventory/`/`notes/` here.** The lump has twelve keys at most, all handled in one function,
so a generated inventory would cost more than it saves. The key table lives in the lump concept.

## Where GAMEINFO is implemented

| Piece | UZDoom | Zandronum |
|---|---|---|
| Key parser (`ParseGameInfo`) | `src/d_main.cpp` | `src/d_main.cpp` |
| Lump discovery (`CheckGameInfo`) | `src/d_main.cpp`: opens every `-file` file as a temporary file system and takes the last `GAMEINFO` in the global namespace | `src/d_main.cpp`: walks the `-file` list backwards and takes the first `GAMEINFO` it meets |
| Call site (startup order) | `src/d_main.cpp`, in the startup/restart loop, before `FindIWAD` | `src/d_main.cpp`, same position |
| Which files are scanned (`GetCmdLineFiles`) | `-file` only, loose arguments included | `-file` only, loose arguments included |
| `IWAD` resolution (`IdentifyVersion`) | `src/d_iwad.cpp`: matched against IWADINFO `IWadname` | `src/d_iwad.cpp`: used as if passed to `-iwad` |
| IWADINFO fallback for unset startup fields (`FindIWAD`) | `src/d_iwad.cpp` | `src/d_iwad.cpp` |
| `LOAD` file lookup (`D_AddFile`) | `src/common/utility/findfile.cpp` | `src/d_main.cpp` |
| `NOSPRITERENAME` consumer | `src/d_main.cpp` (sprite rename pass) | `src/w_wad.cpp` |
| Startup screen (`STARTUPTYPE`, `STARTUPSONG`, title/colors) | `src/common/startscreen/` | `src/win32/st_start.cpp`, `src/win32/i_main.cpp` (Windows only) |

Neither engine reads GAMEINFO from the IWAD, from `-optfile` files, from autoload directories, or
from files that another GAMEINFO's `LOAD` pulled in. See the lump concept for the full rule.

Tier-B backing prose: UDB `Build/Scripting/ZDoom_GAMEINFO.cfg` (keyword list only: it knows the
seven keys both engines share and files `NOSPRITERENAME` under constants rather than keywords;
see the lump concept).
