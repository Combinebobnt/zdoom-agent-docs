# ZScript special words

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki `ZScript special words` (retrieved 2026-08-03, https://zdoom.org/w/index.php?title=ZScript_special_words&oldid=53287) + verified against the UZDoom source's `src/common/scripting/frontend/zcc-parse.lemon` (parser grammar for `is`, `let`, `out`, `&`, `dot`, `cross`) and `wadsrc/static/zscript/` (usage of `self` and `invoker` in action functions); re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — no behavioral drift found.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

ZScript defines several keywords that enable type inference, reference parameters, vector operations, and special context references within action functions.

## `is` — type checking and inheritance

The `is` operator compares a pointer or class type against another class type, returning true if the value is an instance of (or derived from) the specified class:

```zscript
if (mobj is "ClassName")
{
    // mobj is an instance of ClassName or a subclass
}

if ("ClassC" is "ClassA")
{
    // true if ClassC is derived from ClassA
}
```

This operator works both on object instances (checking the object's dynamic type) and on class-type values (checking class-hierarchy membership) — both forms are evaluated by the VM at runtime, including when both operands are literal class-type expressions like `"ClassC" is "ClassA"`; there is no compile-time constant-folding of `is`. It returns `true` for the target class and any of its descendants.

## `let` — type inference from initializers

The `let` keyword declares a variable whose type is inferred from its initial value, eliminating the need to write explicit types:

```zscript
let a = 1;                          // inferred as int
let b = self.Owner;                 // inferred as Actor
let c = 1.25;                       // inferred as double
let d = "Hello, world!";            // inferred as String
let e = FindInventory("Clip");      // inferred as Inventory
```

### Multi-value assignment with `let`

When a function returns multiple values as a tuple, you can destructure the result into multiple variables using square brackets:

```zscript
let [success, newActor] = A_SpawnItemEx(...);
// success is inferred as bool, newActor as Actor
```

### `let` with a cast expression as the initializer

`let` is not itself a casting mechanism — it only ever infers a variable's type from whatever expression initializes it, same as `let a = 1;` above. If that initializer happens to be an explicit type cast (ZScript uses C++-style function-call casting syntax, e.g. `Inventory(someObject)`, since C-style `(Type)expr` casts aren't supported due to parsing conflicts), `let` simply infers the variable's type from the cast's result type — the same declaration works with an explicit type in place of `let`:

```zscript
let inventoryItem = Inventory(someObject);
// inventoryItem's type is inferred as Inventory, from the cast expression's result type.
// If someObject is an Inventory instance, inventoryItem holds the reference.
// If someObject is of a different class, inventoryItem becomes null.
```

## `out` and `&` — pass-by-reference parameters

Both `out` and `&` declare a function parameter as pass-by-reference, allowing the function to modify the caller's value directly. They are equivalent in both meaning and behavior:

```zscript
void ModifyByRef(out MyStruct s)
{
    s.value = 5;  // modifies the original struct, not a copy
}

void ModifyByRefAlt(MyStruct &s)
{
    s.value = 5;  // same behavior, alternative syntax
}
```

The reference syntax is particularly useful for structs, which are value types in ZScript and would otherwise be passed by copy. Both `out` and `&` enforce pass-by-reference, preventing unnecessary copying:

```zscript
void ProcessArray(array<Actor> &ArrayName)
{
    // ArrayName is modified in place
}
```

## `dot` — vector dot product

The `dot` operator calculates the dot product of two vectors, returning a `double`. Both operands must be the same vector type — Vector2, Vector3, or Vector4:

```zscript
Vector2 a = (1, 0);
Vector2 b = (0, 1);
double result = a dot b;  // returns 0 (orthogonal vectors)

Vector3 x = (1, 2, 3);
Vector3 y = (3, 2, 1);
double dp = x dot y;      // returns 1*3 + 2*2 + 3*1 = 10
```

The dot product result encodes the angle between vectors:
- **0** means the vectors are orthogonal (90 degrees apart).
- **1** means they are parallel (pointing the same direction), for unit vectors.
- **-1** means they are antiparallel (pointing opposite directions), for unit vectors.
- **Negative values** indicate the vectors point generally opposite directions (angle > 90 degrees).

## `cross` — vector cross product

The `cross` operator calculates the cross product of two Vector3s, returning a new Vector3 perpendicular to both inputs. The `cross` operator is **not supported for Vector2**:

```zscript
Vector3 a = (1, 2, 3);
Vector3 b = (3, 2, 1);
Vector3 result = a cross b;
// result is perpendicular to both a and b
```

If either input is a zero vector or the two vectors are parallel (or antiparallel), the result is a zero vector. The magnitude of the cross product is `|a| * |b| * sin(angle)`, where angle is the angle between the vectors.

## `self` — reference to the current actor

`self` refers to the object context in which ZScript code is currently executing. In most cases, it is implicitly understood and does not need to be written explicitly. However, it becomes necessary when a local variable shadows a class member:

```zscript
class MyActor : Actor
{
    int myVariable;

    void MyMethod()
    {
        int myVariable = 5;  // shadows the class member
        Print(myVariable);   // prints 5 (the local)
        Print(self.myVariable);  // prints the class member value
    }
}
```

`self` works in any class method or property initializer, not just Actor classes. It is the implicit first parameter for all instance methods and is required when accessing the enclosing object from within nested scope contexts.

## `invoker` — reference to the state's owning actor in action functions

`invoker` is used exclusively within action functions (functions marked with the `action` keyword) and refers to the actor whose state is currently executing the action — the object the state chain belongs to. For an ordinary actor (e.g. a monster running its own state chain), `self` and `invoker` refer to the same object, since the actor is executing its own states.

`self` only diverges from `invoker` for **weapon and CustomInventory item action functions specifically**: there, `self` is overridden to refer to the actual actor using/wielding the item (typically the player pawn), while `invoker` still refers to the item/weapon instance itself. This is a special case baked into how those two kinds of action functions bind their implicit parameters, not a general property of `self` in every action function.

In action functions called from weapon states, `invoker` is the weapon itself, while `self` is the player:

```zscript
class CustomWeapon : Weapon
{
    action void Fire()
    {
        // self is the player
        // invoker is the weapon (this CustomWeapon)
        invoker.AmmoType1.Amount--;  // decrease weapon ammo
        A_FireProjectile(...);
    }
}
```

In weapon sprite (psprite) states specifically, modifying `invoker` affects the weapon's own fields directly, which is what makes it usable for charge-time tracking, firing-delay counters, and other weapon-specific variables — those fields live on the weapon (`invoker`), not on the player pawn (`self`).

## See also

- [ZScript load order and compile sequence](zscript-load-and-compile-order.md) — how ZScript is compiled and when types are resolved.
- [Function pointers](function-pointers.md) — first-class function references in ZScript, distinct from special words.
- [DECORATE to ZScript migration](decorate-to-zscript-differences.md) — language differences when moving actor definitions from DECORATE to ZScript.
