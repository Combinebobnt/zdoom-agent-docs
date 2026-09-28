# `sv_maxclients` and `sv_maxplayers`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum source `src/sv_main.cpp:CUSTOM_CVAR` declarations + verified against engine behavior. Connection cap and admin slot: `src/sv_main.cpp:1043-1048` (`SERVER_FindFreeClientSlot`), `src/sv_main.cpp:1995-2002`; join gate: `src/gamemode.cpp:997` (`GAMEMODE_PreventPlayersFromJoining`), `src/sv_main.cpp:6689-6691`; map-load respectate: `src/p_setup.cpp:4555` (`P_SetupLevel`).

Two separate cvars that both limit player counts, but with fundamentally different semantics and admin-bypass rules. Both default to 32 for backward compatibility with older mods (the engine max is 64, see `MAXPLAYERS` in `src/doomdef.h`).

## Semantic difference

- **`sv_maxclients`** — total hard limit on connected clients **including administrators**, and bots count toward it too (`SERVER_CountPlayers( true )`; `BOTS_FindFreePlayerSlot` also refuses to add a bot once it's reached). When the server is full at this limit, new clients get "Server is full." *except* an administrator (an IP in the admin-list file), who gets exactly one extra slot. This is the connection-level limit.
- **`sv_maxplayers`** — limit on how many clients are actually *playing* (not true spectators). A spectator asking to join while the limit is reached is refused and put in the join queue instead. This is the gameplay-level limit, independent of connection state.

For example, with `sv_maxclients 32` and `sv_maxplayers 16`, the server accepts up to 32 connected clients, but only 16 can be active players; the rest stay spectators, queued if they asked to join. With 32 connected, one administrator can still connect (33 total). A second one is refused.

## Storage and replication

Both are marked `CVAR_ARCHIVE | CVAR_SERVERINFO` (`sv_maxplayers` adds `CVAR_GAMEPLAYSETTING`), so they persist to the config file and replicate to clients. Neither has the `CVAR_LATCH` flag, so a new value applies to the next connection or join attempt without a map restart. Raising `sv_maxplayers` pops the join queue at once. Lowering either one kicks nobody. After lowering `sv_maxplayers`, surplus active players are only turned into spectators at the next map load (`P_SetupLevel`).

**Inventory generator note:** The generated inventory row's `Flags` cell for both of these shows only `32` (the default value) instead of the actual flags, due to a generator parsing issue — this is a known artifact. The real flags are `CVAR_ARCHIVE | CVAR_SERVERINFO` for `sv_maxclients` and `CVAR_ARCHIVE | CVAR_SERVERINFO | CVAR_GAMEPLAYSETTING` for `sv_maxplayers`.

## Limits and validation

Both cvars clamp to the range `[0, 64]`. A negative value is silently set to `0`. Values above 64 are rejected by the CUSTOM_CVAR validation block, which prints an error message and forces the value to `MAXPLAYERS` (64). The `-host <n>` command-line parameter sets `sv_maxclients` at server startup.

`0` is not "unlimited". Neither cvar special-cases it (unlike `sv_maxclientsperip`, where `0` does disable the check). `sv_maxclients 0` refuses every non-administrator connection, leaving only the single admin slot. `sv_maxplayers 0` means no spectator can ever join the game.

## Admin bypass behavior

Administrators (IPs in the admin-list file, per `sv_adminlistfile`) can connect to the server even when it is full at `sv_maxclients`, but only into one extra slot: `SERVER_FindFreeClientSlot` refuses everyone, admins included, once `sv_maxclients + 1` players are in the game. It's an emergency slot, and a client using it is sent an "Emergency!" MOTD saying the server is full. (The source comment calls this joining "from localhost", but the check is the admin IP list.) Administrators are also not exempt from `sv_maxclientsperip`, which is checked first. Administrators are not exempt from `sv_maxplayers` either. They still count toward the active-player limit and get queued like anyone else when it's reached. This is an asymmetric bypass: administrators bypass the *connection* limit, by one slot, but not the *gameplay* limit.

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
