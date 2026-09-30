# addkeysection

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28); Zandronum 3.3-alpha @bdd0f7beb (2026-09-28)
**Provenance:** written from the UZDoom source's `src/gamedata/keysections.cpp`,
`src/common/console/c_bind.cpp`, `src/gameconfigfile.cpp`, `src/menu/doommenu.cpp`,
`src/common/menu/menudef.cpp`, `wadsrc/static/menudef.txt` and
`wadsrc/static/zscript/engine/ui/menu/optionmenuitems.zs`, and the Zandronum source's
`src/keysections.cpp`, `src/c_bind.cpp`, `src/gameconfigfile.cpp`, `src/menu/menudef.cpp`,
`src/menu/optionmenu.cpp` and `wadsrc/static/menudef.txt`, plus both engines' `src/m_misc.cpp`
(`M_SaveDefaults`). The config-write consequence was also observed live on both engines.
`zandronum/docs/commands.txt` has no entry for this command.

Syntax: `addkeysection <menu title> <ini section name>`. A [KEYCONF](../../keyconf/concepts/keyconf-lump.md)
command that starts a new group of rebindable controls in the Customize Controls menu and makes it
the current section for the [`addmenukey`](addmenukey.md) lines that follow.

```text
addkeysection "My Mod Controls" mymodkeys
addmenukey "Dash" +mymod_dash
addmenukey "Toggle Radar" mymod_radar
```

## Outside KEYCONF

The whole command body sits behind the `ParsingKeyConf` flag (UZDoom `keysections.cpp:81`,
Zandronum `keysections.cpp:93`). Typed at the console, run from an alias, or reached any other way
after startup, it does nothing and prints nothing, not even its usage line.

## Arguments

- **Exactly two arguments.** Any other count prints
  `Usage: addkeysection <menu section name> <ini name>` and the line is skipped. Quote a title that
  contains spaces.
- **Menu title.** Shown as a header in the controls menu. A `$`-prefixed title is looked up in
  [LANGUAGE](../../language/concepts/language-lump.md) on both engines when drawn (UZDoom
  `wadsrc/static/zscript/engine/ui/menu/optionmenuitems.zs:77`, Zandronum
  `optionmenu.cpp:518`).
- **Ini section name.** Names the config-file sections that store the user's binds for this
  section's commands (below). Keep it to 32 characters or fewer; see "Engine-family divergence"
  for what each engine does past that.

## What it does

1. **Looks for an existing section to reuse**, then returns early if one matches. The comparison
   is not what it looks like: it compares each existing section's **menu title** against the new
   call's **ini name**, case-insensitively (UZDoom `keysections.cpp:97-104`, Zandronum
   `keysections.cpp:105-112`). See "Duplicate sections" below.
2. Otherwise **appends a new section** with the given title and ini name and makes it current.
3. **Loads the user's saved binds for that ini name immediately**, from the config sections
   `[<Game>.<ini>.Bindings]` and `[<Game>.<ini>.DoubleBindings]`, where `<Game>` is the game's
   config name (`Doom`, `Heretic` and so on). Each saved `key=command` entry is bound as-is,
   replacing whatever that key held (`LoadKeys`, UZDoom `keysections.cpp:39-55`, Zandronum
   `keysections.cpp:49-65`).

Step 3 matters for ordering. The engine's main bind sections are loaded before KEYCONF runs, but
a section's own saved binds land only when its `addkeysection` line executes. A
[`defaultbind`](defaultbind.md) for one of this section's commands must come after this line, or it
runs before the user's saved choice has been loaded.

## How the binds are saved

When the config is written, each key section is saved before the general bind lists
(`M_SaveCustomKeys`, called from `ArchiveGameData`: UZDoom `gameconfigfile.cpp:973`, Zandronum
`gameconfigfile.cpp:597`). For every action in the section, every key currently bound to exactly
that command string is written to `[<Game>.<ini>.Bindings]` (and the double-click binds to
`.DoubleBindings`), after clearing the section. Those keys are then left out of the general
`[<Game>.Bindings]` list (the marker logic in `FKeyBindings::ArchiveBindings`, UZDoom
`c_bind.cpp:499-527`, Zandronum `c_bind.cpp:582-610`).

Consequences:

- **A section's binds only apply while the mod is loaded.** With the mod removed there is no
  `addkeysection` to load them, and the general list never held them, so the player's keys are
  not left pointing at commands that no longer exist.
- **A mid-session config write loses these binds for good.** The exclusion works by marking the
  section's keys during the section pass and blanking them during the general pass. The blanked
  value is the live bind, so after `writeini` (both engines), or UZDoom's `openconfig` or the
  ZScript `CVar.SaveConfig()`, every key bound to a key-section command is unbound for the rest of
  the session. The file that write produces is correct, but the save at exit runs again with those
  keys blank: it clears the section and writes it back empty. At the next start only a
  [`defaultbind`](defaultbind.md) whose key is still free brings a bind back; any key the player
  chose is gone. Observed live on both engines (2026-09-29, local test builds, probe KEYCONF and a
  throwaway config): right after `writeini` the section held both binds, `bind` showed both keys
  empty, a plain control bind survived, and after quitting the section was empty.
- **`writeini <file>` also moves the exit save to `<file>`.** `M_SaveDefaults` restores the config
  path from the new name instead of the saved old one (UZDoom `m_misc.cpp:358`, Zandronum
  `m_misc.cpp:408`), so the empty section lands in `<file>` and the original config keeps its last
  contents. Observed live on Zandronum; UZDoom from source.

## Duplicate sections

Because the reuse check compares title against ini name, repeating the same line does **not**
reuse the section:

```text
addkeysection "My Mod Controls" mymodkeys
addkeysection "My Mod Controls" mymodkeys   // creates a second section
```

The second call finds no section titled `mymodkeys`, so it appends another section with the same
title and ini name. The menu then shows the title twice, each header with its own entries. On
save, both sections write to the same `[<Game>.mymodkeys.Bindings]` section and each clears it
first, so only the later section's binds survive. The earlier section's commands come back
unbound at the next start (or rebound by `defaultbind`, if the key is still free).

To add to a section from a second KEYCONF lump, rely on the current section instead: `addmenukey`
appends to whatever section was current at the end of the previous lump (see
[`addmenukey`](addmenukey.md)). A repeat `addkeysection` only reuses a section when its ini-name
argument equals an existing section's title, ignoring case.

## How the menu shows it

KEYCONF runs before the menus are built. Once MENUDEF is parsed, the engine takes the menu named
`CustomizeControls` and, if it is an option menu, appends each key section to the end of it in
KEYCONF order: a blank line, the title as a header-coloured static text, then one `Control` row
per `addmenukey` action (UZDoom `InitKeySections`, `doommenu.cpp:1051-1080`; Zandronum
`InitKeySections`, `menudef.cpp:1357-1383`). These are the same item types as MENUDEF's
`StaticText` and `Control` (see [the option-menu item inventory](../../menudef/inventory/optionmenu-items.md)),
and the `Control` rows edit the ordinary single-press binds.

## Engine-family divergence

- **Where the sections appear.** UZDoom's `CustomizeControls` (`wadsrc/static/menudef.txt:515`)
  holds only submenu links for the control categories, a layout option and the reset command, so
  KEYCONF sections appear at the bottom of that top-level page, below the reset command, not
  inside any category submenu. Zandronum's `CustomizeControls`
  (`wadsrc/static/menudef.txt:447`) is one flat list of every control, so the sections appear
  after the last built-in control.
- **Mod MENUDEF replacing the menu.** UZDoom declares `CustomizeControls` as `protected`: a mod's
  own `OptionMenu "CustomizeControls"` has its new items appended under a separator instead of
  replacing the menu, and a replacement of a different menu type is refused
  (`ReplaceMenu`, `src/common/menu/menudef.cpp:739`). Zandronum lets a mod replace it outright
  with another option menu (refusing only a different menu type, `menudef.cpp:470-487`), and the
  KEYCONF sections are appended to the replacement.
- **Ini names over 32 characters.** Zandronum truncates the argument in place to 32 characters,
  so the stored name, the load and the save all use the truncated name. UZDoom logs a warning
  and truncates only a copy used for the reuse check; the section keeps the full name. Its load
  path formats the config section name into a 64-byte buffer (`keysections.cpp:41-44`) while the
  save path does not, so a long name is saved in full but looked up truncated. If the game's
  config name plus the ini name exceeds 47 characters, the saved double-click binds never
  reload; past 53, the single-press binds don't either.
