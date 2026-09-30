# LANGUAGE doc index

Router only. See `AGENTS.md` for scope and source locations, `../shared/AUTHORING.md` for
tiers/engine-scope/licensing.

**Both engines parse LANGUAGE's classic format**; the CSV format and `LMACROS` are UZDoom-only.
For BCS/ACS language questions, see `../acs/INDEX.md` instead.

## Concepts

- [The LANGUAGE lump](concepts/language-lump.md) — tier A. When it's read; `[code ...]` sections,
  `default`/`*`/legacy codes (UZDoom remaps `enu` to `en-US`, the default table), `$ifgame`,
  escapes (`\xHH` UZDoom-only); lookup order (`[*]` beats the player's own language); override
  order across lumps (a mod's `[default]` string does not replace a stock one on Zandronum, and
  deletes earlier translations on UZDoom; `[enu default]` works on both); error severity; the
  `language` cvar is inert on non-Windows Zandronum; UZDoom-only CSV/`LMACROS`/`$$` redirects
  and `Obituary_<Class>` labels; server-side `l:` resolves against the server's strings.
- [Retrieving LANGUAGE strings](concepts/string-retrieval.md) — tier B. The consumer side of
  `$LABEL`: the two lookup primitives (return the label, or return null); a per-consumer table of
  the accepted form (`$LABEL`, MAPINFO `lookup`, ACS `l:` bare label), when the lookup runs
  (parse, event or draw time, so whether a `language` change applies live) and what a missing
  label shows; obituary fallbacks; Zandronum intermission `Text`/`Background` hazards; UZDoom's
  `StringTable.Localize`/`Screen.DrawText`/`$$`; which Zandronum messages resolve on the server
  and which on each client.
- [The CSV LANGUAGE format](concepts/csv-format.md) — tier B, UZDoom only. Detection (first bytes
  `default,`/`identifier,`, any case, no BOM); header columns (`identifier`/`filter`/`remarks`,
  multi-code language cells, BCP 47 tags with `-` or `_`, no `*` equivalent, only `default`
  triggers delete-earlier); quoting and escapes (`\"` doesn't work); `filter`; an empty cell
  deletes the string, even an earlier lump's; mixing with classic lumps; `LMACROS` (each lump
  clears earlier macros) and `@[name]` gender variants; the stock `language.csv` build; short rows
  are undefined behavior; Zandronum aborts at startup on a pure-ASCII CSV and skips a non-ASCII
  one as binary.
