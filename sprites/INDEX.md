# Sprites doc index

Router only. See `CLAUDE.md` for scope, `../shared/AUTHORING.md` for tiers/engine-scope/licensing.

## Concepts

- [Sprite naming and rotation encoding](concepts/sprite-naming.md) — tier A. The
  `XXXXYR[FR]` sprite lump name format (4-letter sprite identifier, frame letter, rotation
  digit, optional mirrored frame/rotation pair); rotation-count encoding (`0` = non-rotating,
  `1`–`8` = 8-way, `9`/`A`–`G` = 16-way, mapped to even/odd internal slot indices); and the
  automatic horizontal-flip mirroring syntax — all verified against the sprite-initialization
  code in `src/r_data/sprites.cpp`/`sprites.h`.
