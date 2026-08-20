# `bool CheckActorProperty(int tid, int property, raw value)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-30)
**Provenance:** wiki page `CheckActorProperty - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-30, `https://zdoom.org/w/index.php?title=CheckActorProperty&oldid=36602`) + source-verified against `p_acs.cpp:5020-5086`/`6101`, `zcommon.bcs:266-314`. Verified that the 42-property switch is identical to `GetActorProperty`'s supported set; wiki's 8 additional properties checked individually and confirmed unimplemented (7 compile-but-dead in `zcommon.bcs`, 1 absent entirely). String-property NULL-handling risk cross-referenced against crash checklist.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function.

Compares an actor property against a given value, with special handling for string and boolean properties. Extension function (index -22, `ACSF_CheckActorProperty` at `src/p_acs.cpp:6101`), implementation in `DLevelScript::CheckActorProperty` (`p_acs.cpp:5020-5086`).

## Parameters

- `tid` — actor's thing ID. **`0` means "the activator"** (same convention as `GetActorProperty`). If the TID doesn't resolve to an actor, returns `0` (indistinguishable from a value mismatch).
- `property` — one of the `APROP_*` constants named in the zt-bcc source's `lib/zcommon.bcs:266-314`. Same enum as `GetActorProperty`; see that doc for the full list of 42 supported properties.
- `value` — the value to compare against. Untyped (`raw`), because the same function accepts `int`, `fixed`, and string-table-index arguments depending on which property is being checked. This hides real type distinctions until runtime.

## Behavior differences from `GetActorProperty`

### String property comparisons are **case-insensitive**

For `APROP_SEESOUND`, `APROP_ATTACKSOUND`, `APROP_PAINSOUND`, `APROP_DEATHSOUND`, `APROP_ACTIVESOUND`, `APROP_SPECIES`, and `APROP_NAMETAG`, comparisons use `stricmp` (case-insensitive, line 5085), not strict equality. An actor with no sound set (e.g., a `SeeSound` of `NULL`) compares equal to the empty string `""` (line 5084 protects the first operand; if the actor's sound field is NULL, it's substituted with `""`).

### Boolean properties normalize the operand via `!!` (double-negation)

For `APROP_AMBUSH`, `APROP_INVULNERABLE`, `APROP_DROPPED`, `APROP_CHASEGOAL`, `APROP_FRIGHTENED`, `APROP_FRIENDLY`, `APROP_NOTARGET`, `APROP_NOTRIGGER`, and `APROP_DORMANT`, the comparison is `GetActorProperty(...) == (!!value)` (line 5072). Any nonzero `value` argument means "true", so `CheckActorProperty(tid, APROP_AMBUSH, 5)` returns true if the flag is set — the operand is normalized to a boolean first. Getting this wrong is a common source of logic bugs in boolean flag checks.

### Return value

Returns `true` (nonzero) if the property value matches, `false` (zero) otherwise. **No distinction** between three false cases: the TID didn't resolve to an actor, the property wasn't handled by the switch, or the value genuinely didn't match — all three return `0`.

## Wiki/engine divergence: properties not supported by Zandronum

The ZDoom wiki lists **8 additional `APROP_*` constants** that the Zandronum engine fork does **not** implement in the engine switch:

- **7 properties compile in `zcommon.bcs` but have no engine-side implementation** (lines 308-314 of `lib/zcommon.bcs`) and silently return `0` at runtime: `APROP_FRICTION`, `APROP_DAMAGEMULTIPLIER`, `APROP_MAXSTEPHEIGHT`, `APROP_MAXDROPOFFHEIGHT`, `APROP_DAMAGETYPE`, `APROP_SOUNDCLASS`, `APROP_FRIENDLYSEEBLOCKS`. These are exactly the same seven dead names documented for `GetActorProperty`.
- **1 property is not defined anywhere in the zt-bcc compiler fork**: `APROP_WATERDEPTH` does not appear in `zcommon.bcs` at all and will not compile.

Treat these eight names as unusable on Zandronum despite the first seven compiling without warnings. See [GetActorProperty](getactorproperty.md) for the full explanation — Zandronum shares a frozen ZDoom baseline and doesn't ship every later ZDoom feature. **See the "Engine-family divergence" section below — most of these are live on UZDoom.**

## Engine-family divergence: property coverage

UZDoom's `CheckActorProperty` (`src/playsim/p_acs.cpp:4473-4545`) covers a materially larger `APROP_*` set than Zandronum's. Of the 8 wiki-listed properties documented above as unsupported on Zandronum, 6 are live on UZDoom:

- `APROP_MAXSTEPHEIGHT`, `APROP_MAXDROPOFFHEIGHT`, and `APROP_FRIENDLYSEEBLOCKS` are handled in the plain-integer-equality group, alongside the properties already documented as supported.
- `APROP_DAMAGETYPE` and `APROP_SOUNDCLASS` are handled in the case-insensitive string-comparison group — UZDoom compares **9** string properties this way (the 7 documented above, plus these two), not 7.
- `APROP_WATERDEPTH` is defined in UZDoom's engine-side `APROP_*` enum and handled in the integer-equality group, but **zt-bcc's `lib/zcommon.bcs` still does not declare an `APROP_WATERDEPTH` constant at all** (confirmed absent from the same `zcommon.bcs:266-314` range cited above) — the same compiler serves both engine targets, so a BCS script still cannot reference this property by name on either engine; it's only reachable by passing the raw integer literal in its place.

Only `APROP_FRICTION` and `APROP_DAMAGEMULTIPLIER` remain genuinely unimplemented in UZDoom's `CheckActorProperty` switch (both fall through to the `default: return 0` case) — the same "compiles but dead" status as on Zandronum.

The core mechanics documented above are unchanged on UZDoom: plain-integer equality for the straightforward properties, boolean `!!`-normalization for the same 9 flag properties (`APROP_AMBUSH`/`APROP_INVULNERABLE`/`APROP_DROPPED`/`APROP_CHASEGOAL`/`APROP_FRIGHTENED`/`APROP_FRIENDLY`/`APROP_NOTARGET`/`APROP_NOTRIGGER`/`APROP_DORMANT`), and case-insensitive string comparison with the first operand NULL-guarded (substituted with `""`) but the second (the caller-supplied string-table lookup) left unguarded — see "Crash risk" below, which applies identically on UZDoom. Only the property-coverage set differs.

## Crash risk with invalid string handles

**If a script passes a plain `int` where a string property expects a string-table index** (e.g., `CheckActorProperty(tid, APROP_SPECIES, 5)` — legal because `value` is untyped `raw`) **the second argument to `stricmp` at line 5085 may be NULL**, causing undefined behavior. The engine's `FBehavior::StaticLookupString` returns NULL for invalid indices (line 3328 of `src/p_acs.cpp`), but CheckActorProperty does not guard against it before passing the result to `stricmp`. The first argument is protected (substituted with `""` if NULL, line 5084), but the second is not. For string properties, always pass a valid string-table index (returned by `StrParam()` or another string function), never a bare integer. **This is the same "raw int misused as a string-table index" pattern listed in the [crash-and-bug-checklist](../concepts/crash-and-bug-checklist.md).**

## Examples

**Check if an actor's health is above a threshold:**

```text
if (CheckActorProperty(tid, APROP_HEALTH, 50))
{
    Log(s: "Actor has health >= 50");
}
```

**Check if an actor belongs to a specific species (case-insensitive):**

```text
int species_idx = StrParam(s: "DoomImp");
if (CheckActorProperty(tid, APROP_SPECIES, species_idx))
{
    Log(s: "Actor is a DoomImp");
}
```

**Check a boolean flag (any nonzero value means "true"):**

```text
if (CheckActorProperty(tid, APROP_FRIENDLY, 1))
{
    Log(s: "Actor is friendly");
}
```
