# `void SectorSound(str sound, int volume)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** `SectorSound - ZDoom Wiki` (https://zdoom.org/w/index.php?title=SectorSound&oldid=35965), verified 2026-07-29 against fork source.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.

Plays a sound anchored to the sector of the linedef that activated the current script — not to
any actor or TID. Compiler builtin (`PCD_SECTORSOUND`, signature `;si` in
the zt-bcc source's `src/builtin.c:50,198`), implementation in `DLevelScript::RunScript`'s big switch,
the Zandronum source's `src/p_acs.cpp:11327-11358`.

- `sound` — looked up via `FBehavior::StaticLookupString(STACK(2))`. If the string doesn't
  resolve, `lookup` is `NULL` and the **entire block is skipped** (`p_acs.cpp:11329`) — a bad
  string index is a silent no-op, same failure behavior as `PlaySound`/`PlayActorSound`, not an
  error.
- `volume` — read as a raw int and divided by `127.f` (`p_acs.cpp:11337/11349`) to get the float
  volume passed to `S_Sound`. The opcode itself doesn't clamp it, but the sound engine does
  downstream. `S_StartSound` plays nothing when the volume is 0 or negative (Zandronum
  `src/s_sound.cpp:901`), so a negative value is silent. It then caps the volume times the sound's
  SNDINFO `$volume` at 1.0 (`s_sound.cpp:954`). So a value above 127 is no louder than 127, except
  for a sound whose SNDINFO `$volume` is below 1.0, where it can make up the difference. UZDoom's
  sound engine applies the same two checks.
- **Sector targeting depends on `activationline`, and this is the load-bearing gap the wiki
  doesn't cover at all:**
  - If the script has an `activationline` (i.e. it was triggered by a player/thing crossing or
    using a line with a `ACS_Execute`-family special — the wiki's only documented case), the sound
    plays via `S_Sound(activationline->frontsector, CHAN_AUTO, lookup, vol, ATTN_NORM)`
    (`p_acs.cpp:11333-11338`) — always the line's **front** sector, regardless of which side was
    actually crossed/used.
  - A script started from another script with an `ACS_Execute`-family special or an `ACS_Named*`
    function inherits the caller's `activationline` (the special is run with the calling script's
    line, Zandronum `p_acs.cpp:9334` onward and `6352-6354`, which `p_lnspec.cpp:1781`/`1812` pass
    on to `P_StartScript`). So a chained script still has a line if the chain began at one.
  - If there is **no** `activationline` (e.g. the calling script is an `OPEN`/`ENTER`/`RESPAWN`
    script, was started by `puke` or by a thing's special, or was chained from such a script), the
    engine falls back to a **global, non-sector `S_Sound(CHAN_AUTO, lookup, vol, ATTN_NORM)`**
    call (`p_acs.cpp:11344-11350`) with no sector origin at all. The wiki's description ("plays a
    sound in the sector that the line the script is attached to faces") implicitly assumes a line
    always exists and says nothing about this fallback — calling `SectorSound` from a non-line
    script still works, it just degrades to an origin-less global sound instead of erroring.
- `channel` is always `CHAN_AUTO` in both branches — not user-settable, and not mentioned by the
  wiki (which has no channel parameter for this function, correctly).
- `attenuation` is always `ATTN_NORM` in both branches, consistent with the wiki's "point sound...
  anyone far away will not hear it as loudly."
- Zandronum-specific: when running as a server, both branches additionally replicate the sound to
  clients — `SERVERCOMMANDS_SoundSector(...)` for the sector case, `SERVERCOMMANDS_Sound(...)` for
  the fallback case (`p_acs.cpp:11341-11342`, `11352-11354`) — netcode plumbing the ZDoom wiki
  naturally doesn't and can't describe. Both commands carry the volume as a `Byte`
  (`protocolspec/spec.sounds.txt`): the server sends the float clamped to 0-2 times 127
  (`src/sv_commands.cpp:3694`), and the client caps it at 127 before dividing
  (`src/cl_main.cpp:7247-7248`). So clients never get the above-127 headroom on a quiet SNDINFO
  sound that the server or an offline game does.

**Example (from the wiki, still accurate for the line-triggered case):**

```text
script 1 (void)
{
    SectorSound("world/creak1", 127);
}
```
Triggered by a linedef special (e.g. `ACS_Execute`, "Player Crosses Line") — plays in that line's
front sector.
