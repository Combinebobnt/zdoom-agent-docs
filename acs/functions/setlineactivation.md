# `void SetLineActivation(int lineid, int activation [, int repeat])`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** wiki page `SetLineActivation - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`https://zdoom.org/w/index.php?title=SetLineActivation&oldid=49566`) + source-verified against the Zandronum source's `p_acs.cpp:6814-6832`, `p_spec.cpp:333-336`, `gamemode.cpp:1130-1168`, `network.cpp:1616-1619` and
`zt-bcc/lib/zcommon.bcs:784-795,1705-1706`. The wiki's signature, `lineid`/`activation` semantics,
overwrite-not-OR behavior, and `GetLineActivation`-based read-modify-write workaround all hold
exactly against Zandronum's source. The `repeat` parameter being a complete no-op in Zandronum,
and the absence of any client/server sync call, are this doc's source-verified additions — not
mentioned (and, for `repeat`, actively contradicted) by the ZDoom wiki page.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function.

Sets the line activation flags (`SPAC_*`) of every line matching `lineid`. Extension function
(negative index `-76` in `zt-bcc/lib/zcommon.bcs`'s `special` table, `ACSF_SetLineActivation`),
semantics in the Zandronum source's `src/p_acs.cpp` (`case ACSF_SetLineActivation:`, line 6814).

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
  the Zandronum engine fork (`GetLineActivation` is `ACSF_GetLineActivation`, `p_acs.cpp:6826`, a
  plain read of the same field via the same `P_FindLineFromID` lookup, first match only).
- **`repeat` is accepted by the compiler but is completely ignored by the Zandronum engine fork's
  implementation — it does nothing, regardless of value.** The wiki describes it as controlling
  whether the line's action special can re-trigger (`>0` repeatable, `0` once-only, `<0`/default
  `-1` no change), which is real *upstream* behavior gated on the line's `ML_REPEAT_SPECIAL` flag.
  But in the Zandronum source, `ACSF_SetLineActivation`'s case block only ever reads `args[0]` and
  `args[1]` (guarded by `argCount >= 2`, `p_acs.cpp:6815`) — there is no `args[2]` read anywhere in
  the case, and `ML_REPEAT_SPECIAL` is referenced nowhere in `p_acs.cpp` at all. The flag is only
  ever set by map-load code (`p_udmf.cpp`, `p_xlat.cpp`, and the compatibility table's line-flag
  fixes). `P_ActivateLine` reads it at `p_spec.cpp:317`, and a few other places read it too.
  `Line_SetBlocking`'s flag table (`p_lnspec.cpp:2837-2850`) doesn't include it. Passing a
  third argument compiles cleanly (the `zcommon.bcs` signature has it as an optional trailing
  param) and has zero runtime effect — no error, no partial application, just silently dropped.
  Anyone porting ZDoom-wiki-era BCS that relies on the `repeat` argument to toggle repeatability
  needs a different mechanism in the Zandronum engine fork. No ACS call changes the flag itself.
  The closest substitute: a once-only line's special is cleared after it fires successfully
  (`p_spec.cpp:333-336`), so re-setting it with `SetLineSpecial` re-arms the line.
- **No Zandronum client/server sync call for this function** (no `SERVERCOMMANDS_*` call in
  either `ACSF_SetLineActivation` or `ACSF_GetLineActivation`, unlike e.g. `ChangeCeiling`'s
  `SERVERCOMMANDS_SetSectorFlat`). Most line specials only fire on the server
  (`P_ActivateLine`/`P_TestActivateLine`, `p_spec.h:180-181`), so the server's copy is what gates
  them. But clients do read `activation` locally. `P_ActivateLine` runs on clients too, and
  `GAMEMODE_IsHandledSpecial` (`gamemode.cpp:1137-1168`) lets the local player predict
  `ThrustThing`/`ThrustThingZ` lines (`network.cpp:1616-1619`) and lets spectators use teleport
  lines (`gamemode.cpp:1130-1133`), both through `P_TestActivateLine`'s activation check. The
  automap also colors trigger and teleporter lines from it (`am_map.cpp:2310`, `2358`). Since
  nothing is sent and clients don't run the server's script, a client keeps the map-load value
  unless a `CLIENTSIDE` script makes the same call on that client.

## Engine-family divergence: `repeat` parameter is implemented, unlike the Zandronum engine fork

The description above of `repeat` being a complete no-op is specific to the Zandronum engine
fork. In UZDoom's `ACSF_SetLineActivation` case, the third argument is read and acted on: when a
value is supplied and is greater than zero, every matching line has its "repeatable special"
flag set; when the value is exactly zero, that flag is cleared instead; and when the argument is
omitted (or negative, matching the wiki's documented `-1` default), the flag is left untouched.
This is exactly the upstream ZDoom-wiki-documented behavior the original doc's "repeat" bullet
describes as *not* holding in the Zandronum engine fork — it does hold on UZDoom. The line-id matching, silent
zero-match no-op, and the unmasked direct overwrite of `activation` all still behave the same as
described above; only the `repeat` argument's effect differs.

Net effect: a script written against the ZDoom wiki's documented `repeat` semantics is inert on
Zandronum (per this doc's Zandronum-verified behavior above) but works as documented on UZDoom.
Anyone porting BCS between the two engine families should not rely on `repeat` doing anything on
Zandronum, and should not assume it's safe to omit tracking repeatability separately when
targeting both.

**Example (wiki's, unchanged — still holds for the flag-overwrite semantics on both engines; the
`repeat` argument, if a caller adds one, is inert on the Zandronum engine fork but functions as
documented on UZDoom per the divergence above):**

```text
script "Example" (void)
{
    SetLineActivation(1, SPAC_PUSH);
}
```
