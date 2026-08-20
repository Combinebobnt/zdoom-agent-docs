# `CVar` (struct)

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15)
**Provenance:** ZDoom Wiki `Structs:CVar` (retrieved from HTML snapshot, https://zdoom.org/w/index.php?title=Structs%3ACVar&oldid=54824) + verified against UZDoom source's `wadsrc/static/zscript/engine/base.zs`, `wadsrc/static/zscript/doombase.zs`, and C++ native implementations in `src/common/scripting/interface/vmnatives.cpp` (all per-instance accessors: `GetInt`/`SetInt`/`GetFloat`/`SetFloat`/`GetString`/`SetString`/`GetDefault*`/`GetRealType`/`ResetToDefault`/`FindCVar`), `src/scripting/vmthunks.cpp` (`GetCVar` only), and `src/common/console/c_cvars.cpp` (`FBaseCVar`/`GetCVar(playernum,...)`/type-coercion logic, and the CVARINFO parser in `src/d_main.cpp`'s `ParseCVarInfo()` for the handler-class declaration syntax); re-verified 2026-08-03 against UZDoom 5.0.0-pre (commit fbad53bff5) after upstream pull — no behavioral drift found (only mechanical license-header changes touched the cited files); a pre-existing citation gap was also corrected in this pass (see above).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** Native struct (`struct CVar native`) declared in the ZScript standard library (`wadsrc/static/zscript/engine/base.zs`, with extension in `doombase.zs`). Native methods bound via `DEFINE_ACTION_FUNCTION(_CVar, ...)`, mostly in `src/common/scripting/interface/vmnatives.cpp` (the `GetCVar` static factory is the one exception, in `src/scripting/vmthunks.cpp`).

A container of methods used to access and manipulate console variables (CVars). All type-conversion methods are available through both accessor patterns: by cvar name (static methods) or via a cvar pointer (non-static methods on an already-retrieved `CVar` struct).

## Static methods

### `static CVar FindCVar(Name name)`

Looks up a cvar by name and returns a pointer to it, or `null` if it does not exist. This function provides direct, unfiltered access to the global cvar and is suitable for server and nosave CVars. **Warning:** Using this on user-scoped CVars in a multiplayer context may cause desyncs, because it does not handle per-player variable copies — use `GetCVar` instead.

### `static CVar GetCVar(Name name, PlayerInfo player = null)`

Looks up a cvar by name and returns a pointer to it, or `null` if it does not exist. Unlike `FindCVar`, this method correctly handles user-scoped CVars:

- For user-scoped variables, the `player` argument specifies whose copy of the variable to retrieve. If `player` is `null` and the variable is user-scoped, the function returns `null`.
- For nosave and server-scoped variables, `player` is accepted but ignored; the same global copy is returned.

### `static bool SaveConfig()`

Saves all modified CVars to the config file. Returns `true` on success, `false` on failure. **Note:** This method does not appear in the original ZDoom Wiki page but is present in the UZDoom source.

## Non-static methods

### Type accessors

`CVar` supports five type variants, identified by the `GetRealType()` method, which returns one of the `ECVarType` enum values: `CVAR_Bool`, `CVAR_Int`, `CVAR_Float`, `CVAR_String`, or `CVAR_Color` (in that declaration order, so `CVAR_Bool == 0` through `CVAR_Color == 4`).

Access methods follow a pattern: `Get<Type>()` and `Set<Type>()` for current values, `GetDefault<Type>()` for the default value defined in CVARINFO.

**Write-permission restriction:** `SetBool`/`SetInt`/`SetFloat`/`SetString`/`ResetToDefault` (see below) are only unconditionally usable if the target cvar carries the "cvar was defined by a mod" flag — which every CVARINFO-declared cvar gets automatically, whether or not it uses a custom handler class. Cvars that are *not* CVARINFO-declared (i.e. hardcoded engine/game cvars registered directly in C++) lack that flag, and calling one of these setters on them from outside menu code throws a VM exception ("Attempt to change CVAR '...' outside of menu code"). In practice this means: freely call these setters on your own mod's CVARINFO cvars from anywhere, but only touch built-in engine cvars from menu-context code (e.g. `OptionMenuItem` subclasses).

### `int GetRealType()`

Returns the type of the cvar as an `ECVarType` enum value.

### Boolean accessors

#### `bool GetBool()`

Returns the current value as a boolean. **Semantic detail:** This is implemented as a wrapper over `GetInt()`, so the coercion path is integer-based (`0` → `false`, nonzero → `true`), not a type-native truncation. For a `CVAR_Float` cvar, calling `GetBool()` will convert the float to an integer and then to boolean, not convert the float directly to boolean.

#### `bool GetDefaultBool()`

Returns the default value as a boolean, using the same integer-based coercion as `GetBool()`.

#### `void SetBool(bool b)`

Sets the value to a boolean. Implemented as a wrapper over `SetInt()`, so the value is stored as an integer (1 for true, 0 for false).

### Integer accessors

#### `int GetInt()`

Returns the current value as an integer. For `CVAR_Color` cvars, this returns an RGB value as a packed 24-bit integer (e.g., red = `0xFF0000`, green = `0x00FF00`).

#### `int GetDefaultInt()`

Returns the default value as an integer.

#### `void SetInt(int v)`

Sets the value to an integer. For `CVAR_Color` cvars, the value is interpreted as a packed RGB hex color (e.g., `0xFF0000` for red).

### Float accessors

#### `double GetFloat()`

Returns the current value as a floating-point number.

#### `double GetDefaultFloat()`

Returns the default value as a floating-point number.

#### `void SetFloat(double v)`

Sets the value to a floating-point number.

### String accessors

#### `String GetString()`

Returns the current value as a string. For `CVAR_Color` cvars, this returns the color in the format `"RR GG BB"` (e.g., `"00 ff 00"` for green). Color names from the `X11R6RGB` lump are accepted when setting.

#### `String GetDefaultString()`

Returns the default value as a string, using the same format as `GetString()` for color cvars.

#### `void SetString(String s)`

Sets the value to a string. For `CVAR_Color` cvars, accepts either the `"RR GG BB"` format (e.g., `"ff 00 00"` for red) or an X11R6RGB color name (e.g., `"green"`).

### `int ResetToDefault()`

Resets the cvar to its default value (as defined in CVARINFO); this is unconditional whenever the cvar isn't already at its default, with no failure path in the underlying operation. **Verified discrepancy:** although declared to return `int`, the native implementation never actually produces a return value for it (unlike the other accessors here, it does not go through the VM's return-value setter at all) — the caller-side result is effectively unspecified. Do not rely on this method's return value; treat it as `void` in practice.

## Custom CVar handler classes

Custom CVars can have handlers associated with them to validate or transform values when the player attempts to change them. Handler classes are declared in CVARINFO using the syntax:

```text
User HandlerClass(HandlerClassName) <Type> CvarName
```

For example:

```text
User HandlerClass(MyIntClamper) Int MyValue
```

The handler is implemented as a ZScript class inheriting from one of the five handler base classes:

- `CustomIntCVar` — handles `Int` CVars
- `CustomFloatCVar` — handles `Float` CVars
- `CustomStringCVar` — handles `String` CVars
- `CustomBoolCVar` — handles `Bool` CVars
- `CustomColorCVar` — handles `Color` CVars

Each handler class is abstract and must override the `ModifyValue` method:

```zscript
class MyIntClamper : CustomIntCVar
{
	override int ModifyValue(Name cvarName, int value)
	{
		return clamp(value, 0, 100);
	}
}
```

The `ModifyValue` method receives the cvar name and the proposed new value, and returns the value that will actually be stored.

## Example

```zscript
// Set a server cvar
CVar impAttackType = CVar.FindCVar("sv_imp_attack_mode");
if (impAttackType)
{
	impAttackType.SetInt(2);
}

// Read a user cvar for a specific player (only valid in netgame context)
CVar playerVolume = CVar.GetCVar("user_volume", players[0]);
if (playerVolume)
{
	let vol = playerVolume.GetInt();
	Print("Player volume: " .. vol);
}

// Query default value
CVar colorVar = CVar.FindCVar("sv_default_ui_color");
if (colorVar && colorVar.GetRealType() == CVAR_Color)
{
	int defaultColor = colorVar.GetDefaultInt();
	// Use defaultColor...
}
```

## Wiki/engine divergence

1. The ZDoom Wiki page lists `GetDefaultBool()`, `GetDefaultFloat()`, `GetDefaultInt()`, and `GetDefaultString()` as available only in "development version 9f6c1d6". In the UZDoom 5.0.0-pre checkout, these methods are unconditionally present with no version qualifier and are fully available.

2. The Wiki page omits `SaveConfig()`, a static method present in the UZDoom source for saving CVars to the config file.

3. The Wiki page does not mention that `SetBool`/`SetInt`/`SetFloat`/`SetString`/`ResetToDefault` throw a VM exception when called outside menu code against a cvar that isn't mod-defined (see "Write-permission restriction" above). This restriction is enforced entirely on the C++ side (`src/common/scripting/interface/vmnatives.cpp`) and predates this doc's original verification — it is not new engine behavior, just a previously-undocumented gap.

4. **Error found and corrected in the 2026-08-15 re-verification pass:** the Wiki-derived claim that `ResetToDefault()` "returns nonzero on success" does not hold against the current UZDoom source. The native binding (`DEFINE_ACTION_FUNCTION(_CVar, ResetToDefault)` in `src/common/scripting/interface/vmnatives.cpp`) never invokes the VM's return-value setter for any code path, so no value is ever actually returned to the caller despite the `int` declaration in `wadsrc/static/zscript/engine/base.zs`. Separately, the underlying C++ `FBaseCVar::ResetToDefault()` is `void` and unconditional — there is no success/failure distinction in the operation itself. See the `ResetToDefault()` entry above under "Non-static methods".
