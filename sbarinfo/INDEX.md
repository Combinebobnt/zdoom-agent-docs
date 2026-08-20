# SBARINFO doc index

Router only. See `AGENTS.md` for where SBARINFO parsing lives in engine source,
`../shared/AUTHORING.md` for tiers/engine-scope/licensing.

## Concepts

- [SBARINFO lump format overview](concepts/sbarinfo-lump-overview.md) — tier A. **SBARINFO is
  deprecated in UZDoom/GZDoom-family in favor of ZScript-based status bars, but remains the primary
  and only custom HUD mechanism in Zandronum**, which has no ZScript to deprecate it in favor of;
  multiplayer-safe lump format for status bars and mugshot animations. Multiple SBARINFO lumps are
  merged (not last-only); `#include` is supported. Zandronum adds `IfSpectator`/`IfSpying`
  conditionals not on the wiki; the wiki lists `IfCVarInt`/`IfInvulnerable`/`IfWaterLevel` which
  don't exist in Zandronum. No `StatusBarClass` MAPINFO key exists (ZScript doesn't exist in this
  fork).

## Inventory tables (generated)

_None yet — no extractor exists yet._

## Notes (curated, per key)

_None yet._
