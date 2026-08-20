# `action native A_SetBlend(color color1, float alpha, int tics, color color2 = "")`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-01)
**Provenance:** ZDoom Wiki `A_SetBlend` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_SetBlend&oldid=54493) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3499-3515` and UZDoom's `src/playsim/p_actionfunctions.cpp:1903-1923`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** action function (defined on `AActor`; only takes effect when called on a PlayerPawn-based actor).

Applies a tinted color fade effect to a player's screen, animating from one color to another over a specified number of tics. This affects the player's visual perception only — it does not change any game-world state.

## Parameters

- **color1**: The initial color of the screen tint. Specified as a color literal (e.g., `"FF0000"` for red or `0xFF0000` as an integer). The color is fully opaque at the start of the fade, with opacity determined by **alpha**.
- **alpha**: Float between 0.0 (transparent) and 1.0 (fully opaque) for the initial color **color1**. Values outside this range are clamped.
- **tics**: Integer number of tics over which the blend effect fades. A value of 0 sets the blend immediately without animation.
- **color2** (optional): The destination color the screen tint fades toward over the duration specified by **tics**. Defaults to the empty color (`""`, equivalent to black with alpha=0). **Engine-specific behavior:** In Zandronum, the blend always fades to fully transparent regardless of **color2**'s RGB values; only **color1** is visually relevant in determining the hue of the fade. In UZDoom/GZDoom-family engines, **color2** specifies the actual destination color, and the destination opacity is controlled by the **alpha2** parameter (see below).

## Engine-family divergence

**Zandronum:** The function takes exactly 4 parameters. The fade always animates from **color1** to fully transparent (alpha=0), completing over **tics**. The **color2** parameter, if provided, is ignored — the destination is always transparent. This limitation stems from the underlying `DFlashFader` class being called with a hardcoded destination alpha of 0.

**UZDoom/GZDoom-family:** A fifth parameter, **alpha2** (float, defaults to 0.0), controls the destination opacity. The fade animates from **color1** at **alpha** to **color2** at **alpha2**. This allows modders to create persistent tints (by setting alpha2 to a non-zero value) or to fade between two different colors with different opacities. **This extended signature does not exist in Zandronum and should not be used in mods targeting that engine.**

## Notes

- **Activation requirement:** This function only produces a visible effect when called on an actor that is a PlayerPawn-based class (e.g., `DoomPlayer`, or a custom class inheriting from it). Calling it on non-player actors succeeds but does nothing.
- **Network-side behavior (Zandronum):** The screen blend is a clientside-only visual effect. The function executes on the server and is replicated to clients, but does not require special network handling as it affects UI state only.
- **Comparison to A_SetTranslucent:** Do not confuse this with `A_SetTranslucent`, which controls an actor's own rendering opacity and blend mode in the game world. `A_SetBlend` is a screen-space overlay effect applied to the player's view, not an actor property.

## Examples

A custom player class that briefly flashes the screen red when taking unfiltered damage:

```text
class MyCustomPlayer : DoomPlayer
{
	States
	{
	Pain.Flinch:
		PLAY O 4 A_SetBlend("FF0000", 0.5, 10);
		PLAY O 4 A_Pain;
		Goto Spawn;
	}
}
```

A custom stimpack that briefly flashes green when picked up:

```text
class GreenStimpack : Stimpack
{
	States
	{
	Pickup:
		TNT1 A 0 A_SetBlend("00FF00", 0.3, 15);
		Stop;
	}
}
```

## See also

- [A_FadeIn](a_fadein.md), [A_FadeOut](a_fadeout.md), [A_FadeTo](a_fadeto.md) — related actor-opacity animation functions.
- [A_SetTranslucent](a_settranslucent.md) — sets an actor's own alpha and render style (distinct from screen blend).
