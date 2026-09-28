# Team-game items: TeamItem, Flag, WhiteFlag, Skull, ReturnZone

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** engine source only. The Zandronum source's `wadsrc/static/actors/Skulltag/skulltagteamitems.txt` (all), `wadsrc/static/actors/Skulltag/skulltagmisc.txt:153` (`ReturnZone`), `wadsrc/static/actors/Skulltag/skulltagscorepillars.txt` (`HellScorePillar`, the Heretic skulls), `wadsrc/static/teaminfo.txt`, `wadsrc/static/gamemode.txt:168-213`; `src/g_shared/a_sharedglobal.h:203-255`, `src/g_shared/a_teamitems.cpp` (all), `src/g_shared/a_returnzone.cpp:56-72`, `src/actor.h:404`, `src/thingdef/thingdef_data.cpp:263`, `src/gamemode_enums.h:64,75`; `src/team.cpp` (`TEAM_Tick` 118-132, `TEAM_Reset` 136-169, `TEAM_ExecuteReturnRoutine` 235-305, `TEAM_ShouldUseTeam` 1367-1376, `TEAM_ScoreSkulltagPoint` 435-515, `TEAM_GetItem` 1010-1020, `TEAM_FindOpposingTeamsItemInPlayersInventory` 1038-1057, `TEAM_GetTeamFromItem` 1489-1498, `sv_flagreturntime` 2161), `src/teaminfo.cpp:74-91,103-118,173-181,243`, `src/g_game.cpp:2845-2957,3025-3136` (`GAME_CountTeamItem`, `GAME_CheckMode`), `src/p_map.cpp:1343-1382` (`PIT_CheckThing`), `src/p_mobj.cpp:4856-4863,5071-5083,5878-5889` (`AActor::StaticSpawn`, map-thing team starts), `src/p_user.cpp:997,1057,2063-2068,2181-2330` (`AddInventory`/`RemoveInventory`, `Die`, `DropImportantItems`), `src/medal.cpp:771-851,855-1115`, `src/sv_main.cpp:1549,1707-1711,4286`, `src/cl_main.cpp:6611-6632`, `src/r_defs.h:390`, `src/p_acs.h:342-345`; and, for the post-3.2.1 `sv_requireskulltoscore` gate below, `src/team.cpp:2164` and the introducing commits `676afaf1f`/`020c68f67` checked for ancestry against the 3.2.1 version-bump commit `28f736fb3`. Absence on UZDoom checked in the UZDoom source's `wadsrc/static/zscript`, `wadsrc/static/mapinfo`, `src/scripting/thingdef_data.cpp`, and `src/gamedata/teaminfo.cpp`.
**Bucket:** native C++ classes in Zandronum. `ATeamItem : AInventory`, `AFlag : ATeamItem`, `AWhiteFlag : AFlag`, `ASkull : ATeamItem` declared at `src/g_shared/a_sharedglobal.h:203-255`, implemented in `src/g_shared/a_teamitems.cpp` (the file's own header still calls itself `a_flags.cpp`). `AReturnZone : AActor` is declared and implemented locally in `src/g_shared/a_returnzone.cpp:56-72`. DECORATE declarations: `wadsrc/static/actors/Skulltag/skulltagteamitems.txt` (`TeamItem` :7, `Flag` :19, `WhiteFlag` :85, `Skull` :162) and `wadsrc/static/actors/Skulltag/skulltagmisc.txt:153` (`ReturnZone`). Most team-game logic around them lives in `src/team.cpp`.
**Family rationale:** Shared implementation. Every behavior is one of `ATeamItem`'s virtual methods (`TryPickup`, `HandlePickup`, `AllowPickup`, `Return`, the announce/display hooks) plus `src/team.cpp`'s per-team bookkeeping; the subclasses override between one and seven of those virtuals and add no state. `ReturnZone` is not a team item, but it is the only DECORATE-visible way to set the sector flag the team-item drop and spawn paths check, so it belongs to the same system.

Zandronum's capture-the-flag, one-flag CTF and Skulltag game modes are built on these classes. A modder mostly touches them in three ways: defining new flag/skull classes for custom teams, restyling the stock ones, and placing `ReturnZone`/score-pillar things in maps. All of them are always loaded: they live in `zandronum.pk3`, not the opt-in `skulltag_actors.pk3` (see [Skulltag legacy actor classes](../concepts/skulltag-legacy-classes.md)).

## `TeamItem`

`ACTOR TeamItem : Inventory native`. Sets `+INTERHUBSTRIP` (a deprecated flag that Zandronum maps onto `Inventory.InterHubAmount`) and `Inventory.PickupSound "misc/k_pkup"`. Not placed directly. What its native overrides do:

- **`ShouldRespawn` always returns false.** A team item never respawns as an item (item-respawn dmflags don't apply). It only comes back through the return routine below.
- **`TryPickup` falls back to plain `Inventory` behavior outside team-item modes.** The team logic only runs when the current game mode has the `USETEAMITEM` flag ([GAMEMODE](../../zandronum-lumps/concepts/gamemode.md)). In any other mode a flag or skull is just an ordinary inventory pickup.
- **Pickup order in a team-item mode** (`a_teamitems.cpp:102-245`):
  1. The toucher's existing inventory gets first say through the `HandlePickup` chain. This is how a carried flag intercepts the touch of your own flag to score (see `Flag`).
  2. Only a player who is on a team may continue.
  3. `AllowPickup` returns one of deny, allow, or "return". On "return", the item is removed and the return routine runs (see "Return, drop, and the auto-return timer").
  4. On allow, the engine starts `PICKUP` scripts, then (simple mode only, see below) fires the `GAMEEVENT_TOUCHES` event and marks the team's item as taken. After that it prints the "has taken" messages, resets that team's return timer, plays the announcer entry, and attaches the item.
  5. Any `PowerInvisibility` or `PowerTranslucency` the carrier holds is destroyed on pickup. While the item is held, its `HandlePickup` also refuses those two powerup classes. The source doesn't show what happens to a sphere that tries to give one, so that part is not traced here.
- **`AllowPickup` rules** (`a_teamitems.cpp:274-311`), checked in this order:
  - Deny if the toucher isn't a player on a team.
  - Return if the item's class is exactly the toucher's own team item and the item has `MF_DROPPED` set (it was dropped, not at base).
  - On a client, allow. The server already decided.
  - Deny if the toucher already carries an enemy team item. You can only carry one.
  - Deny, with a "You can't pick up the ... of a team with no players!" message, if the item's team has no players.
  - Deny if the game isn't in progress (e.g. after the match ended).
  - Allow if the item isn't the toucher's own team item. Otherwise deny: your own undropped item at base just blocks the touch.
- **Announcer and message names are built from the team name plus a type word.** `GetType()` returns `"item"`, `"flag"` or `"skull"`, and the announcer entry is `<TeamName><type>Taken` / `<TeamName><type>Returned`, e.g. `BlueflagTaken`. For drops, `Drop()` uses `<TeamName>skullDropped` if the `skulltag` mode is on and `<TeamName>flagDropped` otherwise. See [ANCRINFO](../../zandronum-lumps/concepts/ancrinfo.md) for how entry names resolve.

## `Flag`

`ACTOR Flag : TeamItem native`, the empty base for every team flag. Native overrides:

- **Capturing** (`AFlag::HandlePickup`, `a_teamitems.cpp:606-678`). This runs on the flag the player is *carrying* when they touch another flag. If the carried flag is an enemy's and the touched one is exactly the player's own team flag, it scores, unless:
  - the game isn't in progress, or
  - the touched own flag is a dropped one (that falls through to the normal "return" path instead).

  Scoring gives the team and the player 1 point, the `Capture` medal, and `Assist` to whoever last returned the team's flag. It also fires `GAMEEVENT_CAPTURES`, respawns the carried flag at its origin, and takes it from the carrier. The own flag is never consumed: `HandlePickup` returns true without setting the pickup-good flag, so the touched flag's `TryPickup` fails and it stays at base. The point award itself only happens in **simple mode** and only on the server. In scripted mode the touch is still blocked, but nothing is awarded.
- **`AllowPickup` denies every team flag while `oneflagctf` is on** (`a_teamitems.cpp:688-695`). In one-flag CTF, team flags are fixed goals, not pickups.
- **Carry state.** The stock flags define a `Carry:` state sequence (`BFLS`, `RFLS`, ...). The carrier's floaty icon uses it. See "The carrier's floaty icon".

Stock subclasses (`skulltagteamitems.txt`), all `Radius 20`, `Height 48`, `+NOTDMATCH`, with `Spawn:` and `Carry:` states:

- `BlueFlag` (5130, SpawnID 177)
- `RedFlag` (5131, SpawnID 178)
- `GreenFlag` (5133)
- `GoldFlag` (5134)

## `WhiteFlag`

`ACTOR WhiteFlag : Flag 5132 native` (SpawnID 179), the neutral flag for one-flag CTF. It has **no `Carry:` state**. Its native overrides (`a_teamitems.cpp:710-931`):

- **Pickup** (`AllowPickup`, 777-801). It doesn't use the team-ownership rules at all. Anyone on a team can take it, unless:
  - they already hold a `WhiteFlag`,
  - fewer than two teams have players (message: "You can't pick up the white flag without an opposing team!"), or
  - the game isn't in progress.

  It never answers "return", so a dropped white flag can only be picked up again or time out. It can't be returned by touch.
- **Scoring** (`HandlePickup`, 710-767). While `oneflagctf` is on, touching an **enemy** team flag while carrying the white flag scores. That gives 1 point and the `Capture` medal (no assist), fires `GAMEEVENT_CAPTURES`, takes the white flag away, and respawns it at its origin. Touching your own team's flag or another `WhiteFlag` does nothing.
- **Messages and announcer.** The announcer uses fixed entries rather than team-name-built ones: `YouHaveTheFlag` / `YourTeamHasTheFlag` / `TheEnemyHasTheFlag` on pickup, `WhiteFlagReturned`, `WhiteFlagDropped`. Returns always print "returned automatically".
- **Bookkeeping slot.** The white flag doesn't belong to any team. The engine tracks it in the extra slot `teams.Size()`, which is also what `TEAM_GetTeamFromItem` returns for any class that isn't a team's item. It returns through the `WHITERETURN` script type rather than a team's return script.
- **Found by name, not through TEAMINFO.** The engine looks it up with `PClass::FindClass("WhiteFlag")` plus an is-kind-of test. So a custom one-flag item must **inherit from `WhiteFlag`**. Inheriting only from `Flag` won't do.
- A dropped white flag is given the hard-coded TID **668** (`p_user.cpp:2266`). Scripts can find it by that TID. Map-placed white flags get no such TID from the engine.

## `Skull`

`ACTOR Skull : TeamItem native`, the empty base for Skulltag-mode skulls. It overrides only `AllowPickup`, and only to call the `TeamItem` version (`a_teamitems.cpp:945-948`). **A skull has no capture override.** Touching your own skull while carrying an enemy one doesn't score. Skulltag-mode scoring happens at a score pillar instead (next section). Carry-icon-wise, the stock skulls have no `Carry:` state, so the icon falls back to their `Spawn:` state.

Stock subclasses (`skulltagteamitems.txt`), all `Radius 20`, `Height 16`, `+NOTDMATCH`, **no editor numbers**:

- `BlueSkullST`
- `RedSkullST`
- `GreenSkullST` (inherits `BlueSkullST` with a `translation`)
- `GoldSkullST`

They aren't normally placed directly. Instead, when simple Skulltag mode starts, `GAME_CheckMode` (`g_game.cpp:3081-3128`) **replaces every map-placed Doom key**:

- a `BlueSkull` becomes `BlueSkullST`, and its spot is recorded as team 0's origin;
- a `RedSkull` becomes `RedSkullST`, and its spot is recorded as team 1's origin.

It matches with an is-kind-of test, so subclasses of those keys count too. The team indices are hard-coded, not read from TEAMINFO. Green and gold skulls have no key to be converted from.

`hereticblueskull` (5026) and `hereticredskull` (5025) (`skulltagscorepillars.txt`) are plain subclasses of the Doom **keys** `BlueSkull`/`RedSkull`, not of `Skull`, flagged `game` Doom/Heretic/Hexen/Strife. They exist so a non-Doom map can place a Skulltag skull spot, which the same key-replacement pass then turns into `BlueSkullST`/`RedSkullST`. Outside simple Skulltag mode they are ordinary skull keys.

## Scoring in Skulltag mode: `SCOREPILLAR` and `HellScorePillar`

`SCOREPILLAR` is an actor flag stored in `STFlags` (`actor.h:404`, `thingdef_data.cpp:263`). It only acts inside `PIT_CheckThing`'s bump-special block (`p_map.cpp:1358-1382`). The engine credits a score when a player bumps a pillar and **all** of these hold:

- The pillar actor has `+SOLID` **and** `+BUMPSPECIAL` (the block is gated on a solid collision with a `BUMPSPECIAL` thing). The bumping player must be solid too.
- The code runs on the server in simple mode, and the player is on a team.
- The player carries an enemy team item (any team's, found through `TEAM_FindOpposingTeamsItemInPlayersInventory`).
- `args[0]` equals the player's team index, or equals the number of teams that have player starts on the map (meaning "any team"). The engine comment admits this guess breaks if the map's team starts aren't contiguous.
- `args[1]` is greater than 0. It is the **number of points** awarded.
- The player's own team item isn't currently taken. If it is, the engine shows "The `<team>` skull must be returned first!" instead of scoring, unless the `sv_requireskulltoscore` cvar (default on) has been turned off, in which case the score goes through anyway. This cvar was added after 3.2.1 (`676afaf1f`, `src/team.cpp:2164`; a 3.2.1 client always requires the item at base, with no way to disable that).

A successful score (`TEAM_ScoreSkulltagPoint`, `team.cpp:435-515`) does the following:

- Adds `args[1]` points to the team and the player.
- Removes the carried item and respawns it at its recorded origin.
- Gives the `Tag` medal, and `Assist` if someone earned it, except that in Skulltag mode with `sv_requireskulltoscore` off, no assist is ever recorded to begin with (`TEAM_SetAssistPlayer` skips it; added after 3.2.1, `020c68f67`).
- Fires `GAMEEVENT_CAPTURES` with the point count.
- **Jumps the pillar to a state named `Tag<TeamName>Skull`**, where `<TeamName>` is the TEAMINFO name of the team whose item was carried (the state name is built at runtime with `FindState`). The jump is also sent to clients. If the pillar has no such state, the jump is silently skipped.

After the scoring check, the pillar's own `special` also runs with its `args[0..4]` as the special's arguments. The pillar arguments and any line special share the same five slots, so a score pillar normally carries no special.

Nothing in the source restricts the pillar to the `skulltag` mode. It keys off "simple mode" and "carrying an enemy team item", so a pillar would also accept a flag in CTF. That reading comes from the gating code and wasn't observed in play.

`HellScorePillar` (5020, `skulltagscorepillars.txt`) is the stock pillar: `+SOLID +BUMPSPECIAL +SCOREPILLAR`, radius 16, height 40, with `TagBlueSkull` and `TagRedSkull` states that play a short animation and return to `Spawn`. It has no `TagGreenSkull`/`TagGoldSkull`, so scoring with those teams' skulls leaves it unanimated. The mapper must set `args[1]` (points). A custom pillar needs the same three flags plus `Tag<TeamName>Skull` states for every team it should animate for.

## Simple mode vs. scripted mode

This is the load-bearing switch for every scoring and return claim above. After map load, `GAME_CheckMode` (`g_game.cpp:3025-3136`) turns on "simple CTF/ST mode" when the mode has `USETEAMITEM` **and** the map lacks either a `PICKUP` script or the return script of any available team (`BLUERETURN` for team 0, `REDRETURN` for team 1). See [script types](../../acs/concepts/script-types.md).

- **Simple mode** (the usual case: maps without those scripts). The engine records each team item's spawn origin, awards captures and pillar scores, marks items taken/not taken, respawns returned items at their origin, and prints the take/return messages.
- **Scripted mode** (a `PICKUP` script plus every available team's return script present). The engine still blocks and permits touches, fires the typed scripts, plays announcer entries, and resets return timers. But it awards no points, doesn't respawn returned items, and doesn't record origins or the taken state. The map's ACS is expected to do all of that. `PICKUP` scripts start with the toucher as activator; the return scripts start with no activator.

Only teams 0 and 1 get a return-script type assigned (`TEAM_Reset`, `team.cpp:152-162`). Nothing assigns one for teams 2 and 3. What the loop does when more than two teams are available was not traced, so treat scripted mode as a two-team feature.

Game-mode auto-detection is separate. On a map with only team starts, `GAME_CheckMode` counts `Flag` and `Skull` actors with a thinker iterator (subclasses included). Flags without skulls turn on `ctf`, unless `oneflagctf` is already set. Skulls without flags turn on `skulltag`.

## Return, drop, and the auto-return timer

- **Drop.** `APlayerPawn::DropImportantItems` (`p_user.cpp:2181-2330`) runs on the server when a player carrying an item:
  - dies (`Die` calls it before the rest of the death logic);
  - changes team, becomes a spectator, or disconnects;
  - is a bot being removed;
  - is respawned by the ACS `SetPlayerClass` extension function.

  The team item is taken from the player and a new instance is spawned at the player's position with `MF_DROPPED`. A team flag or skull is spawned `NO_REPLACE`; a white flag is spawned `ALLOW_REPLACE`. Then, unless the drop sector is a return zone:
  - with `DF2_INSTANT_RETURN` (`sv_instantreturn`), the item returns immediately with no returner;
  - otherwise, the team's return timer is set to `sv_flagreturntime * TICRATE` (`sv_flagreturntime` defaults to 15 seconds, `team.cpp:2133`; see [console cvars](../../console/inventory/cvars.md)) and the "dropped" message and announcer entry play.

  A kill on a carrier also gives the killer the `Defense` medal: for a team item, only if the carried item was the killer's own team's; for the white flag, for any enemy killer.
- **Auto-return.** `TEAM_Tick` (`team.cpp:118-132`) counts each team's timer and the white-flag timer down once per tic. When one hits 0, it calls `TEAM_ExecuteReturnRoutine`. Timers don't run during a result sequence. Picking the item up again resets the timer to 0, which disarms it.
- **The return routine** (`TEAM_ExecuteReturnRoutine`, `team.cpp:235-305`) does the following:
  - starts the team's return script type (or `WHITERETURN`);
  - spawns a temporary instance of the item class (with replacement allowed) and gives up if that isn't a `TeamItem`;
  - in simple mode, calls its `Return` (respawns at the origin with `MF_DROPPED` cleared) and its return messages;
  - destroys every `MF_DROPPED` instance of that class on the map.

  Touch-returns (a player touching their own dropped item) take the equivalent path inside `TryPickup`. There, `Return` records the returner as the team's potential `Assist` player (only if a teammate is carrying an enemy item at that moment) and fires `GAMEEVENT_RETURNS`.

## `ReturnZone`

`ACTOR ReturnZone 5067 native` (`skulltagmisc.txt:153`), flags `+NOBLOCKMAP +NOSECTOR +NOGRAVITY +DONTSPLASH`. On `PostBeginPlay` it sets `SECF_RETURNZONE` on the sector it stands in and destroys itself (`a_returnzone.cpp:65-72`). No other code path sets that sector flag: no UDMF key, no sector special. Place one thing in each sector that should act as a zone, typically lava pits or unreachable areas.

The flag is checked **only when a team item spawns**, in `AActor::StaticSpawn` (`p_mobj.cpp:5071-5083`). That check runs on the server or offline, and not for the return routine's own temporary spawn. If the new actor's class is a team's item (or it's a `WhiteFlag` in one-flag CTF), the return routine runs at once, which destroys the dropped copy and respawns the item at its origin. `DropImportantItems` then skips its own timer and message setup for that drop. **An item that spawns outside a zone and then moves into one is not returned.** The source has no movement-time check. This conclusion comes from that missing check, not from play.

## The carrier's floaty icon

In a `USETEAMITEM` mode, the engine shows a floaty icon above a player on a team who carries an enemy team item (`medal.cpp:771-851`, `855-1115`). This is the DECORATE hook for how a carried custom flag looks to other players:

- **Team flags and skulls.** The icon is an `AFloatyIcon` set to the carried item's **`Carry` state if it has one, otherwise its `Spawn` state**, and it copies the item's `Translation`. That's why `GreenSkullST`'s translated colors show over its carrier.
- **The white flag.** One-flag CTF uses the [`FloatyIcon`](../classes/floatyicon.md) class's own `WhiteFlag` state instead, not anything on the `WhiteFlag` actor.
- **Priority and visibility.** Carrier icons override medal icons. The icons are client-side only (never drawn on a server) and are turned off by `cl_icons 0`. Icons are removed when the player no longer carries an enemy item.

## Defining a custom team item

The engine identifies a team's item by **exact class**, not inheritance. `TEAM_GetItem` resolves the TEAMINFO `FlagItem` or `SkullItem` string with `PClass::FindClass`. `TEAM_GetTeamFromItem`, `AllowPickup` and the capture test all compare classes for equality. It picks `FlagItem` when the mode has `USEFLAGASTEAMITEM` (CTF, one-flag CTF) and `SkullItem` otherwise (Skulltag). So a custom item needs both of these:

1. **Inherit from `Flag` or `Skull`** (or from `WhiteFlag` for a one-flag item). That gives the native behavior, and it's what the thinker iterators count for mode auto-detection.
2. **Name that exact class as a team's `FlagItem` or `SkullItem` in a `TEAMINFO` lump.** A `Flag` subclass not named there is treated as belonging to no team (`teams.Size()`), so `AllowPickup` refuses it with the "team with no players" message. It will still trip CTF auto-detection, though.

```decorate
ACTOR PurpleFlag : Flag 20001
{
	Radius 20
	Height 48
	+NOTDMATCH
	Inventory.PickupMessage "Purple flag!"
	Inventory.Icon "PFLAB0"
	States
	{
	Spawn:
		PFLA ABC 3
		PFLA DEF 3 BRIGHT
		Loop
	Carry:
		PFLS ABCDEF 3
		Loop
	}
}
```

```text
Team "Purple"
{
	PlayerColor "80 00 C0"
	TextColor "Purple"
	FlagItem "PurpleFlag"
	SkullItem "PurpleSkull"
	PlayerStartThingNumber 20002
}
```

TEAMINFO notes (`teaminfo.cpp`):

- Every `Team` block **appends** a new team; nothing merges by name.
- To change a stock team's `FlagItem`, start the lump with `ClearTeams` and redefine every team.
- The engine requires between 2 and `MAX_TEAMS` teams.
- The class-name strings aren't checked at parse time. A misspelled or omitted `FlagItem`/`SkullItem` makes `TEAM_GetItem` return null. The return routine passes that straight to `Spawn`, which aborts with the fatal "Tried to spawn a class-less actor" error (`p_mobj.cpp:4860`). So the first timed or return-zone return in a mode that uses the bad key kills the game. That comes from reading the source, not from a test run. Define both classes the example names, even if you only plan to run CTF.
- `PlayerStartThingNumber` is the editor number of this team's player starts. Don't reuse 5082: the engine reserves it for "temporary team starts" (`p_mobj.cpp:5878-5883`). The team also needs at least one such start **placed on the map**. In a `TEAMGAME` mode, `TEAM_ShouldUseTeam` (`team.cpp:1367-1376`) treats a team without starts as unused, and `TEAM_FindOpposingTeamsItemInPlayersInventory` skips unused teams. So that team's item then never counts as a carried enemy item: no pillar score, no carrier icon, and it's ignored by the one-item-at-a-time check. Flag captures compare classes directly and aren't affected. See also [GetTeamProperty](../../acs/functions/getteamproperty.md) for how `sv_maxteams` limits the available teams.

The stock lump (`wadsrc/static/teaminfo.txt`) maps Blue/Red/Green/Gold to `<Color>Flag` and `<Color>SkullST`.

**Replacing a stock flag with `replaces` is fragile.** This isn't traced end to end; it's inferred from the exact-class matching. A map-placed `BlueFlag` spawned with replacement allowed turns into the replacement class, which no longer equals TEAMINFO's `"BlueFlag"`, and returns respawn it `NO_REPLACE`. Point TEAMINFO at the new class instead, or subclass it without `replaces`.

State labels the engine looks up on these actors: `Spawn`, `Carry` (floaty icon), and `Tag<TeamName>Skull` on score pillars. Standard `Inventory` properties (pickup message and sound, `Inventory.Icon`) work as usual. The HUD icons shown for a team's item come from TEAMINFO's `SmallFlagHUDIcon` / `LargeSkullHUDIcon`-style keys, not from the actor.

## Netcode

- **The server decides.** `PIT_CheckThing` only calls `P_TouchSpecialThing` when not in client mode (`p_map.cpp:1351-1354`). Drops, returns, captures and pillar scores run on the server.
- **What clients receive.** Clients get `DestroyThing`, `SpawnThing` and `TakeInventory` commands, plus team-item-specific ones: `TeamItemReturned` (with the returning player), `TeamItemDropped`, and `SetTeamReturnTicks`. On receipt, the client re-runs the return routine or `ATeamItem::Drop` locally for messages and announcer (`cl_main.cpp:6611-6632`). On a client, `AllowPickup` short-circuits to "allow" after the own-dropped check.
- **Join sync.** A joining client gets the simple-mode state (`SetSimpleCTFSTMode`) and every team's return timer (`sv_main.cpp:1549,1707-1711`). When a player's inventory is sent to a client, a `TeamItem` is the one inventory kind broadcast to **all** clients instead of only its owner (`sv_main.cpp:4286`). That's how everyone knows who carries what.
- **Carrier bookkeeping.** Adding or removing a `TeamItem` from a player's inventory in a players-on-teams mode updates the team carrier bookkeeping (`p_user.cpp:997,1057`).

## Engine-family divergence

None of this system exists on UZDoom. Checked against the UZDoom source at @98b16b78fc (5.1.0-pre):

- There are no `TeamItem`, `Flag`, `Skull`, `WhiteFlag`, `ReturnZone`, `HellScorePillar` or `hereticblueskull`/`hereticredskull` classes in its DECORATE or ZScript, so inheriting from them fails to resolve.
- `SCOREPILLAR` is accepted as a dummy flag, grouped with other Skulltag compatibility names that parse and do nothing.
- UZDoom's `TEAMINFO` parser accepts `FlagItem`, `SkullItem` and the flag/skull HUD icon keys but discards their values. It has no CTF, one-flag CTF or Skulltag game modes to use them.
- Editor numbers 5130 and 5131 are mapped to Strife-only flag-spot actors in UZDoom's own doomednum tables, and 5020/5025/5026/5067/5132 aren't mapped at all. A map built for these Zandronum things spawns nothing (or, in Strife, something unrelated) on UZDoom.
