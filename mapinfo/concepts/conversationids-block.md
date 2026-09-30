# ConversationIDs block

**Tier:** A
**Applies to:** UZDoom=yes, Zandronum=no
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-28)
**Provenance:** ZDoom Wiki `MAPINFO/Conversation number definition` (retrieved 2026-09-28, https://zdoom.org/w/index.php?title=MAPINFO/Conversation_number_definition&oldid=44294) + verified against UZDoom source (`src/gamedata/g_mapinfo.cpp:2627-2635`, `src/gamedata/g_doomedmap.cpp:413-415,418-451`, `src/gamedata/info.cpp:511-550`) and Zandronum source (`src/g_mapinfo.cpp:1961-1999`, `src/thingdef/thingdef_properties.cpp:417-440`, `src/p_conversation.cpp:143-165`).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.

A conversation ID definition block in MAPINFO maps conversation numbers to actor classes for Strife conversation systems. This mechanism allows modders to override or extend which actors respond to which conversation IDs, independently of DECORATE actor property declarations.

## Syntax

```mapinfo
ConversationIDs
{
  <number> = <class>
  <number> = None
}
```

The block begins with the `ConversationIDs` keyword, followed by a list of ID-to-actor mappings enclosed in braces. Each line assigns a numeric conversation ID to an actor class name, or to `None` to remove a previously-assigned ID.

## Parsing notes

- The `ConversationIDs` block is new-format-only (new MAPINFO syntax with braces). In old-format (Hexen-style) MAPINFO, the keyword causes a fatal error: "conversationids definitions not supported with old MAPINFO syntax."
- Encountering `ConversationIDs` when the lump's format is undetermined promotes it to new format, the same as other new-format-only blocks.
- A negative ID prints a script message ("must be positive"); `0` passes silently. Neither is fatal: the parser's "N errors encountered" check sits after a loop that only exits by returning on `}`, so it never runs, and the entry is inserted anyway. (The `1–65535` range applies to the DECORATE `ConversationID` property, not to this block.)
- Duplicate ID definitions within the same block produce a script message warning but do not cause a fatal error; the last assignment for a given ID wins.
- Assigning `None` (case-insensitive) removes a conversation ID from the active lookup table (used for disabling built-in IDs like the Strife weapon smith or medic).
- Class-name validation (actor existence check) happens at MAPINFO load time during the `InitSpawnablesFromMapinfo()` call, not during parse. An unknown class name causes a fatal startup error with a detailed script-origin citation.
- The parser is shared with the `spawnnums` block (which maps spawn numbers to actors) but otherwise independent.

## Examples

Assigning conversation IDs to custom actors:

```mapinfo
ConversationIDs
{
  2851 = ByStander
  1205 = ShopKeeper
  3677 = ShopKeeper
}
```

Disabling built-in Strife conversation IDs:

```mapinfo
ConversationIDs
{
  2 = None
  5 = None
}
```

Remapping an ID from one actor to another:

```mapinfo
ConversationIDs
{
  4 = WeaponSmith
}
```

## Resolution order: actor property vs. MAPINFO entry

When both a DECORATE actor's `ConversationID` property and a MAPINFO `conversationids` entry exist for the same ID, **the actor property wins**. The engine init sequence is:

1. MAPINFO is parsed; `conversationids` entries are collected in a temporary map.
2. `InitSpawnablesFromMapinfo()` is called (line 3725 of UZDoom's `src/d_main.cpp`), which clears the runtime `StrifeTypes` table and populates it with all MAPINFO `conversationids` entries.
3. `PClassActor::StaticSetActorNums()` is called immediately after (line 3726), iterating every actor class and calling `RegisterIDs()` on each. This unconditionally writes each actor's own `ConversationID` property into `StrifeTypes`, overwriting any MAPINFO entry for that ID.

Consequence: an actor's declared `ConversationID` cannot be suppressed by a MAPINFO `N = None` entry, since the actor property is applied *after* the MAPINFO table. `None` only clears IDs that came from MAPINFO. That includes UZDoom's own Strife IDs, which are themselves `ConversationIDs` blocks in the engine's bundled MAPINFO (`wadsrc/static/mapinfo/conversationids.txt`, e.g. `2 = WeaponSmith`), which is why the wiki's `2 = None` example works.

The `dumpconversationids` console command (UZDoom only) prints the final resolved mapping.

## Engine-family divergence

### ConversationIDs block: UZDoom-only

The MAPINFO `ConversationIDs` block does not exist in Zandronum. Encountering it in a MAPINFO or ZMAPINFO lump causes a fatal script error: "conversationids: Unknown top level keyword" (Zandronum source `src/g_mapinfo.cpp:1999`). Moving the block into ZMAPINFO does not hide it from Zandronum, as both lump types use identical parsing.

### DECORATE ConversationID property: Both engines, with differences

Both UZDoom and Zandronum accept a `ConversationID` property in DECORATE actor declarations, but their implementations diverge:

**Zandronum** (src/thingdef/thingdef_properties.cpp:417-440):
- Accepts three integer arguments: a primary ID and two teaser/alternate IDs (`conversationid <primary>, <teaser_id1>, <teaser_id2>`).
- Selects between them based on gameinfo flags: `GI_SHAREWARE` vs. `GI_TEASER2`.
- Registers the chosen ID via `SetStrifeType()`, which unconditionally writes to the runtime `StrifeTypes` table.

**UZDoom** (src/scripting/thingdef_properties.cpp:529-537):
- Accepts the same three-argument signature for source compatibility with Zandronum DECORATE, but ignores the teaser IDs (`id1` and `id2`).
- Uses only the primary argument and enforces a range check: `1–65535`.
- Stores the ID in the actor's `ActorInfo()->ConversationID` field, which is registered at engine startup.

```decorate
ConversationID 2851
ConversationID 1205, 1206, 1207
```

A modder targeting both engines must use the primary ID form shown above; the teaser IDs have no effect in UZDoom.

## Wiki/engine divergence

**No divergence found.** The wiki's description of syntax, behavior, and the override rules matches the UZDoom implementation. Its `2 = None`/`5 = None` example works because the built-in Strife IDs come from MAPINFO; it would not clear an ID a DECORATE actor declares itself (see "Resolution order" above).
