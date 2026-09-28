# The `MEDALDEF` lump

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** Zandronum Wiki `MEDALDEF` (https://wiki.zandronum.com/w/index.php?title=MEDALDEF&oldid=2286, retrieved 2026-09-09); verified against the Zandronum source's `src/medal.cpp` (MEDAL_Construct, lines 142-269) and `scoreboard_margin.cpp`; semicolon handling from `src/sc_man.cpp` (`ScanString`'s `AlreadyGot` path, lines 394-402; `TokenMustBe`, lines 540-548; `CheckToken`, lines 571-581) and `src/sc_man_scanner.re` (classic-scanner `;` comment rule, line 241).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0
(NonCommercial) — see [LICENSE](../../LICENSE) §2.

`MEDALDEF` declares medals: named, floaty-icon awards (frag streaks, domination, accuracy, and
similar per-player milestones) that spawn a `FloatyIcon`-descendant actor over a player's head and
optionally show text, a sound, an announcer entry, and a scoreboard icon. Custom medals can be
awarded to players at runtime using either the ACS function `GivePlayerMedal` or the DECORATE
action `A_GivePlayerMedal`. It is a plain text lump of named blocks, each holding a small command
language, parsed once at startup by `MEDAL_Construct`.

## Grammar

```text
MedalName
{
    Icon = "GFXLUMP"
    Class = "FloatyIcon"
    State = "StateName"
    AddFlag AlwaysShowQuantity
}
```

Unlike `ANCRINFO`/`CMPGNINF`'s anonymous `{ }` blocks, every `MEDALDEF` block is named: the bare
token before `{` becomes the medal's identifying name. The parser is `FScanner`-based and reports
errors through `sc.ScriptError`, which routes straight to `I_Error`: a bad `MEDALDEF` file does not
just fail to load, it aborts the engine at startup with that message on screen. This is the same
fatal behavior `VOTEINFO`/`SCORINFO`/`AUTHINFO` share, but `medal.cpp` never calls `SetCMode(true)`
the way `VOTEINFO`'s scanner does. `FScanner`'s `CMode` flag defaults to false, so `MEDALDEF` runs
the scanner's default "classic Hexen scanner" tokenizer rather than the C-mode one, despite sharing
the same fatal `sc.ScriptError` behavior as the other modern-generation lumps.

Inside a block, each command is a bare keyword read positionally. Ten of the twelve commands take
the shape `key = "value"`, where the value must be a quoted string (an empty string is itself a
fatal error); the remaining two, `addflag` and `removeflag`, take a bare, unquoted enum-name token
directly afterward, with no `=` at all. That token is only the flag's own name, not the
`MEDALFLAG_` prefix: `sc.MustGetEnumName` prepends `"MEDALFLAG_"` to whatever the lump wrote and
uppercases the result before the enum lookup, so `AddFlag KeepBetweenLevels` (any case) is what a
`MEDALDEF` file actually writes, not `AddFlag = "MEDALFLAG_KEEPBETWEENLEVELS"`.

## The twelve commands

- **`icon = "lump"`**, the `FTextureID` shown on-screen when the medal is awarded, resolved via
  `TexMan.CheckForTexture` against `TEX_MiscPatch`. Fatal if the named texture doesn't resolve.
  Every medal must have a valid icon by the time its block closes.
- **`scoreboardicon = "lump"`**, a separate icon shown on the scoreboard (rendered by the
  `DrawMedals` scoreboard margin command), resolved the same way as `icon`. Optional: if left
  unspecified, rendering falls back to `icon`. **Important:** if specified but the texture doesn't
  resolve, parsing is fatal — there is no runtime fallback (see "Wiki/engine divergence" below).
- **`class = "ClassName"`**, the `FloatyIcon`-descendant class spawned above the player's head.
  Fatal if the class doesn't exist or doesn't inherit from `FloatyIcon`. Setting `class` also
  resets the medal's previously chosen `state` back to unset, so a block that changes `class`
  without also re-specifying `state` afterward will fail the end-of-block check below.
- **`state = "StateName"`**, a state looked up by name within the medal's *current* `class`.
  Fatal if `class` hasn't been set yet in this medal's history, or the named state doesn't exist
  on it. Every medal must have a valid state by the time its block closes.
- **`text = "string"`**, the text shown under the medal icon when it displays on-screen. A value
  starting with `$` is treated as a string-table lookup (`GStrings`) rather than literal text.
- **`textcolor = "name"`**, the color name used to draw `text` on-screen, resolved through
  `V_FindFontColor`.
- **`quantitycolor = "name"`**, the color name used to draw the "x N" quantity suffix on-screen
  when multiple copies of the same medal are earned. Unlike `textcolor`, this is stored as a raw
  string and spliced as a color escape (e.g., `\c[Gold]`) directly into the suffix during rendering,
  not resolved through the same `V_FindFontColor` lookup.
- **`announcerentry = "name"`**, the name of an `ANCRINFO` event entry to play when the medal is
  triggered. This entry plays only when the medal is awarded to the local player (i.e., when the
  console player is looking through that player's eyes).
- **`lowermedal = "MedalName"`**, marks another, already-defined medal that this one supersedes.
  When this medal is awarded and the lower medal is currently displayed in the player's medal
  queue, this medal instantly replaces it. Fatal if the referenced medal doesn't exist yet, or if
  a medal names itself as its own lower medal.
- **`sound = "name"`**, an `FSoundID` played when the medal triggers. This sound plays only when
  the medal is awarded to a player other than the console player (i.e., when someone else gets the
  medal and you're not looking through their eyes). If awarded to the console player, the
  `announcerentry` plays instead.
- **`addflag FlagName`**, ORs a flag into the medal's flag word. Two flags exist:
  - `KeepBetweenLevels`: the player's earned count for this medal survives a normal per-level
    reset. `MEDAL_ResetPlayerMedals` only clears it when the reset is a full one (e.g., the player
    leaving the game).
  - `AlwaysShowQuantity`: always append the "x N" quantity suffix to the medal's text when
    displaying it on-screen, instead of only when the icon row would otherwise reach or exceed
    320 pixels in width.
- **`removeflag FlagName`**, clears a previously set flag by the same name (bitwise AND-NOT), the
  inverse of `addflag`.

## Re-opening a block extends the existing medal by name, in place

Each time the top-level loop reads a medal name, it looks the name up via `MEDAL_GetMedal` (an
`FName` comparison, which is case-insensitive). If a medal with that name already exists, the
parser reuses the *same* `MEDAL_t` object rather than creating a new one; only a genuinely new name
allocates a fresh medal and pushes it onto the medal list. There is no separate "override" syntax:
naming a block after an existing medal is how you extend it.

What "extend" means depends on the command: `addflag`/`removeflag` are the only two commands that
combine with the medal's prior state (bitwise OR / AND-NOT against whatever flags already existed).
Every other command is a plain overwrite: re-declaring `icon`, `text`, `sound`, or any other
single-value field in a later block simply replaces whatever the field held before, with no way to
explicitly clear a field back to unset short of assigning it a new value. This is a different merge
shape than `ANCRINFO`'s `Default`-block special case: here, *any* re-used name merges into its
existing medal, not just one reserved name.

## Every block must end with an icon, a class, and a state resolved

Immediately after a block's closing `}`, before the parser moves on to the next medal name token,
it checks the medal's current `icon`, `class`, and `state` in that order and calls `sc.ScriptError`
on the first one that's still unset: an invalid `icon` texture ID, a null `iconClass`, or a null
`iconState`. Because the check reads the medal's *cumulative* state rather than what the current
block occurrence itself set, a re-opened block that only tweaks something like `text` or `sound`
passes trivially as long as an earlier occurrence (in this lump or an earlier-loaded one) already
supplied all three. A medal defined from scratch, however, must supply `icon`, `class`, and `state`
before its own closing brace, or `sc.ScriptError` aborts the engine at startup, per the fatal
`I_Error` behavior described above.

## The engine ships its own `MEDALDEF`

The engine's own `wadsrc/static/medaldef.txt` ships 21 stock medals (`Excellent`,
`Domination`, `FirstFrag`, `Capture`, and similar), loaded the same way and at the same point in
`d_main.cpp`'s fixed parse order as a mod's own `MEDALDEF`. Because loading is cumulative across
every loaded archive and re-using a name merges into the existing medal rather than creating a
competing one, a mod that declares a block named e.g. `Excellent` is not adding a second, separate
medal: it is extending the engine's own stock `Excellent` medal in place, per the merge rule above.

## Example

The wiki provides a worked example. Ideally, define your own `FloatyIcon`-descendant class rather
than modify the engine's stock one, to avoid conflicts with other mods:

```decorate
Actor MyCustomFloatyIcon : FloatyIcon
{
   States
   {
       SingleKill:
           SING A -1
           Stop
   }
}
```

Then declare the medal in `MEDALDEF`:

```text
SingleKill
{
   Icon = "SINGA0"
   Class = "MyCustomFloatyIcon"
   State = "SingleKill"
   Text = "Single kill!"
   TextColor = "Gold"
   QuantityColor = "Grey"
   AnnouncerEntry = "SingleKill"
}
```

When a player receives this medal, it spawns a `MyCustomFloatyIcon` actor over their head and uses
the `SingleKill` state to display it.

## Wiki/engine divergence

Two claims in the wiki page diverge from the actual source implementation:

1. **ScoreboardIcon fallback.** The wiki states "If left unspecified, or if the graphic doesn't
   exist, then the Icon is used instead." This is only partially true. If `ScoreboardIcon` is
   **left unspecified**, it defaults to an invalid texture ID and rendering falls back to `Icon`
   (verified in `scoreboard_margin.cpp`'s `DrawMedals::GetMedalIcon`, which both its `Refresh`
   and `Draw` use). However, if `ScoreboardIcon` is
   **specified but the texture doesn't exist**, parsing aborts the engine at startup with
   `sc.ScriptError`, the same as a missing `Icon` — there is no silent fallback in this case.

2. **Trailing semicolons.** The wiki's syntax-box example shows `Property = "<value>";` with
   semicolons, but the wiki's own worked example contains no semicolons. The parser does **not**
   expect or consume semicolons. After a value, the block loop's check for `}` reads the `;`
   in token mode, where it is an ordinary token, and ungets it. The following command-name read
   takes that same `;` back as the command name. It is not `addflag`/`removeflag`, so the parser
   then demands `=` and gets the next keyword (or `}`) instead, aborting the engine at startup
   with an "Expected '=' but got ..." `sc.ScriptError`. The "Unknown option" branch is never
   reached. The classic scanner's rule that `;` starts a comment only applies to string-mode
   reads that come first, such as the top-level medal-name read. Inside a block every command
   read is preceded by that token-mode `}` check, so a `;` there is never a comment, while a
   stray `;` right after a block's closing `}` is silently skipped as one. Follow the wiki's worked example, not its syntax box.

## Engine-family divergence

UZDoom/GZDoom-family engines do not parse `MEDALDEF` and have no medal, floaty-icon, or
medal-queue subsystem of this shape to port it to.
