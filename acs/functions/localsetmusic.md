# `void LocalSetMusic(str song [, int order [, int unused]])`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `LocalSetMusic - ZDoom Wiki` (https://zdoom.org/w/index.php?title=LocalSetMusic&oldid=35967), verified 2026-07-29 against fork source.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.

Changes the background music, but only for the script's activator — unlike `SetMusic`, which 
broadcasts the change to all players and persists it for late-joining clients. Compiler builtin 
(`PCD_LOCALSETMUSIC`, the zt-bcc source's `src/builtin.c:184,307`), implementation in 
`p_acs.cpp:1433-1451`.

- `song` — a string containing the music lump name, looked up via `FBehavior::StaticLookupString`
  (`p_acs.cpp:1437, 1442`). An invalid string index silently no-ops. The special value `"*"` 
  restores the current map's default music as defined in MAPINFO, per the wiki.
- `order` — applies only to tracker-format music (MOD/XM/etc.); specifies the starting pattern 
  order in the song. For non-tracker formats (MP3/OGG/MID), this parameter is ignored. Optional; 
  defaults to `0` if omitted.
- `unused` — the third parameter (`int unused`) is declared in the signature but never read by 
  the engine, per the wiki. The wiki recommends omitting it entirely as it may be repurposed in 
  future versions.
- **Activator-specific delivery:** the music change is only heard by `activator` — not broadcast 
  to all players like `SetMusic` (`p_acs.cpp:1442-1444`). The check is `if (activator == 
  players[consoleplayer].mo)`: the change only applies locally if the executing machine's 
  `consoleplayer` *is* the activator. In multiplayer, each connected client only hears the change 
  if they are the activator.
- **Zandronum netcode addition not in the ZDoom wiki's model:** when running as a network server 
  (`NETWORK_GetState() == NETSTATE_SERVER`), the server additionally sends the music change to 
  the activator's client with `SERVERCOMMANDS_SetMapMusic(..., activator->player - players, 
  SVCF_ONLYTHISCLIENT)` (`p_acs.cpp:1435-1440`) — explicitly targeting only that one client. 
  This send is gated on `activator && activator->player` (bots/non-player activators receive no 
  network packet). Vanilla ZDoom has no per-client targeting mechanism; this is purely 
  Zandronum-specific to keep the music genuinely local in multiplayer.
- **`activator == NULL` behavior:** the wiki does not document what happens if called from a 
  script with no activator (e.g. an `OPEN` script). The code guards the network send on `activator 
  && activator->player`, but the local `S_ChangeMusic` call checks `activator == 
  players[consoleplayer].mo`. If there's no activator, this condition can never be true on any 
  player's machine, so the function silently no-ops everywhere — no crash, no network send. This 
  matches the defensive pattern used in `functions/localambientsound.md` for similar 
  activator-dependent functions.
- **Non-persistent:** unlike `SetMusic`, which also calls `SERVER_SetMapMusic` to save the 
  selection for late joiners, `LocalSetMusic` does not persist. A new client joining the game 
  still hears the *level's* default music (from MAPINFO), not the private music any prior player 
  set via `LocalSetMusic`. This is the key differentiator from `SetMusic` and is implicit in the 
  implementation (`SVCF_ONLYTHISCLIENT` is a send-only flag; there is no persistent state 
  update).
- **Sibling comparison:** `SetMusic` (`p_acs.cpp:1418-1431`) broadcasts to all clients and calls 
  `SERVER_SetMapMusic` to persist the change. `LocalSetMusic` is a fully separate `case` block 
  that sends only to the activator's client (or doesn't send at all if server-side `activator` is 
  null), and makes no persistence call. The wiki's framing ("only affects the player who activated 
  the script") is accurate and matches the code.
- **Likely causes a small hitch on the receiving client.** The `SetMapMusic` network command's
  handler (`ServerCommands::SetMapMusic::Execute()`, `cl_main.cpp:7534` — shared with `SetMusic`,
  distinguished only by the `SVCF_ONLYTHISCLIENT` targeting) calls `S_ChangeMusic()` directly and
  synchronously, with no background/async loading. Inside `S_ChangeMusic` (`s_sound.cpp:2572`), a
  compressed lump is fully read and decompressed into a scratch buffer (`Wads.ReadLump` into
  `musiccache`) before `I_RegisterSong()` parses/initializes the music backend — all inline in the
  same tic the client processes the packet, with no yield back to the render loop in between. A
  large or compressed music lump can therefore produce a visible frame stall for the activating
  player right as the change takes effect; this is local decode/IO cost, not network latency, and
  applies equally to `SetMusic` for every connected client.

**Example:**

```text
script 1 OPEN
{
    if (PlayerNumber() == 0) {
        LocalSetMusic("D_DOOM");  // only player 0 hears this music change
    }
}
```

```text
script 2 RESPAWN
{
    LocalSetMusic("*");  // restore the default map music for this activator only
}
```
