# Console variable (CVar) family

`GetCVar`, `SetCVar`, `GetCVarString`, `SetCVarString`, `GetUserCVar`, `SetUserCVar`,
`GetUserCVarString`, `SetUserCVarString` — eight wiki-documented functions that are actually
thin wrappers around four static engine helpers (`GetCVar`/`SetCVar`/`GetUserCVar`/`SetUserCVar`
in `p_acs.cpp`), each parameterized by an `is_string` bool. One family file instead of eight
per-function files because the redirect/permission/netcode behavior documented below is shared
across the int and string spelling of a given direction — reading, say, `GetCVarString`'s page in
isolation would miss the fork-specific caveats that only show up by reading `GetCVar`'s C++ too.

**Bucket:** `GetCVar` (int-returning form) is a compiler builtin (`PCD_GETCVAR`,
`zt-bcc/src/builtin.c:118`; `case PCD_GETCVAR:`, `p_acs.cpp:12502`). The other seven are extension
functions, indices -53 to -59 (`zcommon.bcs:1681-1687`): `SetCVar` -53, `GetUserCVar` -54,
`SetUserCVar` -55, `GetCVarString` -56, `SetCVarString` -57, `GetUserCVarString` -58,
`SetUserCVarString` -59 — dispatched as `ACSF_SetCVar`/`ACSF_GetUserCVar`/`ACSF_SetUserCVar`/
`ACSF_GetCVarString`/`ACSF_SetCVarString`/`ACSF_GetUserCVarString`/`ACSF_SetUserCVarString` in
`p_acs.cpp:6385-6432`.

**Tier:** A for all eight — wiki-derived and source-verified (2026-07-28).

**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md` for the version-gap caveat).

All eight are documented below regardless of real-world usage — see the family-coverage rule in
`../../shared/AUTHORING.md`'s Authoring rule section (a family's less-used members are exactly the ones nobody's
figured out yet).

## Shared implementation

All eight resolve to one of four static helpers (`p_acs.cpp:5655-5810`), parameterized by
`is_string`:

- `GetCVar(activator, name, is_string)` — backs `GetCVar` / `GetCVarString`.
- `SetCVar(activator, name, value, is_string)` — backs `SetCVar` / `SetCVarString`.
- `GetUserCVar(playernum, name, is_string)` — backs `GetUserCVar` / `GetUserCVarString`.
- `SetUserCVar(playernum, name, value, is_string)` — backs `SetUserCVar` / `SetUserCVarString`.

Picking the string-typed sibling doesn't change *which* cvar-lookup path runs — only how the raw
value is boxed (`UCVarValue`/`ECVarType`: `CVAR_String` vs. `CVAR_Int`/`CVAR_Float` in the shared
`DoGetCVar`/`DoSetCVar` helpers). Every redirect/permission/netcode behavior below applies
identically to the int and string form of a given direction.

---

## `int GetCVar(str cvar)` / `str GetCVarString(str cvar)`

Looks up `cvar` in the engine's global cvar list (`FindCVar`).

- Returns `0` if not found, or if the cvar belongs to an unloaded mod (`CVAR_IGNORE`ed).
- **⚠ `GetCVarString`'s "not found" return is not a safe empty string.** The wiki says both forms
  "return an empty string" (`GetCVar`'s page) or "return `0`" — but the string form's actual
  failure value is the **raw literal integer `0`**, not a string-pool handle for `""`. When later
  read back as a `str` (printed, concatenated, compared), `FBehavior::StaticLookupString(0)`
  resolves it as **string-table index 0 of the currently running behavior module**
  (`p_acs.cpp:3318-3330`) — whichever string literal the compiler happened to place first in that
  module's table, not necessarily `""`. Don't assume a failed `GetCVarString`/`GetUserCVarString`
  prints blank; use the int-typed `GetCVar`/`GetUserCVar` (or a known-cvar existence check) if you
  need a reliable empty-string sentinel.
- **Float cvars round-trip automatically**, not just "usable if int": if the found cvar's real
  type is `CVAR_Float`, the int form transparently converts to/from ACS fixed-point
  (`FIXED2FLOAT`/`FLOAT2FIXED` in `DoGetCVar`/`DoSetCVar`) — the wiki's "only useful for cvars
  that can be represented as integers" undersells this; a float-typed cvar reads/writes correctly
  through the int form, the string form isn't required for it.
- **Userinfo redirect:** if the resolved cvar has `CVAR_USERINFO`, `GetCVar`/`GetCVarString`
  silently redirect to `GetUserCVar`/`GetUserCVarString` for `activator`'s player index —
  confirms the wiki's "it will check the activator of the script." Zandronum-specific addition
  the wiki doesn't mention: with no activator (or an activator with no `player`), a `CLIENTSIDE`
  script running in client mode falls back to `consoleplayer`'s value instead of returning 0
  (`NETWORK_InClientMode()` check, `p_acs.cpp:5744-5747`); a server-side script with no activator
  still returns 0.

**Provenance:** wiki pages `GetCVar (ACS) - ZDoom Wiki.html` (2026-07-28), `GetCVarString (ACS) -
ZDoom Wiki.html` (2026-07-28) + source-verified against `p_acs.cpp:5729-5755` (`GetCVar` helper),
`:6385-6390` (`ACSF_GetCVarString`), `:12502-12504` (`PCD_GETCVAR`), `:3318-3330`
(`StaticLookupString`). **Tier:** A.

---

## `bool SetCVar(str cvar, int value)` / `bool SetCVarString(str cvar, str value)`

- Only cvars with the `CVAR_MOD` flag (mod-defined via `CVARINFO`, matching the wiki) can be set;
  also blocked by `CVAR_IGNORE` or `CVAR_NOSET`. Returns `0`/false for any of these, `1`/true on
  success — matches wiki.
- Userinfo redirect to `SetUserCVar` for `activator`'s player index, same flag check. Unlike the
  `Get` side, there's **no client-mode/consoleplayer fallback** — an activator with no `player`
  (no activator, or a client-mode script with none) just returns 0.
- **`SERVERINFO` cvars silently no-op for non-arbitrators:** the shared `DoSetCVar` helper both
  `SetCVar` and `SetUserCVar` funnel through checks `CVAR_SERVERINFO` and, if set, does nothing
  unless `consoleplayer == Net_Arbitrator` (`p_acs.cpp:5663-5666`) — a Zandronum
  multiplayer-authority rule with no ZDoom-wiki equivalent. The call still returns success (`1`)
  even when this silent no-op fires, since `DoSetCVar` is `void` and `SetCVar`/`SetUserCVar`
  return `1` unconditionally once the earlier permission checks pass.

**Provenance:** wiki pages `SetCVar (ACS) - ZDoom Wiki.html` (2026-07-28), `SetCVarString - ZDoom
Wiki.html` (2026-07-28) + source-verified against `p_acs.cpp:5791-5810` (`SetCVar` helper),
`:5655-5690` (`DoSetCVar`), `:6392-6404` (`ACSF_SetCVar`/`ACSF_SetCVarString`). **Tier:** A.

---

## `int GetUserCVar(int playernum, str cvar)` / `str GetUserCVarString(int playernum, str cvar)`

- Looks up `cvar` directly in `players[playernum].userinfo` — a **different data source** than
  `GetCVar`'s `FindCVar` (the global cvar list), not merely "the same lookup filtered to one
  player." A per-player userinfo entry can be read here in cases the global-cvar redirect path
  wouldn't reach.
- Returns `0` if `playernum` is out of range, that player isn't in game, the cvar isn't in their
  userinfo, or it's `CVAR_IGNORE`d — matches the wiki's combined failure list.
- Same "`0` is not a safe empty string" caveat as `GetCVarString` applies to
  `GetUserCVarString`'s failure return (same `DoGetCVar`/`StaticLookupString` path — see
  `GetCVar`'s section above).

**Provenance:** wiki pages `GetUserCVar - ZDoom Wiki.html` (2026-07-28), `GetUserCVarString (ACS)
- ZDoom Wiki.html` (2026-07-28) + source-verified against `p_acs.cpp:5714-5727` (`GetUserCVar`
helper), `:6406-6418` (`ACSF_GetUserCVar`/`ACSF_GetUserCVarString`). **Tier:** A.

---

## `bool SetUserCVar(int playernum, str cvar, int value)` / `bool SetUserCVarString(int playernum, str cvar, str value)`

- Requires `CVAR_MOD` like `SetCVar`, but **does not check `CVAR_NOSET`** — a real asymmetry with
  `SetCVar` in this fork's source (`p_acs.cpp:5766` vs. `:5795`), not documented on either wiki
  page.
- **Zandronum netcode-specific:** if `playernum == consoleplayer` (setting your own userinfo),
  the engine also immediately mirrors the change into the local global-cvar copy
  (`DoSetCVar(..., force=true)`) and, if running as a network client, queues the cvar name into
  `DACSThinker::ActiveThinker->userInfoChanges` so it gets replicated to the server later
  (`p_acs.cpp:5772-5786`). Setting *another* player's userinfo cvar from a server-side script
  skips this path entirely — it only updates the server's bookkeeping copy in
  `players[playernum].userinfo`, since that player's own client isn't the one calling.

**Provenance:** wiki pages `SetUserCVar (ACS) - ZDoom Wiki.html` (2026-07-28), `SetUserCVarString
(ACS) - ZDoom Wiki.html` (2026-07-28) + source-verified against `p_acs.cpp:5757-5789`
(`SetUserCVar` helper), `:6420-6432` (`ACSF_SetUserCVar`/`ACSF_SetUserCVarString`). **Tier:** A.
