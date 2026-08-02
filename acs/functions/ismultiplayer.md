# `bool IsNetworkGame()` (wiki name: `IsMultiplayer`)

Compiler builtin. `PCD_ISMULTIPLAYER` (the Zandronum source's `src/p_acs.h:685`), implementation
inline in the interpreter's opcode switch (`case PCD_ISMULTIPLAYER:`,
the Zandronum source's `src/p_acs.cpp:11202-11205`).

**Bucket:** compiler builtin.

```cpp
case PCD_ISMULTIPLAYER:

	PushToStack(( NETWORK_GetState( ) == NETSTATE_SERVER ) ||
		NETWORK_InClientMode() );
	break;
```

where (the Zandronum source's `src/network.cpp:1552-1555`):

```cpp
bool NETWORK_InClientMode( )
{
	return ( NETWORK_GetState( ) == NETSTATE_CLIENT ) || ( CLIENTDEMO_IsPlaying( ) == true );
}
```

and the network state enum (the Zandronum source's `src/network.h:266-281`):

```cpp
enum
{
	NETSTATE_SINGLE,             // single player
	NETSTATE_SINGLE_MULTIPLAYER, // single player, emulating a network game (bots, etc) —
	                              // this is the "multiplayer" console command
	NETSTATE_CLIENT,
	NETSTATE_SERVER,
	NUM_NETSTATES
};
```

- Returns `true` only for `NETSTATE_SERVER` or `NETSTATE_CLIENT` (or client-side demo playback,
  via `NETWORK_InClientMode()`). **`NETSTATE_SINGLE_MULTIPLAYER` — the state produced by the
  `multiplayer` console command, which fakes a network game for bot testing — is deliberately
  excluded.** This confirms the wiki's own claim verbatim ("being emulated by the multiplayer
  console command does not count") against the actual enum/switch rather than just trusting the
  prose.
- Fork-specific nuance the wiki page doesn't mention: a client watching a **local demo recorded
  while playing as a network client** (`CLIENTDEMO_IsPlaying()`) also reads back `true` here,
  since `NETWORK_InClientMode()` folds demo playback in with `NETSTATE_CLIENT`. Purely offline
  demo playback of a single-player recording does not trigger this (that path never sets
  `NETSTATE_CLIENT` or the clientdemo flag).
- **Naming divergence — the wiki's function name doesn't exist as a callable in this toolchain.**
  The wiki documents this as `IsMultiplayer()`, and the *raw p-code enum* used by the engine and
  by `zt-bcc/lib/zasm.bcs` is indeed spelled `PCD_ISMULTIPLAYER` (`zasm.bcs:131`, same position as
  `p_acs.h:685` — confirmed positionally identical, i.e. same opcode number, not just a
  same-named coincidence). But `zt-bcc`'s own compiler-builtin name table
  (the zt-bcc source's `src/builtin.c:60`) registers this opcode under the name **`isnetworkgame`**
  only — there is no `ismultiplayer` entry anywhere in `zt-bcc/src` or `zt-bcc/lib` (confirmed by
  grep). In BCS, call it as `IsNetworkGame()` (case-insensitive per BCS
  convention); a script literally named `IsMultiplayer()` will fail to compile with `bcc`. This
  matches the wiki's own "Notes" section, which mentions `IsNetworkGame` as an old alternate name
  for the exact same p-code — but for this toolchain specifically, `IsNetworkGame` is the *only*
  name that resolves, not merely an alternate one.
- The wiki's cross-reference to `SinglePlayer()`/`GameType()` (only reporting singleplayer for
  offline Cooperative without multiplayer emulation) was not independently re-verified against
  those functions' own switch cases here — noted as unverified if precision on that specific
  relationship ever matters.

**Returns:** `bool` (`0`/`1`) — whether the current game is an actual network game (hosting or
connected as a client, including demo-of-a-network-game playback), as opposed to true
single-player or bot-emulated "multiplayer".

**Provenance:** wiki page `IsMultiplayer - Zandronum Wiki.html` (`_intake/`, retrieved
`oldid=1306`) + source-verified (`p_acs.h:685`, `p_acs.cpp:11202-11205`, `network.cpp:1552-1555`,
`network.h:266-281`, `zt-bcc/src/builtin.c:60`, `zt-bcc/lib/zasm.bcs:131`). The wiki's behavioral
description is accurate; this doc's additions are the demo-playback nuance and the
wiki-name-vs-callable-name divergence, neither of which the wiki mentions. **Engine:** Zandronum
3.2.1 — `PCD_ISMULTIPLAYER`'s implementation traces back to the original Skulltag 0.97c2 import
commit (`bc562a817`), confirmed via `git log -S` on `p_acs.cpp`/`network.cpp`, which is an
ancestor of the 3.2.1 version-bump commit `28f736fb3`; this is long-standing base functionality,
not a recent addition. **Tier:** A.

**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.
