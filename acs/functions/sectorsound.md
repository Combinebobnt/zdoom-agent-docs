# `void SectorSound(str sound, int volume)`

**Tier:** A
**Engine:** Zandronum 3.2.1 (checked out source reports 3.3-alpha; `PCD_SECTORSOUND` is long-standing Hexen-era ACS, not a netcode-gated addition, so this is not expected to be version-sensitive).
**Provenance:** `SectorSound - ZDoom Wiki` (https://zdoom.org/w/index.php?title=SectorSound&oldid=35965), verified 2026-07-29 against fork source.
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
  volume passed to `S_Sound`. **Not clamped** either direction: the wiki's documented 0–127 range
  is a convention, not an enforced bound — passing >127 yields a float volume >1.0, and a negative
  value passes straight through as a negative float. The wiki doesn't mention this.
- **Sector targeting depends on `activationline`, and this is the load-bearing gap the wiki
  doesn't cover at all:**
  - If the script has an `activationline` (i.e. it was triggered by a player/thing crossing or
    using a line with a `ACS_Execute`-family special — the wiki's only documented case), the sound
    plays via `S_Sound(activationline->frontsector, CHAN_AUTO, lookup, vol, ATTN_NORM)`
    (`p_acs.cpp:11333-11338`) — always the line's **front** sector, regardless of which side was
    actually crossed/used.
  - If there is **no** `activationline` — e.g. the calling script is an `OPEN`/`ENTER`/`RESPAWN`
    script, or was reached via a non-line path like `ACS_ExecuteAlways` from another script — the
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
  naturally doesn't and can't describe.

**Example (from the wiki, still accurate for the line-triggered case):**

```
script 1 (void)
{
    SectorSound("world/creak1", 127);
}
```
Triggered by a linedef special (e.g. `ACS_Execute`, "Player Crosses Line") — plays in that line's
front sector.
