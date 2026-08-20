# `void LineAttack(int tid, fixed angle, fixed pitch, int damage [, str pufftype [, str damagetype [, fixed range [, int flags [, int pufftid]]]]])`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** Wiki page `LineAttack (ACS) - ZDoom Wiki.html` (ZDoom wiki, `https://zdoom.org/w/index.php?title=LineAttack_%28ACS%29&oldid=53708`, retrieved 2026-07-29). The wiki page does **not** document the angle/pitch encoding or state that they are fractions-of-turn, but the actual implementation matches the wiki in all tested details. Verified against the Zandronum source's `src/p_acs.cpp:6435-6475`, `p_map.cpp:4188-4556`, `p_local.h:30`, `p_local.h:499-506`, and `zt-bcc/lib/zcommon.bcs:1688, 1057-1058`. **Fork divergences found**: (1) `LineAttack(0, ...)` from a script with no activator crashes (unguarded NULL dereference), unlike the similar-looking `SetActorAngle(0, ...)` which silently no-ops; (2) `pufftid` is silently dropped (never assigned, no error) whenever the hit doesn't produce a persistent puff — most notably the default case of hitting a normal, bleeding actor with a puff class that lacks `MF3_PUFFONACTORS`. Both are documented above.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function.

Fires a hitscan attack (raycast). Extension function, index `-60` in `zcommon.bcs` (`case ACSF_LineAttack:` at the Zandronum source's `src/p_acs.cpp:6435-6475`).

## Parameters

- `tid` — TID of the actor(s) to fire from. **`0` means "the activator,"** applied directly without NULL guard — **`LineAttack(0, ...)` from a script with no activator (e.g. `CLIENTSIDE` or `UNLOADING`) crashes the engine** (immediate NULL dereference in `P_LineAttack` at `p_map.cpp:4231`, `t1->z`). This is a fatal difference from `SetActorAngle(0, ...)`, which guards against activator-less scripts. **Nonzero `tid` fans out** via `FActorIterator` — fires one complete hitscan attack **per actor sharing the TID**; see the shared-TID pattern (a single TID deliberately reused across many actors, e.g. an entire spawned group) noted elsewhere in this tree. Every *persistent* spawned puff receives the same `pufftid` assignment — but not every hit spawns a persistent puff; see the `pufftid` entry below for when it's silently dropped instead.

- `angle` — **fixed-point fraction of a full turn** (`0.0`–`1.0`, same encoding as `SetActorAngle`/`Sin`/`Cos`) — **the wiki does not state the unit and does not document the encoding**, which is a gap. The raw ACS 16.16 fixed value is shifted left by `ANGLETOFINESHIFT` (16 bits) to index engine sine/cosine lookup tables for the full-turn angle space. North = `0.25`, East = `0.0`, South = `0.75`, West = `0.5`.

- `pitch` — **fixed-point fraction of a full turn** (same encoding as `angle`) — **also undocumented unit in the wiki.** Shifted right by `ANGLETOFINESHIFT` to index sine/cosine tables (`p_map.cpp:4222, 4226`). **Positive pitch aims downward** (`vz = -finesine[pitch]`, `p_map.cpp:4226`).

- `damage` — damage dealt to the target hit by the hitscan.

- `pufftype` — name of the puff actor class to spawn. Default: `"BulletPuff"` (applied when unspecified or when string handle is 0, `p_acs.cpp:6440`).

- `damagetype` — damage type name passed to the engine's damage system. Default: `"None"` (applied when unspecified or handle is 0, `p_acs.cpp:6441`).

- `range` — **maximum hitscan distance in map units (fixed-point).** Default: `2048.0` (= `MISSILERANGE`, `p_local.h:30` = `32*64*FRACUNIT`). **Caveat: passing an explicit `0` is indistinguishable from omission** (`argCount > 6 && args[6]` check at `p_acs.cpp:6442` treats 0-argument and omitted-argument identically), so an explicit `0` silently becomes `2048.0`, not a "no range limit." If you need no range limit, pass a large fixed value like `999999.0`.

- `flags` — bitwise-OR combination of the following. Default: `0`.
  - `FHF_NORANDOMPUFFZ` (`0x1`) — disable the random Z offset applied to spawned puff (maps to engine `LAF_NORANDOMPUFFZ`, `p_acs.cpp:6447`).
  - `FHF_NOIMPACTDECAL` (`0x2`) — disable decal generation from the impact (maps to engine `LAF_NOIMPACTDECAL`, `p_acs.cpp:6448`).
  Both constants are defined in `zcommon.bcs:1057-1058`.

- `pufftid` — TID to assign to the spawned puff actor (0 = no assignment). Default: `0`. **Assignment is guarded** (`if (puff != NULL && pufftid != 0)`, `p_acs.cpp:6453, 6467`) — a NULL puff return does not crash. Puff is added to the TID hash immediately (`puff->AddToHash()`, `p_acs.cpp:6456, 6470`).

  **`pufftid` is silently dropped in the single most common hitscan outcome: hitting a normal actor that bleeds.** `P_LineAttack` (`p_map.cpp:4188-4556`) only returns a *persistent* puff — one `pufftid` can actually attach to — when hitting a wall/floor, hitting nothing (`MF3_ALWAYSPUFF` puff types only), or hitting an actor that is `MF_NOBLOOD`/`MF2_INVULNERABLE`/`MF2_DORMANT`, or whose puff class itself sets `MF3_PUFFONACTORS` (`p_map.cpp:4425-4435`). For the default case — a normal actor that bleeds, hit by a puff class without `MF3_PUFFONACTORS` (i.e. the default `BulletPuff`) — no visible puff is spawned at all going into the damage step; instead a **temporary** puff is spawned purely to serve as the `P_DamageMobj` inflictor (`puff = P_SpawnPuff(..., PF_TEMPORARY, ...); killPuff = true;`, `p_map.cpp:4464-4472`), and that temporary puff is `Destroy()`ed and the local `puff` pointer reset to `NULL` before the function returns (`p_map.cpp:4546-4554`). `ACSF_LineAttack` in `p_acs.cpp` only assigns `pufftid` to whatever pointer `P_LineAttack` returns — so on this path it receives `NULL` and the `if (puff != NULL && ...)` guard means `pufftid` is never applied, with no error or warning. A script that expects to find/manipulate the puff afterward via `pufftid` will find nothing on this path, and get a real, usable actor on every other path — the same call site behaves differently depending on the target actor's flags and the puff class's own flags, not on anything the caller passed.

## Network note

The fork adds no ACS-level client synchronization for this function. Hitscan attacks inherently client-predict on both server and clients per the engine's netcode; this function has no `[AK]`-tagged server-sync code like `ACSF_PlaySound` does immediately below it in the source. The client-side decal/puff behavior is engine-level, not ACS-specific.

## Engine-family divergence: ZScript event handler can silently cancel the attack

UZDoom's `P_LineAttack` (the UZDoom source's `src/playsim/p_map.cpp`) opens with a call to
`t1->Level->localEventManager->WorldHitscanPreFired(t1, angle, distance, pitch, damage, damageType, pufftype, flags, sz, offsetforward, offsetside)`
and returns `nullptr` immediately, before doing any tracing, damage, or puff spawning, if that
call returns true. This routes through UZDoom's ZScript `EventHandler` system: any loaded mod can
override `WorldHitscanPreFired` and veto the hitscan outright. Zandronum has no ZScript event-handler
system and no equivalent call — its `P_LineAttack` always performs the attack. From the calling ACS
script's point of view this is invisible either way (`LineAttack` has no return value to check), but
on UZDoom a mod's event handler can make the call a silent no-op — no damage, no puff, no decal —
in a way that has no counterpart on Zandronum.

Aside from this addition, the rest of `ACSF_LineAttack`'s behavior — the unguarded NULL dereference
when `tid` is `0` and there is no activator, the angle/pitch fraction-of-turn encoding (translated via
`DAngle::fromQ16`, which resolves to the same fraction-of-a-full-turn semantics), positive pitch aiming
downward, the `range`-argument-0-treated-as-omitted caveat, the `2048.0` (`MISSILERANGE`) default range,
the `"BulletPuff"`/`"None"` defaults, the guarded `pufftid` assignment, and the silent `pufftid` drop when
hitting a normal bleeding actor with a puff class lacking `MF3_PUFFONACTORS` — all agree with the
Zandronum-verified description above (the UZDoom source's `src/playsim/p_acs.cpp:5958-5997` and
`src/playsim/p_map.cpp:4648-4978`).
