# ANIMDEFS switches

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/gamedata/textures/anim_switches.cpp` (`InitSwitchList`, `ProcessSwitchDef`, `ParseSwitchDef`, `AddSwitchPair`, `FindSwitch`), `src/gamedata/textures/animations.h` (`FSwitchDef`, `FTextureAnimator::Init`), `src/playsim/p_switch.cpp` (`P_StartButton`, `P_ChangeSwitchTexture`, `DActiveButton::Tick`, `DActiveButton::AdvanceFrame`), `src/playsim/p_spec.cpp` and `p_spec.h` (`P_ActivateLine`, `BUTTONTIME`), `src/playsim/p_lnspec.cpp` (`LS_GlassBreak`), `src/common/engine/sc_man.cpp` (`GetNumber`, `ScriptError`), `src/common/engine/m_random.h` and `wadsrc/static/animdefs.txt`; and the Zandronum source's `src/textures/anim_switches.cpp` (same functions), `src/textures/textures.h` (`FSwitchDef`), `src/p_switch.cpp` (same functions plus the `SERVERCOMMANDS_SetLineTexture`/`SERVERCOMMANDS_SoundPoint` calls), `src/p_spec.cpp` and `p_spec.h` (`P_ActivateLine`, `BUTTONTIME`), `src/p_lnspec.cpp` (`LS_GlassBreak`), `src/sv_commands.cpp` (`SERVERCOMMANDS_SetLineTexture`), `src/cl_main.cpp` (`ServerCommands::SetLineTexture::Execute`), `src/gamemode.cpp` (`GAMEMODE_IsHandledSpecial`), `src/network.cpp` (`NETWORK_IsClientPredictedSpecial`), `src/sc_man.cpp`, `src/m_random.h` and `wadsrc/static/animdefs.txt`. Keyword list cross-checked against UltimateDoomBuilder's `Build/Scripting/ZDoom_ANIMDEFS.cfg` and SLADE's `z_animdefs` block in `dist/res/config/languages/zdoom.txt`.

A `switch` block names a wall texture that works as a switch, and the frames it shows when used
(`on`) and when it resets (`off`). This page covers the block's keywords, frame timing, how the
animation plays at runtime, and how the Boom binary `SWITCHES` lump fits in. For the outer grammar
(no braces, a block ends at the first word it doesn't know), load order and the lump-wide error
table, see the lump page, [The ANIMDEFS lump](animdefs-lump.md).

The ANIMDEFS `switch` parser is line-for-line the same on both engines. The differences are at
runtime, plus one detail of the `SWITCHES` reader; see "Engine-family divergence".

## Grammar

```text
switch [doom [<n>] | heretic | hexen | strife | any] <base texture>
    [quest]
    on  [sound <sound>] pic <texture> <duration> [pic <texture> <duration> ...]
    off [sound <sound>] pic <texture> <duration> [pic <texture> <duration> ...]

    <duration> is: tics <n> | rand <min> <max>
```

`quest`, `on` and `off` may come in any order after the base texture, and `quest` may repeat.
Inside a state, `sound` and the `pic` lines may interleave (the sound can come after a `pic`).
The block ends at the first word that isn't `quest`/`on`/`off` (UZDoom
`anim_switches.cpp:142-169`, Zandronum `anim_switches.cpp:154-181`), and a state ends at the first
word that isn't `sound`/`pic` (UZDoom `:225-281`, Zandronum `:237-293`).

## Keywords

The UZDoom and Zandronum columns are identical because the parsers are.

| Keyword | Arguments | Meaning | UZDoom | Zandronum |
|---|---|---|---|---|
| `doom` | optional integer | Only load on Doom **and Chex** (`GAME_DoomChex`). The number (a vanilla game-mission filter in the stock file: `doom 1`/`2`/`3`) is read and thrown away | yes | yes |
| `heretic`, `hexen`, `strife` | none | Only load on that game. No number is accepted after these | yes | yes |
| `any` | none | Load on every game. Same as giving no game word | yes | yes |
| (no game word) | | Treated as `any`; the word is read as the base texture instead | yes | yes |
| `quest` | none | Marks a Strife quest panel. Only `GlassBreak` reads it (see "`quest`") | yes | yes |
| `on` | a state | Frames shown when the switch is used. Required: without a usable `on` state the switch is dropped | yes | yes |
| `off` | a state | Frames shown when a repeatable switch resets. Optional (see "Omitting `off`") | yes | yes |
| `sound` | sound name | Sound for this state. Resolved at parse time against SNDINFO (already loaded). An unknown name silently means "no sound", so the default is used | yes | yes |
| `pic` | texture, duration | One frame. Any texture namespace is accepted (wall first). Unlike `texture`/`flat` blocks, a number is not a frame index here: it's looked up as a texture name | yes | yes |
| `tics` | integer | Frame duration in **game tics** (35 per second) | yes | yes |
| `rand` | integer, integer | Random duration, `min` to `max` tics inclusive. Reversed bounds are swapped | yes | yes |

There is no `chex` game word; `doom` covers Chex. Neither editor config lists `quest` or `any`.
UltimateDoomBuilder and SLADE both list `doom`, `heretic`, `hexen`, `strife`, `on`, `off`,
`sound`, `pic`, `tics` and `rand`.

An invented example (all names are the mod's own):

```text
// Three-frame lever, repeatable, with its own reset animation and sounds
switch MYLEVR1
    on  sound mymod/leverdown
        pic MYLEVR2 tics 3
        pic MYLEVR3 tics 0          // last frame: duration is never read
    off sound mymod/leverup
        pic MYLEVR2 tics 3
        pic MYLEVR1 tics 0

// Doom and Chex only, single frame, default sounds
switch doom MYSWOFF on pic MYSWON tics 0
```

## Timing

Switch frame times are whole **game tics**. They run on the playsim's thinker clock, so they stop
while the game is paused (unlike texture animations, which run on the render clock in
milliseconds; see the lump page's "Timing").

- **Integers only.** `tics` and `rand` read a plain integer (`MustGetNumber`), so `tics 2.5` is a
  fatal `SC_GetNumber: Bad numeric constant "2.5"` (UZDoom `sc_man.cpp:634-664`, Zandronum
  `sc_man.cpp:590-606`). Texture animation frames do take fractions.
- **Values are masked to 16 bits** (`& 65535`), so `tics -1` becomes 65535 (UZDoom
  `anim_switches.cpp:250`, Zandronum `:262`). Numbers are parsed C-style (base 0), so `0x10` is
  16 and a leading zero means octal (`010` is 8). UZDoom's scanner can turn octal off, but nothing
  does so for ANIMDEFS (UZDoom `sc_man.cpp:296-301`, Zandronum `sc_man.cpp:603`).
- **`rand <min> <max>`** picks `min` plus a random 0 to `max - min`, so `min` to `max` inclusive
  (UZDoom `anim_switches.cpp:253-266` with `p_switch.cpp:445-449`; Zandronum
  `anim_switches.cpp:265-278` with `p_switch.cpp:439-443`).

### The last frame's duration is never used

When the button thinker reaches the **last** frame of a state, it doesn't read that frame's time at
all (UZDoom `p_switch.cpp:427-442`, Zandronum `p_switch.cpp:421-436`):

- **Last `on` frame, repeatable line:** held for `BUTTONTIME`, which is `TICRATE` = **35 tics (one
  second)**, fixed and not configurable (UZDoom `p_spec.h:122`, Zandronum `p_spec.h:433`). Then
  the `off` state starts.
- **Last `on` frame, non-repeatable line:** the animation ends there and the switch stays on.
- **Last `off` frame:** the animation ends there.

So `tics 0` on a last frame (the stock definitions' convention, since they're all single-frame) is
harmless, and so is any other value. It's just ignored.

### `tics 0` on any other frame freezes the switch

On a frame that is **not** the last one, the frame's time is loaded into the thinker's countdown.
The countdown is an unsigned 32-bit counter (UZDoom `p_switch.cpp:56`, Zandronum `p_switch.cpp:76`)
that is decremented *before* the zero test (UZDoom `:390`, Zandronum `:375`). A time of 0 wraps
around instead of expiring, so the frame stays for about 4.29 billion tics (over three years of
game time). In practice the switch **freezes on that frame**. There's no error or warning at
parse time or at runtime. The same happens when `rand 0 <n>` rolls 0, a 1 in `n + 1` chance per
use.

Both engines behave this way (identical code). Use `tics 1` or more on every frame but the last.
Traced from source on both engines and observed live on both (2026-09-29, local test builds, probe
map): with `on pic A tics 0 pic B tics 0`, a used switch stayed on `A` for 115 tics and more,
while `tics 1` on `A` moved to `B` and then back to the off texture. The `rand 0 <n>` roll
freezes the same way: with `on pic A rand 0 1 pic B tics 1`, repeated uses of one switch cycled
normally until the first 0 roll (use 3 on UZDoom, use 2 on Zandronum), which then held `A` for
over 400 tics, and a later use didn't unstick it. `rand 0 0` froze on the first use on both.

## Omitting `off`

With no `off` state (or an `off` state dropped because one of its textures is missing), both
engines build a default one: a single frame showing the base texture, with **the `on` state's
sound** copied in (UZDoom `anim_switches.cpp:185-195`, Zandronum `:197-207`). So a switch with
`on sound X` and no `off` plays X both when pressed and when it resets. Give it an explicit `off`
state without a `sound` line to get the stock reset sound instead.

## How the animation plays

### Which lines animate

A line's switch animates only when its special **succeeds**, and only for these activation types
(UZDoom `p_spec.cpp:155-158`, Zandronum `p_spec.cpp:338-342`):

| Activation | UZDoom | Zandronum |
|---|---|---|
| Use (front side) | animates | animates |
| Impact (shot) | animates | animates |
| Push (bump) | animates | does not animate |
| Cross, or any other type | does not animate | does not animate |

The switch is always looked for on the line's **front sidedef**, whichever side the player used.
Whether the line is repeatable (`ML_REPEAT_SPECIAL`) decides whether it resets. A compatibility
path (`LEVEL2_DUMMYSWITCHES`) also animates non-repeatable shootable lines whose special failed
because no sector has the tag, on both engines.

The engine checks the sidedef's upper, middle and lower textures for a switch and uses the first
match. The order differs between engines; see "Engine-family divergence".

### Pressing

1. The part's texture is set to the first `on` frame at once.
2. If the line is repeatable **or** the `on` state has more than one frame, a button thinker
   starts. Otherwise that's the whole animation (UZDoom `p_switch.cpp:292-300`, Zandronum
   `p_switch.cpp:282-295`).
3. The press sound plays from the line's midpoint, at static attenuation. It's the `on` state's
   `sound` if it has one. Otherwise it's `switches/exitbutn` when the line's special is
   `Exit_Normal`, `Exit_Secret`, `Teleport_NewMap` or `Teleport_EndGame`, and
   `switches/normbutn` for anything else (UZDoom `:270-283`, Zandronum `:257-270`).
4. The thinker steps through the remaining `on` frames, each for its own time.

**Exit switches** change to their first `on` frame and the level then ends, so later frames of a
multi-frame `on` state don't get a chance to play.

### Resetting (repeatable lines only)

After the last `on` frame has shown for 35 tics, the thinker plays the reset sound and runs the
`off` frames (UZDoom `p_switch.cpp:390-418`, Zandronum `p_switch.cpp:375-412`). The reset sound is
the `off` state's `sound` (the copied `on` sound for a default `off` state), or
`switches/normbutn`. **Never** `switches/exitbutn`, even for an exit special. The last `off` frame
is left in place and the thinker ends. Nothing forces the last `off` frame to be the base texture.
If it isn't, the next use animates only if that texture is itself a switch key.

### Both directions are switches

Registering a switch also registers its **last `on` texture** as a switch key, whose animation is
the `off` state (UZDoom `anim_switches.cpp:197-198`, Zandronum `:209-210`). So a line whose texture
is currently that "on" texture is itself a switch: using it plays the `off` state as if it were a
press. That's how a line that starts in the "on" texture in the map works, and it matches vanilla
Doom, where each switch pair works in both directions.

Only one button thinker runs per sidedef. Using a repeatable switch again while its thinker is
running forces that thinker to its next step on the next tic instead of starting a new one, with
no press sound (UZDoom `p_switch.cpp:71-88`, Zandronum `p_switch.cpp:91-108`). In practice this
matters while the last `on` frame is showing (that texture is a switch key, as above): the second
use skips the rest of the one-second hold and starts the reset right away. Intermediate frames
are usually not switch keys, so using the line then changes nothing about the animation.

### `quest`

`quest` is read only by `GlassBreak` (Strife-style breakable glass). That special changes both
sides' switch textures as non-repeatable switches, and if either one is a `quest` switch it gives
the activator (or the first player in the game, if none) Strife's `QuestItem29`,
`UpgradeAccuracy` and `UpgradeStamina` (UZDoom `p_lnspec.cpp:3284-3351`, Zandronum
`p_lnspec.cpp:3438-3488`). On a normal use, `quest` does nothing.

## The `SWITCHES` lump

The Boom binary `SWITCHES` lump is read **after** every ANIMDEFS (see the lump page's "When it is
read"), and only the last-loaded `SWITCHES` lump counts. Each 20-byte record holds an off texture
name (9 bytes), an on texture name (9 bytes) and a 16-bit episode field. Reading stops at the first
record whose episode field is zero. The episode value is otherwise **ignored**: there's no game or
episode filtering, unlike ANIMDEFS game words (UZDoom `anim_switches.cpp:51-91`, Zandronum
`anim_switches.cpp:64-103`).

Each record becomes the same kind of pair an ANIMDEFS `switch` makes: a one-frame `on` state, a
one-frame `off` state back to the off texture, no sounds (so the defaults above apply), not a
quest panel. A record is skipped with no message if either texture is missing. A record whose two
names are the same prints `Switch <name> in SWITCHES has the same 'on' state` to the console and
is skipped.

### Which definition wins

Every definition, from ANIMDEFS or `SWITCHES`, goes through `AddSwitchPair` (UZDoom
`anim_switches.cpp:305-353`, Zandronum `:317-365`). It's last-definition-wins **per texture key**:

- A later definition with the same base texture and the same last `on` texture replaces the
  earlier pair in place.
- A later definition that reuses only **one** of an earlier pair's two textures (same base but a
  different `on` texture, or its base is an earlier switch's `on` texture) disables that earlier
  definition for the shared texture and adds the new pair. The earlier switch's other direction
  keeps working.

Because `SWITCHES` is read last, a `SWITCHES` record beats any ANIMDEFS `switch` that uses either
of its textures. A mod that ships a `SWITCHES` lump for Boom compatibility and also wants ANIMDEFS
animations or sounds on the same textures loses them.

## Bad input

Every "fatal" here is `FScanner::ScriptError`, which calls `I_Error` on both engines (UZDoom
`sc_man.cpp:1063-1088`, where `NoFatalErrors` is off for ANIMDEFS; Zandronum `sc_man.cpp:888-906`).
A fatal error stops startup.

| Input | Result (both engines) |
|---|---|
| Base texture doesn't exist | Block parsed, then dropped silently. Its frame textures aren't checked |
| An `on` frame texture doesn't exist | `on` state dropped silently, so the whole switch is dropped |
| An `off` frame texture doesn't exist | `off` state dropped silently; the default `off` state is built |
| No `on` state | Switch dropped silently |
| Game word doesn't match the running game | Block fully parsed (errors in it are still fatal), then dropped silently |
| `pic` without `tics`/`rand` | Fatal `Must specify a duration for switch frame` |
| `on` or `off` with no `pic` | Fatal `Switch state needs at least one frame` |
| Second `sound` in one state | Fatal `Switch state already has a sound`, unless the first name was unknown (then it was never recorded, and the second one is accepted) |
| Second `on` or `off` | Fatal `Switch already has an on state` / `off state`, unless the first one was dropped for a missing texture |
| Last `on` frame is the base texture | Fatal `The on state for switch <name> must end with a texture other than <name>`. Only checked if the switch wasn't already dropped (missing texture or game mismatch) |
| Fractional or non-numeric duration | Fatal `SC_GetNumber: Bad numeric constant` |
| `tics 0` (or a `rand` rolling 0) on a non-last frame | Accepted silently; the switch freezes on that frame at runtime |
| Unknown `sound` name | Silent; the default sound plays |
| `chex <texture>` or `heretic 1 <texture>` | `chex`/`1` is read as the base texture (missing, so dropped silently), and the real texture name then ends the block and is read as a top-level keyword: fatal |
| Unknown word inside the block (a typo) | Ends the block; fatal as an unknown top-level keyword (see the lump page) |

## Engine-family divergence

- **Which part is checked first.** When a sidedef carries switch textures on more than one part,
  UZDoom uses the first match in the order upper, **middle**, lower (a 2021 upstream change back to
  vanilla's order). Zandronum uses upper, **lower**, middle (UZDoom `p_switch.cpp:249-268`,
  Zandronum `p_switch.cpp:222-244`). A sidedef with switch textures on both the lower and middle
  parts animates a different part on each engine.
- **Push activation.** UZDoom animates a switch when a Push-activated line's special succeeds;
  Zandronum doesn't (UZDoom `p_spec.cpp:155-158`, Zandronum `p_spec.cpp:340`). Both run the
  special.
- **`SWITCHES` quest flag.** UZDoom sets `QuestPanel` to false on switches from the `SWITCHES`
  lump (`anim_switches.cpp:83`). Zandronum never sets it, so it holds whatever the unzeroed
  allocation contained (`anim_switches.cpp:88-96`). It only matters for `GlassBreak` on a
  `SWITCHES`-lump texture. Minor.
- **Everything else matches**: parser, keywords, error messages, timing, `BUTTONTIME`, sounds,
  default `off` state, redefinition and the stock switch list in `wadsrc/static/animdefs.txt`.

## Zandronum-specific: which machine's copy is used

The server decides. It runs the line special, finds the switch in **its own** copy, and runs the
button thinker. Each texture change (the first frame, and every later frame from the thinker) is
sent to clients as `SetLineTexture` carrying the texture's **name**. Each sound (press and reset)
is sent as `SoundPoint` carrying the sound's name (`p_switch.cpp:284-302`, `:388-406`).

- A client whose copy **lacks the switch** still sees every frame the server sends, as long as it
  has the textures.
- A client **missing a frame texture** prints `SetLineTexture: unknown texture: <name>` and leaves
  the wall unchanged (`cl_main.cpp:7084-7092`).
- A switch that exists **only in the client's copy** never animates, because the server doesn't
  treat the line as a switch.
- Clients don't run line specials themselves, with one exception: `ThrustThing` and `ThrustThingZ`
  are predicted for the local player (`gamemode.cpp:1162-1164`, `network.cpp:1616-1619`). A
  switch-textured line with one of those specials also runs the switch from the **client's** copy,
  on top of what the server sends.
- ANIMDEFS isn't checked at connect (see the lump page), so nothing warns about a mismatch.

The switch parser and button code (`src/textures/anim_switches.cpp`, `src/p_switch.cpp`,
`src/p_spec.cpp`) haven't changed since the 3.2.1 version-bump commit (`28f736fb3`), so the
parsing and runtime behavior on this page holds on 3.2.1. The netcode files cited above weren't
checked against 3.2.1.

## See also

- [The ANIMDEFS lump](animdefs-lump.md) for the outer grammar, load order and lump-wide errors.
- [Texture and flat animations](texture-flat-animations.md) for animations, which time in
  fractional tics on the render clock.
- [Animated doors](animated-doors.md) for the other block that swaps wall textures on use.
