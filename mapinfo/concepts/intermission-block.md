# Intermission block structure

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** ZDoom Wiki `MAPINFO/Intermission_definition` (retrieved 2026-09-28, https://zdoom.org/w/index.php?title=MAPINFO/Intermission_definition&oldid=54706) + verified against UZDoom `src/intermission/intermission_parse.cpp` (whole file, incl. `:71` default duration, `:276-300` Wiper, `:308-400` TextScreen) and `src/intermission/intermission.cpp:210-234,400-520`, and Zandronum `src/intermission/intermission_parse.cpp:79,483-568` and `src/intermission/intermission.cpp:166-178,307-369`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

An intermission is a sequence of visual steps shown between levels or when finishing an episode. An `intermission` block in MAPINFO defines such a sequence by name, composing it from several sub-block/action types (Image, Scroller, Cast, Fader, Wiper, TextScreen, GotoTitle, and on UZDoom, Cutscene). Each sub-block represents one step; steps execute in order. Upon completion of the final step, the intermission either links to another named intermission via the `Link` property or returns control to the game state that invoked it (advancing to the next level in a hub/map transition, or ending the game if invoked at episode end — the caller's `ending` parameter determines which).

## Block structure and parsing

```mapinfo
intermission <name>
{
  Image { ... }
  Scroller { ... }
  Fader { ... }
  Wiper { ... }
  TextScreen { ... }
  Cast { ... }
  GotoTitle { }
  Link = <other_intermission_name>
}
```

An intermission descriptor is identified by a name string and contains a series of sub-block actions plus an optional `Link` property. A sub-block `{}` contains action-specific properties. Unknown sub-block types cause a fatal parse error (both engines).

The `Link` property is not a step — it is a descriptor field parsed by early return and can appear anywhere in the block. When set, `Link = <name>` causes the intermission to branch to the named intermission after all steps complete, rather than ending. If a later `intermission <name>` block redefines an earlier one with the same name, the later definition silently replaces it (last definition wins), allowing mods to override built-in intermissions by name.

## Generic properties

The following properties are supported within any sub-block (Image, Scroller, Cast, Fader, Wiper, TextScreen, GotoTitle, Cutscene):

| Property | Type | Description |
|---|---|---|
| `Background = <image>[, <tile>]` | String, optional int | Lump name of the background image for this step. Optional second argument: if 0 or omitted, the image is stretched to fill the screen; if non-zero, the image is tiled at its native resolution and clipped to screen bounds. Optional third argument (a palette lump name) is parsed but ignored by both engines. A `"$LABEL"` value is looked up in LANGUAGE; **on Zandronum a missing label crashes the engine** when the step starts (observed live), and UZDoom uses the label as the image name. |
| `Draw = <image>, <x>, <y>` | String, int, int | Overlay image name and screen coordinates (x, y) where (0, 0) is top-left and (319, 199) is bottom-right. Drawn unconditionally. |
| `DrawConditional = <condition>, <image>, <x>, <y>` | String, String, int, int | Conditional overlay. `<condition>` is meant to be "Multiplayer" or a player class name; see "DrawConditional evaluation" below, since the `Multiplayer` form never draws in either engine. |
| `Music = <song>[, <order>]` | String, optional int | SNDINFO logical music name; optional sub-song order for formats supporting multiple tracks (e.g., MUS with subsongs). |
| `Sound = <sound>` | String | SNDINFO logical sound name to play upon entering this step. |
| `Time = <length>` | Float or minus-prefixed int | Duration of this step. **Syntax:** positive number (with or without decimal) = seconds (multiplied by 35); minus-prefixed integer = tics (stored directly). Examples: `Time = 3.5` equals 122 tics; `Time = -105` equals 105 tics. The default is 0 for every action type, and a step whose duration is 0 (or negative) never ends on its own: it waits for a key press. |

## Action types

### Image

Displays a full-screen background image for a specified duration, with optional overlays.

| Property | Type | Default | Description |
|---|---|---|---|
| `Time` | Float or `-int` | 0 (wait for a key) | Duration to display. |

**Example:**
```mapinfo
Image
{
  Background = "ENDPIC"
  Time = 5
  Draw = "OVERLAY", 160, 100
}
```

### Scroller

Scrolls from one image to another with configurable direction, speed, and delay.

| Property | Type | Default | Description |
|---|---|---|---|
| `Background2 = <lump>` | String | (required) | Destination image lump after scroll completes. |
| `ScrollDirection = <type>` | Identifier | Right | Scroll direction: `Left`, `Right`, `Up`, or `Down`. |
| `ScrollTime = <length>` | Float or `-int` | 640 tics | Total duration of the scroll animation. Same syntax as `Time` (positive = seconds, minus-prefixed int = tics). |
| `InitialDelay = <length>` | Float or `-int` | 0 tics | Delay before scrolling begins. Same syntax as `Time`. |

### Fader

Fades in or out from a background image over a duration.

| Property | Type | Default | Description |
|---|---|---|---|
| `FadeType = <type>` | Identifier | FadeIn | Fade direction: `FadeIn` or `FadeOut`. |
| `Time` | Float or `-int` | 0 (wait for a key) | Duration of the fade. |

### Wiper

Forces a screen wipe into the next step.

| Property | Type | Default | Description |
|---|---|---|---|
| `WipeType = <type>` | Identifier | Default | Wipe effect: `Crossfade`, `Melt`, `Burn`, or `Default`. An unrecognized name is silently ignored and leaves `Default`. |

Wiper has no key of its own besides `WipeType`; `Background2` is a Scroller key.

### TextScreen

Displays scrolling text, with configurable color, speed, and position.

| Property | Type | Default | Description |
|---|---|---|---|
| `Position = <x>, <y>` | Int, Int | (-1, -1) | Text upper-left corner in screen coordinates (0-319 x, 0-199 y). Default (-1, -1) defers to GameInfo block settings (`textScreenX`, `textScreenY`). |
| `TextLump = <lump>` | String | (none) | Lump name containing the text to display. Mutually exclusive with `Text` key. |
| `Text = <line>[, <line>, ...]` | String, String... | (none) | Explicit text lines to display (unlimited); each line on separate entry separated by comma. Mutually exclusive with `TextLump`. On UZDoom a single string starting with `$` is looked up in the [LANGUAGE](../../language/concepts/language-lump.md) lump (with several strings the `$` stays literal). **On Zandronum the lookup never matches** and the screen shows the bare label (observed live), because the parser appends a newline before the lookup; use a cluster `EnterText`/`ExitText` or literal text there. See [string retrieval](../../language/concepts/string-retrieval.md). |
| `TextColor = <color>` | String | Untranslated | Color name (from X11R6RGB or a [TEXTCOLO](../../fonts/concepts/textcolo-lump.md) color constant). |
| `TextDelay = <length>` | Float or `-int` | 10 tics | Delay before the text starts typing out. Same syntax as `Time` (positive = seconds, minus-prefixed int = tics). The default of 10 is stored directly as tics. |
| `TextSpeed = <value>` | Int | 2 | Tics per character while the text types out. |
| `Time` | Float or `-int` | 0 (wait for a key) | How long the screen stays **after** the text has finished typing: a positive duration has `TextDelay + TextSpeed × character count` added to it. If 0 or negative, the screen stays until a key press. A key press while the text is still typing skips to the fully-typed text. |

### Cast

Displays a cast-of-characters slide, showing actor classes with attack animations and accompanying sounds. Used for game credits/end credits.

| Property | Type | Default | Description |
|---|---|---|---|
| `CastClass = <name>` | String | (required) | Actor class name (e.g., "Cyberdemon", "ArchVile"). Class is resolved via the game's actor registry at intermission start. |
| `CastName = <string>` | String | (required) | Display name for the character. If the string starts with `$`, it is interpreted as a LANGUAGE lump identifier. |
| `AttackSound = <label>, <offset>, <sound>` | String, Int, String | (none) | Repeatable. Play a sound during the cast animation. `<label>` must be either `Melee` or `Missile`; any other value is silently ignored at parse time. `<offset>` is a frame offset (0 or positive integer) within that animation sequence. `<sound>` is a SNDINFO logical sound name. Multiple `AttackSound` entries per cast block are allowed. |

**Example:**
```mapinfo
Cast
{
  CastClass = "ArchVile"
  CastName = "The Archvile"
  AttackSound = "Missile", 5, "arch/attack"
  AttackSound = "Melee", 2, "arch/melee"
}
```

### GotoTitle

Terminates the intermission and returns to the title screen immediately. Has no properties; appears as `GotoTitle { }` (braces required, may be empty or contain only comments).

### Cutscene (UZDoom only)

Not supported in Zandronum.

Plays a video or runs a ZScript function as an intermission step. Supports audio syncing with the video/function.

| Property | Type | Default | Description |
|---|---|---|---|
| `Video = "<path>"` | String | (none) | Full path, name, and file extension of a video file (e.g., `"graphics/videos/intro.ivf"`). Mutually exclusive with `Function`. |
| `Function = "<funcname>"` | String | (none) | ZScript function to execute. Function must be static, have no return type, and take a `ScreenJobRunner` as its sole argument. Mutually exclusive with `Video`. |
| `Sound = "<soundname>"` | String | (none) | SNDINFO logical sound name to play during the cutscene. |
| `SoundID = <id>` | Int | -1 | Resource ID for audio playback (not a sound index). Default -1 means no ID-based sound. |
| `FPS = <value>` | Int | (format-dependent) | Playback framerate; used only for ANM video format. |
| `Delete` | (none) | — | Clear the cutscene's video and function assignments without deleting the cutscene definition itself. The cutscene remains defined but displays nothing. |
| `Clear` | (none) | — | Completely clear the cutscene definition (equivalent to deleting and reinitializing it). |

**Example (UZDoom):**
```mapinfo
Cutscene
{
  Video = "graphics/videos/intro.ivf"
  Sound = "Music/IntroMusic"
  FPS = 30
}
```

## Engine-family divergence

### Cutscene block (UZDoom only)

The `Cutscene` sub-block is not implemented in Zandronum. UZDoom projects can include `Cutscene` blocks in intermission definitions; Zandronum will treat `Cutscene { ... }` as an unknown intermission action type and raise a fatal parse error. Mods targeting Zandronum should avoid this block entirely.

All Cutscene sub-keys (`Video`, `Function`, `Sound`, `SoundID`, `FPS`, `Delete`, `Clear`) are verified against UZDoom source only.

### DrawConditional evaluation (both engines)

The condition string in `DrawConditional` is evaluated when the overlay is drawn (UZDoom `src/intermission/intermission.cpp:222-234`, Zandronum `src/intermission/intermission.cpp:166-178`; same logic, Zandronum tests its network state instead of `multiplayer`):

- In any multiplayer game, **no** conditional overlay is drawn.
- **`"Multiplayer"` never draws, in either engine.** In single-player it is rejected by the first test. In multiplayer it falls through to the class-name branch, which rejects every multiplayer game. The wiki's "draw only in multiplayer" is therefore not what the code does.
- Any other string, in single-player: drawn if player 1's actor is that class **or a subclass of it**. An unknown class name draws nothing.

## Wiki/engine divergence: timing syntax

The original ZDoom Wiki page describes the timing syntax inconsistently. **Actual behavior (both engines identical):**

All timing properties use the same convention:
- **Positive number** (with or without decimal): duration in **seconds** (multiplied by 35 to convert to tics).
- **Minus-prefixed integer**: duration in **tics** (stored directly, no conversion).

The wiki documents `Time` correctly (positive = seconds, negative = tics) but states `InitialDelay`, `ScrollTime`, and `TextDelay` with the opposite (positive = tics, negative = seconds). This is a documentation error covering three properties; the code implements only one unified convention.

All property defaults are stated in tics. Calculations with TICRATE (35):

| Input | Calculation | Result |
|---|---|---|
| `Time = 3` | 3 sec × 35 tics/sec | 105 tics |
| `Time = -105` | tics directly | 105 tics |
| `ScrollTime = 100` | 100 sec × 35 | 3500 tics |
| `ScrollTime = -640` | tics directly | 640 tics |
| `InitialDelay = 1.5` | 1.5 sec × 35 | 52 tics |
| `InitialDelay = -52` | tics directly | 52 tics |
| (no `TextDelay`, default) | stored directly | 10 tics |
| `TextDelay = 10` | 10 sec × 35 (the default's number, written out, means seconds) | 350 tics |
| `TextDelay = 0.3` | 0.3 sec × 35 | 10 tics |
