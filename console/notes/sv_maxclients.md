# `sv_maxclients` and `sv_maxplayers`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** Zandronum source `src/sv_main.cpp:CUSTOM_CVAR` declarations + verified against engine behavior.

Two separate cvars that both limit player counts, but with fundamentally different semantics and admin-bypass rules. Both default to 32 for backward compatibility with older mods (the engine max is 64, see `MAXPLAYERS` in `src/doomdef.h`).

## Semantic difference

- **`sv_maxclients`** — total hard limit on connected clients **including administrators**. When the server is full at this limit, new clients cannot connect *except* administrators (admins can bypass up to the absolute maximum of 64, per the admin-list file). This is the connection-level limit.
- **`sv_maxplayers`** — limit on how many clients are actually *playing* (not spectating). Excess clients are forced to spectate. This is the gameplay-level limit, independent of connection state.

For example, with `sv_maxclients 32` and `sv_maxplayers 16`, the server accepts up to 32 connected clients, but only 16 can be active players; the remaining 16 are automatically spectators. Administrators can connect beyond 32 (up to 64 total, per the admin list) even when `sv_maxclients 32` would normally reject new clients.

## Storage and replication

Both are marked `CVAR_ARCHIVE | CVAR_SERVERINFO`, so they persist to the config file and replicate to clients. Neither has the `CVAR_LATCH` flag, so changes take effect immediately without requiring a map restart.

**Inventory generator note:** The generated inventory row's `Flags` cell for both of these shows only `32` (the default value) instead of the actual flags, due to a generator parsing issue — this is a known artifact. The real flags are `CVAR_ARCHIVE | CVAR_SERVERINFO` for `sv_maxclients` and `CVAR_ARCHIVE | CVAR_SERVERINFO | CVAR_GAMEPLAYSETTING` for `sv_maxplayers`.

## Limits and validation

Both cvars clamp to the range `[0, 64]`. Setting either to `0` is allowed but removes the limit entirely (clients can connect up to the absolute 64 cap). Values above 64 are rejected by the CUSTOM_CVAR validation block, which prints an error message and forces the value to `MAXPLAYERS` (64).

## Admin bypass behavior

Administrators (IPs in the admin-list file, per `sv_adminlistfile`) can connect to the server even when it is full at `sv_maxclients`, up to the absolute maximum of 64 total connections. Administrators are not exempt from `sv_maxplayers` — they still count toward the active-player limit and can be forced to spectate if `sv_maxplayers` is exceeded. This is an asymmetric bypass: administrators bypass the *connection* limit but not the *gameplay* limit.

## Zandronum-specific: `sv_maxclients`/`sv_maxplayers` don't exist on UZDoom

Neither cvar exists on UZDoom (checked the `~/source/UZDoom` checkout, `5a9b0ec511` (2026-08-15):
no `sv_`-prefixed cvar of any kind is registered anywhere in the tree, and there's no admin-IP-list
concept — `adminlist`/`IsAdmin` are absent too). This isn't a naming difference or a behavior tweak; the underlying
model these two cvars implement doesn't apply. UZDoom keeps the original ZDoom peer-to-peer
netcode (join-in-progress over a fixed `players[]`/`playeringame[]` array, no dedicated-server
process, no distinct "connected but spectating" vs. "actively playing" cap, no admin bypass path)
rather than Zandronum's client-server model with a real dedicated server, RCON, and an admin list
that can bypass the connection cap. `MAXPLAYERS` is still `64` on UZDoom too (`src/common/engine/
i_net.h`), so the absolute player-count ceiling this doc's `[0, 64]` clamp discussion refers to is
shared — only the two cvars, their admin-bypass semantics, and the "connected but spectating"
distinction are Zandronum-only.

## Related cvars

- **`sv_adminlistfile`** — path to the admin-list file (default `adminlist.txt`), which defines which IPs are administrators and thus can bypass `sv_maxclients`.
- **`sv_maxclientsperip`** — limits how many connections from the same IP address are allowed (default 2), independent of `sv_maxclients`.
