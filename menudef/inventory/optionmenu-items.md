# `OptionMenu` item keywords

**Generated:** by hand — no `tools/gen_inventory.py` extractor exists for this table yet, same
bootstrap state as `listmenu-items.md` in this same directory — see that file's header for why, and
`maintainer/plans/2026-09-09_menudef_section.md` for the plan this table fulfills.
**Tier:** C for every row (defaults to C until a `notes/` file promotes it).
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc51 (2026-09-09); Zandronum 3.3-alpha @bdd0f7beb43d (2026-09-09).

See [`concepts/item-dispatch-model.md`](../concepts/item-dispatch-model.md) for the dispatch
mechanism (`PClass::FindClass("OptionMenuItem" + keyword)` on UZDoom vs. a hardcoded
`sc.Compare(...)` chain in `ParseOptionMenuBody` on Zandronum). Out of scope for this table: block-header
settings (`ifgame`/`ifoption`, `Class`, `Title`, `Position`, `DefaultSelection`, `ScrollTop`,
`Indent`, and UZDoom's further additions).

The last two rows (`NetgameOnly`, `RequiresRconAccess`) are menu-level *flags* that set a
descriptor field rather than pushing an item onto it — listed here anyway since they're still
`ParseOptionMenuBody` keywords, just not ones with a class in the UZDoom-class/Zandronum-class
sense (see their own Notes cell).

This table supersedes the wiki page's four-item addition list
(`maintainer/_intake/menudef/MENUDEF - Zandronum Wiki.html`, `oldid=1549`): two of its four
(`TextField`, `NumberField`) turn out to be base-grammar items present on both engines, not
Zandronum-only, and the wiki names the remaining two differently than the actual keywords
(`PlayerField` matches, but `TeamField`/`PlayerClassField` are not real keywords — see
`JoinMenuTeamOption`/`JoinMenuPlayerClassOption` below). The wiki is also missing two real
additions it never mentioned (`ServerBrowserSlot`, `MicTestBar`).

| Keyword | UZDoom class | Zandronum class | Zan | UZD | Tier | Notes |
|---|---|---|---|---|---|---|
| Submenu | `OptionMenuItemSubmenu` | `FOptionMenuItemSubmenu` | yes | yes | C | |
| Command | `OptionMenuItemCommand` | `FOptionMenuItemCommand` | yes | yes | C | |
| SafeCommand | `OptionMenuItemSafeCommand` | `FOptionMenuItemSafeCommand` | yes | yes | C | confirms before running the bound command |
| Option | `OptionMenuItemOption` | `FOptionMenuItemOption` | yes | yes | C | |
| Control | `OptionMenuItemControl` | `FOptionMenuItemControl` (`map=false`) | yes | yes | C | |
| MapControl | `OptionMenuItemMapControl` | `FOptionMenuItemControl` (`map=true`) | yes | yes | C | UZDoom uses a dedicated subclass; Zandronum reuses one class with a bool |
| StaticText | `OptionMenuItemStaticText` | `FOptionMenuItemStaticText` | yes | yes | C | |
| StaticTextSwitchable | `OptionMenuItemStaticTextSwitchable` | `FOptionMenuItemStaticTextSwitchable` | yes | yes | C | |
| Slider | `OptionMenuItemSlider` | `FOptionMenuSliderCVar` | yes | yes | C | not the same keyword/class pair as `ListMenu`'s own `Slider` — see `listmenu-items.md` |
| ColorPicker | `OptionMenuItemColorPicker` | `FOptionMenuItemColorPicker` | yes | yes | C | |
| TextField | `OptionMenuItemTextField` | `FOptionMenuTextField` | yes | yes | A | near-identical `Init`/ctor signature and behavior on both engines (both carry a `[TP]` attribution comment even on the UZDoom side) — a base-grammar item, not a Zandronum-specific delta. [notes](../notes/textfield.md) |
| NumberField | `OptionMenuItemNumberField` | `FOptionMenuNumberField` | yes | yes | A | same as `TextField` — shared base-grammar item despite the wiki page's framing. [notes](../notes/numberfield.md) |
| PlayerField | — | `FOptionMenuPlayerField` | yes | no | A | `[TP]`; optional `nobots`/`notself` attribute list; Zandronum-only. [notes](../notes/playerfield.md) |
| JoinMenuTeamOption | — | `FOptionMenuTeamField` | yes | no | C | `[TP]`; the wiki page's "TeamField" is not the real keyword name |
| JoinMenuPlayerClassOption | — | `FOptionMenuPlayerClassField` | yes | no | C | `[TP]`; the wiki page's "PlayerClassField" is not the real keyword name |
| ServerBrowserSlot | — | `FOptionMenuServerBrowserLine` | yes | no | C | `[BB]`; not mentioned by the wiki page at all |
| MicTestBar | — | `FOptionMenuMicTestBar` | yes | no | C | `[AK]`; not mentioned by the wiki page at all |
| screenresolution | — | `FOptionMenuScreenResolutionLine` | yes | no | C | no `[TP]`/`[AK]`/`[BB]` attribution comment; confirmed absent from UZDoom's `menudef.cpp` and `ui/menu/*.zs` anyway |
| LabeledSubmenu | `OptionMenuItemLabeledSubmenu` | — | no | yes | C | UZDoom-only, postdates the Zandronum fork |
| ScaleSlider | `OptionMenuItemScaleSlider` | — | no | yes | C | UZDoom-only; plain-text display for scale-related settings |
| FlagOption | `OptionMenuItemFlagOption` | — | no | yes | C | UZDoom-only |
| DoubleTapControl | `OptionMenuItemDoubleTapControl` | — | no | yes | C | UZDoom-only |
| DoubleControl | `OptionMenuItemDoubleControl` | — | no | yes | C | UZDoom-only |
| JoyCurve | `OptionMenuItemJoyCurve` (`joystickmenu.zs`) | — | no | yes | C | UZDoom-only; in practice only constructed programmatically by the joystick-config menu builder, not typically hand-written in MENUDEF text, but reachable via this keyword since its `Init` is public |
| JoyMap | `OptionMenuItemJoyMap` (`joystickmenu.zs`) | — | no | yes | C | UZDoom-only; same programmatic-construction caveat as `JoyCurve` |
| Inverter | `OptionMenuItemInverter` (`joystickmenu.zs`) | — | no | yes | C | UZDoom-only; same caveat |
| JoyConfigMenu | `OptionMenuItemJoyConfigMenu` (`joystickmenu.zs`) | — | no | yes | C | UZDoom-only; same caveat |
| ReverbSaveSelect | `OptionMenuItemReverbSaveSelect` (`reverbedit.zs`) | — | no | yes | C | UZDoom-only; reverb-edit submenu item; same programmatic-construction caveat |
| ReverbSelect | `OptionMenuItemReverbSelect` (`reverbedit.zs`) | — | no | yes | C | UZDoom-only; same caveat |
| ReverbOption | `OptionMenuItemReverbOption` (`reverbedit.zs`) | — | no | yes | C | UZDoom-only; same caveat |
| SliderReverbEditOption | `OptionMenuItemSliderReverbEditOption` (`reverbedit.zs`) | — | no | yes | C | UZDoom-only; same caveat |
| NetgameOnly | — | sets `desc->mNetgameOnly = true` | yes | no | A | menu-level flag, not an item; `[TP]`; Zandronum-only. [notes](../notes/netgameonly.md) |
| RequiresRconAccess | — | sets `desc->mRequiresRCON = true` | yes | no | C | menu-level flag, not an item; `[AK]`; Zandronum-only |

`OptionMenuJoyEnable`, `OptionMenuJoyEnableInBackground`, and `OptionMenuJoyReset` (also in
`joystickmenu.zs`) are deliberately **not** MENUDEF keywords at all — their class names omit the
`Item` that `PClass::FindClass("OptionMenuItem" + keyword)` requires, so they can only be
constructed directly from ZScript (which the joystick-menu builder does), never from MENUDEF text —
not listed as rows above since they aren't reachable that way. Several other classes are
base/abstract and excluded from dispatch by a `protected`/private `Init` rather than by naming
(`OptionMenuFieldBase`, `OptionMenuItemOptionBase`, `OptionMenuSliderBase`,
`OptionMenuItemControlBase`) — see
[`concepts/item-dispatch-model.md`](../concepts/item-dispatch-model.md).
