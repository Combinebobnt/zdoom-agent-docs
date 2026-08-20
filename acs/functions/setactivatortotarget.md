# `bool SetActivatorToTarget(int tid)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** ZDoom Wiki, "SetActivatorToTarget" (`https://zdoom.org/w/index.php?title=SetActivatorToTarget&oldid=35899`), processed 2026-07-29.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function.

Changes the current script's activator, for the remainder of the executing script, to the
"target" of the actor found by `tid`. Extension function (`ACSF_SetActivatorToTarget`, index
`-13` in the zt-bcc source's `lib/zcommon.bcs:1641`), implementation in
the Zandronum source's `src/p_acs.cpp:5963-5982`.

## Resolution logic

- `tid` — TID of the actor whose "target" becomes the new activator. **`0` means "the current
  activator"** (`SingleActorFromTID`, `p_acs.cpp:4445`: `if (tid == 0) return defactor;`, where
  `defactor` is passed in as the activator) — same zero-means-activator convention as other
  actor-targeting builtins in this engine.
- Actual switch case (`p_acs.cpp:5963-5982`):
  1. Resolve `actor` from `tid` (or the current activator if `tid == 0`). **If no actor is found
     at all, return `0` immediately and leave the activator untouched.**
  2. If `actor` is a **live player** (`actor->player != NULL && actor->player->playerstate ==
     PST_LIVE`), overwrite `actor` with the result of `P_BulletSlope(actor, &actor)`
     (`p_pspr.cpp:1290-1324`) — i.e. whatever the player's autoaim cone hits within `16*64` map
     units, or `NULL` if the aim aiming at nothing/nothing in range.
  3. Otherwise (monster, corpse, projectile, non-live player, any other actor), overwrite `actor`
     with `actor->target`.
  4. If the resulting `actor` is non-`NULL`, the activator is set to it and the function returns
     `1`/true. **If it's `NULL`, the function returns `0` and the current activator is left
     completely unchanged** — it does *not* fall back to the originally-resolved actor.

- What `->target` actually holds by the time step 3 reads it (this is why the wiki's bullet list
  of "monster / dead actor / projectile" cases all reduce to the same one field access):
  - **Living monster:** whatever it's currently attacking/chasing.
  - **Missile/projectile:** the shooter, set when the projectile spawns (standard Doom-engine
    missile convention — projectiles use `target` to mean "owner", not "what I'm chasing").
  - **An actor that has died:** `target` gets overwritten to its **killer** in `AActor::Die`
    (`p_interaction.cpp:496-500`: `// [RH] Set the target to the thing that killed it. Strife
    apparently does this. if (source != NULL) target = source;`) — so reading a corpse's `target`
    after death gives you the killer, not whatever it was fighting when it died.

## Engine-family divergence: Zandronum added a wider live-player autoaim cone

Step 2 above (the live-player branch) calls through to a shared autoaim helper, and that helper's
own internals differ meaningfully between the two engines, changing whether this function actually
finds a target for a live-player activator at an oblique angle:

- **Angle sweep width.** Both engines' autoaim helpers skip the multi-angle sweep entirely and
  only ever try one dead-center trace whenever the aiming player has freelook allowed on the
  current level *and* their own autoaim-distance setting is at or below half a degree (i.e.
  autoaim effectively off) — a very common modern client configuration. Outside that case (autoaim
  meaningfully nonzero, or freelook disallowed), the two engines differ: UZDoom's helper is the
  stock ZDoom-family behavior and always tries exactly three fixed candidates — dead center and
  ±5.625° — with no way to widen it. Zandronum's helper adds a much finer sweep of up to fifteen
  candidate angles (dead center, a run of small steps out to roughly ±5° in each direction, plus
  the same two ±5.625° checks UZDoom has), used by default unless a server operator explicitly
  turns on a compat flag that narrows it back down to UZDoom's three-angle behavior. Practically:
  when the sweep actually runs (autoaim on, freelook off, or similar), a live player standing close
  to but not precisely facing a valid target is more likely to have that target picked up by
  `SetActivatorToTarget` on Zandronum's default settings than on UZDoom, where only the same three
  fixed offsets are ever tried.
- **Linked-portal restriction.** UZDoom's call site passes an "aim restricted through linked
  portals" flag into the shared helper (relevant only on maps using its line-portal system), a
  concept Zandronum's older two-argument version of the same helper has no equivalent for at all.
  This has no practical effect on maps that don't use linked line portals.
- **Netcode lag compensation.** Zandronum's autoaim helper wraps its aim check in client-position
  reconciliation ("unlagged") bookkeeping so a live-player autoaim result accounts for network
  latency in multiplayer; UZDoom's equivalent helper has no analogous mechanism, consistent with
  it being coop/single-player-focused rather than a competitive-multiplayer-oriented fork.

None of this affects the non-player branch (step 3, reading `->target` directly) or the
core resolution/return-value contract described above and below — both of those are identical
between the two engines.

## Wiki/engine divergence: "no target" does *not* fall back to the actor itself

The wiki's final bullet claims: *"If the actor has no target, the activator is the actor
itself."* **This is not what the Zandronum engine's code does.** Re-reading `p_acs.cpp:5963-5982`:
when the resolved `actor->target` (or, for a live player, the autoaim result) comes back `NULL`,
execution falls straight through the `if (actor != NULL)` guard to `return 0` — `activator` is
never assigned the original targetless actor as a fallback. The net effect is that the activator
that was active *before* the call remains active; the function does not "pin" it to the actor you
asked about. Anything written against the wiki's stated fallback (e.g. assuming a targetless
monster still becomes the new activator) will silently keep operating on the old activator
instead. Always check the boolean return value rather than assuming a fallback.

The UZDoom engine's `ACSF_SetActivatorToTarget` case (`src/playsim/p_acs.cpp:5459-5480`) has the
identical shape — the same nested non-null guard, with no fallback-to-self branch — so this same
divergence from the wiki's stated behavior holds on UZDoom too, not just on Zandronum.

## Return value

`true` (`1`) if a new activator was found and assigned; `false` (`0`) if `tid` resolved to no
actor, or the resolved actor/aim had no target — in both `0` cases the activator is left exactly
as it was before the call.

## See also

- `SetActivator` (`p_acs.cpp:5952-5961`, index `-12`) — sets the activator directly to the actor
  found by `tid` (optionally through an `AAPTR_*` pointer conversion), with no target-chasing
  step at all.
