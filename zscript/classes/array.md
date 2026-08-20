# Dynamic arrays (`Array<T>`)

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki `Dynamic arrays` (retrieved 2026-08-03, https://zdoom.org/w/index.php?title=Dynamic_arrays&oldid=51251) + verified against UZDoom engine source (`wadsrc/static/zscript/engine/dynarrays.zs`, `src/common/scripting/core/dynarrays.cpp`, and `src/common/utility/tarray.h`); re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — no behavioral drift found. `dynarrays.zs`/`dynarrays.cpp` picked up only a mechanical license-header/whitespace update; `tarray.h` picked up unrelated internal refactoring (dropped the unused `TT` template parameter, `TDeletingArray`/`TMap` iterator changes, a new `SSize64`/`FindNoCase`) that does not touch any of the `Array<T>` methods documented here (`Push`, `PushV`, `Pop`, `Delete`, `Insert`, `ShrinkToFit`, `Grow`, `Resize`, `Reserve`, `Max`, `Clear`, `Find`, `Copy`, `Move`, `Append`) — their bodies and the `PushV` int32/String-only restriction are byte-for-byte unchanged.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Native struct template, implemented as `DynArray_I8`, `DynArray_I16`, `DynArray_I32`, `DynArray_F32`, `DynArray_F64`, `DynArray_Ptr`, `DynArray_Obj`, `DynArray_String`, and `DynArray_TRS` (engine source: `wadsrc/static/zscript/engine/dynarrays.zs` and `src/common/scripting/core/dynarrays.cpp`).

Dynamic arrays are resizable container objects that wrap the engine's `TArray` template, providing a complete set of methods for dynamic element management. They are available in ZScript only and do not exist in Zandronum.

## Supported element types

- **Signed integers:** `int8`, `int16`, `int32` (ZScript's `int` keyword maps to `int32`).
- **Floating-point:** `float` (32-bit) and `double` (64-bit).
- **Class references and pointers:** `Pointer` (untyped void pointers) and any actor/object class type.
- **Other:** `String` and the `TRS` struct (a transform-rotation-scale vector type).

Note: The wiki's list of "Double, Int, String, Pointer, and Class Types" is incomplete — the underlying implementation supports two distinct integer widths (int16 and int32) and two distinct floating-point widths (float and double) as separate array variants, plus additional types like `TRS` not mentioned in the wiki.

## Declaration and instantiation

Arrays can be declared as class members or inside function scope:

```zscript
class MyClass {
    Array<int> myArray;         // Class member
    
    void MyFunction() {
        Array<Actor> actorArray;  // Local variable
    }
}
```

Modern ZScript parsers (UZDoom 5.0.0-pre) correctly handle nested template closing brackets; the wiki's note about `Array<Class<Actor> >` requiring a space between the closing brackets is outdated — `Array<Class<Actor>>` works correctly.

## Core methods

All methods are available on every array type. The generic parameter `<T>` represents the element type.

### `int Size()` (read-only property)

Returns the current number of elements in the array. **Verified mechanism:** `Size` is a native read-only *field* aliased directly onto the underlying container's element count (bound via a field-registration macro, not a function-registration one) — it is not a real method at the native level. The ZScript compiler front-end additionally special-cases the name `Size` when it sees call syntax on a dynamic-array type, transparently rewriting `myArray.Size()` into the same field access as `myArray.Size`; both forms are valid and equivalent, but the underlying implementation is a field either way.

### `void Copy(Array<T> other)`

Replaces the calling array's contents with a copy of `other`'s contents.

### `void Move(Array<T> other)`

Transfers `other`'s data into the calling array and clears `other` in the process. This is more efficient than `Copy` when `other` will not be used afterward, as it avoids duplicating memory.

### `void Append(Array<T> other)`

Copies all elements from `other` and appends them to the end of the calling array.

### `int Find(T item)`

Searches for the first element equal to `item` and returns its index. **Returns `Size()` if the item is not found**, not `-1` or an error. To check if an item exists:

```zscript
if (myArray.Find(item) != myArray.Size()) {
    // Item found
}
```

### `int Push(T item)`

Appends `item` to the end of the array, expanding its size by one. Returns the index of the newly added element.

### `vararg uint PushV(T item, ...)`

Appends an arbitrary number of comma-delimited elements to the end of the array, expanding it by the count of arguments. **Available only for `int`/`int32` and `String` arrays.** Returns the index of the last appended element.

On integer arrays, floating-point values passed to `PushV` are converted to integers via truncation (not rounding). For example, `3.7` becomes `3`.

### `bool Pop()`

Removes and discards the last element, decreasing the array's size by one. Returns `true` on success, or `false` if the array was already empty (no error is thrown).

### `void Delete(uint index, int deletecount = 1)`

Removes `deletecount` elements starting at `index`. If the range extends past the end of the array, only the elements in range are deleted; excess parameters do not cause an error.

### `void Insert(uint index, T item)`

Inserts `item` at position `index`, shifting all elements at and after `index` to the right. The array implicitly grows to accommodate the new element. If `index` is beyond the current size, the gap is zero-filled.

### `void ShrinkToFit()`

Reduces the array's allocated memory to match its current size, discarding any unused reserved space.

### `void Grow(uint amount)`

Increases the array's allocated capacity by `amount` elements without changing the logical size. Newly allocated space is uninitialized.

### `void Resize(uint amount)`

Grows or shrinks the array to exactly `amount` elements. If shrinking, removed elements are destroyed. If growing, new elements are zero-initialized.

### `int Reserve(uint amount)`

Grows the array by `amount` new entries and returns the index of the first one. **Verified discrepancy:** unlike `std::vector::reserve`, this method **does change the logical size** — `Size()` increases by `amount` immediately, and the new entries are valid and indexable right away, not held back as unused capacity for a later size increase.

Because those slots are immediately indexable, whether they start out zeroed matters. This is not uniform across array types: for the plain numeric/pointer variants (`int8`/`int16`/`int32`/`float`/`double`/`Pointer`), the reserved entries are left with indeterminate contents — the engine does not guarantee they are zero, since no explicit clearing is performed for these types. Object arrays are the one variant that is explicitly guaranteed clear: their newly reserved entries are always set to `null` (required so the garbage collector never scans a stale, non-pointer value there). `String` and `TRS` arrays get properly default-constructed entries (an empty string / a default `TRS`), which are well-defined even though they aren't produced via an explicit zero-fill. In practice: write to a freshly reserved numeric/pointer entry before reading it; don't assume it starts at zero.

### `int Max()`

Returns the total number of allocated entries (capacity), including those not yet added to the logical size. This can be significantly larger than `Size()` after growth/reserve operations. **Caution:** Check `Size()` before using this value, as `Max() > Size()` is expected behavior.

### `void Clear()`

Removes all elements and reduces the array to size 0, destroying all contents.

## Null-checking for object arrays

When an object or pointer array contains a null reference, test the element directly without explicit null-checking overhead:

```zscript
Array<Actor> actors;
// ... populate array ...

if (actors.Size() > 0) {
    for (int i = 0; i < actors.Size(); i++) {
        if (!actors[i]) {
            Console.Printf("Detected null element at %d", i);
        }
    }
}
```

## Example

This example demonstrates a class that spawns and tracks explosive barrels, then detonates them when the spawning actor dies:

```zscript
class BarrelZombie : Zombieman {
    Array<Actor> barrels;

    override void Tick() {
        super.Tick();
        if (health > 0 && !isFrozen() && GetAge() % 70 == 0) {
            let bar = Spawn('ExplosiveBarrel', pos, ALLOW_REPLACE);
            if (bar) {
                barrels.Push(bar);
            }
        }
    }

    override void Die(Actor source, Actor inflictor, int dmgflags, Name MeansOfDeath) {
        for (int i = 0; i < barrels.Size(); i++) {
            let bar = barrels[i];
            if (bar && bar.health > 0) {
                bar.DamageMobj(self, self, bar.health, 'normal');
            }
        }
        super.Die(source, inflictor, dmgflags, MeansOfDeath);
    }
}
```

## Wiki/engine divergence

1. The wiki's claim that `Array<Class<Actor> >` requires a space between the closing angle brackets is outdated. **Verified against the ZCC grammar** (`src/common/scripting/frontend/zcc-parse.lemon`): the parser lexes `>>` as a single right-shift token and has a dedicated grammar rule that closes two levels of nested generic brackets from it, so `Array<Class<Actor>>` is valid without a space.

2. Not present on the wiki page this file is derived from, but worth flagging here: the `Reserve()` and `Size()` entries above each carry a "Verified discrepancy"/"Verified mechanism" note describing behavior that isn't how a reader familiar with `std::vector`-style containers would expect a "reserve" or a "size property" to work. See those entries for detail.
