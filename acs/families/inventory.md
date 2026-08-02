# Inventory family

`ClearInventory`, `ClearActorInventory`, `GiveInventory`, `GiveActorInventory`, `TakeInventory`,
`TakeActorInventory`, `CheckInventory`, `CheckActorInventory`, `UseInventory`,
`UseActorInventory`, `CheckWeapon`, `SetWeapon`, `GetWeapon`, `DropItem`, `DropInventory`,
`GetMaxInventory` — sixteen wiki-documented functions that read like one uniform "inventory API"
but are actually two distinct subsystems plus a compiler-optimization detail, all sharing the
"plain activator form / explicit-`tid` `Actor` form" naming pattern. One family file instead of
sixteen per-function files because the cross-cutting findings below (shared helpers, a `tid==0`
asymmetry, and a dead function) only show up by reading several of these together, not any one
wiki page in isolation.

**Bucket:** `ClearInventory`/`ClearActorInventory`/`GiveInventory`/`GiveActorInventory`/
`TakeInventory`/`TakeActorInventory`/`CheckInventory`/`CheckActorInventory`/`UseInventory`/
`UseActorInventory`/`CheckWeapon`/`SetWeapon` are all compiler builtins (`zt-bcc/src/builtin.c`,
`PCD_*` opcodes in `p_acs.cpp`'s main switch). `DropItem` (-74), `GetWeapon` (-69),
`DropInventory` (-82), and `GetMaxInventory` (-93) are extension functions (`zcommon.bcs`'s
`special` table, `case ACSF_*:` in `p_acs.cpp`).

**Tier:** A for fifteen; `GetMaxInventory` is tier A for the negative finding (confirmed dead,
see below).

**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md` for the version-gap caveat).

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
the non-Direct form, so this repo doesn't document them separately.

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
— see "Shared implementation" above). No wiki divergence found.

**Provenance:** wiki pages `ClearInventory - ZDoom Wiki.html`, `ClearActorInventory - ZDoom
Wiki.html` (2026-07-28) + source-verified against `p_acs.cpp:1249`, `:11677-11701`. **Tier:** A.

---

## `void GiveInventory(str item, int amount)` / `void GiveActorInventory(int tid, str item, int amount)`

`PCD_GIVEINVENTORY` / `PCD_GIVEACTORINVENTORY` → shared `GiveInventory(activator, type, amount)`
/ `DoGiveInv` helpers (`p_acs.cpp:1274-1391`).

- `amount <= 0` or an unresolvable `item` name is a **silent no-op** — not on the wiki.
- `"Armor"` is special-cased **case-insensitively** (`stricmp`) to the concrete class
  `"BasicArmorPickup"`.
- An unknown class, or a class that isn't `AInventory`-derived, prints an `ACS: I don't know what
  %s is.` / `...is not an inventory item.` console warning rather than failing silently — a
  different failure-signaling convention than the [spawning family](spawning.md)'s
  `SpawnForced`.
- The actual grant goes through `DoGiveInv`, which spawns a temporary item actor and calls
  `CallTryPickup` — so max-capacity/ammo-cap clamping, weapon-pending-swap suppression, and
  Zandronum's `SERVERCOMMANDS_GiveInventory` replication all happen here. `BasicArmorPickup`
  multiplies `SaveAmount` by `amount` instead of setting `Amount` directly — armor's "amount"
  isn't a plain item count.
- `GiveActorInventory` fans out over every actor matching `tid` (undocumented multi-target on its
  wiki page), or all players at `tid==0` (matches wiki).

**Provenance:** wiki pages `GiveInventory - ZDoom Wiki.html`, `GiveActorInventory - ZDoom
Wiki.html` (2026-07-28) + source-verified against `p_acs.cpp:1274-1391`, `:11703-11726`.
**Tier:** A.

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
- Removal goes through `DoTakeInv`: decrements `Amount`, and at `<= 0` either zeroes it (if
  `IF_KEEPDEPLETED`, e.g. ammo — stays at 0 for weapon bookkeeping) or fully destroys the item.
  This operates directly on the inventory item rather than through the drop path, confirming the
  wiki's claim that (unlike `ClearInventory`) it can remove undroppable items.
- `TakeActorInventory` fans out over every actor matching `tid` (undocumented multi-target), or
  all players at `tid==0` (matches wiki).

**Provenance:** wiki pages `TakeInventory - ZDoom Wiki.html`, `TakeActorInventory - ZDoom
Wiki.html` (2026-07-28) + source-verified against `p_acs.cpp:1401-1477`, `:11733-11756`.
**Tier:** A.

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

**Provenance:** wiki pages `CheckInventory - ZDoom Wiki.html`, `CheckActorInventory - ZDoom
Wiki.html` (2026-07-28) + source-verified against `p_acs.cpp:1559-1576`, `:11758-11771`.
**Tier:** A.

---

## `int UseInventory(str classname)` / `int UseActorInventory(int tid, str classname)`

`PCD_USEINVENTORY` (`p_acs.cpp:11773-11775`) / `PCD_USEACTORINVENTORY`
(`p_acs.cpp:11777-11797`), both via shared `UseInventory`/`DoUseInv` helpers (`p_acs.cpp:1522-1549`).

- Invokes `AActor::UseInventory(item)` for real — calls the item's virtual `Use()`, then
  decrements/destroys the stack only on success. For an `APlayerPawn` specifically
  (`p_user.cpp:1066-1114`) this also gates on `health<=0`/frozen-player flags, plays `UseSound`,
  flashes the status bar, and replicates via `SERVERCOMMANDS_PlayerUseInventory`; a non-player
  actor gets the plain path with none of those checks.
- No-activator case loops every in-game player and sums each one's use result — confirms "runs
  for all active players," but the wiki calls the return a plain bool when it's actually
  **declared `int` and can be a sum > 1** in this branch (three players succeeding returns `3`,
  not an error).
- All failure modes (unresolved classname, item not owned, `Amount<=0`, item pending destruction,
  the item's own `Use()` returning false, dead/frozen player) are silent — contribute `0`, no
  console message.
- `UseActorInventory`'s `tid==0` is hardcoded to call `UseInventory(NULL, type)` — i.e. it forces
  the same all-players path as plain `UseInventory`'s no-activator case, **regardless of whether
  the calling script has a real activator** — not a `FActorIterator(0)` walk. `tid != 0` walks
  `FActorIterator(tid)` and sums each matched actor's per-actor result (0 or 1); this return is a
  genuine count and matches its wiki page exactly.

**Provenance:** wiki pages `UseInventory - ZDoom Wiki.html`, `UseActorInventory - ZDoom
Wiki.html` (2026-07-28) + source-verified against `p_acs.cpp:1522-1549`, `:11773-11797`,
`p_user.cpp:1066-1114`. **Tier:** A.

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
correct.

**Provenance:** wiki page `CheckWeapon - ZDoom Wiki.html` (2026-07-28) + source-verified against
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
  `SERVERCOMMANDS_SetPlayerPendingWeapon` on a Zandronum server — no ZDoom-wiki equivalent.

**Provenance:** wiki page `SetWeapon - ZDoom Wiki.html` (2026-07-28) + source-verified against
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
exists in this fork's netcode.

**Provenance:** wiki page `GetWeapon - ZDoom Wiki.html` (2026-07-28) + source-verified against
`p_acs.cpp:6685-6694`, cross-checked against `CheckWeapon`'s fallback at `p_acs.cpp:12251-12256`.
**Tier:** A.

---

## `int DropItem(int tid, str item [, int dropamount [, int chance]])`

Extension function -74 (`case ACSF_DropItem:`, `p_acs.cpp:6735-6766`). Spawns a **new instance**
of `item` into the world via `P_DropItem()`/`Spawn()` (`p_enemy.cpp:3463-3491`) — not taken from
any actor's existing inventory slot; this is the odd one out in the family, world-spawning rather
than inventory-manipulating. `dropamount` (default `-1`) feeds `ModifyDropAmount`, meaningful only
for `Inventory`-derived classes. `chance` (default `256`) gates an 8-bit `pr_dropitem()` roll —
matches the wiki's "255+ always drops." `tid==0` drops from the activator (only if non-NULL);
nonzero `tid` iterates every matching actor via `FActorIterator`. Return value counts actors
*attempted* regardless of whether the roll/spawn actually succeeded — matches wiki. No divergence
found.

**Provenance:** wiki page `DropItem - ZDoom Wiki.html` (2026-07-28) + source-verified against
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

**Provenance:** wiki page `DropInventory - ZDoom Wiki.html` (2026-07-28) + source-verified
against `p_acs.cpp:6768-6802`, `p_mobj.cpp:924-958`, `a_pickups.cpp:797-834`. **Tier:** A.

---

## `int GetMaxInventory(int tid, str inventory)` — **dead in this fork**

Extension function -93. **No `ACSF_GetMaxInventory` enum member and no switch case exist anywhere
in the Zandronum source's `src/p_acs.cpp`** — `grep -n "GetMaxInventory" p_acs.cpp` returns zero hits
in the whole file (every genuinely-implemented `ACSF_*` name appears at least once; zero hits is
the tell for "never backported"). The `ACSF_*` enum jumps from `ACSF_Warp = 92` straight to a
comment block (`p_acs.cpp:~5449`) noting Zandronum's own numbering resumes at `ACSF_ResetMap =
100` — ZDoom's upstream 93-99 range (`GetMaxInventory`, `SetSectorDamage`, `SetSectorTerrain`,
`SpawnParticle`, `SetMusicVolume`, `CheckProximity`, `CheckActorState`) was never backported into
this fork at all. This is the exact same gap the [spawning family](spawning.md) already documented
for `SpawnParticle` at -96 — `GetMaxInventory` at -93 sits in the same dead range. A call falls
through the switch's `default: break;` and unconditionally returns `0`.

The wiki page itself already flags this (its own "Zandronum" section states Zandronum 3.0 doesn't
support it and always returns 0, suggesting `GetAmmoCapacity` as a workaround) — so this isn't a
silent trap the way `SpawnParticle` was, but it's still worth recording plainly: **don't call
`GetMaxInventory` in this fork; use `GetAmmoCapacity` for ammo-type items, or track max
inventory manually for others.**

**Provenance:** wiki page `GetMaxInventory - ZDoom Wiki.html` (2026-07-28, wiki page itself notes
the Zandronum gap) + source-verified via full-file grep of the Zandronum source's `src/p_acs.cpp`
finding zero references, cross-checked against the enum layout at `p_acs.cpp:~5362-5469`.
**Tier:** A.
