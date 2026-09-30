# addmenukey

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/gamedata/keysections.cpp`,
`src/menu/doommenu.cpp` and `src/d_main.cpp`, and the Zandronum source's `src/keysections.cpp`,
`src/menu/menudef.cpp` and `src/d_main.cpp`. `zandronum/docs/commands.txt` has no entry for this
command.

Syntax: `addmenukey <label> <command>`. A [KEYCONF](../../keyconf/concepts/keyconf-lump.md) command
that adds one rebindable control to the current key section, the one most recently started by
[`addkeysection`](addkeysection.md). In the Customize Controls menu it becomes a `Control` row:
the label on the left, the keys bound to the command on the right.

```text
addkeysection "My Mod Controls" mymodkeys
addmenukey "Dash" +mymod_dash
addmenukey "Use Medkit" "use Medkit"
defaultbind q +mymod_dash
```

## Behavior

- **KEYCONF only.** The body is gated on `ParsingKeyConf` (UZDoom `keysections.cpp:117`,
  Zandronum `keysections.cpp:125`). Anywhere else the command does nothing and prints nothing.
- **Exactly two arguments.** Any other count prints `Usage: addmenukey <description> <command>`
  and adds nothing. Quote a label or command that contains spaces.
- **No current section.** If no `addkeysection` has run yet, it prints
  `You must use addkeysection first.` and adds nothing. The rest of the lump keeps running.
- **No deduplication.** Adding the same label or command twice gives two rows.
- **Label.** A `$`-prefixed label is looked up in [LANGUAGE](../../language/concepts/language-lump.md) when drawn, as for MENUDEF items.
- **Command.** Stored verbatim. The row shows and edits the keys whose bind is exactly this
  string, compared case-insensitively, so `+mymod_dash` and `+mymod_dash; +use` are different
  commands. The same exact string is what the config save matches when it writes the section's
  binds under the section's ini name (see [`addkeysection`](addkeysection.md)).
- **Single-press binds only.** The row edits the ordinary bind list. The section's
  double-click binds are still saved and reloaded under its ini name, but KEYCONF cannot create
  one: `doublebind` is not in the KEYCONF allowlist, and [`defaultbind`](defaultbind.md) only
  touches single-press binds.

## Which section is "current"

The current-section index is a file-level variable that is only changed by `addkeysection`
(UZDoom `keysections.cpp:77`, Zandronum `keysections.cpp:89`). It is not reset between KEYCONF
lumps, so **it carries across lumps**: an `addmenukey` at the top of a lump with no
`addkeysection` of its own lands in the last section started by an earlier lump, which may belong
to another mod. Start every KEYCONF that adds keys with its own `addkeysection`.

The `restart` command re-runs KEYCONF on both engines, and the section list is rebuilt from
scratch, so a leftover index from the previous run is rejected with the usual error.

## Engine-family divergence

The command body is identical on both engines. The only difference is where the resulting rows
appear in the menu: at the bottom of UZDoom's top-level Customize Controls page, or after the
last built-in control in Zandronum's flat list. See
[`addkeysection`](addkeysection.md#engine-family-divergence).
