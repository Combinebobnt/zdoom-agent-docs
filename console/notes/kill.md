# `kill`

**Tier:** B
**Applies to:** UZDoom=yes, Zandronum=yes
**Verified against:** UZDoom 5.1.0-pre @98b16b78fc (2026-09-23); Zandronum 3.3-alpha @bdd0f7beb (2026-09-24)
**Provenance:** Zandronum `docs/commands.txt` (`kill [monsters]` entry), verified against both engines' source (the `kill` CCMD in Zandronum `src/p_interaction.cpp`, `P_Massacre`/`KillAll`/`AActor::Massacre`; UZDoom `FLevelLocals::Massacre`), and observed live on Zandronum.

`kill` with no argument kills the calling player. `kill monsters` kills every monster on the level,
and `kill <classname>` kills every actor of that class (and its replacement). UZDoom also accepts
`kill baddies`, which spares `MF_FRIENDLY` monsters.

## Dormant actors are skipped

**`kill monsters` and `kill <class>` never touch an actor with the `DORMANT` flag.** The selection
loop filters them out before any damage is applied:

- Zandronum: `P_Massacre` (`src/p_enemy.cpp:3821`) for `kill monsters`, and `KillAll`
  (`src/d_net.cpp:2047`) for `kill <class>`. Both test `!(flags2 & MF2_DORMANT) && (flags3 &
  MF3_ISMONSTER)`.
- UZDoom: both forms go through `FLevelLocals::Massacre` (`src/playsim/p_enemy.cpp:3421`), which
  has the same test plus the optional friendly filter.

This is easy to misread because `AActor::Massacre()` itself clears `MF2_DORMANT` and
`MF2_INVULNERABLE` before dealing `TELEFRAG_DAMAGE` (Zandronum `src/p_mobj.cpp:1518`, UZDoom
`src/playsim/p_mobj.cpp:1721`). That code path is simply never reached for a dormant actor.

Ordinary damage doesn't reach them either: `P_DamageMobj` returns early for a dormant target unless
the damage is `DMG_FORCED` (Zandronum `src/p_interaction.cpp:1261`, UZDoom
`src/playsim/p_interaction.cpp:1168`).

So a dormant actor spawned as a test fixture (for example a solid blocker placed with
`summon`/`Spawn` and then made dormant) survives `kill monsters` indefinitely, with no message.
Remove it by TID instead, for example with ACS `Thing_Remove(tid)`, or wake it first
(`Thing_Activate(tid)`) and then kill it. The ACS `Thing_Destroy(0, ...)` massacre path calls
the same `P_Massacre` and has the same gap.

## Netgames

Zandronum's `docs/commands.txt` calls the command "broken in netgames", but the current source
routes it through the server: a client's `kill` is forwarded as `CLIENTCOMMANDS_KillCheat`, and
`P_Massacre` returns 0 without doing anything on a client. `kill monsters` is gated by
`CheckCheatmode`. The dormant skip above applies on the server the same way.
