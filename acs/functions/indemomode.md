# `int InDemoMode(void)`

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.2.1 @28f736fb3 (2026-08-18)
**Provenance:** Zandronum Wiki `InDemoMode` (retrieved 2026-08-18, https://wiki.zandronum.com/w/index.php?title=InDemoMode&oldid=1305) + source-verified against Zandronum's `src/p_acs.cpp:7513-7514` and `src/cl_demo.cpp:895-898`.
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0 (NonCommercial) — see [LICENSE](../../LICENSE) §2.
**Bucket:** extension function (index -140; dispatched as `ACSF_InDemoMode`).

Checks whether the engine is currently playing a client-side demo.

## Parameters

None.

## Return value

Returns `1` (true) if a client-side demo is playing, `0` (false) otherwise.

## Remarks

A client-side demo (recorded while playing in a multiplayer session or similar) can be played back locally without a connection to the game server. This function detects such playback state, which is useful for scripts that need to alter behavior when reviewing recorded gameplay versus active participation. In singleplayer or during normal multiplayer participation (not demo playback), this function returns `0`.

The function's behavior is specific to the distinction between active gameplay and demo playback in Zandronum's client-side demo system. Server-side scripts and singleplayer-only scenarios will always see `0`, since client-side demo playback is inherently a client feature.

**Wiki/compiler divergence:** The wiki's signature shows `int InDemoMode (void)`, diverging from the zt-bcc compiler's actual return-type declaration `InDemoMode():bool` in `lib/zcommon.bcs` (-140) — both are functionally equivalent (returning 0/1), but the compiler's stronger type claim is more accurate than the wiki's weaker int typing.

## Zandronum-specific: client-side demo feature only

This function and the underlying client-side demo playback system are Zandronum-only features. UZDoom does not ship this functionality — server-side `demoplayback` and single-player recorded-session playback exist in UZDoom, but the client-side netcode-integrated demo system this function checks does not. A UZDoom build should not call this function; any script using it will silently fail to compile or link if ported to UZDoom (the `ACSF_InDemoMode` index has no corresponding implementation).

## Examples

```acs
Script 1 OPEN
{
    if (InDemoMode())
    {
        PrintBold(s:"We are watching a demo right now!");
    }
}
```

## See also

- [ExecuteClientScript](executeclientscript.md) — related netcode-aware script execution
- [IsNetworkGame](ismultiplayer.md) — check for network multiplayer status
