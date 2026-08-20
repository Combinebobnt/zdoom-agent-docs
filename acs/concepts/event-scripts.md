# EVENT scripts

**Tier:** B (wiki-sourced concept page; the load-bearing/version-sensitive claims were traced to source and to git history, but result-value ordering across multiple scripts, network-traffic performance claims, and the leave-reason enum values were not independently traced — see notes above for exactly which parts are untraced).
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-07-28)
**Provenance:** wiki page `EVENT scripts - Zandronum Wiki.html` (`_intake/`, retrieved 2026-07-28, `https://wiki.zandronum.com/w/index.php?title=EVENT_scripts&oldid=2562`) + verified against the Zandronum source (`gamemode.h`, `gamemode.cpp`, `gi.cpp`, `actor.h`, `p_acs.h`) and the zt-bcc source's `lib/zcommon.bcs`, including a git-ancestry check against the 3.2.1→3.3-alpha version-bump commits (2026-07-28).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.

Zandronum's own script type (`SCRIPT_Event = 16`, tagged `[BB]` in `p_acs.h` — not part of the
ZDoom script-type set, see [Script types](script-types.md)) for hooking game events:
`script "Name" (int type, int arg1, int arg2) EVENT { ... }`. `type` is a `GAMEEVENT_*` constant;
`arg1`/`arg2` meaning depends on which event fired.

## Version-gap warning (why this page needed extra care)

This entry targets Zandronum 3.2.1 (per `../../shared/AUTHORING.md`'s "Engine scope" — Zandronum
stays co-equal and fully verified even though UZDoom is the tree's primary engine), but the only
local checkout is a `master` HEAD that reports `3.3-alpha` in `version.h`. Two `GAMEEVENT_*`
events on the wiki page are recent enough that this gap actually matters here — resolved by
checking topological ancestry
in the Zandronum source's git history against the commit that set `version.h` to the `3.2.1`
release string (`28f736fb3`, immediately followed by the bump to `3.3-alpha` at `7279c8bc1`;
note the commit *dates* in this history are unreliable/synthetic — e.g. both bumps are dated
within days of each other in 2025 despite 3.2.1 being a much older real-world release — so
ancestry, not date, is what was checked):

- **`GAMEEVENT_DOMINATION_PRECONTROL` (18) and `GAMEEVENT_DOMINATION_CONTEST` (19)** — both
  commits (`110ba0f44`, `ce75d5a7d`) **are ancestors of** the 3.2.1 version-bump commit, i.e.
  both shipped in 3.2.1. Also present in `zt-bcc/lib/zcommon.bcs`'s `GAMEEVENT_e`-equivalent enum
  as real named BCS constants. Safe to use.
- **`GAMEEVENT_PLAYERJOINS` (20)** — the wiki page itself already flags this as "development
  version 3.3-alpha and above only," and that held up: its commit (`de253db6d`) is **not** an
  ancestor of the 3.2.1 bump. Confirmed real and wired into gameplay in the current checkout
  (`gamemode.cpp:1361`, `GAMEEVENT_e` in `gamemode.h:128`), but **not exposed as a named BCS
  constant in `zt-bcc/lib/zcommon.bcs`** — the compiler-side enum stops at
  `GAMEEVENT_DOMINATION_CONTEST`. Do not use `GAMEEVENT_PLAYERJOINS` when targeting Zandronum
  3.2.1: it is neither guaranteed present in that engine version, nor callable by name
  from this toolchain even if it were.

Every other `GAMEEVENT_*` value on the wiki page (0-17) is well below this gap and unaffected.

## Verified per-event details

- **`GAMEEVENT_CAPTURES` (2)** — confirmed the third event argument (`arg2`) really does carry
  the points-earned value: `team.cpp:500` calls
  `GAMEMODE_HandleEvent(GAMEEVENT_CAPTURES, player->mo, playerAssistNumber, numPoints)`. The
  wiki's "in Zandronum 3.1" qualifier is consistent with this being long-present, well before the
  3.2.1 target.
- **`GAMEEVENT_ACTOR_SPAWNED` / `_ACTOR_DAMAGED` / `_ACTOR_DAMAGED_PREMOD`** — confirmed
  disabled-by-default with the two enable paths the wiki describes: `GameInfo`'s
  `forcespawneventscripts`/`forcedamageeventscripts` keys (`gi.cpp:393-394`) and the per-actor
  `STFL_USESPAWNEVENTSCRIPT`/`STFL_USEDAMAGEEVENTSCRIPT` flags, with
  `STFL_NOSPAWNEVENTSCRIPT`/`STFL_NODAMAGEEVENTSCRIPT` as the opt-out (`actor.h:438-443`) —
  matches the wiki's Method A/B/opt-out description exactly, including the flag-name casing
  difference (GameInfo key is lowercase `forcespawneventscripts`, DECORATE flag is
  `USESPAWNEVENTSCRIPT`).
- **`AAPTR_DAMAGE_SOURCE`/`_INFLICTOR`/`_TARGET`** — confirmed present as real BCS constants
  (`zt-bcc/lib/zcommon.bcs:1276-1278`), usable with `SetActivator`/`SetPointer`/etc. as the wiki
  describes.
- **`GetEventResult`** — confirmed real, extension function `zcommon.bcs:1782` (`ACSF` index
  -152). `SetResultValue` is a separate, already-documented tier-C compiler builtin (see
  `INDEX.md`'s signature-only block).
- **Client-mode dispatch: stronger claim than the wiki states.** `GAMEMODE_HandleEvent()`
  (`gamemode.cpp:1245`) opens with `if (NETWORK_InClientMode()) return 1;` — i.e. the event
  dispatch function itself never even attempts to run `StaticStartTypedScripts(SCRIPT_Event,
  ...)` when called in client mode; only the server ever originates an `EVENT` script trigger.
  The wiki's narrower claim ("event handling does not work at all in CLIENTSIDE scripts," meaning
  specifically the `SetResultValue`-based result-override feature) is a special case of this: a
  `CLIENTSIDE`-flagged `EVENT` script still gets *triggered* by the server and relayed down via
  the same per-script clientside-execution replication path documented in
  [Client-side scripting](clientside-scripting.md), but the result-value round-trip described
  below never crosses back from a client since the client-side call into `GAMEMODE_HandleEvent`
  is the one that no-ops.
- **Result-value chaining ("last script fired decides the outcome")** — plausible from the
  `OverrideResult`/`lOldResult` save-restore logic around the `StaticStartTypedScripts` call in
  `GAMEMODE_HandleEvent`, which lets nested/re-entrant event calls each see and modify a shared
  result value, but the exact "scripts run in this order" claim was not traced through
  `StartTypedScripts`'s per-module iteration order to independently confirm — treat as
  plausible-but-untraced.

## Leave reasons (`GAMEEVENT_PLAYERLEAVESSERVER`'s `arg2`)

Not independently re-verified value-by-value in this pass (`LEAVEREASON_LEFT`/`_KICKED`/
`_ERROR`/`_TIMEOUT`/`_RECONNECT` = 0-4) — spot-checking every disconnect code path was out of
scope; flagged here as wiki-sourced, not fork-verified, in case a future session needs to trust
or distrust a specific `arg2` value.

## Engine-family divergence

The script-type enum value survives (`SCRIPT_Event = 16`, still carrying the `[BB]` tag) in
UZDoom's `src/playsim/p_acs.h`, inherited from shared codebase ancestry, but nothing behind it
does: there is no `gamemode.cpp`/`gamemode.h` file anywhere in the UZDoom source tree, no
`GAMEEVENT_*` constant of any kind, and no `HandleEvent`-style dispatch path. The declaration is
the *only* occurrence of `SCRIPT_Event` in the entire checkout — nothing ever calls
`StartTypedScripts`/`StaticStartTypedScripts` for that type. This is the same shape as the
`SCRIPTF_ClientSide`/`SCRIPTF_Ignored` divergence documented in
[Zandronum/UZDoom compatibility](zandronum-uzdoom-compat.md): a Zandronum-compiled `EVENT` script
loads cleanly under UZDoom, but silently never runs, since nothing ever triggers a script of that
type. The `AAPTR_DAMAGE_SOURCE`/`_INFLICTOR`/`_TARGET` pointers this mechanism exists to populate
(see [Actor pointer selectors](actor-pointers.md)) are correspondingly also absent from UZDoom: its
`AAPTR_` enum carries the shared ZDoom-lineage selectors (including an unrelated `AAPTR_TARGET`,
which is the actor's own target pointer, not a damage-event one) but has no `AAPTR_DAMAGE_SOURCE`,
`AAPTR_DAMAGE_INFLICTOR`, or `AAPTR_DAMAGE_TARGET` — those three are Zandronum additions.

**Correction (2026-08-15 re-verification pass), `GetEventResult` vs. `SetResultValue`:** an earlier
pass of this section said "`GetEventResult`/`SetResultValue` have nothing to read or write to on
that engine," which reads as though neither function works under UZDoom. Only the first half holds.
`GetEventResult` genuinely has no UZDoom counterpart — no extension function, no VM opcode, no
name of that form anywhere in the checkout. `SetResultValue` is a different case: it is a plain
ACS bytecode instruction (`PCD_SETRESULTVALUE`) that UZDoom implements and executes normally, and
is the ordinary way a script called as a line special reports success/failure — the engine's own
bundled `strifehelp.acs` uses it throughout. What is absent on UZDoom is specifically the *event*
result it would override in the Zandronum mechanism above; `SetResultValue` in any other context
behaves exactly as it does on any ZDoom-family engine.

**UZDoom's equivalent mechanism is not ACS at all.** Hooking game events on UZDoom is done through
the ZScript event-handler system (`StaticEventHandler`/`EventHandler`, native dispatch in
`src/events.cpp`, stdlib declarations in `wadsrc/static/zscript/events.zs`), not through a script
type — see [Event handlers](../../zscript/classes/eventhandler.md) for the full hook list. Several
`GAMEEVENT_*` events documented above have a close ZScript counterpart: `GAMEEVENT_ACTOR_SPAWNED`
maps onto `WorldThingSpawned`, `GAMEEVENT_ACTOR_DAMAGED`/`_PREMOD` onto `WorldThingDamaged`
(whose `WorldEvent` carries `Thing`/`Inflictor`/`DamageSource`/`Damage`/`DamageType` as fields,
which is how the missing `AAPTR_DAMAGE_*` pointers are replaced), `GAMEEVENT_PLAYERJOINS` onto
`PlayerEntered`, and `GAMEEVENT_PLAYERLEAVESSERVER` onto `PlayerDisconnected` (with no leave-reason
field — the `LEAVEREASON_*` distinction below has no UZDoom analogue). The correspondence is
functional, not structural: dispatch is per-registered-handler virtual calls in a configurable
order rather than one script type keyed on an event-ID argument, there is no
`forcespawneventscripts`-style global gate and no per-actor opt-in/opt-out flag (a registered
handler's `WorldThingSpawned` fires for every actor that survives its own spawn), and the
result-override contract is per-hook and short-circuiting rather than a shared result value — e.g.
`PlayerRespawning` defaults to returning `true`, and the dispatch loop in `src/events.cpp` aborts
and reports "no respawn" as soon as any one handler returns `false`.
