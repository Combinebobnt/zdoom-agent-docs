# `SetFont`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-07-29)
**Provenance:** `SetFont - ZDoom Wiki.html`
(`https://zdoom.org/w/index.php?title=SetFont&oldid=43079`), verified against
the Zandronum source's `src/p_acs.cpp` (`PCD_SETFONT`/`PCD_SETFONTDIRECT` at lines 11146-11154,
`DLevelScript::DoSetFont` at lines 4355-4369, the `DLevelScript` member declaration at
`p_acs.h:1073`, `Serialize`/constructor at `p_acs.cpp:3765-3794`), the Zandronum source's `src/v_font.cpp`
(`V_GetFont` at lines 313-345, the built-in font table around lines 2685-2766), and
the Zandronum source's `src/sv_commands.cpp` (`SERVERCOMMANDS_PrintHUDMessage`, lines 2452-2455) on
2026-07-29.
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** compiler builtin — `zt-bcc/src/builtin.c:91`: `{ "setfont", ";s" }`, compiling to
`PCD_SETFONT` (or, for a compile-time-constant string literal argument, the folded
`PCD_SETFONTDIRECT` form — same handler either way). Not a `zcommon.bcs` `special`-table entry.

## Syntax

```text
void SetFont(str fontlump);
```

## Scope and persistence — matches the wiki, verified structurally

`activefont` (and its string-name shadow, `activefontname`) is a **member field of the
`DLevelScript` object** (`p_acs.h:1073`/`1079`), i.e. per running-script-*instance* state, not a
global or per-map/per-player setting — confirming the wiki's "within only the script" claim rather
than just taking it on faith. Concretely:

- Every new script instance's constructor sets `activefont = SmallFont` (`p_acs.cpp:3794`) — each
  fresh run of a script (including a second concurrent instance of the *same* script number)
  starts back at the default font regardless of what an earlier/other instance set.
- The value survives the script's own blocking waits (`Delay`/`TagWait`/...): it's part of the
  object that gets serialized/saved (`p_acs.cpp:3765-3767`) and simply persists on the still-alive
  `DLevelScript` instance across tics.
- Once set, every subsequent `Print`/`PrintBold`/`HudMessage`/`HudMessageBold` call made by *that
  same script instance* uses it (`p_acs.cpp:10958`, `11037`, `11053`, `11071`, `11089` all read
  `activefont` directly) — exactly the wiki's claim, with no additional caveats found.

## Fallback behavior on an unresolvable name — not on the wiki

`DoSetFont` (`p_acs.cpp:4355-4369`) doesn't leave the previous font in place or error out if
`fontlump` doesn't resolve to anything loadable; it unconditionally overwrites the current font:

```text
activefont = V_GetFont(fontname);
if (activefont == NULL)
    activefont = SmallFont;
```

So an unrecognized `fontlump` silently **resets the script's active font to `SmallFont`**, even if
a different, valid font had been set earlier in the same script — not a no-op, and not
distinguishable from an explicit `SetFont("SmallFont")` call. There's no error, warning, or return
value (the function is `void`) to detect the failure; use the sibling `CheckFont(str):bool`
(extension function -73, a real implemented case in the Zandronum engine fork's `ACSF_CheckFont` switch, verified
at `p_acs.cpp:6731-6732` — not one of the never-backported ACSF stubs) beforehand if the script
needs to tell "my font loaded" from "silently fell back."

## Name resolution order (`V_GetFont`) — confirms the wiki's picture-as-font trick is real

`V_GetFont` (`v_font.cpp:313-345`) tries, in order:

1. An already-registered `FFont` by name (`FFont::FindFont`) — covers every `FONTDEFS`-defined
   font and the engine's built-ins: `SmallFont`, `SmallFont2` (aliases to `SmallFont` outside
   Strife, confirmed at `v_font.cpp:2703-2711`), `BigFont`, and `ConFont` (registered under the
   lump name `CONFONT` but the wiki's engine-internal name `ConsoleFont`, confirmed at
   `v_font.cpp:2742-2744`) — all still present in the Zandronum engine fork exactly as the wiki lists them.
2. A single-lump `FON`/`FON2`-format font lump matching `fontlump`'s name.
3. **A plain texture/graphic matching `fontlump`'s name**, wrapped as a one-character
   `FSinglePicFont` — this is the real mechanism backing the wiki's "use `SetFont` with an image's
   name, then `HudMessage` the single letter `A`" trick; verified as a genuine, unconditional
   fallback branch, not a documentation myth.

No divergence found between the wiki's font list/picture-trick description and the Zandronum
engine fork's behavior.

## Zandronum-only netcode note (absent from the ZDoom wiki, which predates Zandronum's client/server split)

The server process has no screen and can't actually build an `FFont` — `V_GetFont` returns `NULL`
there, so `DoSetFont` always falls through to `activefont = SmallFont` on the server side
regardless of what name was requested. To still tell clients which font a HUD message should
render in, the server separately tracks the **name string** (`activefontname`, set unconditionally
in `DoSetFont` before the `NULL` check collapses `activefont`) and includes it in the
`HUDMESSAGE_SEND_FONT`-flagged replication payload whenever `activefont != SmallFont` would have
been true on a client (`sv_commands.cpp:2452-2455`) — i.e. the flag is really keyed off "was a
non-default font requested," reconstructed from the name rather than from the (always-`SmallFont`
on the server) pointer. Not something a script author needs to act on, but explains why
`activefontname` exists as a separate field at all.

## Engine-family divergence: unresolved-name fallback and default font

UZDoom's `DLevelScript::DoSetFont` does not carry Zandronum's "unconditionally reset to `SmallFont`
on failure" behavior. It simply does `activefont = V_GetFont(fontname)` and stops there — if the
name doesn't resolve, `activefont` becomes a null pointer, not `SmallFont`. The engine-wide
`V_GetFont` UZDoom calls can itself return null (when none of its resolution steps, described
below, find anything), so a failed `SetFont` genuinely leaves the script instance's font pointer
null rather than pinned to a known font.

The default value differs too: a fresh `DLevelScript` instance's font field is null-initialized at
construction, not assigned `SmallFont` the way Zandronum's constructor does. So "never called
`SetFont`" and "called `SetFont` with an unresolvable name" are the same null state on UZDoom,
where Zandronum treats the former as `SmallFont` from the start and the latter as an explicit reset
to `SmallFont`.

What actually happens with a null font is decided later, at the point a message is built, not at
`SetFont` time. Every one of `Print`, `PrintBold`, `HudMessage`, and `HudMessageBold` ultimately
constructs the same underlying message object, and *that* constructor is where a null font gets
resolved — with a short fallback chain rather than a flat substitution: use the given font if
non-null; otherwise, if a global "generic UI" flag is set, use an alternate built-in font; otherwise
use `SmallFont` if it can render the message text; otherwise fall back further to the IWAD's
original small font if *that* can render it; and only past all of those does it land on the same
alternate built-in font as the "generic UI" case. In practice this usually ends up picking
`SmallFont`-equivalent output for plain ASCII text, so a script that never touches non-Latin
characters may not observe a difference — but the choice is now content- and cvar-dependent instead
of the deterministic, immediate "always exactly `SmallFont`" that Zandronum guarantees, and it's
decided independently at every single `Print`/`HudMessage` call rather than fixed once when the bad
`SetFont` call happened.

Separately, UZDoom's font name resolution (`V_GetFont`) accepts a broader set of names than the
lookup order described above: a handful of legacy/alternate names are redirected before lookup
(e.g. a name matching the built-in big font's old lump name resolves to the big font, and the
console font's lump name resolves to the console font, alongside its documented in-engine name), an
all-uppercase-style name that fails outright falls back to trying the big font, and — beyond a
single `FON`/`FON2` lump or a plain texture — a font can also be assembled from a whole folder of
same-named patch lumps, with the newest-loaded matching resource (folder or single lump) taking
precedence over older ones of the same name. None of this changes the SmallFont/BigFont/ConFont/
picture-as-font cases the wiki and the existing verification above already cover — it only means
some `fontlump` names that would fail to resolve (and thus trigger the divergence above) on
Zandronum can succeed on UZDoom.

## See also

[`HudMessage`](hudmessage.md), [`HudMessageBold`](hudmessagebold.md), `Print`, `PrintBold` (not all
documented in this tree yet) — every one of them reads whatever `SetFont` last set for that script
instance. `CheckFont` (extension function -73, real/implemented in the Zandronum engine fork) for validating a name
before committing to it, since `SetFont` itself gives no success/failure signal.
