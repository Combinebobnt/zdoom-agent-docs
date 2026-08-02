# Actor pointer selectors (`AAPTR_*`) in ACS/BCS

In ACS/BCS there is no pointer *type* and no `target`/`master`/`tracer` field access syntax like
DECORATE or ZScript have. Instead, an actor relationship is always resolved at call time by
passing an `AAPTR_*` selector constant into one of a handful of extension functions
(`SetPointer`, `SetActivator`, `SetActivatorToTarget`, `SetActivatorToPlayer`,
`IsPointerEqual` — see [IsPointerEqual](../functions/ispointerequal.md)); none of the wiki's
ZScript-side material (`self`/`owner`/`invoker`, class-scoped pointer variables, casting with
`let`/`SpecificClass(...)`) applies here — **this fork has no ZScript at all**, matching the
"no ZScript" note already recorded in [Activation](activation.md).

## Resolution mechanism: `COPY_AAPTR`

Every `AAPTR_*` selector passed from ACS is resolved server-side by a single C++ function,
`COPY_AAPTR(AActor *origin, int selector)` (`actorptrselect.cpp`), not by a per-function switch —
so its priority order applies uniformly to every ACS function that takes a selector:

1. **Damage-event selectors** (`AAPTR_DAMAGE_SOURCE`/`AAPTR_DAMAGE_INFLICTOR`/`AAPTR_DAMAGE_TARGET`)
   are checked *first*, independent of `origin`, but only inside a currently-running ACS script
   (`ACS_IsCalledFromScript()`) — see "Damage-event pointers" below.
2. If `origin` is a player, a player-specific selector (`AAPTR_PLAYER_GETTARGET`,
   `AAPTR_PLAYER_GETCONVERSATION`, or the ZScript-only `AAPTR_PLAYER_GETFLOATYICON`/
   `AAPTR_PLAYER_GETCAMERA` — not usable from ACS, see "Not reachable from ACS/BCS" below) wins.
3. Else a general selector (`AAPTR_TARGET`/`AAPTR_MASTER`/`AAPTR_TRACER`/`AAPTR_FRIENDPLAYER`)
   applies if `origin` is non-null.
4. Else a static selector (`AAPTR_PLAYER1`-`AAPTR_PLAYER8`/`AAPTR_NULL`) applies unconditionally.
5. If none of the above matched, `origin` itself is returned unchanged — **this is the fallback
   for any selector value `COPY_AAPTR` doesn't recognize at all**, not just for `AAPTR_DEFAULT`.

Selectors can be bitwise-OR'd (e.g. `AAPTR_TARGET|AAPTR_PLAYER_GETTARGET`, the wiki's documented
pattern for "get the target, or the player's aim-target if the origin is a player") because each
priority tier masks the selector against its own bitmask (`selector & AAPTR_GENERAL_SELECTORS`,
etc.) before switching on it — combining selectors from *different* tiers is meaningful, combining
two from the *same* tier is not (only one can win per tier).

## `AAPTR_GET_LINETARGET` is a trap in ACS/BCS

`zcommon.bcs` declares `AAPTR_GET_LINETARGET = 0x8000` and it compiles fine in any function call
that takes an `int` selector — but `COPY_AAPTR` has **no case for it in any of the three
switches** (general/player/static). Passed alone, it falls through every tier and hits the step-5
fallback, silently returning `origin` unchanged instead of "the actor being aimed at." The wiki's
own DECORATE/ACS table already hints at this by listing the ZScript analog as "None — see
`AimTarget`," but doesn't say the ACS constant is dead weight if actually used; this is Zandronum
`3.2.1`-verified, not a wiki-vs-fork gap. If you need line-of-sight targeting from ACS, there is no
`AAPTR_GET_LINETARGET`-based path — combine `AAPTR_PLAYER_GETTARGET` (works for a player origin,
via `P_BulletSlope`) with your own aim-trace extension function for non-player origins.

## Not reachable from ACS/BCS

`AAPTR_PLAYER_GETFLOATYICON` exists in `actorptrselect.h` but has **no corresponding constant in
`zt-bcc/lib/zcommon.bcs`** — there is no BCS name for it, and no way to pass its raw value
(`0x4000000`) usefully since nothing in BCS names it. It's usable only from
DECORATE/ZScript action-function code, not from ACS. `AAPTR_PLAYER_GETCAMERA` (`0x8000000`), by
contrast, **is** exposed in `zcommon.bcs` and works from ACS.

## Damage-event pointers (Zandronum-only, not in the ZDoom wiki page)

`AAPTR_DAMAGE_SOURCE`/`AAPTR_DAMAGE_INFLICTOR`/`AAPTR_DAMAGE_TARGET` are a Zandronum-native
addition absent from the ZDoom wiki page entirely (added for the `GAMEEVENT_ACTOR_DAMAGED` EVENT
script type — see [EVENT scripts](event-scripts.md) for how that script type itself is gated).
`COPY_AAPTR` special-cases them before anything else: if the selector matches one of the three and
`ACS_IsCalledFromScript()` is true, it returns `ACS_GetScriptDamagePointers(selector)`, which reads
`g_pCurrentScript->pDamageSource`/`pDamageInflictor`/`pDamageTarget` — fields only populated on the
script instance actually running as the `GAMEEVENT_ACTOR_DAMAGED` handler. Calling with one of
these selectors from any other script (or from a damage-event script after control has passed to
a called function whose `g_pCurrentScript` differs) silently returns `NULL`, same as an unresolved
TID — there's no error, just a quiet no-op. Git ancestry check: the introducing commit
(`2a12c5931`, plus the two later `AAPTR_PLAYER_GETFLOATYICON`/`AAPTR_PLAYER_GETCAMERA` additions,
`756e6e5f4`/`9b65e2ddc`) are all ancestors of `28f736fb3` (the 3.2.1 version-bump commit), so this
whole selector set is present in the 3.2.1 target, not a `3.3-alpha`-only feature.

## `AAPTR_MASTER`/`AAPTR_TARGET`/`AAPTR_TRACER` assignment loop guard

`SetPointer`'s underlying `ASSIGN_AAPTR` calls `VerifyTargetChain`/`VerifyMasterChain` after
writing `target`/`master` (not `tracer`, which has no loop guard at all) unless the caller passes
the `PTROP_UNSAFETARGET`/`PTROP_UNSAFEMASTER` flag bits — matching the wiki's "prevention may
involve... setting the pointer to NULL," but concretely: a chain that would create a target/master
cycle gets silently reset to `NULL` on the *assigning* actor, not rejected with an error, and only
for those two fields.

**Provenance:** wiki page `Actor pointer - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`oldid=54704`) + source-verified against the Zandronum source's `src/actorptrselect.h`/`.cpp`
(`COPY_AAPTR`, `ASSIGN_AAPTR`, `AAPTR` enum), `p_acs.cpp` (`ACSF_SetPointer` ~5938,
`ACSF_SetActivator` ~5952, `ACSF_SetActivatorToTarget` ~5963, `ACSF_IsPointerEqual` ~6916,
`ACSF_SetActivatorToPlayer` ~7504, `ACS_GetScriptDamagePointers` ~13729), and
`zt-bcc/lib/zcommon.bcs:757-774,1276-1278` (`AAPTR_*` constant availability). Git ancestry for the
damage-pointer/floaty-icon/camera additions checked against `28f736fb3` (3.2.1 version-bump
commit) via `git merge-base --is-ancestor`. **Engine:** Zandronum 3.2.1. **Tier:** A.
