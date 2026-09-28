# The `ANCRINFO` lump

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** Zandronum Wiki `ANCRINFO` (https://wiki.zandronum.com/w/index.php?title=ANCRINFO&oldid=2172, retrieved 2026-09-09) + verified against the Zandronum source's `src/announcer.cpp` (`ANNOUNCER_Construct` at line 161, `ANNOUNCER_ParseAnnouncerInfo` at line 178, `announcer_ParseAnnouncerInfoLump` at line 506, and the `AnnouncerProfile` class at line 68). Standard-key table checked against the `ANNOUNCER_PlayEntry` call sites, `src/medal.cpp:1130-1245` (medal award conditions), `src/p_interaction.cpp:3051-3053` (Accuracy/Precision), `src/team.cpp:487` (Tag), `src/g_shared/a_teamitems.cpp:321-333,444-452,549-559,811-828` (team item and white flag entries), and the `AnnouncerEntry`/`WelcomeSound`/`Inventory.PickupAnnouncerEntry` values in `wadsrc/static/medaldef.txt`, `gamemode.txt` and `actors/`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0
(NonCommercial) — see [LICENSE](../../LICENSE) §2.

`ANCRINFO` declares announcer profiles: named sets of event-to-sound mappings (frag/point
milestones, round start, etc.) selected by the `cl_announcer` cvar. It is a plain text lump of
anonymous `{ }`-delimited blocks, each holding `key = value` pairs.

## Grammar and the one reserved key

```text
{
    name = "My Announcer"
    fraglimit = "announcer/2fragsleft"
}
```

Each block's tokens are consumed positionally: a bare token starts a new key, the next token must
be a literal `=` (a fatal `I_Error` if it isn't), and the token after that is the value. **`name`
is the only key with reserved meaning** — it sets the profile's display name via `SetName`. Every
other key, with no fixed vocabulary at all, is added directly as an event-name-to-sound-value
mapping via `AddEntry`. Unlike `BOTINFO` (see [`bots/concepts/botinfo-lump.md`](../../bots/concepts/botinfo-lump.md)),
an unrecognized key here is not fatal — there is no recognized-key check to fail, since any key
other than `name` is valid by construction. Only a missing `=` is a parse error.

## A block named `Default` (case-insensitively) merges instead of replacing

`ANNOUNCER_Construct` pre-seeds one profile named `"Default"` with no entries and keeps a pointer
to it (`g_DefaultAnnouncer`). When parsing finds a block, it compares that block's `name` against
the current default profile's name (`CompareNoCase`): a match calls `Merge`, updating the default
profile with every entry from the new block (overwriting any existing entry with the same key);
anything else is `Push`ed as a brand-new profile. A block that omits `name` entirely keeps the
class's own default name (`"UNNAMED ANNOUNCER"`, from `AnnouncerProfile`'s constructor) — which
never matches `"Default"`, so it is always pushed as a new profile rather than merged, and two
such nameless blocks do not merge with each other; both become separate profiles sharing the same
display name. There is no "override the default announcer entirely" form: to extend it, name a
block `Default` (case-insensitive); anything else adds a new, separate profile.

## The default profile also backfills every profile's fallback sound

Beyond the merge behavior above, every event key parsed from *any* block — default or not — is
opportunistically copied into the default profile too, but only if the default profile doesn't
already have an entry for that key (`if ( !g_DefaultAnnouncer->EntryExists(key) )`). So the first
occurrence of a given event key anywhere in load order becomes the tree-wide fallback sound for
every other profile that doesn't declare its own value for that same key — not just the entries an
author explicitly wrote into a `Default`-named block.

## Loading is additive, not replacing

The engine scans **every loaded archive** for a lump named `ANCRINFO` and parses each one in turn
(`Wads.FindLump` loop in `ANNOUNCER_ParseAnnouncerInfo`) — a mod adds and extends announcer
profiles rather than overriding a prior lump wholesale, and multiple mods declaring `ANCRINFO` do
not conflict outright (though same-named non-`Default` profiles still both get pushed as separate
entries — there is no per-name dedup outside the `Default` special case above).

## Standard announcer keys

Zandronum's gameplay code calls announcer entries throughout match events. The following is a
reference list of standard announcer keys an `ANCRINFO` profile can define. Some names are
hardcoded in the engine; others come from data the engine reads: a `MEDALDEF` medal's
`AnnouncerEntry`, a `GAMEMODE` block's `WelcomeSound`, and an item's
`Inventory.PickupAnnouncerEntry` (played only when the player picking it up is the one the local
view is on, and only with `cl_announcepickups` on). The team keys are built from the `TEAMINFO`
team name, so the default `Green` and `Gold` teams produce `GreenScores`, `GoldFlagTaken` and so on
alongside the blue and red rows below. Keys are case-insensitive (parsed via `FName` comparison) and mods may define any
additional custom keys.
Defining a key is optional — if the engine fires an announcer entry that the active profile does
not have, the default profile's entry is used as a fallback (see "The default profile also
backfills" above). If neither has an entry, the announcement is silently skipped.

| Key | Typical usage |
|---|---|
| `accuracy` | Awarded the "Accuracy" medal (every 5 consecutive hits on players, below 10) |
| `assist` | Awarded the "Assist" medal |
| `blueflagdropped` | Blue flag has been dropped in CTF |
| `blueflagreturned` | Blue flag has been returned to its base in CTF |
| `blueflagtaken` | Blue flag has been taken (picked up) in CTF |
| `blueleads` | Blue team takes the lead in team games |
| `bluescores` | Blue team scores (CTF, team games) |
| `blueskulldropped` | Blue skull has been dropped |
| `blueskullreturned` | Blue skull has been returned to its base |
| `blueskulltaken` | Blue skull has been taken (picked up) |
| `capture` | Awarded the "Capture" medal |
| `defense` | Awarded the "Defense" medal |
| `domination` | Awarded the "Domination" medal |
| `doomsphere` | Doom Sphere power-up picked up |
| `drain` | Drain Rune power-up picked up |
| `excellent` | Awarded the "Excellent" medal |
| `fight` | "Fight!" countdown ends; match begins |
| `firstfrag` | Awarded the "First Frag" medal (first kill of the match) |
| `fisting` | Awarded the "Fisting" medal |
| `fiveminutewarning` | Five minutes of match time remain (timed modes only) |
| `guardsphere` | Guard Sphere power-up picked up |
| `haste` | Haste Rune power-up picked up |
| `highjump` | High Jump Rune power-up picked up |
| `impressive` | Awarded the "Impressive" medal |
| `incredible` | Awarded the "Incredible" medal |
| `invisibility` | Invisibility Sphere power-up picked up |
| `invulnerability` | Invulnerability Sphere power-up picked up |
| `llama` | Awarded the "Llama" medal (fragging a player who was chatting, in the console or a menu, or lagging) |
| `megasphere` | Megasphere power-up picked up |
| `mostimpressive` | Awarded the "Most Impressive" medal |
| `nextroundin` | Countdown to the next round (rounds-based modes) |
| `one` | "One" countdown before match start |
| `onefragleft` | Player is one frag away from winning |
| `oneminutewarning` | One minute of match time remains (timed modes only) |
| `partialinvisibility` | Partial Invisibility Sphere power-up picked up |
| `perfect` | Awarded the "Perfect" medal |
| `possessionartifactdropped` | Possession artifact dropped in Possession mode |
| `possessionartifactpickedup` | Possession artifact picked up in Possession mode |
| `precision` | Awarded the "Precision" medal (every 5 consecutive hits on players, from 10 up) |
| `preparetofight` | "Prepare to fight!" countdown before match start |
| `prosperity` | Prosperity Rune power-up picked up |
| `rage` | Rage Rune power-up picked up |
| `redflagdropped` | Red flag has been dropped in CTF |
| `redflagreturned` | Red flag has been returned to its base in CTF |
| `redflagtaken` | Red flag has been taken (picked up) in CTF |
| `redleads` | Red team takes the lead in team games |
| `redscores` | Red team scores (CTF, team games) |
| `redskulldropped` | Red skull has been dropped |
| `redskullreturned` | Red skull has been returned to its base |
| `redskulltaken` | Red skull has been taken (picked up) |
| `reflection` | Reflection Rune power-up picked up |
| `regeneration` | Regeneration Rune power-up picked up |
| `resistance` | Resistance Rune power-up picked up |
| `soulsphere` | Soul Sphere power-up picked up |
| `spam` | Awarded the "Spam" medal |
| `spread` | Spread Rune power-up picked up |
| `strength` | Strength Rune power-up picked up |
| `tag` | Awarded the "Tag" medal (scoring with an enemy skull in Skulltag mode) |
| `teamsaretied` | Score tied in team games (CTF, team games) |
| `termination` | Awarded the "Termination" medal |
| `terminator` | Terminator Sphere power-up picked up |
| `theenemyhastheflag` | An enemy picks up the white flag (One Flag CTF only) |
| `three` | "Three" countdown before match start |
| `threefragsleft` | Player has three frags remaining to win |
| `timefreeze` | Time Freeze Sphere power-up picked up |
| `totaldomination` | Awarded the "Total Domination" medal |
| `turbosphere` | Turbo Sphere power-up picked up |
| `two` | "Two" countdown before match start |
| `twofragsleft` | Player has two frags remaining to win |
| `victory` | Awarded the "Victory" medal (winning a duel or an LMS round without earning "Perfect") |
| `votefailed` | Vote failed |
| `votenow` | New vote started |
| `votepassed` | Vote passed |
| `welcometoctf` | Welcome message at CTF match start |
| `welcometooneflagctf` | Welcome message at One Flag CTF match start |
| `welcometodomination` | Welcome message at Domination match start |
| `welcometost` | Welcome message at SkullTag mode match start |
| `whiteflagdropped` | White flag dropped in One Flag CTF |
| `whiteflagreturned` | White flag returned in One Flag CTF |
| `youaretiedforthelead` | Player tied for the lead in frags |
| `youfailit` | Awarded the "You Fail It" medal |
| `youhavetheflag` | The local player picks up the white flag (One Flag CTF only) |
| `yourskillisnotenough` | Awarded the "Your Skill Is Not Enough" medal |
| `yourteamhastheflag` | A teammate picks up the white flag (One Flag CTF only) |
| `youvelostthelead` | Player was in the lead but another player has taken it |
| `youvetakenthelead` | Player overtakes the leader in frags |
| `youwin` | Player wins the match |

## Engine-family divergence: no counterpart outside Zandronum

UZDoom/GZDoom-family engines do not parse `ANCRINFO` at all and have no announcer-profile
subsystem of this shape to port it to.
