# Sprite naming and rotation encoding

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki "Creating new sprite graphics" (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=Creating_new_sprite_graphics&oldid=54007), verified against the Zandronum source's sprite initialization code (`src/r_data/sprites.cpp`, `src/r_data/sprites.h`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

A sprite lump name encodes the actor's sprite identity, animation frame, and rotation angle in a fixed binary format. This format is read directly by the engine at wad-load time; understanding it is necessary to create multi-frame or rotating sprite sets.

## Lump name format

Every sprite lump name has this exact structure:

```text
XXXXYRD[FRD]
```

Where:

- **XXXX** (4 characters, positions 0–3): The sprite identifier — a unique 4-letter code used to group all frames and rotations of one sprite together (e.g., `TROO`, `CYBR`, `POSS`). The engine hashes on these 4 characters to organize lookup tables; sprites are identified by their first 4 characters only. Any other length is either a syntax error (at lump load time) or ignored entirely.
- **Y** (position 4, frame letter): A single letter indicating which animation frame this lump represents. Valid frame letters are case-insensitive:
  - `A`–`Z` (frames 0–25)
  - `[` (frame 26), `\` (frame 27), `]` (frame 28)
  
  This gives 29 possible frames per sprite. Frame letters are mapped to indices by subtracting `'A'` from the character value (`src/r_data/sprites.cpp:359`, `src/thingdef/thingdef_states.cpp` frame parsing). For example, `XXXXA` is frame 0, `XXXXB` is frame 1, `XXXX[` is frame 26.
- **R** (position 5, rotation digit): A single digit or letter indicating the rotation slot. See "Rotation encoding" below.
- **D** (position 6, optional): An optional second frame letter (same 29-character range as position 4) indicating which frame to mirror. If present, **position 7 must also be present** and must be a second rotation digit.
- **FRD** (positions 6–7, optional): If present, specifies an alternative frame and rotation to display as a horizontally flipped copy of the main frame/rotation specified in positions 4–5. Only valid if positions 6 and 7 are both filled. See "Mirroring" below.

## Rotation encoding

The rotation digit (position 5, and position 7 if mirroring) specifies both the rotation slot and the frame's rotation count. A single digit can mean "this is one of an 8-frame set" or "this is one of a 16-frame set," depending on the digit's numeric value.

### Rotation count 0: non-rotating sprites

A rotation digit of `0` means this frame has only one graphic, used from all angles. The engine automatically fills all 16 internal rotation slots with the same graphic.

Example: `BARRL0` → The barrel sprite, frame A, rotation 0. Only one lump needed; it displays identically from every direction.

### Rotation count 8: eight-way rotations

Rotation digits `1`–`8` encode the eight cardinal and intercardinal directions (front, front-left, left, back-left, back, back-right, right, front-right). The engine interprets these as 8-way rotation and fills the remaining 16-way slots by replicating the 8-way set.

Digit mapping (`src/r_data/sprites.cpp:97–99`): digits `1`–`8` are converted to internal indices `0, 2, 4, 6, 8, 10, 12, 14` respectively. These are the "even" slots in the engine's 16-rotation table.

Example: `XXXXA1`, `XXXXA2`, ..., `XXXXA8` → Eight separate lumps for a full 8-way rotation set of frame A.

### Rotation count 16: sixteen-way rotations

For higher-resolution rotation coverage, combine digits `1`–`8` with the extended notation `9` / `A`–`G`. These fill the remaining "odd" slots in the engine's 16-rotation table, giving a 16-way rotation set.

Digit mapping (`src/r_data/sprites.cpp:102–104`): digits `9` and `A`–`G` (ASCII 57 and 65–71) are converted to rotation values 9–16, then to internal indices `1, 3, 5, 7, 9, 11, 13, 15` respectively.

Example: `XXXXA1`, `XXXXA9`, `XXXXA2`, `XXXXAA`, ..., `XXXXAG` → A full 16-way rotation set where digits 1–8 and 9/A–G interleave to cover all angles evenly.

If you provide only the 8-way rotations (digits 1–8) without the 16-way slots (9/A–G), the engine replicates the 8-way set to fill the empty 16-way slots automatically. A sprite is not *required* to provide 16-way graphics; 8-way is sufficient, though less smooth at intermediate angles.

## Mirroring

The optional 6th and 7th characters allow a single graphic to serve double duty, flipped, for two rotation slots — saving lump space. If the first 5 characters are `XXXXA2`, adding characters specify a mirrored copy.

Example: `XXXXA2C8` means:
- Positions 0–5: `XXXXA2` — frame A, rotation 2.
- Positions 6–7: `C8` — This same graphic will also be used as a flipped copy for frame C, rotation 8.

The engine loads one physical lump but marks both rotation slots (frame A rotation 2 and frame C rotation 8) as pointing to it. When frame C rotation 8 is needed, the engine renders the graphic horizontally flipped. This technique is the standard way to reduce sprite sheet sizes without losing visual detail (`src/r_data/sprites.cpp:361–362`).

Mirroring is most effective for frames where the left half mirrors the right half (walk cycles, idle stances, etc.). A 4-frame walk cycle can be compressed from 32 individual rotations (8 rotations × 4 frames) down to 16 or even fewer by mirroring across frame and rotation boundaries.

## Frame letter restriction in DECORATE

In a DECORATE `States{}` block, frame letters are references to these sprite frame indices, resolved at compile time. The state-machine page (`../../decorate/concepts/state-machine.md`) covers DECORATE's syntax for referencing frames; this page covers only the lump-naming encoding itself.

## Implementation details

- **Sprite lookup** (`src/r_data/sprites.cpp:339–365`): At startup, the engine scans all loaded lumps in the sprite namespace, groups them by their first 4 characters, and for each group extracts the frame letter (position 4) and rotation digit (position 5). If a 6th and 7th character are present, they're parsed as a secondary frame and rotation, and the lump is marked as flipped.
- **Rotation slot conversion** (`src/r_data/sprites.cpp:53–104`): The character at position 5 is converted to a rotation value:
  - `'0'` → 0 (non-rotating)
  - `'1'`–`'8'` → 1–8 (8-way, then mapped to even indices 0, 2, 4, ..., 14)
  - `'9'`–`'G'` → 9–16 (16-way, mapped to odd indices 1, 3, 5, ..., 15)
  - Any other character → 17 (invalid, rejected)
- **Frame index validation** (`src/r_data/sprites.cpp:66–70`): The frame index (position 4 minus `'A'`, giving 0–28 for A–]) must be less than 29; rotation must be ≤ 16. If violated, the lump is silently skipped with an error message.
- **Flip flag storage** (`src/r_data/sprites.cpp:87–90, 110–113`): Each frame's rotation slots carry a 16-bit flip mask (`sprtemp[frame].Flip`). When a lump is marked as flipped (positions 6–7 present), the corresponding bit is set.

## Open questions (unverified in this checkout — don't guess past these)

- **Frame letter quoting in DECORATE**: The ZDoom wiki states that if you use frame letters `[`, `\`, or `]` in a DECORATE state line, the frame string must be wrapped in quotes (e.g., `SPRITE "[" 4 A_SomeAction` instead of `SPRITE [ 4 A_SomeAction`). The 0–28 index range and mapping are verified in the source; this specific lexer requirement was not independently traced in the Zandronum checkout and should be verified against `src/sc_man.cpp` or `src/sc_man_scanner.re` if needed.

## Engine-family divergence

The lump-name format and rotation/frame encoding described above were checked against the UZDoom
source's `src/r_data/sprites.cpp` and found identical to Zandronum's: the same `XXXXYRD[FRD]`
seven/eight-character structure, the same 0–28 frame-letter range, and the same rotation-slot
arithmetic — an 8-way digit `1`–`8` still maps to the even internal slots via `(rotation-1)*2`,
and the 16-way extension `9`/`A`–`G` still maps to the odd slots via `(rotation-9)*2+1`, with the
same 0 (non-rotating, fills all slots) and out-of-range-rejects-as-invalid behavior. No extended or
GZDoom-family-only sprite-naming convention was found beyond what this page already documents; the
mechanism is shared, unmodified, ZDoom-family infrastructure that predates the Zandronum/UZDoom
split.
