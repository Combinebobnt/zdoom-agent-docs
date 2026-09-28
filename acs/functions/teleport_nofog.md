# Teleport_NoFog

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-26); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki (Teleport_NoFog, https://zdoom.org/w/index.php?title=Teleport_NoFog&oldid=44998), verified against Zandronum source (p_teleport.cpp:378-395,411-419, p_lnspec.cpp:897-901, wadsrc/static/xlat/base.txt:212-215,273)
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

## Signature

```text
Teleport_NoFog(int tid, int useangle, int tag, int keepheight)
```

## Parameters

- `tid` — Thing ID of a TeleportDest or other valid destination actor. The teleport will pick a random destination from all actors with this TID, optionally restricted to a specific sector tag.

- `useangle` — Controls how the destination actor's angle (and the thing's velocity) are applied
  to the teleported thing. **UZDoom dispatches all four `useangle` values directly; Zandronum only
  distinguishes zero from non-zero, which still produces three distinct outcomes rather than two
  (see "Engine-family divergence" below).**
  - **0** (Hexen-compatible): On UZDoom, never changes the thing's angle or velocity, with or
    without an originating linedef. **On Zandronum this is only true with no originating
    linedef; with one, Zandronum's `useangle=0` instead rotates the thing's angle and velocity
    the same way UZDoom's mode 2 does** (see "Engine-family divergence").
  - **1**, and any value UZDoom doesn't recognize as 0/2/3 (Strife-compatible; also Zandronum's
    behavior for *any* non-zero value, with or without a line): Use the destination actor's angle,
    and zero the thing's velocity (including player bobbing velocity).
  - **2** / **3** (UZDoom-only "Boom-compatible" variants — 2 reproduces Boom's angle-direction
    bug, 3 corrects it): rotate the thing's angle and velocity to exit at the same angle relative
    to the *originating* linedef that it entered at, instead of simply substituting the
    destination's angle. **This only has an effect when the call carries an originating
    linedef** — true when the special itself sits on a line, or when an ACS script's own
    activation was triggered by a `Cross`/`Use`/`Push`/`Impact`-tagged special (see
    `acs/functions/lineside.md`'s `activationline` finding for the same no-line-context script
    types). Called from an `OPEN`/`ENTER`/`RESPAWN`/`DEATH` script, from the console, or via
    `ACS_Execute`/`ACS_ExecuteAlways`/`ACS_NamedExecute` — none of which carry an originating
    line — modes 2 and 3 silently fall back to mode-1 behavior on UZDoom. **Zandronum has no
    dispatch for 2 or 3 at all; see "Engine-family divergence" for the `useangle=0` path that
    reaches the same rotation there instead.**

- `tag` — Destination sector tag. If non-zero, teleport destinations are limited to TeleportDest actors in sectors with this tag. If `tid` is 0 and `tag` is non-zero, uses the first TeleportDest found in the first matching sector (old Doom behavior).

- `keepheight` — If set (non-zero), the teleported thing maintains its height relative to the floor of the destination sector. If 0, the thing lands on the floor (or maintains its z-offset if it's a missile or has `MF_NOGRAVITY`).

## Return

Returns `true` if teleport succeeds, `false` if:
- No destination actor with the matching `tid` (and optional sector `tag`) exists
- The destination actor exists but is NULL or invalid
- The thing being teleported has the `MF2_NOTELEPORT` flag set
- The teleport was triggered from the back side of a line. **This includes ACS calls:** a script
  started by `ACS_Execute`/`ACS_ExecuteAlways`/`ACS_ExecuteWithResult`/`ACS_LockedExecute` on a
  line activated from its back side remembers that side, and every action special the script calls
  (this one included, and any script it starts in turn) receives it, so `Teleport_NoFog` from that
  script also fails. Scripts started any other way (`OPEN`/`ENTER`, the console, a thing special,
  or a DECORATE `ACS_*` call) always carry the front side and are unaffected; the one exception is
  UZDoom's ZScript `Level.ExecuteSpecial`, whose caller passes the side explicitly
  (`src/playsim/p_lnspec.cpp:3981`). Same on both engines:
  `LS_ACS_Execute` turns the line side into `ACS_BACKSIDE` (UZDoom `src/playsim/p_lnspec.cpp:1905-1925`,
  Zandronum `src/p_lnspec.cpp:1753-1781`), the script constructor stores it as `backSide` (UZDoom
  `src/playsim/p_acs.cpp:10488`, Zandronum `src/p_acs.cpp:13094`), the `PCD_LSPEC*` cases pass it
  to `P_ExecuteSpecial` (UZDoom `:7141-7283`, Zandronum `:9333-9455`), and `EV_Teleport` returns
  early on any non-zero side (UZDoom `src/playsim/p_teleport.cpp:394`, Zandronum `src/p_teleport.cpp:364`).
- The destination position is blocked by geometry

## Behavior

Teleports the activating thing to a TeleportDest actor's location **without fog at either the source or destination** (the main difference from the fog-generating `Teleport` action special).

The thing's height in the destination is determined by:
- If `keepheight` is set: same height above the floor as at the origin
- If `keepheight` is 0 and the thing is a player: lands on the floor
- If `keepheight` is 0 and the thing is a missile: lands at the same height relative to floor as before

Velocity handling: mode **0** preserves the thing's velocity untouched on UZDoom regardless of line
context, and on Zandronum only when there's no originating linedef. Mode **1** (and, on UZDoom,
modes 2/3 when there's no originating linedef) zero both linear and bobbing velocity; this differs
from some wiki phrasings that suggest velocity is always preserved. **On UZDoom,** modes 2/3 *with*
an originating linedef instead rotate the thing's velocity to exit at the same relative angle it
entered at, rather than zeroing it (Lee Killough's Boom silent-teleporter behavior; UZDoom's
`EV_Teleport`, `src/playsim/p_teleport.cpp:403-421`). **Zandronum reaches the identical rotation
through mode 0 instead of a dedicated mode:** `useangle=0` with an originating linedef rotates
velocity the same way (Zandronum's `EV_Teleport`, `src/p_teleport.cpp:378-395,411-419`); Zandronum
has no dispatch that reaches this rotation from a non-zero `useangle`.

## Engine-family divergence: Zandronum folds Boom rotation into `useangle=0`, not a separate mode

Zandronum's `LS_Teleport_NoFog` (`src/p_lnspec.cpp:897-901`) reduces `useangle` to a plain C++
boolean: it calls `EV_Teleport(arg0, arg2, ln, backSide, it, false, false, !arg1, true, !!arg3)`,
passing `keepOrientation = !arg1` and an unconditional `haltVelocity = true`. Any non-zero
`useangle` (1, 2, 3, or anything else) produces byte-identical behavior (destination angle
applied, velocity zeroed); Zandronum's `EV_Teleport`/`P_Teleport` (`src/p_teleport.cpp`, HEAD is
unchanged in this area since `28f736fb3` bar an unrelated backtrace-fog revert) have no code path
that reads `arg1`/`useangle` for anything other than "is it zero." A map author using
`useangle=2` or `useangle=3` on Zandronum silently gets the same dispatch as `useangle=1`.

That "is it zero" flag does more than skip a destination-angle overwrite, though.
`EV_Teleport` (`src/p_teleport.cpp:378-395` and `:411-419`) gates its own Lee Killough Boom
silent-teleporter rotation on `keepOrientation && line` alone; there is no separate flag the way
UZDoom has `TELF_ROTATEBOOM`/`TELF_ROTATEBOOMINVERSE`. So on Zandronum, `useangle=0` called with an
originating linedef (the special placed directly on a line, or an ACS script triggered by
`Cross`/`Use`/`Push`/`Impact`) rotates the thing's angle and velocity to exit at the same angle
relative to the line it entered at, using the identical formula UZDoom uses for its non-inverted
mode 2 (`R_PointToAngle2(0, 0, line->dx, line->dy) - searcher->angle + ANG90`, no negation), even
though Zandronum has no `useangle` value that selects this rotation on its own. Only `useangle=0`
with **no** originating linedef truly leaves angle and velocity untouched on Zandronum; any
non-zero `useangle` always applies the destination angle and zeroes velocity, with or without a
line.

UZDoom's `LS_Teleport_NoFog` (`src/playsim/p_lnspec.cpp:1127-1155`) instead switches on all four
`useangle` values, setting `TELF_KEEPORIENTATION` alone for mode 0, and adding
`TELF_ROTATEBOOM`/`TELF_ROTATEBOOMINVERSE` only for modes 2/3, and only when `ln != NULL`
(both cases guard on it explicitly); without an originating linedef, cases 2 and 3 fall through
with no extra flags, identical to mode 1, and mode 0 never sets the rotation flags regardless of
line context. `EV_Teleport` (`src/playsim/p_teleport.cpp:404`) double-checks the same `line`
pointer (`(flags & (TELF_ROTATEBOOM|TELF_ROTATEBOOMINVERSE)) && line`) before applying the
rotation. So the two engines diverge specifically on `useangle=0` with an originating linedef:
UZDoom's mode 0 never rotates there, while Zandronum's `useangle=0` rotates exactly like UZDoom's
own mode 2 would. Away from that one case, the two engines agree: an ACS-invoked
`Teleport_NoFog(tid, 2, tag, keepheight)` with no originating line collapses to mode-1 (Strife)
behavior on both, and any non-zero `useangle` collapses to that same mode-1 behavior on Zandronum
regardless of line context.

This affects map conversions. Zandronum's own Boom-to-Hexen translation table
(`wadsrc/static/xlat/base.txt:212-215,273`) converts linedef types 207–210 and 268 (Teleport
Preserve Direction) to `Teleport_NoFog(0, 0, tag, 1)`, using `useangle=0`, not `2`. These specials
sit directly on the converted linedef, so `ln` is non-NULL when they fire, and Zandronum's own
`useangle=0`-with-line rotation (above) applies: the relative-angle adjustment is kept, not lost.
UZDoom's own translation table (also `wadsrc/static/xlat/base.txt:212-215,273`) converts the same
types to `Teleport_NoFog(0, 2, tag, 1)` instead, reaching the identical rotated result through its
dedicated mode 2. The two engines' own xlat conversions agree on outcome; they only diverge for a
hand-written ACS call that spells the rotation as `useangle=2` or `useangle=3` instead of relying
on either engine's xlat table: that spelling rotates on UZDoom (given a line) but silently
collapses to mode-1 behavior on Zandronum, which has no dispatch for those values at all.

## See also

- `Teleport` (action special 70) — identical except fog is generated at both source and destination
- `TeleportOther`, `TeleportGroup` (action specials, not extension functions) — teleport other actors or groups
