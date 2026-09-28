# The `SKININFO` lump

**Tier:** A
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-27)
**Provenance:** Zandronum Wiki [SKININFO](https://wiki.zandronum.com/w/index.php?title=SKININFO&oldid=2216)
(retrieved 2026-09-09) + verified against the Zandronum source's `src/r_data/sprites.cpp:509-1023` (`R_InitSkins`), `src/r_data/sprites.cpp:1075-1096` (`R_CreateSkin`), `src/d_netinfo.cpp:315-334` (`D_PlayerClassToInt`), `src/s_advsound.cpp:460-472` (`S_FindSoundNoHash`).
**Wiki license:** Derived from the Zandronum Wiki; this file as a whole is CC BY-NC-SA 4.0
(NonCommercial) — see [LICENSE](../../LICENSE) §2.

`SKININFO` declares player skins: alternate player sprites with their own sounds, status-bar
face, scale, and menu visibility. It is parsed by the same function, `R_InitSkins`, that also
parses the much older `S_SKIN` lump. `SKININFO` is the newer dialect that lets one lump declare
several skins in `{ }`-delimited blocks; `S_SKIN` is the original flat dialect, one skin per lump
with no braces at all. This page documents `SKININFO`'s own grammar and keys; `S_SKIN` is
described only as far as needed to explain how the shared parser tells the two dialects apart.

## One function, two lump names, one dialect flag

`R_InitSkins` runs a single outer loop over lump names: it first walks every loaded archive for a
lump named `S_SKIN` (`Wads.FindLump`, cumulative across WADs like every lump in this section), and
once that search is exhausted it resets its lump cursor and starts walking every archive again for
a lump named `SKININFO`. Each lump instance found, under either name, gets one `FScanner` opened
over it and is fed into the same parsing logic.

Which dialect that logic uses for a given lump is decided by content, not by which of the two
names matched, via a three-state local (`s_skin`: 1 = undetermined, 0 = confirmed braced
`SKININFO`-style, 2 = confirmed flat `S_SKIN`-style and locked). Every lump starts undetermined.
The very first token of the lump's first skin block is checked for a literal `{`: if it is one,
the lump switches into the braced dialect for the rest of its contents; if it isn't, the dialect
locks permanently to the flat, single-skin `S_SKIN` form (a bare run of `key = value` pairs ended
implicitly by running out of tokens, not by a closing brace) and it stays that way for the rest of
that lump. In principle an `S_SKIN` lump that happens to open with `{` would be parsed in the
braced dialect too. The reverse doesn't work the same way: because a `SKININFO`-named lump always
runs the eat-before-`{` step described next, a `SKININFO` lump that never contains a `{` at all
doesn't fall back to the flat form either; the scanner exhausts every token looking for a brace
that never appears, and the pending skin fails to parse (see "Malformed keys and per-dialect
recovery" below).

## The legacy "eat everything before `{`" quirk

Only when the *lump name itself* is `SKININFO` (not when the flat-vs-braced check above is what
decides the dialect), the parser runs one more step before each skin block: it discards tokens one
at a time until it finds a literal `{`, per the source's own comment that "the original SKININFO
parser ate everything before the starting bracket" and that this is kept "to retain compatibility
with existing wads." In practice this means anything sitting between the end of one skin's closing
`}` and the next skin's opening `{` inside a `SKININFO` lump, or before the first skin's `{`, is
silently skipped rather than being read as a key. Tokens after the *last* skin's `}` are not
skipped the same way: the discard step runs out of tokens without finding a `{`, the leftover
token is then read as a key with no `=` after it, and the already-finished last skin gets the
"Bad format for skin" warning and is removed. If a non-empty `SKININFO` lump contains no `{` at all,
this discard step consumes every remaining token in the lump without ever finding one; the parser
then still tries to read a key/value pair, finds nothing left to read, and prints a "Bad format
for skin" warning for that pending skin rather than quietly doing nothing (see "Malformed keys and
per-dialect recovery" below). `S_SKIN` lumps never run this discard step at all, since it only
fires for lumps found under the `SKININFO` name.

## Braced multi-skin dialect

Within a lump parsed in the braced dialect, a skin's key list runs until a literal `}` ends that
skin's block. The outer loop then reads on: if the next token it finds is another `{`, a
brand-new skin is created sharing the same lump, rather than the lump ending there; if the lump
has simply run out of tokens, that skin was the last one in it. This is the entire point of the
newer dialect: one `SKININFO` lump can declare an arbitrary number of skins. The flat `S_SKIN`
dialect has no such mechanism, per the source's own comment that "`S_SKIN` generally contains one
skin in a lump, unless converted to `SKININFO`," so a mod wanting several skins from one lump needs
the braced form.

```text
{
    name = "Marine Two"
    sprite = "PLAY"
    scale = "1.0"
    hidden = "true"
    dsplpain = "myskpain"
    *taunt = "myskntaunt"
}
{
    name = "Marine Three"
    sprite = "PLA2"
    class = "Marine"
}
```

## Malformed keys and per-dialect recovery

A key with no `=` after it doesn't stop the whole lump with a fatal error: the parser prints a
`Bad format for skin <N>: <key>` warning and marks that one skin for removal. A `game` or `class`
value the engine can't use follows the same removal path, and stops reading that skin's remaining
keys immediately rather than finishing the block first.

What differs between the two dialects is what happens to the rest of the lump once a skin is
marked for removal. In the braced dialect, a removed skin is fast-forwarded to its own closing `}`
and the outer loop continues into whatever follows, so one bad skin doesn't take the rest of the
lump down with it; a source comment notes this finish-parsing-to-`}` step specifically exists to
stop the last skin in a multi-skin lump from being removed twice over in edge cases. In the flat
`S_SKIN` dialect there is no closing `}` to fast-forward to, so a removed skin simply ends parsing
for that entire lump.

## The 11 general keys

Every key is matched case-insensitively. Unless noted, an unrecognized value for a key never
raises an error: it is either ignored, leaving the field at its default, or mapped to a fallback
(see `gender`, `scale` and `game` below).

- **`name`**: sets the skin's display name. If it collides (case-insensitively) with an
  already-registered skin's name, the new skin is silently renamed to `skin<index>` and a warning
  is printed; this is not a fatal error.
- **`sprite`**: the 4-character sprite name supplying this skin's frames (forced to upper case).
  Omitting it only has a defined fallback in the flat `S_SKIN` dialect, where the parser instead
  uses whatever lump name immediately follows the marker lump; that fallback never fires for a
  braced `SKININFO` block. A `SKININFO` block that never sets `sprite` isn't left broken by this,
  though: every skin is pre-initialized, before any key is even read, to the default sprite of the
  first registered player class (`PlayerClasses[0]`), so an omitted `sprite` key just means the
  skin keeps that sprite rather than getting one of its own. This holds even for a skin bound by
  `class` to a different player class.
- **`crouchsprite`**: an optional separate 4-character sprite name used for the crouching pose.
  If it's absent, or equal to `sprite`, no separate crouch sprite is generated.
- **`face`**: a 3-character status-bar face prefix. If fewer than 3 non-null characters are
  supplied, the face prefix is discarded back to empty rather than kept partial.
- **`gender`**: the skin's gender, which selects which gendered variant of a player sound plays.
  Accepts `female`, `other`/`cyborg` (neuter) or `0`/`1`/`2`; any other value means male.
- **`scale`**: a single uniform scale factor applied to both axes (there is no separate X/Y scale
  key here), clamped to a fixed-point range of roughly `1/65536` up to `256.0`. A non-numeric value
  parses as 0 and is clamped up to that `1/65536` minimum, not left at the default.
- **`game`**: restricts the skin to a specific game (`heretic`, `strife`, or anything else treated
  as the Doom-family default, which also covers Chex Quest since it shares Doom's game-type
  bitmask). A skin whose declared game doesn't match the currently running game stops reading its
  remaining keys immediately and is removed, following the same non-fatal removal path a malformed
  key takes (see "Malformed keys and per-dialect recovery" above). `game` and `class` (below) both
  ultimately choose which player class(es) the skin attaches to; a game that legitimately spans two
  player-class hierarchies (e.g. a Heretic skin exposed to a Doom-family game) is flagged
  internally as a cross-game skin rather than rejected outright.
- **`class`**: binds the skin to one specific player class instead of inferring one from `game`.
  The value is matched (case-insensitively) against each player class's `Player.DisplayName`
  (e.g. `Marine`), not its actor class name. When more than one player class is registered, a
  value matching none of them discards the skin, the same way a mismatched `game` does. When only
  one player class exists (stock Doom), any value is accepted and binds to that class.
- **`hidden`**: `true`/`yes` or `false`/`no` (case-insensitive); despite the name, `true` means
  the skin is **revealed** (visible in the skin menu), and `false` means it is **hidden** (not
  available without unlocking). Skins default to revealed (`bRevealed = true`) when the key is
  never given. A Skulltag-era addition, not present in the original ZDoom-lineage `S_SKIN` key set.
- **`cheat`**: `true`/`yes` or `false`/`no`, marking the skin as a "cheat" skin. Also a
  Skulltag-era addition alongside `hidden`.
- **`color`**: an arbitrary string copied verbatim into the skin's stored color/translation
  string, with no validation at parse time.

## Sprite frames are matched only within the lump's own archive

Once `sprite`/`crouchsprite` name a 4-character prefix, the actual frame lumps for it are searched
for only among lumps belonging to the *same archive* (WAD/PK3) as the `S_SKIN`/`SKININFO` lump
itself, not across the whole merged lump directory every other loaded archive contributes to. A
source comment explains this restriction exists because, without it, an older WAD ("hr.wad")
stopped working correctly. In practice, a mod's skin frames need to ship in the same archive as
its `S_SKIN`/`SKININFO` lump; frames sitting in a different loaded WAD/PK3 won't be picked up.

## The sound keys: two overlapping mechanisms

Anything not matching one of the 11 keys above is checked against two further, overlapping
mechanisms before finally falling back to a generic custom-property store (see below).

**Any key starting with `*`** is treated as a direct player-sound replacement: its value is looked
up as a sound lump, first in the skin's own namespace, then by full name with a fallback to the
sounds namespace. If found, the exact key `*pain` (case-insensitive) is special-cased to replace
all four of the standard pain-severity sounds (100%/75%/50%/25% health) in one shot. Any other
`*name` registers just that one named player-sound event, but only if a sound with exactly that
`*name` already exists in the sound table when skins load (typically declared through SNDINFO's
`$playersound`, which is parsed earlier at startup). The key isn't checked against a fixed list,
so a skin can use any player sound the mod declares; an undeclared name such as
`*mycustomevent` is silently dropped, with no warning.

**Nine further key names, none of them star-prefixed, are a closed legacy set** that each alias to
one or more of eighteen fixed built-in sound-event names (the same `*`-prefixed names as above,
just not typed with the star): `dsplpain` sets `*pain100`, `*pain75`, `*pain50`, `*pain25`, *and*
`*poison` all at once to the same replacement sound; `dsoof` sets `*grunt` and `*land`; `dspldeth`
sets `*death` and `*wimpydeath`; `dspdiehi` sets `*xdeath` and `*crazydeath`; `dsnoway` sets
`*usefail` and `*puzzfail`; `dsslop` sets `*gibbed` and `*splat`; `dspunch` sets `*fist`; `dsjump`
sets `*jump`; `dstaunt` sets `*taunt`. Their value is looked up in three steps: the skin's own
namespace, then the global namespace, then by full name with a fallback to the sounds namespace.
These nine names exist because they mirror the vanilla Doom
sound-lump names (`dsplpain`, `dsoof`, `dspldeth`, ...) that a skin historically overrode
one-for-one; using one of them is shorthand for setting every event it's grouped with to the same
sound, rather than setting each event individually the way the `*`-prefixed form does. The two
mechanisms aren't perfectly symmetric, either: the star form's `*pain` shortcut covers only the
four pain-severity sounds, while the legacy `dsplpain` key covers those same four plus `*poison`
in one shot.

## Anything else becomes a custom property

A key matching none of the above (not one of the 11 general keys, not a `*`-prefixed sound event,
not one of the nine legacy sound-alias names) is stored as a free-form custom property on the
skin instead of causing an error. Its value is auto-typed: an integer-looking string becomes an
int, a float-looking string becomes a float, `true`/`false` (case-insensitive) become a bool, and
anything else is kept as a string. This is a later addition layered onto the original parser and
gives a skin an open-ended metadata bag beyond the fixed key set above, without needing engine
changes to add a new named property.

## Wiki/engine divergence

The Zandronum Wiki's example skin block at the end of its page carries an unquoted `color` value:
`color = ff 00 00`. The scanner reads one token at a time per value (line 611 in `R_InitSkins`);
an unquoted sequence like this is tokenized as three separate whitespace-separated items (`ff`,
`00`, `00`). The parser reads `ff` as the value for `color`, then sees the next token `00` and
expects an `=` after it (the key-value syntax), finds none, prints `Bad format for skin`, marks
the skin for removal, and stops parsing that skin. A correctly-formed value must be a single
token, either quoted as a single string (`color = "ff0000"`) or structured as one token (e.g.
`color = ff0000`).

## Engine-family divergence

The `SKININFO` lump name and its braced multi-skin dialect exist only in Zandronum's fork of
`R_InitSkins`; the UZDoom/GZDoom-family source tree has no reference to a `SKININFO` lump at all.
UZDoom's own `R_InitSkins` (`src/r_data/sprites.cpp`) still parses `S_SKIN`, but only the flat,
one-skin-per-lump dialect described above as background: there is no dialect-detection flag, no
brace handling, and none of the eat-before-`{` quirk, since that quirk only exists to support the
`SKININFO` lookup Zandronum added on top. The Skulltag-era `hidden`/`cheat` keys and the custom
property fallback described above are Zandronum-side additions layered onto the shared parser and
likewise have no UZDoom counterpart.
