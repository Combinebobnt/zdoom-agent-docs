# ACS_Execute

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** written from the Zandronum source's `src/botcommands.cpp` (`botcmd_ACS_Execute`); the map-number lookup is `FindLevelByNum` in `src/g_mapinfo.cpp:128`. No wiki page covers this command.

## Engine-family divergence

`ACS_Execute` is a bot command, not an ACS/BCS function — it lives in Zandronum's bot-command
dispatcher (`botcommands.cpp`), which UZDoom/GZDoom-family engines don't have at all. There is no
UZDoom counterpart to diverge from; see `../AGENTS.md`.

The bot command surface's bridge into ACS — one of three related commands (see "Related" below),
this one the plain fire-and-forget form: numbered script, no result. Call shape is
`ACS_Execute(script, map, arg0, arg1, arg2)` — 5 int arguments, `RETURNVAL_VOID`.

- **`script`** — a numbered ACS script (positive script number; there is no way to target a named
  script from this command — see `ACS_NamedExecuteWithResult`).
- **`map`** — a map *number* (`FindLevelByNum`, the numeric `MAPxx`/`ExMx`-style lookup, not a map
  lump name). `0`, or any number that matches no defined level's `levelnum`, means "run on the current
  map" (`level.mapname`) — this is a silent fallback, not an error; there is no way to distinguish
  "explicitly asked for the current map" from "gave an invalid map number" from the caller's side.
- **`arg0`/`arg1`/`arg2`** — up to 3 script arguments, passed through to `P_StartScript` with the
  bot's own player actor as the activator and no special flags (not `ACS_ALWAYS`, so a
  currently-running instance of the same script blocks a re-trigger the same way a normal in-map
  `ACS_Execute` special would).

## Related

- `ACS_ExecuteWithResult` — the same numbered-script bridge, but always targets the current map (no
  `map` argument), takes 4 script arguments instead of 3, runs with `ACS_ALWAYS|ACS_WANTRESULT`,
  and returns the script's result as an int.
- `ACS_NamedExecuteWithResult` — targets a *named* script instead of a numbered one (one string
  argument, resolved via `-FName(name)`), otherwise matches `ACS_ExecuteWithResult`'s
  always-current-map/4-args/`ACS_ALWAYS|ACS_WANTRESULT`/int-result shape.
