# `bool IsNetworkGame()` (wiki name: `IsMultiplayer`)

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-15)
**Provenance:** wiki page `IsMultiplayer - Zandronum Wiki.html` (`_intake/`, retrieved
`https://wiki.zandronum.com/w/index.php?title=IsMultiplayer&oldid=1306`) + source-verified (`p_acs.h:685`, `p_acs.cpp:11202-11205`, `network.cpp:1552-1555`,
`network.h:266-281`, `zt-bcc/src/builtin.c:60`, `zt-bcc/lib/zasm.bcs:131`). The wiki's behavioral
description is accurate; this doc's additions are the demo-playback nuance and the
wiki-name-vs-callable-name divergence, neither of which the wiki mentions.

**Phase 5 correction, 2026-08-15: this file's own `Applies to:` previously read `Zandronum=no`,
which contradicted its own body — every line below was already about a working Zandronum
implementation.** `engine_matrix.py`'s automated cohort classifier resolves the doc name
`ismultiplayer` to `zt-bcc`'s compiler-builtin table entry `isnetworkgame`
(`zt-bcc/src/builtin.c:60`), then checks that name against each engine's own PCD enum by
name-guessing `pcd_isnetworkgame` — which exists at UZDoom's index 118 but not at Zandronum's
(Zandronum spells the same-position opcode `PCD_ISMULTIPLAYER`), so the automated pass reported
`uzdoom-only` and never surfaced the mismatch against this file's own already-correct prose.
Corrected here; worth teaching a future automated cohort pass to flag a doc-file-vs-classifier
disagreement like this one, not just a classifier-vs-source one, but that's a tooling
follow-up, not done as part of this fix.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Compiler builtin. `PCD_ISMULTIPLAYER` (the Zandronum source's `src/p_acs.h:685`), implementation
inline in the interpreter's opcode switch (`case PCD_ISMULTIPLAYER:`,
the Zandronum source's `src/p_acs.cpp:11202-11205`).

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

## Engine-family divergence: netgame flag vs. live network-state check

UZDoom implements the same compiler-table entry (`isnetworkgame`, dispatched to `PCD_ISNETWORKGAME`
— the same opcode position as Zandronum's `PCD_ISMULTIPLAYER`, just spelled differently in each
engine's own enum) with a simpler mechanism: `case PCD_ISNETWORKGAME: PushToStack(netgame); break;`
(`src/playsim/p_acs.cpp:8943-8945`) — a single global `bool netgame`, not a live
`NETWORK_GetState()`/`NETWORK_InClientMode()` computation. `netgame` (together with `multiplayer`)
is set `true` by normal multiplayer session setup (`src/g_game.cpp:2932`) and by demo playback with
more than one recorded player (`src/g_game.cpp:2931`), and reset `false` at points including level
load (`src/g_level.cpp:469`) and demo teardown (`src/d_net.cpp:403`).

**Not independently re-verified for UZDoom:** whether a bot-emulated "multiplayer" console command
sets `netgame` the way Zandronum's `NETSTATE_SINGLE_MULTIPLAYER` state deliberately does *not*
count, and whether single-player-recording demo playback vs. network-recording demo playback are
distinguished the same way Zandronum's `CLIENTDEMO_IsPlaying()` nuance documents above — treat
UZDoom's exact edge-case behavior here as unconfirmed rather than assuming symmetry with
Zandronum's documented nuances.
