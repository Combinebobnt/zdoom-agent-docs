# LOCKDEFS doc index

Router only. See `AGENTS.md` for scope and source locations, `../shared/AUTHORING.md` for
tiers/engine-scope/licensing.

**Both engines parse LOCKDEFS.** Key item classes are documented in
`../decorate/classes/key.md`; the lock-taking line specials are tier-C rows in `../acs/INDEX.md`.

## Concepts

- [The LOCKDEFS lump](concepts/lockdefs-lump.md) — tier A. `Lock <number> [game] { ... }` and
  `ClearLocks`; bare key names (all required) and `Any { }` groups (one of); `Message`,
  `RemoteMessage`, `Mapcolor`, `LockedSound`; what the stock lump defines per game and the xlat
  numbering scheme behind it; unknown bare key names silently skipped (an empty lock opens with any
  key); Zandronum's 1-254 lock range and "above 255 is unlocked" versus UZDoom's unbounded map.
