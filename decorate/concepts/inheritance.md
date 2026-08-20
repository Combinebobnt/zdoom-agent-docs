# Inheritance

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes — `SKIP_SUPER`'s restriction rule differs between the two,
see "Engine-family divergence" below; the rest of this file's inheritance/replaces/doomednum
mechanics apply to both
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-31)
**Provenance:** ZDoom Wiki "Using inheritance" (retrieved 2026-07-31, https://zdoom.org/w/index.php?title=Using_inheritance&oldid=53923), cross-checked against the Zandronum source's class-creation and actor-parsing machinery (`src/dobjtype.cpp:273-315`, `src/thingdef/thingdef.cpp:80-174`, `src/thingdef/thingdef_properties.cpp:448-467`, `src/p_mobj.cpp:7633-7652`). Per `../../shared/AUTHORING.md`'s engine-scope caveats, the local checkout is a `master` HEAD reporting `3.3-alpha` in `version.h`, not a pristine 3.2.1 checkout — the files cited here (`dobjtype.cpp`, `thingdef.cpp`, `p_mobj.cpp`) are not touched by the applied ZandronumMCP patch.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

This page covers how a derived actor class inherits properties, flags, and fields from its parent, how `replaces` and `doomednum` work, and how multiple-level inheritance chains resolve. For state-label inheritance specifically (how a subclass's `Goto` can reach a parent's labels), see `state-machine.md`'s "Label scoping and inheritance" section — this file covers property/flag inheritance, not state inheritance.

## How properties and fields are inherited

When a derived class is created at DECORATE compile time, its default property values are **copied from the parent's defaults** into its own new defaults instance — not looked up dynamically at runtime. The creation process (`PClass::CreateDerivedClass`, `src/dobjtype.cpp:273-315`) allocates a fresh `Defaults` buffer for the subclass and fills it with a `memcpy` from the parent's Defaults (`dobjtype.cpp:310-311`):

```text
type->Defaults = (BYTE *)M_Malloc(size);
memcpy (type->Defaults, Defaults, Size);
if (size > Size)
{
	memset (type->Defaults + Size, 0, size - Size);
}
```

Once this copy is made, the DECORATE parser then walks the subclass's property definitions and overwrites individual fields in place. This is why:

- **An unmentioned property keeps the parent's value** — it was already copied into the defaults buffer.
- **Flags words (and multi-word flag fields) carry over wholesale** — each flag is a bit in the copied buffer; unmentioned flags stay as they were.
- **A multi-level inheritance chain resolves correctly** — when a grandchild class is created, its defaults are copied from the *parent's* already-overwritten buffer (which includes any property changes the parent made), not re-derived from the grandparent's original.

The key point: properties and flags are **not** looked up by walking ancestors at runtime. They're concrete values baked into each class's own defaults instance at parse time.

## `SKIP_SUPER` — resetting to base defaults

The `SKIP_SUPER` property resets a derived actor's inherited properties to the base `AActor` defaults, wiping out whatever properties the parent class had set (`thingdef_properties.cpp:448-467`):

```text
DEFINE_PROPERTY(skip_super, 0, Actor)
{
	...
	memcpy ((void *)defaults, (void *)GetDefault<AActor>(), sizeof(AActor));
	...
}
```

**Three caveats:**

- **Reset target**: `SKIP_SUPER` copies `AActor`'s defaults wholesale, not zero values. An actor using `SKIP_SUPER` gets `AActor`'s own properties (zero health, default flags, etc.), not a blank slate.
- **Ordering**: `SKIP_SUPER` must appear before any `States{ }` block in the definition (`thingdef_properties.cpp:456-459`). A parse-time warning is issued if it appears after state definitions.
- **Inventory exception**: `SKIP_SUPER` is ignored for actors descended from `AInventory` — a parse-time warning is issued if an inventory item tries to use it (`thingdef_properties.cpp:450-454`).
- **State label table**: The inherited state-label table is **not** reset by `SKIP_SUPER`. The parent's states remain available for `Goto` and other state-jump mechanisms, even though the properties have been reset. (See `state-machine.md` for how state labels are inherited separately.)

## Species and same-ancestry monsters

When a species is not explicitly set via the `Species` property, an actor's species is automatically determined by walking up the class hierarchy. The `GetSpecies()` function (`p_mobj.cpp:7633-7652`) climbs the parent classes as long as they have the `MF3_ISMONSTER` flag set; when it reaches a non-monster ancestor, it uses that ancestor's class name as the species:

```text
if (GetDefaultByType(thistype)->flags3 & MF3_ISMONSTER)
{
	while (thistype->ParentClass)
	{
		if (GetDefaultByType(thistype->ParentClass)->flags3 & MF3_ISMONSTER)
			thistype = thistype->ParentClass;
		else 
			break;
	}
}
return Species = thistype->TypeName;
```

**Wiki divergence:** The ZDoom Wiki states that "monsters within the same species cannot hurt each other with projectiles" as if it were automatic. In Zandronum, this behavior is **not automatic** — it requires the `MF6_DONTHARMSPECIES` flag (`actor.h:313`) to be explicitly set on actors that should follow this rule. Species are determined automatically by inheritance, but the projectile-blocking mechanic is flag-gated, not unconditional. No shipped actor in Zandronum has this flag set by default.

## The `replaces` keyword and doomednum — two separate mechanisms

The `replaces` keyword and the trailing doomednum in an actor header are **two independent mechanisms**:

**`replaces` — actor substitution:** The `replaces` keyword (`thingdef_parse.cpp:1065-1076`) names another actor to replace. When that named actor is spawned (map-spawned only — not created via inventory, script, or other means), the replacement is used instead. The replacement is bidirectional: the replaced class's `Replacee` field points to the replacement, and the replacement's `Replacement` field points back (the relationship is set up in `SetReplacement`, `thingdef.cpp:203-204`):

```text
replacee->ActorInfo->Replacement = info;
info->Replacee = replacee->ActorInfo;
```

`replaces` does not require the new class to inherit from the replaced class — both can be unrelated; every wiki example happens to use inheritance alongside `replaces`, but they're independent mechanisms. A class cannot list itself as its own replacement (the parser rejects this with an error).

**doomednum — editor/map thing number:** The numeric value in an actor declaration is the map editor thing number, used by maps to reference the actor. doomednum is **not inherited** — when a derived class is created, its doomednum is explicitly initialized to `-1` by `CreateNewActor` (`thingdef.cpp:173`), regardless of the parent's number. A subclass with no trailing number gets no doomednum (represented as -1); the parent keeps its original number. Zandronum enforces a specific range: `[-1, 32767]` (`thingdef_parse.cpp:1083`); values outside this range are an error.

## Inheritance chains and state redeclaration

When a subclass redefines a state label that the parent already defined (e.g., overriding `Death:` or `Missile:`), only that label's states are replaced. Other inherited labels — from the parent or grandparent — that the subclass does not redeclare remain in place and continue to use the ancestor's state sequences. This allows a subclass to override selective states while delegating the rest to inherited implementations.

A practical consequence: if a subclass redefines `Death:` with its own sequence, but the parent's `Death:` sequence expected to be called from a `Missile:` state, the subclass must also redeclare `Missile:` (or any other state that calls `Goto Death`) to point to the new `Death:` if the old one is no longer valid. See `state-machine.md`'s examples for the state-label inheritance model in detail.

## ZScript-only features not available in DECORATE

The wiki page shows examples in **both ZScript and DECORATE** (marked "deprecated"). The following ZScript features do not exist in Zandronum's DECORATE-only codebase and should be ignored for Zandronum projects:

- **Class syntax and `Default{ }` blocks** — ZScript's class-definition syntax with a `Default { }` property block is a ZScript-only feature; DECORATE instead lists properties and flags directly in the actor body (e.g., `Health 100` without a `Default { }` wrapper).
- **Anonymous action blocks** — ZScript allows `{ statements; }` code blocks in place of action-function calls in states. DECORATE states accept only bare action-function names or no action at all.
- **Field-assignment syntax** — ZScript allows `bFRIGHTENED = true` flag assignments in code blocks; DECORATE uses `+FRIGHTENED` / `-FRIGHTENED` flag keywords in property/state declarations instead.
- **`FindState()` and `ResolveState()` as jump targets** — ZScript allows a state line to `return FindState("Label")` or `return ResolveState("Label")` to jump to a state. Neither exists in Zandronum's DECORATE; use `Goto Label` instead (see `state-machine.md` for dynamic vs. static jump differences).
- **`override` virtual methods** — ZScript's `override` keyword and virtual-method dispatch do not apply to DECORATE.

## Open questions (unverified in this checkout — don't guess past these)

- Whether the `Offset(0, 0)` special case (mentioned in `state-machine.md` as "keep previous offset" for Hexen compatibility) affects property inheritance in any way.
- Whether `SKIP_SUPER` applies the same reset to multi-word flag fields (flags2, flags3, etc.) as the source code snippet above suggests for the core `AActor` size, or whether a more complex interaction is needed.

## Engine-family divergence

Confirmed directly in UZDoom source: the core defaults-copy inheritance mechanism this file
documents (`PClass::CreateDerivedClass` `memcpy`-ing the parent's `Defaults` buffer,
`src/common/objects/dobjtype.cpp`), the `replaces` keyword, and the doomednum `[-1, 32767]` range
enforcement (`src/scripting/decorate/thingdef_parse.cpp`) are all present in UZDoom essentially
unchanged from what's documented above for Zandronum.

`SKIP_SUPER`'s restriction differs, though. Zandronum (per this file's "Three caveats" above)
ignores `SKIP_SUPER` specifically for classes descended from `AInventory`. UZDoom's `skip_super`
property (`src/scripting/thingdef_properties.cpp`) instead rejects it — with an `MSG_OPTERROR`,
not a hard abort — on **any** class whose instance size no longer matches base `AActor`'s
(`info->Size != actorclass->Size`), which in practice means any class that has added its own user
variables or other size-extending state, not just `AInventory` descendants specifically. The two
engines gate the same property on structurally different conditions (ancestry vs. instance-size
match), not the same rule reworded.

## Cross-references

- `state-machine.md` — the state-label inheritance model (how `Goto` resolves ancestor labels and the dotted-label fallback mechanic).
- `actor-definition-syntax.md` — the actor header line, `replaces`, and doomednum parsing details.
- `creating-monsters.md` — practical recipes for deriving monster variants.
