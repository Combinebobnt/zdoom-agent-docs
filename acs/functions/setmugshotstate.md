# `void SetMugShotState(str state)`

**Tier:** A
**Engine:** Zandronum 3.2.1 (checked out source reports `3.3-alpha`; `PCD_SETMUGSHOTSTATE` and `FMugShot::SetState` carry no version-gating markers around them, so this is not expected to be version-sensitive — see "Engine scope" in `../../shared/AUTHORING.md`).
**Provenance:** `SetMugShotState - ZDoom Wiki.html` (https://zdoom.org/w/index.php?title=SetMugShotState&oldid=52901), verified 2026-07-29 against the Zandronum source's `src/p_acs.cpp`, `sv_commands.cpp`, `cl_main.cpp`, `g_shared/shared_sbar.cpp`, `g_shared/sbarinfo.cpp`, `g_doom/doom_sbar.cpp`, and `g_shared/sbar_mugshot.cpp`.
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
  `Print`/`HudMessage`, the opcode never reads `activator`. On a server (`NETSTATE_SERVER`, which
  — per `network.h:266-282` — covers a dedicated server *and* a listen server hosting), it calls
  `SERVERCOMMANDS_SetMugShotState(statename)`
  (the Zandronum source's `src/sv_commands.cpp:5178-5185`), which does
  `NetCommand(...).sendCommandToClients()` with **no player argument** — the default
  (`ulPlayerExtra = MAXPLAYERS, flags = 0`, the Zandronum source's `src/network/netcommand.h:109`)
  broadcasts to *every* connected client, unconditionally. There is no per-player targeting
  parameter and no way to change only the calling player's own mugshot from server-side ACS — one
  `SetMugShotState()` call changes every connected client's status bar face at once. Each client
  applies it independently on receipt (`SVC2_SETMUGSHOTSTATE` in
  the Zandronum source's `src/cl_main.cpp:2351-2360`, `StatusBar->SetMugShotState(statename)` on that
  client's own local `StatusBar`). This broadcast-to-everyone behavior is not mentioned anywhere
  on the wiki page, which only shows a single-player example.
- When *not* running as a server (singleplayer, or executed by a `CLIENTSIDE` script on a client),
  the `else if` branch runs instead and sets the local `StatusBar` directly with no networking at
  all — this is the only path that actually is "just this one player."
- `state` is looked up via `FBehavior::StaticLookupString` the same as any other string-arg
  builtin (an invalid/out-of-range string handle resolves to whatever `StaticLookupString`
  returns for that case, not a crash).

## Whether the named state existing matters, and what happens if it doesn't (silent no-op, not a fallback)

`StatusBar->SetMugShotState` is a **virtual with a no-op default**
(the Zandronum source's `src/g_shared/shared_sbar.cpp:1519-1521`,
`DBaseStatusBar::SetMugShotState(const char*, bool, bool) { }`). It is overridden in exactly two
places:

- `DSBarInfo` (SBARINFO-defined status bars,
  the Zandronum source's `src/g_shared/sbarinfo.cpp:1146-1149`) — any game using a SBARINFO lump.
- Doom's own **native, non-SBARINFO** status bar
  (the Zandronum source's `src/g_doom/doom_sbar.cpp:1367-1370`, and also used to draw the classic
  face via `MugShot.GetFace(...)` at line 1350) — so this works out of the box on Doom even
  without a custom SBARINFO lump, contrary to what "as defined in SBARINFO" in the wiki's own
  wording might suggest.

No override exists for Heretic/Hexen/Strife's native status bars in this fork — on those games,
absent a SBARINFO lump, `SetMugShotState` silently does nothing at all (hits the base no-op),
not a fallback to a default face.

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
(`false`, `false`; declared in the Zandronum source's `src/g_shared/sbar.h:374`). Calling
`SetMugShotState` again with the *same* state name that's already playing is a safe no-op that
does **not** restart its animation (`reset` is `false`), unlike what "sets the state" might
suggest.

## See also

None of `List of default mug shots`, `A_SetMugshotState` (ZScript — **this fork has no ZScript at
all**, see [Constants](../concepts/constants.md) and
[Activation](../concepts/activation.md) for the same caveat elsewhere in this tree), or `SBARINFO`
needed further verification for this doc.
