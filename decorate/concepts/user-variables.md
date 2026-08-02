# User variables

**Tier:** A
**Engine:** Zandronum 3.2.1
**Provenance:** ZDoom Wiki "User variable" (retrieved 2026-08-01, oldid=54780) + exhaustively verified against Zandronum source: declaration/parsing and error-recovery behavior (`src/thingdef/thingdef_parse.cpp:349-403` `ParseUserVariable`, `src/sc_man.cpp:888-925` `FScanner::ScriptError`/`ScriptMessage`, `src/thingdef/thingdef.cpp:357-359` deferred abort), per-class instance layout (`src/dobjtype.cpp:256-269` `PClass::CreateNew`, `:348-356` `PClass::Extend`), the DECORATE-side write path (`src/thingdef/thingdef_codeptr.cpp:5149-5202` `A_SetUserVar`/`A_SetUserArray`), the DECORATE-side bare-identifier read path (`src/thingdef/thingdef_expression.cpp:1841-1966` `FxIdentifier::Resolve`/`FxSelf`, `src/thingdef/thingdef_exp.h:70-73` `FCompileContext::FindInClass`, `src/thingdef/thingdef_expression.cpp:2093-2147` `FxClassMember`), the Weapon calling convention (`src/p_pspr.cpp:257` `P_SetPsprite`), the CustomInventory calling convention (`src/thingdef/thingdef_codeptr.cpp:128-181` `ACustomInventory::CallStateChain`, `src/g_shared/a_pickups.cpp:1818,1829,1838-1848` its Drop/Use/TryPickup call sites), and the ACS-side read/write gate (`src/p_acs.cpp:5593-5652`, cross-referenced in `../../acs/functions/getuservariable.md`). The feature predates the Zandronum 3.2.1 version-bump commit `28f736fb3` (introduced by the upstream-ported commit `57cff1f42`/`19b23f2cf`, confirmed an ancestor of the version-bump commit via `git merge-base --is-ancestor`) and is implemented entirely in Zandronum's own DECORATE compiler — nothing in this file depends on ZScript or any GZDoom/UZDoom-only mechanism.

User variables are custom integer fields you can declare on an actor in DECORATE to store per-instance state. They are guaranteed not to conflict with predefined engine fields, making them safe for mod-specific data storage.

## Declaration syntax

User variables are declared inside an actor definition with the keyword `var`:

```
actor MyMonster : ZombieMan
{
    var int user_my_health_boost;
    var int user_ammo_counter[10];

    // ... properties, flags, states ...
}
```

**Requirements:**
- **Type:** Must be `int` only. Zandronum's DECORATE parser rejects `float`, `string`, or other types, unlike the wiki's mention of float support — this is a Zandronum-only limitation. This is *not* an immediate hard abort: `ParseUserVariable` calls `sc.ScriptMessage("User variables must be of type int")` and increments `FScriptPosition::ErrorCounter`, then keeps parsing the rest of the file so any further errors are also reported in the same pass. DECORATE loading as a whole still fails: once every DECORATE lump has been parsed, `LoadDecorations()` checks `ErrorCounter > 0` and calls `I_Error("%d errors while parsing DECORATE scripts", ...)` (`src/thingdef/thingdef.cpp:357-359`) — a deferred-fatal, not a silent recovery.
- **Name:** Must start with the literal prefix `user_` (case-insensitive matching, enforced with `strnicmp("user_", name, 5)`). A non-matching name goes through the identical `ScriptMessage` + deferred-abort path described above, not a separate mechanism. The prefix exists to guarantee no collision with internal engine fields.
- **Native classes:** Unlike the three checks above, declaring *any* user variable on a native (not DECORATE-defined) class is an immediate hard abort, not deferred: `ParseUserVariable` calls `sc.ScriptError("Native classes may not have user variables")` when `!cls->bRuntimeClass`, and `FScanner::ScriptError` calls `I_Error` directly (`src/sc_man.cpp:888-904`) with no further parsing.
- **Arrays:** Optional bracket notation with a compile-time constant size, e.g. `var int user_array[42];`. A zero or negative size goes through the same soft `ScriptMessage` + deferred-abort path as the type/name checks above (`sc.ScriptMessage("Array size must be positive")`), and additionally the parser locally recovers by clamping the *declared* array to size 1 (`maxelems = 1;`) so scanning can continue and surface any later errors in the same file (`src/thingdef/thingdef_parse.cpp:376-386`). The clamp does not rescue the load — `ErrorCounter` is still nonzero, so the deferred `I_Error` check at the end of the DECORATE pass still aborts the whole load; there is no way to end up with a working size-1 array from this path.
- **Semicolon:** Declarations end with `;`, not a bare identifier line.

## Usage in expressions

User variables are readable in DECORATE action-function expressions — e.g., as parameters to action functions (`A_SetHealth(user_boost + 50)`, `A_Jump(256 - user_count / 2, "Special")`):

```
// Missile: check user_rockets via expression in A_Jump condition
POSS F 8 A_JumpIf(user_rockets > 0, "UseRocket")
    A_PosAttack
    Goto See

UseRocket:
    POSS E 10 A_CustomMissile("Rocket")
    A_SetUserVar("user_rockets", user_rockets - 1)
    Goto See
```

**Note:** DECORATE expressions in Zandronum do not support anonymous `{ statements; }` action blocks — those are a GZDoom-era ZScript feature. Inline code blocks do not exist; all logic must be structured via state jumps and action functions. See `state-machine.md` for the full list of Zandronum-unsupported extensions.

## Modification: action functions and ACS

User variables are written via:

- **DECORATE action functions:** `A_SetUserVar(varname, value)` and `A_SetUserArray(varname, index, value)`. Both look up `varname` in `self->GetClass()->Symbols` at runtime and check that the resolved symbol has the `bUserVar` flag (and the matching `int`/`int[]` type) before writing; failing either check produces a console message (`Printf("%s is not a user variable in class %s\n", ...)`, `src/thingdef/thingdef_codeptr.cpp:5149-5202`) and returns with no effect — never a crash.
- **ACS scripts:** `SetUserVariable(tid, varname, value)` and `SetUserArray(tid, varname, index, value)`, using the actor's thing ID. `GetUserVariable`/`GetUserArray` read them.

**The `bUserVar` gate applies on both sides, and is more fundamental than the `int`/`int[]` type restriction documented separately in the ACS-side doc.** The gate isn't "wrong type returns 0/no-ops" — it's "not a `user_`-declared field at all returns 0/no-ops," independent of type. A same-named native or DECORATE member field that isn't declared via `var int user_<name>;` (and so never has `bUserVar` set) is treated identically to a nonexistent name by all four functions. See `../../acs/functions/getuservariable.md` for the exact source trace (Zandronum's `GetUserVariable`/`GetUserArray` share one static C++ helper, so the finding applies to both, and the write side in `p_acs.cpp:5593-5621` applies the same gate).

## Conditions for Weapon and CustomInventory

The wiki describes special pickup/drop/store handling for weapons and `CustomInventory` items. The underlying mechanism for both is the same: DECORATE action functions and bare-identifier expressions are compiled/executed against **two different actor pointers**, `self` and `stateowner`, and which one ends up holding "the player/receiver" versus "the weapon/item" differs from the default (non-weapon, non-inventory) case where they're the same object.

**Default case (a plain actor's own states):** `FState::CallAction` is invoked as `newstate->CallAction(this, this)` (`src/p_mobj.cpp:586`) — `self` and `stateowner` are the same object, so there is no distinction to worry about; a bare identifier and `A_SetUserVar` both read/write that actor's own instance.

**Weapon states:** `P_SetPsprite` calls `state->CallAction(player->mo, player->ReadyWeapon)` (`src/p_pspr.cpp:257`) — **`self` is the player pawn, `stateowner` is the weapon object.** Every `DEFINE_ACTION_FUNCTION_PARAMS`-style action function (including `A_SetUserVar`/`A_SetUserArray`) receives `self` as its own local `self` parameter and operates on it, so `A_SetUserVar` called from a weapon's own state writes to **the player pawn**, not the weapon — this is the verified mechanism behind the wiki's "weapons... are never stored [on]" and "weapons may set the user variables on the player" claims. If the pawn's class doesn't have that `user_` field declared, the write silently no-ops with the "is not a user variable" console message described above.

**CustomInventory states:** `ACustomInventory::CallStateChain` invokes `State->CallAction(actor, this, &StateCall)` (`src/thingdef/thingdef_codeptr.cpp:135-181`), where `actor` is the receiving actor passed in by the caller and `this` is the `CustomInventory` item. The three call sites all pass the *receiver*, not the item, as `actor`: `TryPickup` passes `toucher` for the `Pickup` state (`src/g_shared/a_pickups.cpp:1838-1848`), `Use` passes `Owner` for the `Use` state (`:1829`), and `SpecialDropAction` passes `dropper` for the `Drop` state (`:1818`). So — same pattern as Weapon — **`self` is the receiving actor, `stateowner` is the item**, for all three of Pickup/Use/Drop. This matches the wiki's "user variables stored through DECORATE via... CustomInventory are set upon the owner itself" and explains the console-message claim ("if the receiver does not have the variable defined, it will log a console message") directly: it's the same `bUserVar`-lookup-on-`self`-fails-silently-with-a-message path as the Weapon case. The one part of the wiki's phrasing this doesn't literally match is "will only affect the item itself until picked up" — a `CustomInventory` item's *own* pre-pickup states (e.g. an idle `Spawn` loop, ticked normally like any other actor before it's touched) still run through the default `self == stateowner == this` path (`src/p_mobj.cpp:586`), so user variables read/written there do affect the item's own instance; it's specifically the `Pickup`/`Use`/`Drop` label chains (run via `CallStateChain`, not normal ticking) where `self` switches to the receiver.

**A genuine footgun this uncovers, not previously documented anywhere in this tree: bare-identifier *reads* inside a Weapon's or CustomInventory item's own state code are not safe even when the field is misused, unlike the write side.** A bare identifier (e.g. `user_rockets` in `A_JumpIf(user_rockets > 0, ...)`) resolves at **compile time** via `FxIdentifier::Resolve`'s `ctx.FindInClass(Identifier)` (`src/thingdef/thingdef_expression.cpp:1841-1863`), which is `cls->Symbols.FindSymbol(...)` where `cls` is the class currently being parsed (`src/thingdef/thingdef_exp.h:70-73`) — i.e. the *Weapon or CustomInventory item's own class*, since that's the class whose DECORATE body is being compiled. This produces an `FxClassMember` whose `membervar->offset` is a byte offset valid for **that item/weapon class's own instance layout** (each class's user-variable fields are appended to its own private `Size` via `PClass::Extend`, `src/dobjtype.cpp:348-356`, and every instance is allocated with exactly that class's `Size` bytes, `PClass::CreateNew`, `:256-269`). But at **runtime**, `FxSelf::EvalExpression` returns the `self` pointer verbatim (`src/thingdef/thingdef_expression.cpp:1960-1966`), and — per the Weapon/CustomInventory calling convention above — `self` at that point is the *player pawn or receiving actor*, a completely unrelated class with its own, differently-sized layout. `FxClassMember::EvalExpression` then computes `object + membervar->offset` (`:2137-2147`) using that mismatched pointer+offset pair. Concretely: if you declare `var int user_rockets;` on a Weapon (or CustomInventory item) and reference it as a bare identifier inside that same class's own state code, the read does not access "the weapon's own field" or get redirected to any pawn field of the same name — it reads whatever raw memory sits at the pawn/receiver's own address plus an offset computed for the weapon/item's layout, which is uninitialized/unrelated data at best and an out-of-bounds heap read at worst (if the weapon/item class's own `Size` is larger than the pawn/receiver class's `Size`). The write path (`A_SetUserVar`) does **not** share this bug, because it re-resolves the symbol at runtime against `self`'s *actual* class (`self->GetClass()->Symbols.FindSymbol`, `src/thingdef/thingdef_codeptr.cpp:5149-5166`) rather than trusting a compile-time-resolved offset — so a weapon/item-declared user variable, if absent from the pawn/receiver's own class, fails safely there instead. **Practical takeaway (matches the wiki's actual recommendation): declare the user variable on the player pawn or receiving actor's own class, never on the Weapon or CustomInventory item class** — this sidesteps both the write-side no-op and the read-side type confusion, since `self` is always the pawn/receiver by the time either path runs.

## See also

- `expressions.md` — identifier resolution and how user variables are read in DECORATE expressions
- `state-machine.md` — action-function calling convention and the `self`/`stateowner` distinction
- `crash-and-bug-checklist.md` — indexes the read-side type-confusion finding above
- `a_setuservar.md`, `a_setuservarfloat.md` — the DECORATE action functions for writing user variables
- `../../acs/functions/getuservariable.md` — ACS-side read gate (`bUserVar`), shared verbatim by `GetUserArray`; also links `SetUserVariable`/`SetUserArray`
