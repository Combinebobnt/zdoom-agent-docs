# Console variables (CVars)

**Generated:** by `python3 tools/gen_inventory.py console-cvars` from every `CVAR`/`CUSTOM_CVAR` declaration tree-wide in the Zandronum source's `src/` (~197 files declare at least one -- see `../AGENTS.md`), plus a handful of cvars declared via a raw `F*CVar` constructor bypassing those macros (e.g. `skill`/`msg`/`noise` -- the engine-visible name is the constructor's quoted string argument, not the C++ variable name); UZDoom's own equivalent of the bypass is the `CVARD`/`CUSTOM_CVARD` "documented" macro family, whose `_NAMED` variants (`CVARD_NAMED`/`CUSTOM_CVARD_NAMED`) also split the console name from the C++ variable name -- both matched for the `UZD` column, cross-referenced against the UZDoom source's `src/` tree by name for the `UZD` column. `Flags` is the raw flag-macro expression from the declaration (e.g. `CVAR_ARCHIVE | CVAR_NOSETBYACS`), not yet decoded per-flag -- see `zandronum/docs/commands.txt` for prose meaning. Do not hand-edit rows; use `../notes/<name>.md` instead -- its `Tier`/`Notes` cell is picked up automatically on the next regen. Extraction reads the Zandronum source as its base (confirmed present for every row); UZDoom presence is a name cross-reference only (the `UZD` column). **Tier:** per row.

| CVar | Type | Kind | Flags | Zan | UZD | Tier | Notes |
|---|---|---|---|---|---|---|---|
| acstimestamp | Int | plain | CVAR_ARCHIVE \| CVAR_NOSETBYACS | yes | — | C |  |
| addrocketexplosion | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| allcheats | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| alwaysapplydmflags | Bool | custom | CVAR_SERVERINFO \| CVAR_GAMEPLAYSETTING | yes | yes | C |  |
| am_backcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_cdwallcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_cheat | Int | custom | 0 | yes | yes | A | [notes](../notes/am_cheat.md) |
| am_colorset | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_customcolors | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_drawmapback | Int | plain | CVAR_ARCHIVE | yes | yes | A | [notes](../notes/am_drawmapback.md) |
| am_efwallcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_fdwallcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_followplayer | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_gridcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_interlevelcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_intralevelcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_lockedcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_map_secrets | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_notseencolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_ovcdwallcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_ovefwallcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_overlay | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_ovfdwallcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_ovinterlevelcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_ovlockedcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_ovotherwallscolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_ovsecretsectorcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_ovsecretwallcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_ovspecialwallcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_ovtelecolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_ovthingcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_ovthingcolor_citem | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_ovthingcolor_friend | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_ovthingcolor_item | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_ovthingcolor_monster | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_ovthingcolor_ncmonster | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_ovunseencolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_ovwallcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_ovyourcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_rotate | Int | plain | CVAR_ARCHIVE | yes | yes | A | [notes](../notes/am_rotate.md) |
| am_secretsectorcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_secretwallcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_showalllines | Int | custom | 0 | yes | yes | C |  |
| am_showitems | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_showkeys | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_showmaplabel | Int | custom | CVAR_ARCHIVE | yes | yes | C |  |
| am_showmonsters | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_showsecrets | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_showsubsector | Int | plain | 0 | yes | yes | C |  |
| am_showthingsprites | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_showtime | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_showtotaltime | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_showtriggerlines | Bool | plain | CVAR_ARCHIVE | yes | yes | A | [notes](../notes/am_showtriggerlines.md) |
| am_specialwallcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_textured | Bool | custom | CVAR_ARCHIVE | yes | yes | C |  |
| am_thingcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_thingcolor_citem | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_thingcolor_friend | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_thingcolor_item | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_thingcolor_monster | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_thingcolor_ncmonster | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_tswallcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_wallcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_xhaircolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| am_yourcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| authhostname | String | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| autoaim | Float | plain | CVAR_USERINFO \| CVAR_ARCHIVE | yes | yes | A | [notes](../notes/autoaim.md) |
| autosavecount | Int | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| autosavenum | Int | plain | CVAR_NOSET\|CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| bgamma | Float | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| blood_fade_scalar | Float | plain | CVAR_ARCHIVE | yes | yes | C |  |
| blood_fade_usemaxhealth | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| bot_allowchat | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| botdebug_commands | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| botdebug_dataheaders | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| botdebug_maxgiveupnodes | Float | plain | CVAR_ARCHIVE | yes | — | C |  |
| botdebug_maxroamgiveupnodes | Float | plain | CVAR_ARCHIVE | yes | — | C |  |
| botdebug_maxsearchnodes | Float | plain | CVAR_ARCHIVE | yes | — | C |  |
| botdebug_obstructiontest | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| botdebug_showcosts | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| botdebug_showevents | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| botdebug_showgoal | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| botdebug_shownodes | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| botdebug_showstackpushes | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| botdebug_statechanges | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| botdebug_states | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| botdebug_walktest | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| botskill | Int | custom | CVAR_SERVERINFO \| CVAR_LATCH | yes | — | C |  |
| buckshot | Bool | plain | CVAR_SERVERINFO \| CVAR_LATCH \| CVAR_CAMPAIGNLOCK \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| cd_drive | String | custom | CVAR_ARCHIVE\|CVAR_NOINITCALL\|CVAR_GLOBALCONFIG | yes | — | C |  |
| cd_enabled | Bool | custom | CVAR_ARCHIVE\|CVAR_NOINITCALL\|CVAR_GLOBALCONFIG | yes | — | C |  |
| chase_dist | Float | custom | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | yes | C |  |
| chase_height | Float | plain | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | yes | C |  |
| chasedemo | Bool | plain | 0 | yes | yes | C |  |
| chat_sound | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| chat_substitution | Bool | plain | CVAR_ARCHIVE | yes | yes | A | [notes](../notes/chat_substitution.md) |
| chatmacro0 | String | plain | CVAR_ARCHIVE | yes | yes | C |  |
| chatmacro1 | String | plain | CVAR_ARCHIVE | yes | yes | C |  |
| chatmacro2 | String | plain | CVAR_ARCHIVE | yes | yes | C |  |
| chatmacro3 | String | plain | CVAR_ARCHIVE | yes | yes | C |  |
| chatmacro4 | String | plain | CVAR_ARCHIVE | yes | yes | C |  |
| chatmacro5 | String | plain | CVAR_ARCHIVE | yes | yes | C |  |
| chatmacro6 | String | plain | scumbag...", CVAR_ARCHIVE | yes | yes | C |  |
| chatmacro7 | String | plain | CVAR_ARCHIVE | yes | yes | C |  |
| chatmacro8 | String | plain | CVAR_ARCHIVE | yes | yes | C |  |
| chatmacro9 | String | plain | CVAR_ARCHIVE | yes | yes | C |  |
| cl_allowmultipleannouncersounds | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| cl_allycolor | Color | custom | CVAR_ARCHIVE | yes | — | C |  |
| cl_alwaysbob | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_alwaysplayfragsleft | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| cl_announcepickups | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_announcer | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_autologin | Bool | custom | CVAR_ARCHIVE \| CVAR_NOINITCALL | yes | — | C |  |
| cl_autoready | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_backupcommands | Int | custom | CVAR_ARCHIVE | yes | — | A | [notes](../notes/cl_backupcommands.md) |
| cl_bloodsplats | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| cl_bloodtype | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| cl_bobrangex | Float | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_bobrangey | Float | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_bobspeed | Float | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_bobstyle | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| cl_buffercommands | Bool | custom | CVAR_ARCHIVE \| CVAR_NOSETBYACS \| CVAR_DEBUGONLY | yes | — | C |  |
| cl_capfps | Bool | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| cl_chatprefix | String | custom | CVAR_ARCHIVE | yes | — | C |  |
| cl_chatsuffix | String | custom | CVAR_ARCHIVE | yes | — | C |  |
| cl_clientflags | Int | custom | CVAR_USERINFO \| CVAR_ARCHIVE | yes | — | C |  |
| cl_clientsidepuffs | Flag | plain | CLIENTFLAGS_CLIENTSIDEPUFFS | yes | — | C |  |
| cl_colorizepings | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_connect_flags | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| cl_connectiontype | Int | plain | CVAR_USERINFO \| CVAR_ARCHIVE | yes | — | C |  |
| cl_connectsound | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_disallowfullpitch | Bool | custom | CVAR_ARCHIVE | yes | — | C |  |
| cl_doautoaim | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| cl_dontrestorefrags | Flag | plain | CCF_DONTRESTOREFRAGS | yes | — | C |  |
| cl_drawcoopinfo | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_emulatepacketloss | Bool | plain | 0 | yes | — | C |  |
| cl_enemycolor | Color | custom | CVAR_ARCHIVE | yes | — | C |  |
| cl_freechase | Bool | custom | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | — | C |  |
| cl_grenadetrails | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_hideaccount | Bool | custom | CVAR_ARCHIVE | yes | — | C |  |
| cl_hidecountry | Flag | plain | CCF_HIDECOUNTRY | yes | — | C |  |
| cl_hidevotescreen | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_hitscandecalhack | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_icons | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_identifymonsters | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_identifytarget | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_intermissiontimer | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_interpolateweapons | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_joinpassword | String | plain | 0 | yes | — | C |  |
| cl_jumpswayspeed | Float | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_keepserversettings | Bool | plain | CVAR_ARCHIVE \| CVAR_DEBUGONLY | yes | — | C |  |
| cl_maxdecals | Int | custom | CVAR_ARCHIVE | yes | yes | A | [notes](../notes/cl_maxdecals.md) |
| cl_maxscoreboardheight | Float | custom | CVAR_ARCHIVE | yes | — | C |  |
| cl_maxscoreboardwidth | Float | custom | CVAR_ARCHIVE | yes | — | C |  |
| cl_medals | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_missiledecals | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| cl_motdtime | Float | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_motionswayspeed | Float | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_netgraph | Bool | plain | CVAR_ARCHIVE \| CVAR_NOSETBYACS | yes | — | C |  |
| cl_noammoswitch | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_nocountriesifunavailable | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_noprediction | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| cl_noswitchonfire | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| cl_oldfreelooklimit | Bool | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| cl_onekey | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_overrideplayercolors | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| cl_password | String | plain | 0 | yes | — | C |  |
| cl_predict_players | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_protectcvars | Bool | plain | CVAR_ARCHIVE \| CVAR_NOSETBYACS | yes | — | C |  |
| cl_pufftype | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| cl_respawninvuleffect | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_respawnonfire | Flag | plain | CLIENTFLAGS_RESPAWNONFIRE | yes | — | C |  |
| cl_rockettrails | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| cl_run | Bool | plain | CVAR_GLOBALCONFIG\|CVAR_ARCHIVE | yes | yes | C |  |
| cl_scoreboardalpha | Float | custom | CVAR_ARCHIVE | yes | — | C |  |
| cl_scoreboardhorizalign | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| cl_scoreboardscreenheight | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| cl_scoreboardscreenwidth | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| cl_scoreboardscrollspeed | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| cl_scoreboardvertalign | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| cl_scoreboardx | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_scoreboardy | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_showallyicon | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| cl_showcommands | Int | plain | CVAR_ARCHIVE\|CVAR_DEBUGONLY | yes | — | C |  |
| cl_showenemyicon | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| cl_showfullscreenvote | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_showlargefragmessages | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_showonetickpredictionerrors | Bool | plain | 0 | yes | — | C |  |
| cl_showpacketloss | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_showpredictionsuccess | Bool | plain | 0 | yes | — | C |  |
| cl_showscoreleft | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_showspawnnames | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_showspawns | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_showwarnings | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_skins | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| cl_soundwhennotactive | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| cl_spectatormode | Int | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| cl_spectatormove | Float | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| cl_spreaddecals | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| cl_startasspectator | Flag | plain | CCF_STARTASSPECTATOR | yes | — | C |  |
| cl_stfullscreenhud | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_stillbobrange | Float | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_stillbobspeed | Float | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_swaystyle | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| cl_taunts | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_telespy | Bool | plain | CVAR_GLOBALCONFIG\|CVAR_ARCHIVE | yes | — | C |  |
| cl_ticsperupdate | Int | plain | CVAR_USERINFO \| CVAR_ARCHIVE | yes | — | A | [notes](../notes/cl_ticsperupdate.md) |
| cl_unlagged | Flag | plain | CLIENTFLAGS_UNLAGGED | yes | — | C |  |
| cl_usealpha3countrycode | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_usecustombob | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_usecustompitch | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_usecustomsway | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_useoriginalweaponorder | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_usescoreboardscale | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_usescoreboardscale_screenratio | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_useshortcolumnnames | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_useskulltagmouse | Bool | plain | CVAR_GLOBALCONFIG \| CVAR_ARCHIVE | yes | — | C |  |
| cl_viewbob | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_viewpitchoffset | Float | plain | CVAR_ARCHIVE | yes | — | C |  |
| cl_viewpitchstyle | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| cl_viewswayspeed | Float | plain | CVAR_ARCHIVE | yes | — | C |  |
| color | Color | plain | CVAR_USERINFO \| CVAR_ARCHIVE | yes | yes | C |  |
| colorset | Int | plain | CVAR_USERINFO \| CVAR_ARCHIVE | yes | yes | C |  |
| compat_anybossdeath | Flag | plain | COMPATF_ANYBOSSDEATH | yes | yes | C |  |
| compat_autoaim | Flag | plain | ZACOMPATF_AUTOAIM | yes | — | C |  |
| compat_badangles | Flag | plain | COMPATF2_BADANGLES | yes | yes | C |  |
| compat_boomscroll | Flag | plain | COMPATF_BOOMSCROLL | yes | yes | C |  |
| compat_bridgedrops | Flag | plain | ZACOMPATF_OLD_BRIDGE_DROPS | yes | — | C |  |
| compat_clientssendfullbuttoninfo | Flag | plain | ZACOMPATF_CLIENTS_SEND_FULL_BUTTON_INFO | yes | — | C |  |
| compat_corpsegibs | Flag | plain | COMPATF_CORPSEGIBS | yes | — | C |  |
| compat_crossdropoff | Flag | plain | COMPATF_CROSSDROPOFF | yes | yes | C |  |
| compat_dehhealth | Flag | plain | COMPATF_DEHHEALTH | yes | yes | C |  |
| compat_disablestealthmonsters | Flag | plain | ZACOMPATF_DISABLESTEALTHMONSTERS | yes | — | C |  |
| compat_disabletaunts | Flag | plain | ZACOMPATF_DISABLETAUNTS | yes | — | C |  |
| compat_dont_stop_player_scripts_on_disconnect | Flag | plain | ZACOMPATF_DONT_STOP_PLAYER_SCRIPTS_ON_DISCONNECT | yes | — | C |  |
| compat_dropoff | Flag | plain | COMPATF_DROPOFF | yes | yes | C |  |
| compat_explosionthrust | Flag | plain | ZACOMPATF_OLD_EXPLOSION_THRUST | yes | — | C |  |
| compat_floormove | Flag | plain | COMPATF2_FLOORMOVE | yes | yes | C |  |
| compat_fullweaponlower | Flag | plain | ZACOMPATF_FULL_WEAPON_LOWER | yes | — | C |  |
| compat_hitscan | Flag | plain | COMPATF_HITSCAN | yes | yes | C |  |
| compat_instantrespawn | Flag | plain | ZACOMPATF_INSTANTRESPAWN | yes | — | C |  |
| compat_invisibility | Flag | plain | COMPATF_INVISIBILITY | yes | yes | C |  |
| compat_light | Flag | plain | COMPATF_LIGHT | yes | yes | C |  |
| compat_limited_airmovement | Flag | plain | ZACOMPATF_LIMITED_AIRMOVEMENT | yes | — | C |  |
| compat_limitpain | Flag | plain | COMPATF_LIMITPAIN | yes | yes | C |  |
| compat_maskedmidtex | Flag | plain | COMPATF_MASKEDMIDTEX | yes | yes | C |  |
| compat_mbfmonstermove | Flag | plain | COMPATF_MBFMONSTERMOVE | yes | yes | C |  |
| compat_minotaur | Flag | plain | COMPATF_MINOTAUR | yes | yes | C |  |
| compat_missileclip | Flag | plain | COMPATF_MISSILECLIP | yes | yes | C |  |
| compat_mushroom | Flag | plain | COMPATF_MUSHROOM | yes | yes | C |  |
| compat_netscriptsareclientside | Flag | plain | ZACOMPATF_NETSCRIPTS_ARE_CLIENTSIDE | yes | — | C |  |
| compat_noblockfriends | Flag | plain | COMPATF_NOBLOCKFRIENDS | yes | yes | C |  |
| compat_nocrosshair | Flag | plain | ZACOMPATF_NO_CROSSHAIR | yes | — | C |  |
| compat_nodoorlight | Flag | plain | COMPATF_NODOORLIGHT | yes | yes | C |  |
| compat_nogravity_spheres | Flag | plain | ZACOMPATF_NOGRAVITY_SPHERES | yes | — | C |  |
| compat_noland | Flag | plain | ZACOMPATF_NO_LAND | yes | — | C |  |
| compat_noobituaries | Flag | plain | ZACOMPATF_NO_OBITUARIES | yes | — | C |  |
| compat_nopassover | Flag | plain | COMPATF_NO_PASSMOBJ | yes | yes | C |  |
| compat_notossdrops | Flag | plain | COMPATF_NOTOSSDROPS | yes | yes | C |  |
| compat_oldintermission | Flag | plain | ZACOMPATF_OLDINTERMISSION | yes | — | C |  |
| compat_oldradiusdmg | Flag | plain | ZACOMPATF_OLDRADIUSDMG | yes | — | C |  |
| compat_oldrandom | Flag | plain | ZACOMPATF_OLD_RANDOM_GENERATOR | yes | — | C |  |
| compat_oldweaponswitch | Flag | plain | ZACOMPATF_OLD_WEAPON_SWITCH | yes | — | C |  |
| compat_oldzdoomzmovement | Flag | plain | ZACOMPATF_OLD_ZDOOM_ZMOVEMENT | yes | — | C |  |
| compat_originalsoundcurve | Flag | plain | ZACOMPATF_ORIGINALSOUNDCURVE | yes | — | C |  |
| compat_plasmabump | Flag | plain | ZACOMPATF_PLASMA_BUMP_BUG | yes | — | C |  |
| compat_polyobj | Flag | plain | COMPATF_POLYOBJ | yes | yes | C |  |
| compat_pushwindow | Flag | plain | COMPATF2_PUSHWINDOW | yes | yes | C |  |
| compat_ravenscroll | Flag | plain | COMPATF_RAVENSCROLL | yes | yes | C |  |
| compat_resetglobalvarsonmapreset | Flag | plain | ZACOMPATF_RESET_GLOBALVARS_ON_MAPRESET | yes | — | C |  |
| compat_sectorsounds | Flag | plain | COMPATF_SECTORSOUNDS | yes | yes | C |  |
| compat_shortTex | Flag | plain | COMPATF_SHORTTEX | yes | yes | C |  |
| compat_silentinstantfloors | Flag | plain | COMPATF_SILENT_INSTANT_FLOORS | yes | yes | C |  |
| compat_silentpickup | Flag | plain | COMPATF_SILENTPICKUP | yes | yes | C |  |
| compat_silentwestspawns | Flag | plain | ZACOMPATF_SILENT_WEST_SPAWNS | yes | — | C |  |
| compat_skulltagjumping | Flag | plain | ZACOMPATF_SKULLTAG_JUMPING | yes | — | C |  |
| compat_soundslots | Flag | plain | COMPATF_MAGICSILENCE | yes | yes | C |  |
| compat_soundtarget | Flag | plain | COMPATF_SOUNDTARGET | yes | yes | C |  |
| compat_spritesort | Flag | plain | COMPATF_SPRITESORT | yes | yes | C |  |
| compat_stairs | Flag | plain | COMPATF_STAIRINDEX | yes | yes | C |  |
| compat_trace | Flag | plain | COMPATF_TRACE | yes | yes | C |  |
| compat_useblocking | Flag | plain | COMPATF_USEBLOCKING | yes | yes | C |  |
| compat_wallrun | Flag | plain | COMPATF_WALLRUN | yes | yes | C |  |
| compatflags | Int | custom | CVAR_SERVERINFO \| CVAR_CAMPAIGNLOCK \| CVAR_GAMEPLAYFLAGSET | yes | yes | C |  |
| compatflags2 | Int | custom | CVAR_SERVERINFO \| CVAR_CAMPAIGNLOCK \| CVAR_GAMEPLAYFLAGSET | yes | yes | C |  |
| compatmode | Int | custom | CVAR_ARCHIVE\|CVAR_NOINITCALL\|CVAR_SERVERINFO | yes | yes | C |  |
| con_alpha | Float | custom | CVAR_ARCHIVE | yes | yes | C |  |
| con_centernotify | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| con_colorinmessages | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| con_ctrl_d | String | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| con_interpolate | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| con_midtime | Float | plain | CVAR_ARCHIVE | yes | yes | C |  |
| con_notablist | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| con_notifylines | Int | custom | CVAR_ARCHIVE | yes | yes | C |  |
| con_notifytime | Float | plain | CVAR_ARCHIVE | yes | yes | C |  |
| con_scaletext | Bool | custom | CVAR_ARCHIVE | yes | yes | A | [notes](../notes/con_scaletext.md) |
| con_scaletext_usescreenratio | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| con_showtimestamps | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| con_speed | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| con_virtualheight | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| con_virtualwidth | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| cooperative | Bool | custom | CVAR_SERVERINFO \| CVAR_LATCH \| CVAR_CAMPAIGNLOCK \| CVAR_NOINITCALL | yes | — | C |  |
| crashlog_dir | String | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| crashlogs | Int | plain | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | — | C |  |
| crosshair | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| crosshaircolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| crosshairforce | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| crosshairgrow | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| crosshairhealth | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| crosshairscale | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| ctf | Bool | custom | CVAR_SERVERINFO \| CVAR_LATCH \| CVAR_CAMPAIGNLOCK | yes | — | C |  |
| d3d_antilag | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| d3d_showpacks | Int | plain | 0 | yes | — | C |  |
| database_maxpagecount | Int | custom | CVAR_ARCHIVE\|CVAR_NOSETBYACS | yes | — | C |  |
| databasefile | String | custom | CVAR_ARCHIVE\|CVAR_NOSETBYACS | yes | — | C |  |
| deathmatch | Bool | custom | CVAR_SERVERINFO \| CVAR_LATCH \| CVAR_CAMPAIGNLOCK | yes | yes | C |  |
| debuganimated | Bool | plain | 0 | yes | yes | A | [notes](../notes/debuganimated.md) |
| defaultiwad | String | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| dehload | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| demo_compress | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| demo_pure | Bool | custom | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | — | C |  |
| developer | Bool | plain | 0 | yes | yes | A | [notes](../notes/developer.md) |
| dimamount | Float | custom | CVAR_ARCHIVE | yes | yes | C |  |
| dimcolor | Color | plain | CVAR_ARCHIVE | yes | yes | C |  |
| disableautosave | Int | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| displaynametags | Int | custom | CVAR_ARCHIVE | yes | yes | C |  |
| dlg_musicvolume | Float | custom | CVAR_ARCHIVE | yes | yes | C |  |
| dmflags | Int | custom | CVAR_SERVERINFO \| CVAR_CAMPAIGNLOCK \| CVAR_GAMEPLAYFLAGSET | yes | yes | A | [notes](concepts/dmflags.md) |
| dmflags2 | Int | custom | CVAR_SERVERINFO \| CVAR_CAMPAIGNLOCK \| CVAR_GAMEPLAYFLAGSET | yes | yes | A | [notes](concepts/dmflags.md) |
| domination | Bool | custom | CVAR_SERVERINFO \| CVAR_LATCH \| CVAR_CAMPAIGNLOCK | yes | — | C |  |
| duel | Bool | custom | CVAR_SERVERINFO \| CVAR_LATCH \| CVAR_CAMPAIGNLOCK | yes | — | C |  |
| duellimit | Int | custom | CVAR_CAMPAIGNLOCK \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| dumpsections | Bool | plain | 0 | yes | — | C |  |
| dumpspawnedthings | Bool | plain | 0 | yes | yes | C |  |
| eaxedit_test | Bool | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG\|CVAR_NOINITCALL | yes | yes | C |  |
| fluid_chorus | Bool | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| fluid_chorus_depth | Float | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| fluid_chorus_level | Float | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| fluid_chorus_speed | Float | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| fluid_chorus_type | Int | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| fluid_chorus_voices | Int | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| fluid_gain | Float | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| fluid_interp | Int | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| fluid_patchset | String | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| fluid_reverb | Bool | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| fluid_reverb_damping | Float | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| fluid_reverb_level | Float | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| fluid_reverb_roomsize | Float | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| fluid_reverb_width | Float | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| fluid_samplerate | Int | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| fluid_threads | Int | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| fluid_voices | Int | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| forcewater | Bool | custom | CVAR_ARCHIVE\|CVAR_SERVERINFO | yes | yes | C |  |
| fov | Float | custom | CVAR_ARCHIVE \| CVAR_USERINFO \| CVAR_UNSYNCED_USERINFO \| CVAR_NOINITCALL | yes | yes | A | [notes](../notes/fov.md) |
| fraglimit | Int | custom | CVAR_SERVERINFO \| CVAR_CAMPAIGNLOCK \| CVAR_GAMEPLAYSETTING | yes | yes | C |  |
| freelook | Bool | plain | CVAR_GLOBALCONFIG\|CVAR_ARCHIVE | yes | yes | C |  |
| fullscreen | Bool | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG\|CVAR_NOINITCALL | yes | — | C |  |
| g15_enable | Bool | custom | CVAR_ARCHIVE | yes | — | C |  |
| g15_showlargefragmessages | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| Gamma | Float | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| genblockmap | Bool | plain | CVAR_SERVERINFO\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| gender | String | plain | CVAR_USERINFO \| CVAR_ARCHIVE | yes | yes | C |  |
| genglnodes | Bool | plain | CVAR_SERVERINFO | yes | — | C |  |
| gennodes | Bool | plain | CVAR_SERVERINFO\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| ggamma | Float | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| gl_aalines | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| gl_attachedlights | Bool | plain | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | — | C |  |
| gl_billboard_mode | Int | plain | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | yes | C |  |
| gl_billboard_particles | Bool | plain | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | yes | C |  |
| gl_brightfog | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| gl_brightmap_shader | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG\|CVAR_NOINITCALL | yes | — | C |  |
| gl_cachenodes | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| gl_cachetime | Float | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| gl_clamp_per_texture | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| gl_colormap_shader | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG\|CVAR_NOINITCALL | yes | — | C |  |
| gl_debug | Bool | plain | 0 | yes | yes | C |  |
| gl_direct_state_change | Bool | plain | 0 | yes | — | C |  |
| gl_distfog | Int | custom | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | yes | C |  |
| gl_draw_sync | Bool | plain | 0 | yes | — | C |  |
| gl_dynlight_shader | Bool | custom | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG \| CVAR_NOINITCALL | yes | — | C |  |
| gl_enhanced_nightvision | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| gl_enhanced_nv_stealth | Int | plain | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | yes | C |  |
| gl_fog_shader | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG\|CVAR_NOINITCALL | yes | — | C |  |
| gl_fogmode | Int | custom | CVAR_ARCHIVE\|CVAR_NOINITCALL | yes | yes | C |  |
| gl_forcemultipass | Bool | plain | 0 | yes | — | C |  |
| gl_fuzztype | Int | custom | CVAR_ARCHIVE | yes | yes | C |  |
| gl_glow_shader | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG\|CVAR_NOINITCALL | yes | — | C |  |
| gl_interpolate_model_frames | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| gl_light_ambient | Int | custom | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | — | C |  |
| gl_light_models | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| gl_light_particles | Bool | plain | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | yes | C |  |
| gl_light_sprites | Bool | plain | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | yes | C |  |
| gl_lightmode | Int | custom | CVAR_ARCHIVE\|CVAR_NOINITCALL | yes | yes | C |  |
| gl_lights | Bool | custom | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG \| CVAR_NOINITCALL | yes | — | C |  |
| gl_lights_additive | Bool | custom | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG \| CVAR_NOINITCALL | yes | — | C |  |
| gl_lights_checkside | Bool | plain | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | — | C |  |
| gl_lights_intensity | Float | plain | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | — | C |  |
| gl_lights_size | Float | plain | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | — | C |  |
| gl_mask_sprite_threshold | Float | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| gl_mask_threshold | Float | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG\|CVAR_DEBUGONLY | yes | yes | C |  |
| gl_mirror_envmap | Bool | plain | CVAR_GLOBALCONFIG\|CVAR_ARCHIVE | yes | yes | C |  |
| gl_mirrors | Bool | plain | 0 | yes | yes | C |  |
| gl_no_skyclear | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| gl_nocoloredspritelighting | Bool | custom | 0 | yes | — | C |  |
| gl_nolayer | Bool | plain | 0 | yes | — | C |  |
| gl_noquery | Bool | plain | 0 | yes | — | C |  |
| gl_noskyboxes | Bool | plain | 0 | yes | yes | C |  |
| gl_notexturefill | Bool | custom | 0 | yes | yes | C |  |
| gl_particles_style | Int | plain | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | yes | C |  |
| gl_plane_reflection | Bool | custom | CVAR_GLOBALCONFIG\|CVAR_ARCHIVE | yes | yes | C |  |
| gl_portals | Bool | plain | 0 | yes | yes | C |  |
| gl_precache | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| gl_quadbufferedstereo | Bool | plain | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | — | C |  |
| gl_render_flats | Bool | plain | CVAR_DEBUGONLY | yes | yes | C |  |
| gl_render_precise | Bool | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| gl_render_segs | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| gl_render_things | Bool | plain | CVAR_DEBUGONLY | yes | yes | C |  |
| gl_render_walls | Bool | plain | CVAR_DEBUGONLY | yes | yes | C |  |
| gl_sclipfactor | Float | plain | CVAR_ARCHIVE | yes | yes | C |  |
| gl_sclipthreshold | Float | plain | CVAR_ARCHIVE | yes | yes | C |  |
| gl_seamless | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| gl_sky_detail | Int | plain | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | — | C |  |
| gl_sort_textures | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| gl_sprite_blend | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| gl_spritebrightfog | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| gl_spriteclip | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| gl_texture | Bool | plain | 0 | yes | yes | C |  |
| gl_texture_filter | Int | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG\|CVAR_NOINITCALL | yes | yes | C |  |
| gl_texture_filter_anisotropic | Float | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG\|CVAR_NOINITCALL | yes | yes | C |  |
| gl_texture_format | Int | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG\|CVAR_NOINITCALL | yes | — | C |  |
| gl_texture_hqresize | Int | custom | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG \| CVAR_NOINITCALL | yes | — | C |  |
| gl_texture_hqresize_fonts | Flag | plain | 4 | yes | yes | C |  |
| gl_texture_hqresize_maxinputsize | Int | custom | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG \| CVAR_NOINITCALL | yes | yes | C |  |
| gl_texture_hqresize_sprites | Flag | plain | 2 | yes | yes | C |  |
| gl_texture_hqresize_targets | Int | custom | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG \| CVAR_NOINITCALL | yes | yes | C |  |
| gl_texture_hqresize_textures | Flag | plain | 1 | yes | yes | C |  |
| gl_texture_usehires | Bool | custom | CVAR_ARCHIVE\|CVAR_NOINITCALL | yes | — | C |  |
| gl_texture_useshaders | Bool | plain | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | — | C |  |
| gl_trimsprites | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| gl_use_models | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| gl_usecolorblending | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| gl_usefb | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| gl_usevbo | Int | custom | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG \| CVAR_NOINITCALL | yes | — | C |  |
| gl_vid_multisample | Int | custom | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG \| CVAR_NOINITCALL | yes | — | C |  |
| gl_warp_shader | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG\|CVAR_NOINITCALL | yes | — | C |  |
| gl_weaponlight | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| gltest_slopeopt | Bool | plain | 0 | yes | — | C |  |
| gtang | Float | plain | 0 | yes | — | C |  |
| gus_memsize | Int | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| gus_patchdir | String | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| handicap | Int | plain | CVAR_USERINFO \| CVAR_ARCHIVE | yes | — | A | [notes](../notes/handicap.md) |
| hud_althud | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| hud_althudscale | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| hud_ammo_red | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| hud_ammo_yellow | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| hud_armor_green | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| hud_armor_red | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| hud_armor_yellow | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| hud_berserk_health | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| hud_health_green | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| hud_health_red | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| hud_health_yellow | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| hud_scale | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| hud_showdmstats | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| hud_showitems | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| hud_showmonsters | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| hud_showscore | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| hud_showsecrets | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| hud_showstats | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| hud_showtime | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| hud_timecolor | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| hudcolor_ltim | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| hudcolor_statnames | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| hudcolor_stats | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| hudcolor_time | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| hudcolor_titl | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| hudcolor_ttim | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| hudcolor_xyco | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| idmypos | Bool | plain | 0 | yes | yes | C |  |
| in_mouse | Int | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG\|CVAR_NOINITCALL | yes | yes | C |  |
| infighting | Int | plain | CVAR_SERVERINFO | yes | yes | C |  |
| instagib | Bool | plain | CVAR_SERVERINFO \| CVAR_LATCH \| CVAR_CAMPAIGNLOCK \| CVAR_GAMEPLAYSETTING | yes | — | A | [notes](../notes/instagib.md) |
| invasion | Bool | custom | CVAR_SERVERINFO \| CVAR_LATCH \| CVAR_CAMPAIGNLOCK | yes | — | C |  |
| invertmouse | Bool | plain | CVAR_GLOBALCONFIG\|CVAR_ARCHIVE | yes | yes | C |  |
| joinmenukey | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| joy_dinput | Bool | custom | CVAR_GLOBALCONFIG\|CVAR_ARCHIVE\|CVAR_NOINITCALL | yes | yes | C |  |
| joy_ps2raw | Bool | custom | CVAR_GLOBALCONFIG\|CVAR_ARCHIVE\|CVAR_NOINITCALL | yes | yes | C |  |
| joy_xinput | Bool | custom | CVAR_GLOBALCONFIG\|CVAR_ARCHIVE\|CVAR_NOINITCALL | yes | yes | C |  |
| k_allowfullscreentoggle | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| k_mergekeys | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| language | String | custom | CVAR_ARCHIVE | yes | yes | C |  |
| lastmanstanding | Bool | custom | CVAR_SERVERINFO \| CVAR_LATCH \| CVAR_CAMPAIGNLOCK | yes | — | C |  |
| lms_allowchaingun | Flag | plain | LMS_AWF_CHAINGUN | yes | — | C |  |
| lms_allowchainsaw | Flag | plain | LMS_AWF_CHAINSAW | yes | — | C |  |
| lms_allowgrenadelauncher | Flag | plain | LMS_AWF_GRENADELAUNCHER | yes | — | C |  |
| lms_allowminigun | Flag | plain | LMS_AWF_MINIGUN | yes | — | C |  |
| lms_allowpistol | Flag | plain | LMS_AWF_PISTOL | yes | — | C |  |
| lms_allowplasma | Flag | plain | LMS_AWF_PLASMA | yes | — | C |  |
| lms_allowrailgun | Flag | plain | LMS_AWF_RAILGUN | yes | — | C |  |
| lms_allowrocketlauncher | Flag | plain | LMS_AWF_ROCKETLAUNCHER | yes | — | C |  |
| lms_allowshotgun | Flag | plain | LMS_AWF_SHOTGUN | yes | — | C |  |
| lms_allowssg | Flag | plain | LMS_AWF_SSG | yes | — | C |  |
| lms_spectatorchat | Flag | plain | LMS_SPF_CHAT | yes | — | C |  |
| lms_spectatorview | Flag | plain | LMS_SPF_VIEW | yes | — | C |  |
| lms_spectatorvoicechat | Flag | plain | LMS_SPF_VOICECHAT | yes | — | C |  |
| lmsallowedweapons | Int | custom | CVAR_SERVERINFO \| CVAR_GAMEPLAYFLAGSET | yes | — | C |  |
| lmsspectatorsettings | Int | custom | CVAR_SERVERINFO \| CVAR_GAMEPLAYFLAGSET | yes | — | C |  |
| lobby | String | custom | CVAR_SERVERINFO | yes | — | C |  |
| login_default_user | String | custom | CVAR_ARCHIVE \| CVAR_NOINITCALL | yes | — | C |  |
| longsavemessages | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| lookspring | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| lookstrafe | Bool | plain | CVAR_GLOBALCONFIG\|CVAR_ARCHIVE | yes | yes | C |  |
| m_filter | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| m_forward | Float | plain | CVAR_GLOBALCONFIG\|CVAR_ARCHIVE | yes | yes | C |  |
| m_hidepointer | Bool | plain | 0 | yes | yes | C |  |
| m_noprescale | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| m_pitch | Float | plain | CVAR_GLOBALCONFIG\|CVAR_ARCHIVE | yes | yes | C |  |
| m_show_backbutton | Int | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| m_showinputgrid | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| m_side | Float | plain | CVAR_GLOBALCONFIG\|CVAR_ARCHIVE | yes | yes | C |  |
| m_use_mouse | Int | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| m_yaw | Float | plain | CVAR_GLOBALCONFIG\|CVAR_ARCHIVE | yes | yes | C |  |
| map_point_coordinates | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| masterhostname | String | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG\|CVAR_NOSETBYACS | yes | — | C |  |
| maxviewpitch | Float | custom | CVAR_ARCHIVE\|CVAR_SERVERINFO | yes | yes | C |  |
| menu_authpassword | String | plain | 0 | yes | — | C |  |
| menu_authusername | String | plain | 0 | yes | — | C |  |
| menu_botspawn0 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_botspawn1 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_botspawn10 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_botspawn11 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_botspawn12 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_botspawn13 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_botspawn14 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_botspawn15 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_botspawn2 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_botspawn3 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_botspawn4 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_botspawn5 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_botspawn6 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_botspawn7 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_botspawn8 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_botspawn9 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_browser_filtername | String | custom | CVAR_ARCHIVE | yes | — | C |  |
| menu_browser_gametype | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| menu_browser_servers | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| menu_browser_showempty | Bool | custom | CVAR_ARCHIVE | yes | — | C |  |
| menu_browser_showfull | Bool | custom | CVAR_ARCHIVE | yes | — | C |  |
| menu_browser_sortby | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| menu_callvoteban | Bool | plain | 0 | yes | — | C |  |
| menu_callvoteflag | String | plain | 0 | yes | — | C |  |
| menu_callvoteintermission | Bool | plain | 0 | yes | — | C |  |
| menu_callvotelimit | Int | plain | 0 | yes | — | C |  |
| menu_callvotemap | Int | plain | 0 | yes | — | C |  |
| menu_callvotenextsecret | Bool | plain | 0 | yes | — | C |  |
| menu_callvoteplayer | Int | plain | 0 | yes | — | C |  |
| menu_callvotereason | String | plain | 0 | yes | — | C |  |
| menu_callvotevalue | Float | plain | 0 | yes | — | C |  |
| menu_ignoreaction | Bool | plain | 0 | yes | — | C |  |
| menu_ignoreduration | Int | plain | 0 | yes | — | C |  |
| menu_ignoretype | Bool | plain | 0 | yes | — | C |  |
| menu_joinclassidx | Int | plain | 0 | yes | — | C |  |
| menu_jointeamidx | Int | plain | 0 | yes | — | C |  |
| menu_playerindex | Int | plain | 0 | yes | — | C |  |
| menu_rconpassword | String | plain | 0 | yes | — | C |  |
| menu_screenratios | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| menu_skirmishbotskill | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_skirmishduellimit | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_skirmishfraglimit | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_skirmishgamemode | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_skirmishlevel | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_skirmishmodifier | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_skirmishpointlimit | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_skirmishskill | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_skirmishtimelimit | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_skirmishwavelimit | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_skirmishwinlimit | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_teambotspawn0 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_teambotspawn1 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_teambotspawn10 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_teambotspawn11 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_teambotspawn12 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_teambotspawn13 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_teambotspawn14 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_teambotspawn15 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_teambotspawn16 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_teambotspawn17 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_teambotspawn18 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_teambotspawn19 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_teambotspawn2 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_teambotspawn3 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_teambotspawn4 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_teambotspawn5 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_teambotspawn6 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_teambotspawn7 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_teambotspawn8 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_teambotspawn9 | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| menu_textsizescalar | Int | custom | CVAR_NOINITCALL | yes | — | C |  |
| menu_voicevolume | Float | plain | 0 | yes | — | C |  |
| midi_config | String | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| midi_dmxgus | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| midi_timiditylike | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| midi_voices | Int | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| mod_autochip | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| mod_autochip_scan_threshold | Int | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| mod_autochip_size_force | Int | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| mod_autochip_size_scan | Int | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| mod_dumb | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| mod_interp | Int | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| mod_samplerate | Int | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| mod_volramp | Int | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| mouse_capturemode | Int | custom | CVAR_GLOBALCONFIG\|CVAR_ARCHIVE | yes | yes | C |  |
| mouse_sensitivity | Float | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| movebob | Float | plain | CVAR_USERINFO \| CVAR_UNSYNCED_USERINFO \| CVAR_ARCHIVE | yes | yes | C |  |
| msg | Int | plain | CVAR_ARCHIVE | yes | yes | A | [notes](../notes/msg.md) |
| msg0color | Int | custom | CVAR_ARCHIVE | yes | yes | C |  |
| msg1color | Int | custom | CVAR_ARCHIVE | yes | yes | C |  |
| msg2color | Int | custom | CVAR_ARCHIVE | yes | yes | C |  |
| msg3color | Int | custom | CVAR_ARCHIVE | yes | yes | C |  |
| msg4color | Int | custom | CVAR_ARCHIVE | yes | yes | C |  |
| msg5color | Int | custom | CVAR_ARCHIVE | yes | — | A | [notes](../notes/msg5color.md) |
| msgmidcolor | Int | custom | CVAR_ARCHIVE | yes | yes | C |  |
| msgmidcolor2 | Int | custom | CVAR_ARCHIVE | yes | yes | C |  |
| name | String | plain | CVAR_USERINFO \| CVAR_ARCHIVE | yes | yes | C |  |
| nametagcolor | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| net_zstd_level | Int | custom | CVAR_ARCHIVE\|CVAR_NOSETBYACS | yes | — | C |  |
| net_zstd_smart | Bool | plain | CVAR_ARCHIVE\|CVAR_NOSETBYACS | yes | — | C |  |
| net_zstd_threshold | Int | plain | CVAR_ARCHIVE\|CVAR_NOSETBYACS | yes | — | C |  |
| nofilecompression | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| noise | Bool | plain | 0 | yes | — | C |  |
| nomonsterinterpolation | Bool | plain | CVAR_GLOBALCONFIG\|CVAR_ARCHIVE | yes | yes | C |  |
| norawinput | Bool | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG\|CVAR_NOINITCALL | yes | — | C |  |
| oneflagctf | Bool | custom | CVAR_SERVERINFO \| CVAR_LATCH \| CVAR_CAMPAIGNLOCK | yes | — | C |  |
| opl_core | Int | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| opl_fullpan | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| opl_numchips | Int | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | A | [notes](../notes/opl_numchips.md) |
| opl_singlevoice | Bool | plain | 0 | yes | — | C |  |
| paletteflash | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| pf_hazard | Flag | plain | PF_HAZARD | yes | yes | C |  |
| pf_hexenweaps | Flag | plain | PF_HEXENWEAPONS | yes | yes | C |  |
| pf_ice | Flag | plain | PF_ICE | yes | yes | C |  |
| pf_poison | Flag | plain | PF_POISON | yes | yes | C |  |
| playerclass | String | plain | CVAR_USERINFO \| CVAR_ARCHIVE | yes | yes | C |  |
| png_gamma | Float | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| png_level | Int | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| pointlimit | Int | custom | CVAR_SERVERINFO \| CVAR_CAMPAIGNLOCK \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| possession | Bool | custom | CVAR_SERVERINFO \| CVAR_LATCH \| CVAR_CAMPAIGNLOCK | yes | — | C |  |
| preferoptionalwads | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| privatechat_sound | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| pwo_switchonsameweight | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| pwo_switchonunknown | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| queryiwad | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| queryiwad_key | String | plain | CVAR_GLOBALCONFIG\|CVAR_ARCHIVE | yes | yes | C |  |
| r_3dfloors | Int | plain | 0 | yes | yes | C |  |
| r_clearbuffer | Int | plain | 0 | yes | yes | C |  |
| r_columnmethod | Int | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| r_deathcamera | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| r_drawflat | Bool | plain | 0 | yes | — | C |  |
| r_drawfuzz | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| r_drawmirrors | Bool | plain | 0 | yes | yes | C |  |
| r_drawplayersprites | Bool | plain | 0 | yes | yes | C |  |
| r_drawrespawnstring | Bool | plain | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | — | C |  |
| r_drawspectatingstring | Bool | plain | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | — | C |  |
| r_drawtrans | Bool | custom | CVAR_ARCHIVE | yes | yes | C |  |
| r_drawvoxels | Bool | plain | 0 | yes | yes | C |  |
| r_fakecontrast | Int | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| r_fogboundary | Bool | plain | 0 | yes | yes | C |  |
| r_maxparticles | Int | custom | CVAR_ARCHIVE | yes | yes | C |  |
| r_mirror_recursions | Int | custom | CVAR_GLOBALCONFIG\|CVAR_ARCHIVE | yes | — | C |  |
| r_nopolytilt | Bool | plain | 0 | yes | — | C |  |
| r_np2 | Bool | plain | 0 | yes | — | C |  |
| r_particles | Bool | plain | 0 | yes | yes | C |  |
| r_polymost | Int | plain | 0 | yes | — | C |  |
| r_quakeintensity | Float | custom | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | yes | C |  |
| r_rail_smartspiral | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| r_rail_spiralsparsity | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| r_rail_trailsparsity | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| r_shadercolormaps | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| r_skyboxes | Bool | plain | 0 | yes | yes | C |  |
| r_splitsprites | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| r_stretchsky | Bool | custom | CVAR_ARCHIVE | yes | — | C |  |
| r_viewsize | String | plain | CVAR_NOSET | yes | yes | C |  |
| railcolor | Int | plain | CVAR_USERINFO \| CVAR_ARCHIVE | yes | — | C |  |
| rgamma | Float | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| save_dir | String | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| savestatistics | Int | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| sb_backgroundalpha | Float | custom | CVAR_ARCHIVE \| CVAR_NOSETBYACS | yes | — | C |  |
| sb_backgroundcolor | Color | plain | CVAR_ARCHIVE \| CVAR_NOSETBYACS | yes | — | C |  |
| sb_customizebackground | Flag | plain | CUSTOMIZE_BACKGROUND | yes | — | C |  |
| sb_customizeborders | Flag | plain | CUSTOMIZE_BORDERS | yes | — | C |  |
| sb_customizeflags | Int | custom | CVAR_ARCHIVE \| CVAR_NOINITCALL \| CVAR_NOSETBYACS | yes | — | C |  |
| sb_customizerowbackgrounds | Flag | plain | CUSTOMIZE_ROWBACKGROUNDS | yes | — | C |  |
| sb_customizetext | Flag | plain | CUSTOMIZE_TEXT | yes | — | C |  |
| sb_darkbordercolor | Color | plain | CVAR_ARCHIVE \| CVAR_NOSETBYACS | yes | — | C |  |
| sb_darkrowbackgroundcolor | Color | custom | CVAR_ARCHIVE \| CVAR_NOINITCALL \| CVAR_NOSETBYACS | yes | — | C |  |
| sb_deadrowbackgroundalpha | Float | custom | CVAR_ARCHIVE \| CVAR_NOSETBYACS | yes | — | C |  |
| sb_headerfont | String | plain | CVAR_ARCHIVE \| CVAR_NOSETBYACS | yes | — | C |  |
| sb_headertextcolor | Int | custom | CVAR_ARCHIVE \| CVAR_NOSETBYACS | yes | — | C |  |
| sb_lightbordercolor | Color | plain | CVAR_ARCHIVE \| CVAR_NOSETBYACS | yes | — | C |  |
| sb_lightrowbackgroundcolor | Color | custom | CVAR_ARCHIVE \| CVAR_NOINITCALL \| CVAR_NOSETBYACS | yes | — | C |  |
| sb_localrowbackgroundcolor | Color | custom | CVAR_ARCHIVE \| CVAR_NOINITCALL \| CVAR_NOSETBYACS | yes | — | C |  |
| sb_localrowdemotextcolor | Int | custom | CVAR_ARCHIVE \| CVAR_NOSETBYACS | yes | — | C |  |
| sb_localrowtextcolor | Int | custom | CVAR_ARCHIVE \| CVAR_NOSETBYACS | yes | — | C |  |
| sb_marginfont | String | plain | CVAR_ARCHIVE \| CVAR_NOSETBYACS | yes | — | C |  |
| sb_noborders | Bool | plain | CVAR_ARCHIVE \| CVAR_NOSETBYACS | yes | — | C |  |
| sb_nolocalrowbackgroundcolor | Bool | plain | CVAR_ARCHIVE \| CVAR_NOSETBYACS | yes | — | C |  |
| sb_onlylocalrowbackground | Bool | plain | CVAR_ARCHIVE \| CVAR_NOSETBYACS | yes | — | C |  |
| sb_rowbackgroundalpha | Float | custom | CVAR_ARCHIVE \| CVAR_NOSETBYACS | yes | — | C |  |
| sb_rowfont | String | plain | CVAR_ARCHIVE \| CVAR_NOSETBYACS | yes | — | C |  |
| sb_rowtextcolor | Int | custom | CVAR_ARCHIVE \| CVAR_NOSETBYACS | yes | — | C |  |
| sb_showgapsinrowbackground | Bool | plain | CVAR_ARCHIVE \| CVAR_NOSETBYACS | yes | — | C |  |
| sb_useheadertextcolorforborders | Bool | plain | CVAR_ARCHIVE \| CVAR_NOSETBYACS | yes | — | C |  |
| sb_useteamtextcolors | Bool | plain | CVAR_ARCHIVE \| CVAR_NOSETBYACS | yes | — | C |  |
| screenblocks | Int | custom | CVAR_ARCHIVE | yes | yes | A | [notes](../notes/screenblocks.md) |
| screenshot_dir | String | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| screenshot_quiet | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| screenshot_type | String | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| sdl_nokeyrepeat | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| secretmessage | String | plain | CVAR_ARCHIVE | yes | — | C |  |
| show_messages | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| show_obituaries | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| showendoom | Int | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| showloadtimes | Bool | plain | 0 | yes | — | C |  |
| skill | Int | plain | CVAR_SERVERINFO\|CVAR_LATCH | yes | yes | C |  |
| skin | String | plain | CVAR_USERINFO \| CVAR_ARCHIVE | yes | yes | C |  |
| skulltag | Bool | custom | CVAR_SERVERINFO \| CVAR_LATCH \| CVAR_CAMPAIGNLOCK | yes | — | C |  |
| skyoffset | Float | plain | 0 | yes | yes | C |  |
| smooth_mouse | Bool | plain | CVAR_GLOBALCONFIG\|CVAR_ARCHIVE | yes | — | C |  |
| snd_announcervolume | Float | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| snd_buffercount | Int | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| snd_buffersize | Int | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| snd_channels | Int | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| snd_drawoutput | Int | plain | 0 | yes | yes | C |  |
| snd_driver | Int | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| snd_flipstereo | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| snd_hrtf | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| snd_lockmusic | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| snd_menuvolume | Float | plain | CVAR_ARCHIVE | yes | yes | C |  |
| snd_mididevice | Int | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | A | [notes](../notes/snd_mididevice.md) |
| snd_midipatchset | String | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| snd_midiprecache | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| snd_movievolume | Float | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| snd_musicvolume | Float | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | A | [notes](../notes/snd_musicvolume.md) |
| snd_output | String | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| snd_output_format | String | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| snd_pitched | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| snd_profile | Bool | plain | 0 | yes | — | C |  |
| snd_resampler | String | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| snd_samplerate | Int | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| snd_sfxvolume | Float | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG\|CVAR_NOINITCALL | yes | yes | A | [notes](../notes/snd_sfxvolume.md) |
| snd_speakermode | String | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| snd_waterlp | Float | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| snd_waterreverb | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| spc_amp | Float | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| splashfactor | Float | custom | CVAR_SERVERINFO | yes | yes | C |  |
| st_oldouch | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| st_scale | Bool | custom | CVAR_ARCHIVE | yes | yes | C |  |
| statfile | String | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| stillbob | Float | plain | CVAR_USERINFO \| CVAR_UNSYNCED_USERINFO \| CVAR_ARCHIVE | yes | yes | C |  |
| storesavepic | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| survival | Bool | custom | CVAR_SERVERINFO \| CVAR_LATCH \| CVAR_CAMPAIGNLOCK | yes | — | C |  |
| sv_adminlistfile | String | custom | CVAR_ARCHIVE\|CVAR_SENSITIVESERVERSETTING\|CVAR_NOSETBYACS | yes | — | C |  |
| sv_afk2spec | Int | plain | CVAR_ARCHIVE \| CVAR_SERVERINFO | yes | — | C |  |
| sv_aircontrol | Float | custom | CVAR_SERVERINFO\|CVAR_NOSAVE\|CVAR_GAMEPLAYSETTING | yes | yes | A | [notes](../notes/sv_aircontrol.md) |
| sv_allowcrouch | Flag | plain | DF_YES_CROUCH | yes | yes | C |  |
| sv_allowjump | Flag | plain | DF_YES_JUMP | yes | yes | C |  |
| sv_allowprivatechat | Int | custom | CVAR_ARCHIVE \| CVAR_NOSETBYACS \| CVAR_SERVERINFO | yes | — | A | [notes](../notes/sv_allowprivatechat.md) |
| sv_allowvoicechat | Int | custom | CVAR_NOSETBYACS \| CVAR_SERVERINFO | yes | — | A | [notes](../notes/sv_allowvoicechat.md) |
| sv_applylmsspectatorsettings | Flag | plain | ZADF_ALWAYS_APPLY_LMS_SPECTATORSETTINGS | yes | — | C |  |
| sv_artifactreturntime | Int | plain | CVAR_SERVERINFO \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| sv_awarddamageinsteadkills | Flag | plain | ZADF_AWARD_DAMAGE_INSTEAD_KILLS | yes | — | C |  |
| sv_banexemptionfile | String | custom | CVAR_ARCHIVE\|CVAR_NOSETBYACS\|CVAR_SENSITIVESERVERSETTING | yes | — | C |  |
| sv_banfile | String | custom | CVAR_ARCHIVE\|CVAR_NOSETBYACS\|CVAR_SENSITIVESERVERSETTING | yes | — | C |  |
| sv_banfilereparsetime | Int | plain | CVAR_ARCHIVE\|CVAR_NOSETBYACS | yes | — | C |  |
| sv_barrelrespawn | Flag | plain | DF2_BARRELS_RESPAWN | yes | yes | C |  |
| sv_bfgfreeaim | Flag | plain | DF2_YES_FREEAIMBFG | yes | — | C |  |
| sv_broadcast | Bool | custom | CVAR_ARCHIVE\|CVAR_NOSETBYACS | yes | — | C |  |
| sv_chasecam | Flag | plain | DF2_CHASECAM | yes | yes | C |  |
| sv_cheats | Bool | plain | CVAR_SERVERINFO \| CVAR_LATCH \| CVAR_NOSETBYACS | yes | yes | C |  |
| sv_colorstripmethod | Int | plain | CVAR_ARCHIVE | yes | — | A | [notes](../notes/sv_colorstripmethod.md) |
| sv_coop_damagefactor | Float | custom | CVAR_SERVERINFO \| CVAR_GAMEPLAYSETTING | yes | — | A | [notes](../notes/sv_coop_damagefactor.md) |
| sv_coop_halveammo | Flag | plain | DF_COOP_HALVE_AMMO | yes | — | C |  |
| sv_coop_loseammo | Flag | plain | DF_COOP_LOSE_AMMO | yes | — | C |  |
| sv_coop_losearmor | Flag | plain | DF_COOP_LOSE_ARMOR | yes | — | C |  |
| sv_coop_loseinventory | Flag | plain | DF_COOP_LOSE_INVENTORY | yes | — | C |  |
| sv_coop_losekeys | Flag | plain | DF_COOP_LOSE_KEYS | yes | — | C |  |
| sv_coop_losepowerups | Flag | plain | DF_COOP_LOSE_POWERUPS | yes | — | C |  |
| sv_coop_loseweapons | Flag | plain | DF_COOP_LOSE_WEAPONS | yes | — | C |  |
| sv_coop_spactorspawn | Flag | plain | ZADF_COOP_SP_ACTOR_SPAWN | yes | — | C |  |
| sv_coopspawnvoodoodolls | Bool | plain | CVAR_SERVERINFO \| CVAR_LATCH | yes | — | C |  |
| sv_coopunassignedvoodoodolls | Bool | plain | CVAR_SERVERINFO \| CVAR_LATCH | yes | — | C |  |
| sv_coopunassignedvoodoodollsfornplayers | Int | plain | CVAR_SERVERINFO \| CVAR_LATCH | yes | — | C |  |
| sv_corpsequeuesize | Int | custom | CVAR_ARCHIVE\|CVAR_SERVERINFO | yes | yes | C |  |
| sv_country | String | plain | CVAR_ARCHIVE\|CVAR_NOSETBYACS\|CVAR_SERVERINFO | yes | — | C |  |
| sv_crouch | Mask | plain | DF_NO_CROUCH\|DF_YES_CROUCH | yes | yes | C |  |
| sv_deadplayerscankeepinventory | Flag | plain | ZADF_DEAD_PLAYERS_CAN_KEEP_INVENTORY | yes | — | C |  |
| sv_defaultdmflags | Bool | plain | 0 | yes | — | A | [notes](../notes/sv_defaultdmflags.md) |
| sv_degeneration | Flag | plain | DF2_YES_DEGENERATION | yes | yes | C |  |
| sv_disableautohealth | Bool | plain | CVAR_ARCHIVE\|CVAR_SERVERINFO | yes | yes | C |  |
| sv_disallowspying | Flag | plain | DF2_DISALLOW_SPYING | yes | yes | C |  |
| sv_disallowsuicide | Flag | plain | DF2_NOSUICIDE | yes | yes | C |  |
| sv_distinguishteamchatlines | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| sv_dominationscorerate | Int | custom | CVAR_SERVERINFO \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| sv_dontcheckammo | Flag | plain | DF2_DONTCHECKAMMO | yes | yes | C |  |
| sv_donthidestats | Flag | plain | ZADF_DONT_HIDE_STATS | yes | — | C |  |
| sv_dontkeepjoinqueue | Flag | plain | ZADF_DONT_KEEP_JOIN_QUEUE | yes | — | C |  |
| sv_dontoverrideplayercolors | Flag | plain | ZADF_DONT_OVERRIDE_PLAYER_COLORS | yes | — | C |  |
| sv_dontpushallies | Flag | plain | ZADF_DONT_PUSH_ALLIES | yes | — | C |  |
| sv_doubleammo | Flag | plain | DF2_YES_DOUBLEAMMO | yes | yes | C |  |
| sv_dropstyle | Int | plain | CVAR_SERVERINFO \| CVAR_ARCHIVE | yes | yes | A | [notes](../notes/sv_dropstyle.md) |
| sv_duelcountdowntime | Int | plain | CVAR_ARCHIVE \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| sv_dumppackets | Bool | plain | CVAR_NOSETBYACS | yes | — | C |  |
| sv_dumppackets_chance | Float | plain | CVAR_NOSETBYACS | yes | — | C |  |
| sv_dumppackets_dir | String | plain | CVAR_NOSETBYACS | yes | — | C |  |
| sv_emulatepacketloss | Bool | plain | 0 | yes | — | C |  |
| sv_enforcebans | Bool | plain | CVAR_ARCHIVE\|CVAR_NOSETBYACS | yes | — | C |  |
| sv_enforcemasterbanlist | Bool | custom | CVAR_ARCHIVE\|CVAR_NOSETBYACS\|CVAR_SERVERINFO | yes | — | C |  |
| sv_falldamage | Flag | plain | DF_FORCE_FALLINGHX | yes | yes | C |  |
| sv_fallingdamage | Mask | plain | DF_FORCE_FALLINGHX\|DF_FORCE_FALLINGZD | yes | yes | C |  |
| sv_fastmonsters | Flag | plain | DF_FAST_MONSTERS | yes | yes | C |  |
| sv_fastweapons | Int | custom | CVAR_SERVERINFO \| CVAR_GAMEPLAYSETTING | yes | yes | A | [notes](../notes/sv_fastweapons.md) |
| sv_flagreturntime | Int | plain | CVAR_CAMPAIGNLOCK \| CVAR_SERVERINFO \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| sv_forbidvoteflags | Int | custom | CVAR_ARCHIVE \| CVAR_SERVERINFO | yes | — | A | [notes](../notes/sv_forbidvoteflags.md) |
| sv_forcealpha | Flag | plain | ZADF_FORCE_ALPHA | yes | — | C |  |
| sv_forcegldefaults | Flag | plain | ZADF_FORCE_VIDEO_DEFAULTS | yes | — | C |  |
| sv_forcejoinpassword | Bool | plain | CVAR_ARCHIVE\|CVAR_NOSETBYACS\|CVAR_SERVERINFO | yes | — | C |  |
| sv_forcelogintojoin | Bool | plain | CVAR_ARCHIVE\|CVAR_NOSETBYACS | yes | — | A | [notes](../notes/sv_forcelogintojoin.md) |
| sv_forcepassword | Bool | plain | CVAR_ARCHIVE\|CVAR_NOSETBYACS\|CVAR_SERVERINFO | yes | — | C |  |
| sv_forcerandomclass | Bool | plain | 0 | yes | — | C |  |
| sv_forcerespawn | Flag | plain | DF_FORCE_RESPAWN | yes | yes | C |  |
| sv_forcerespawntime | Int | plain | CVAR_ARCHIVE\|CVAR_SERVERINFO\|CVAR_GAMEPLAYSETTING | yes | — | A | [notes](../notes/sv_forcerespawntime.md) |
| sv_forcesoftwarepitchlimits | Flag | plain | ZADF_FORCE_SOFTWARE_PITCH_LIMITS | yes | — | C |  |
| sv_forcevideodefaults | Flag | plain | ZADF_FORCE_VIDEO_DEFAULTS | yes | — | C |  |
| sv_gravity | Float | custom | CVAR_SERVERINFO\|CVAR_NOSAVE\|CVAR_GAMEPLAYSETTING | yes | yes | C |  |
| sv_hackerlistfile | String | custom | CVAR_ARCHIVE\|CVAR_NOSETBYACS | yes | — | C |  |
| sv_hostemail | String | plain | CVAR_ARCHIVE\|CVAR_NOSETBYACS\|CVAR_SERVERINFO | yes | — | C |  |
| sv_hostname | String | custom | CVAR_ARCHIVE\|CVAR_NOSETBYACS\|CVAR_SERVERINFO | yes | — | C |  |
| sv_infiniteammo | Flag | plain | DF_INFINITE_AMMO | yes | yes | C |  |
| sv_infiniteinventory | Flag | plain | DF2_INFINITE_INVENTORY | yes | yes | C |  |
| sv_instantreturn | Flag | plain | DF2_INSTANT_RETURN | yes | — | C |  |
| sv_invasioncountdowntime | Int | plain | CVAR_ARCHIVE \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| sv_itemrespawn | Flag | plain | DF_ITEMS_RESPAWN | yes | yes | C |  |
| sv_joinpassword | String | custom | CVAR_ARCHIVE\|CVAR_NOSETBYACS\|CVAR_SENSITIVESERVERSETTING | yes | — | C |  |
| sv_jump | Mask | plain | DF_NO_JUMP\|DF_YES_JUMP | yes | yes | C |  |
| sv_keepfrags | Flag | plain | DF2_YES_KEEPFRAGS | yes | yes | C |  |
| sv_keepteams | Flag | plain | ZADF_YES_KEEP_TEAMS | yes | — | C |  |
| sv_killallmonsters | Flag | plain | DF2_KILL_MONSTERS | yes | yes | C |  |
| sv_killallmonsters_percentage | Int | custom | CVAR_SERVERINFO | yes | — | C |  |
| sv_killbossmonst | Flag | plain | DF2_KILLBOSSMONST | yes | yes | C |  |
| sv_limitcommands | Bool | custom | CVAR_ARCHIVE \| CVAR_NOSETBYACS \| CVAR_SERVERINFO \| CVAR_DEBUGONLY | yes | — | A | [notes](../notes/sv_limitcommands.md) |
| sv_lmscountdowntime | Int | plain | CVAR_ARCHIVE \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| sv_logfile_append | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| sv_logfilenametimestamp | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| sv_logfiletimestamp | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| sv_logfiletimestamp_usedate | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| sv_losefrag | Flag | plain | DF2_YES_LOSEFRAG | yes | yes | C |  |
| sv_maprotation | Bool | plain | CVAR_ARCHIVE \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| sv_markchatlines | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| sv_maxacsbanduration | Int | custom | CVAR_SERVERINFO \| CVAR_NOSETBYACS | yes | — | A | [notes](../notes/sv_maxacsbanduration.md) |
| sv_maxbloodscalar | Flag | plain | ZADF_MAX_BLOOD_SCALAR | yes | — | C |  |
| sv_maxclients | Int | custom | 32 | yes | — | A | [notes](../notes/sv_maxclients.md) |
| sv_maxclientsperip | Int | plain | CVAR_ARCHIVE \| CVAR_SERVERINFO | yes | — | C |  |
| sv_maxfov | Float | custom | CVAR_ARCHIVE \| CVAR_SERVERINFO \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| sv_maxlives | Int | custom | CVAR_SERVERINFO \| CVAR_LATCH \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| sv_maxpacketsize | Int | custom | CVAR_ARCHIVE \| CVAR_SERVERINFO | yes | — | A | [notes](../notes/sv_maxpacketsize.md) |
| sv_maxpacketspertick | Int | custom | CVAR_ARCHIVE | yes | — | A | [notes](notes/sv_maxpacketsize.md) |
| sv_maxplayers | Int | custom | 32 | yes | — | A | [notes](notes/sv_maxclients.md) |
| sv_maxproximityrolloffdist | Float | custom | CVAR_NOSETBYACS \| CVAR_SERVERINFO | yes | — | C |  |
| sv_maxteams | Int | custom | CVAR_SERVERINFO \| CVAR_CAMPAIGNLOCK \| CVAR_LATCH \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| sv_measureoutboundtraffic | Bool | plain | 0 | yes | — | C |  |
| sv_minfov | Float | custom | CVAR_ARCHIVE \| CVAR_SERVERINFO \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| sv_minimizetosystray | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| sv_minproximityrolloffdist | Float | custom | CVAR_NOSETBYACS \| CVAR_SERVERINFO | yes | — | C |  |
| sv_minvoters | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| sv_monsterrespawn | Flag | plain | DF_MONSTERS_RESPAWN | yes | yes | C |  |
| sv_motd | String | plain | CVAR_ARCHIVE | yes | — | C |  |
| sv_noallyicons | Flag | plain | ZADF_NO_ALLY_ICONS | yes | — | C |  |
| sv_noarmor | Flag | plain | DF_NO_ARMOR | yes | yes | C |  |
| sv_noautoaim | Flag | plain | DF2_NOAUTOAIM | yes | yes | C |  |
| sv_noautomap | Flag | plain | DF2_NO_AUTOMAP | yes | yes | C |  |
| sv_noautomapallies | Flag | plain | DF2_NO_AUTOMAP_ALLIES | yes | yes | C |  |
| sv_nocallvote | Int | custom | CVAR_ARCHIVE \| CVAR_SERVERINFO | yes | — | A | [notes](../notes/sv_nocallvote.md) |
| sv_nochangemapvote | Flag | plain | FORBIDVOTE_CHANGEMAP | yes | — | C |  |
| sv_nocoopinfo | Flag | plain | ZADF_NO_COOP_INFO | yes | — | C |  |
| sv_nocountendmonst | Flag | plain | DF2_NOCOUNTENDMONST | yes | yes | C |  |
| sv_nocrouch | Flag | plain | DF_NO_CROUCH | yes | yes | C |  |
| sv_nodoorclose | Flag | plain | ZADF_NODOORCLOSE | yes | — | C |  |
| sv_nodrop | Flag | plain | ZADF_NODROP | yes | — | C |  |
| sv_noduellimitvote | Flag | plain | FORBIDVOTE_DUELLIMIT | yes | — | C |  |
| sv_noenemyicons | Flag | plain | ZADF_NO_ENEMY_ICONS | yes | — | C |  |
| sv_noexit | Flag | plain | DF_NO_EXIT | yes | yes | C |  |
| sv_noflagvote | Flag | plain | FORBIDVOTE_FLAG | yes | — | C |  |
| sv_noforcespecvote | Flag | plain | FORBIDVOTE_FORCESPEC | yes | — | C |  |
| sv_nofov | Flag | plain | DF_NO_FOV | yes | yes | C |  |
| sv_nofraglimitvote | Flag | plain | FORBIDVOTE_FRAGLIMIT | yes | — | C |  |
| sv_nofreelook | Flag | plain | DF_NO_FREELOOK | yes | yes | C |  |
| sv_nohealth | Flag | plain | DF_NO_HEALTH | yes | yes | C |  |
| sv_noidentifytarget | Flag | plain | ZADF_NO_IDENTIFY_TARGET | yes | — | C |  |
| sv_noitems | Flag | plain | DF_NO_ITEMS | yes | yes | C |  |
| sv_nojump | Flag | plain | DF_NO_JUMP | yes | yes | C |  |
| sv_nokickvote | Flag | plain | FORBIDVOTE_KICK | yes | — | C |  |
| sv_nokill | Flag | plain | DF2_NOSUICIDE | yes | — | C |  |
| sv_nomapvote | Flag | plain | FORBIDVOTE_MAP | yes | — | C |  |
| sv_nomedals | Flag | plain | ZADF_NO_MEDALS | yes | — | C |  |
| sv_nomonsters | Flag | plain | DF_NO_MONSTERS | yes | yes | C |  |
| sv_nonextmapvote | Flag | plain | FORBIDVOTE_NEXTMAP | yes | — | C |  |
| sv_nonextsecretvote | Flag | plain | FORBIDVOTE_NEXTSECRET | yes | — | C |  |
| sv_noplayertimeout | Bool | plain | CVAR_NOSETBYACS\|CVAR_DEBUGONLY | yes | — | C |  |
| sv_nopointlimitvote | Flag | plain | FORBIDVOTE_POINTLIMIT | yes | — | C |  |
| sv_noresetmapvote | Flag | plain | FORBIDVOTE_RESETMAP | yes | — | C |  |
| sv_norespawn | Flag | plain | DF2_NO_RESPAWN | yes | yes | C |  |
| sv_norespawninvul | Flag | plain | DF2_NO_RESPAWN_INVUL | yes | — | C |  |
| sv_norocketjumping | Flag | plain | ZADF_NO_ROCKET_JUMPING | yes | — | C |  |
| sv_norunes | Flag | plain | DF2_NO_RUNES | yes | — | C |  |
| sv_nospawntelefog | Flag | plain | ZADF_NO_SPAWN_TELEFOG | yes | — | C |  |
| sv_noteamselect | Flag | plain | DF2_NO_TEAM_SELECT | yes | — | C |  |
| sv_noteamswitch | Flag | plain | DF2_NO_TEAM_SWITCH | yes | yes | C |  |
| sv_notimelimitvote | Flag | plain | FORBIDVOTE_TIMELIMIT | yes | — | C |  |
| sv_nounlagged | Flag | plain | ZADF_NOUNLAGGED | yes | — | C |  |
| sv_nounlaggedbfgtracers | Flag | plain | ZADF_NOUNLAGGED_BFG_TRACERS | yes | — | C |  |
| sv_noweaponspawn | Flag | plain | DF_NO_COOP_WEAPON_SPAWN | yes | yes | C |  |
| sv_nowinlimitvote | Flag | plain | FORBIDVOTE_WINLIMIT | yes | — | C |  |
| sv_oldfalldamage | Flag | plain | DF_FORCE_FALLINGZD | yes | yes | C |  |
| sv_password | String | custom | CVAR_ARCHIVE\|CVAR_NOSETBYACS\|CVAR_SENSITIVESERVERSETTING | yes | — | C |  |
| sv_possessioncountdowntime | Int | plain | CVAR_ARCHIVE \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| sv_possessionholdtime | Int | plain | CVAR_ARCHIVE \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| sv_printconnectionmessages | Bool | plain | CVAR_ARCHIVE\|CVAR_NOSETBYACS | yes | — | C |  |
| sv_proximityvoicechat | Bool | custom | CVAR_NOSETBYACS \| CVAR_SERVERINFO | yes | — | C |  |
| sv_pure | Bool | plain | CVAR_SERVERINFO \| CVAR_LATCH | yes | — | C |  |
| sv_queryignoretime | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| sv_randomcoopstarts | Bool | plain | CVAR_SERVERINFO \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| sv_randommaprotation | Bool | plain | CVAR_ARCHIVE \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| sv_rconpassword | String | custom | CVAR_ARCHIVE\|CVAR_NOSETBYACS\|CVAR_SENSITIVESERVERSETTING | yes | — | C |  |
| sv_requireskulltoscore | Bool | custom | CVAR_SERVERINFO \| CVAR_CAMPAIGNLOCK \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| sv_respawndelaytime | Float | custom | CVAR_ARCHIVE \| CVAR_SERVERINFO \| CVAR_GAMEPLAYSETTING | yes | — | A | [notes](../notes/sv_respawndelaytime.md) |
| sv_respawninsurvivalinvasion | Bool | custom | CVAR_ARCHIVE \| CVAR_SERVERINFO \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| sv_respawnsuper | Flag | plain | DF_RESPAWN_SUPER | yes | yes | C |  |
| sv_samelevel | Flag | plain | DF_SAME_LEVEL | yes | yes | C |  |
| sv_samespawnspot | Flag | plain | DF2_SAME_SPAWN_SPOT | yes | yes | C |  |
| sv_sharekeys | Flag | plain | ZADF_SHARE_KEYS | yes | — | C |  |
| sv_shootthroughallies | Flag | plain | ZADF_SHOOT_THROUGH_ALLIES | yes | — | C |  |
| sv_shotgunstart | Flag | plain | DF2_SHOTGUNSTART | yes | — | C |  |
| sv_showcommands | Int | plain | CVAR_ARCHIVE\|CVAR_DEBUGONLY | yes | — | C |  |
| sv_showlauncherqueries | Bool | plain | CVAR_ARCHIVE | yes | — | C |  |
| sv_showspawnnames | Bool | plain | CVAR_DEBUGONLY | yes | — | C |  |
| sv_showwarnings | Bool | plain | CVAR_GLOBALCONFIG\|CVAR_ARCHIVE | yes | — | C |  |
| sv_smartaim | Int | plain | CVAR_ARCHIVE \| CVAR_SERVERINFO | yes | yes | A | [notes](../notes/sv_smartaim.md) |
| sv_spawnfarthest | Flag | plain | DF_SPAWN_FARTHEST | yes | yes | C |  |
| sv_suddendeath | Bool | plain | CVAR_SERVERINFO \| CVAR_LATCH \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| sv_survival_nomapresetondeath | Flag | plain | ZADF_SURVIVAL_NO_MAP_RESET_ON_DEATH | yes | — | C |  |
| sv_survivalcountdowntime | Int | plain | CVAR_ARCHIVE \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| sv_terminatorfragaward | Int | custom | CVAR_SERVERINFO \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| sv_timestamp | Bool | plain | CVAR_ARCHIVE\|CVAR_NOSETBYACS | yes | — | C |  |
| sv_timestampformat | Int | plain | CVAR_ARCHIVE\|CVAR_NOSETBYACS | yes | — | A | [notes](../notes/sv_timestampformat.md) |
| sv_unblockallies | Flag | plain | ZADF_UNBLOCK_ALLIES | yes | — | C |  |
| sv_unblockplayers | Flag | plain | ZADF_UNBLOCK_PLAYERS | yes | — | C |  |
| sv_unlagged_debugactors | Bool | plain | 0 | yes | — | C |  |
| sv_unlimited_pickup | Bool | custom | CVAR_SERVERINFO | yes | yes | C |  |
| sv_updatemaster | Bool | custom | CVAR_SERVERINFO\|CVAR_NOSETBYACS | yes | — | C |  |
| sv_usemapsettingspossessionholdtime | Bool | plain | CVAR_ARCHIVE \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| sv_usemapsettingswavelimit | Bool | plain | CVAR_ARCHIVE \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| sv_useteamstartsindm | Bool | plain | CVAR_SERVERINFO \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| sv_useticbuffer | Bool | plain | CVAR_ARCHIVE\|CVAR_NOSETBYACS\|CVAR_DEBUGONLY | yes | — | A | [notes](../notes/sv_useticbuffer.md) |
| sv_voteconnectwait | Int | plain | CVAR_ARCHIVE \| CVAR_SERVERINFO | yes | — | C |  |
| sv_votecooldown | Int | plain | CVAR_ARCHIVE \| CVAR_SERVERINFO | yes | — | A | [notes](../notes/sv_votecooldown.md) |
| sv_weapondrop | Flag | plain | DF2_YES_WEAPONDROP | yes | yes | C |  |
| sv_weaponstay | Flag | plain | DF_WEAPONS_STAY | yes | yes | C |  |
| sv_website | String | plain | CVAR_ARCHIVE\|CVAR_NOSETBYACS\|CVAR_SERVERINFO | yes | — | C |  |
| switchonpickup | Int | plain | CVAR_USERINFO \| CVAR_UNSYNCED_USERINFO \| CVAR_ARCHIVE | yes | — | C |  |
| synth_watch | Bool | plain | 0 | yes | — | C |  |
| teamdamage | Float | custom | CVAR_SERVERINFO \| CVAR_GAMEPLAYSETTING | yes | yes | A | [notes](../notes/teamdamage.md) |
| teamgame | Bool | custom | CVAR_SERVERINFO \| CVAR_LATCH \| CVAR_CAMPAIGNLOCK | yes | — | C |  |
| teamlms | Bool | custom | CVAR_SERVERINFO \| CVAR_LATCH \| CVAR_CAMPAIGNLOCK | yes | — | C |  |
| teamplay | Bool | custom | CVAR_SERVERINFO \| CVAR_LATCH \| CVAR_CAMPAIGNLOCK | yes | yes | C |  |
| teampossession | Bool | custom | CVAR_SERVERINFO \| CVAR_LATCH \| CVAR_CAMPAIGNLOCK | yes | — | C |  |
| telezoom | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| terminator | Bool | custom | CVAR_SERVERINFO \| CVAR_LATCH \| CVAR_CAMPAIGNLOCK | yes | — | C |  |
| testpolymost | Bool | plain | 0 | yes | — | C |  |
| ticker | Bool | plain | 0 | yes | yes | C |  |
| tilt | Bool | plain | 0 | yes | yes | C |  |
| timelimit | Float | custom | CVAR_SERVERINFO \| CVAR_CAMPAIGNLOCK \| CVAR_GAMEPLAYSETTING | yes | yes | C |  |
| timidity_8bit | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| timidity_byteswap | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| timidity_chorus | String | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| timidity_exe | String | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| timidity_extargs | String | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| timidity_frequency | Int | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | A | [notes](../notes/timidity_frequency.md) |
| timidity_mastervolume | Float | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | A | [notes](../notes/timidity_mastervolume.md) |
| timidity_pipe | Int | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| timidity_reverb | String | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| timidity_stereo | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| transsouls | Float | custom | CVAR_ARCHIVE | yes | yes | A | [notes](../notes/transsouls.md) |
| turbo | Float | custom | 0 | yes | yes | C |  |
| use_joystick | Bool | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG\|CVAR_NOINITCALL | yes | yes | C |  |
| use_mouse | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| var_friction | Bool | plain | CVAR_SERVERINFO | yes | yes | C |  |
| var_pushers | Bool | plain | CVAR_SERVERINFO | yes | yes | C |  |
| vid_activeinbackground | Bool | plain | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | yes | C |  |
| vid_adapter | Int | plain | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | yes | C |  |
| vid_aspect | Int | custom | CVAR_GLOBALCONFIG\|CVAR_ARCHIVE | yes | yes | C |  |
| vid_asyncblit | Bool | plain | CVAR_NOINITCALL\|CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| vid_attachedsurfaces | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| vid_brightness | Float | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| vid_contrast | Float | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| vid_cursor | String | custom | CVAR_ARCHIVE \| CVAR_NOINITCALL | yes | yes | C |  |
| vid_defbits | Int | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| vid_defheight | Int | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| vid_defwidth | Int | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| vid_displaybits | Int | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| vid_forceddraw | Bool | plain | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | — | C |  |
| vid_fps | Bool | plain | 0 | yes | yes | C |  |
| vid_hw2d | Bool | custom | CVAR_NOINITCALL | yes | — | C |  |
| vid_hwaalines | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| vid_maxfps | Int | custom | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | yes | C |  |
| vid_noblitter | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| vid_nopalsubstitutions | Bool | custom | CVAR_ARCHIVE | yes | yes | C |  |
| vid_nowidescreen | Bool | custom | CVAR_GLOBALCONFIG\|CVAR_ARCHIVE | yes | — | C |  |
| vid_palettehack | Bool | plain | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| vid_refreshrate | Int | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| vid_renderer | Int | custom | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG \| CVAR_NOINITCALL | yes | yes | C |  |
| vid_showpalette | Int | plain | 0 | yes | yes | C |  |
| vid_tft | Bool | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| vid_vsync | Bool | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | yes | C |  |
| vid_winscale | Float | custom | CVAR_ARCHIVE\|CVAR_GLOBALCONFIG | yes | — | C |  |
| voice_enable | Int | plain | CVAR_ARCHIVE \| CVAR_NOSETBYACS \| CVAR_USERINFO | yes | — | C |  |
| voice_listenfilter | Int | plain | CVAR_NOSETBYACS \| CVAR_USERINFO | yes | — | C |  |
| voice_muteself | Bool | custom | CVAR_ARCHIVE \| CVAR_NOSETBYACS \| CVAR_GLOBALCONFIG | yes | — | C |  |
| voice_noisemodelfile | String | plain | CVAR_ARCHIVE \| CVAR_NOSETBYACS \| CVAR_GLOBALCONFIG | yes | — | C |  |
| voice_outputvolume | Float | custom | CVAR_ARCHIVE \| CVAR_NOSETBYACS \| CVAR_GLOBALCONFIG | yes | — | C |  |
| voice_panelrows | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| voice_panelshowteams | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| voice_panelx | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| voice_panely | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| voice_recorddriver | Int | custom | CVAR_ARCHIVE \| CVAR_NOSETBYACS \| CVAR_GLOBALCONFIG | yes | — | C |  |
| voice_recordsensitivity | Float | custom | CVAR_ARCHIVE \| CVAR_NOSETBYACS \| CVAR_GLOBALCONFIG | yes | — | C |  |
| voice_recordvolume | Float | custom | CVAR_ARCHIVE \| CVAR_NOSETBYACS \| CVAR_GLOBALCONFIG | yes | — | C |  |
| voice_showpanel | Int | custom | CVAR_ARCHIVE | yes | — | C |  |
| voice_suppressnoise | Bool | plain | CVAR_ARCHIVE \| CVAR_NOSETBYACS \| CVAR_GLOBALCONFIG | yes | — | C |  |
| voice_transmitfilter | Int | plain | CVAR_NOSETBYACS \| CVAR_USERINFO | yes | — | C |  |
| wavelimit | Int | custom | CVAR_CAMPAIGNLOCK \| CVAR_SERVERINFO \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| wi_autoscreenshot | Int | plain | CVAR_ARCHIVE | yes | — | C |  |
| wi_noautostartmap | Bool | plain | CVAR_USERINFO\|CVAR_UNSYNCED_USERINFO\|CVAR_ARCHIVE | yes | yes | C |  |
| wi_percents | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| wi_showtotaltime | Bool | plain | CVAR_ARCHIVE | yes | yes | C |  |
| win_x | Int | plain | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | yes | C |  |
| win_y | Int | plain | CVAR_ARCHIVE \| CVAR_GLOBALCONFIG | yes | yes | C |  |
| winlimit | Int | custom | CVAR_SERVERINFO \| CVAR_CAMPAIGNLOCK \| CVAR_GAMEPLAYSETTING | yes | — | C |  |
| wipetype | Int | plain | CVAR_ARCHIVE | yes | yes | C |  |
| zacompatflags | Int | custom | CVAR_SERVERINFO \| CVAR_CAMPAIGNLOCK \| CVAR_GAMEPLAYFLAGSET | yes | — | C |  |
| zadmflags | Int | custom | CVAR_SERVERINFO \| CVAR_CAMPAIGNLOCK \| CVAR_GAMEPLAYFLAGSET | yes | — | A | [notes](concepts/dmflags.md) |
