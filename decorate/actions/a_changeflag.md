# `void A_ChangeFlag(string flagname, bool value)`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-11); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki `A_ChangeFlag` (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=A_ChangeFlag&oldid=48413) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:4609-4744`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `src/thingdef/thingdef_codeptr.cpp:4609` (`DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_ChangeFlag)`).

Changes the specified actor flag and sets it to the given value. **Note:** Not all flags will produce useful results when changed during gameplay; some flags control fundamental engine behavior at spawn time or require special handling (see "Special-case flags" below).

## Parameters

- **`flagname`** — the name of the flag to change, as a string. Can use dot notation to specify actor-class-specific flags (e.g., `"FRIENDLY"` or `"weapon.nohitscanscan"`). The flag name is case-insensitive.
- **`value`** — the value to set the flag to. `true` sets the flag; `false` clears it.

## Flag name resolution

Flag names are resolved via the engine's `FindFlag` function, which supports two forms:

1. **Simple names** (e.g., `"FRIENDLY"`, `"SHOOTABLE"`) — applied to the calling actor's class.
2. **Dot notation** (e.g., `"weapon.nohitscanscan"`) — for actor-class-specific flags. The part before the dot is the class name (e.g., `weapon`), and the part after is the flag name within that class. This allows changing flags on specialized actor subclasses even when called from a parent class context.

## Special-case flags: relinking and counting

### Blockmap/sector relinking (MF_NOBLOCKMAP, MF_NOSECTOR)

Changing `MF_NOBLOCKMAP` or `MF_NOSECTOR` (both in the `flags` word) requires the actor to be unlinked from and relinked to the world collision system. The function handles this automatically:

- Before modifying the flag, the actor is unlinked from the blockmap and sector links via `UnlinkFromWorld()`.
- The flag is changed.
- The actor is relinked via `LinkToWorld()`.

**Consequence:** Toggling these flags during gameplay can be expensive in terms of collision-system updates; use sparingly.

### Monster/item/secret counting flags

If changing certain counting flags causes the actor's classification to change, the engine updates global counters:

- **`MF_COUNTKILL`** — increments or decrements `level.total_monsters` if the actor's `CountsAsKill()` result changes. In multiplayer, the updated count is broadcast to clients via `SERVERCOMMANDS_SetMapNumTotalMonsters`.
- **`MF_COUNTITEM`** — increments or decrements `level.total_items` if the item-count flag changes. Broadcast via `SERVERCOMMANDS_SetMapNumTotalItems`.
- **`MF5_COUNTSECRET`** — increments or decrements `level.total_secrets` if the secret-count flag changes. Broadcast via `SERVERCOMMANDS_SetMapNumTotalSecrets`.

These updates reflect the actor's new role in the map's statistics, so clearing `MF_COUNTKILL` on a monster will lower the kill count, and setting it later will raise it again.

## Deprecated flags

Some flags are marked as deprecated in the engine's flag table. If `flagname` refers to a deprecated flag (checked via `fd->flagbit` and `HandleDeprecatedFlags`), the function uses special deprecation handling rather than the normal flag-word update. Exact behavior depends on which deprecated flag is involved.

## Zandronum-specific: server-authoritative

**This is server-authoritative in multiplayer.** On network clients:

- **For client-side-only actors** (where `NETWORK_InClientModeAndActorNotClientHandled(self)` is true), the function returns immediately without modifying the flag.
- On servers and single-player, the flag change proceeds normally.
- After the flag changes on the server, if the change actually occurred (the old value differed from the new), the server broadcasts it to all clients via `SERVERCOMMANDS_SetThingFlags`, specifying which flag-word was modified (`FLAGSET_FLAGS`, `FLAGSET_FLAGS2`, etc.).

This prevents desyncs where clients and the server have conflicting actor state.

## Engine-family divergence: multiplayer broadcast

UZDoom's `A_ChangeFlag` has no server-authoritative behavior at all: there is no early-return for client-side actors and no equivalent of `SERVERCOMMANDS_SetThingFlags`, so the flag is simply changed locally on whichever machine runs the script. This means the "Zandronum-specific: server-authoritative" section above (and the "In multiplayer, the updated count is broadcast to clients via `SERVERCOMMANDS_SetMapNumTotal*`" sentences in the "Monster/item/secret counting flags" section) describe Zandronum-only networking; UZDoom has no `SERVERCOMMANDS_*` broadcast mechanism for `A_ChangeFlag` or its counting-flag side effects at all. The counting-flag bookkeeping itself (updating `level.total_monsters`/`total_items`/`total_secrets` when a flag change alters the actor's classification) still happens in UZDoom — it's implemented as an unconditional decrement-then-increment bracket around the flag change (rather than Zandronum's explicit before/after comparison), which nets to the same result: the totals only actually change when the classification genuinely changes, they just aren't broadcast anywhere since UZDoom has no client/server split for this.

## Related functions

- `A_CheckFlag` — checks whether a flag is set without modifying it (and can jump to a state).
- `A_ChangeCountFlags` — changes counting flags specifically (kill/item/secret counts).
- `A_ChangeLinkFlags` — changes flags that affect physics linking specifically.
