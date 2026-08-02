# `sv_forbidvoteflags`

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** Zandronum source `src/callvote.cpp` + verified against declared CVAR behavior and flag aliasing.

Master bitfield that controls which vote types are disabled on the server. Multiple individual `sv_no*vote` cvars (e.g., `sv_nokickvote`, `sv_nomapvote`) are **Flag-type aliases** into this single bitfield — setting one alias updates the master, and vice versa.

## Bitfield layout and vote-type aliases

Each bit in `sv_forbidvoteflags` corresponds to one vote type. The individual Flag cvars provide named access to each bit:

| Bit | Value | CVar name | Vote type |
|-----|-------|-----------|-----------|
| 0 | 1 | `sv_nokickvote` | Kick votes |
| 1 | 2 | `sv_noforcespecvote` | Force-to-spectator votes |
| 2 | 4 | `sv_nomapvote` | Map votes |
| 3 | 8 | `sv_nochangemapvote` | Change-map votes |
| 4 | 16 | `sv_nofraglimitvote` | Frag-limit votes |
| 5 | 32 | `sv_notimelimitvote` | Time-limit votes |
| 6 | 64 | `sv_nowinlimitvote` | LMS win-limit votes |
| 7 | 128 | `sv_noduellimitvote` | Duel-limit votes |
| 8 | 256 | `sv_nopointlimitvote` | Point-limit votes |
| 9 | 512 | `sv_noflagvote` | DMFlag votes |
| 10 | 1024 | `sv_nonextmapvote` | Next-map votes |
| 11 | 2048 | `sv_nonextsecretvote` | Next-secret-map votes |
| 12 | 4096 | `sv_noresetmapvote` | Reset-map votes |

For example, `sv_nokickvote` true sets bit 0 (value 1) in `sv_forbidvoteflags`; setting `sv_nomapvote` true sets bit 2 (value 4) independently. Multiple bits can be set simultaneously (e.g., `sv_forbidvoteflags 7` disables kicks, force-spec, and map votes).

## Server replication and cvar behavior

This cvar is marked `CVAR_ARCHIVE | CVAR_SERVERINFO`, so the flag state persists to the config file and is replicated to clients. Changing any individual alias (`sv_nokickvote`, `sv_nomapvote`, etc.) automatically updates `sv_forbidvoteflags` (and vice versa) — they are synchronized views of the same bitfield, not independent cvars.

The flag-aliasing pattern — where one "master" bitfield cvar has multiple named boolean aliases — appears elsewhere in the engine for other bitmask categories (see the `dmflags` / `dmflags2` family and related Flag cvars).

## Related cvars

- **Individual vote-type cvars** (all Flag aliases into this bitfield): `sv_nokickvote`, `sv_noforcespecvote`, `sv_nomapvote`, `sv_nochangemapvote`, `sv_nofraglimitvote`, `sv_notimelimitvote`, `sv_nowinlimitvote`, `sv_noduellimitvote`, `sv_nopointlimitvote`, `sv_noflagvote`, `sv_nonextmapvote`, `sv_nonextsecretvote`, `sv_noresetmapvote`.
- **`sv_nocallvote`** — separately controls whether any votes can be called at all (0 = all allowed, 1 = none, 2 = players only).
- **`sv_votecooldown`** — cooldown between votes in minutes.
- **`sv_voteconnectwait`** — seconds a client must wait after connecting before being allowed to call votes.
