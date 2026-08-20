# ZScript class definitions, modifiers, and hierarchy

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki "ZScript classes" (retrieved 2026-08-03, https://zdoom.org/w/index.php?title=ZScript_classes&oldid=55397) + verified against the UZDoom source's `wadsrc/static/zscript/` stdlib and `src/common/scripting/` parser/backend; re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after an ~8-month upstream pull — updated the `extend class`/`extend struct` ordering claim (extensions are now pre-scanned and compiled together with their target class, regardless of textual order) and corrected the `IsAbstract()` note (the class-pointer form is a working compiler intrinsic; only the `Object` instance-method form is unimplemented). Checked and confirmed unchanged: `String`-is-not-a-class and the `Behavior`/`BehaviorIterator` 4.15.1+ version gate. **Correction, same re-verification pass:** the cross-archive extension *restriction* (you still can't extend a class the compiler can't find in the current compile unit) is unchanged, but a full trace of the `extend class`/`extend struct` rework (commit `e85bf3f569`, in `src/common/scripting/frontend/zcc_compile.cpp`) showed the compiler no longer *reports* that condition — it now fails silently instead of raising a compile-time error. See "Class extension" below; this is a correction to a claim in an earlier revision of this file, not something newly introduced by the source-level re-verification itself.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

ZScript classes are similar to C++ classes and may contain data members, methods, and virtual functions. They follow a single-inheritance hierarchy rooted in `Object`.

## Internal class hierarchy

The standard library defines several base classes that form the foundation for modding:

- `Object` — the root of all classes. Every ZScript class inherits from `Object` and thus inherits its intrinsic methods.
- `Thinker : Object` — an object that receives `Tick()` calls each game tic. Used for animated objects, AI logic, and other time-dependent behavior.
- `Actor : Thinker` — an interactive game entity with physics, sprites, and gameplay behavior. This is the primary class for gameplay objects like monsters, items, and projectiles.
- `VisualThinker : Thinker` — a lightweight particle/visual-effect thinker introduced in UZDoom 4.15pre. Spawned without the full overhead of an `Actor`.
- `SectorEffect : Thinker` — base for moving platform and dynamic light effects.
  - `Mover : SectorEffect` — base for platform movement logic.
    - `MovingFloor : Mover` — floors that move.
      - `Floor : MovingFloor` — regular floor.
      - `Plat : MovingFloor` — platform.
    - `MovingCeiling : Mover` — ceilings that move.
      - `Ceiling : MovingCeiling` — regular ceiling.
      - `Door : MovingCeiling` — a door (moving ceiling/floor hybrid).
    - `Elevator : Mover` — elevators.

Additional internal classes for specialized behavior:

- `Behavior : Object` (introduced in UZDoom 4.15.1) — represents a behavior component, marked `abstract` and `play`-scoped.
- `BehaviorIterator : Object` (introduced in UZDoom 4.15.1) — iterator for enumerating behaviors.
- `ThinkerIterator : Object` — iterate over thinkers in the level.
- `ActorIterator : Object` — iterate over actors, optionally by TID.
- `BlockThingsIterator : Object` — iterate over things occupying a specific 3D area.
- `SpotState : Object` — manages spawn spot states (used for `GetSpawnSpot()` etc.).
- `StaticEventHandler : Object` — event handler for global game events (version 2.4+).
- `LevelPostProcessor : Object` — runs after map generation, used for MAPINFO postprocessing.
- `Service` — abstract base class for plugin-like subsystems.

**Note on `String`:** The wiki lists `String` as an internal class, but it is not. `String` is a built-in primitive type in ZScript, not a class deriving from `Object`.

## Class modifiers

Several modifiers may appear after a class name (or after its parent class, if any) to control how the class behaves:

### `abstract`

Marks a class as abstract — it cannot be directly instantiated or spawned. Abstract classes exist only to serve as parent classes for other classes:

```zscript
class MyBase : Actor abstract
{
	// Abstract function that child classes must override
	virtual void MyMethod() {}
}

class MyChild : MyBase
{
	// This class is concrete and can be spawned
	override void MyMethod() { /* ... */ }
}
```

Abstract classes can also define abstract methods (functions with no body), which child classes must override.

**Instantiation failure mode depends on how the class is named, not just that it's abstract.** Verified 2026-08-15 against `src/common/scripting/backend/codegen.cpp` and `src/playsim/p_mobj.cpp`:

- `new SomeAbstractClass` where the class name is a compile-time-constant class-pointer expression: `FxNew::Resolve` (`codegen.cpp`) checks `bAbstract` while resolving and raises a compile-time `MSG_ERROR` ("Cannot instantiate abstract class %s").
- `new` through a class-pointer variable the compiler can't resolve to a constant at compile time: the compile-time check in `FxNew::Resolve` never runs (it's gated on `val->isConstant()`); the same `bAbstract` check instead happens at runtime in the `BuiltinNew` VM builtin, which throws a `ThrowAbortException(X_OTHER, ...)` VM abort — a runtime crash, not a compile error.
- Spawning an abstract *actor* class (`Actor.Spawn`, `level.SpawnActor`, `A_SpawnItem`, and other paths that bottom out in `AActor::StaticSpawn`, `p_mobj.cpp`): there is no exception at all. The engine prints `Attempt to spawn an instance of abstract actor class %s` to the console and returns `null`, with no compile-time or runtime error to catch.

So "cannot be directly instantiated or spawned" is accurate as an end result, but only the narrowest case (a literal, compile-time-resolvable class name after `new`) is actually a compile-time error; a class-pointer variable resolved at runtime aborts the VM, and an abstract actor spawn attempt fails silently (console message + null return) instead.

**Wiki vs. source divergence:** The wiki shows an example using `IsAbstract()` to check whether a class is abstract at runtime. Source has two distinct forms of this and they behave differently:

- As an `Object` instance method (`someObject.IsAbstract()`, "is the class of this object abstract") — this is commented out in the `Object` base class's intrinsics list as unimplemented. Do not rely on it.
- As a class-pointer method (`class<Actor> cls = ...; cls.IsAbstract()`) — this **is** implemented, as a compiler intrinsic special-cased for class-pointer-typed expressions, returning a bool. This form has existed since long before 5.0.0-pre and still works.

If the wiki's example calls `IsAbstract()` on a class-pointer value, it is accurate; if it calls it on a plain object instance, it is not. Since the retrieved wiki text isn't reproduced here, check which form a specific piece of code uses before assuming it will or won't compile.

### `play`, `ui`, `data`

These scope modifiers control which execution context the class belongs to:

- `play` — network play scope. A class member with `play` scope can only access other `play`-scoped members.
- `ui` — user interface scope. Can access rendering and input state, but not game state. Cannot call game-affecting code.
- `data` — data scope (default). Holds only data and is accessible from all scopes.

If a class inherits from another class, it assumes the parent's scope. A class can only be marked with one scope modifier (`ui`, `play`, and `clearscope` are mutually exclusive; the compiler rejects a class carrying more than one with "Class %s has incompatible flags").

**Verified 2026-08-15 against `src/common/scripting/frontend/zcc_compile.cpp`:** the "assumes the parent's scope" rule is enforced, not just a default — if the parent class is already `ui`- or `play`-scoped, writing an explicit `ui`/`play` modifier on the child is a compile-time error ("Can't change class scope in class %s"), even if the modifier names the same scope the parent already has. Only an unscoped child (no modifier at all) silently inherits the parent's scope without complaint. In other words: once a class hierarchy commits to `ui` or `play` at some ancestor, every subclass must leave the scope modifier off entirely.

```zscript
class MyPlayClass : Actor play
{
	// This is play-scoped
}

class MyUIClass : Object ui
{
	// This is ui-scoped
}

class MyDataClass : Object
{
	// This is implicitly data-scoped (default)
}
```

These modifiers apply to both classes and structs.

## Class extension

ZScript allows extending an existing class definition across multiple files by using the `extend class` keyword:

```zscript
extend class MyMonster
{
	void MyNewMethod()
	{
		// New method added to MyMonster, from another file in the same mod
	}
}
```

Extensions allow organizing code or adding functionality without modifying the original class definition.

**Important restriction:** A class can only be extended if the compiler can find its base definition within the same compile unit — all files pulled into a single `ZSCRIPT` lump via its `#include` chain (each `ZSCRIPT` lump found in the loaded archives is compiled independently; see [`zscript-load-and-compile-order.md`](zscript-load-and-compile-order.md)). Practically, this means: extensions defined in one mod archive cannot attach to a class defined in a different archive's `ZSCRIPT` lump, and classes defined in the engine's base `.pk3` (such as `Actor`, `Thinker`, etc. in UZDoom's `uzdoom.pk3`) **cannot be extended** from user mods — only from within the engine's own ZScript codebase, since each is its own independent compile with its own independent list of known classes.

**The restriction still holds, but the failure mode changed in 5.0.0-pre — and this looks like an unintended regression, not a deliberate design change.** Verified 2026-08-03 by tracing the `extend class`/`extend struct` rework in `src/common/scripting/frontend/zcc_compile.cpp` (introduced by commit `e85bf3f569`, "make sure extensions are compiled together with their respective class"). **Scope note:** this trace is against the local UZDoom fork's checkout specifically, not confirmed against a mainline GZDoom tree — per this tree's usual caveat, treat it as a UZDoom-fork finding until someone checks whether GZDoom proper carries the same commit/rework.

- **Through UZDoom 4.15.x:** the compiler resolved every `extend class`/`extend struct` node the moment its linear top-level pass reached it, searching the list of classes/structs already processed *in this same compile*. If no match was found — whether because the name was mistyped, the base genuinely lives in a different archive, or (see "Ordering" below) the extension simply appears before its base in file order — the compiler raised a hard compile-time error naming the class/struct as unfound in the current translation unit.
- **As of 5.0.0-pre:** the compiler now pre-scans all extension nodes into a name-keyed table before its main pass runs. The main pass only ever consults that table from the branch that processes a *matching* non-extension class/struct definition, immediately after finishing that base — it looks up and applies any queued extensions sharing its name. Nothing afterward walks the table to check for entries that were never matched this way. An extension whose base is never found anywhere in the compile unit is therefore simply left behind in that (function-local) table when the compiler's constructor returns, and is discarded along with it — with no error, and no warning.

Net effect: a cross-archive extension, or a same-file typo in the extended class's name, now compiles cleanly and silently does nothing, where 4.15.x would have refused to compile. If something else in the same compile unit calls a method the dropped extension was meant to add, the resulting error points at that unrelated call site rather than at the broken `extend` block — a confusing place to go looking. If the extension only added fields, a `Default` block, or members nothing else references, there is no diagnostic anywhere at all. This is a plausible upstream bug worth reporting rather than a documented behavior change — the fix would be a pass over whatever is left in the pre-scan table after the main loop finishes, raising the same error that already exists for the found-immediately case. The commit's own message and diff describe only the ordering fix below; nothing suggests removing the error path was intentional.

**Ordering (version-gated) — the other half of the same change:** through UZDoom 4.15.x, a class had to be fully processed before it could be extended within the same compile — an `extend class` directive appearing before the original class definition in AST/`#include` order would fail the lookup described above, even though the base class did exist later in the same compile unit (a false-positive error, not a real problem). As of 5.0.0-pre this restriction is gone: the pre-scan described above queues an extension regardless of where it appears textually, then applies it right after its base's own processing whenever the main pass reaches that base — so textual order between a base definition and its extension(s) within the same compile unit no longer matters. This half of the change is a straightforward improvement; it's specifically the *base-not-found* case above (not the *found-but-in-the-wrong-order* case) that lost its diagnostic.

## Cross-mod class references

ZScript provides two approaches for checking whether a class exists when loading multiple mods:

**Compile-time check:**
```zscript
class<Actor> cls = "MissingClassName";
// If "MissingClassName" doesn't exist, this is a compile error.
```

**Runtime check:**
```zscript
string classname = "MissingClassName";
class<Actor> cls = classname;
// If the class doesn't exist, cls is null. No compile-time error.
```

The runtime approach is useful for addon compatibility — an addon can load alongside a base mod and safely check for classes without requiring all dependency mods to be present.
