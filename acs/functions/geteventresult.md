# GetEventResult

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** wiki page `GetEventResult - Zandronum Wiki.html` (`_intake/`, retrieved 2026-07-29, `https://wiki.zandronum.com/w/index.php?title=GetEventResult&oldid=2283`) + verified against the Zandronum source (`p_acs.cpp`, `gamemode.h`, `gamemode.cpp`, `chat.cpp`, `sv_main.cpp`, `team.cpp`, `domination.cpp`, `medal.cpp`, `p_setup.cpp`) and the zt-bcc source's `lib/zcommon.bcs`, including a git-ancestry check of the `GetEventResult` and `GAMEEVENT_ACTOR_ARMORDAMAGED`→`GAMEEVENT_ACTOR_DAMAGED_PREMOD`-rename commits against the 3.2.1 version-bump commit `28f736fb3` (2026-07-29).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

```text
int GetEventResult(void);
```

Extension function, `zcommon.bcs:1782`, `ACSF` index **-152** (`ACSF_GetEventResult` in
`p_acs.cpp`). Implementation is a one-line passthrough: `case ACSF_GetEventResult: return
GAMEMODE_GetEventResult();` (`p_acs.cpp:7950-7953`), which just reads a single static global,
`g_lEventResult` (`gamemode.cpp:136`, default-initialized to `1`).

## What it actually returns

`g_lEventResult` is not scoped per event type — it's one shared global written and restored
around every `EVENT` script dispatch in `GAMEMODE_HandleEvent()` (`gamemode.cpp:1245-1269`):

```cpp
const LONG lOldResult = GAMEMODE_GetEventResult( );
GAMEMODE_SetEventResult( OverrideResult );      // OverrideResult defaults to 1
FBehavior::StaticStartTypedScripts( SCRIPT_Event, pActivator, true, Event, bRunNow, false, DataOne, DataTwo );
LONG lResult = GAMEMODE_GetEventResult( );
GAMEMODE_SetEventResult( lOldResult );          // restored as soon as StartTypedScripts returns
return lResult;
```

(The two trailing `//` notes are this doc's annotations, not engine comments.) Listener scripts only
run inside that `StaticStartTypedScripts` call when `bRunNow` is `true`: `StartTypedScripts`
(`p_acs.cpp:3412-3417`) otherwise just queues each script for a later tic.

So `GetEventResult()` called from inside an `EVENT` script simply reads whatever the shared
global currently holds at that moment. For an event dispatched with `bRunNow = true`, that is
the incoming `OverrideResult` if no script has touched it yet, or a value a previous
`SetResultValue()` call (this script's own, or an earlier-firing sibling `EVENT` script for the
same event) already wrote, per the chaining behavior described in
[EVENT scripts](../concepts/event-scripts.md). The old/new save-restore also means nested event
calls (an event triggered while another is already being handled) don't clobber the outer
result.

Events dispatched without `bRunNow` (`_PLAYERFRAGS`, `_CAPTURES`, `_TOUCHES`, `_RETURNS`,
`_ROUND_*`, `_PLAYERCONNECT`, `_PLAYERLEAVESSERVER`, `_JOINQUEUECHANGED`, `_DOMINATION_CONTROL`)
behave differently. Their scripts are only queued, and first run from the ACS thinker after
`GAMEMODE_HandleEvent()` has already returned and restored the old value, so they never see the
seed. A first-tic `SetResultValue()` in one
of them (`p_acs.cpp:10467-10468`) writes `g_lEventResult` with no save/restore around it, so the
value sticks: later `GetEventResult()` calls outside any immediate dispatch read it back until
another first-tic `SetResultValue()` changes it. Nothing else resets the global. This logic is
unchanged since 3.2.1 (`28f736fb3`).

**`OverrideResult` (the value seeded before scripts run) is `1` by default for every event type
except the two damage events.** Checked every `GAMEMODE_HandleEvent(...)` call site in
the Zandronum source's `src`: `GAMEEVENT_ACTOR_DAMAGED`/`GAMEEVENT_ACTOR_DAMAGED_PREMOD`
(`gamemode.cpp:1340`) are the only ones that pass a non-default `OverrideResult` — the incoming
`damage` amount. Every other call site (`GAMEEVENT_CHAT` in `chat.cpp:1155` and `sv_main.cpp:1291`,
`GAMEEVENT_PLAYERFRAGS`, `_MEDALS`, `_CAPTURES`, `_TOUCHES`, `_RETURNS`, `_ROUND_*`,
`_PLAYERCONNECT`, `_ACTOR_SPAWNED`, `_DOMINATION_*`, `_PLAYERLEAVESSERVER`, `_LEVEL_INIT`,
`_JOINQUEUECHANGED`, `_PLAYERJOINS`) omits the argument and gets the `= 1` default
(`gamemode.h:245`). Of that list, `GAMEEVENT_PLAYERJOINS` (`GAMEMODE_HandlePlayerJoinsEvent`,
`gamemode.cpp:1352-1365`) postdates the 3.2.1 target: its introducing commit `de253db6d` is not
an ancestor of the 3.2.1 version-bump commit `28f736fb3`, so it does not exist in a real 3.2.1
client. See [EVENT scripts](../concepts/event-scripts.md)'s version-gap section for the full
ancestry check; every other event in the list above predates 3.2.1.

## Wiki/engine divergence: event-type compatibility claim

The wiki's "Usage" section frames this as a hard compatibility restriction: *"This is only
compatible with the following event types: `GAMEEVENT_CHAT`, `GAMEEVENT_ACTOR_DAMAGED`, and
`GAMEEVENT_ACTOR_ARMORDAMAGED`... If used in a non-EVENT script or when the event type isn't any
of the ones listed above, this will always return 1."*

That's an oversimplification, verified against the source above:

- **There is no per-event-type gate in the code at all.** `GetEventResult()` is a plain global
  read; it works identically regardless of which `GAMEEVENT_*` fired. The "always return 1" claim
  only holds if nothing in the current event's script chain has called `SetResultValue()` yet —
  it is the *initial* value for most event types, not an enforced ceiling. A script that calls
  `SetResultValue(5)` and then `GetEventResult()` in a `GAMEEVENT_PLAYERFRAGS` handler will read
  back `5`, not `1`, even though `PLAYERFRAGS` isn't one of the wiki's three "compatible" types.
- What actually matters is **whether the event's caller reads the returned value back and acts
  on it**, and `GAMEEVENT_CHAT` and the two damage events are not the only ones that do. The
  consumers at this checkout:
  - `GAMEEVENT_CHAT`: `chat.cpp:1155`/`sv_main.cpp:1291` drop the chat message if the result is `0`.
  - `GAMEEVENT_ACTOR_DAMAGED`/`_PREMOD`: `gamemode.cpp:1340` replaces the applied damage with the
    result.
  - `GAMEEVENT_MEDALS`: `medal.cpp:431` withholds the medal if the result is `0`.
  - `GAMEEVENT_DOMINATION_CONTEST`: when the game info enables contest scripts, `domination.cpp:141`
    counts the player as contesting the point only if the result is nonzero. Otherwise the event
    doesn't fire and every on-team player counts.
  - `GAMEEVENT_DOMINATION_PRECONTROL`: `domination.cpp:181` denies the capture if the result is `0`.
  - `GAMEEVENT_DOMINATION_POINT`: `domination.cpp:199` awards the result (clamped to at least `0`)
    as the team's points.
  - `GAMEEVENT_PLAYERJOINS` (3.3-alpha only, see below): `gamemode.cpp:1361` refuses the join if
    the result is `0`.

  All of these dispatch with `bRunNow = true`. The deferred events listed above can't be consumed
  (their scripts haven't run yet when `GAMEMODE_HandleEvent()` returns), and the two remaining
  immediate ones, `GAMEEVENT_ACTOR_SPAWNED` (`gamemode.cpp:1309`) and `GAMEEVENT_LEVEL_INIT`
  (`p_setup.cpp:4422`), discard the result. For those, `GetEventResult()`/`SetResultValue()` still
  *work*, they're just inert from the engine's point of view. The wiki conflates "the engine
  doesn't consume this event's outcome" with "the function returns a hardcoded 1," which isn't
  what the code does. The medal and domination consumers were already present at 3.2.1
  (`28f736fb3`).
- **Naming divergence, not just a wiki inaccuracy:** the wiki's third "compatible" type,
  `GAMEEVENT_ACTOR_ARMORDAMAGED`, does not exist under that name anywhere in Zandronum's
  toolchain. It was renamed to `GAMEEVENT_ACTOR_DAMAGED_PREMOD` in
  the Zandronum source commit `b9b31b7c1` ("Rename GAMEEVENT_ACTOR_ARMORDAMAGED to
  GAMEEVENT_ACTOR_DAMAGED_PREMOD to more descriptively match its behaviour", 2024-04-05) — see
  the "Version check" section below for why this rename predates the 3.2.1 target.
  `zt-bcc/lib/zcommon.bcs:1204` only defines `GAMEEVENT_ACTOR_DAMAGED_PREMOD`; there is no
  `GAMEEVENT_ACTOR_ARMORDAMAGED` BCS constant to reference even if you wanted to match the wiki
  literally.

## Version check (3.2.1 vs. this checkout's 3.3-alpha)

Per `../../shared/AUTHORING.md`'s engine-scope note and `../concepts/event-scripts.md`'s version-gap section, this
project targets Zandronum 3.2.1 but the Zandronum source's checkout is a `master` HEAD
reporting `3.3-alpha`. Checked git ancestry against the 3.2.1 version-bump commit `28f736fb3`
("changed the version string to 3.2.1", committed 2025-08-04 in this repo's commit-graph time —
per `event-scripts.md`, commit *dates* in this history are synthetic/unreliable, so ancestry was
used, not dates):

- `ACSF_GetEventResult` was added in commit `7d6c2b49b` ("Added ACS function: GetEventResult",
  2022-02-13) — **confirmed an ancestor of `28f736fb3`**, i.e. `GetEventResult()` shipped in
  3.2.1. Safe to use.
- `GAMEEVENT_ACTOR_ARMORDAMAGED` was added in commit `e78e7875b` (2021-11-28) and renamed to
  `GAMEEVENT_ACTOR_DAMAGED_PREMOD` in commit `b9b31b7c1` (2024-04-05) — **both confirmed ancestors
  of `28f736fb3`**, i.e. the rename had already happened by the 3.2.1 release. A 3.2.1 client has
  never had a constant literally named `GAMEEVENT_ACTOR_ARMORDAMAGED`; use
  `GAMEEVENT_ACTOR_DAMAGED_PREMOD`.

## Practical notes

- Calling this outside an `EVENT` script just returns whatever `g_lEventResult` happens to
  hold. That is `1` at startup and is restored to the pre-event value after each
  `GAMEMODE_HandleEvent()` call, but a first-tic `SetResultValue()` in a deferred event's script
  leaves its value behind (see above). Inside an immediate dispatch, before any `SetResultValue`
  call, it returns the seed: `1`, or the incoming damage for the two damage events. It is not an
  error to call it elsewhere; there's no non-`EVENT`-script guard in the implementation.
- Pairs with `SetResultValue()` — see `functions/setresultvalue.md`'s note that
  Zandronum's `EVENT` scripts route `SetResultValue()` into this same
  `GAMEMODE_SetEventResult()` global, but only during the script's first tic.
- See [EVENT scripts](../concepts/event-scripts.md) for the full event-type list, the
  result-value chaining behavior across multiple listener scripts, and the client-mode dispatch
  short-circuit. On a server, a `CLIENTSIDE`-flagged `EVENT` script is forwarded to clients and
  never runs there (`p_acs.cpp:3404-3410`), so it can't affect the server's result. On a client,
  `GAMEMODE_HandleEvent` returns `1` without starting any script (`gamemode.cpp:1247-1249`), so
  `GetEventResult()` in such a script never sees a server-originated override.

## Engine-family divergence

`GetEventResult` is bound as ACSF (CALLFUNC) index **152**, inside the 100–199 range UZDoom
reserves for Zandronum's own extensions and implements none of (see
[Zandronum/UZDoom compatibility](../concepts/zandronum-uzdoom-compat.md)). A Zandronum-compiled
object calling it under UZDoom hits the dispatcher's `default: break;` case and gets back `0` —
no error, no log line, script execution continues normally.

That `0` is not a harmless placeholder here. On Zandronum, `g_lEventResult` starts each dispatch
seeded at `1` for every event type except the two damage events (seeded at the incoming damage
amount instead), so a script that never called `SetResultValue()` normally reads back `1`, not `0` — and
`0` is itself a meaningful in-band value the consuming engine code acts on (blocks the chat
message for `GAMEEVENT_CHAT`, zeroes the applied damage for the damage events). Under UZDoom,
`GetEventResult()` always returns `0` regardless of whether any `SetResultValue()` call happened,
which is indistinguishable from a script having deliberately blocked the chat message or zeroed
the damage — there is no way for a caller to tell "no result was ever set" apart from "the result
was explicitly set to the block/zero value." See [EVENT scripts](../concepts/event-scripts.md) for
the full `SetResultValue`/result-chaining mechanism this reads back from on Zandronum.
