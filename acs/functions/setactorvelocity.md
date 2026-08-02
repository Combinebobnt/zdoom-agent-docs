# `bool SetActorVelocity(int tid, fixed velx, fixed vely, fixed velz, bool add, bool setbob)`

Sets or adds to the velocity of the actor(s) matching `tid`. Extension function (`zcommon.bcs`
index -23), implementation in `DLevelScript::CallFunction`'s `case ACSF_SetActorVelocity`
(the Zandronum source's `src/p_acs.cpp:6104-6118`), which forwards into `P_Thing_SetVelocity`
(the Zandronum source's `src/p_things.cpp:602-622`).

**Bucket:** extension function.

- `tid` — **`0` means the activator**, passed straight to `P_Thing_SetVelocity` with no null
  check at the `p_acs.cpp` call site (`args[0] == 0` branch, line 6105-6107). This is
  **verified safe, not a crash**: `P_Thing_SetVelocity` itself guards `if (actor != NULL)`
  (`p_things.cpp:604`) before touching anything, so a `tid=0` call from a script with no
  activator (`OPEN`/`ENTER`/`RESPAWN`/etc.) is a silent no-op — unlike the sibling
  `PlayActorSound` (see [PlayActorSound](playactorsound.md)), which crashes in exactly this
  situation because its own callee skips the null guard. Nonzero `tid` iterates *every* matching
  actor via `TActorIterator`, not just one — undocumented fan-out, same pattern as
  [PlaySound](playsound.md).
- `velx`/`vely`/`velz` — **plain `fixed_t` map-units-per-tic, added directly to
  `actor->velx`/`vely`/`velz`.** No `/8`-style scaling macro is involved (contrast
  [Floor_MoveToValue](floor_movetovalue.md)'s `speed` argument) — the wiki's numbers can be used
  as-is.
- `add` — if `false` (replace mode), `actor->velx`/`vely`/`velz` are zeroed **and, if the actor
  is a player, `player->velx`/`vely` are also unconditionally zeroed** (`p_things.cpp:606-610`)
  *regardless of `setbob`* — see the `setbob` note below, this is the one real gap in the wiki's
  description. If `true` (add mode), the existing velocity (both actor and, conditionally, player
  bob velocity) is left alone and `velx`/`vely`/`velz` are added on top.
- `setbob` — **only gates the `+=` onto the player's separate `velx`/`vely` bob-tracking fields**
  (`p_things.cpp:614-618`), not whether those fields get *reset*. Concretely: calling this with
  `add=false, setbob=false` on a player still zeroes `player->velx`/`vely` (killing their current
  view-bob amplitude) even though the new velocity you're setting is never added into those
  fields — the player's `mo->velx`/`vely` (actual motion) and `player->velx`/`vely` (bob-only,
  feeds `player->bob` via `DMulScale16` at `p_user.cpp:2861`) diverge in that specific
  combination. The wiki's "if true, the speed adjustment influences bobbing" phrasing is correct
  as far as it goes but doesn't mention this replace-mode-always-zeroes-bob interaction. For a
  non-player actor, `setbob` has no effect at all (guarded on `actor->player != NULL`).
- **Return value is dead — always `0`/`false`.** The `case ACSF_SetActorVelocity:` block
  unconditionally `return 0;` after the iterator loop (`p_acs.cpp:6118`), regardless of whether
  `tid` resolved to any actor at all. Despite the declared `bool` return type (and the wiki not
  documenting a return value at all), there is no way to detect from the return value whether
  anything was actually affected.
- **Zandronum-only netcode, absent from the wiki:** every affected actor triggers
  `SERVER_UpdateThingVelocity(actor, true)` (`p_things.cpp:620`, `updateXY` defaults to `true`),
  which is a no-op on a client/singleplayer (`NETWORK_GetState() != NETSTATE_SERVER` early-outs)
  but on a server replicates via `SERVERCOMMANDS_MoveThingExact`. For a **non-player** actor this
  also force-syncs its X/Y/Z **position**, not just velocity (`sv_main.cpp:5578-5583`, `if
  (!pActor->player)` adds the position bits) — a deliberate workaround for velocity-only sync
  drift noted in-line ("there are sync issues, if we don't also update the actual position").
  For a **player** actor, only the velocity bits are sent; position is deliberately left alone
  since `SERVERCOMMANDS_MovePlayer` already handles it elsewhere and forcing position here would
  fight client-side prediction.

**Example — launch an actor at a fixed 3D velocity, replacing its current motion:**

```
SetActorVelocity(tid, FixedMul(cos(angle), speed), FixedMul(sin(angle), speed), 0, false, false);
```

**Provenance:** wiki page `SetActorVelocity - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`oldid=33146`) + source-verified against `p_acs.cpp:6104-6118`, `p_things.cpp:602-622`,
`sv_main.cpp:5563-5586`, `p_user.cpp:2805-2861`. The wiki's `tid`/`velx`/`vely`/`velz`/`add`
description checks out; its `setbob` description is correct but incomplete (doesn't mention the
replace-mode bob-zeroing interaction above), and it says nothing about the always-`0` return
value or the Zandronum server-side netcode/position-sync behavior — all source-verified additions
in this file. **Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD —
see "Engine scope" in `../../shared/AUTHORING.md`). **Tier:** A.
