# CheckActorClass

**Tier:** A
**Engine:** Zandronum 3.2.1 (verified against 3.3-alpha checkout)
**Provenance:** `CheckActorClass - ZDoom Wiki` (oldid=37309), verified against Zandronum source 2026-07-29
**Bucket:** Extension function (`zcommon.bcs` index -27, dispatches to `case ACSF_CheckActorClass` in `p_acs.cpp:6202`)

**Syntax:** `bool CheckActorClass(int tid, str class)`

---

## Description

Compares an actor's class type name against a provided string and returns true only if they match.

### Parameters

- **`tid`**: Target actor's thing ID. Use `0` to refer to the activator.
- **`class`**: Class name string to match against the actor's class type. Comparison is **case-insensitive** (verified via `FName`'s internal `stricmp` matching).

### Return value

`true` if the actor's class name matches the provided string, `false` otherwise.

The function returns `false` in three distinct but silent scenarios:
1. The actor's class name genuinely does not match the provided string.
2. Nonzero `tid` matches no actor (null lookup result).
3. `tid == 0` and the activator is `NULL` (e.g., in `OPEN` scripts).

These cases cannot be distinguished by the return value alone.

### Behavior details

- **TID resolution:** Uses `SingleActorFromTID(tid, activator)`, which means only the **first actor** matching a nonzero `tid` is checked; if multiple actors share the same TID, the others are not tested. Iteration order is undefined (engine-internal). For `tid == 0`, returns the activator or `NULL`.

- **Case sensitivity:** The class name comparison is **case-insensitive**. `CheckActorClass(tid, "doomimp")`, `CheckActorClass(tid, "DoomImp")`, and `CheckActorClass(tid, "DOOMÍMP")` are all equivalent. This is transparent to the script — the wiki does not document it — but is verified via the engine's `FName` name-table implementation, which normalizes lookups via `stricmp` before index comparison.

- **Bad string index:** If `args[1]` (the class string) is an invalid string-table index, `FBehavior::StaticLookupString` returns `NULL`. This is safe: `FName(NULL)` in the `FName(const char *)` constructor routes to `FindName(NULL, false)`, which has an explicit `if (text == NULL) return 0` guard, degrading to a `NAME_None` comparison. The function returns `false` rather than crashing.

- **Nonzero `tid` TID mismatches:** Unlike the `Get/SetActorX/Y/Z` family, there is **no fallback to activator** when a nonzero TID matches no actor — the lookup simply returns `NULL` and the function returns `false`.

### Related functions

- **`GetActorClass`** (index -68): Companion getter, returns the actor's class name as a string. **Diverges on the NULL-actor path:** returns the literal string `"None"` instead of `false`. See [notes on non-mandatory-sequence families](#family-note) below.

---

## Wiki notes

The wiki page is feature-complete and accurate in its core description. However, it has two defects in the published code examples:

1. **Negative array index in the third example:** The switch statement at line `switch (monster_msg[class_index][MONST_CLASS_NAME])` accesses the array **before** the `if (class_index > -1)` guard. When no class matches, `class_index` remains `-1`, resulting in a negative array index (`monster_msg[-1][...]`), which is undefined behavior in most contexts. This is the same class of defect already documented for `LumpRead`'s swapped argument order in the [lump-io family](families/lump-io.md). **The guard and the array access should be swapped.**

2. **String switch statement:** The same switch statement in the third example uses `switch (monster_msg[class_index][MONST_CLASS_NAME])`, where the switched variable is a `str`. BCS switch statements do not support string operands — they require integer types. The wiki example should either use a sequence of `if/else` statements or restructure to switch on an integer (e.g., `class_index`). This is a toolchain incompatibility, not a Zandronum fork divergence, but it prevents the example from compiling as written.

---

## Family note

`CheckActorClass` and `GetActorClass` (index -68) are adjacent in the engine's `EACSFunctions` enum (positions 27 and 68) and are both type-related actor queries dispatching through the same `SingleActorFromTID` helper. However, they are **not a mandatory-sequence pair** — each is independently usable without the other, so they are documented separately in `functions/` rather than consolidated into a `families/` file. A family file would be justified only if they were mutually dependent (e.g., Open/Read/Close lump operations) or if divergence on an edge case (like `GetActorClass` returning `"None"` vs. `CheckActorClass` returning `false` on NULL) warranted shared documentation. See `CLAUDE.md` for layout rationale.

---

## Code references

- **Engine implementation:** the Zandronum source's `src/p_acs.cpp:6202-6206` (the case block)
- **Declaration:** the zt-bcc source's `lib/zcommon.bcs:1655`
- **FName name-table matching:** the Zandronum source's `src/name.cpp:91-124` (case-insensitive `stricmp` matching in `FindName`)
- **FName equality operator:** the Zandronum source's `src/name.h:75` (index-based comparison after case-insensitive lookup)
