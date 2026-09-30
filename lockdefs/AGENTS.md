# lockdefs/: the LOCKDEFS lump

LOCKDEFS defines locks: numbered sets of inventory items a player must hold before a locked line
special, door or UDMF `locknumber` line lets them through, plus the message, sound and automap
color used when they don't. **Read `../shared/AUTHORING.md` and `../shared/ARCHETYPES.md` first.**

**Both engines parse LOCKDEFS**, with the same keyword set and near-identical parsers. Every file
here stamps `Applies to: UZDoom=yes, Zandronum=yes` plus a `Verified against:` pair, and carries an
`## Engine-family divergence` heading wherever the two differ. The biggest difference is the
lock-number range: Zandronum stores locks in a fixed 256-entry array, UZDoom in a map.

If your agent harness has the `zdoom-docs-lookup` subagent registered (adapters for several
harnesses ship in `../agents/`), prefer delegating a lookup question to it instead of reading
this tree by hand. See the root [`AGENTS.md`](../AGENTS.md)'s "Subagents" section.

## Layout

- `INDEX.md`: this section's router.
- `concepts/<topic>.md`: Archetype 3. The whole grammar fits one concept page.

**No `inventory/`/`notes/` here.** LOCKDEFS has six keywords and no engine table large enough to
generate an inventory from. The key items themselves are actor classes, documented under
`../decorate/classes/key.md`.

## Where LOCKDEFS is implemented

| Piece | UZDoom | Zandronum |
|---|---|---|
| Parser (`P_InitKeyMessages`, `ParseLock`, `ParseKeygroup`, `ClearLocks`) and the lock table | `src/gamedata/a_keys.cpp` | `src/g_shared/a_keys.cpp` |
| Runtime check (`P_CheckKeys`) and automap colors (`P_GetMapColorForLock`/`ForKey`) | `src/gamedata/a_keys.cpp` | `src/g_shared/a_keys.cpp` |
| Call site: `P_Init`, run once from `D_DoomMain` after actors and SNDINFO load | `src/p_setup.cpp`, called from `src/d_main.cpp` | `src/p_setup.cpp`, called from `src/d_main.cpp` |
| Lock args of `Door_Animated`, `ACS_LockedExecute`, `ACS_LockedExecuteDoor` (and `FS_Execute`, UZDoom only) | `src/playsim/p_lnspec.cpp` | `src/p_lnspec.cpp` |
| Door lock arg (`Door_LockedRaise`, `Generic_Door` via `EV_DoDoor`) | `src/playsim/mapthinkers/a_doors.cpp` | `src/p_doors.cpp` |
| UDMF line `locknumber` (read, then checked on activation) | `src/maploader/udmf.cpp`, `src/playsim/p_spec.cpp` | `src/p_udmf.cpp`, `src/p_spec.cpp` |
| Automap lock/key coloring | `src/am_map.cpp` | `src/am_map.cpp` |
| ZScript `Actor.CheckKeys`, `Key.IsLockDefined` and friends (UZDoom only) | `src/scripting/vmthunks_actors.cpp` | none |
| Stock lump | `wadsrc/static/lockdefs.txt`; Harmony replacement in `wadsrc_extra/static/filter/harmony/lockdefs.txt` | `wadsrc/static/lockdefs.txt` |
| Boom/Doom line translation to lock numbers (`RCard`..`CardIsSkull` enum) | `wadsrc/static/xlat/defines.i`, `xlat/base.txt` | `wadsrc/static/xlat/defines.i`, `xlat/base.txt` |

Tier-B backing prose: UDB `Build/Scripting/ZDoom_LOCKDEFS.cfg`. It is a keyword list only: it
omits `Chex` from its game constants, shows `LockedSound` taking a single name (the engines accept
a comma-separated list), and its `//$Title "..."` entry is an editor annotation the engines read as
an ordinary comment. See the lump concept.
