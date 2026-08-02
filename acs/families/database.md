# Database family

**Tier:** A for all fifteen — wiki-derived and source-verified 2026-07-29.
**Engine:** Zandronum 3.2.1 (verified against the Zandronum source `master` HEAD — see "Engine scope" in `../../shared/AUTHORING.md` for the version-gap caveat).
**Provenance:** wiki page `Database - Zandronum Wiki.html` (`?oldid=1276`, saved 2026-07-29) + source-verified against the Zandronum source (`p_acs.cpp:5473-5490,7225-7371`, `za_database.cpp` in full, `za_database.h`).
**Bucket:** all fifteen are extension functions (negative index in `zcommon.bcs`), semantics in the Zandronum source's `src/p_acs.cpp` (`case ACSF_*DBEntr*`/`ACSF_*DBResult*`/`ACSF_*DBTransaction`, around line 7225-7371) which thinly wrap the Zandronum source's `src/za_database.cpp` (`DATABASE_*`), the actual SQLite layer. Indices -108 to -125 (`zcommon.bcs:1741-1758`, with -113 and -114 reserved/unused between `IncrementDBEntry` and `SortDBEntries`, and -122 reserved between `GetDBEntryRank` and `BeginDBTransaction`).

`SetDBEntry`, `GetDBEntry`, `SetDBEntryString`, `GetDBEntryString`, `IncrementDBEntry`,
`GetDBEntryRank`, `GetDBEntries`, `SortDBEntries`, `CountDBResults`, `GetDBResultKeyString`,
`GetDBResultValueString`, `GetDBResultValue`, `FreeDBResults`, `BeginDBTransaction`,
`EndDBTransaction` — a Zandronum-only SQLite-backed key/value store, addressed by
`(namespace, key)` pairs. Grouped as one family because the query functions
(`GetDBEntries`/`SortDBEntries`) return an opaque **result handle** that only the
`GetDBResult*`/`CountDBResults`/`FreeDBResults` functions can consume — none of those five are
meaningful in isolation, same shape as [Lump I/O](lump-io.md).

All fifteen are documented below regardless of real-world usage — see the family-coverage rule in
`../../shared/AUTHORING.md`'s Authoring rule section (an unused family is exactly the one nobody has figured out
yet), and because the persistence/availability gotchas below aren't guessable from the wiki page
alone.

---

## The database itself isn't guaranteed to persist — read this before anything else

The wiki's framing ("allowing you to persist data across server restarts") describes the
*intended use case*, not the default state. Whether writes survive a restart is entirely a
server-config question, invisible from ACS:

- Backing store is `CUSTOM_CVAR(String, databasefile, ":memory:", CVAR_ARCHIVE|CVAR_NOSETBYACS)`
  (`za_database.cpp:68`) — **the default value is `:memory:`**, an in-memory SQLite database that
  is silently discarded on server exit. Nothing in ACS can detect or change this: the cvar is
  `CVAR_NOSETBYACS`, so it can only be set from the server config/console, not from a script.
  Persistence requires the server operator to have pointed `databasefile` at a real file path.
- If `databasefile` is set to an **empty string**, no database is opened at all
  (`DATABASE_Init`, `za_database.cpp:213-241`) — every read function then silently returns its
  empty-result default (see below) and every write is a no-op, with only a console `Printf`
  (`"<Function> error: No database.\n"`, `DATABASE_IsAvailable`) as any indication — nothing
  script-visible signals the failure.
- Because none of this is queryable from ACS, a script using this family cannot itself
  distinguish "namespace/key genuinely has no entry" from "there is no database backing it at
  all" — both produce the same default return values.

## Data retrieval and saving

### `void SetDBEntry(str namespace, str key, int value)` / `void IncrementDBEntry(str namespace, str key, int value)`

Both funnel through `DATABASE_SaveSetEntry`/`DATABASE_SaveIncrementEntryInt`
(`za_database.cpp:447-509`), which store the value as `CAST(... AS INTEGER)`-compatible text in a
single SQLite table (`Namespace text, KeyName text, Value text, Timestamp text, PRIMARY KEY
(Namespace, KeyName)`, `DATABASE_CreateTable`) — there is exactly one physical table for the
whole database; "namespace" is a column value, not a separate SQLite table, so `GetDBEntries`
scanning a namespace is a `WHERE Namespace=?` scan, not a per-namespace table lookup.

- **`SetDBEntry(ns, key, 0)` does *not* delete the entry.** The delete-on-empty rule
  (`DATABASE_SaveSetEntry`, `za_database.cpp:452-462`) only fires when the *formatted string* is
  empty — `SetDBEntry` always formats the int as `"%d"` first (`DATABASE_SaveSetEntryInt`), so
  `0` becomes the non-empty string `"0"` and is stored normally. Only `SetDBEntryString(ns, key,
  "")` — an actual empty string argument — triggers the delete path. This asymmetry between the
  int and string setters isn't on the wiki.
- `IncrementDBEntry` on a key that doesn't exist yet creates it with value `value` (not
  `0 + value` via a separate insert-then-update — same net effect, just note there's no implicit
  zero-row read).
- Both return `1` in the engine (`p_acs.cpp:7225-7255`) despite `zcommon.bcs` declaring them
  `void` — irrelevant to BCS callers since a `void`-declared call can't read a return value
  anyway.

### `int GetDBEntry(str namespace, str key)` / `str GetDBEntryString(str namespace, str key)`

Both funnel through `DATABASE_SaveGetEntry` (`za_database.cpp:476-485`), which returns `""` if
the entry doesn't exist **or** if there's no database at all — `GetDBEntry` then converts that
via `.ToLong()`, so a missing entry and a database-unavailable condition both silently read back
as **`0`** (int form) or **`""`** (string form). There's no distinct error return to check
against.

## Iteration and sorting

### `int GetDBEntryRank(str namespace, str key, bool descending)`

`DATABASE_GetEntryRank` (`za_database.cpp:513-539`) computes rank as `1 + COUNT(*)` of other rows
in the same namespace with a strictly lower (`descending=false`) or strictly higher
(`descending=true`) value — i.e. **rank via strict inequality, not row position**. Tied values
all receive the *same* rank (e.g. three entries tied for the best score in a namespace all rank
`1`), which the wiki's phrasing ("return the position of the given key") doesn't make clear.
Returns **`-1`** if the key doesn't exist or the database is unavailable — this is a real sentinel
here, unlike the `0`-default the plain get functions use.

### `int GetDBEntries(str namespace)` / `int SortDBEntries(str namespace, int limit, int offset, bool descending)`

Both allocate a new slot in a global result vector (`g_dbQueries`, `p_acs.cpp:7280-7371`) and
return its index as the "resource" handle — despite the wiki's `resource` pseudo-type, the BCS
signature (`zcommon.bcs:1748,1758`) is a plain `int`. `GetDBEntries` returns rows in whatever
order SQLite's table scan yields (**not sorted by value**); use `SortDBEntries` if order matters.
`SortDBEntries`'s `offset` is a plain SQL `OFFSET` — the wiki's "a value of 1 will cause the
returned database to start at the second highest value" phrasing is just describing standard
`LIMIT n OFFSET m` semantics, not a family-specific quirk.

**Handle lifetime gotcha, not on the wiki:** `FreeDBResults` (`p_acs.cpp:7296-7306`) only shrinks
`g_dbQueries` when you free the **most-recently-allocated** (highest-index) handle still live —
freeing any earlier handle just clears its own entry in place and leaves the vector's tail
untouched. Handles are never reused for a later `GetDBEntries`/`SortDBEntries` call regardless
(every call does `g_dbQueries.resize(size+1)` and takes the new trailing slot) — so failing to
free in strict LIFO order doesn't corrupt anything, but it does mean stale empty slots accumulate
in `g_dbQueries` for the rest of the game session instead of being reclaimed.

### `int CountDBResults(int handle)`

Returns `-1` for an out-of-range handle (`p_acs.cpp:7287-7294`) — distinct from the `0`
"namespace matched zero rows" case. Check for `-1` specifically before assuming an empty result.

### `str GetDBResultKeyString(int handle, int row)` / `str GetDBResultValueString(int handle, int row)`

**Gotcha, not on the wiki:** on failure these return the literal strings `"Invalid handle"` (bad
`handle`) or `"Invalid index"` (bad `row`) — not an empty string (`p_acs.cpp:7308-7330`). Code
that doesn't validate against `CountDBResults` first and just prints/stores the result can end up
displaying or persisting that literal text as if it were real data.

### `int GetDBResultValue(int handle, int row)`

Unlike its string sibling, this one degrades silently: returns `0` for an out-of-range `handle`
or `row` (`p_acs.cpp:7332-7342`), indistinguishable from a genuinely-stored value of `0`.

## Transactions

### `void BeginDBTransaction()` / `void EndDBTransaction()`

Thin wrappers issuing raw `BEGIN TRANSACTION`/`END TRANSACTION` to SQLite
(`za_database.cpp:267-283`) — **not reentrant/nestable**. SQLite itself rejects a second `BEGIN`
before a matching `END`/`COMMIT`; the resulting SQLite error goes to the console
(`sqlite3_exec` failure path in `database_ExecuteCommand`) and is not surfaced to the calling
script in any way. If the database is unavailable, both are silent no-ops. The wiki's
performance/atomicity claims (batch writes are faster than per-row writes; a crash mid-transaction
either commits everything or nothing) are standard SQLite transaction semantics and check out —
not a fork-specific embellishment.

## "Stops the entire gamesim" claim

Confirmed by source shape, not just wiki assertion: every `ACSF_*DB*` case calls straight into
synchronous `sqlite3_*` calls (`za_database.cpp`) with no threading or async queuing anywhere in
this file. Since ACS executes inline in the single-threaded game tic, any of these functions
blocks the entire simulation for as long as the underlying SQLite call takes — the wiki's warning
about batching writes into a transaction to avoid stalls is accurate advice, not folklore.
