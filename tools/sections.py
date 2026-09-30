"""Single manifest of every documentation section in this tree.

Every tool (lint_docs.py, gen_inventory.py, lookup.py) reads this instead of hardcoding
section names, paths, or archetypes — adding a section means adding one entry here, not
editing three scripts. See ../shared/ARCHETYPES.md for what each archetype tag means.

A section may not have every directory populated yet (e.g. a brand-new lump-format section
might start with just concepts/) — tools should treat a missing directory as "zero entries",
not as an error, and a missing INDEX.md as "not scaffolded yet", also not an error.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Shared markdown-table cell escaping, used by gen_inventory.py (writing), lint_docs.py and
# lookup.py (reading) alike -- a raw `|` in a cell value (e.g. a CVar's `CVAR_ARCHIVE |
# CVAR_NOSETBYACS` flag expression) would otherwise be misread as a column separator, silently
# shifting every later cell in that row. Escaping on write and unescaping on read must use the
# same rule or a round-trip (write, then read back for a preserve-by-key merge) silently
# corrupts -- found by --check producing a different result on every run before this existed.
_PIPE_SPLIT_RE = re.compile(r'(?<!\\)\|')


def escape_cell(value):
    return value.replace("|", "\\|").replace("\n", " ")


def split_row(line):
    """Split one markdown table row on unescaped `|` only, then unescape `\\|` back to a literal
    `|` in each resulting cell."""
    cells = _PIPE_SPLIT_RE.split(line.strip())
    if cells and cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    return [c.strip().replace("\\|", "|") for c in cells]

# Archetype tags — see ../shared/ARCHETYPES.md for the full schema of each.
CALLABLE = "callable"           # one file per callable, or a family file; Tier/Provenance/Engine
                                 # header block directly under the H1.
TABLE_INVENTORY = "table_inv"   # generated, complete; never hand-edited row-by-row. Carries a
                                 # **Generated:** marker instead of a Tier/Provenance header block.
TABLE_NOTES = "table_notes"     # curated half of a Table-of-entries section; same header block
                                 # as CALLABLE.
CONCEPT = "concept"             # prose; same header block as CALLABLE, no signature H1.

# Header-block archetypes: everything except generated inventory files carries the same
# Tier:/Provenance:/Engine: block directly under the H1.
HEADER_BLOCK_ARCHETYPES = (CALLABLE, TABLE_NOTES, CONCEPT)

# key -> {"index": "<section>/INDEX.md", "agents": "<section>/AGENTS.md", "dirs": {dir: archetype}}
# Optional "lumps": {LUMP NAME: "<rel path>"} maps a lump/format name to its entry concept page
# (lookup.py resolves it ahead of every other tier; lint_docs.py checks the target). LANGUAGE is
# deliberately absent: it would shadow the `language` console cvar row.
SECTIONS = {
    "acs": {
        "index": "acs/INDEX.md",
        "agents": "acs/AGENTS.md",
        "dirs": {
            "acs/functions": CALLABLE,
            "acs/families": CALLABLE,
            "acs/concepts": CONCEPT,
        },
        "lumps": {
            "BEHAVIOR": "acs/concepts/acse-object-format.md",
            "LOADACS": "acs/concepts/libraries.md",
        },
        # acs/INDEX.md predates the multi-section split and has its own alphabetical-order
        # convention for these three headings; other sections don't require this (yet) since
        # their INDEX.md layout is new and less established. Label -> exact heading text.
        "ordered_headings": {
            "Families": "## Families",
            "Functions > Prose (tier A/B)": "### Prose (tier A/B)",
            "Functions > Signature-only (tier C)": "### Signature-only (tier C)",
        },
    },
    "decorate": {
        "index": "decorate/INDEX.md",
        "agents": "decorate/AGENTS.md",
        "dirs": {
            "decorate/actions": CALLABLE,
            "decorate/classes": CALLABLE,
            "decorate/families": CALLABLE,
            "decorate/inventory": TABLE_INVENTORY,
            "decorate/notes": TABLE_NOTES,
            "decorate/concepts": CONCEPT,
        },
        "lumps": {"DECORATE": "decorate/concepts/actor-definition-syntax.md"},
    },
    "zscript": {
        "index": "zscript/INDEX.md",
        "agents": "zscript/AGENTS.md",
        "dirs": {
            "zscript/classes": CALLABLE,
            "zscript/families": CALLABLE,
            "zscript/concepts": CONCEPT,
        },
        "lumps": {"ZSCRIPT": "zscript/concepts/zscript-load-and-compile-order.md"},
    },
    "mapinfo": {
        "index": "mapinfo/INDEX.md",
        "agents": "mapinfo/AGENTS.md",
        "dirs": {
            "mapinfo/inventory": TABLE_INVENTORY,
            "mapinfo/notes": TABLE_NOTES,
            "mapinfo/concepts": CONCEPT,
        },
        "lumps": {"MAPINFO": "mapinfo/concepts/mapinfo-format.md"},
    },
    "gldefs": {
        "index": "gldefs/INDEX.md",
        "agents": "gldefs/AGENTS.md",
        "dirs": {
            "gldefs/inventory": TABLE_INVENTORY,
            "gldefs/notes": TABLE_NOTES,
            "gldefs/concepts": CONCEPT,
        },
        "lumps": {"GLDEFS": "gldefs/concepts/gldefs-overview.md"},
    },
    "sbarinfo": {
        "index": "sbarinfo/INDEX.md",
        "agents": "sbarinfo/AGENTS.md",
        "dirs": {
            "sbarinfo/inventory": TABLE_INVENTORY,
            "sbarinfo/notes": TABLE_NOTES,
            "sbarinfo/concepts": CONCEPT,
        },
        "lumps": {"SBARINFO": "sbarinfo/concepts/sbarinfo-lump-overview.md"},
    },
    "cvarinfo": {
        "index": "cvarinfo/INDEX.md",
        "agents": "cvarinfo/AGENTS.md",
        "dirs": {
            "cvarinfo/inventory": TABLE_INVENTORY,
            "cvarinfo/notes": TABLE_NOTES,
            "cvarinfo/concepts": CONCEPT,
        },
        "lumps": {"CVARINFO": "cvarinfo/concepts/declaration-syntax.md"},
    },
    "console": {
        "index": "console/INDEX.md",
        "agents": "console/AGENTS.md",
        "dirs": {
            "console/inventory": TABLE_INVENTORY,
            "console/notes": TABLE_NOTES,
            "console/concepts": CONCEPT,
        },
    },
    "sprites": {
        "index": "sprites/INDEX.md",
        "agents": "sprites/AGENTS.md",
        "dirs": {
            "sprites/concepts": CONCEPT,
        },
    },
    "bots": {
        "index": "bots/INDEX.md",
        "agents": "bots/AGENTS.md",
        "dirs": {
            "bots/inventory": TABLE_INVENTORY,
            "bots/notes": TABLE_NOTES,
            "bots/concepts": CONCEPT,
        },
        "lumps": {"BOTINFO": "bots/concepts/botinfo-lump.md"},
    },
    "zandronum-lumps": {
        "index": "zandronum-lumps/INDEX.md",
        "agents": "zandronum-lumps/AGENTS.md",
        "dirs": {
            "zandronum-lumps/concepts": CONCEPT,
            "zandronum-lumps/inventory": TABLE_INVENTORY,
            "zandronum-lumps/notes": TABLE_NOTES,
        },
        "lumps": {
            "ANCRINFO": "zandronum-lumps/concepts/ancrinfo.md",
            "AUTHINFO": "zandronum-lumps/concepts/authinfo.md",
            "CMPGNINF": "zandronum-lumps/concepts/cmpgninf.md",
            "GAMEMODE": "zandronum-lumps/concepts/gamemode.md",
            "MEDALDEF": "zandronum-lumps/concepts/medaldef.md",
            "SCORINFO": "zandronum-lumps/concepts/scorinfo.md",
            "SECTINFO": "zandronum-lumps/concepts/sectinfo.md",
            "SKININFO": "zandronum-lumps/concepts/skininfo.md",
            "TEAMINFO": "zandronum-lumps/concepts/teaminfo.md",
            "VOTEINFO": "zandronum-lumps/concepts/voteinfo.md",
        },
    },
    "menudef": {
        "index": "menudef/INDEX.md",
        "agents": "menudef/AGENTS.md",
        "dirs": {
            "menudef/inventory": TABLE_INVENTORY,
            "menudef/notes": TABLE_NOTES,
            "menudef/concepts": CONCEPT,
        },
        "lumps": {"MENUDEF": "menudef/concepts/item-dispatch-model.md"},
    },
    "netcode": {
        "index": "netcode/INDEX.md",
        "agents": "netcode/AGENTS.md",
        "dirs": {
            "netcode/concepts": CONCEPT,
        },
    },
    "keyconf": {
        "index": "keyconf/INDEX.md",
        "agents": "keyconf/AGENTS.md",
        "dirs": {
            "keyconf/concepts": CONCEPT,
        },
        "lumps": {"KEYCONF": "keyconf/concepts/keyconf-lump.md"},
    },
    "lockdefs": {
        "index": "lockdefs/INDEX.md",
        "agents": "lockdefs/AGENTS.md",
        "dirs": {
            "lockdefs/concepts": CONCEPT,
        },
        "lumps": {"LOCKDEFS": "lockdefs/concepts/lockdefs-lump.md"},
    },
    "gameinfo-lump": {
        "index": "gameinfo-lump/INDEX.md",
        "agents": "gameinfo-lump/AGENTS.md",
        "dirs": {
            "gameinfo-lump/concepts": CONCEPT,
        },
        "lumps": {"GAMEINFO": "gameinfo-lump/concepts/gameinfo-lump.md"},
    },
    "sndinfo": {
        "index": "sndinfo/INDEX.md",
        "agents": "sndinfo/AGENTS.md",
        "dirs": {
            "sndinfo/concepts": CONCEPT,
        },
        "lumps": {"SNDINFO": "sndinfo/concepts/sndinfo-lump.md"},
    },
    "textures": {
        "index": "textures/INDEX.md",
        "agents": "textures/AGENTS.md",
        "dirs": {
            "textures/concepts": CONCEPT,
        },
        "lumps": {"TEXTURES": "textures/concepts/textures-lump.md"},
    },
    "language": {
        "index": "language/INDEX.md",
        "agents": "language/AGENTS.md",
        "dirs": {
            "language/concepts": CONCEPT,
        },
    },
    "terrain": {
        "index": "terrain/INDEX.md",
        "agents": "terrain/AGENTS.md",
        "dirs": {
            "terrain/concepts": CONCEPT,
        },
        "lumps": {"TERRAIN": "terrain/concepts/terrain-lump.md"},
    },
    "decaldef": {
        "index": "decaldef/INDEX.md",
        "agents": "decaldef/AGENTS.md",
        "dirs": {
            "decaldef/concepts": CONCEPT,
        },
        "lumps": {"DECALDEF": "decaldef/concepts/decaldef-lump.md"},
    },
    "animdefs": {
        "index": "animdefs/INDEX.md",
        "agents": "animdefs/AGENTS.md",
        "dirs": {
            "animdefs/concepts": CONCEPT,
        },
        "lumps": {"ANIMDEFS": "animdefs/concepts/animdefs-lump.md"},
    },
    "fonts": {
        "index": "fonts/INDEX.md",
        "agents": "fonts/AGENTS.md",
        "dirs": {
            "fonts/concepts": CONCEPT,
        },
        "lumps": {
            "FONTDEFS": "fonts/concepts/fontdefs-lump.md",
            "TEXTCOLO": "fonts/concepts/textcolo-lump.md",
        },
    },
}

# Cross-section concepts live here, outside any one section's own directory.
SHARED_CONCEPTS_DIR = "shared/concepts"


def doc_dirs():
    """Yield (relative_dir_str, archetype) for every configured doc directory across every
    section, plus the shared cross-section concepts directory, regardless of whether it
    currently exists on disk."""
    for section in SECTIONS.values():
        yield from section["dirs"].items()
    yield (SHARED_CONCEPTS_DIR, CONCEPT)


def existing_doc_dirs():
    """Like doc_dirs(), but only directories that currently exist."""
    for rel, archetype in doc_dirs():
        if (ROOT / rel).is_dir():
            yield rel, archetype


def all_md_files():
    """Yield (Path, archetype, section_key_or_None) for every .md file in every configured,
    existing doc directory."""
    dir_to_section = {}
    for key, section in SECTIONS.items():
        for rel in section["dirs"]:
            dir_to_section[rel] = key
    for rel, archetype in existing_doc_dirs():
        section_key = dir_to_section.get(rel)  # None for shared/concepts
        for path in sorted((ROOT / rel).glob("*.md")):
            yield path, archetype, section_key
