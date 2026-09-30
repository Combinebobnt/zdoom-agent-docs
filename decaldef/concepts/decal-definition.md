# The `decal` block

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/gamedata/decallib.cpp` and `decallib.h` (`DecalKeywords`, `GetDecalID`, `ParseDecal`, `AddDecal`, `GetDecalByName`, `GetDecalByNum`, `FDecalGroup::GetDecal`, `FDecalTemplate::ApplyToDecal`, `FTranslation::FTranslation`, `FindAnimator`, `ReadScale`), `src/playsim/a_decals.cpp` (`DImpactDecal::StaticCreate`, `CloneSelf`, `ShootDecal`, `SpawnDecal`), `wadsrc/static/zscript/actors/shared/decal.zs`, `wadsrc/static/mapinfo/common.txt`, `src/maploader/udmf.cpp` (thing `arg0str`), `src/playsim/p_map.cpp` (blood decal colour), `src/common/engine/renderstyle.cpp` (legacy style table), `src/common/utility/palette.cpp` (`V_GetColor`, `V_GetColorFromString`), `src/common/utility/cmdlib.cpp` (`IsNum`), `src/common/engine/sc_man.cpp` (`ScriptError`, `ScriptMessage`, `ParseHex`, `MustMatchString`) and `src/d_main.cpp`; and the Zandronum source's `src/decallib.cpp` and `decallib.h` (same functions), `src/g_shared/a_decals.cpp` (`DImpactDecal::StaticCreate`, `ShootDecal`, `ADecal::BeginPlay`), `wadsrc/static/actors/shared/decal.txt`, `src/p_udmf.cpp`, `src/p_mobj.cpp` (`P_SpawnMapThing`), `src/network.cpp` (`NETWORK_InClientMode`), `src/p_acs.cpp` (`DoSpawnDecal`), `src/sv_commands.cpp` and `src/cl_main.cpp` (`SVC2_SHOOTDECAL`), `src/p_map.cpp`, `src/r_data/renderstyle.cpp`, `src/v_video.cpp`, `src/cmdlib.cpp`, `src/sc_man.cpp` and `src/d_main.cpp`. Stock usage checked in both engines' `wadsrc/static/decaldef.txt`. Keyword names cross-checked against SLADE's `z_decaldef` block in `dist/res/config/languages/zdoom.txt`.

This page covers everything inside `decal <name> [<id>] { ... }`: each keyword, its defaults
and units, what bad input does, and the map-placed `Decal` thing that uses the optional ID. For
the lump's outer grammar, load order and the general redefinition rules, see
[the DECALDEF lump](decaldef-lump.md). Groups and `generator` lines are in
[decal groups and generators](decalgroups-and-generators.md), and the animator blocks a decal
attaches with `animator` are in [animators](animators.md).

## Block shape and defaults

```text
decal <name> [<id>]
{
    <keyword> [<arguments>]
    ...
}
```

Keywords may appear in any order and any number of times. Each one overwrites the field it sets,
so the last occurrence wins, except the flip and `fullbright` flags, which only ever turn on.
Keywords are case-insensitive. A block with no keywords at all is legal and defines a decal with no
texture.

| Field | Default | Set by |
|---|---|---|
| Texture | none (invalid) | `pic` |
| Scale | 1.0 on both axes | `x-scale`, `y-scale` |
| Render style | solid (opaque, alpha ignored) | `solid`, `add`, `translucent`, `fuzzy`, `shade`, UZDoom `translatable` |
| Alpha | 1.0 | `add`, `translucent` |
| Shade colour | none | `shade` |
| Colour translation | none | `colors` |
| Flips, full brightness | off | `flipx`, `flipy`, `randomflipx`, `randomflipy`, `fullbright` |
| Animator | none | `animator` |
| Lower decal | none | `lowerdecal` |
| Translatable | off (UZDoom only) | `translatable`, `opaqueblood` |

Defaults: the UZDoom source's `src/gamedata/decallib.cpp:363-368`, the Zandronum source's
`src/decallib.cpp:458-463`.

## Keywords

| Keyword | Arguments | Effect | UZDoom | Zandronum |
|---|---|---|---|---|
| `pic` | texture or lump name | The graphic to stamp | yes | yes |
| `x-scale` | number | Horizontal size multiplier, clamped to 1/256 .. 256 | yes | yes |
| `y-scale` | number | Vertical size multiplier, same clamp | yes | yes |
| `solid` | none | Opaque style; alpha is ignored | yes | yes |
| `add` | number | Additive style with this alpha | yes | yes |
| `translucent` | number | Translucent style with this alpha | yes | yes |
| `fuzzy` | none | Spectre-fuzz style | yes | yes |
| `shade` | colour, or `BloodDefault` | Stencil-like style: the graphic's intensity is the opacity, drawn in one colour | yes | yes |
| `colors` | two colours | A gradient palette translation from the first to the second | yes | yes |
| `flipx`, `flipy` | none | Always mirror horizontally / vertically | yes | yes |
| `randomflipx`, `randomflipy` | none | 50% chance per spawn to mirror | yes | yes |
| `fullbright` | none | Ignores sector light | yes | yes |
| `animator` | animator name | Attach a fader, stretcher, slider, colorchanger or combiner | yes | yes |
| `lowerdecal` | decal or group name | Another decal stamped underneath at the same spot | yes | yes |
| `translatable` | none | Solid style, and follow the spawner's translation (blood colour) | yes | **fatal unknown keyword** |
| `opaqueblood` | none | Deprecated alias of `translatable` | yes | **fatal unknown keyword** |

There are no other keywords. Both parsers match against a fixed list (UZDoom
`decallib.cpp:149-170`, Zandronum `decallib.cpp:258-277`), and anything else is a fatal error.

### `pic`

The name is looked up as a texture of any type first (wall texture, flat, sprite, TEXTURES
definition). If none exists, a lump of that name in the graphics namespace is turned into a decal
texture. A name that matches neither is not an error: the decal is defined with no texture
(UZDoom `decallib.cpp:388-396`, Zandronum `decallib.cpp:483-491`). Impact decals then draw
nothing, and a map-placed `Decal` thing prints a message (see below).

### Scale

`x-scale` and `y-scale` take a decimal number. 1.0 is the graphic's own size. Values are clamped
to the range 1/256 .. 256 with no message (UZDoom `ReadScale`, `decallib.cpp:1173-1177`;
Zandronum `decallib.cpp:1431-1435`). A non-numeric value is a fatal `Bad numeric constant` error.

### Render style and alpha

The style is a single slot. `solid`, `add`, `translucent`, `fuzzy`, `shade` and (UZDoom)
`translatable` each overwrite it, so the last one in the block decides. Alpha is a separate slot
that only `add` and `translucent` write, and it survives a later style keyword. `translucent 0.5`
followed by `shade "ff 00 00"` gives a half-opaque red shaded decal. The stock bullet chips on both
engines rely on this: `translucent 0.85` then `shade "00 00 00"`.

What each style does with alpha, from the legacy style table (UZDoom
`src/common/engine/renderstyle.cpp:38-45`, Zandronum `src/r_data/renderstyle.cpp:98-105`):

- **`solid`** forces full opacity. An alpha set earlier is ignored while this style is active.
- **`translucent`** blends normally at the given alpha.
- **`add`** adds the graphic's colour onto the wall, scaled by alpha. Stock plasma scorches use
  `add 1.0` with `fullbright`.
- **`fuzzy`** is the spectre effect. Alpha is not used.
- **`shade`** uses the graphic's red channel (palette index in the software renderer) as opacity
  and paints the whole decal in the shade colour, times alpha.

The alpha number is 0.0 (invisible) to 1.0 (full). UZDoom stores it as a double with no clamp.
Zandronum stores it in 16 bits where 1.0 is 32768 and doubles it when the decal is created
(`decallib.cpp:499`, `decallib.cpp:1049`), so a value of 2.0 or more overflows. Keep it within
0 .. 1 on both.

### `shade`

Takes one colour argument, normally quoted. The colour forms are the engine-wide ones (UZDoom
`src/common/utility/palette.cpp:558-640`, Zandronum `src/v_video.cpp:442-525`):

- `"RR GG BB"`: three space-separated hex components. A one-digit component is doubled (`"f 8 0"`
  is `ff 88 00`).
- `"RRGGBB"`: six hex digits with no spaces.
- `"#RRGGBB"` or `"#RGB"`. A `#` string of any other length is black, silently.
- An X11 colour name (`"dark red"`), looked up in the `X11R6RGB` lump.
- **`BloodDefault`** (quoted or not) uses the game's default blood colour from `gameinfo`
  (UZDoom `decallib.cpp:438-452`, Zandronum `decallib.cpp:533-547`).

A malformed hex component prints `Bad hex number: ...` and becomes 0. It is a warning, not an
error, and loading continues. UZDoom's warning carries the script position; Zandronum's is a plain
console line.

**Blood decals override the shade colour.** When an actor with a custom blood colour bleeds, the
blood decal is created with that colour at half brightness as an override (UZDoom
`src/playsim/p_map.cpp:5239-5251`, Zandronum `src/p_map.cpp:4701-4718`). A `shade` decal used for
blood therefore takes the bleeding actor's colour, and only falls back to its own shade (such as
`BloodDefault`) for actors without a custom blood colour. The override only shows on shaded decals.

### `colors`

Takes two colours in the same forms as `shade`. It builds a palette translation: palette index
*i* of the decal graphic is drawn as the colour at position *i*/255 of a gradient from the first
colour to the second. It does not change the render style. The gradient is built in
`FTranslation::FTranslation` (UZDoom `decallib.cpp:995-1033`, Zandronum `decallib.cpp:1069-1107`),
identically on both engines, and has two arithmetic quirks:

- **The green step is computed from the red start value** (UZDoom `decallib.cpp:1024`, Zandronum
  `decallib.cpp:1098`). The green channel only ramps as intended when the start colour's red and
  green components are equal.
- **A channel can only ramp upward.** The step is unsigned, so a channel whose end value is below
  its start does not fade down: it counts upward and wraps through 0 on its way to the end value.

A gradient where every channel of the second colour is at least that channel of the first, and the
first colour's red and green match (for example black to anything), comes out as written. No stock
decal uses `colors` on either engine.

Identical colour pairs share one translation. After 256 distinct pairs the engine prints
`Too many decal translations defined` and the decal gets no translation.

### Flips

`flipx` and `flipy` set the mirror flag permanently. `randomflipx` and `randomflipy` XOR the
matching mirror flag with a fresh random bit every time the decal is stamped (UZDoom
`FDecalTemplate::ApplyToDecal`, `decallib.cpp:965-988`; Zandronum `decallib.cpp:1039-1062`). So
`flipx` together with `randomflipx` is still a 50/50 flip, not "always flipped". The two random
flips are independent.

### `fullbright`

Draws the decal at full brightness regardless of the sector's light level. It does not change the
render style.

### `animator`

Names an animator block (`fader`, `stretcher`, `slider`, `colorchanger` or `combiner`) that must be
defined **above** this decal. When several animators share the name, the most recently defined one
at that point wins (`FindAnimator` searches newest first: UZDoom `decallib.cpp:1147-1159`,
Zandronum `decallib.cpp:1357-1368`). The animator starts when the decal is stamped. See
[animators](animators.md) for the blocks themselves.

An unknown name leaves the decal unanimated. UZDoom prints `Unable to find animator <name>` through
`ScriptMessage`, which is formatted in red as a "Script error" but is **not fatal**
(`decallib.cpp:462-469`, `sc_man.cpp:1096-1115`). Zandronum says nothing.

### `lowerdecal`

Names a decal or group, defined **above** this block, that is stamped at the same spot just before
this one, so it appears underneath. The lower decal uses its own template (style, colour, animator,
flips). If both decals have the same shade colour, an override colour (such as a blood colour) is
passed to the lower decal too; otherwise the lower decal keeps its own. A lower decal can have a
lower decal of its own. An unknown name leaves the field empty, silently, on both engines.

The two engines treat a **group** here differently, and treat **permanent** decals differently:

- **UZDoom resolves a group at load time.** Its name lookup reduces a group to one member picked at
  random (`GetDecalByName`, `decallib.cpp:884-896`), and that member is stored. Every spawn of the
  upper decal uses that one member for the rest of the session, and redefining the group later
  doesn't change it.
- **Zandronum stores the group itself.** Its name lookup returns the group unresolved
  (`decallib.cpp:958-970`), and the member is picked each time the upper decal is stamped
  (`src/g_shared/a_decals.cpp:679-682`). Redefining the group later does take effect.
- **Zandronum skips `lowerdecal` on permanent decals.** Its permanent path in `ShootDecal`
  (`a_decals.cpp:799-812`) stamps only the decal itself. That path serves the map-placed `Decal`
  thing and ACS `SpawnDecal` with `SDF_PERMANENT`. UZDoom routes permanent decals through the same
  creation function as impact decals, which draws the lower decal (`src/playsim/a_decals.cpp:709-726`).

The stock `BFGLightning1` decal names the group `BFGScorch` as its `lowerdecal`, in both engines'
`decaldef.txt`, so the scorch under BFG lightning varies per hit on Zandronum and is fixed per
session on UZDoom.

**Don't name a decal's own name as its `lowerdecal` when redefining it.** The lookup finds the old
definition, which the redefinition then deletes. The reference fix-up that redefinition performs
runs before the new decal is linked in, so it never repairs the new decal's own `lowerdecal`
(UZDoom `decallib.cpp:837-849`, Zandronum `decallib.cpp:918-930`). The new decal is left pointing
at a deleted definition. To layer a new graphic over a stock decal, copy the stock decal under a
new name first and point `lowerdecal` at the copy.

### `translatable` and `opaqueblood` (UZDoom only)

`translatable` sets the style to solid and marks the decal translatable (`decallib.cpp:476-480`).
`opaqueblood` is the same keyword under its old name, kept for compatibility. When a translatable
decal is stamped with a translation, it takes that translation and is drawn solid
(`a_decals.cpp:747-751`, and `CloneSelf` at `a_decals.cpp:787-791` for spread pieces). Two limits:

- **Only blood and `A_SprayDecal` pass a translation.** Blood passes the bleeding actor's blood
  translation, and only when that actor has a custom blood colour (`p_map.cpp:5248`).
  `A_SprayDecal` passes one when asked to. Bullet, projectile, `Decal` thing and ACS `SpawnDecal`
  decals pass none, so for them `translatable` just means `solid`.
- **Any `shade` in the block defeats it**, before or after. The check requires the decal to have no
  shade colour. `shade` followed by `translatable` is worse: the style ends up solid while the shade
  colour stays set, so the decal is drawn opaque and uncoloured.

Zandronum has neither keyword and rejects both as fatal errors.

## The optional ID and the `Decal` thing

### The ID

A whole number between the name and the `{` gives the decal an ID for the `Decal` thing. Rules
(re-verified against `GetDecalID` and `AddDecal` on both engines):

- **Range 1 to 65535.** Anything else is fatal. A token counts as a number if it's made only of
  digits and `-`, so `-5` is read as an ID and wraps to a huge value that fails the range check,
  while `5a` is taken as the start of the block and fails as `Expected '{'`. UZDoom's error reads
  `Decal ID must be between 1 and 65535`. Zandronum's is garbled, reading
  `Expected 'Decal ID must be between 1 and 65535', got '...'` with the token after the ID
  (UZDoom `decallib.cpp:331-348`, Zandronum `decallib.cpp:425-442`).
- **IDs are unique across decals and groups.** Defining something with an ID already in use takes
  the ID away from the previous holder.
- **A redefinition without an ID drops the ID.** To keep a stock decal usable from `Decal` things,
  repeat its ID in the redefinition.

### The map-placed `Decal` thing (editor number 9200)

A `Decal` thing stamps one permanent decal when the map loads, then removes itself. It exists on
both engines: UZDoom maps 9200 to the ZScript class `Decal` in `wadsrc/static/mapinfo/common.txt:83`,
and Zandronum declares `ACTOR Decal 9200 native` in `wadsrc/static/actors/shared/decal.txt`.

- **Which decal.** `args[0] + args[1] * 256` is the ID. In Hexen-format maps each arg is a byte,
  so the second arg carries the high byte. In UDMF `arg0` alone can hold the whole ID. A group ID
  picks one member per thing, at map load.
- **Where.** The engine traces up to 64 map units horizontally from the thing, in the direction
  **opposite** its facing angle, at the thing's own height. Place the thing within 64 units of the
  wall, facing away from it.
- **Permanent.** The decal is not an impact decal: it doesn't count toward `cl_maxdecals`, isn't
  removed when that limit is reached, and ignores a line's "no automatic decals" flag. It still
  spreads onto neighbouring walls when `cl_spreaddecals` is on.
- **Messages.** A decal without a valid texture prints
  `Decal actor at (x,y) does not have a valid texture` and nothing is stamped. An unknown or zero
  ID, and a missing wall, are only reported with `developer` on.

Sources: UZDoom `src/playsim/a_decals.cpp:881-918` (`SpawnDecal`, called from `BeginPlay` in
`decal.zs`), `a_decals.cpp:857-872` (`ShootDecal`); Zandronum `src/g_shared/a_decals.cpp:822-862`
(`ADecal::BeginPlay`) and `a_decals.cpp:780-820` (`ShootDecal`).

**UZDoom can also pick a decal by name.** In a UDMF map, a thing with no special and an `arg0str`
string gets its first arg set to the negated name index (`src/maploader/udmf.cpp:813-816`). The
`Decal` thing treats a negative first arg as a decal or group **name** (`a_decals.cpp:885-889`), so
`arg0str = "MyScorch";` places a named decal with no ID needed. Zandronum's UDMF loader performs the
same `arg0str` conversion (`src/p_udmf.cpp:730-733`), but its `Decal` thing reads the result as a
numeric ID, which is almost never a real one. So nothing is stamped.

## Errors

Every "fatal" entry below is a script error raised while DECALDEF is read during startup (UZDoom
`d_main.cpp:3679`, Zandronum `d_main.cpp:3015`). That's before the game loop's
recoverable-error handler exists, so on both engines it aborts startup with
`Script error, "DECALDEF" line N:` and the message.

| Condition | UZDoom | Zandronum |
|---|---|---|
| Unknown keyword in the block | Fatal: `Unknown keyword '...'` | Fatal: `Bad syntax.` (the keyword isn't named) |
| `translatable` or `opaqueblood` | Accepted | Fatal: `Bad syntax.` |
| Non-number after `x-scale`, `y-scale`, `add`, `translucent` | Fatal: `SC_GetFloat: Bad numeric constant` | Same |
| Scale outside 1/256 .. 256 | Clamped, silently | Same |
| Alpha of 2.0 or more | Accepted as is | Overflows, silently |
| Bad hex in a `shade` or `colors` colour | Warning `Bad hex number`, component becomes 0 | Same (no script position) |
| `pic` names nothing | Silent, no texture | Same |
| `animator` names nothing defined yet | Red `Unable to find animator` message, not fatal | Silent |
| `lowerdecal` names nothing defined yet | Silent | Same |
| Missing `}` before end of lump | Fatal: unexpected end of file | Same |
| ID out of range | Fatal | Fatal, garbled message (above) |

## Engine-family divergence

Every point here was checked in both engines' source:

- **`translatable`/`opaqueblood`** exist only on UZDoom. Zandronum rejects both as fatal.
- **`lowerdecal` naming a group** is fixed to one member at load on UZDoom, and re-picked on every
  spawn on Zandronum.
- **Permanent decals** (the `Decal` thing, `SpawnDecal` with `SDF_PERMANENT`) draw their
  `lowerdecal` on UZDoom and skip it on Zandronum.
- **An unknown `animator`** prints a non-fatal message on UZDoom and nothing on Zandronum.
- **An unknown keyword** names the keyword in UZDoom's fatal error and just says `Bad syntax.` on
  Zandronum.
- **Alpha** is a double on UZDoom and a 16-bit value on Zandronum, which overflows at 2.0.
- **The `Decal` thing picks a decal by name** from a UDMF `arg0str` only on UZDoom.
- **The `colors` quirks** (green step from red start, upward-only channels) are identical on both.
- **SLADE** lists `x-scale` and `y-scale` split into `x`, `y` and `scale` (highlighting only), and
  lacks `translatable` and `opaqueblood`.

## Zandronum-specific: which machine's copy is used

**Online, a map-placed `Decal` thing stamps nothing on clients.** The chain, all in the Zandronum
source:

1. `Decal` carries no network flags: its DECORATE definition is empty
   (`wadsrc/static/actors/shared/decal.txt`).
2. `P_SpawnMapThing` refuses to spawn any map thing on a client unless its class has
   `ALLOWCLIENTSPAWN` or `CLIENTSIDEONLY` (`src/p_mobj.cpp:6187-6193`). "Client" here includes
   client-side demo playback (`src/network.cpp:1552-1555`). So clients never create the thing.
3. The server does spawn it, and `ADecal::BeginPlay` stamps the decal on the server with a plain
   `ShootDecal` call (`src/g_shared/a_decals.cpp:851`). It doesn't go through the
   `SVC2_SHOOTDECAL` wrapper, which only ACS `SpawnDecal` uses (`src/p_acs.cpp:5812-5826`), and no
   other code in the client or server modules syncs decals.

The result: in single player and offline games the decal appears as normal; on a server it exists
only in the server's own world, and no client sees it. A client's DECALDEF copy is never consulted
for these things. UZDoom has no such split; every machine runs the same map load.

The same spawn gate gives a workaround: a DECORATE class that inherits from `Decal`, replaces it
and sets `+CLIENTSIDEONLY` is spawned by each client (which then stamps from its own DECALDEF) and
skipped by the server, since `P_SpawnMapThing` checks the replacement class's flags
(`p_mobj.cpp:6119`, `6187-6199`). Observed live (2026-09-29, local test build, server + 2 clients,
probe map): with a plain map-placed `Decal` thing neither client showed the decal; adding
`actor ClientDecal : Decal replaces Decal { +CLIENTSIDEONLY }` made it appear on both.

For impact decals and ACS `SpawnDecal`, see the lump page's
[which machine's copy is used](decaldef-lump.md#zandronum-specific-which-machines-copy-is-used).

## Example

A scorch mark with a soot layer under it, and a blood splat that follows the bleeding actor's
colour on UZDoom (the texture names are the mod's own; drop `translatable` for Zandronum):

```text
decal MySoot
{
    pic MYSOOT
    shade "10 10 10"
    translucent 0.6
    x-scale 1.5
    y-scale 1.5
    randomflipx
}

decal MyScorch 4001
{
    pic MYSCRCH
    add 0.8
    fullbright
    randomflipx
    randomflipy
    lowerdecal MySoot
}

decal MyBloodSplat
{
    pic MYBLUD1
    translatable
    randomflipx
}
```

`MyScorch` can then be placed from a map with a `Decal` thing whose first two args are `161` and
`15` (161 + 15 x 256 = 4001), or with `arg0` = 4001 in UDMF.

## See also

- [The DECALDEF lump](decaldef-lump.md) for the outer grammar, load order, redefinition and the
  impact-decal and `SpawnDecal` netcode.
- [Decal groups and generators](decalgroups-and-generators.md) for `decalgroup` and `generator`.
- [Animators](animators.md) for the blocks `animator` names.
- [`../../acs/families/spawning.md`](../../acs/families/spawning.md) for ACS `SpawnDecal`.
- [`../../console/notes/cl_maxdecals.md`](../../console/notes/cl_maxdecals.md) for the impact-decal
  limit, which permanent decals ignore.
- The DECORATE `Decal` property row in
  [`../../decorate/inventory/actor-properties.md`](../../decorate/inventory/actor-properties.md).
