# Animated door family (`Door_Animated`/`Door_AnimatedClose`)

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes — file-level claim for `Door_Animated`;
`Door_AnimatedClose` is UZDoom-only (see its own section below)
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-29); Zandronum 3.3-alpha @bdd0f7beb (2026-09-29)
**Provenance:** written from the UZDoom source's `src/playsim/p_lnspec.cpp:290-303`
(`LS_Door_Animated`, `LS_Door_AnimatedClose`), `src/playsim/mapthinkers/a_doors.cpp:560-586`
(`DAnimatedDoor::StartClosing`) and `:762-848` (`FLevelLocals::EV_SlidingDoor`),
`src/gamedata/a_keys.cpp:466-472` (`P_CheckKeys`), `src/playsim/actionspecials.h:38`, `:288` and
`src/playsim/p_acs.cpp:7142-7155` (`PCD_LSPEC*` passes the script's `activationline`); the
Zandronum source's `src/p_lnspec.cpp:253-260`, `src/p_doors.cpp:1076-1139`,
`src/g_shared/a_keys.cpp:398-403`, `src/actionspecials.h:15` and `src/p_acs.cpp:9332-9347`; and
the zt-bcc source's `lib/zcommon.bcs:1374`, `:1613`. The door's own behavior (definitions, timing,
multiplayer) is from [`animdefs/concepts/animated-doors.md`](../../animdefs/concepts/animated-doors.md);
no wiki page was used.
**Bucket:** action special (`Door_Animated` index 14, `FUNC(LS_Door_Animated)`;
`Door_AnimatedClose` index 274, `FUNC(LS_Door_AnimatedClose)`, UZDoom only).

One file for both specials because they are thin wrappers around the same engine function,
`EV_SlidingDoor` (shared-implementation rationale): every finding about how a call picks its
sector and what it returns applies to both. What an `animateddoor` definition is, how a line
finds one, the frame timing and the Zandronum netcode are on
[`animdefs/concepts/animated-doors.md`](../../animdefs/concepts/animated-doors.md); this file covers
only what a script sees when it calls the specials.

## `int Door_Animated(int tag, int speed, int delay [, int lock])`

Starts a Strife-style sliding door in every sector with `tag` whose lines carry an
`animateddoor` texture, or closes one that is already open and waiting.

- `tag`: `0` means "the door behind the activating line": the script's activation line's back
  sector is the door. **A script with no activation line crashes on `tag` 0** (see below).
- `speed`: tics per frame step, minus 1. Raw tics, no `SPEED()`/`TICS()` scaling.
- `delay`: tics the door stays open, minus 1. `0` leaves it open for good.
- `lock`: optional LOCKDEFS lock number. Checked against the activator before anything else.
- **Return value:** `1` if at least one door started, else `0`. See "Return value traps" below.

### Crash: `tag` 0 with no activation line

An action special called from ACS receives the script's own activation line (`PCD_LSPEC*`
passes `activationline`, UZDoom `p_acs.cpp:7142-7155`, Zandronum `p_acs.cpp:9332-9347`). With
`tag` 0, `EV_SlidingDoor` reads `line->backsector` without checking the line (UZDoom
`a_doors.cpp:774`, Zandronum `p_doors.cpp:1088`). So `Door_Animated(0, ...)` from an `OPEN` or
`ENTER` script, a `puke`d script, or any script not started by a line is a null-pointer
dereference on both engines. A script started by a one-sided line has a line but no back sector,
and crashes one step later. Use a nonzero `tag` from scripts. Observed live for the no-line case
(2026-09-29, local test builds, probe map): `Door_Animated(0, 8, 70)` from an `OPEN` script crashed
both engines with SIGSEGV at exactly those lines. The one-sided-line case also crashes both
engines: a script set on a one-sided wall with `SetLineSpecial(..., ACS_ExecuteAlways, ...)`
and started by the player using that wall logged its first line, then died with SIGSEGV in
`LS_Door_Animated`, reading `ceilingdata` through the null back sector.

### `lock` with no activator

`P_CheckKeys` returns false for a null activator before looking at the lock (UZDoom
`a_keys.cpp:472`, Zandronum `a_keys.cpp:404`). So a nonzero `lock` from a script with no activator
(an `OPEN` script, for example) always fails: the door doesn't move and the call returns `0`. The
key check's "remote" message wording is picked by `tag != 0`.

### Return value traps

- **Closing a waiting door by tag returns `0` on UZDoom.** A tagged sector that already has an
  animated door waiting to close is told to close, but the loop never sets its return flag for
  that case (`a_doors.cpp:808-819`). The call returns `1` only if some other tagged sector started
  a new door. On Zandronum a tagged call skips busy sectors entirely (`p_doors.cpp:1118-1121`), so
  it neither closes the door nor returns `1` for it.
- **`tag` 0 on a busy sector** returns the result of the close attempt when the door is waiting
  (`0` if a thing is in the way or closing would crush it, `a_doors.cpp:560-572`), and `0` for any
  other ceiling mover. It needs a player activator: UZDoom returns `0` for a missing or non-player
  activator (`a_doors.cpp:779`); Zandronum returns `0` for a non-player activator but reads
  `actor->player` without a null check (`p_doors.cpp:1093`), so a null activator crashes there.
- **No definition, no door.** A sector whose lines have no `animateddoor` definition on their
  front upper texture is skipped, silently. A call where every sector is skipped returns `0` with
  no message.

## `int Door_AnimatedClose(int tag, int speed)` (UZDoom only)

Closes animated doors that are open and waiting. Never starts one.

- `tag`: same meaning as `Door_Animated`'s, including the `tag` 0 crash with no activation line
  and the player-activator requirement for `tag` 0.
- `speed`: ignored. The door closes at the speed it was opened with.
- **Return value:** with `tag` 0, the close attempt's result. **With a nonzero `tag` it is always
  `0`**, even when doors close: the tagged loop never sets its return flag for a close
  (`a_doors.cpp:808-822`). Don't use the result as a success check. Observed live: on a door
  opened with a long `delay`, `Door_AnimatedClose(tag, 8)` returned `0` and the door closed
  (ceiling 64 to 0).
- A sector with no active door is skipped (`a_doors.cpp:793`, `:822`), so a door that finished with
  `delay` 0 (no thinker left) can't be closed with this.

## Engine-family divergence: `Door_AnimatedClose` doesn't exist on Zandronum

Zandronum has no special 274: its `actionspecials.h` has no such row and there is no
`LS_Door_AnimatedClose`. It is worse than a no-op when compiled with zt-bcc: any special numbered
256 or higher is emitted as `PCD_LSPEC5EX`, which Zandronum reads as a different instruction, so
the call corrupts script execution. See
[`../functions/ceiling_movetovalue.md`](../functions/ceiling_movetovalue.md) for the mechanism,
which applies here unchanged. Don't call it on Zandronum. To close a waiting door there, re-run
`Door_Animated` with `tag` 0 from the door's own line (a tagged call won't close it, see above).

Other differences in how the two engines run a door (tagged re-triggering, the starting middle
texture, precaching) are listed in the concept page's
[Engine-family divergence](../../animdefs/concepts/animated-doors.md#engine-family-divergence).
