# Console variable (CVar) family

**Tier:** A for all eight.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-06)
**Provenance:** ZDoom Wiki `GetCVar (ACS)` (https://zdoom.org/w/index.php?title=GetCVar_%28ACS%29&oldid=52409, retrieved 2026-08-06), `SetCVar (ACS)` (https://zdoom.org/w/index.php?title=SetCVar_%28ACS%29&oldid=45546, retrieved 2026-08-07), `GetCVarString (ACS)` (https://zdoom.org/w/index.php?title=GetCVarString_%28ACS%29&oldid=45557, retrieved 2026-08-06), `SetCVarString` (https://zdoom.org/w/index.php?title=SetCVarString&oldid=40915, retrieved 2026-08-07), `GetUserCVar` (https://zdoom.org/w/index.php?title=GetUserCVar&oldid=45562, retrieved 2026-08-07), `GetUserCVarString (ACS)` (https://zdoom.org/w/index.php?title=GetUserCVarString_%28ACS%29&oldid=45555, retrieved 2026-08-07), `SetUserCVar (ACS)` (https://zdoom.org/w/index.php?title=SetUserCVar_%28ACS%29&oldid=45548, retrieved 2026-08-07), `SetUserCVarString (ACS)` (https://zdoom.org/w/index.php?title=SetUserCVarString_%28ACS%29&oldid=45550, retrieved 2026-08-07). Wiki-derived and source-verified against the Zandronum source's `src/p_acs.cpp:5655-5810` (shared helpers) and `:6385-6432` (ACSF dispatchers), `:12502-12504` (PCD_GETCVAR), `:3318-3330` (StaticLookupString) — final source verification pass 2026-08-07.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `GetCVar` (int-returning form) is a compiler builtin (`PCD_GETCVAR`,
`zt-bcc/src/builtin.c:118`; `case PCD_GETCVAR:`, `p_acs.cpp:12502`). The other seven are extension
functions, indices -53 to -59 (`zcommon.bcs:1681-1687`): `SetCVar` -53, `GetUserCVar` -54,
`SetUserCVar` -55, `GetCVarString` -56, `SetCVarString` -57, `GetUserCVarString` -58,
`SetUserCVarString` -59 — dispatched as `ACSF_SetCVar`/`ACSF_GetUserCVar`/`ACSF_SetUserCVar`/
`ACSF_GetCVarString`/`ACSF_SetCVarString`/`ACSF_GetUserCVarString`/`ACSF_SetUserCVarString` in
`p_acs.cpp:6385-6432`.

`GetCVar`, `SetCVar`, `GetCVarString`, `SetCVarString`, `GetUserCVar`, `SetUserCVar`,
`GetUserCVarString`, `SetUserCVarString` — eight wiki-documented functions that are actually
thin wrappers around four static engine helpers (`GetCVar`/`SetCVar`/`GetUserCVar`/`SetUserCVar`
in `p_acs.cpp`), each parameterized by an `is_string` bool. One family file instead of eight
per-function files because the redirect/permission/netcode behavior documented below is shared
across the int and string spelling of a given direction — reading, say, `GetCVarString`'s page in
isolation would miss the fork-specific caveats that only show up by reading `GetCVar`'s C++ too.

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

## Warning: indeterminate features

**⚠ Reading non-playsim cvars can break demo and multiplayer sync.** Querying display/input cvars
like `screenblocks`, `invertmouse`, or other engine-configuration state with `GetCVar`/`GetCVarString`
is unsafe if the result is used to modify playsim (anything that uses the random number generator,
changes level geometry, spawns obstacles/monsters/powerups, etc.). This is documented on the wiki
pages; the caveat applies equally to Zandronum and ZDoom-family engines.

**Server/User cvars (defined via `CVARINFO`) are safe.** Reading `CVAR_USERINFO` and `CVAR_SERVERINFO`
flags with these functions doesn't risk desync — they're the intended use case for mod-scripted
playsim logic.

---

## `int GetCVar(str cvar)` / `str GetCVarString(str cvar)`

Looks up `cvar` in the engine's global cvar list (`FindCVar`).

- Returns `0` if not found, or if the cvar belongs to an unloaded mod (`CVAR_IGNORE`ed).
- **⚠ `GetCVarString`'s "not found" return is not a safe empty string.** The wiki says both forms
  "return an empty string" (`GetCVar`'s page) or "return `0`" — but the string form's actual
  failure value is the **raw literal integer `0`**, not a string-pool handle for `""`. When later
  read back as a `str` (printed, concatenated, compared), `FBehavior::StaticLookupString(0)`
  resolves it as **string-table index 0 of the first-loaded behavior module** (accessed via
  `StaticModules[0]`; `p_acs.cpp:3318-3330`) — whichever string literal that module's compiler
  happened to place first in its string table, not necessarily `""`. Don't assume a failed
  `GetCVarString`/`GetUserCVarString` prints blank; use the int-typed `GetCVar`/`GetUserCVar`
  (or a known-cvar existence check) if you need a reliable empty-string sentinel.
- **Float cvars round-trip automatically**, not just "usable if int": if the found cvar's real
  type is `CVAR_Float`, the int form transparently converts to/from ACS fixed-point
  (`FLOAT2FIXED` in `DoGetCVar`, `FIXED2FLOAT` in `DoSetCVar`) — the wiki's "only useful for cvars
  that can be represented as integers" undersells this; a float-typed cvar reads/writes correctly
  through the int form, the string form isn't required for it.
- **Userinfo redirect:** if the resolved cvar has `CVAR_USERINFO`, `GetCVar`/`GetCVarString`
  silently redirect to `GetUserCVar`/`GetUserCVarString` for `activator`'s player index —
  confirms the wiki's "it will check the activator of the script." Zandronum-specific addition
  the wiki doesn't mention: with no activator (or an activator with no `player`), a `CLIENTSIDE`
  script running in client mode falls back to `consoleplayer`'s value instead of returning 0
  (`NETWORK_InClientMode()` check, `p_acs.cpp:5744-5747`); a server-side script with no activator
  still returns 0.
  - **Trap for a script dispatched via `ExecuteClientScript`/`NamedExecuteClientScript`:** the
    activator on the receiving client is the *calling* script's own activator, replicated over the
    wire — not `NULL`, and not the target client's local player — so this redirect can silently read
    a *different player's* userinfo cvar than intended. See `functions/executeclientscript.md`'s
    activator-serialization bullet; the fix is `SetActivatorToPlayer(ConsolePlayerNumber())` before
    reading, or reading via the explicit `GetUserCVar(ConsolePlayerNumber(), ...)` form instead of
    plain `GetCVar`.

**Provenance:** ZDoom Wiki `GetCVar (ACS)` (https://zdoom.org/w/index.php?title=GetCVar_%28ACS%29&oldid=52409, retrieved 2026-08-06), ZDoom Wiki
`GetCVarString (ACS)` (https://zdoom.org/w/index.php?title=GetCVarString_%28ACS%29&oldid=45557, retrieved 2026-08-06) + source-verified against `p_acs.cpp:5729-5755`
(`GetCVar` helper), `:6385-6390` (`ACSF_GetCVarString`), `:12502-12504` (`PCD_GETCVAR`), `:3318-3330`
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

**Provenance:** ZDoom Wiki `SetCVar (ACS)` (https://zdoom.org/w/index.php?title=SetCVar_%28ACS%29&oldid=45546, retrieved 2026-08-07), `SetCVarString` (https://zdoom.org/w/index.php?title=SetCVarString&oldid=40915, retrieved 2026-08-07) — verified against `p_acs.cpp:5791-5810` (`SetCVar` helper), `:5655-5690` (`DoSetCVar`), `:6392-6404` (`ACSF_SetCVar`/`ACSF_SetCVarString`), `:5795` (`SetCVar`'s `CVAR_NOSET` check). **Tier:** A.

---

## `int GetUserCVar(int playernum, str cvar)` / `str GetUserCVarString(int playernum, str cvar)`

- Looks up `cvar` directly in `players[playernum].userinfo` — a **different data source** than
  `GetCVar`'s `FindCVar` (the global cvar list), not merely "the same lookup filtered to one
  player." A per-player userinfo entry can be read here in cases the global-cvar redirect path
  wouldn't reach.
- **Wiki/source drift:** The wiki pages state "playernumber: The number of the player (0 to 7)" but
  `MAXPLAYERS` is actually 64 in the Zandronum source (`doomdef.h:57`); valid range is 0-63.
- Returns `0` if `playernum` is out of range, that player isn't in game, the cvar isn't in their
  userinfo, or it's `CVAR_IGNORE`d — matches the wiki's combined failure list.
- **`GetUserCVarString` wiki divergence:** The wiki states "will return an empty string" on failure,
  but the source returns the literal integer `0`, not a string-pool handle for `""`. This is the same
  unsafe-empty-string caveat as `GetCVarString`; see that section above.
- Same "`0` is not a safe empty string" caveat as `GetCVarString` applies to
  `GetUserCVarString`'s failure return (same `DoGetCVar`/`StaticLookupString` path — see
  `GetCVar`'s section above).

**Provenance:** ZDoom Wiki `GetUserCVar` (https://zdoom.org/w/index.php?title=GetUserCVar&oldid=45562, retrieved 2026-08-07), `GetUserCVarString (ACS)` (https://zdoom.org/w/index.php?title=GetUserCVarString_%28ACS%29&oldid=45555, retrieved 2026-08-07; note: wiki page carries `(Verification needed)` marker) — verified against `p_acs.cpp:5714-5727` (`GetUserCVar` helper), `:6406-6418` (`ACSF_GetUserCVar`/`ACSF_GetUserCVarString`), `:57` (doomdef.h, `MAXPLAYERS`). **Tier:** A.

---

## `bool SetUserCVar(int playernum, str cvar, int value)` / `bool SetUserCVarString(int playernum, str cvar, str value)`

- Requires `CVAR_MOD` like `SetCVar`, but **does not check `CVAR_NOSET`** — a real asymmetry with
  `SetCVar` in Zandronum's source (`p_acs.cpp:5766` vs. `:5795`), not documented on either wiki
  page. The wiki pages' generic "or it is not writable" claim doesn't capture this Zandronum-specific
  difference.
- **Zandronum netcode-specific:** if `playernum == consoleplayer` (setting your own userinfo),
  the engine also immediately mirrors the change into the local global-cvar copy
  (`DoSetCVar(..., force=true)`) and, if running as a network client, queues the cvar name into
  `DACSThinker::ActiveThinker->userInfoChanges` so it gets replicated to the server later
  (`p_acs.cpp:5772-5786`). **Note: the `userInfoChanges` queueing feature postdates the 3.2.1
  version gate** (commit `3aec4d310`, `master` HEAD only) — if targeting strict 3.2.1 compatibility,
  verify this is available before relying on it. Setting *another* player's userinfo cvar from a
  server-side script skips this path entirely — it only updates the server's bookkeeping copy in
  `players[playernum].userinfo`, since that player's own client isn't the one calling.

**Provenance:** ZDoom Wiki `SetUserCVar (ACS)` (https://zdoom.org/w/index.php?title=SetUserCVar_%28ACS%29&oldid=45548, retrieved 2026-08-07), `SetUserCVarString (ACS)` (https://zdoom.org/w/index.php?title=SetUserCVarString_%28ACS%29&oldid=45550, retrieved 2026-08-07) — verified against `p_acs.cpp:5757-5789` (`SetUserCVar` helper), `:6420-6432` (`ACSF_SetUserCVar`/`ACSF_SetUserCVarString`), `:5766` (`SetUserCVar`'s `CVAR_NOSET` absence). **Tier:** A.

---

## Engine-family divergence: three "Zandronum-specific" labels are actually shared upstream behavior

Three caveats in the `SetCVar`/`SetUserCVar` sections above are worded as if unique to Zandronum;
reading UZDoom's cvar-setting code (`src/playsim/p_acs.cpp`) shows two are present unchanged and a
third is only half Zandronum-only:

- **`SetUserCVar`'s missing `CVAR_NOSET` check** (that section's first bullet): UZDoom's
  `DLevelScript::SetUserCVar` has the identical gap — it checks `CVAR_IGNORE`/`CVAR_MOD` but never
  `CVAR_NOSET`, the same asymmetry with `SetCVar` (which does check `CVAR_NOSET`, in
  `DLevelScript::SetCVar`) that the existing bullet describes as "in Zandronum's source." The
  asymmetry is shared upstream ZDoom-family behavior, not a Zandronum-only difference.
- **`SetCVar`'s `SERVERINFO`/arbitrator gate** (that section's third bullet): UZDoom's shared
  `DoSetCVar` helper contains the same early-return on `CVAR_SERVERINFO` when
  `consoleplayer != Net_Arbitrator`. The "no ZDoom-wiki equivalent" half of the existing claim
  still holds (the wiki genuinely doesn't document it), but "a Zandronum multiplayer-authority
  rule" overstates it — the rule itself is shared between the two forks, only the wiki gap is real.
- **`SetUserCVar`'s "Zandronum netcode-specific" bullet bundles two mechanisms, and only one is
  actually Zandronum-only**: UZDoom's `DLevelScript::SetUserCVar` also mirrors a self-targeted
  change into the local global-cvar copy via a forced `DoSetCVar` call when the target player is
  the console player — the same behavior the existing bullet's first half describes. What UZDoom
  genuinely lacks is the second half: there is no `userInfoChanges`-style queue or any other
  bookkeeping to replicate the change to a server later: UZDoom has no equivalent of that
  client-queues-then-server-replicates userinfo path.

The no-activator-falls-back-to-`consoleplayer` behavior on the `Get` side and the
`ExecuteClientScript` activator trap (both in the `GetCVar`/`GetCVarString` section above) remain
correctly scoped as Zandronum-specific: UZDoom's dispatcher passes `-1` for a player-less
activator, which fails the unsigned range check in `GetCVar`/`G_GetUserCVar` and returns `nullptr`
with no fallback, and UZDoom has no `ExecuteClientScript`/`NamedExecuteClientScript` functions at
all.
