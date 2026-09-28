# `FloatyIcon`

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** engine source only. Zandronum 3.3-alpha: `wadsrc/static/actors/Skulltag/skulltagmisc.txt:7-110` (FloatyIcon), `:118-143` (PathNode), `:167-174` (SpringPadZone); `src/g_shared/a_sharedglobal.h:259-275`; `src/g_shared/a_icon.cpp:8-86`; `src/medal.cpp:102-121, 196-214, 273-321, 412-489, 631-851, 855-1124`; `src/medal.h:63-91`; `wadsrc/static/medaldef.txt`; `src/r_things.cpp:540-550`; `src/gl/scene/gl_sprite.cpp:531-541`; `src/actorptrselect.cpp:59`; `wadsrc/static/actors/constants.txt:253`; `src/d_main.cpp:646, 668-669`; `src/sv_main.cpp:1170-1177`; `src/voicechat.cpp:722-732`; `src/chat.cpp:897`; `src/c_console.cpp:1683`; `src/menu/menu.cpp:347`; `src/p_user.cpp:2434, 2635-2636, 3201, 3487-3492`; `src/g_game.cpp:2101-2104`; `src/cl_main.cpp:3688-3691`; `src/p_mobj.cpp:3135-3139`; `src/g_shared/a_springpad.cpp:56-74`; `src/astar.cpp:749-752`; `src/bots.cpp:358`; `src/thingdef/thingdef.cpp:183-206`; `src/thingdef/thingdef.h:172-179`; `src/actor.h:1353-1356`.
**Bucket:** native C++ class in Zandronum (`class AFloatyIcon : public AActor` in `src/g_shared/a_sharedglobal.h:259`, implementation in `src/g_shared/a_icon.cpp`; DECORATE definition `ACTOR FloatyIcon native` in `wadsrc/static/actors/Skulltag/skulltagmisc.txt:7`, loaded from `zandronum.pk3`). All spawning and state selection lives in `src/medal.cpp`.

The actor that floats above a player's head: chat bubble, console/menu/voice/lag indicators,
ally/enemy markers, carried flag or skull, Terminator/Possession artifact, and medal icons. One
player has at most one, held in `player_t::pIcon`. The engine owns it completely: it is spawned,
re-stated, and destroyed only by the medal/icon code in `src/medal.cpp`, never by a map or a
DECORATE call. For the medal definitions that feed it, see
[`MEDALDEF`](../../zandronum-lumps/concepts/medaldef.md); this file does not repeat that lump's
grammar, queue, or `LowerMedal` rules.

Defaults: `Height 8`, `+NOBLOCKMAP`, `+NOGRAVITY`.

## You cannot spawn one yourself

`AFloatyIcon::Tick` (`a_icon.cpp:27-31`) destroys the icon on its first tic unless its `tracer` is a
player's body whose `player->pIcon` points back at this exact actor. A `FloatyIcon` placed in a map,
summoned, or created with `A_SpawnItemEx` therefore vanishes immediately. To change what players see,
restyle the classes the engine spawns (see "Restyling" below). To reach the live icon from
DECORATE/ACS, use the `AAPTR_PLAYER_GETFLOATYICON` pointer selector (`constants.txt:253`,
resolved to `origin->player->pIcon` in `actorptrselect.cpp:59`).

## How it follows its player

- **`SetTracer(mo)`** (`a_icon.cpp:61-72`) sets `tracer` and immediately moves the icon to
  `tracer->z + tracer->height + 4` map units. Called on every spawn/re-state, and again when a
  player's body is swapped (for example the Heretic/Hexen skull-pop death, `p_user.cpp:2635-2636`).
- **`Tick`** (`a_icon.cpp:22-59`) re-positions it to the same point above the tracer every tic, then
  resets `alpha` to opaque and `RenderStyle` to Normal, applies the fade (below), and finally copies
  the tracer's render style and alpha if the tracer is not Normal/opaque (`CopyTracerTranslucency`,
  `:74-86`). That copy is skipped for the Ally icon so teammates stay easy to spot. So an invisible
  or translucent player gets an equally invisible/translucent icon.
- **Consequence for modders:** a custom icon class's `Alpha` and `RenderStyle` properties are
  overwritten every tic and have no visible effect. Only sprite frames, `bright`, frame durations,
  and (for team items only) `Translation` carry through.

## Lifetime: `lTick`

`lTick` is a countdown in tics (`a_sharedglobal.h:269`). `0` means "no timeout". While nonzero,
`Tick` decrements it; during the final `TICRATE` (35) tics it ramps alpha from opaque to 0 with the
Translucent style; when it reaches 0 the icon destroys itself.

- **Medal icons** get `lTick` = the medal's remaining queue time (`medal.cpp:743`), which starts at
  `MEDAL_ICON_DURATION` = 3 seconds (`medal.h:63`). A medal restored after a respawn or after a
  carrier icon cleared resumes with its remaining time, not a fresh 3 seconds.
- **Status and carrier icons** always get `lTick = 0` (`medal.cpp:1117`) and are instead deleted by
  `medal_SelectIcon`'s validity check (`:880-1017`) the tic their condition stops holding.
- Also destroyed: on player death when the player will be reborn (`p_user.cpp:3487-3492`), in
  `G_PlayerFinishLevel` (`g_game.cpp:2101-2104`), and when a client learns a player (re)joined
  (`cl_main.cpp:3688-3691`).

## States, triggers, and setters

`medal_SelectIcon` (`medal.cpp:855-1124`) looks the state up by name on
`RUNTIME_CLASS(AFloatyIcon)->GetReplacement()`, so the label names below are the contract a
replacement class must keep. `medal_GetDesiredIcon` (`:771-851`) decides which applies.

| Label (sprite) | Shown when | Where the condition is set |
|---|---|---|
| `Chat` (`TALK`) | player has `PLAYERSTATUS_CHATTING` (typing a chat message) | `chat.cpp:897` on the typing client, sent to others; bots also toggle it (`botcommands.cpp`) |
| `InConsole` (`CNSL`) | `PLAYERSTATUS_INCONSOLE` | `c_console.cpp:1683` when the console opens |
| `InMenu` (`MENU`) | `PLAYERSTATUS_INMENU` | `menu/menu.cpp:347` when a menu opens |
| `VoiceChat` (`SPKR`) | `PLAYERSTATUS_TALKING` | `voicechat.cpp:722-732`, each tic, from whether that player's voice audio is currently playing |
| `Lag` (`LAGG`) | `PLAYERSTATUS_LAGGING`; deleted at once if not running as a network client | server, `sv_main.cpp:1170-1177`: no command from the client for 1 second (5 seconds during intermission or while spectating) |
| `Ally` (`ALLY`) / `Enemy` (`ENEM`) | the player is / is not a teammate of the player whose view the HUD shows, and the matching cvar allows it (see "Visibility") | computed locally from `IsTeammate` against `HUD_GetViewPlayer()` |
| `WhiteFlag` (`WFLS`) | One Flag CTF, player on a team carries `WhiteFlag` | inventory check |
| `TerminatorArtifact` (`ARNO`) | Terminator mode, player has `CF2_TERMINATORARTIFACT` | cheats2 flag |
| `PossessionArtifact` (`PPOS`) | (Team) Possession, player has `CF2_POSSESSIONARTIFACT` | cheats2 flag |
| (team item) | a `GMF_USETEAMITEM` mode (CTF, Skulltag), player carries the opposing team's item | not a FloatyIcon label: the icon is set to the carried item's own `Carry` state, or its `Spawn` state if it has none, and copies the item's `Translation` (`medal.cpp:1068-1077, 1103-1107`) |
| 21 medal labels (`Excellent`, `Incredible`, `Impressive`, `Most_Impressive`, `Domination`, `Total_Domination`, `Accuracy`, `Precision`, `Victory`, `Perfect`, `FirstFrag`, `Termination`, `Capture`, `Tag`, `Assist`, `Defense`, `Llama`, `YouFailIt`, `YourSkillIsNotEnough`, `Fisting`, `Spam`) | the stock medal of the same name reaches the top of the player's medal queue | referenced by name from the engine's own `medaldef.txt` (`Class = "FloatyIcon"`, `State = "<label>"`), not from C++ |

`Spawn` shares its frames with `TerminatorArtifact` (both labels sit on the same `ARNO` sequence);
every engine spawn path calls `SetState` immediately, so `Spawn` itself is never what players see.

## Priority when several apply

Three layers, from the top:

1. **Carrier icons** (`WhiteFlag`, team item, `TerminatorArtifact`, `PossessionArtifact`; the
   `SPRITE_WHITEFLAG..SPRITE_TEAMITEM` enum range, `medal.h:74-77`) beat medals. `MEDAL_Tick`
   (`medal.cpp:310`) lets `medal_SelectIcon` run for them even while a medal is queued, and
   `medal_TriggerMedal` (`:730`) refuses to replace an existing carrier icon. The medal keeps
   counting down underneath and reappears if the carrier icon clears before it expires.
2. **A queued medal** beats every status icon: `medal_SelectIcon` only runs when the queue is empty
   (`:310`).
3. **Among status/carrier conditions**, the last assignment in `medal_GetDesiredIcon` wins:
   Possession > Terminator > WhiteFlag / team item > Lag > VoiceChat > InMenu > InConsole > Chat >
   Ally / Enemy.

## Visibility and cvars

- **Never exists on a dedicated server.** `medal_TriggerMedal` (`:725`) and `medal_SelectIcon`
  (`:867`) both bail out under `NETSTATE_SERVER`; each client (or an offline game) spawns its own
  icons locally from replicated player state. It is not a networked actor.
- **Hidden from the viewer it belongs to.** Both renderers skip the icon of
  `players[consoleplayer].camera->player` (software `r_things.cpp:540-550`, GL
  `gl_sprite.cpp:531-541`) unless chasecam is on or the sprite is being drawn in a mirror. This
  covers your own icon in first person and the icon of a player you are spying on. Ally/Enemy is
  additionally never assigned to the viewed player (`medal.cpp:787`), and is removed in free
  spectate mode.
- **Spectators** get no icon at all (`:867`).
- **`cl_icons`** (bool, default true, `:103`): false destroys and suppresses every status/carrier
  icon. It does not gate medal icons.
- **`cl_medals`** (bool, default true, `:102`): false keeps medals out of the local queue, so no
  medal icon, text, or announcer (`:437`). The award count still increments.
- **`cl_showallyicon`** (default 1) / **`cl_showenemyicon`** (default 0) (`:106-121`): 0 never,
  1 only in game modes with `GMF_PLAYERSONTEAMS`, 2 always. Clamped to 0-2.
- **Server-side overrides:** `sv_noallyicons` / `sv_noenemyicons` (`zadmflags`,
  `d_main.cpp:668-669`) forbid those icons regardless of the client cvar; `sv_nomedals`
  (`:646`) blocks medal awards entirely (`medal.cpp:424`).

## Medal icon classes

A medal's `Class` from `MEDALDEF` is spawned as-is: `Spawn(medal->iconClass, ..., NO_REPLACE)`
followed by a `static_cast<AFloatyIcon *>` (`medal.cpp:736`). That cast is safe because
`MEDAL_Construct` rejects any class that is not a descendant of `FloatyIcon` with a fatal
`Class '%s' is not a descendant of 'FloatyIcon'.` (`:203-205`). The `State` is resolved by exact
name on that class at parse time (`FindStateByString(..., true)`, `:214`), so dotted labels work.

Because the medal path uses `NO_REPLACE`, **`replaces FloatyIcon` does not affect medal icons.** The
stock medals all name `FloatyIcon` itself; to restyle one, re-open its `MEDALDEF` block and point
`Class`/`State` at your own subclass (see the MEDALDEF doc's merge rules).

## Restyling

Status icons go through the opposite path: `Spawn<AFloatyIcon>(..., ALLOW_REPLACE)` (`:1101`) with
states looked up on the replacement class. A subclass inherits every parent state label
(`ResetBaggage` rebuilds labels from the parent, `thingdef.h:172-179`), so a replacement only needs
to redefine the labels it wants to change:

```decorate
Actor MyFloatyIcon : FloatyIcon replaces FloatyIcon
{
  States
  {
  Chat:
    MCHT AB 8 Bright
    Loop
  }
}
```

**Always inherit from `FloatyIcon` when replacing it.** DECORATE's `replaces` performs no
inheritance check (`SetReplacement`, `thingdef.cpp:183-206`), and `Spawn<AFloatyIcon>` is a plain
`static_cast` (`actor.h:1353-1356`). A non-descendant replacement that lacks a given label
produces no icon for that condition at all, silently, since the spawn only happens when the state
lookup succeeds (`medal.cpp:1086-1087`). One that does define the label would be spawned and then have
`lTick`, `currentSprite`, and `bTeamItemFloatyIcon` written into an object that has no such fields,
which is undefined behavior (inferred from the cast; not tested in-engine). It would also lack
`AFloatyIcon::Tick`, so it would not follow the player.

Team-item icons show the carried item's own `Carry`/`Spawn` frames, so restyle those on the
flag/skull class, not on `FloatyIcon`.

## `SpringPadZone`

`ACTOR SpringPadZone 5068 native` (`skulltagmisc.txt:167`; `+NOBLOCKMAP +NOSECTOR +NOGRAVITY
+DONTSPLASH +ALLOWCLIENTSPAWN`). A map-editor marker: in `PostBeginPlay` it sets `PLANEF_SPRINGPAD`
on the floor of the sector it stands in, then destroys itself (`a_springpad.cpp:65-74`). The whole
sector floor becomes a spring pad; there is no per-thing strength argument.

- Any actor that lands on that floor with its z-movement code (`P_ZMovement`, `p_mobj.cpp:3135-3139`)
  has its vertical velocity negated (bounces back up at the speed it landed with), is snapped to the
  floor, and skips the rest of that landing path (splash, `HitFloor`, player landing squat/sound).
  Floor-bouncing and exploding missiles are handled earlier in the same block and never reach it.
- A player jumping from the pad gets half the normal jump velocity (`p_user.cpp:2434`) and no jump
  delay (`:3201`).
- `+ALLOWCLIENTSPAWN` lets clients spawn it themselves, so the sector flag is set client-side too
  (inferred purpose; the flag's effect is what the thing's own code relies on).

## `PathNode`

Debug marker (`skulltagmisc.txt:118`, no editor number) spawned only by the bot A* pathfinder
(`astar.cpp:749-752` and three similar sites) when the `botdebug_shownodes` cvar (`bots.cpp:358`) is
nonzero; its `NODE` frames mark open-list, current, closed-list, and on-path nodes.

## Engine-family divergence

UZDoom has no `FloatyIcon`, `SpringPadZone`, or `PathNode` class and no medal/floaty-icon
subsystem: a search of its ZScript standard library (`wadsrc/static/zscript`) and C++ `src/` at
@98b16b78fc (5.1.0-pre) finds none of these names and no `PLANEF_SPRINGPAD` equivalent. A mod that
inherits from or replaces any of them is Zandronum-only.
