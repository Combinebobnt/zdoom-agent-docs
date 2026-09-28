# `void SetMugShotState(str state)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** `SetMugShotState - ZDoom Wiki.html` (https://zdoom.org/w/index.php?title=SetMugShotState&oldid=52901), verified 2026-07-29 against the Zandronum source's `src/p_acs.cpp`, `sv_commands.cpp`, `cl_main.cpp`, `g_shared/shared_sbar.cpp`, `g_shared/sbarinfo.cpp`, `g_doom/doom_sbar.cpp`, and `g_shared/sbar_mugshot.cpp`; corrections backed by `src/d_main.cpp`, `src/g_level.cpp`, `src/network/netcommand.cpp`, `wadsrc/static/sbarinfo.txt`, `wadsrc/static/sbarinfo/*.txt` and `wadsrc/static/mapinfo/heretic.txt`/`hexen.txt`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Sets the current mugshot ("face") animation state for the status bar's mugshot widget. Compiler
builtin (`PCD_SETMUGSHOTSTATE`, the zt-bcc source's `src/builtin.c:158,306` — signature `";s"`, void
return, one required `str` argument), implementation in
the Zandronum source's `src/p_acs.cpp:12743-12750`.

## Behavior

```cpp
case PCD_SETMUGSHOTSTATE:
    // [EP] Server doesn't have a status bar, but should inform the clients about it
    if ( NETWORK_GetState() == NETSTATE_SERVER )
        SERVERCOMMANDS_SetMugShotState(FBehavior::StaticLookupString(STACK(1)));
    else if ( StatusBar != NULL )
        StatusBar->SetMugShotState(FBehavior::StaticLookupString(STACK(1)));
    sp--;
    break;
```

- **Completely activator-independent, and not scoped to one player at all.** Unlike
  `Print`/`HudMessage`, the opcode never reads `activator`. On a server (`NETSTATE_SERVER`,
  `network.h:266-282`, set by `-host` at the Zandronum source's `src/d_main.cpp:2428-2429`), which
  never creates a status bar of its own (`src/g_level.cpp:496-497`), it calls
  `SERVERCOMMANDS_SetMugShotState(statename)`
  (the Zandronum source's `src/sv_commands.cpp:5178-5185`), which does
  `NetCommand(...).sendCommandToClients()` with **no player argument**. The default
  (`ulPlayerExtra = MAXPLAYERS, flags = 0`, the Zandronum source's `src/network/netcommand.h:109`)
  broadcasts to every connected client. The only clients skipped are ones still joining the
  current level (`CLS_SPAWNED_BUT_NEEDS_AUTHENTICATION`), since a no-target, no-flag send gets
  `SVCF_SKIP_CLIENTS_WITHOUT_FULLUPDATE` added (`src/network/netcommand.cpp:79-80,307-308`), and
  the state is not replayed to them later. There is no per-player targeting
  parameter and no way to change only the calling player's own mugshot from server-side ACS — one
  `SetMugShotState()` call changes every connected client's status bar face at once. Each client
  applies it independently on receipt (`SVC2_SETMUGSHOTSTATE` in
  the Zandronum source's `src/cl_main.cpp:2351-2360`, `StatusBar->SetMugShotState(statename)` on that
  client's own local `StatusBar`). This broadcast-to-everyone behavior is not mentioned anywhere
  on the wiki page, which only shows a single-player example.
- When *not* running as a server (singleplayer, an offline bot game in `NETSTATE_SINGLE_MULTIPLAYER`,
  or any script a client runs locally, normally a `CLIENTSIDE` one), the `else if` branch runs
  instead and sets the local `StatusBar` directly with no networking at all. This is the only path
  that actually is "just this one player."
- `state` is looked up via `FBehavior::StaticLookupString` the same as any other string-arg
  builtin. An invalid or out-of-range string handle resolves to `NULL`
  (the Zandronum source's `src/p_acs.cpp:3318-3355`). On a server that just sends an empty name
  (`NetCommand::addString` treats `NULL` as length 0, `src/network/netcommand.cpp:221-233`),
  which clients ignore as an unknown state. Offline or on a client, a status bar that forwards to
  `FMugShot::SetState` misses the lookup and then calls `strchr` on the null pointer
  (`src/g_shared/sbar_mugshot.cpp:303`). That is undefined behavior (a null-pointer read, likely a
  crash), not a safe no-op.

## Whether the named state existing matters, and what happens if it doesn't (silent no-op, not a fallback)

`StatusBar->SetMugShotState` is a **virtual with a no-op default**
(the Zandronum source's `src/g_shared/shared_sbar.cpp:1519-1521`,
`DBaseStatusBar::SetMugShotState(const char*, bool, bool) { }`). It is overridden in exactly two
places:

- `DSBarInfo` (SBARINFO-driven status bars,
  the Zandronum source's `src/g_shared/sbarinfo.cpp:1146-1149`).
- Doom's own **native, non-SBARINFO** status bar
  (the Zandronum source's `src/g_doom/doom_sbar.cpp:1367-1370`, and also used to draw the classic
  face via `MugShot.GetFace(...)` at line 1350). So this works out of the box on Doom even
  without a custom SBARINFO lump, contrary to what "as defined in SBARINFO" in the wiki's own
  wording might suggest.

Which bar a game gets is decided by Zandronum's `CreateStatusBar`
(`src/g_shared/sbarinfo.cpp:1575-1620`). The stock `zandronum.pk3` ships a root `SBARINFO` lump
holding the default mugshot state definitions (`wadsrc/static/sbarinfo.txt`), so the
custom-lump branch always runs. The parsed game type defaults to the running game
(`sbarinfo.cpp:471`); a mod SBARINFO's `base` line, or a `statusbar` block without one, changes it:

- Stock Doom and Chex get the native Doom bar (`sbarinfo.cpp:1583-1587`). The override applies.
- Heretic and Hexen have no native bars in Zandronum. Their stock bars are SBARINFO scripts
  (`wadsrc/static/mapinfo/heretic.txt:28`, `hexen.txt:30`) run through `DSBarInfo`, so the state
  is set, but neither `sbarinfo/heretic.txt` nor `sbarinfo/hexen.txt` draws a mugshot, so nothing
  visible changes unless a mod's SBARINFO adds `drawmugshot`.
- Strife (or a mod SBARINFO with `base Strife`) gets the native Strife bar
  (`sbarinfo.cpp:1590-1593`), which has no override. `SetMugShotState` silently does
  nothing at all there (the base no-op), not a fallback to a default face.
- A custom SBARINFO with its own `statusbar` block and no `base` gets `DSBarInfo`, and the
  override applies.

Both overrides just forward to `FMugShot::SetState`
(the Zandronum source's `src/g_shared/sbar_mugshot.cpp:296-332`), which is where "state doesn't
exist" is actually decided:

```cpp
FMugShotState *state = FindMugShotState(FName(state_name, true));
if (state == NULL) {
    // ...try the part before a '.', if any...
    if (state == NULL) {
        // Requested state does not exist, so do nothing.
        return false;
    }
}
```

An unknown/typo'd state name is a **verified silent no-op** — `false` is returned, but the ACS
builtin never reads a return value at all (`void`), so from ACS this is completely
indistinguishable from success; the mugshot just keeps showing whatever it was already on. There
is no fallback to a default/"normal" state. If `state_name` contains a `.` (e.g. a directional
variant like `"pain.ouch"`), a miss on the full name retries just the part before the dot before
giving up.

If the state *is* found and differs from the currently-playing one, it always switches
immediately and resets the new state's animation — the ACS builtin only ever supplies the
`state_name` argument, so `wait_till_done` and `reset` both use the virtual's own defaults
(`false`, `false`; declared in the Zandronum source's `src/g_shared/sbar.h:373`). Calling
`SetMugShotState` again with the *same* state name that's already playing does **not** restart
its animation (`reset` is `false`), unlike what "sets the state" might suggest. It still clears
the mugshot's internal normal/ouch flags (`sbar_mugshot.cpp:314-315`), which keeps the automatic
normal/god face from being reasserted until the current state finishes.

The set state plays until it finishes (`FMugShot::Tick`, `sbar_mugshot.cpp:256-267`). The
player's own status can still replace it earlier: taking damage, the evil grin, and death switch
the face immediately, and the rampage face waits for it to finish (`FMugShot::UpdateState`,
`sbar_mugshot.cpp:341-483`).

## Engine-family divergence: activator-scoped and view-gated, not a client-broadcast, and inert on every stock status bar

Where the section above describes Zandronum's `SetMugShotState` as "completely activator-independent, and not scoped to one player at all," broadcasting unconditionally to every connected client from server-side ACS, this engine's version of the same opcode works the opposite way. Its C++ opcode handler (UZDoom's `src/playsim/p_acs.cpp`) only forwards the call to the local status bar when either the current game isn't a multiplayer game at all, or the script's `activator` actor happens to be the one the local console player is actually viewing through right now (its own body, or whatever camera actor it's currently possessing). If neither holds — for example a multiplayer script whose activator is some other player's pawn, or a scope with no meaningful activator at all — the call is silently skipped for that execution, with no fallback and no broadcast. There is no "send to every connected client" counterpart in this engine's networking model: each client independently evaluates this same activator check against its own console player, so a single call only has any chance of affecting the mugshot belonging to whichever client is running as (or currently watching through) the activator, never any other client's view.

Separately and more fundamentally, this engine dispatches the call through a scripting-language virtual method on the status bar object rather than the fixed pair of C++ subclass overrides Zandronum uses. Neither of the two status-bar implementations this engine ships by default — the native Doom status bar, nor the wrapper that backs SBARINFO-defined bars — actually overrides that virtual method, so for every stock game/status-bar configuration the call reaches no code that touches any stored mugshot state at all: it is a complete no-op regardless of whether the named state exists, not merely for an unknown/typo'd name as documented above for Zandronum. The face these built-in bars actually show is instead recomputed automatically every frame from the player's own pain/health/god-mode status, entirely independent of anything ever passed to this builtin. The only way this builtin could have any visible effect on this engine is if a mod supplies its own custom scripting-language status bar class that itself overrides that virtual method — something no stock configuration does.

## See also

None of `List of default mug shots`, `A_SetMugshotState` (ZScript — **Zandronum has no ZScript at
all**, see [Constants](../concepts/constants.md) and
[Activation](../concepts/activation.md) for the same caveat elsewhere in this tree), or `SBARINFO`
needed further verification for this doc.
