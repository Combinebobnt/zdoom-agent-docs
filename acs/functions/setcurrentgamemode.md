# `int SetCurrentGamemode(str mode)`

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the Zandronum source's `src/p_acs.cpp:7516-7580`,
`src/gamemode.cpp:1390-1480`, `src/g_level.cpp:678-763` and `src/g_level.cpp:1234-1284`, plus
`zt-bcc/lib/zcommon.bcs:1765`. No secondary prose source exists: UltimateDoomBuilder's
`Zandronum_ACS.cfg` and SLADE's language files carry no entry for this function, and no wiki page
was consulted.
**Bucket:** extension function (index `-132`; dispatched as `ACSF_SetCurrentGamemode`).

Switches the server's game mode by name and immediately restarts the current map in the new mode.
Declared in `zt-bcc/lib/zcommon.bcs:1765` as `SetCurrentGamemode` (lowercase `m`). Some docs and
the Zandronum source's own comments spell it `SetCurrentGameMode`; ACS/BCS name lookup is
case-insensitive, so both call the same function. The inverse is
[GetCurrentGamemode](getcurrentgamemode.md), which returns the same names this function accepts.

## Parameters

- `mode` - a game mode name without the `GAMEMODE_` prefix. The engine prepends `GAMEMODE_`,
  upper-cases the result and looks it up with an exact string match against the `GAMEMODE_e`
  enum's element names (`p_acs.cpp:7522-7531`). So matching is case-insensitive, but the name
  must be the enum spelling, not the display name: `LastManStanding` and `TeamLMS` work,
  `Last Man Standing` or `LMS` do not. The 16 valid names are the ones listed in
  [GetCurrentGamemode](getcurrentgamemode.md): `Cooperative`, `Survival`, `Invasion`,
  `Deathmatch`, `Teamplay`, `Duel`, `Terminator`, `LastManStanding`, `TeamLMS`, `Possession`,
  `TeamPossession`, `TeamGame`, `CTF`, `OneFlagCTF`, `Skulltag`, `Domination`.

## Refusals (return `0`, nothing changes)

Checked in this order (`p_acs.cpp:7519-7570`):

1. **Called in client mode** (a clientside script on a network client), or while the game is in
   its **result sequence** (the end-of-match results screen). Only the server, or an offline
   game, can switch modes.
2. **Unknown name** (see Parameters).
3. **Already in that mode.** A call naming the current mode returns `0`, the same value as a real
   refusal, so a script cannot tell "no-op" from "refused" by the return value alone. Compare
   against `GetCurrentGamemode()` first if that distinction matters.
4. **The map is locked to a different mode** by its MAPINFO `gamemode` property
   (`p_acs.cpp:7538-7540`; see
   [Zandronum map-definition extensions](../../mapinfo/concepts/zandronum-map-extensions.md)).
   This check postdates 3.2.1 (see Version notes).
5. **The map has no spawn points for the target mode's type.** Which check applies follows the
   target mode's game-type flag from the `GAMEMODE` lump (see
   [The `GAMEMODE` lump](../../zandronum-lumps/concepts/gamemode.md)), not its name, so a mod that
   re-flags a mode changes which starts it needs:
   - `TEAMGAME` modes: refused if no team has any team starts (`TEAM_GetNumTeamsWithStarts() < 1`,
     so a single team with starts is enough to pass).
   - `DEATHMATCH` modes: refused if the map has no deathmatch starts. Additionally, switching to
     `Duel` is refused when `GAME_CountActivePlayers()` is greater than 2.
   - `COOPERATIVE` modes: refused if no player start (player 1 through the maximum) exists.

## What a successful switch does

1. `GAMEMODE_SetCurrentMode` runs immediately (`gamemode.cpp:1390-1480`): it sets the internal
   current mode, force-sets the mode cvars (`cooperative`, `deathmatch`, `teamgame` cleared, then
   the target mode's own cvar such as `ctf` or `survival` set), and resets the scoreboard. It also
   **clears the `instagib` and `buckshot` modifiers** unconditionally; nothing in this path turns
   them back on. `GetCurrentGamemode()` called later in the same script already reports the new
   mode.
2. It then calls `G_ChangeLevel` on the current map with `CHANGELEVEL_NOINTERMISSION`,
   `CHANGELEVEL_RESETHEALTH`, `CHANGELEVEL_RESETINVENTORY` and the engine-only
   `CHANGELEVEL_HIDENAME` (`p_acs.cpp:7578`; see [ChangeLevel](changelevel.md) for these flags).
   So every player's health and inventory are reset, and no intermission or level-name message
   is shown. Inside that call, `UNLOADING` scripts run synchronously and, on a server, clients are
   told the map is exiting (`g_level.cpp:756-763`). The reload itself is queued (`gameaction =
   ga_completed`, `g_level.cpp:737`) rather than performed inside the ACS call.
3. Returns `1`.

Clients pick up the new mode when they re-authenticate the reloaded map: the server sends each
client the current mode at that point (`sv_main.cpp:7051`, inside `server_AuthenticateLevel`).

**Two cases where the mode changes but the map is not reloaded.** `G_ChangeLevel` returns early
without queuing anything if it is called from an `UNLOADING` script (it prints "Unloading scripts
cannot exit the level again.") or if a level exit is already pending (`g_level.cpp:682-690`).
`SetCurrentGamemode` has already switched the mode by then and still returns `1`. In the
pending-exit case the new mode carries over to whatever map the pending exit loads, unless that
map's own MAPINFO `gamemode` lock overrides it on load (`g_level.cpp:1364-1365`).

**Offline campaign maps can undo the switch.** The reload goes through `G_DoLoadLevel`, which in
an offline game re-applies the map's `CMPGNINF` block, including its `gamemode` key, when one
exists for that map (`g_level.cpp:1234-1284`; campaign handling is disabled on servers and
clients, `campaign.cpp:180-185`). On such a map the call returns `1`, but the reloaded map comes
back in the campaign's mode. See [CMPGNINF](../../zandronum-lumps/concepts/cmpgninf.md).

**Example:**

```acs
script "SwitchToCTF" (void)
{
    if (StrIcmp(GetCurrentGamemode(), "CTF") == 0)
        terminate;

    if (!SetCurrentGamemode("ctf"))
        Log(s:"Could not switch to CTF on this map");
    // On success the map restarts: code after this point should not rely on the current level.
}
```

**Returns:** `int`. `1` if the mode was switched (and, in the normal case, a map restart queued);
`0` on any refusal listed above, including when the named mode is already active.

## Version notes

The function was added in commit `c487ff0a5` ("Added new ACS functions: SetGamemodeLimit()...
SetCurrentGamemode()... GetCurrentGamemode()..."), which is an ancestor of the 3.2.1
version-bump commit `28f736fb3` (checked with `git merge-base --is-ancestor`), so it exists in
Zandronum 3.2.1. The name-matching rewrite (`55259b91c1`), the automatic map reset
(`d1b8476b29`) and the `CHANGELEVEL_HIDENAME` flag on that reset (`1dde993e34`) are all
ancestors of `28f736fb3` too. The one exception is refusal 4, the MAPINFO `gamemode` lock check
(`p_acs.cpp:7538-7540`), added in `7aa633182` along with the MAPINFO property itself: that commit
postdates 3.2.1, so a 3.2.1 engine has neither the property nor this refusal.

## Engine-family divergence

UZDoom has no `SetCurrentGamemode`: no `ACSF_SetCurrentGamemode` case and no reference to the name
anywhere in its `src/` or `wadsrc/` trees. The function is bound as ACSF (CALLFUNC) index 132,
inside the 100-199 range UZDoom's ACSF enum reserves for Zandronum's extensions without
implementing any of them (`tools/engine_matrix.py SetCurrentGamemode`, bin
`zandronum-only-silent`). A Zandronum-compiled object calling it under UZDoom gets a silent `0`:
no error, no log line, and nothing switches. Because `0` is also this function's refusal value, a
script that checks the return reads the UZDoom case as an ordinary refusal. See
[Zandronum/UZDoom compatibility](../concepts/zandronum-uzdoom-compat.md) for the general
mechanism.
