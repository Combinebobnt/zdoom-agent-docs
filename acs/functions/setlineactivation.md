# `void SetLineActivation(int lineid, int activation [, int repeat])`

Sets the line activation flags (`SPAC_*`) of every line matching `lineid`. Extension function
(negative index `-76` in `zt-bcc/lib/zcommon.bcs`'s `special` table, `ACSF_SetLineActivation`),
semantics in the Zandronum source's `src/p_acs.cpp` (`case ACSF_SetLineActivation:`, line 6814).

**Bucket:** extension function.

- `lineid` — a line ID (not a linedef index), resolved via `P_FindLineFromID(args[0], line)`
  looped until exhausted (`p_acs.cpp:6819`) — same tag-loop pattern as `ChangeCeiling`/
  `ChangeFloor`. **Every** line sharing that ID gets its activation flags overwritten, and zero
  matches is a silent no-op (no console message, no error).
- `activation` — a bitmask of `SPAC_*` constants (`SPAC_NONE=0x0`, `SPAC_CROSS=0x1`,
  `SPAC_USE=0x2`, `SPAC_MCROSS=0x4`, `SPAC_IMPACT=0x8`, `SPAC_PUSH=0x10`, `SPAC_PCROSS=0x20`,
  `SPAC_USETHROUGH=0x40`, `SPAC_ANYCROSS=0x80`, `SPAC_MUSE=0x100`, `SPAC_MPUSH=0x200`,
  `SPAC_USEBACK=0x400` — all present in `zt-bcc/lib/zcommon.bcs:784-795`, usable from BCS as-is).
  The engine performs a **direct, unmasked overwrite** — `lines[line].activation = args[1];`
  (`p_acs.cpp:6821`) replaces the line's entire `DWORD activation` field with whatever raw int is
  passed, no validation against the known `SPAC_*` bits. This matches the wiki's own caveat that
  calling this clears any flags not included in the new value — confirmed exactly, since it's a
  plain assignment rather than an OR. To add a flag without losing existing ones, the wiki's
  `SetLineActivation(1, GetLineActivation(1) | SPAC_PUSH)` pattern is the only way, and holds in
  this fork (`GetLineActivation` is `ACSF_GetLineActivation`, `p_acs.cpp:6826`, a plain read of
  the same field via the same `P_FindLineFromID` lookup, first match only).
- **`repeat` is accepted by the compiler but is completely ignored by this fork's engine
  implementation — it does nothing, regardless of value.** The wiki describes it as controlling
  whether the line's action special can re-trigger (`>0` repeatable, `0` once-only, `<0`/default
  `-1` no change), which is real *upstream* behavior gated on the line's `ML_REPEAT_SPECIAL` flag.
  But in the Zandronum source, `ACSF_SetLineActivation`'s case block only ever reads `args[0]` and
  `args[1]` (guarded by `argCount >= 2`, `p_acs.cpp:6815`) — there is no `args[2]` read anywhere in
  the case, and `ML_REPEAT_SPECIAL` is referenced nowhere in `p_acs.cpp` at all (only read at
  `p_spec.cpp:317`, from the line's static level-data flags, never written from ACS). Passing a
  third argument compiles cleanly (the `zcommon.bcs` signature has it as an optional trailing
  param) and has zero runtime effect — no error, no partial application, just silently dropped.
  Anyone porting ZDoom-wiki-era BCS that relies on the `repeat` argument to toggle repeatability
  needs a different mechanism in this fork (there does not appear to be one exposed to ACS at
  all — repeatability is set from the linedef's flags at map-load time only).
- **No Zandronum client/server sync call for this function** (no `SERVERCOMMANDS_*` call in
  either `ACSF_SetLineActivation` or `ACSF_GetLineActivation`, unlike e.g. `ChangeCeiling`'s
  `SERVERCOMMANDS_SetSectorFlat`). This is consistent rather than a bug: activation flags gate
  whether an action special *fires* at all, which is evaluated authoritatively server-side
  (`P_ActivateLine`/`P_TestActivateLine`, `p_spec.h:180-181`) — there's no client-visible state to
  keep in sync, unlike a texture change which clients must render.

**Example (wiki's, unchanged — still holds since the flag-overwrite semantics are unchanged; the
`repeat` argument, if a caller adds one, would simply be inert):**

```
script "Example" (void)
{
    SetLineActivation(1, SPAC_PUSH);
}
```

**Provenance:** wiki page `SetLineActivation - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`oldid=49566`) + source-verified against the Zandronum source's `p_acs.cpp:6814-6832` and
`zt-bcc/lib/zcommon.bcs:784-795,1705-1706`. The wiki's signature, `lineid`/`activation` semantics,
overwrite-not-OR behavior, and `GetLineActivation`-based read-modify-write workaround all hold
exactly against this fork's source. The `repeat` parameter being a complete no-op in this fork,
and the absence of any client/server sync call, are this doc's source-verified additions — not
mentioned (and, for `repeat`, actively contradicted) by the ZDoom wiki page.
**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.
