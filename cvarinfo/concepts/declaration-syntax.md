# CVARINFO declaration syntax

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki `CVARINFO` (retrieved via `extract_wiki_html.py`, oldid=54137) + verified against the Zandronum engine source's `src/d_main.cpp:1713–1850`.

CVARINFO is the lump format for declaring custom mod-specific console variables (CVARs). This file documents the declaration syntax and scopes as implemented in **Zandronum**; the ZDoom wiki page describes additional features (`nosave`, `cheat`, `latch`, `handlerclass`) that exist in ZDoom/GZDoom engines but not in Zandronum — see the "Engine-family divergence" section below.

## Syntax

```
<scope> [noarchive] <type> <name> [= defaultvalue];
```

## Scopes

A CVARINFO declaration requires exactly one scope, selecting where the CVAR's value lives and how it's synchronized:

- **`server`** — Shared across all players in a multiplayer game; only the server/host can modify it (sv_cheats exemption does not apply). Saved to save game files. Changes take effect immediately on the server, but clients don't see them until at least one tic later.

- **`user`** — Per-player CVAR, visible/modifiable by each player independently and replicated across the network to all other players. Not saved to save games, but persisted in the player's config file. Intended for player-specific cosmetic options (name, skin, color, gender, etc.) that all clients need to see — if its value affects gameplay, it will cause desync in multiplayer.

- **`local`** — Per-player CVAR, config-only, not replicated across network and not saved to save games. Each player's value is local to their own client. Intended for user-specific UI/cosmetic options that other players don't need to see. **Critical:** Nothing that can modify gameplay should be tied to a `local` CVAR, as it will cause desync (see the `user` scope note above). Introduced in Zandronum 3.2.1 (commit e64b31af47).

## Options

- **`noarchive`** — If present, prevents the CVAR from being written to the player's config file (it is still created and usable during the session, but not persisted to disk).

## Types

The CVAR's data type, required and one of:

- **`int`** — Integer value, defaults to `0`.
- **`float`** — Floating-point value, defaults to `0.0`.
- **`bool`** — Boolean value, defaults to `false`.
- **`string`** — Text string, defaults to `""` (empty string). User CVAR names and values combined cannot exceed 254 characters total; exceeding this will silently prevent the CVAR from loading on a future session (engine behavior in Zandronum 3.2.1+).
- **`color`** — RGB color value, defaults to `"00 00 00"` (black). Specified as three hex bytes separated by spaces.

## Naming

CVAR names must begin with a letter and may only contain alphanumeric characters (`a–z`, `A–Z`, `0–9`) and the underscore (`_`). Server CVAR names are limited to 63 characters; exceeding this in Zandronum is silently ignored (earlier ZDoom versions would load but exhibit issues in multiplayer).

## Default values

A default value is optional, signaled by an `=` after the CVAR name:

```
server int mymod_intensity = 10;
user string playername = "Player";
local bool ui_showdebug = false;
```

Type-checking is enforced at parse time: numeric types require a valid literal of that type, booleans require `true` or `false`, and other types accept any string.

## Duplicate CVAR handling

If a CVARINFO declares a CVAR name that already exists, Zandronum produces a hard parse error with an error message naming the conflicting CVAR and instructing the player to remove it from their config file. **Exception:** if the existing CVAR has flags `CVAR_ARCHIVE|CVAR_UNSETTABLE|CVAR_AUTO` (created by a raw `ConsoleCommand` call, marked as [AK]), Zandronum deletes it and allows the CVARINFO-declared CVAR to replace it. This deletion happens silently (Zandronum 3.2.1+, commit c9d8c2ee8, `[AK] Added a flag check...`).

## Engine-family divergence

The ZDoom wiki page this was verified against describes several features not present in Zandronum:

- **`nosave` scope** — Per-player, config-only, not replicated (similar to Zandronum's `local`, but designed for data "unique to each player but visible for other players"). Exists in ZDoom/GZDoom but not in Zandronum; use `local` in Zandronum instead.

- **`cheat` option** — Makes the CVAR modifiable from console only when `sv_cheats` is enabled. Does not exist in Zandronum; Zandronum allows console changes based on its own `sv_cheats` cvar but doesn't attach it to individual CVARs at declaration time.

- **`latch` option** — Changes take effect only when starting a new game (from console only; `SetCVar`/script changes apply immediately). Zandronum has a `CVAR_LATCH` flag in its cvar system (used for built-in engine cvars), but the CVARINFO parser does not expose it as a keyword.

- **`handlerclass` option** — Allows attaching a ZScript callback handler for CVAR-change events. Requires ZScript, which does not exist in Zandronum.

Also, the wiki describes "How to read in ZScript" semantics; these do not apply to Zandronum, which does not implement ZScript. In Zandronum, CVARs are only readable via ACS functions like `GetCVar`, `GetUserCVar`, `SetCVar`, etc. (see the `console/` section of this tree for details).

**Severity of using an unsupported keyword:** writing `nosave`, `cheat`, `latch`, or `handlerclass` in a Zandronum CVARINFO lump is not silently ignored — Zandronum's parser rejects the unrecognized token with a hard parse error (`sc.ScriptError("Unknown cvar attribute...")`, `src/d_main.cpp:1752-1755`) that aborts loading of the entire CVARINFO lump. A mod targeting both GZDoom and Zandronum must omit these keywords entirely from any CVARINFO lump Zandronum will load, not merely expect them to be no-ops.
