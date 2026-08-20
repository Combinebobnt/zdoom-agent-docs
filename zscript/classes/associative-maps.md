# Associative maps: `Map<K,V>` and `MapIterator<K,V>`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki `Associative maps` (retrieved 2026-08-03, https://zdoom.org/w/index.php?title=Associative_maps&oldid=55343) + verified against the UZDoom source's `src/common/scripting/core/maps.h` and `src/common/scripting/core/maps.cpp`; re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — no behavioral drift found for Map/MapIterator.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** native structs — `ZSMap<KT,VT>` and `ZSMapIterator<KT,VT>` in the UZDoom source's `src/common/scripting/core/maps.h`, with all methods registered via `DEFINE_ACTION_FUNCTION_NATIVE` macro expansions in `src/common/scripting/core/maps.cpp`. Neither type is defined in the ZScript standard library (`wadsrc/static/zscript/`).

Associative maps are type-safe, generic key-value containers. They succeed ZScript's earlier `Dictionary` class by supporting typed keys and values beyond simple strings, though with a fixed type-combination whitelist rather than arbitrary types.

## Declaration

```zscript
Map<KeyType, ValueType> myMap;
```

### Supported key and value types

The actual implementation defines exactly 16 map specializations (2 key types × 8 value types), each paired with a matching iterator specialization, for 32 concrete native types total, corresponding to:

- **Keys:** `int` (uint32_t) or `string` (FString)
- **Values:** `int8`, `int16`, `int32`, `float`, `double`, `DObject*`, `void*`, or `string`

A request for an unsupported combination (e.g., `Map<int, class<Actor>>` where the wiki's own example claims they don't work) **will not compile**.

## Map methods

### Lifecycle and contents

**`void Clear()`**
Removes all entries, invalidating live iterators.

**`uint CountUsed() const`**
Returns the number of key-value pairs currently stored. Does not invalidate iterators.

**`void Copy(out Map<KeyType, ValueType> other)`**
Replaces this map's contents with a copy of `other`'s contents. Invalidates live iterators on *this* map only — `other` is only read, its own revision counter is untouched, so iterators already live on `other` remain valid.

**`void Move(out Map<KeyType, ValueType> other)`**
Transfers `other`'s contents into this map, leaving `other` empty. Invalidates live iterators on both maps.

**`void Swap(out Map<KeyType, ValueType> other)`**
Exchanges the contents of both maps. Invalidates live iterators on both maps.

### Key lookup and access

**`bool CheckKey(KeyType key) const`**
Returns `true` if `key` exists, `false` otherwise. Does not insert or invalidate iterators.

**`ValueType Get(KeyType key)`**
Returns the value for `key`. If `key` does not exist, inserts a default-constructed value for `key` and **invalidates live iterators**. The return of a default value on a missing key is the signature behavior that distinguishes this from `GetIfExists`.

**`ValueType GetIfExists(KeyType key) const`**
Returns the value for `key` if it exists, or a default-constructed value if it does not. Unlike `Get`, **does not insert a new entry**, and does not invalidate iterators.

**`ValueType, bool CheckValue(KeyType key) const`**
Combination of `CheckKey` and `GetIfExists`: returns the value for `key` and a boolean `true`/`false` indicating whether the key exists. Does not insert or invalidate iterators.

### Insertion and removal

**`void Insert(KeyType key, ValueType value)`**
Sets `key` to the given `value`, replacing any prior value. Invalidates live iterators.

**`bool InsertNew(KeyType key)`**
**Returns `void` (the wiki lists this as returning `bool`, which is incorrect).** Sets `key` to an empty default-constructed value, replacing any prior value. Invalidates live iterators.

**`void Remove(KeyType key)`**
Removes `key` if it exists. Invalidates live iterators. Has no effect if `key` is not present.

### Critical: mutation via `Get` and iterator invalidation

Every mutator operation — `Insert`, `InsertNew`, `Remove`, `Clear`, `Copy`, `Move`, `Swap` — **invalidates all live iterators on the map it's called on** by incrementing that map's internal revision counter (`Move` and `Swap` bump the counter on *both* maps involved since both maps' contents actually change; `Copy` only bumps the counter on the map being written to, not on the source map passed in, since the source is only read — see its own entry above). Crucially, **a seemingly-read-only call to `Get` is a mutator** because it inserts a default value on a missing key. If you call `Get` on a non-existent key while iterating, the iterator becomes invalid. Use `GetIfExists`, `CheckValue`, or `CheckKey` instead to test or read during iteration. An invalid iterator throws a `ThrowAbortException` with message "MapIterator::<method> called from invalid iterator" or "...called from invalid position" when methods like `Next` or `GetValue` are invoked.

## MapIterator methods

**`bool Init(Map<KeyType, ValueType> other)`**
Initializes this iterator for `other`. Returns `true` if initialization succeeded (the map exists), `false` otherwise. **Must call `Next()` before reading any values** — `Init` advances to the *start* of the sequence, not to the first element.

**`bool ReInit()`**
Restarts iteration on the same map. Returns `true` if the map still exists (wasn't deleted), `false` otherwise. Again, **must call `Next()` before reading**.

**`bool Valid()`**
Returns `true` if the iterator is in a valid state. An iterator becomes invalid if the underlying map is modified (via `Insert`, `Remove`, `Clear`, etc.), or if the map is deleted. This is the check to make before calling `Next`, `GetKey`, or `GetValue`.

**`bool Next()`**
Advances the iterator to the next entry and returns `true` if an entry exists at the new position, `false` if iteration is complete. On an invalid iterator, throws an exception with message "MapIterator::Next called from invalid iterator". **Throws an exception if called on an iterator that has not yet been initialized** (e.g., directly after `Init` or `ReInit`, before the first `Next()` call).

**`KeyType GetKey()`**
Returns the key at the current iterator position. **Only safe to call after `Next()` returns `true`.** On an invalid iterator or invalid position, throws an exception with message "MapIterator::GetKey called from invalid iterator" or "...called from invalid position".

**`ValueType GetValue()`**
Returns the value at the current iterator position. **Only safe to call after `Next()` returns `true`.** Throws the same exceptions as `GetKey` on invalid state.

**`void SetValue(ValueType value)`**
Sets the value at the current iterator position to the given `value`. **Only safe to call after `Next()` returns `true`.** Does not invalidate the iterator (mutating the *value* for an existing key is not the same as inserting or removing keys).

## Alternative iteration: foreach

The wiki documents a `foreach` syntax for iterating over maps:

```zscript
foreach(key, value : myMap) { /* ... */ }
foreach(value : myMap) { /* ... */ }
foreach(key, value : myIterator) { /* ... */ }
foreach(value : myIterator) { /* ... */ }
```

This feature is implemented at the ZScript compiler level (the code generator that resolves `foreach` loop nodes), not in `maps.cpp`, and its desugaring has been confirmed against the local UZDoom checkout. `foreach(value : myMap)` and `foreach(key, value : myMap)` over a `Map` both compile down to a hidden local `MapIterator` variable, a call to its `Init` method, and a `while` loop on `Next` that assigns `GetKey`/`GetValue` into the loop variables each pass — equivalent to the manual `MapIterator` pattern shown below, just compiler-generated. Passing a `MapIterator` directly to `foreach` (`foreach(key, value : myIterator)` / `foreach(value : myIterator)`) instead compiles to a call to that iterator's own `ReInit` guarding a `while (Next())` loop, reusing the passed-in iterator rather than declaring a new one. The single-value form (`value` only, no `key`) simply omits assigning the key each pass; it still walks every entry.

## Examples

A simple map counting actor class occurrences:

```zscript
class ActorCounter : Thinker
{
	Map<string, int> counts;

	void CountActor(string className)
	{
		int existing = counts.GetIfExists(className);
		counts.Insert(className, existing + 1);
	}

	static int GetCount(string className)
	{
		ThinkerIterator it = ThinkerIterator.Create('ActorCounter');
		let counter = ActorCounter(it.Next());
		if (!counter) return 0;
		return counter.counts.GetIfExists(className);
	}
}
```

Iterating with a `MapIterator`:

```zscript
Map<string, int> testMap;
testMap.Insert("first", 1);
testMap.Insert("second", 2);
testMap.Insert("third", 3);

MapIterator<string, int> it;
it.Init(testMap);

// Must call Next() once before reading the first entry
while (it.Next()) {
	Console.Printf("key='%s' value=%d\n", it.GetKey(), it.GetValue());
}
```

**Note on `Get` vs. `GetIfExists` during iteration:**

This example **will corrupt the iteration** because `Get` on a missing key inserts a default value and invalidates the iterator:

```zscript
Map<string, int> testMap;
testMap.Insert("key1", 100);

MapIterator<string, int> it;
it.Init(testMap);

while (it.Next()) {
	// BAD: calling Get on a non-existent key invalidates the iterator
	int val = testMap.Get("missing");  // Inserts "missing" -> 0, bumps revision
	// Iterator is now invalid; next iteration is undefined behavior
}
```

Use `GetIfExists` or `CheckValue` instead:

```zscript
MapIterator<string, int> it;
it.Init(testMap);

while (it.Next()) {
	// GOOD: GetIfExists doesn't mutate
	int val = testMap.GetIfExists("missing");  // Returns 0, doesn't insert, iterator still valid
}
```
