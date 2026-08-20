# ZScript statements

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki `Statements` page (retrieved 2026-08-03, https://zdoom.org/w/index.php?title=Statements&oldid=54863) + verified against the UZDoom source's `src/common/scripting/frontend/zcc-parse.lemon` parser grammar and `src/common/scripting/backend/codegen.cpp` runtime implementation; re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — no behavioral drift found
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

ZScript statements are the code-flow constructs that control execution logic within code blocks. Statements can also be used in DECORATE anonymous functions.

## if/else conditionals

IF statements execute a block conditionally based on a boolean expression. The ELSE block is optional. ELSE IF chains allow testing multiple conditions in sequence.

```zscript
if (condition) {
    // execute if condition is true
} else if (otherCondition) {
    // execute if first condition is false and otherCondition is true
} else {
    // execute if all conditions are false
}
```

The ELSE block can be omitted entirely, or omitted if the IF block ends with a `return`.

## switch statements

SWITCH statements dispatch to different code blocks based on a case value. A `name`-typed condition is left as-is; any other numeric condition is cast to `int` (non-numeric types like `string` or object pointers are not permitted in switch conditions). Each CASE block must end with `break` unless a fall-through to the next case is desired.

```zscript
switch (value) {
    case 0:
        DoThing1();
        break;
    case 1:
        DoThing2();
        break;
    default:
        DoThing3();
        break;
}
```

`name` values can be used directly as case values; a case label's value type must match the switch condition's type.

## for loops

FOR loops execute code repeatedly while incrementing/decrementing a counter variable. The basic form is `for (initialization; condition; increment)`.

```zscript
for (int i = 0; i < 10; i++) {
    // executes 10 times
}
```

The counter can be a pre-existing variable (which will be modified during and after the loop) or declared within the loop. Pre- and post-increment operators (`++i` vs `i++`) differ in when the value is tested against the loop condition, and this matters only if the counter is used after the loop.

FOR loops support `break` to terminate early and `continue` to skip to the next iteration.

### Iterating over arrays

FOR loops commonly iterate over array contents by index:

```zscript
for (int i = 0; i < myArray.Size(); i++) {
    let item = myArray[i];
    if (item) {
        // do something
    }
}
```

When iterating backward (to safely delete items), declare the counter as `int` (`Array.Size()` returns a signed `int`) and start at `Size() - 1`, testing `i >= 0` as the loop condition so index `0` is still visited.

### Iterating over linked lists

Linked lists (like an actor's inventory chain) can be traversed by following pointer chains:

```zscript
for (let item = actor.Inv; item != null; item = item.Inv) {
    // do something with item
}
```

## while and do-while loops

WHILE loops execute code repeatedly as long as a condition remains true. DO-WHILE tests the condition after executing the block, so the block always executes at least once.

```zscript
while (condition) {
    // executes while condition is true
}

do {
    // executes first, then checks condition
} while (condition);
```

Both loop types support `break` to terminate and `continue` to skip to the next iteration (or, for do-while, to skip to the condition check).

## foreach loops

FOREACH is a ZScript-specific loop construct for iterating over arrays, dynamic arrays, and iterator objects without manual indexing. Several forms exist:

**Single-variable form** (iterates a dynamic array forward, from index 0; also works on a Map to visit values only, and on an iterator object to visit its default result type):
```zscript
Array<Actor> things;
foreach (mo : things) {
    if (mo) { /* do something */ }
}
```

**Key-value form** (for associative maps):
```zscript
Map<Name, Actor> things;
foreach (k, v : things) {
    console.printf("Key %s is type %s", k, v.GetClassName());
}
```

**Iterator forms** (for BlockThingsIterator, BlockLinesIterator, ThinkerIterator, ActorIterator, BehaviorIterator):
```zscript
// Typed form: casts each result to the named subclass instead of the
// iterator's default type (here, Actor)
foreach (Key item : ThinkerIterator.Create('Key')) {
    // do something
}

// Three-argument iterator (BlockThingsIterator, BlockLinesIterator only)
foreach (thing, pos, flags : BlockThingsIterator.Create(origin, radius)) {
    console.printf("Thing type: %s", thing.GetClassName());
}
```

**Typed form** (specifies the iteration variable type explicitly; also usable on a plain array to fix the loop variable's type):
```zscript
foreach (Actor mo : thingList) {
    // do something
}
```

**Caveat:** A single-variable foreach over an array captures the array's size once at loop entry, and its per-element access has its runtime bounds check disabled (the compiler assumes the captured size is still accurate). Calling Delete, Clear, Pop, etc. on the array during the loop is not flagged as an error but can shrink it below the captured size, producing an unchecked out-of-bounds read. Use a FOR loop iterating backward if dynamic removal is needed.

## break and continue

BREAK terminates FOR, WHILE, DO-WHILE, or FOREACH loops immediately (does not exit the enclosing function).

CONTINUE skips the current iteration and proceeds to the next one in FOR, WHILE, DO-WHILE, or FOREACH loops.

## return

RETURN exits the current function immediately and optionally provides a return value. In void-returning functions, RETURN is optional and only needed to exit early. In typed-return functions, RETURN must provide a value of the matching type.

```zscript
int GetValue() {
    return 42;
}

void EarlyExit() {
    if (condition) {
        return;  // exit early, void function
    }
    // more code
}
```

RETURN terminates the entire function, not just a loop — use BREAK to exit only a loop.

For a function declared with multiple return types, RETURN takes a comma-separated list of values, one per declared return type:

```zscript
int, int GetPair() {
    return 1, 2;
}
```
