# `bool SetActivatorToTarget(int tid)`

**Tier:** A
**Engine:** Zandronum 3.2.1 (this is a long-standing ZDoom-lineage function, not a recent Zandronum-specific addition, so no 3.2.1-vs-3.3-alpha ancestry check was needed; verified directly against the Zandronum source's checkout).
**Provenance:** ZDoom Wiki, "SetActivatorToTarget" (`oldid=35899`), processed 2026-07-29.
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

## Wiki/fork divergence: "no target" does *not* fall back to the actor itself

The wiki's final bullet claims: *"If the actor has no target, the activator is the actor
itself."* **This is not what this fork's code does.** Re-reading `p_acs.cpp:5963-5982`: when the
resolved `actor->target` (or, for a live player, the autoaim result) comes back `NULL`, execution
falls straight through the `if (actor != NULL)` guard to `return 0` — `activator` is never
assigned the original targetless actor as a fallback. The net effect is that the activator that
was active *before* the call remains active; the function does not "pin" it to the actor you
asked about. Anything written against the wiki's stated fallback (e.g. assuming a targetless
monster still becomes the new activator) will silently keep operating on the old activator
instead. Always check the boolean return value rather than assuming a fallback.

## Return value

`true` (`1`) if a new activator was found and assigned; `false` (`0`) if `tid` resolved to no
actor, or the resolved actor/aim had no target — in both `0` cases the activator is left exactly
as it was before the call.

## See also

- `SetActivator` (`p_acs.cpp:5952-5961`, index `-12`) — sets the activator directly to the actor
  found by `tid` (optionally through an `AAPTR_*` pointer conversion), with no target-chasing
  step at all.
