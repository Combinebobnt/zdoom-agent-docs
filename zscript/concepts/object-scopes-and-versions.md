# Object scopes and versions

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki "Object scopes and versions" (retrieved 2026-08-03, https://zdoom.org/w/index.php?title=Object_scopes_and_versions&oldid=53298) + verified against UZDoom `src/common/scripting/core/scopebarrier.cpp`, `src/common/scripting/frontend/zcc_compile.cpp`, and `src/common/scripting/frontend/zcc-parse.lemon`; re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — ZScript version ceiling bumped 4.15.1 → 5.0.0 (tracked automatically since the doc describes it relative to the checkout, not a hardcoded number); no drift in the scope-barrier access rules, keywords, or version-gating logic itself.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

ZScript has a versioning system and a scoping system to ensure compatibility and prevent unsafe access across context boundaries — most notably, preventing UI code (which renders to the screen on the client) from directly manipulating playsim state (the canonical server-side game simulation) in ways that could corrupt multiplayer/demo/netcode consistency.

## Versioning

ZScript source code declares its version using a `version` directive, placed before any other declarations in the ZSCRIPT lump or `zscript.txt` file:

```zscript
version "2.4"
```

The version number format is `major.minor[.revision]`. At compile time, the engine rejects any `version` directive higher than the engine's own ZScript version ceiling (`VER_MAJOR`/`VER_MINOR`/`VER_REVISION` in `src/version.h`, enforced in `zcc_parser.cpp`) — in the local UZDoom 5.0.0-pre checkout, the ceiling is 5.0.0. (The wiki states the current version is 4.14.3/4.14.0; this reflects the ZScript version at the time the wiki page was written, not the engine's current build.) The ceiling itself moved between the two verification passes: it was 4.15.1 as of commit `515ea869f4` (the previous verification) and was bumped to 5.0.0 in the pull that landed commit `fbad53bff5`, alongside the engine's own version bump to 5.0.0-pre.

Classes, fields, and methods can be marked with their own version thresholds (e.g., `virtual version("2.4") ui void SomeMethod()`). Code compiled under an earlier version than a symbol's threshold will fail to compile and the mod will not load.

A few notes on version vs. engine release version: a given GZDoom/UZDoom release may carry a ZScript version number unrelated to the engine's own version number (e.g., a UZDoom 4.15pre build carries ZScript version 4.14.3). The `version` directive gates features; newer versions have different functions and restrictions (e.g., the scoping system itself is only active in ZScript version 2.4 and above, so declaring version 2.4 prevents older versions from loading the mod).

## Scoping system

ZScript's scoping system is only active for ZScript version 2.4 and above. Every object (class, field, method) has a **scope** — one of three labels: **data**, **play**, or **ui**. The scope governs which contexts can access that object and how (read-only, write, or fully).

### Scope semantics

- **data scope:** Neutral context. No client/server semantics. Default for unspecified classes (unless inherited from a parent with ui/play scope).
- **play scope:** Playsim context. Safe only for server-side/canonical simulation code. Cannot be read or written from ui scope.
- **ui scope:** Client-side UI context. Cannot read or modify play-scope or actor fields.

### Access table

Access is determined by the calling context (left) and the code object's scope (top). "Full" means the context can call methods, read all fields, and write non-readonly fields. "Readonly" means only const methods are callable and no fields are writable. "None" means no access (not even reads).

| Calling context | data scope | play scope | ui scope |
|---|---|---|---|
| **data** | full | readonly | none |
| **play** | full | full | none |
| **ui** | full | readonly | full |

**Note:** The "readonly" column for `data → play` access describes the access level available to a data-scope context attempting to read a play-scope field or call a play-scope method. It does not mean all play fields are marked readonly; it means write attempts will fail. Similarly, a readonly method (marked `const`) can be called across scope boundaries even if the destination scope would normally block non-const calls.

### Scope keywords and defaults

Four scope-related keywords are recognized:

- **`play`** — marks a class, field, or method as belonging to the play scope. Classes marked `play` inherit this scope to all unspecified fields and methods by default.
- **`ui`** — marks a class, field, or method as belonging to the ui scope. Classes marked `ui` inherit this scope to all unspecified fields and methods by default.
- **`clearscope`** — marks a method or struct as data scope, preventing it from inheriting the enclosing class's scope. Used to allow a method or struct to be callable from both ui and play contexts. The method itself is subject to data-scope restrictions (can only access data-scope fields, cannot modify play-scope state).
- **`virtualscope`** — marks a method to use the scope of the object it's called on, not the scope declared in its original definition. Extremely rare; internal use only. Examples: `Object.Destroy()` is `virtualscope` so that calling `myActor.Destroy()` uses play-scope semantics and calling `myUIPanel.Destroy()` uses ui-scope semantics, even though both call the same underlying method.

**Engine divergence:** UZDoom also supports `unsafe(clearscope)`, a variant of clearscope used internally. This is not documented on the wiki.

**Unrelated engine feature (not part of the scope system):** as of the 2026-08-01 UZDoom tree (commit `fbad53bff5`), a `norollback` field flag exists for client-side prediction/rollback netcode — it marks a field to be skipped when restoring rolled-back predicted state, which is orthogonal to the ui/play/data access barrier described above. It is implicitly applied to ui-scope fields (and to native/transient fields) and cannot be combined with an explicit `play` scope on a non-native field (compile error). It doesn't change the access table, the version threshold, or any of the scope keywords covered here.

For virtual methods, the scope is set once in the virtual declaration and cannot be changed in overrides — attempting to do so is a compile error.

### Defaults

- **Default scope for unspecified classes:** data (unless the class inherits from a parent with ui or play scope, in which case it inherits the parent's scope).
- **Default scope for unspecified fields/methods in a class:** the class's own scope (e.g., all fields in an `Actor : play` class are play unless explicitly marked `clearscope` or `const`).

### Construction and readonly scopes

Construction (instantiation) of a class marked with a non-writable scope (as seen from the calling context) is not possible. For example, ui-scope code cannot construct a play-scope class, since doing so would require write access to modify the newly-created object.

Methods marked `const` (rendered as `readonly` in the flags) can be called across scope boundaries — this is the primary escape hatch for data-scope utility code callable from both ui and play contexts.
