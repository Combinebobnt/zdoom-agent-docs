# PathToLastHeardSound

**Tier:** B
**Applies to:** UZDoom=no, Zandronum=yes
**Verified against:** Zandronum 3.3-alpha @bdd0f7beb (2026-09-25)
**Provenance:** written from the Zandronum source's `src/botcommands.cpp` (`botcmd_PathToLastHeardSound`). No wiki page covers this command.
**Source excerpt:** This file quotes Zandronum engine source verbatim; reproduced under Zandronum's own license terms — see [LICENSE](../../LICENSE) §3.

## Engine-family divergence

`PathToLastHeardSound` is a bot command, not an ACS/BCS function — it lives in Zandronum's
bot-command dispatcher (`botcommands.cpp`), which UZDoom/GZDoom-family engines don't have at all.
There is no UZDoom counterpart to diverge from; see `../AGENTS.md`.

**Unimplemented stub — always returns `PATH_UNREACHABLE`, regardless of arguments or bot state.**

The name and its `1, 0, RETURNVAL_INT` row shape place it alongside `PathToGoal`,
`PathToLastKnownEnemyPosition`, and `Roam` — the same A*-pathing command family, all sharing the
`PATH_*` int-return convention. But `botcmd_PathToLastHeardSound`'s entire body is:

```cpp
static void botcmd_PathToLastHeardSound( CSkullBot *pBot )
{
	float	fSpeed;

	fSpeed = (float)pBot->m_ScriptData.alStack[pBot->m_ScriptData.lStackPosition - 1];
	pBot->PopStack( );

	if ( fSpeed < 0 )
		fSpeed = 0;
	if ( fSpeed > 100 )
		fSpeed = 100;

	g_iReturnInt = PATH_UNREACHABLE;
}
```

It pops its speed argument (still required by the table's `lNumArgs: 1`, so a caller must still
push one), clamps it into 0-100 exactly like its siblings, and then does nothing else: no A* call,
no movement, no sound-position lookup at all. Every call returns `PATH_UNREACHABLE` unconditionally.
A botscript relying on this command to path toward a heard sound will never move and will always
see the "unreachable" result — there is no known workaround inside the bot command surface itself.

## Related

- `PathToGoal`, `PathToLastKnownEnemyPosition`, `Roam` — the three sibling pathing commands that
  actually dispatch to the A* pathfinder (`src/astar.cpp`).
- `GetChatFrequency`, `LookForPlayerEnemies` — other bot senses that, unlike this one, are fully
  implemented.
