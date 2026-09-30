# ANIMDEFS animated doors (`animateddoor`)

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/gamedata/textures/animations.cpp` (`InitAnimDefs`, `ParseAnimatedDoor`, `FindAnimatedDoor`, the `FDoorAnimation` serializer), `src/gamedata/textures/animations.h` (`FDoorAnimation`), `src/playsim/mapthinkers/a_doors.cpp` and `a_doors.h` (`DAnimatedDoor::Construct`, `Tick`, `StartClosing`, `FLevelLocals::EV_SlidingDoor`), `src/playsim/p_lnspec.cpp` (`LS_Door_Animated`, `LS_Door_AnimatedClose`), `src/playsim/actionspecials.h`, `src/gamedata/r_defs.h` (`side_t::part::InitFrom`), `src/sound/s_sndseq.cpp` (`SN_StartSequence`, `FindSequence`), `src/common/utility/cmdlib.cpp` (`IsNum`), `src/common/engine/sc_man.cpp` (`ScriptError`), `src/p_setup.cpp` (precache), `wadsrc/static/animdefs.txt`, `wadsrc/static/sndseq.txt` and `wadsrc/static/xlat/strife.txt`; and the Zandronum source's `src/textures/animations.cpp` (same parser functions), `src/p_doors.cpp` (`DAnimatedDoor`, `EV_SlidingDoor`, and every `SERVERCOMMANDS_*` call in them), `src/p_lnspec.cpp` (`LS_Door_Animated`), `src/actionspecials.h`, `src/p_spec.cpp` (`P_ActivateLine`), `src/gamemode.cpp` (`GAMEMODE_IsHandledSpecial`), `src/network.cpp` (`NETWORK_IsClientPredictedSpecial`), `src/sv_commands.cpp` (`SERVERCOMMANDS_SetLineTexture`), `src/cl_main.cpp` (the `SetLineTexture`, `SetSomeLineFlags`, `SetSectorCeilingPlane` and `StartSectorSequence` client handlers), `src/sv_main.cpp` (`SERVER_UpdateLines`, `SERVER_UpdateSectors`), `src/textures/texturemanager.cpp` (`GetTexture`), `src/dsectoreffect.cpp`, `src/sc_man.cpp` and `wadsrc/static/animdefs.txt`. Keyword names cross-checked against UltimateDoomBuilder's `Build/Scripting/ZDoom_ANIMDEFS.cfg` and `Build/Configurations/Includes/ZDoom_linedefs.cfg`, and SLADE's `z_animdefs` block in `dist/res/config/languages/zdoom.txt`.

An `animateddoor` block gives a door texture a list of frames and an open/close sound sequence.
The `Door_Animated` line special (and, on UZDoom only, `Door_AnimatedClose`) plays those frames
on the door's middle texture, Strife-style: the door sector's ceiling jumps open at once, the
lines stay blocking while the frames play, then become passable. This page covers the block's
keywords, how a line finds its definition, timing, and multiplayer. For the lump's outer grammar,
load order and the general error table, see [the lump page](animdefs-lump.md).

## Syntax

```text
animateddoor <base texture>
    opensound  <SNDSEQ sequence name>
    closesound <SNDSEQ sequence name>
    pic <texture | frame number>
    pic ...
    allowdecals
```

The block ends at the first word that isn't one of its four keywords, which is then read as the
next top-level keyword (UZDoom `animations.cpp:915-981`, Zandronum `animations.cpp:737-802`).
Keywords are case-insensitive, may come **in any order**, and may repeat. Neither engine has a game
filter for this block: the special works in any game.

| Keyword | Argument | Meaning | UZDoom | Zandronum |
|---|---|---|---|---|
| `animateddoor` | texture name | The door's base texture. Looked up as a wall texture first, then any namespace, honouring replacements (`TEXMAN_Overridable \| TEXMAN_TryAny`). Marks the base texture as refusing wall decals | yes | yes |
| `opensound` | one word | **SNDSEQ sequence name** (not an SNDINFO sound) started on the door sector's interior channel when the door opens. A repeat replaces the earlier one. Default: none | yes | yes |
| `closesound` | one word | SNDSEQ sequence started on the ceiling channel when the door starts closing. Default: none | yes | yes |
| `pic` | texture name or frame number | Appends one frame. See "Frames" below | yes | yes |
| `allowdecals` | none | Lets decals stick to the **base** texture again. The frame textures' own decal setting is not touched | yes | yes |

There is no duration keyword: frame timing comes from the line special's `speed` argument.

### Sounds are sound sequences

`opensound` and `closesound` are passed to `SN_StartSequence` by name, which searches the SNDSEQ
sequence list and does nothing if the name isn't found (UZDoom `s_sndseq.cpp:988-996` and
`FindSequence` at `:1028-1038`). So a plain SNDINFO logical sound name plays **nothing**, with no
warning. Define a `:MyDoorOpen` sequence in SNDSEQ and name that. The stock doors use
`DoorOpenStone`, `DoorOpenAirlock` and similar, which both engines' `sndseq.txt` define.

### Frames

- **A name** is looked up like the base texture. If the base texture exists and the frame doesn't,
  that is a fatal `Unknown texture <name>` (`ScriptError`, which calls `I_Error` in both engines:
  UZDoom `sc_man.cpp:1063-1087`, Zandronum `sc_man.cpp:888-905`).
- **A number** counts from the base texture in texture order: `pic 1` is the base itself, `pic 2`
  the next texture. It is **not range-checked**. Any word made only of digits and `-` counts as a
  number (`IsNum`), so a texture whose name is all digits can't be named in a `pic` line.
- **No minimum frame count is enforced.** A block with no `pic` line is accepted, but closing such
  a door then reads frame 0 of an empty list (undefined behaviour). Give at least one frame.
- **The first `pic` should be the base texture.** When the door starts, the engine shows the base
  texture itself (copied from the upper texture) and then steps through frames 2 to N. The first
  listed frame is only shown as the last step of closing, where it is the door's resting closed
  look. Every stock definition lists its base texture first for this reason.

### Base texture missing

If the base texture doesn't exist, the whole block is dropped **silently**: its keywords are still
consumed, `pic` names are not checked, and nothing is stored (UZDoom `animations.cpp:926-929` and
`:958`, the `!error` guard). Only a missing frame of an existing base is an error.

### Redefinition: first wins

`FindAnimatedDoor` scans the list from the start and returns the first definition whose base
texture matches (UZDoom `animations.cpp:989-1000`, Zandronum `animations.cpp:810-821`). Later
definitions for the same texture are stored but never found. The engine's `animdefs.txt` loads
first and defines seven Strife doors (`SIGLDR01`, `DORSTN01`, `DORQTR01`, `DORCRG01`, `DORCHN01`,
`DORIRS01`, `DORALN01`; the same seven in both engines), so **a mod can't redefine a stock door**.
Replacing the textures themselves still works, since the lookup is by texture, not by name. A mod
that needs different frames or sounds should use its own base texture.

## Which line uses which definition

The match is always on a line's **front side (`sidedef[0]`) upper texture**, never its middle or
lower texture.

- **Tag 0 (manual door).** The activating line's front upper texture picks the definition, and the
  line's **back sector** is the door (UZDoom `a_doors.cpp:774`, Zandronum `p_doors.cpp:1088`).
  Neither engine checks that the line exists or has a back sector, so tag 0 needs a two-sided
  activating line.
- **Tagged.** For each tagged sector, the first line in that sector's line list that has a back
  sector and whose front upper texture has a definition is used (UZDoom `a_doors.cpp:825-837`,
  Zandronum `p_doors.cpp:1123-1137`). A sector with no such line is skipped.
- **No definition.** If the upper texture has no `animateddoor` definition (or its block was
  dropped), `Door_Animated` does nothing and returns false. No message is printed.
- **The second face.** The door also animates one other line of the sector: the first one whose
  front upper texture is the same texture. If there is none, only the one line animates (UZDoom
  `a_doors.cpp:708-717`, Zandronum `p_doors.cpp:1000-1010`).

On both lines, the frames go on the **middle** texture of **both** sides. The upper texture is
never changed.

## What the door does

1. **Start.** The front middle texture of both lines is set from their upper texture (see
   "Engine-family divergence" for how this differs). The sector's ceiling rises **instantly** by
   the base texture's scaled height (64 if the texture can't be found), both lines are made
   blocking, and `opensound` starts.
2. **Opening.** One frame step every `speed + 1` tics. After the last frame, one more step makes
   both lines non-blocking.
3. **Waiting.** `delay + 1` tics. With `delay` 0 there is no wait and no closing: the door's
   thinker is removed and the door stays open for good.
4. **Closing.** If any thing is touching the sector, or lowering the ceiling would crush
   something, closing is refused and retried after another `delay + 1` tics. Otherwise both lines
   become blocking again, `closesound` starts, and the frames step back down, one every
   `speed + 1` tics, ending on the first `pic`. One more step drops the ceiling **instantly** to
   where it was. Lines that weren't blocking before the door started lose the blocking flag again.

The line special's arguments are raw tics on both engines: no `SPEED()`/`TICS()` conversion
(UZDoom `p_lnspec.cpp:290-303`, Zandronum `p_lnspec.cpp:253-260`).

| Special | Number | Arguments | UZDoom | Zandronum |
|---|---|---|---|---|
| `Door_Animated` | 14 | `tag`, `speed` (tics per frame minus 1), `delay` (tics), `lock` | yes | yes |
| `Door_AnimatedClose` | 274 | `tag`, `speed` (see below) | yes | no |

**Worked timing.** Strife's own doors use `Door_Animated(tag, 4, 105)` (`xlat/strife.txt:229`,
`:321`). With the stock eight-frame definitions that is 5 tics per frame step, 8 steps (40 tics)
until the door is passable, a 106-tic wait, then 9 steps (45 tics) to close. At 35 tics per second
that is roughly 1.1 s open, 3 s open-wait and 1.3 s close.

**Using the special on a door that's already moving.** A sector already busy with any ceiling
mover doesn't start a new door. If that mover is an animated door in its waiting phase, the
activation closes it early instead (a tag-0 activation only does this for a player; see the
divergence section for tagged activations). **A door that finished with `delay` 0 has no thinker
left**, so activating it again starts a new door on top: the ceiling rises by another texture
height and the frames play again.

**Bad arguments.** `speed` and `delay` aren't validated. A negative `speed` makes the frame timer
count down from below zero and effectively never reach its next step.

## Engine-family divergence

- **`Door_AnimatedClose` is UZDoom-only** (special 274, `actionspecials.h:288`). It only closes an
  animated door that is currently waiting, exactly like re-activating `Door_Animated` on it. On a
  sector with no active door it does nothing and returns false (`a_doors.cpp:793`, `:822`), so it
  can't close a door that finished with `delay` 0. Its `speed` argument is never used: the closing
  runs at the speed the door was opened with.
- **Re-triggering a waiting door by tag.** UZDoom closes it (`a_doors.cpp:808-819`). Zandronum
  skips any busy sector (`p_doors.cpp:1118-1121`), so a tagged `Door_Animated` never closes a door
  early there. Tag-0 re-use by a player closes a waiting door on both.
- **Tag-0 re-use with no activator.** UZDoom refuses when there is no activator or it isn't a
  player (`a_doors.cpp:779`). Zandronum only checks the activator's player field and doesn't guard
  against there being no activator at all (`p_doors.cpp:1093`).
- **Starting middle texture.** UZDoom copies the upper texture to the front middle only if the
  middle is empty, and copies the upper texture's offsets and scale onto a middle whose own are
  still at their defaults (`a_doors.cpp:721-725`, `r_defs.h:1244-1251`). So a door line that
  already has a front middle texture shows it until the first frame step. Zandronum always replaces
  the front middle texture with the upper one and copies no offsets or scale
  (`p_doors.cpp:1013-1015`).
- **Precaching.** UZDoom precaches every frame of an animated door whose base texture is in the
  level (`p_setup.cpp:136-143`). Zandronum has no such step, which can only cause a load hitch on
  the first frame.
- **Parser.** The `animateddoor` parsers match line for line: same keywords, same lookups, same
  errors.

## Zandronum-specific: which machine's copy is used

**The server runs the door; clients only display what it sends.** `DAnimatedDoor` has no dedicated
server command. Clients never run `Door_Animated` from a line: for a player activator,
`GAMEMODE_IsHandledSpecial` lets a client execute only `ThrustThing` and `ThrustThingZ`
(`gamemode.cpp:1137-1167`, `network.cpp:1616-1619`), and non-player activations are server-only.
So only the server looks up the `animateddoor` definition and runs the thinker. As the thinker
runs, the server sends generic updates (`p_doors.cpp`):

| Moment | Server sends | Client does |
|---|---|---|
| Start | `SetLineTexture` for both lines (`:1025-1026`), `SetSomeLineFlags` (`:1049-1050`), `StartSectorSequence` with the `opensound` name (`:1061`), `SetSectorCeilingPlane` (`:1066`) | Sets the middle textures, blocking flags and ceiling height, and plays the named sequence from its own SNDSEQ |
| Each frame step, opening or closing | `SetLineTexture` for both lines (`:908-909`, `:971-972`) | Sets the middle texture |
| Opening finished | `SetSomeLineFlags` (`:876-877`) | Clears blocking |
| Closing starts | `SetSomeLineFlags`, `SetSectorCeilingPlane` (`:821-825`), `StartSectorSequence` with the `closesound` name (`:834`) | Sets blocking flags and ceiling height, plays the sequence |
| Closing finished | `SetSectorCeilingPlane` (`:936`) | Drops the ceiling |

What this means for a client:

- **The client's own `animateddoor` definition is never consulted.** A client with a different
  ANIMDEFS (not checksummed on connect, per the lump page) still sees the server's frames and hears
  the server's sequence names.
- **The frame textures and the SNDSEQ sequences must exist on the client.** `SetLineTexture` sends
  a texture **name**, which the client looks up with `TexMan.GetTexture` (wall textures first,
  then any namespace; `cl_main.cpp:7084-7092`, `texturemanager.cpp:308-328`). A name the client
  doesn't have prints `Unknown texture: "<name>"` and the client shows the engine's `-NOFLAT-`
  placeholder instead of the frame. A sequence name the client doesn't have plays nothing.
- **Frame steps arrive at network rate.** Each step is a separate texture command, so the client
  sees the animation as packets arrive, not on its own clock.
- **Late joiners** get the current middle textures, blocking flags and ceiling height through
  `SERVER_UpdateLines` and `SERVER_UpdateSectors` (`sv_main.cpp:3682-3723`, `:3502-3503`), which
  resend any line whose textures or flags changed and any sector whose ceiling moved.
- **One gap.** When closing finishes, the server clears the blocking flag on lines that weren't
  blocking before, but sends no flag update (`p_doors.cpp:945-950`). Connected clients keep the
  lines blocking until something else resends their flags. The ceiling is down at that point, so
  this rarely shows.
- **Clientside ACS builds a client-only door.** Nothing in `LS_Door_Animated` or
  `EV_SlidingDoor` checks the network state, so a `CLIENTSIDE` script that calls `Door_Animated`
  builds a door on that client only, from the client's own ANIMDEFS, which the server knows
  nothing about. Observed live (2026-09-29, local test build, server + 2 clients, probe map): a
  `NET CLIENTSIDE` script puked by one client returned 1 and raised the tagged sector's ceiling
  to 64 on that client, while the other client and the server both still read 0. The same call
  from a server-side script opened the door everywhere.

The door thinker, its parser and the four server commands it uses (with their client handlers)
are unchanged since the Zandronum 3.2.1 version bump, so this holds on 3.2.1.

## Example

```text
// A four-frame sliding door. MYDOOR1 is the upper texture of the door's
// outer lines; MyDoorOpen and MyDoorClose are sequences in SNDSEQ.
animateddoor MYDOOR1
    opensound MyDoorOpen
    closesound MyDoorClose
    pic MYDOOR1
    pic MYDOOR2
    pic MYDOOR3
    pic MYDOOR4
```

Give the door sector's outer lines `MYDOOR1` as their front upper texture (the door sector on
their back side), and trigger it with, for example, `Door_Animated(0, 3, 140)`: 4 tics per frame,
about 4 seconds open.

## Editors

UltimateDoomBuilder's `ZDoom_ANIMDEFS.cfg` and SLADE's `z_animdefs` both list `animateddoor`,
`opensound`, `closesound`, `pic` and `allowdecals`. Neither says the sounds are SNDSEQ sequences.
UltimateDoomBuilder's `Door_Animated` argument 1 uses its `door_speeds` list (4, 16, 32, 64, 128),
built for map-unit speeds. Only 4 ("Animated") is a sensible value here, and the default of 16
gives 17 tics per frame. Its config has no `Door_AnimatedClose`.

## See also

- [The ANIMDEFS lump](animdefs-lump.md) for the outer grammar, load order and the general error
  table.
- [Switches](switches.md), the other ANIMDEFS block whose texture change the Zandronum server
  decides and sends.
- [Texture and flat animations](texture-flat-animations.md): a door frame can itself be an
  animated texture.
- [The animated door family](../../acs/families/animated-doors.md) for calling `Door_Animated`
  and `Door_AnimatedClose` from ACS (return values, the `tag` 0 crash with no activation line).
