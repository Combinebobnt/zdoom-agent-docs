# CVARINFO declaration syntax

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** ZDoom Wiki `CVARINFO` (retrieved via `extract_wiki_html.py`, https://zdoom.org/w/index.php?title=CVARINFO&oldid=54137) + verified against the Zandronum engine source's `src/d_main.cpp:1713–1850`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

CVARINFO is the lump format for declaring custom mod-specific console variables (CVARs). Both UZDoom and Zandronum parse it with their own hand-written `ParseCVarInfo` scanner in `d_main.cpp` (UZDoom: `src/d_main.cpp:1829–1984`; Zandronum: `src/d_main.cpp:1713–1850` — the two are separate, independently-maintained implementations, not shared code, though close in structure since Zandronum's traces to an older ZDoom baseline). This file documents the syntax and scopes common to both engines, noting divergences explicitly. The ZDoom wiki page describes additional features (`nosave`, `cheat`, `latch`, `handlerclass`) that this pass confirmed are implemented in UZDoom but do not exist in Zandronum — see "Engine-family divergence" below.

## Syntax

```text
<scope> [noarchive] <type> <name> [= defaultvalue];
```

## Scopes

A CVARINFO declaration requires exactly one scope, selecting where the CVAR's value lives and how it's synchronized:

- **`server`** — Shared across all players in a multiplayer game; only the server/host can modify it (sv_cheats exemption does not apply). Saved to save game files. Changes take effect immediately on the server, but clients don't see them until at least one tic later.

- **`user`** — Per-player CVAR, visible/modifiable by each player independently and replicated across the network to all other players. Not saved to save games, but persisted in the player's config file. Intended for player-specific cosmetic options (name, skin, color, gender, etc.) that all clients need to see — if its value affects gameplay, it will cause desync in multiplayer.

- **`local`** — Per-player CVAR, config-only, not replicated across network and not saved to save games. Each player's value is local to their own client. Intended for user-specific UI/cosmetic options that other players don't need to see. **Critical:** Nothing that can modify gameplay should be tied to a `local` CVAR, as it will cause desync (see the `user` scope note above). Introduced in Zandronum 3.2.1 (commit e64b31af47). **`local` is a Zandronum-only keyword** — UZDoom has no `local` scope; its nearest equivalent is the `nosave` scope (see "Engine-family divergence" below), which is not accepted by Zandronum's parser.

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

CVAR names must begin with a letter or underscore and may only contain alphanumeric characters (`a–z`, `A–Z`, `0–9`) and the underscore (`_`) — correcting this file's earlier "must begin with a letter" wording: both engines tokenize CVAR names with the same generic identifier rule as the rest of their script languages (a letter or underscore, followed by zero or more letters, digits, or underscores), so a leading underscore is accepted by both (confirmed: UZDoom `src/common/engine/sc_man_scanner.re:61,226`; Zandronum `src/sc_man_scanner.re:36,162`). Server CVAR names are limited to 63 characters; exceeding this in Zandronum is silently ignored (earlier ZDoom versions would load but exhibit issues in multiplayer).

## Default values

A default value is optional, signaled by an `=` after the CVAR name:

```text
server int mymod_intensity = 10;
user string playername = "Player";
local bool ui_showdebug = false;
```

Type-checking is enforced at parse time: numeric types require a valid literal of that type, booleans require `true` or `false`, and other types accept any string.

## Duplicate CVAR handling

If a CVARINFO declares a CVAR name that already exists, Zandronum produces a hard parse error with an error message naming the conflicting CVAR and instructing the player to remove it from their config file (`src/d_main.cpp:1793–1803`, re-confirmed this pass). **Exception:** if the existing CVAR has flags exactly `CVAR_ARCHIVE|CVAR_UNSETTABLE|CVAR_AUTO` (created by a raw `ConsoleCommand` call, marked as [AK]), Zandronum deletes it and allows the CVARINFO-declared CVAR to replace it. This deletion happens silently (Zandronum 3.2.1+, commit c9d8c2ee8, `[AK] Added a flag check...`).

## Engine-family divergence: Duplicate CVAR handling

UZDoom has no equivalent exception. Its `ParseCVarInfo` checks only whether a CVAR of that name already exists at all, and unconditionally raises a hard parse error naming the conflicting CVAR if so — there is no flag-based carve-out for a CVar auto-created by a raw console `set` command (confirmed: `src/d_main.cpp:1934–1937`). Concretely: a pre-existing `set`-created CVar (which UZDoom also flags `CVAR_AUTO`, see `src/common/console/c_cvars.cpp:1610`) that collides with a later CVARINFO declaration is a hard, unrecoverable load error on UZDoom, whereas the identically-shaped scenario is Zandronum's one documented silent-recovery case. A mod relying on Zandronum's [AK] exception (e.g. expecting a CVARINFO declaration to silently supersede a cvar the same mod created earlier via `ConsoleCommand("set ...")`) will fail to load on UZDoom instead.

The ZDoom wiki page describes several features this pass confirmed are genuinely implemented in UZDoom's `ParseCVarInfo` (`src/d_main.cpp:1850–1889`), all absent from Zandronum's:

- **`nosave` scope** — Per-player, config-only, not replicated (similar to Zandronum's `local`, but designed for data "unique to each player but visible for other players"). Confirmed in UZDoom: the `nosave` token sets `CVAR_CONFIG_ONLY` and forcibly clears any `server`/`user` flags already set on the same declaration, for backward-compat with a `server nosave`/`user nosave` spelling (`src/d_main.cpp:1872–1875,1891–1897`). Exists in UZDoom but not in Zandronum; use `local` in Zandronum instead.

- **`cheat` option** — Makes the CVAR modifiable from console only when `sv_cheats` is enabled. Confirmed in UZDoom: sets the `CVAR_CHEAT` flag (`src/d_main.cpp:1864–1867`). Does not exist in Zandronum; Zandronum allows console changes based on its own `sv_cheats` cvar but doesn't attach it to individual CVARs at declaration time.

- **`latch` option** — Changes take effect only when starting a new game (from console only; `SetCVar`/script changes apply immediately). Confirmed in UZDoom: sets the `CVAR_LATCH` flag (`src/d_main.cpp:1868–1871`). Zandronum has a `CVAR_LATCH` flag in its cvar system (used for built-in engine cvars), but the CVARINFO parser does not expose it as a keyword.

- **`handlerclass` option** — Allows attaching a ZScript callback handler for CVAR-change events. Confirmed in UZDoom: parsed as `handlerClass(<name>)` (`src/d_main.cpp:1876–1883`) and routed through `C_CreateZSCustomCVar` instead of the plain `C_CreateCVar` (`src/common/console/c_cvars.cpp:1481–1494`). Requires ZScript, which does not exist in Zandronum.

Also, the wiki describes "How to read in ZScript" semantics; these apply to UZDoom (which implements ZScript) but not to Zandronum, which does not implement ZScript at all. In Zandronum, CVARs are only readable via ACS functions like `GetCVar`, `GetUserCVar`, `SetCVar`, etc. (see the `console/` section of this tree for details).

**Severity of using an unsupported keyword:** writing `nosave`, `cheat`, `latch`, or `handlerclass` in a Zandronum CVARINFO lump is not silently ignored — Zandronum's parser rejects the unrecognized token with a hard parse error naming the bad attribute (`src/d_main.cpp:1752-1755`, re-confirmed this pass) that aborts loading of the entire CVARINFO lump. UZDoom's parser is symmetric here: any token it doesn't recognize as one of `server`/`user`/`noarchive`/`cheat`/`latch`/`nosave`/`handlerClass` likewise triggers a hard parse error that aborts the whole lump (`src/d_main.cpp:1884–1887`) — so a mod targeting both engines must omit whichever keywords the *other* engine doesn't support (Zandronum's `local` on UZDoom; UZDoom's `nosave`/`cheat`/`latch`/`handlerclass` on Zandronum) from any CVARINFO lump that engine will load, not merely expect them to be no-ops.
