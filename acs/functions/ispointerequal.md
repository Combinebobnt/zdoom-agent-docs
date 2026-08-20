# `bool IsPointerEqual(int ptr_select1, int ptr_select2 [, int tid1 [, int tid2]])`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-28)
**Provenance:** wiki page `IsPointerEqual - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-28,
`https://zdoom.org/w/index.php?title=IsPointerEqual&oldid=54021`) + source-verified against `p_acs.cpp:6916-6930` (`ACSF_IsPointerEqual` case) and
`p_acs.cpp:4445-4456` (`SingleActorFromTID`), `zt-bcc/lib/zcommon.bcs:1713` (index `-84`) and
`:757-...` (`AAPTR_*` constants).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (negative index → `ACSF_IsPointerEqual` in `p_acs.cpp`).

Compares two resolved actor pointers for identity (same actor or not). Extension function
(`ACSF_IsPointerEqual`, index `-84` in the zt-bcc source's `lib/zcommon.bcs:1713`), implementation in
`p_acs.cpp:6916-6930`.

- `ptr_select1`/`ptr_select2` — `AAPTR_*` pointer-selector constants (`AAPTR_DEFAULT`,
  `AAPTR_TARGET`, `AAPTR_PLAYER1`, etc., named in `zt-bcc/lib/zcommon.bcs:757-...`), resolved via
  `COPY_AAPTR` — the same selector mechanism used elsewhere in the engine (e.g.
  `A_SetPointer`/`SetActivator`), not a raw TID.
- `tid1`/`tid2` — determine *which actor* each `ptr_select` is resolved relative to, via
  `SingleActorFromTID(tid, activator)` (`p_acs.cpp:4445-4456`). **`0` means "the activator"**
  (`if (tid == 0) return defactor;`) — matches the wiki, and both default to `0` when omitted
  (`p_acs.cpp:6918-6923`, fall-through `switch (argCount)` populating `tid1`/`tid2` only if
  supplied). **If `tid1 == tid2`, the second lookup is skipped and the same resolved actor is
  reused for both** (`p_acs.cpp:6926`: `tid2 == tid1 ? actor : SingleActorFromTID(tid2, activator)`)
  — an optimization, not a behavior difference, but relevant if a TID's `FActorIterator` could
  otherwise return different actors across two separate calls for a duplicated TID.
- Return value: `COPY_AAPTR(actor, ptr_select1) == COPY_AAPTR(actor2, ptr_select2)` — a raw
  pointer-equality check on the two resolved `AActor*` results, coerced to ACS `bool`
  (1/0). If either `tid` fails to resolve to an actor, `SingleActorFromTID` returns `NULL`, and
  `COPY_AAPTR(NULL, ...)` is used in the comparison rather than erroring — a `NULL == NULL` case
  (both sides unresolved) evaluates true, same as vanilla ZDoom.

No wiki/fork divergence found: this extension function exists in the Zandronum engine fork exactly
as the wiki describes, including the tid-defaults-to-activator convention and the ACS-only
`tid1`/`tid2` overload (the wiki's DECORATE/ZScript-only 2-argument form doesn't apply to ACS/BCS
and isn't covered further here, since only the ACS version is in scope).

**Example — check if the imp's target was player 1 at time of death** (from the wiki, still valid
for ACS with the caller resolved via `tid` instead of "the DECORATE caller"):

```text
if (IsPointerEqual(AAPTR_TARGET, AAPTR_PLAYER1, tid) == TRUE)
{
    Log(s: "Killed by player 1");
}
```

## Engine-family divergence: client-side pointer/TID resolution

UZDoom's `ACSF_IsPointerEqual` (`src/playsim/p_acs.cpp:6427-6442`) is functionally identical to
Zandronum's for the common case, but both TID lookups and the pointer-selector resolution are
routed through a per-script `bClientSide` flag: `Level->SingleActorFromTID(tid, bClientSide,
activator)` (`g_levellocals.h:342-345`, still `tid == 0 ? defactor : ...`) picks between the normal
server-side TID hash and a separate client-side TID hash, and the equality check itself uses
`COPY_AAPTREX(Level, actor, ptr_select, clientSideState)` rather than plain `COPY_AAPTR`. This
supports UZDoom/GZDoom-family client-side ACS (e.g. `CLIENTSIDE` scripts predicting locally), which
has no equivalent in Zandronum's implementation — Zandronum's `SingleActorFromTID`/`COPY_AAPTR` only
ever resolve against the single server-side actor list. The tid-defaults-to-activator convention and
the `tid1 == tid2` reuse optimization are unchanged in both hash modes.
