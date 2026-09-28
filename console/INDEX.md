# Console cvar/ccmd doc index

Router only. See `AGENTS.md` for where cvars/ccmds are declared in engine source,
`../shared/AUTHORING.md` for tiers/engine-scope/licensing.

## Concepts

- [The 3D view window's screen rectangle](concepts/view-window-geometry.md) — tier B. The exact
  `viewwidth`/`viewheight`/`viewwindowx`/`viewwindowy` table `screenblocks` produces (full screen at
  11+, `ST_Y`-tall at 10, bit-masked fractions below); why the view is always horizontally centred,
  and why the unpitched horizon sits at `floor(ST_Y/2)` for every value 3-10 rather than at screen
  centre. Shrinking the view **crops** rather than squashes: both software focal lengths derive from
  `viewwidth` and the aspect term comes from the full screen, never from `viewheight`. GL reaches the
  same result via `glScissor` and agrees exactly at `screenblocks >= 10`, differing by under 1% below
  it purely from the two renderers' different bit masks.
- [DMFlags: Bitfield cvars and their mechanics](concepts/dmflags.md) — tier A. Explains critical 2-bit field semantics for falling damage, jump, and crouch; documents the non-functional `DF_NO_ITEMS` flag; calls out source-comment inversions in `dmflags2` (`DF2_NO_AUTOMAP`, `DF2_NO_AUTOMAP_ALLIES`, `DF2_DISALLOW_SPYING`); notes `dmflags3` doesn't exist in Zandronum (GZDoom-family only).
- [Outbound traffic measurement](concepts/outbound-traffic-measurement.md) — tier A. What
  `sv_measureoutboundtraffic`/`dumptrafficmeasure` actually count: pre-compression stream bytes
  queued for clients during an actor class's `AActor::Tick` or a script's `RunScript`, counted once
  per recipient client, server-only, reset every map. Caveats: mid-window packet flushes charge
  whole packets to whoever triggered them, early returns in `AActor::Tick` drop bytes, player
  weapon traffic is never attributed, and `ACS_ExecuteWithResult` from an actor's tick credits the
  actor with the script's bytes. Contrasts `stat nettraffic` and the Win32 server GUI totals.
  Zandronum-only.

## Inventory tables (generated)

- [Console variables](inventory/cvars.md) — every `CVAR`/`CUSTOM_CVAR` declaration tree-wide.
- [Console commands](inventory/ccmds.md) — every `CCMD` declaration tree-wide.

## Notes (curated, per cvar/ccmd)

- [autoaim](notes/autoaim.md) — vertical-distance autoaim threshold; corrects a wiki description of a nonexistent horizontal-angle-preset system.
- [cl_backupcommands](notes/cl_backupcommands.md) — clamp range and packet-loss recovery semantics.
- [cl_ticsperupdate](notes/cl_ticsperupdate.md) — clamp range and bandwidth/latency tradeoff.
- [cl_usecustombob](notes/cl_usecustombob.md) — Zandronum-only client override of a weapon's bob style/speed and still bob; also `cl_alwaysbob`.
- [cl_usecustomsway](notes/cl_usecustomsway.md) — Zandronum-only client override of a weapon's sway speeds and style; on alone disables sway.
- [cl_usecustompitch](notes/cl_usecustompitch.md) — Zandronum-only client override of a weapon's pitch offset and style.
- [fov](notes/fov.md) — corrects the wiki's default (100 → 90) and documents `sv_minfov`/`sv_maxfov` server clamps.
- [handicap](notes/handicap.md) — corrects the wiki's hardcoded-100 assumption; actual clamp is `(0, deh.MaxSoulsphere)`, DEHACKED/IWAD-dependent.
- [instagib](notes/instagib.md) — `CVAR_LATCH` semantics (takes effect at the next `map` command or new game, not on `changemap` or a normal exit); forces rail hits to 999 damage.
- [teamdamage](notes/teamdamage.md) — takes effect immediately (no `CVAR_LATCH`), unlike `instagib`/`buckshot`.
- [sv_forbidvoteflags](notes/sv_forbidvoteflags.md) — master bitfield cvar with 13 named `sv_no*vote` aliases.
- [sv_maxclients / sv_maxplayers](notes/sv_maxclients.md) — connection-limit vs. active-player-limit distinction, admin bypass behavior.
- [sv_aircontrol](notes/sv_aircontrol.md) — fixed-point `1/256` default, interaction with `compat_limited_airmovement`.
- [sv_respawndelaytime](notes/sv_respawndelaytime.md) — sub-second float seconds, spawn-telefrag exemption.
- [sv_smartaim](notes/sv_smartaim.md) — four-value enum controlling autoaim target filtering; interacts with `autoaim`/`cl_doautoaim`/`sv_noautoaim`.
- [sv_maxpacketsize / sv_maxpacketspertick](notes/sv_maxpacketsize.md) — outgoing packet flush threshold and per-tick reliable-packet cap (Zandronum only).
- [addban](notes/addban.md) — time-format grammar for IP bans (minutes/hours/days/weeks/months/years/permanent, wildcards, IPv4-only).
- [kill](notes/kill.md) — `kill monsters`/`kill <class>` silently skip dormant actors; remove a dormant fixture by TID instead.
- [ban](notes/ban.md) — ban by player name; cross-references `addban`'s time grammar.
- [ban_idx](notes/ban_idx.md) — ban by player index; cross-references `addban`'s time grammar.
- [callvote](notes/callvote.md) — vote-type enumeration (Kick, ForceSpec, Map, ChangeMap, NextMap, NextSecret, ResetMap, FragLimit, TimeLimit, WinLimit, DuelLimit, PointLimit, Flag).
- [map](notes/map.md) — no-intermission map change; immediate client reconnection.
- [changemap](notes/changemap.md) — with-intermission map change; contrast to `map`.
- [dumptrafficmeasure](notes/dumptrafficmeasure.md) — server-only dump of per-actor-class/per-script traffic totals (silent on clients), ascending sort or `desc`; see `concepts/outbound-traffic-measurement.md` for what the numbers mean.
- [sv_measureoutboundtraffic](notes/sv_measureoutboundtraffic.md) — server-only recording switch; not archived or serverinfo, toggling doesn't reset the totals.
- [cleartrafficmeasure](notes/cleartrafficmeasure.md) — empties the traffic totals; also runs automatically on every map load.
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
- [cl_maxdecals](notes/cl_maxdecals.md) — limits impact decals only (map-placed and `SDF_PERMANENT` decals are never counted); 0 stops and removes impact decals; negative values clamp to 0.
- [con_scaletext](notes/con_scaletext.md) — Bool in Zandronum vs. Int (0–3) in UZDoom/GZDoom; the wiki's scaling-level behavior doesn't apply.
- [debuganimated](notes/debuganimated.md) — ANIMATED-lump debug output, printed during texture init; set it via startup commands (`+` args, `autoexec.cfg`), or set it later and re-run texture init (`restart` on Zandronum, `debug_restart` on UZDoom).
- [developer](notes/developer.md) — Zandronum boolean flag; the wiki's integer severity levels (1–4) don't exist in Zandronum.
- [msg](notes/msg.md) — message-level filter system, interacting with `msg0color`–`msg5color`.
- [msg5color](notes/msg5color.md) — Zandronum-specific private-chat color (message level 5); no ZDoom/GZDoom counterpart.
- [opl_numchips](notes/opl_numchips.md) — chip-count clamping (1–8); used by the OPL MIDI device (next song) and raw OPL formats (reset live, capped at 2).
- [screenblocks](notes/screenblocks.md) — wiki/Zandronum default divergence (wiki: 10, Zandronum: 11); clamp range 3–12.
- [st_scale](notes/st_scale.md) — tier B. `Bool`, defaults **on**, `CVAR_ARCHIVE` and **not** `CVAR_USERINFO` (so `GetCVar` answers the executing machine's own copy, never a remote player's). Decides the global `ST_Y`, the status bar's top screen row, via three distinct `DBaseStatusBar::SetScaled` formulas (unscaled, scaled, and a separate 5:4-aspect-bucket form) written in terms of the bar's own `RelTop`/`HorizontalResolution`/`VirticalResolution` rather than the stock Doom bar's 32/320/200, since an `SBARINFO` lump replaces all three and force-scales regardless of the cvar. Also records that `VirtualToRealCoords`'s `vbottom` offset is unreachable from a HUD message, while the 5:4 `ST_Y` formula includes the equivalent term.
- [snd_mididevice](notes/snd_mididevice.md) — platform-specific range/enumeration; declared separately for Windows vs. non-Windows.
- [snd_musicvolume](notes/snd_musicvolume.md) — volume-range clamping and callback semantics.
- [snd_sfxvolume](notes/snd_sfxvolume.md) — volume-range clamping and `CVAR_NOINITCALL`; wiki default (0.5) diverges from Zandronum's (1.0).
- [timidity_frequency](notes/timidity_frequency.md) — sample-rate clamping (4000–65000 Hz); wiki default (44100) diverges from Zandronum's (22050).
- [timidity_mastervolume](notes/timidity_mastervolume.md) — TiMidity++-specific output-scaling range.
- [transsouls](notes/transsouls.md) — Lost Soul translucency clamping (0.25–1.0) for the `SoulTrans` render style; on Zandronum only the stock `LostSoul` uses it, on UZDoom no stock actor does.
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
- [sv_timestampformat](notes/sv_timestampformat.md) — six timestamp formats for the Windows GUI server console (not the logfile), gated on `sv_timestamp`.
- [sv_useticbuffer](notes/sv_useticbuffer.md) — debug-build-only command buffering to smooth laggy-client jitter for other players.
- [sv_votecooldown](notes/sv_votecooldown.md) — minimum minutes between votes; corrects a stale wiki alias (`SV_LimitNumVotes`).
- [quicksave](notes/quicksave.md) — F6 default bind; branches on quicksave-slot-rotation and confirmation cvars, opens the Save menu if no slot is picked yet.
- [quickload](notes/quickload.md) — F9 default bind; loads the remembered quicksave slot; refuses in netgames (on Zandronum, in any non-single-player network state, including offline with bots).
- [menu_save](notes/menu_save.md) — F2 default bind; thin wrapper opening the `SavegameMenu` screen.
- [menu_load](notes/menu_load.md) — F3 default bind; thin wrapper opening the `LoadgameMenu` screen.
