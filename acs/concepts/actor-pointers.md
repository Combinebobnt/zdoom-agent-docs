# Actor pointer selectors (`AAPTR_*`) in ACS/BCS

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** wiki page `Actor pointer - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`https://zdoom.org/w/index.php?title=Actor_pointer&oldid=54704`) + source-verified against the Zandronum source's `src/actorptrselect.h`/`.cpp`
(`COPY_AAPTR`, `ASSIGN_AAPTR`, `AAPTR` enum), `p_acs.cpp` (`ACSF_SetPointer` ~5938,
`ACSF_SetActivator` ~5952, `ACSF_SetActivatorToTarget` ~5963, `ACSF_IsPointerEqual` ~6916,
`ACSF_SetActivatorToPlayer` ~7504, `ACS_GetScriptDamagePointers` ~13729), and
`zt-bcc/lib/zcommon.bcs:757-774,1276-1278` (`AAPTR_*` constant availability). Git ancestry for the
damage-pointer/floaty-icon/camera additions checked against `28f736fb3` (3.2.1 version-bump
commit) via `git merge-base --is-ancestor`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

In ACS/BCS there is no pointer *type* and no `target`/`master`/`tracer` field access syntax like
DECORATE or ZScript have. Instead, an actor relationship is always resolved at call time by
passing an `AAPTR_*` selector constant into one of a handful of extension functions
(`SetPointer`, `SetActivator`, `SetActivatorToTarget`, `SetActivatorToPlayer`,
`IsPointerEqual` — see [IsPointerEqual](../functions/ispointerequal.md)); none of the wiki's
ZScript-side material (`self`/`owner`/`invoker`, class-scoped pointer variables, casting with
`let`/`SpecificClass(...)`) applies to ACS/BCS code on either engine — **the Zandronum engine fork
has no ZScript at all**, matching the "no ZScript" note already recorded in
[Activation](activation.md), and on UZDoom, where ZScript does exist, it is a separate language
that ACS still has no pointer-field access syntax through.

## Resolution mechanism: `COPY_AAPTR`

Every `AAPTR_*` selector passed from ACS is resolved server-side by a single C++ function,
`COPY_AAPTR(AActor *origin, int selector)` (`actorptrselect.cpp`), not by a per-function switch —
so its priority order applies uniformly to every ACS function that takes a selector:

1. **Damage-event selectors** (`AAPTR_DAMAGE_SOURCE`/`AAPTR_DAMAGE_INFLICTOR`/`AAPTR_DAMAGE_TARGET`)
   are checked *first*, independent of `origin`, but only inside a currently-running ACS script
   (`ACS_IsCalledFromScript()`) — see "Damage-event pointers" below.
2. If `origin` is a player, a player-specific selector (`AAPTR_PLAYER_GETTARGET`,
   `AAPTR_PLAYER_GETCONVERSATION`, `AAPTR_PLAYER_GETCAMERA` — all named in `zcommon.bcs` — or
   `AAPTR_PLAYER_GETFLOATYICON`, reachable from ACS too but only via a raw literal, see below) wins.
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

## No BCS constant, but still callable from ACS/BCS with a raw literal

`AAPTR_PLAYER_GETFLOATYICON` exists in `actorptrselect.h` but has **no corresponding constant in
`zt-bcc/lib/zcommon.bcs`** — there is no BCS name for it. That does *not* make it unreachable from
ACS, though: `SetPointer`/`SetActivator`/`IsPointerEqual` all take the selector as a plain `int`
parameter (`zcommon.bcs`'s `-38:SetPointer(int,int;int,int):bool` and similar), so a raw literal
`0x4000000` (or a script-defined `enum`/`#define` wrapping it) reaches Zandronum's `COPY_AAPTR`
exactly like any named selector — `COPY_AAPTR` has no way to distinguish an ACS-originated call
from a DECORATE-originated one in the first place; Zandronum has exactly one `COPY_AAPTR` entry
point, with no caller-origin parameter. The real limitation is narrower than "not usable from ACS":
it's "the wiki's own name for it, and zt-bcc's compiler-level convenience of a named constant,
aren't available — write the raw hex value yourself." `AAPTR_PLAYER_GETCAMERA` (`0x8000000`), by
contrast, **is** exposed in `zcommon.bcs` under a real name and works from ACS the ordinary way.

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

## Engine-family divergence

The core resolution mechanism carries over intact: UZDoom's `COPY_AAPTREX`
(`src/playsim/actorptrselect.cpp`) implements the same general/player/static selector tiers, and
`SetPointer`, `SetActivator`, `SetActivatorToTarget`, and `IsPointerEqual` are all present and
bound to the same ACSF names as on Zandronum. Ordinary `AAPTR_TARGET`/`AAPTR_MASTER`/
`AAPTR_TRACER`/`AAPTR_PLAYER1`-`8`/etc. usage from ACS/BCS behaves the same on both engines,
subject to the client-side filter described below.

One structural note first, because two of the differences below depend on it: UZDoom splits the
resolver in two. `COPY_AAPTREX(Level, origin, selector, clientSide)` is the real implementation and
is what **every** ACS call site uses, passing the running script's own client-side flag;
`COPY_AAPTR(origin, selector)` is a thin wrapper that DECORATE/ZScript action functions use, which
passes `CSPTR_IGNORE` (disabling the filter) and additionally returns `NULL` outright when `origin`
is `NULL` — so the "static selectors apply even with a null origin" step holds on the ACS path but
not on the DECORATE/ZScript one. Zandronum has only the single `COPY_AAPTR` and no client-side
parameter at all.

Several specifics documented above don't, though:

- **The Zandronum-native damage-event pointers are entirely absent from UZDoom.**
  `AAPTR_DAMAGE_SOURCE`/`_INFLICTOR`/`_TARGET` have no matching enumerator or `case` anywhere in
  UZDoom's `actorptrselect.h`/`.cpp` — there's no `GAMEEVENT_ACTOR_DAMAGED` EVENT-script mechanism
  on UZDoom for them to have been built for in the first place (see
  [EVENT scripts](event-scripts.md)'s own divergence section). A call using one of these selectors
  falls through UZDoom's `COPY_AAPTREX` the same way any unrecognized selector value does.
- **`SetActivatorToPlayer` is Zandronum-only.** It's bound in Zandronum's reserved 100-199 ACSF
  range and confirmed absent from UZDoom's own ACSF table; a Zandronum-compiled call to it silently
  returns 0 on UZDoom rather than assigning the activator.
- **`AAPTR_PLAYER_GETCAMERA`, which this file documents as working from ACS on Zandronum, is dead
  weight on UZDoom instead.** UZDoom's `actorptrselect.h` has no enumerator or `case` for it at
  all — passed from a call built against `zcommon.bcs`'s constant, it falls through every tier of
  UZDoom's `COPY_AAPTREX` unmatched, silently returning `origin` unchanged. This is the mirror image
  of the `AAPTR_PLAYER_GETFLOATYICON` case this file already documents as reachable from ACS on
  Zandronum only via a raw literal, for a different reason (no BCS constant at all, rather than an
  engine-side gap). `AAPTR_PLAYER_GETFLOATYICON` is missing from UZDoom's enumerator list as well, so on UZDoom both
  of these Zandronum player-tier additions are absent engine-side, not just unnamed in BCS.
- **`AAPTR_GET_LINETARGET` inverts the other way: it's a real, working selector on UZDoom, not the
  dead "trap" this file documents on Zandronum.** UZDoom's `COPY_AAPTREX` implements a genuine
  `case` for it in the general-selector tier, resolving it via the same aim-trace (`P_BulletSlope`,
  portal-restricted) used for `AAPTR_PLAYER_GETTARGET` — and, unlike `AAPTR_PLAYER_GETTARGET`, it
  works for a non-player origin too, since it sits in the general tier rather than the player tier.
  A script that correctly avoids `AAPTR_GET_LINETARGET` on Zandronum as useless would be leaving
  working aim-target resolution on the table if ported to UZDoom unchanged.

  **The bitmask membership changed with it, and that inverts an OR-combination in the dangerous
  direction.** UZDoom includes `AAPTR_GET_LINETARGET` in its `AAPTR_GENERAL_SELECTORS` mask;
  Zandronum's mask omits the bit entirely. So `AAPTR_TARGET|AAPTR_GET_LINETARGET` masks down to
  plain `AAPTR_TARGET` on Zandronum (the unknown bit is simply discarded) and returns the target as
  intended — but on UZDoom the same value survives masking, matches **no** `case` in the general
  tier, matches nothing in the static tier either, and falls through to the step-5 `origin`
  fallback. Working Zandronum code that OR-combines `AAPTR_GET_LINETARGET` with any other general
  selector therefore silently returns the origin actor on UZDoom instead. Only combine selectors
  drawn from *different* tiers; on UZDoom `AAPTR_GET_LINETARGET` is no longer a free bit to set
  alongside `AAPTR_TARGET`/`AAPTR_MASTER`/`AAPTR_TRACER`/`AAPTR_FRIENDPLAYER`.

- **UZDoom filters resolved pointers across the client-side barrier; Zandronum has no equivalent.**
  Because every ACS call site goes through `COPY_AAPTREX` with a real `EPTRClientSideState` (never
  `CSPTR_IGNORE`), UZDoom applies a check that has no counterpart in Zandronum's resolver:
  - For `AAPTR_TARGET`/`AAPTR_MASTER`/`AAPTR_TRACER` **only**, a successfully resolved actor is
    discarded and `NULL` returned instead when that actor's own client-side-ness disagrees with the
    calling script's *and* it isn't the console player's own actor. A server-side script therefore
    cannot reach a client-side-only actor through target/master/tracer at all — it reads as an
    unresolved pointer, with no error.
  - When resolving *from* a client-side script, `AAPTR_PLAYER_GETTARGET`,
    `AAPTR_PLAYER_GETCONVERSATION` and `AAPTR_GET_LINETARGET` return `NULL` unconditionally, and
    `AAPTR_PLAYER1`-`8`/`AAPTR_FRIENDPLAYER` resolve only the console player's own actor (any other
    player number yields `NULL`).

  Caveat on the second half: in the UZDoom revision stamped above, the predicate deciding whether a script runs
  client-side is stubbed out to always report "not client-side" (with an in-source `TODO` saying it
  broke too many existing CLIENTSIDE scripts pending a dedicated flag), and it is the only input to
  that flag. So today every ACS script resolves pointers as server-side, and the live effect is the
  first bullet only. Don't rely on the second bullet's behavior being unreachable — it's a stub, not
  a design decision, and the surrounding machinery is fully wired.

- **`AAPTR_DEFAULT` is an explicit early-out on UZDoom, not a fall-through.** `COPY_AAPTREX` returns
  `origin` immediately when the selector is exactly `AAPTR_DEFAULT` (0), before any tier is
  consulted and before the client-side filter above can apply; Zandronum reaches the same answer
  only by falling off the end of all three switches. The returned value is identical either way, so
  this matters only when reasoning about the filter — a `AAPTR_DEFAULT` resolution is never filtered
  on UZDoom, whereas an `AAPTR_TARGET` resolution of the same actor can be.
