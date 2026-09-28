# `void SetThingSpecial(int tid, int special [, int arg0 [, int arg1 [, int arg2 [, int arg3 [, int arg4]]]]])`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** wiki page `SetThingSpecial - ZDoom Wiki.html` (`_intake/`, retrieved 2026-07-29, `https://zdoom.org/w/index.php?title=SetThingSpecial&oldid=35980`) + source-verified against the Zandronum source (`p_acs.cpp:11525-11581`) and `zt-bcc/src/builtin.c` (signature `setthingspecial = ;ii;rrrrr`). The wiki's basic description (sets the special and arguments for things with the same TID, uses activator if tid is 0) is confirmed in Zandronum. The named-ACS-special handling (present on both engines) and Zandronum's network replication are not on the ZDoom wiki page.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin (`PCD_*` opcode in `p_acs.cpp`).
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

Compiler builtin (`PCD_SETTHINGSPECIAL`), implementation at
the Zandronum source's `src/p_acs.cpp:11525-11581`. Sets the `special` field and **all five**
`args[0..4]` slots on one or more actors identified by `tid`. Unlike the action special
`Thing_SetSpecial` (index 127, see `functions/thing_setspecial.md`), which only sets
`args[0..2]` and is callable from linedef actions, this is ACS-only and sets every argument slot.

## Signature and behavior

Zandronum's case body, with its `[BB]`/`[BC]` comment lines omitted:

```cpp
case PCD_SETTHINGSPECIAL:
{
	int specnum = STACK(6);
	int arg0 = STACK(5);

	// Convert named ACS "specials" into real specials.
	if (specnum >= -ACSF_ACS_NamedExecuteAlways && specnum <= -ACSF_ACS_NamedExecute)
	{
		specnum = NamedACSToNormalACS[-specnum - ACSF_ACS_NamedExecute];
		arg0 = -FName(FBehavior::StaticLookupString(arg0));
	}

	if (STACK(7) != 0)
	{
		FActorIterator iterator (STACK(7));
		AActor *actor;

		while ( (actor = iterator.Next ()) )
		{
			actor->special = specnum;
			actor->args[0] = arg0;
			actor->args[1] = STACK(4);
			actor->args[2] = STACK(3);
			actor->args[3] = STACK(2);
			actor->args[4] = STACK(1);

			if ( NETWORK_GetState( ) == NETSTATE_SERVER )
			{
				SERVERCOMMANDS_SetThingArguments( actor );
			}
		}
	}
	else if (activator != NULL)
	{
		activator->special = specnum;
		activator->args[0] = arg0;
		activator->args[1] = STACK(4);
		activator->args[2] = STACK(3);
		activator->args[3] = STACK(2);
		activator->args[4] = STACK(1);

		if ( NETWORK_GetState( ) == NETSTATE_SERVER )
		{
			SERVERCOMMANDS_SetThingArguments( activator );
		}
	}
	sp -= 7;
}
break;
```

- **Sets all five `args` slots** — `args[0]` through `args[4]` — taking one argument parameter
  for each. `Thing_SetSpecial` (the action special) takes only three argument parameters and
  leaves `args[3]`/`args[4]` untouched; this builtin sets them all in one call.

- **`tid=0` uses the script's activator** — if `activator != NULL`, the special and arguments
  are set on the activator alone; if `activator == NULL` (e.g. an `OPEN` script with no
  activator), the call silently no-ops with no error. Nonzero `tid` iterates through all
  actors with that TID via `FActorIterator`, setting the special and arguments on every match.

- **Supports named ACS specials** — if `special` is a negative index in the range
  `[-ACSF_ACS_NamedExecuteAlways, -ACSF_ACS_NamedExecute]`, it's treated as encoding a named
  script special (see `families/script-execution.md` for the `Acs_NamedExecute*` family).
  The `special` value is converted to a real action-special index via the `NamedACSToNormalACS`
  lookup table, and `arg0` is converted from a string-table index to a `-FName(...)` string
  name for the script. Both engines do this conversion (it is inherited ZDoom code, not a
  Zandronum addition); the ZDoom wiki page just doesn't document it.

- **Network replication in multiplayer** — on the server (`NETWORK_GetState() == NETSTATE_SERVER`),
  the function calls `SERVERCOMMANDS_SetThingArguments(actor)` for every actor modified (or the
  activator, if `tid=0`). This replicates the argument change to all connected clients. This
  is Zandronum-specific netcode and also not documented on the wiki. Only the five `args`
  are sent (as full 32-bit values, `protocolspec/spec.things.txt:197-204`); the `special`
  number itself is never sent, so a client's copy of the actor keeps its old special. An actor
  with no net ID (`NetID == 0`) is skipped by `EnsureActorHasNetID` (`sv_commands.cpp:99-112`),
  so clients never see the change for it. Offline, or on a client running the script itself,
  the change is applied locally with no broadcast.

**Returns:** `void` — no return value.

**Difference from `Thing_SetSpecial`** — the action special `Thing_SetSpecial` (index 127,
`p_lnspec.cpp:1050-1079`) is callable from linedef actions and sets only `args[0..2]`, leaving
`args[3]`/`args[4]` untouched. This compiler builtin sets all five and is ACS-only. The wiki
page itself (in the `Thing_SetSpecial` section) suggests using `SetThingSpecial` when all five
arguments need to be set.

**Activator-absent no-op** — if `tid=0` and there is no activator (activator-less contexts like
`OPEN` scripts), the function silently does nothing, indistinguishable from successful
completion. There is no return value or error signal.
