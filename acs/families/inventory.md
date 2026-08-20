# Inventory family

**Tier:** A for fifteen; `GetMaxInventory` is tier A for the negative finding (confirmed dead,
see below). Two source-only additions with no wiki starting point are tier B: the
`CheckInventory`/`CheckActorInventory` cost note, and the closing "no non-player declarative
starting inventory" section.
**Applies to:** UZDoom=yes, Zandronum=yes — file-level claim for the majority; `GetMaxInventory`
specifically is the outlier, confirmed `uzdoom-only` (see its own section below)
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-06)
**Provenance:** ZDoom Wiki pages `ClearInventory` (retrieved 2026-08-06, https://zdoom.org/w/index.php?title=ClearInventory&oldid=40599), `ClearActorInventory` (retrieved 2026-08-06, https://zdoom.org/w/index.php?title=ClearActorInventory&oldid=42468), `GiveInventory` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=GiveInventory&oldid=52127), `GiveActorInventory` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=GiveActorInventory&oldid=45630), `TakeInventory` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=TakeInventory&oldid=52106), `TakeActorInventory` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=TakeActorInventory&oldid=45631), `CheckInventory` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=CheckInventory&oldid=35673), `CheckActorInventory` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=CheckActorInventory&oldid=35649), `UseInventory` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=UseInventory&oldid=40595), `UseActorInventory` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=UseActorInventory&oldid=35842), `CheckWeapon` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=CheckWeapon&oldid=35674), `SetWeapon` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=SetWeapon&oldid=35978), `GetWeapon` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=GetWeapon&oldid=48815), `DropItem` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=DropItem&oldid=48036), `DropInventory` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=DropInventory&oldid=53653), `GetMaxInventory` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=GetMaxInventory&oldid=49108). Verified against the Zandronum source throughout.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** `ClearInventory`/`ClearActorInventory`/`GiveInventory`/`GiveActorInventory`/
`TakeInventory`/`TakeActorInventory`/`CheckInventory`/`CheckActorInventory`/`UseInventory`/
`UseActorInventory`/`CheckWeapon`/`SetWeapon` are all compiler builtins (`zt-bcc/src/builtin.c`,
`PCD_*` opcodes in `p_acs.cpp`'s main switch). `DropItem` (-74), `GetWeapon` (-69),
`DropInventory` (-82), and `GetMaxInventory` (-93) are extension functions (`zcommon.bcs`'s
`special` table, `case ACSF_*:` in `p_acs.cpp`).

`ClearInventory`, `ClearActorInventory`, `GiveInventory`, `GiveActorInventory`, `TakeInventory`,
`TakeActorInventory`, `CheckInventory`, `CheckActorInventory`, `UseInventory`,
`UseActorInventory`, `CheckWeapon`, `SetWeapon`, `GetWeapon`, `DropItem`, `DropInventory`,
`GetMaxInventory` — sixteen wiki-documented functions that read like one uniform "inventory API"
but are actually two distinct subsystems plus a compiler-optimization detail, all sharing the
"plain activator form / explicit-`tid` `Actor` form" naming pattern. One family file instead of
sixteen per-function files because the cross-cutting findings below (shared helpers, a `tid==0`
asymmetry, and a dead function) only show up by reading several of these together, not any one
wiki page in isolation.

All sixteen are documented below despite uneven real-world usage — see the family-coverage rule
in `../../shared/AUTHORING.md`'s Authoring rule section (the low-usage members of a family are exactly the ones
nobody's figured out yet).

## Shared implementation — the Check/Give/Take/Clear core

`ClearInventory`, `GiveInventory`, `TakeInventory`, `CheckInventory` and their `*Actor` siblings
all funnel into just **four shared static helpers** in `p_acs.cpp`: `ClearInventory(AActor*)`,
`GiveInventory`/`DoGiveInv`, `TakeInventory`/`DoTakeInv`, `CheckInventory(AActor*, const char*)`.
The plain and `*Actor` forms differ only in how the target actor(s) are resolved:

- **Plain forms** (no `tid` parameter) always operate on the VM's `activator`. With no activator,
  `ClearInventory`/`GiveInventory`/`TakeInventory` fan out to **every player in game**; but
  `CheckInventory(NULL, ...)` has no sane "check all players" return shape and instead returns `0`
  immediately — a real asymmetry inside this group.
- **`*Actor` forms with `tid != 0`** walk `FActorIterator(tid)` — every actor sharing that TID is
  affected, not just one (undocumented on any of these wiki pages).
- **`*Actor` forms with `tid == 0`:** `ClearActorInventory`/`GiveActorInventory`/
  `TakeActorInventory` explicitly special-case this to the same "all players" fan-out as their
  plain-form no-activator case. **`CheckActorInventory` breaks the pattern**: it resolves the
  actor via `SingleActorFromTID(tid, NULL)`, which for `tid==0` returns the hardcoded `NULL`
  default (not the activator, not an all-players loop) — so `CheckActorInventory(0, "item")`
  always resolves to a null actor and returns `0` unconditionally. It's neither "all players"
  like its Give/Take/Clear siblings nor "the activator" like plain `CheckInventory` — a real
  three-way asymmetry no wiki page calls out.

`*Direct` opcode variants (`GIVEINVENTORYDIRECT`, `TAKEINVENTORYDIRECT`, `CHECKINVENTORYDIRECT`)
exist only for the plain forms (no Direct variant for `*ActorInventory`). The compiler
(`zt-bcc/src/codegen/obj.c`) emits these automatically whenever every argument to the call
resolved to a compile-time constant — a pure bytecode-encoding optimization (immediate operands
instead of stack push/pop). The `p_acs.cpp` case bodies for the Direct opcodes call the identical
`GiveInventory`/`TakeInventory`/`CheckInventory` helpers; there is no behavioral difference from
the non-Direct form, so this repo doesn't document them separately. Confirmed unchanged on UZDoom:
no `*ActorInventoryDirect` opcode exists there either, and the Direct case bodies route through the
same dispatch described below.

## Engine-family divergence: dispatch architecture

On UZDoom, three of these four shared helpers no longer exist as native C++ functions. The
`PCD_CLEARINVENTORY`/`PCD_CLEARACTORINVENTORY`, `PCD_GIVEINVENTORY`/`PCD_GIVEACTORINVENTORY`, and
`PCD_TAKEINVENTORY`/`PCD_TAKEACTORINVENTORY` opcode bodies (`src/playsim/p_acs.cpp`) now call
`ScriptUtil::Exec` to invoke ZScript-side entry points (`ScriptUtil.GiveInventory`/`TakeInventory`/
`ClearInventory` in `wadsrc/static/zscript/scriptutil/scriptutil.zs`) that do the string→class
resolution, the `"Armor"` special-casing, and the no-activator/`tid==0` all-players fan-out, then
call the ZScript `Actor.GiveInventory`/`TakeInventory`/`ClearInventory` methods
(`wadsrc/static/zscript/actors/inventory_util.zs`) that do the actual mutation — `GiveInventory`'s
per-class amount handling (e.g. armor's `SaveAmount *= amount`) is a `SetGiveAmount` override on
the relevant `Inventory` subclass (`inventory.zs`, `armor.zs`), not inline code in the give path
itself. Only `CheckInventory` remains a native static helper (`p_acs.cpp`) — and it has gained a
third `bool max` parameter, making it *also* the entire implementation behind `GetMaxInventory`
(see that member's own section below). The net per-call behavior this file already documents (the
`tid==0` fan-out patterns, the `"Armor"`/`"Health"` special-casing, the `amount<=0` no-op, and the
Give-warns/Take-is-silent diagnostic asymmetry) is preserved end-to-end through this different
plumbing — UZDoom's unknown-item warning text differs from Zandronum's (`GiveInventory: Unknown
item type %s.` / `GiveInventory: %s is not an inventory item.` via ZScript's `Console.Printf`, vs
Zandronum's `ACS: I don't know what %s is.` / `ACS: %s is not an inventory item.` via native
`Printf`), but both are unconditional, always-visible console warnings, and `TakeInventory` stays
silent on both engines. See the `TakeInventory` section below for the one behavioral crack this
re-architecture actually closes.

## `UseInventory`/`UseActorInventory` and `CheckWeapon`/`SetWeapon` are a different subsystem

Despite the shared naming convention, none of these four share the Check/Give/Take/Clear group's
helpers, and none share helpers with each other except the `UseInventory`/`UseActorInventory`
pair. The plain Check/Give/Take group is pure bookkeeping — it reads or mutates an `AInventory`'s
`Amount` counter without invoking the item's own behavior. `UseInventory`/`UseActorInventory`
instead **execute** the item's real `Use()` effect (healing, ammo consumption, a weapon switch via
`AWeapon::Use`, player sound/HUD flash) and only *incidentally* decrement/destroy the stack as a
side effect of a successful use. `CheckWeapon` is not a possession check at all — it's a
class-identity check against the single currently-*equipped* weapon slot (`player->ReadyWeapon`),
categorically different from `CheckInventory`'s "how many do I have." `SetWeapon` can only
*select* a weapon the actor already owns (it never grants one, unlike `GiveInventory`), gated by
an ammo check the wiki omits entirely.

---

## `void ClearInventory()` / `void ClearActorInventory(int tid)`

`PCD_CLEARINVENTORY` / `PCD_CLEARACTORINVENTORY` (`p_acs.cpp:11677-11701`), both call the shared
`ClearInventory(AActor*)` helper (`p_acs.cpp:1249`). No amount/type args — calls the native
`AActor::ClearInventory()`, which correctly skips `INVENTORY.UNDROPPABLE`-flagged items (matches
wiki). `ClearActorInventory` fans out over every actor matching `tid` (or all players at `tid==0`
— see "Shared implementation" above).

**Weapon slot interaction (wiki omitted):** `ClearInventory` also resets player `ReadyWeapon` to
`NULL`, `PendingWeapon` to `WP_NOCHANGE`, and clears sprite states (`p_mobj.cpp:1157-1161`). For
a player with an equipped weapon, this is a side effect that affects subsequent `CheckWeapon()`,
`SetWeapon()`, and `GetWeapon()` behavior — neither wiki page mentions this cross-cutting
interaction.

**Netcode replication (Zandronum-only, wiki omitted):** On a Zandronum server, `ClearInventory`
calls `SERVERCOMMANDS_DestroyAllInventory(player - players)` to notify clients (`p_mobj.cpp:1165`
with `[BB]` tag). This is purely additive; the behavior is otherwise correct. UZDoom has no
`SERVERCOMMANDS_*` replication subsystem at all (confirmed by a full-source grep), so this specific
addition doesn't apply there — expected, since it's Zandronum's own client-server netcode, not a
general engine feature.

## Engine-family divergence: `Inventory.UNCLEARABLE` flag

UZDoom's `ClearInventory`/`ClearActorInventory` (via the ZScript `Actor.ClearInventory()` — see
"dispatch architecture" above) also skip any item flagged `+Inventory.UNCLEARABLE`
(`wadsrc/static/zscript/actors/inventory/inventory.zs`'s `flagdef Unclearable`) — a flag
independent of `UNDROPPABLE`, so an item can be droppable yet still immune to `ClearInventory` on
UZDoom. A full-source grep of the Zandronum source finds no `Unclearable`/`UNCLEARABLE` symbol
anywhere — this isn't a flag Zandronum leaves unset on any actor, it's a distinction Zandronum has
no way to express at all.

**Provenance:** ZDoom Wiki `ClearInventory` (retrieved 2026-08-06, https://zdoom.org/w/index.php?title=ClearInventory&oldid=40599) and `ClearActorInventory` (retrieved 2026-08-06, https://zdoom.org/w/index.php?title=ClearActorInventory&oldid=42468) + source-verified against `p_acs.cpp:1249`, `:11677-11701`. **Tier:** A.

---

## `void GiveInventory(str item, int amount)` / `void GiveActorInventory(int tid, str item, int amount)`

`PCD_GIVEINVENTORY` / `PCD_GIVEACTORINVENTORY` → shared `GiveInventory(activator, type, amount)`
/ `DoGiveInv` helpers (`p_acs.cpp:1274-1391`).

- `amount <= 0` or a NULL `item` name is a **silent no-op** — not on the wiki.
- `"Armor"` is special-cased **case-insensitively** (`stricmp`) to the concrete class
  `"BasicArmorPickup"`.
- An unknown class, or a class that isn't `AInventory`-derived, prints an `ACS: I don't know what
  %s is.` / `...is not an inventory item.` console warning rather than failing silently — a
  different failure-signaling convention than the [spawning family](spawning.md)'s
  `SpawnForced`. This is a distinct failure mode from the `amount<=0`/NULL case above.
- The actual grant goes through `DoGiveInv`, which spawns a temporary item actor and calls
  `CallTryPickup` — so max-capacity/ammo-cap clamping, weapon-pending-swap suppression, and
  Zandronum's `SERVERCOMMANDS_GiveInventory` replication all happen here. `BasicArmorPickup`
  and `BasicArmorBonus` multiply `SaveAmount` by `amount` instead of setting `Amount` directly — armor's "amount"
  isn't a plain item count. **Consequence:** if an armor's `SaveAmount` is zero at spawn,
  the grant is silently lost (`0 * amount = 0`) regardless of the `amount` value.
- `GiveActorInventory` fans out over every actor matching `tid` (undocumented multi-target on its
  wiki page), or all players at `tid==0` (matches wiki).

Confirmed on UZDoom (see "Engine-family divergence: dispatch architecture" above for what changed
structurally there): every claim in this section holds on both engines.

**Provenance:** ZDoom Wiki `GiveInventory` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=GiveInventory&oldid=52127) and
`GiveActorInventory` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=GiveActorInventory&oldid=45630) + source-verified against
`p_acs.cpp:1274-1391`, `:11703-11726`. **Tier:** A.

---

## `void TakeInventory(str item, int amount)` / `void TakeActorInventory(int tid, str item, int amount)`

`PCD_TAKEINVENTORY` / `PCD_TAKEACTORINVENTORY` → shared `TakeInventory(activator, type, amount)`
/ `DoTakeInv` helpers (`p_acs.cpp:1401-1477`).

- `amount <= 0` is a silent no-op, matching the wiki's "no inventory can be a negative amount."
- **`"Armor"` here is case-***sensitive*** (`strcmp`, `p_acs.cpp:1451`)** — the opposite of
  `GiveInventory`'s case-insensitive `stricmp` for the same literal string — and maps to a
  *different* class (`"BasicArmor"`, the running-total class, vs. Give's `"BasicArmorPickup"`).
  `TakeInventory("armor", 5)` (lowercase) misses the special-case entirely and looks for a
  literal class named `"armor"` (fails → no-op), while `GiveInventory("armor", 5)` works
  regardless of case. A real, wiki-unstated crack between two functions that look like a matched
  pair.
- **Second Give/Take asymmetry (error diagnostics):** `GiveInventory` prints `ACS: I don't know
  what %s is.` / `...is not an inventory item.` for an unresolvable or non-`AInventory` class;
  `TakeInventory` is silent (just returns without side-effect), making failed `TakeInventory`
  calls invisible to debugging.
- Removal goes through `DoTakeInv`: decrements `Amount`, and at `<= 0` either zeroes it (if
  `IF_KEEPDEPLETED`, e.g. ammo — stays at 0 for weapon bookkeeping) or fully destroys the item.
  This operates directly on the inventory item rather than through the drop path, confirming the
  wiki's claim that (unlike `ClearInventory`) it can remove undroppable items.
- `TakeActorInventory` fans out over every actor matching `tid` (undocumented multi-target), or
  all players at `tid==0` (matches wiki).

## Engine-family divergence: the `"Armor"` case-sensitivity crack is closed on UZDoom

The case-sensitivity half of the "real, wiki-unstated crack" above is a Zandronum-specific artifact
of its native `strcmp` (`p_acs.cpp:1451`, re-confirmed by direct read). On UZDoom, `TakeInventory`'s
`"Armor"` special-case lives in ZScript (`ScriptUtil.TakeInventory`, `scriptutil.zs` — see "dispatch
architecture" above) and is written as a `Name` comparison (`type == 'Armor'`); `Name`/`FName`
lookups in this engine family are inherently case-insensitive — `FName::NameManager::FindName`
(`src/utility/name.cpp`) lowercases every string before hashing it, and the ACS item-name string is
already converted to an `FName` at the `PCD_TAKEINVENTORY`/`PCD_TAKEACTORINVENTORY` opcode sites
before the ZScript call, so `"armor"`, `"Armor"`, and `"ARMOR"` all resolve to the same name index
by the time the comparison runs. `TakeInventory("armor", 5)` therefore behaves identically to
`TakeInventory("Armor", 5)` on UZDoom, matching `GiveInventory`'s case-insensitivity instead of
diverging from it — the crack Zandronum has does not exist here. The **class-identity** half of the
original claim still holds, though the target is no longer a hardcoded literal: UZDoom's `"Armor"`
resolves to `Actor.GetBasicArmorClass()` (`inventory_util.zs`), which defaults to `"BasicArmor"`
but is overridable via `GameInfo.BasicArmorClass`, while `GiveInventory`'s `"Armor"` still hardcodes
the literal `"BasicArmorPickup"`. The two functions still target different classes on UZDoom; they
just no longer disagree on case.

**Provenance:** ZDoom Wiki `TakeInventory` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=TakeInventory&oldid=52106) and
`TakeActorInventory` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=TakeActorInventory&oldid=45631) + source-verified against
`p_acs.cpp:1401-1477`, `:11733-11756`. **Tier:** A.

---

## `int CheckInventory(str item)` / `int CheckActorInventory(int tid, str item)`

`PCD_CHECKINVENTORY` / `PCD_CHECKACTORINVENTORY` → shared `CheckInventory(activator, type)`
helper (`p_acs.cpp:1559-1576`), the latter via `SingleActorFromTID(tid, NULL)`.

- Two pseudo-items neither wiki page mentions: `"Armor"` (case-insensitive) redirects to the
  `"BasicArmor"` class; **`"Health"` bypasses the inventory system entirely and returns
  `activator->health`** directly, not a count.
- For any other item, returns `item->Amount` if the actor has it — but "doesn't have it" and
  "unknown class name" are genuinely indistinguishable, both returning `0` via a null lookup
  chain (`PClass::FindClass` → `FindInventory` → `0`).
- `CheckInventory(NULL, ...)` (no activator) returns `0` unconditionally — see "Shared
  implementation" above for why this breaks the Give/Take/Clear group's "all players" pattern.
- `CheckActorInventory(0, ...)` also always returns `0` (`SingleActorFromTID` default, not the
  activator, not an all-players loop) — the wiki's "does not treat tid 0 as the activator" is
  accurate but understates how thoroughly tid 0 is a guaranteed no-op here, not a fallback to any
  useful semantic.
- **Cost, not just semantics (tier B — source-verified, no wiki starting point):** the shared
  static helper (`p_acs.cpp:1559-1576`) does, per call: up to two `stricmp()` calls for the
  special-cased `"Armor"`/`"Health"` names (one check each via `if`/`else if`), then `PClass::FindClass(type)` (a name-table + class
  hash lookup), then `AActor::FindInventory` (a linear walk of the actor's own inventory linked
  list). Cheaper than a class-name substring scan across every actor, but not a fixed-cost lookup
  either — a script calling this every tic for several items is walking a hash lookup plus a
  linked-list scan each time, not touching a precomputed table.

## Engine-family divergence: unknown-class diagnostic and lookup cost

Zandronum's shared helper (`p_acs.cpp:1559-1576`) is completely silent for an unresolved class name
or a class that isn't `AInventory`-derived — the doc's "genuinely indistinguishable" claim above is
exact. UZDoom's equivalent helper (`p_acs.cpp`, same signature plus the `bool max` parameter that
also makes it `GetMaxInventory`'s implementation — see that member's own section) adds a
`DPrintf(DMSG_ERROR, ...)` call for both the unknown-class and the not-an-inventory-item cases. The
return value is still `0` either way, so ACS-visible behavior is unchanged, but the two failure
modes are now distinguishable in a UZDoom console/log once `developer` is raised to `DMSG_ERROR` or
higher — Zandronum never prints anything here at any `developer` level, because the check doesn't
exist. Separately, the tier-B cost note above gets one more layer on UZDoom: `item->Amount`/
`MaxAmount` access goes through `IntVar()` → `ScriptVar()` → `PClass::FindSymbol()`, a
class-symbol-table lookup by field name, rather than Zandronum's direct struct-member dereference —
a small added cost per call, not a different order of magnitude.

**Provenance:** ZDoom Wiki `CheckInventory` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=CheckInventory&oldid=35673) and
`CheckActorInventory` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=CheckActorInventory&oldid=35649) + source-verified against
`p_acs.cpp:1559-1576`, `:11758-11771` (tier A); the cost note adds no new citation beyond the
same `p_acs.cpp:1559-1576` helper already cited, read for cost rather than semantics (tier B,
no wiki starting point for that specific framing). **Tier:** A (semantics); B (cost note).

---

## `int UseInventory(str classname)` / `int UseActorInventory(int tid, str classname)`

`PCD_USEINVENTORY` (`p_acs.cpp:11773-11775`) / `PCD_USEACTORINVENTORY`
(`p_acs.cpp:11777-11797`), both via shared `UseInventory`/`DoUseInv` helpers (`p_acs.cpp:1522-1549`).

- Invokes `AActor::UseInventory(item)` for real — calls the item's virtual `Use()`, then
  decrements/destroys the stack only on success. For an `APlayerPawn` specifically
  (`p_user.cpp:1066-1114`), a gate on time-frozen status (`LEVEL2_FROZEN`/`timefreezer`) is
  applied; the `CF_TOTALLYFROZEN` player-freeze flag is *bypassed* specifically on the ACS
  path (`p_acs.cpp:1500-1508`). Player path also plays `UseSound`, flashes the status bar, and
  replicates via `SERVERCOMMANDS_PlayerUseInventory`; a non-player actor gets the plain path
  with none of those checks.
- No-activator case loops every in-game player and sums each one's use result — confirms "runs
  for all active players," but the wiki calls the return a plain bool when it's actually
  **declared `int` and can be a sum > 1** in this branch (three players succeeding returns `3`,
  not an error).
- All failure modes (unresolved classname, item not owned, `Amount<=0`, item pending destruction,
  the item's own `Use()` returning false, time-frozen player) are silent — contribute `0`, no
  console message.
- `UseActorInventory`'s `tid==0` is hardcoded to call `UseInventory(NULL, type)` — i.e. it forces
  the same all-players path as plain `UseInventory`'s no-activator case, **regardless of whether
  the calling script has a real activator** — not a `FActorIterator(0)` walk. `tid != 0` walks
  `FActorIterator(tid)` and sums each matched actor's per-actor result (0 or 1); this return is a
  genuine count and matches its wiki page exactly.

Confirmed on UZDoom: `DoUseInv`'s `CF_TOTALLYFROZEN` bypass, `PlayerPawn::UseInventory`'s
frozen/sound/HUD-flash handling (now a ZScript override in `player_inventory.zs`), and the
`sv_infiniteinventory`/`DF2_INFINITE_INVENTORY` depletion-skip all carry over unchanged.

**Provenance:** ZDoom Wiki `UseInventory` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=UseInventory&oldid=40595) and
`UseActorInventory` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=UseActorInventory&oldid=35842) + source-verified against
`p_acs.cpp:1522-1549`, `:1487-1512` (DoUseInv), `:11773-11797`, `p_user.cpp:1066-1114`.
**Tier:** A.

---

## `bool CheckWeapon(str weapon)`

`PCD_CHECKWEAPON` (`p_acs.cpp:12250-12266`) — self-contained, no shared helper. Reads
`activator->player->ReadyWeapon` directly and compares its class name to `weapon` — this checks
the **currently readied/equipped weapon**, not mere possession; owning the weapon but not having
it selected returns false. `activator==NULL`, `activator->player==NULL` (non-player actors always
fail — weapons are player-only), or `ReadyWeapon==NULL` (nothing readied yet) → `0`.

**Zandronum-only addition absent from the ZDoom wiki entirely:** as a network server, if the
activator's client hasn't yet confirmed its starting weapon selection
(`!bClientSelectedWeapon && ReadyWeapon==NULL && PendingWeapon==WP_NOCHANGE`), `CheckWeapon`
instead compares against `player->StartingWeaponName` (`p_acs.cpp:12251-12256`, `[BB]`-tagged) —
lets the check answer correctly right at spawn, before the client's weapon-selection packet has
round-tripped. Purely additive; the wiki's core "is this the active weapon" semantic is otherwise
correct. Confirmed absent from the UZDoom source (no `StartingWeaponName`/`bClientSelectedWeapon`
symbols anywhere) — expected, since the Zandronum engine fork's client-server netcode this fallback
exists for isn't present on UZDoom at all; the core `ReadyWeapon` comparison is otherwise identical.

**Provenance:** ZDoom Wiki `CheckWeapon` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=CheckWeapon&oldid=35674) + source-verified against
`p_acs.cpp:12250-12266`. **Tier:** A.

---

## `bool SetWeapon(str weaponname)`

`PCD_SETWEAPON` (`p_acs.cpp:12268-12310`) — self-contained, no shared helper with `CheckWeapon` or
the `UseInventory` pair. **Does not grant the weapon** — looks it up via
`activator->FindInventory(...)`; not owned, or not `AWeapon`-derived, both fail silently (`0`).
Player-only (`activator->player==NULL` → `0`); no explicit dead/spectator gate in this case body
itself, unlike `UseInventory`'s `health<=0` check.

- **Ammo gate the wiki omits entirely:** if the weapon isn't already `ReadyWeapon`, the code calls
  `weap->CheckAmmo(AWeapon::EitherFire, false)` first — insufficient ammo for *both* primary and
  alt fire makes `SetWeapon` fail and return `0` **even though the actor owns the weapon**. Any
  owned-but-empty gun, or a melee weapon needing ammo it lacks, silently refuses to be selected.
- **Idempotent short-circuit:** re-selecting the already-`ReadyWeapon` succeeds unconditionally
  (sets `PendingWeapon = WP_NOCHANGE`, returns `1`) — bypassing the ammo check, so re-selecting
  your current (even empty) weapon always "succeeds."
- On a real switch, sets `player->PendingWeapon` and replicates via
  `SERVERCOMMANDS_SetPlayerPendingWeapon` on a Zandronum server — no ZDoom-wiki equivalent. UZDoom
  has no `SERVERCOMMANDS_*` subsystem at all, so only the `PendingWeapon` assignment applies there.

On UZDoom, `PCD_SETWEAPON` dispatches via `ScriptUtil::Exec` to `ScriptUtil.SetWeapon` (`scriptutil.zs`)
instead of a self-contained `p_acs.cpp` case body — the same "no shared helper with `CheckWeapon`"
claim above still holds (this is its own ZScript function, not reused by anything else in this
family), and every behavioral claim in this section (lookup-not-grant, the `CheckAmmo` gate, the
idempotent already-ready short-circuit) reads verbatim off that ZScript function.

**Provenance:** ZDoom Wiki `SetWeapon` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=SetWeapon&oldid=35978) + source-verified against
`p_acs.cpp:12268-12310`. **Tier:** A.

---

## `str GetWeapon()`

Extension function -69 (`case ACSF_GetWeapon:`, `p_acs.cpp:6685-6694`). Reads the same
`activator->player->ReadyWeapon` field `CheckWeapon` compares against, but returns its class
`TypeName` directly instead of a bool. `activator==NULL`, `activator->player==NULL` (non-player
actor), or `ReadyWeapon==NULL` all return the literal string `"None"` — matches the wiki exactly,
and unlike `CheckInventory`'s unknown-item case this failure value is an unambiguous, printable
sentinel rather than a bare `0`.

**Notable gap versus its sibling:** `GetWeapon` has **no equivalent of `CheckWeapon`'s
Zandronum-only `StartingWeaponName` server-side fallback** (see `CheckWeapon` above) — right after
a player spawns on a server, before their weapon-selection packet round-trips,
`CheckWeapon("Pistol")` can correctly answer `true` via that fallback while `GetWeapon()` still
returns `"None"` for the same activator at the same instant. Querying and boolean-checking "the
same" state can disagree during that window; nothing on either wiki page mentions it since it only
exists in the Zandronum engine fork's netcode. On UZDoom this window doesn't exist at all: since
`CheckWeapon` has no `StartingWeaponName` fallback there either (see that section), `CheckWeapon`
and `GetWeapon` stay consistent with each other at every instant — both simply read `ReadyWeapon`
the same way, with nothing to disagree about.

**Provenance:** ZDoom Wiki `GetWeapon` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=GetWeapon&oldid=48815) + source-verified against
`p_acs.cpp:6685-6694`, cross-checked against `CheckWeapon`'s fallback at `p_acs.cpp:12251-12256`.
**Tier:** A.

---

## `int DropItem(int tid, str item [, int dropamount [, int chance]])`

Extension function -74 (`case ACSF_DropItem:`, `p_acs.cpp:6735-6766`). Spawns a **new instance**
of `item` into the world via `P_DropItem()`/`Spawn()` (`p_enemy.cpp:3463-3491`) — not taken from
any actor's existing inventory slot; this is the odd one out in the family, world-spawning rather
than inventory-manipulating. `dropamount` (default `-1`) feeds `ModifyDropAmount`, meaningful only
for `Inventory`-derived classes. `chance` (default `256`) gates an 8-bit `pr_dropitem()` roll via
comparison `pr_dropitem() <= chance` (`p_enemy.cpp:3471`). `tid==0` drops from the activator (only if non-NULL);
nonzero `tid` iterates every matching actor via `FActorIterator`. Return value counts actors
*attempted* regardless of whether the roll/spawn actually succeeded — matches wiki.

**Wiki divergence (low-end boundary):** The wiki states "never dropped if this is -1 or less," but
the source comparison `pr_dropitem() <= chance` only guarantees never-drop when `chance < 0`
(i.e., `-1` or less). At `chance == 0`, the roll succeeds when `pr_dropitem()` returns 0 — one
result out of the 8-bit range [0, 255] — making it a 1-in-256 drop, not a never-drop. High-end
boundary ("255+ always drops") is correct: both 255 and 256 guarantee a drop since max roll is 255.

On UZDoom, `ACSF_DropItem` (`p_acs.cpp`) still spawns via `P_DropItem` (`p_enemy.cpp`), but
`P_DropItem` there is a thin native trampoline into the ZScript `Actor.A_DropItem` function
(`inventory_util.zs`) rather than doing the spawn/roll inline; the roll comparison itself
(`random[DropItem]() <= chance`) and the wiki-divergence finding below both carry over unchanged —
same 8-bit range, same `<=` comparison, same 1-in-256 result at `chance==0`.

**Provenance:** ZDoom Wiki `DropItem` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=DropItem&oldid=48036) + source-verified against
`p_acs.cpp:6735-6766`, `p_enemy.cpp:3463-3491`. **Tier:** A.

---

## `void DropInventory(int tid, str itemtodrop)`

Extension function -82 (`case ACSF_DropInventory:`, `p_acs.cpp:6768-6802`). Looks up the item via
`FindInventory` and, if present, calls `AActor::DropInventory` (`p_mobj.cpp:924-958`), which routes
through `item->CreateTossable()` (`a_pickups.cpp:797-834`): either the item itself becomes the
world pickup (`BecomePickup()`) if `Amount==1`, or `Amount` is decremented and a fresh
`Amount=1` copy is spawned at the owner's position with toss velocity. This is a genuine
remove-and-spawn-a-tossable path, distinct from `TakeInventory`'s plain destroy/decrement with no
world pickup. Drops exactly one sample per call regardless of held quantity — matches wiki. Not
having the item is a silent no-op. `tid==0` targets the activator's inventory; nonzero targets
every actor matching that TID. No divergence found.

On UZDoom, `AActor::DropInventory` (`p_mobj.cpp`) is a native trampoline into the ZScript
`Actor.DropInventory` method (`inventory_util.zs`), which calls `Inventory.CreateTossable`
(`inventory.zs`) — the "one item becomes the pickup at `Amount==1`, otherwise `Amount` decrements
and a fresh copy spawns" split, and the toss-velocity/`ClearCounters` handling, both carry over
unchanged. The default-amount plumbing changed representation (a `-1` sentinel that `CreateTossable`
clamps to `1`, rather than a literal default of `1`) but the net effect — exactly one sample dropped
per call — is identical. No divergence found on UZDoom either.

**Provenance:** ZDoom Wiki `DropInventory` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=DropInventory&oldid=53653) + source-verified
against `p_acs.cpp:6768-6802`, `p_mobj.cpp:924-958`, `a_pickups.cpp:797-834`. **Tier:** A.

---

## `int GetMaxInventory(int tid, str inventory)` — **dead on Zandronum, live on UZDoom**

Extension function -93. **No `ACSF_GetMaxInventory` enum member and no switch case exist anywhere
in the Zandronum source's `src/p_acs.cpp`** — `grep -n "GetMaxInventory" p_acs.cpp` returns zero hits
in the whole file (every genuinely-implemented `ACSF_*` name appears at least once; zero hits is
the tell for "never backported"). The `ACSF_*` enum jumps from `ACSF_Warp = 92` straight to a
comment block (`p_acs.cpp:~5449`) noting Zandronum's own numbering resumes at `ACSF_ResetMap =
100` — ZDoom's upstream 93-99 range (`GetMaxInventory`, `SetSectorDamage`, `SetSectorTerrain`,
`SpawnParticle`, `SetMusicVolume`, `CheckProximity`, `CheckActorState`) was never backported into
the Zandronum engine fork at all. This is the exact same gap the [spawning family](spawning.md)
already documented for `SpawnParticle` at -96 — `GetMaxInventory` at -93 sits in the same dead
range. A call falls through the switch's `default: break;` and unconditionally returns `0`.

The wiki page itself already flags this (its own "Zandronum" section states Zandronum 3.0 doesn't
support it and always returns 0, suggesting `GetAmmoCapacity` as a workaround) — so this isn't a
silent trap the way `SpawnParticle` was, but it's still worth recording plainly: **don't call
`GetMaxInventory` on Zandronum; use `GetAmmoCapacity` for ammo-type items, or track max
inventory manually for others. On UZDoom, `GetMaxInventory` works and this workaround isn't
needed — see below.**

**UZDoom-side confirmation (2026-08-14):** `tools/engine_matrix.py GetMaxInventory` resolves this
name to bin `uzdoom-only` — UZDoom's own ACSF enum, unlike Zandronum's, never dropped the upstream
ZDoom 93–99 range this function belongs to, so `GetMaxInventory` is genuinely implemented and
callable on UZDoom. This is the one member of this family where the divergence runs the opposite
direction from every other reserved-range case documented in this tree: dead on Zandronum, live on
UZDoom, not the other way around.

**Full-source read (2026-08-15):** `case ACSF_GetMaxInventory:` (`p_acs.cpp`) resolves the target
via `Level->SingleActorFromTID(args[0], bClientSide, activator)` and, if non-NULL, calls the exact
same `CheckInventory(AActor*, const char*, bool)` helper `CheckInventory`/`CheckActorInventory` use
(see that member's "Engine-family divergence" section above) with `max=true` — on UZDoom,
`GetMaxInventory` isn't just *implemented*, it's the same function as `CheckInventory` with one
extra argument. Consequences: `"Armor"` redirects to `"BasicArmor"` (case-insensitive), same as
`CheckInventory`; `"Health"` bypasses the inventory system and returns `activator->GetMaxHealth()`
(as opposed to plain `CheckInventory`'s `activator->health`) — a pseudo-item behavior with no
Zandronum equivalent to compare against, since the function doesn't exist there at all. The `tid==0`
case is also its own, fourth variant of the asymmetry the "Shared implementation" section documents
for this family: `SingleActorFromTID` is called with `activator` as the default (not the hardcoded
`NULL` that `CheckActorInventory` passes), so `GetMaxInventory(0, "item")` resolves to **the calling
script's activator** — matching plain `CheckInventory`'s no-tid behavior, not
`CheckActorInventory(0, ...)`'s guaranteed-zero no-op.

**Provenance:** ZDoom Wiki `GetMaxInventory` (retrieved 2026-08-07, https://zdoom.org/w/index.php?title=GetMaxInventory&oldid=49108, wiki page itself notes
the Zandronum gap) + source-verified via full-file grep of the Zandronum source's `src/p_acs.cpp`
finding zero references, cross-checked against the enum layout at `p_acs.cpp:~5362-5469`.
**Tier:** A.

---

## Related DECORATE-side gap: there is no non-player declarative "starting inventory" property

**Tier:** B — source-verified, no wiki starting point.

Worth recording alongside this ACS-side family, since it's the natural DECORATE-side counterpart
someone reaching for these functions might expect to exist instead: **neither the Zandronum nor the
UZDoom engine fork has a way to give a non-player actor a declarative starting inventory item.**

- `DropItem` the DECORATE **property** (`DEFINE_PROPERTY(dropitem, S_i_i, Actor)`,
  `thingdef_properties.cpp:761` — distinct from the `DropItem` ACS extension function documented
  above, same name, different mechanism entirely) is the actor's **death-drop** list, consulted
  only when the actor dies, not a starting/spawn-time inventory grant.
- The only starting-inventory DECORATE property that exists at all in either engine fork is
  `Player.StartItem` (`DEFINE_CLASS_PROPERTY_PREFIX(player, startitem, S_i, PlayerPawn)`,
  `thingdef_properties.cpp:2655`), and it is hard-restricted to `PlayerPawn` subclasses by its own
  macro declaration.
- Giving a non-player actor (a monster, a decoration, any non-`PlayerPawn` class) a starting
  inventory item declaratively is **not possible** in either engine fork — the only mechanism is an
  imperative `A_GiveInventory` call from a `Spawn:` state, or one of the ACS-side `Give*Inventory`
  functions documented above, run after the actor already exists.

**UZDoom confirmation (2026-08-15):** both declarations still exist, same names, same restrictions —
`DEFINE_PROPERTY(dropitem, S_i_i, Actor)` (`src/scripting/thingdef_properties.cpp:714`, still the
actor's death-drop list, unrelated to spawn-time grants) and
`DEFINE_CLASS_PROPERTY_PREFIX(player, startitem, S_i, PlayerPawn)`
(`src/scripting/thingdef_properties.cpp:1753`, still `PlayerPawn`-only). The file moved from
`src/thingdef/` to `src/scripting/` and the line numbers shifted, but the properties and their
restrictions are otherwise unchanged — no declarative non-player starting-inventory mechanism was
added.

**Provenance:** source-verified directly against `src/thingdef/thingdef_properties.cpp:761,2655`
(the `DropItem` and `Player.StartItem` `DEFINE_PROPERTY`/`DEFINE_CLASS_PROPERTY_PREFIX`
declarations) — no wiki page consulted for this section.
