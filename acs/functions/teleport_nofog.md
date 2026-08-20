# Teleport_NoFog

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** ZDoom Wiki (Teleport_NoFog, https://zdoom.org/w/index.php?title=Teleport_NoFog&oldid=44998), verified against Zandronum source (p_teleport.cpp, p_lnspec.cpp)
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

## Signature

```text
Teleport_NoFog(int tid, int useangle, int tag, int keepheight)
```

## Parameters

- `tid` — Thing ID of a TeleportDest or other valid destination actor. The teleport will pick a random destination from all actors with this TID, optionally restricted to a specific sector tag.

- `useangle` — Controls how the destination actor's angle (and the thing's velocity) are applied
  to the teleported thing. **UZDoom implements all four modes the wiki describes; Zandronum
  implements only a binary distinction — see "Engine-family divergence" below.**
  - **0** (Hexen-compatible): Do not change the thing's angle or velocity.
  - **1**, and any value UZDoom doesn't recognize as 0/2/3 (Strife-compatible; also Zandronum's
    behavior for *any* non-zero value): Use the destination actor's angle, and zero the thing's
    velocity (including player bobbing velocity).
  - **2** / **3** (UZDoom-only "Boom-compatible" variants — 2 reproduces Boom's angle-direction
    bug, 3 corrects it): rotate the thing's angle and velocity to exit at the same angle relative
    to the *originating* linedef that it entered at, instead of simply substituting the
    destination's angle. **This only has an effect when the call carries an originating
    linedef** — true when the special itself sits on a line, or when an ACS script's own
    activation was triggered by a `Cross`/`Use`/`Push`/`Impact`-tagged special (see
    `acs/functions/lineside.md`'s `activationline` finding for the same no-line-context script
    types). Called from an `OPEN`/`ENTER`/`RESPAWN`/`DEATH` script, from the console, or via
    `ACS_Execute`/`ACS_ExecuteAlways`/`ACS_NamedExecute` — none of which carry an originating
    line — modes 2 and 3 silently fall back to mode-1 behavior even on UZDoom.

- `tag` — Destination sector tag. If non-zero, teleport destinations are limited to TeleportDest actors in sectors with this tag. If `tid` is 0 and `tag` is non-zero, uses the first TeleportDest found in the first matching sector (old Doom behavior).

- `keepheight` — If set (non-zero), the teleported thing maintains its height relative to the floor of the destination sector. If 0, the thing lands on the floor (or maintains its z-offset if it's a missile or has `MF_NOGRAVITY`).

## Return

Returns `true` if teleport succeeds, `false` if:
- No destination actor with the matching `tid` (and optional sector `tag`) exists
- The destination actor exists but is NULL or invalid
- The thing being teleported has the `MF2_NOTELEPORT` flag set
- The teleport was triggered from the back side of a line (only relevant for linedef activation, not ACS calls)
- The destination position is blocked by geometry

## Behavior

Teleports the activating thing to a TeleportDest actor's location **without fog at either the source or destination** (the main difference from the fog-generating `Teleport` action special).

The thing's height in the destination is determined by:
- If `keepheight` is set: same height above the floor as at the origin
- If `keepheight` is 0 and the thing is a player: lands on the floor
- If `keepheight` is 0 and the thing is a missile: lands at the same height relative to floor as before

Velocity handling: mode **0** preserves the thing's velocity untouched. Mode **1** — and modes 2/3
when there's no originating linedef — zero both linear and bobbing velocity; this differs from
some wiki phrasings that suggest velocity is always preserved. **On UZDoom only,** modes 2/3 *with*
an originating linedef instead rotate the thing's velocity to exit at the same relative angle it
entered at, rather than zeroing it (Lee Killough's Boom silent-teleporter behavior — UZDoom's
`EV_Teleport`, `src/playsim/p_teleport.cpp:403-421`).

## Engine-family divergence: `useangle` modes 2/3 don't exist on Zandronum

Zandronum's `LS_Teleport_NoFog` (`src/p_lnspec.cpp:897-901`) reduces `useangle` to a plain C++
boolean: it calls `EV_Teleport(arg0, arg2, ln, backSide, it, false, false, !arg1, true, !!arg3)`,
passing `keepOrientation = !arg1` and an unconditional `haltVelocity = true`. Any non-zero
`useangle` — 1, 2, 3, or anything else — produces byte-identical behavior (destination angle
applied, velocity zeroed); Zandronum's `EV_Teleport`/`P_Teleport` (`src/p_teleport.cpp`, re-read
fresh this pass) have no code path that reads `arg1`/`useangle` for anything other than "is it
zero." A map author using `useangle=2` or `useangle=3` on Zandronum silently gets mode-1 (Strife)
behavior.

UZDoom's `LS_Teleport_NoFog` (`src/playsim/p_lnspec.cpp:1127-1155`) instead switches on all four
`useangle` values, setting `TELF_KEEPORIENTATION | TELF_ROTATEBOOM` for mode 2 and
`TELF_KEEPORIENTATION | TELF_ROTATEBOOMINVERSE` for mode 3 — **but only when `ln != NULL`** (both
cases guard on it explicitly); without an originating linedef, cases 2 and 3 fall through with no
flags set, identical to mode 1. `EV_Teleport` (`src/playsim/p_teleport.cpp:404`) double-checks the
same `line` pointer (`(flags & (TELF_ROTATEBOOM|TELF_ROTATEBOOMINVERSE)) && line`) before applying
the Boom-style relative-angle rotation. So even on UZDoom, an ACS-invoked
`Teleport_NoFog(tid, 2, tag, keepheight)` from an `OPEN`/`ENTER`/`RESPAWN`/`DEATH` script, from the
console, or via the `ACS_Execute` family collapses to mode-1 behavior exactly like Zandronum always
does — the two engines only diverge once the call chain actually has an originating linedef (a
`Cross`/`Use`/`Push`/`Impact`-triggered script, or the special placed directly on a line), where
UZDoom alone honors the distinct Boom-rotation behavior and Zandronum still just applies mode 1.

This affects map conversions: Boom linedef types 207–210 (Teleport Preserve Direction) are
documented as converting to `Teleport_NoFog(0, 2, tag, 1)`. On Zandronum this always behaves as
`Teleport_NoFog(0, 1, tag, 1)` — the relative-angle adjustment is lost. On UZDoom it depends on how
the conversion is realized: the original Boom special activates directly off the crossed linedef,
so a straight special-71-on-a-line conversion keeps `ln` non-NULL and gets the real Boom rotation;
only a conversion that instead routes through an ACS script with no line context would lose it.

## See also

- `Teleport` (action special 70) — identical except fog is generated at both source and destination
- `TeleportOther`, `TeleportGroup` (action specials, not extension functions) — teleport other actors or groups
