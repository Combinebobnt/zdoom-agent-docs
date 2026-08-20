# `void SetActorAngle(int tid, fixed angle)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `SetActorAngle - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29, `https://zdoom.org/w/index.php?title=SetActorAngle&oldid=36012`) + source-verified against `p_acs.cpp:5839-5867, 4445-4453, 12594-12597`, `p_mobj.cpp:3941-3951`, and `zt-bcc/src/builtin.c:133`. The angle-encoding table and `fixed` parameter typing both check out against source with no wiki/fork divergence found; the multi-actor-vs-single-actor TID asymmetry with `GetActorAngle`, the always-`false` interpolate flag, and the server-to-client angle broadcast are real fork/engine details the wiki doesn't mention, recorded above.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.

Sets the facing angle of actor(s) by TID. Compiler builtin (`PCD_SETACTORANGLE`,
the Zandronum source's `src/p_acs.cpp:12594-12597`), implementation in the file-local
`SetActorAngle(AActor*, int, int, bool)` helper (`p_acs.cpp:5839-5867`), which the ACS case calls
with `interpolate` hardcoded to `false`.

- `angle` — a **fixed-point fraction of a full turn** (`0.0`-`1.0`), the same encoding as
  `GetActorAngle`/`Sin`/`Cos`/`VectorAngle` — see
  [units-and-encodings.md](../concepts/units-and-encodings.md). The wiki's `North=0.25`,
  `West=0.5`, `South=0.75`, `East=1.0` (`0.0`) table checks out against source: the helper does
  `activator->SetAngle(angle << 16, interpolate)`, and `angle` here is the raw ACS 16.16 fixed
  value (`1.0` = `65536`), so left-shifting 16 more places lands it in the engine's 32-bit BAM
  space (`angle_t`, full turn = `2^32`) at exactly the same fraction — `0.25` (`16384`) becomes
  `0x40000000`, a quarter turn. No divergence from the wiki here, unlike some other angle
  builtins in Zandronum (`Sin`/`VectorAngle`) where the wiki mistypes the parameter as `int`; the
  wiki's `SetActorAngle` signature already says `fixed`, and `builtin.c:133`
  (`{ "setactorangle", ";if" }`, void return, one int, one fixed) agrees.
- `tid` — **`0` means "the activator"**, applied directly and **guarded**: if `tid == 0` and
  `activator == NULL` (e.g. called from a script with no activator), the call is a silent no-op,
  not a crash (`p_acs.cpp:5841-5851`).
- **A nonzero `tid` sets the angle on *every* actor sharing that TID**, not just one — the
  helper loops a full `FActorIterator` (`p_acs.cpp:5852-5866`). This is the same read/write
  asymmetry already documented for `SetActorProperty`/`GetActorProperty`
  (`functions/setactorproperty.md`): `GetActorAngle` reads only the *first* actor matching a TID
  (`SingleActorFromTID`, one `iterator.Next()` call, `p_acs.cpp:4445-4453`), while
  `SetActorAngle` on the same nonzero TID mutates all of them in one call. In projects where a TID
  is deliberately shared across many actors, that's a real thing to keep in
  mind — not a bug, just easy to assume symmetric with the getter and get wrong.
- **`interpolate` is always `false` from ACS** — the underlying `AActor::SetAngle(angle_t, bool)`
  (`p_mobj.cpp:3941-3951`) only uses `interpolate` to set `CF_INTERPVIEW` on a player's view when
  `true`; since the ACS opcode never passes `true`, an ACS-driven angle change on a player pawn
  snaps instantly rather than smoothly panning the view, even though the C++ function itself
  supports smoothing for other (non-ACS) callers.
- **Zandronum multiplayer sync**: when the calling side is the server (`NETWORK_GetState() ==
  NETSTATE_SERVER`), each affected actor's new angle is broadcast to clients via
  `SERVERCOMMANDS_SetThingAngleExact` (`p_acs.cpp:5848-5849, 5863-5864`) — a Zandronum-specific
  netcode detail with no equivalent on the (single-player-oriented) wiki page.

## Example (from the wiki)

```acs
script 1 (int spintime)
{
    while (spintime-- > 0)
    {
        SetActorAngle (100, GetActorAngle (100) - 0.02);
        Delay (1);
    }
}
```
