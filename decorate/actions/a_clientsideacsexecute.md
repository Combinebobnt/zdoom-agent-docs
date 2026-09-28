# `A_ClientsideACSExecute` (run a named CLIENTSIDE script locally)

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-22)
**Provenance:** engine source only. Zandronum, read at upstream `master` @bdd0f7beb: `src/thingdef/thingdef_codeptr.cpp:6064-6083`, `wadsrc/static/actors/actor.txt:189`, `src/network.h:270-279` (`NETSTATE_*` order), and in `src/p_acs.cpp` the functions `ACS_IsScriptClientSide`, `P_StartScript` and `DLevelScript::RunScript` (cited by name, since that file carries a local patch that shifts line numbers), plus `FUNC(LS_ACS_ExecuteWithResult)` in `src/p_lnspec.cpp`. Introduced by 587bc09e3 (2024-04-18), an ancestor of the 3.2.1 commit 28f736fb3. UZDoom source @98b16b78fc has no declaration of this name.
**Bucket:** `DEFINE_ACTION_FUNCTION_PARAMS(AActor, A_ClientsideACSExecute)` in `src/thingdef/thingdef_codeptr.cpp`; declared on `Actor`, so any actor's states can use it.

Runs a named `CLIENTSIDE` ACS script immediately on the local machine, with the calling actor as
activator. It never runs on a server, and the server doesn't forward it anywhere: each client
runs the script itself when its own copy of the actor reaches the state.

## Signature

```text
A_ClientsideACSExecute(string script, int arg1 = 0, int arg2 = 0, int arg3 = 0, int arg4 = 0)
```

## Parameters

- **`script`**: a script **name**. The engine takes it as a name and negates its name index, the
  same encoding named scripts use everywhere, so only named scripts can be reached. There is no
  way to call a numbered script.
- **`arg1`..`arg4`**: passed to the script. Four arguments, like `ACS_ExecuteWithResult`.

## Behavior

- **Where it runs.** It returns at once on a server (the only network state above "client").
  It runs in single player, in offline multiplayer with bots, and on each client.
- **Silent no-op unless the script is client-side.** Before running anything it checks that the
  script exists and is marked `CLIENTSIDE`. Under the
  `ZACOMPATF_NETSCRIPTS_ARE_CLIENTSIDE` compat flag a `NET` script also passes. A misspelled name
  or an ordinary server-side script does nothing, with no console message, even in single player.
- **How it runs.** Through `ACS_ExecuteWithResult`: activator is the calling actor, no line, and
  like `ACS_ExecuteAlways` a new instance starts even if the script is already running. The
  script runs synchronously until it finishes or hits its first delay.
- **Result.** The action result is true when the script's result value is nonzero. That value is
  whatever `SetResultValue` set before the script finished or first delayed, and defaults to 1,
  so a script that never sets it reports true.
- **It only fires where the state actually executes.** Clients run their own copies of actor
  state sequences, so this usually fires on every client, but only on those that really run
  the state containing the call. It isn't a substitute for a server-to-client broadcast.

## Compared with calling `ACS_ExecuteWithResult` from DECORATE

The plain special behaves differently for a client-side script: on a server it doesn't run the
script but tells every client to run it, and returns false. `A_ClientsideACSExecute` is the
client-local form: no server involvement, no traffic, and a guarantee that only client-side
scripts ever run through it.
See [ACS_ExecuteWithResult](../../acs/functions/acs_executewithresult.md) and
[Client-side scripting](../../acs/concepts/clientside-scripting.md).

## Zandronum-specific: absent on UZDoom

UZDoom has no `A_ClientsideACSExecute`; a state table calling it doesn't resolve there. UZDoom
has its own, differently-shaped handling of `CLIENTSIDE` scripts in `src/playsim/p_acs.cpp`
(`IsClientSideScript`, `ShouldIgnoreClientSideScript`), not traced for this entry. Don't assume
Zandronum's client/server semantics carry over.

## Example

```decorate
ACTOR GlowingOrb
{
  States
  {
  Spawn:
    ORBS A 35 A_ClientsideACSExecute("OrbPulseFX", 1)
    Loop
  }
}
```
