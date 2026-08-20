# `int SetActorFlag(int tid, str flagname, bool value)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** wiki page `SetActorFlag - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29,
`https://zdoom.org/w/index.php?title=SetActorFlag&oldid=45141`) + source-verified against the Zandronum source `master` HEAD
(the Zandronum source's `src/p_acs.cpp:5357-5461,9059-9063`, `thingdef/thingdef.h:32`) and its git
history (`2e8aa53e6`, confirmed not an ancestor of `master`). Wiki describes real upstream ZDoom
behavior faithfully; the divergence is entirely on Zandronum's side (function never merged to
Zandronum `master` / the 3.2.1 target) and is recorded above rather than silently assumed to work.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (declared as one; has no actual implementation to point to).

**Implemented on UZDoom** (`case ACSF_SetActorFlag:` at `src/playsim/p_acs.cpp`): resolves the
target actor(s) by `tid` (0 meaning the activator, matching this doc's other UZDoom-only entries'
tid-0 convention), looks up the flag by name via the engine's `ModActorFlag` helper, and reports
the count of actors actually modified as its `int` return value — a real per-actor loop, not the
single-actor form the wiki's Zandronum-oriented phrasing might suggest.

**Compiles and links, but is dead in Zandronum's engine at every checked revision — including
the `master` HEAD that stands in for the 3.2.1 target.** Extension function, declared at
the zt-bcc source's `lib/zcommon.bcs:1833` (`-202:SetActorFlag(int,str,bool):int`), so `bcc` happily
accepts a call to it and emits `ACSF_SetActorFlag` (index 202) as the runtime call. But
the Zandronum source's `src/p_acs.cpp`'s `DLevelScript::CallFunction` — the function that dispatches
every `ACSF_*` index — has **no `case ACSF_SetActorFlag:`** anywhere in the switch, and no
`ACSF_SetActorFlag` enumerator exists in its `EACSFunctions` enum (`p_acs.cpp:5357` onward) at
all. The enum jumps straight from `ACSF_Warp = 92` to `ACSF_GetActorFloorTexture = 204`
(`p_acs.cpp:5461`, comment `// [BB] Out of order ZDoom backport.`), silently skipping indices
200–203 (`CheckClass`, `DamageActor`, `SetActorFlag`, `SetTranslation` in `zcommon.bcs`'s
numbering) entirely — they were never backported to this branch.

## What actually happens if you call it

`CallFunction`'s switch has a catch-all `default: break;` (`p_acs.cpp:9059-9060`) immediately
before the function's final `return 0;` (`p_acs.cpp:9063`). An index with no matching `case` —
which is exactly what `ACSF_SetActorFlag` (202) is here — falls straight through to that default
and the call **silently returns `0`**, doing nothing to any actor. No compiler error, no runtime
warning, no log line: it looks exactly like a successful call that "affected 0 actors," which is
indistinguishable from a real zero-actors-matched result. This is the same
declared-but-unimplemented-extension-function footgun as an out-of-range `GetActorProperty`
property (see `functions/getactorproperty.md`), just one level up — there the *property* lookup
misses, here the *function* itself was never wired in.

## Why zt-bcc declares it at all, and why it's not just a stale/aspirational entry

The wiki page this doc was built from describes real, working ZDoom behavior — `SetActorFlag`
does exist upstream, added to mainline ZDoom in 2016 mimicking DECORATE's `A_ChangeFlag`. It also
exists, verified in the Zandronum source's own git history, as commit `2e8aa53e6` ("Add
SetActorFlag ACS function", 2016-08-24) — but that commit lives only on
`origin/PredictionStuff`, `origin/clientserver`, `origin/g2.2`, and `origin/gz-zscript`, and
`git merge-base --is-ancestor 2e8aa53e6 HEAD` on the local checkout returns false: **it was never
merged into `master`**, which is the branch the 3.2.1 engine target uses and
this repo's docs are verified against. zt-bcc's compiler table apparently anticipated the
function landing (matching its would-be index, right after `ACSF_DamageActor = 201`), but on
`master`, it just isn't there. `master` also has no
string-flag-name overload of the internal `ModActorFlag` helper it would have needed
(the Zandronum source's `src/thingdef/thingdef.h:32` only declares `ModActorFlag(AActor*, FFlagDef*,
bool)`, not a string-name-lookup version) — confirming this isn't a case of the feature existing
under a different entry point, it's genuinely absent end-to-end.

**Practical consequence (Zandronum only — UZDoom just calls `SetActorFlag` directly, see above):**
there is no working way to set an arbitrary named actor flag from ACS on Zandronum. `CheckFlag`
(`ACSF_CheckFlag`, `-75` in `zcommon.bcs`, implemented at
`p_acs.cpp:6802-6810`) — the wiki's own "See also" link — **does** work as a read-only flag
query. `A_ChangeFlag` exists (the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:4609`) but is
a DECORATE action function, not callable from ACS. If a Zandronum script needs to flip a named
flag at runtime, the only real options are the verified DECORATE-side workaround below, one of the
specific dedicated setters Zandronum does implement (e.g. `ChangeActorAngle`/`ChangeActorPitch`),
or a boolean `APROP_*` via `SetActorProperty` for the flags that have a matching property, like
`APROP_AMBUSH`/`APROP_INVULNERABLE`/`APROP_FRIENDLY` — see `functions/getactorproperty.md`'s
property-type table for which flags have an `APROP_*` counterpart.

## Verified workaround (Zandronum only): `CustomInventory` + `A_ChangeFlag`, triggered via `GiveActorInventory`

The standard Zandronum-community fix, and it holds up against Zandronum's source: define a
DECORATE item whose base class is **`CustomInventory`** (not plain `Inventory`) with only a
`Pickup:` state block (no `Use:` state), and give it to the target actor from ACS with
`GiveActorInventory`/`GiveInventory`.

```text
ACTOR SetAmbushFlag : CustomInventory
{
    +INVENTORY.QUIET
    States
    {
    Pickup:
        TNT1 A 0 A_ChangeFlag("AMBUSH", true)
        Stop
    }
}
```
```text
GiveActorInventory(mons_tid, "SetAmbushFlag", 1);
```

Why this actually works, traced end to end against the Zandronum source's `src`:

- ACS's `GiveInventory`/`GiveActorInventory` spawns the item and calls
  `item->CallTryPickup(actor)` on the target (`p_acs.cpp:1274-1306`, `DoGiveInv`) — the give is not
  a raw inventory-array write, it goes through the same pickup path a real touch-pickup would.
- `AInventory::CallTryPickup` virtual-dispatches to `ACustomInventory::TryPickup`
  (`a_pickups.cpp:1682-1692` → `1833-1844`), which finds the `Pickup:` state and runs
  `CallStateChain(toucher, pickupstate)` — **`toucher` is the actor being given the item, not the
  item itself.**
- `ACustomInventory::CallStateChain` (`thingdef_codeptr.cpp:135-151`) executes each state's action
  function as `State->CallAction(actor, this, &StateCall)`, where `actor` (the toucher) is passed
  as the codepointer's `self` — so `A_ChangeFlag`'s `self` inside the `Pickup:` block **is the
  actor `GiveActorInventory` targeted, not the spawned item.** This is *not* how a plain
  `Inventory`-derived item's `Pickup:` state behaves for pointer purposes in every DECORATE
  codepointer, but it is confirmed correct specifically for `A_ChangeFlag` via this exact call
  chain.
- Because there's no `Use:` state, `ACustomInventory::TryPickup`'s `else if (useok) GoAwayAndDie();`
  branch (`a_pickups.cpp:1840-1846`) fires — the item self-destructs immediately after running the
  `Pickup:` block, so it never sits in the target's inventory or shows up in `CheckInventory`.
- `+INVENTORY.QUIET` just suppresses the normal pickup message/sound; it has no bearing on the
  mechanism above.

One item class per flag (or per fixed flag+value combo) is required — there's no way to pass the
flag name/value as ACS-side parameters into the DECORATE state, since `A_ChangeFlag`'s arguments
are compiled into the state definition, not read from the giving script.
