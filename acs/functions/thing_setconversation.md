# `bool Thing_SetConversation(int tid, int dlg_id)`

**Tier:** A.
**Applies to:** UZDoom=yes, Zandronum=yes — the Zandronum-side stamp below is a `master` HEAD checkout ahead of the 3.2.1 target (the 3.2.1-vs-3.3-alpha gap); see "Engine scope" in `../../shared/AUTHORING.md`.
**Verified against:** UZDoom 5.0.0-pre @5a9b0ec511 (2026-08-15); Zandronum 3.2.1 @28f736fb3 (2026-08-17)
**Provenance:** originally written with no wiki intake — not previously documented anywhere in
this tree (confirmed no `INDEX.md` entry, tier C or otherwise, before this doc). A
`Thing_SetConversation - ZDoom Wiki.html` intake page
(`https://zdoom.org/w/index.php?title=Thing_SetConversation&oldid=27544`) was processed
afterward; it only covers the bare `tid`/`convid` signature (both already captured above) and
adds no facts beyond what was already source-verified, so no content changed as a result.
Entirely source-verified against the Zandronum source (`p_lnspec.cpp:3544-3572` for the special
itself, `p_conversation.cpp:172-177` for `GetConversation`, `p_usdf.cpp:390,397` for the USDF
numeric-ID registration gap, `p_lnspec.cpp:3534` for the `StartConversation` client-mode gate).
**Wiki license:** Derived from the ZDoom Wiki; this file as a whole is GNU Free Documentation License 1.2 — see [LICENSE](../../LICENSE) §2.
**Bucket:** action special (index 79, `zcommon.bcs`'s `special` table). Not a BCS/zt-bcc
extension — a base ACS line special, callable from any ACS script.

Attaches or clears a Strife/USDF dialogue tree on an actor, so a later `Thing_Activate` (action
special 130) or USE-key interaction opens that conversation via `StartConversation()`.

- `tid` — actor(s) to set/clear the conversation on. `0` targets the activator. If `tid != 0` and
  no actor currently carries that TID, the iterator loop simply runs zero times — **this is not
  treated as failure** (see return value below).
- `dlg_id` — numeric conversation ID.
  - `0` **explicitly clears** the conversation: sets both `actor->ConversationRoot = -1` and
    `actor->Conversation = NULL` (Zandronum `p_lnspec.cpp:3544-3572`). This is documented,
    intentional behavior, not a fallback/no-op side effect.
  - Nonzero — looked up via `GetConversation(dlg_id)` against the `DialogueRoots` map (Zandronum
    `p_conversation.cpp:172-177`). A failed lookup (ID not registered) returns `false` immediately
    and touches no actor.
  - On success, sets `actor->ConversationRoot` (index into `StrifeDialogues`) and
    `actor->Conversation` (pointer to `FStrifeDialogueNode`) on every matching actor.

**Return value semantics differ from `Thing_Activate`'s "did anything happen" convention:**
`Thing_SetConversation` returns `true` for (a) a successful clear (`dlg_id=0`), (b) a successful
set on ≥1 matching actor, and (c) `tid != 0` matching **zero** actors — the only case it returns
`false` is when `dlg_id != 0` and the ID lookup itself fails. Don't read a `true` return as proof
any actor was actually touched.

**SCRIPT vs. USDF conversations — the one non-obvious gotcha:** works with both, but a USDF
conversation is only reachable by numeric ID (and thus by this function) if its declaration
includes an explicit `Actor` field (Strife namespace) or `Id` field (ZDoom namespace) (Zandronum
`p_usdf.cpp:390,397`). A USDF conversation declared with only a class name (e.g.
`conversation MyNPC { actor Footknight; ... }` without an explicit id) is registered only in
`ClassRoots` (class-name lookup), never in the `DialogueRoots` int map that
`GetConversation(int)` reads — so it is **unreachable from `Thing_SetConversation`** regardless
of `dlg_id` value. Strife-format (SCRIPT) conversations always get a numeric ID and don't have
this limitation.

**UZDoom comparison** (confirmed against `LS_Thing_SetConversation`,
`src/playsim/p_lnspec.cpp:3384-3412`; `FLevelLocals::GetConversation`,
`src/p_conversation.cpp:96-101`; `ParseConversation`'s `Actor`/`Id` handling,
`src/maploader/usdf.cpp:431,439,473`): every mechanic documented above — the `dlg_id=0`
explicit-clear path, the `DialogueRoots` lookup and its failure return, the per-matching-actor
`ConversationRoot`/`Conversation` assignment, the "loop runs zero times but the call still
succeeds" return-value quirk, and the USDF numeric-ID registration gap — holds identically on
UZDoom. The one structural (not behavioral) difference is that UZDoom's conversation state
(`DialogueRoots`, `ClassRoots`, `StrifeDialogues`, `GetConversation`) lives on `FLevelLocals`
(per-level, supporting UZDoom's multi-level-in-flight architecture) rather than as Zandronum's
single set of file-scope globals — invisible from ACS, since `Thing_SetConversation` only ever
operates on the current level either way. UZDoom's USDF parser additionally accepts `Id` under a
`Gz` (GZDoom) namespace bit alongside `Zd` (Zandronum's parser only recognizes `Zd`), a namespace
addition that doesn't change the documented reachability rule.

## Zandronum-specific: no client-replication for conversation state

Unlike `Thing_Activate` (which broadcasts `SERVERCOMMANDS_ThingActivate` to sync clients), this
special has no client-replication code at all — Zandronum `p_lnspec.cpp:3544-3572` has no
`SERVERCOMMANDS_*` call. In practice this doesn't desync gameplay because `StartConversation()`
itself gates on `!NETWORK_InClientMode()` (Zandronum `p_lnspec.cpp:3534`, comment-tagged `[SB]` — a
Zandronum-side addition over base ZDoom) — only the server's copy of `actor->Conversation` is ever
consulted when a conversation actually opens. It would only matter if some other client-side code
tried to read an actor's conversation state directly.

This entire caveat is Zandronum-specific, not just differently-behaved: a full-tree search of the
UZDoom source turns up zero occurrences of `SERVERCOMMANDS_` (the entire replication-message
family Zandronum's client-server model relies on) and no `NETWORK_InClientMode()`-style gate
anywhere. UZDoom's own netcode (`src/d_net.cpp` — `ticcmd_t`, `TryRunTics`, `NetUpdate`) is built
around the classic Doom-lineage ticcmd-exchange model rather than Zandronum's dedicated
client-server split, which is consistent with that absence, but the netcode internals weren't
traced deeply enough this pass to characterize UZDoom's synchronization model beyond that. Either
way, there is no analogous "does this replicate to clients" question to ask about
`Thing_SetConversation` on UZDoom.

**Example:**

```text
script "Example" (void)
{
    Thing_SetConversation(100, 42); // attach conversation #42 to TID 100
    Thing_SetConversation(0, 0);    // clear activator's conversation
}
```
