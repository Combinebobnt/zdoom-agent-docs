# Console cvar/ccmd doc index

Router only. See `AGENTS.md` for where cvars/ccmds are declared in engine source,
`../shared/AUTHORING.md` for tiers/engine-scope/licensing.

## Concepts

- [DMFlags: Bitfield cvars and their mechanics](concepts/dmflags.md) — tier A. Explains critical 2-bit field semantics for falling damage, jump, and crouch; documents the non-functional `DF_NO_ITEMS` flag; calls out source-comment inversions in `dmflags2` (`DF2_NO_AUTOMAP`, `DF2_NO_AUTOMAP_ALLIES`, `DF2_DISALLOW_SPYING`); notes `dmflags3` doesn't exist in Zandronum (GZDoom-family only).

## Inventory tables (generated)

- [Console variables](inventory/cvars.md) — every `CVAR`/`CUSTOM_CVAR` declaration tree-wide.
- [Console commands](inventory/ccmds.md) — every `CCMD` declaration tree-wide.

## Notes (curated, per cvar/ccmd)

- [autoaim](notes/autoaim.md) — vertical-distance autoaim threshold; corrects a wiki description of a nonexistent horizontal-angle-preset system.
- [cl_backupcommands](notes/cl_backupcommands.md) — clamp range and packet-loss recovery semantics.
- [cl_ticsperupdate](notes/cl_ticsperupdate.md) — clamp range and bandwidth/latency tradeoff.
- [fov](notes/fov.md) — corrects the wiki's default (100 → 90) and documents `sv_minfov`/`sv_maxfov` server clamps.
- [handicap](notes/handicap.md) — corrects the wiki's hardcoded-100 assumption; actual clamp is `(0, deh.MaxSoulsphere)`, DEHACKED/IWAD-dependent.
- [instagib](notes/instagib.md) — `CVAR_LATCH` semantics (takes effect next map, not immediately).
- [teamdamage](notes/teamdamage.md) — takes effect immediately (no `CVAR_LATCH`), unlike `instagib`/`buckshot`.
- [sv_forbidvoteflags](notes/sv_forbidvoteflags.md) — master bitfield cvar with 13 named `sv_no*vote` aliases.
- [sv_maxclients / sv_maxplayers](notes/sv_maxclients.md) — connection-limit vs. active-player-limit distinction, admin bypass behavior.
- [sv_aircontrol](notes/sv_aircontrol.md) — fixed-point `1/256` default, interaction with `compat_limited_airmovement`.
- [sv_respawndelaytime](notes/sv_respawndelaytime.md) — sub-second float seconds, spawn-telefrag exemption.
- [sv_smartaim](notes/sv_smartaim.md) — four-value enum controlling autoaim target filtering; interacts with `autoaim`/`cl_doautoaim`/`sv_noautoaim`.
- [sv_maxpacketsize / sv_maxpacketspertick](notes/sv_maxpacketsize.md) — UDP packet size and transmission-rate tuning.
- [addban](notes/addban.md) — time-format grammar for IP bans (minutes/hours/days/weeks/months/years/permanent, wildcards, IPv4-only).
- [ban](notes/ban.md) — ban by player name; cross-references `addban`'s time grammar.
- [ban_idx](notes/ban_idx.md) — ban by player index; cross-references `addban`'s time grammar.
- [callvote](notes/callvote.md) — vote-type enumeration (Kick, ForceSpec, Map, ChangeMap, NextMap, NextSecret, ResetMap, FragLimit, TimeLimit, WinLimit, DuelLimit, PointLimit, Flag).
- [map](notes/map.md) — no-intermission map change; immediate client reconnection.
- [changemap](notes/changemap.md) — with-intermission map change; contrast to `map`.
- [dumptrafficmeasure](notes/dumptrafficmeasure.md) — network traffic diagnostics; requires `sv_measureoutboundtraffic`.
- [stat](notes/stat.md) — enumerated diagnostic/profiling stat properties.
- [addmap / insertmap](notes/addmap.md) — optional minplayers/maxplayers limits.
- [ignore / ignore_idx](notes/ignore.md) — duration unit (minutes) and indefinite-omit semantics.
- [kickfromgame / kickfromgame_idx](notes/kickfromgame.md) — deprecated; equivalent to `forcespec`.
- [login_add](notes/login_add.md) — available on Windows and Linux (libsecret); corrects a wiki claim of Windows-only.
- [sayto / sayto_idx](notes/sayto.md) — magic values (`"Server"` name, index `-1`) for addressing the server.
- [am_cheat](notes/am_cheat.md) — 0–6 mode enum controlling automap cheat visibility; does not persist to config.
- [am_drawmapback](notes/am_drawmapback.md) — mode enum (not boolean); mode 2 draws mod-defined/Raven colors only.
- [am_rotate](notes/am_rotate.md) — 0–2 mode enum (not boolean); mode 2 is overlay-conditional.
- [am_showtriggerlines](notes/am_showtriggerlines.md) — ZDoom divergence: Zandronum is Bool-only, no door/non-door distinction.
- [chat_substitution](notes/chat_substitution.md) — keyword substitution in chat messages; Zandronum adds a `$location` keyword absent from the ZDoom wiki.
- [cl_maxdecals](notes/cl_maxdecals.md) — negative values clamp to 0; zero disables decals entirely.
- [con_scaletext](notes/con_scaletext.md) — Bool in Zandronum vs. Int (0–3) in UZDoom/GZDoom; the wiki's scaling-level behavior doesn't apply.
- [debuganimated](notes/debuganimated.md) — ANIMATED-lump debug output; only settable from the command line/`autoexec.cfg`, since the lump loads before the console exists.
- [developer](notes/developer.md) — Zandronum boolean flag; the wiki's integer severity levels (1–4) don't exist in Zandronum.
- [msg](notes/msg.md) — message-level filter system, interacting with `msg0color`–`msg5color`.
- [msg5color](notes/msg5color.md) — Zandronum-specific private-chat color (message level 5); no ZDoom/GZDoom counterpart.
- [opl_numchips](notes/opl_numchips.md) — chip-count clamping (1–8) and a real-time reset callback.
- [screenblocks](notes/screenblocks.md) — wiki/Zandronum default divergence (wiki: 10, Zandronum: 11); clamp range 3–12.
- [snd_mididevice](notes/snd_mididevice.md) — platform-specific range/enumeration; declared separately for Windows vs. non-Windows.
- [snd_musicvolume](notes/snd_musicvolume.md) — volume-range clamping and callback semantics.
- [snd_sfxvolume](notes/snd_sfxvolume.md) — volume-range clamping and `CVAR_NOINITCALL`; wiki default (0.5) diverges from Zandronum's (1.0).
- [timidity_frequency](notes/timidity_frequency.md) — sample-rate clamping (4000–65000 Hz); wiki default (44100) diverges from Zandronum's (22050).
- [timidity_mastervolume](notes/timidity_mastervolume.md) — TiMidity++-specific output-scaling range.
- [transsouls](notes/transsouls.md) — Lost Soul translucency clamping (0.25–1.0); interacts with the `SoulTrans` render style.
- [sv_allowprivatechat](notes/sv_allowprivatechat.md) — three-value enum (off / anyone / teammates only).
- [sv_allowvoicechat](notes/sv_allowvoicechat.md) — four-mode voice-chat scoping; corrects a wiki claim that it's alpha-only (it shipped in 3.2.1).
- [sv_colorstripmethod](notes/sv_colorstripmethod.md) — controls color-code handling in console/logfile output, not in-game chat.
- [sv_coop_damagefactor](notes/sv_coop_damagefactor.md) — monster-to-player damage multiplier only; doesn't affect PvP or player-to-monster damage.
- [sv_defaultdmflags](notes/sv_defaultdmflags.md) — auto-populates dmflags per game mode; see `concepts/dmflags.md` for the bitfields themselves.
- [sv_dropstyle](notes/sv_dropstyle.md) — controls monster item-drop scatter pattern (default/Doom/Strife).
- [sv_fastweapons](notes/sv_fastweapons.md) — weapon-frame cycling speed; mode 2 skips non-codepointer frames.
- [sv_forcelogintojoin](notes/sv_forcelogintojoin.md) — forces spectate until account-server auth succeeds; distinct from `sv_forcepassword`.
- [sv_forcerespawntime](notes/sv_forcerespawntime.md) — idle-respawn cooldown; only takes effect with the `SV_ForceRespawn` dmflag set.
- [sv_limitcommands](notes/sv_limitcommands.md) — debug-build-only command-flood throttling (join/suicide/team-change).
- [sv_maxacsbanduration](notes/sv_maxacsbanduration.md) — caps how long ACS's `BanFromGame()` can ban for; 0 disables it entirely.
- [sv_nocallvote](notes/sv_nocallvote.md) — master vote on/off switch, distinct from `SV_ForbidVoteFlags`'s per-type filtering.
- [sv_timestampformat](notes/sv_timestampformat.md) — six timestamp formats for the server console/logfile, gated on `sv_timestamp`.
- [sv_useticbuffer](notes/sv_useticbuffer.md) — debug-build-only command buffering to smooth laggy-client jitter for other players.
- [sv_votecooldown](notes/sv_votecooldown.md) — minimum minutes between votes; corrects a stale wiki alias (`SV_LimitNumVotes`).
- [quicksave](notes/quicksave.md) — F6 default bind; branches on quicksave-slot-rotation and confirmation cvars, opens the Save menu if no slot is picked yet.
- [quickload](notes/quickload.md) — F9 default bind; loads the remembered quicksave slot, refuses outright in netgames.
- [menu_save](notes/menu_save.md) — F2 default bind; thin wrapper opening the `SavegameMenu` screen.
- [menu_load](notes/menu_load.md) — F3 default bind; thin wrapper opening the `LoadgameMenu` screen.
