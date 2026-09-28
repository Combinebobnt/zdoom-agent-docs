# `action native A_SetBlend(color color1, float alpha, int tics, color color2 = "")`

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.3-alpha @bdd0f7beb (2026-09-26)
**Provenance:** ZDoom Wiki `A_SetBlend` (retrieved 2026-08-01, https://zdoom.org/w/index.php?title=A_SetBlend&oldid=54493) + verified against the Zandronum source's `src/thingdef/thingdef_codeptr.cpp:3499-3515`, `src/g_shared/a_flashfader.cpp:16-59`, `src/thingdef/thingdef_parse.cpp:99-122` and `src/cl_main.cpp:9426-9462`, and UZDoom's `src/playsim/p_actionfunctions.cpp:1903-1923`.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** action function (defined on `AActor`; only takes effect when called on a PlayerPawn-based actor).

Applies a tinted color fade effect to a player's screen, animating from one color to another over a specified number of tics. This affects the player's visual perception only — it does not change any game-world state.

## Parameters

- **color1**: The initial color of the screen tint. Its opacity at the start of the fade is **alpha**. On UZDoom it can be given as a color string (e.g. `"FF0000"` for red) or as an integer (`0xFF0000`). On Zandronum the parser reads it as a color string only (`"RRGGBB"`, `"#RRGGBB"`, `"#RGB"`, `"RR GG BB"` or a color name, with `"none"` giving black; `thingdef_parse.cpp:99-122`), so write colors as strings there.
- **alpha**: Float between 0.0 (transparent) and 1.0 (fully opaque) for the initial color **color1**. On Zandronum neither the action nor the fader clamps it (`thingdef_codeptr.cpp:3512`, `a_flashfader.cpp:61-73`), so keep it within that range.
- **tics**: Integer number of tics over which the blend effect fades. A value of 0 ends the fade on its first tick at the destination values, so **color1** is never shown (Zandronum `a_flashfader.cpp:52-57`).
- **color2** (optional): The destination color the screen tint fades toward over the duration specified by **tics**. **Engine-specific behavior:** In Zandronum, the RGB fades toward **color2** while the opacity always fades to 0. An omitted or empty **color2** (`""`) is replaced by **color1** (`thingdef_codeptr.cpp:3509-3510`), so the tint simply fades out in color1's hue. In UZDoom/GZDoom-family engines, **color2** defaults to the empty color (black), specifies the actual destination color, and the destination opacity is controlled by the **alpha2** parameter (see below).

## Engine-family divergence

**Zandronum:** The function takes exactly 4 parameters. The fade always animates from **color1** at **alpha** to fully transparent (alpha=0), completing over **tics**. A provided **color2** still sets the RGB the tint shifts toward while it fades, but the destination opacity is always 0. This limitation stems from the underlying `DFlashFader` class being called with a hardcoded destination alpha of 0 (`thingdef_codeptr.cpp:3512-3514`).

**UZDoom/GZDoom-family:** A fifth parameter, **alpha2** (float, defaults to 0.0), controls the destination opacity. The fade animates from **color1** at **alpha** to **color2** at **alpha2**. This lets the fade run between two different colors and opacities. It does not leave a persistent tint: `A_SetBlend` creates its fader with termination on, so when the fade ends the fader zeroes the end alpha and the blend clears (`src/playsim/a_flashfader.cpp:60-65`). **This extended signature does not exist in Zandronum and should not be used in mods targeting that engine.**

## Notes

- **Activation requirement:** This function only produces a visible effect when called on an actor with a player attached (a player's pawn, e.g. `DoomPlayer` or a custom class inheriting from it, controlled by a player). Calling it on non-player actors succeeds but does nothing, since the fader removes itself on its first tick (Zandronum `a_flashfader.cpp:47-51`). On a Zandronum server, a non-player caller still sends the fade command, with a player index computed from a null player pointer (`a_flashfader.cpp:26-27`), so avoid it in online play.
- **Network-side behavior (Zandronum):** On a server, creating the fader sends a dedicated flash-fader command to all clients (`a_flashfader.cpp:24-27`), and each client builds its own fader for that player (`cl_main.cpp:9426-9462`). The tint is drawn only on the screen of whoever is viewing that player (`shared_sbar.cpp:1688-1695`).
- **Comparison to A_SetTranslucent:** Do not confuse this with `A_SetTranslucent`, which controls an actor's own rendering opacity and blend mode in the game world. `A_SetBlend` is a screen-space overlay effect applied to the player's view, not an actor property.

## Examples

A custom player class that briefly flashes the screen red when in pain:

```decorate
ACTOR MyCustomPlayer : DoomPlayer
{
	States
	{
	Pain:
		PLAY G 4 A_SetBlend("FF0000", 0.5, 10)
		PLAY G 4 A_Pain
		Goto Spawn
	}
}
```

A pickup that briefly flashes the collecting player's screen green (a `CustomInventory` `Pickup` state runs with the player as `self`):

```decorate
ACTOR GreenFlashPickup : CustomInventory
{
	Inventory.PickupMessage "Green flash!"
	States
	{
	Spawn:
		STIM A -1
		Stop
	Pickup:
		TNT1 A 0 A_SetBlend("00FF00", 0.3, 15)
		Stop
	}
}
```

## See also

- [A_FadeIn](a_fadein.md), [A_FadeOut](a_fadeout.md), [A_FadeTo](a_fadeto.md) — related actor-opacity animation functions.
- [A_SetTranslucent](a_settranslucent.md) — sets an actor's own alpha and render style (distinct from screen blend).
