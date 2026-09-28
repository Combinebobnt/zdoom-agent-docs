# Bot commands

**Generated:** by `python3 tools/gen_inventory.py bots-commands` from the Zandronum source's `src/botcommands.cpp` (`g_BotCommands[NUM_BOTCMDS]`, a single named table -- the bot command set lives nowhere else, unlike cvars/ccmds which are declared tree-wide). No `Zan`/`UZD` columns: this section is Zandronum-only, with no UZDoom counterpart at all -- see `../AGENTS.md`. `Args`/`StringArgs` are `lNumArgs`/`lNumStringArgs` (the int-stack and string-stack argument counts `BOTCMD_RunCommand` enforces before dispatching); `Returns` is the row's `ReturnType` with its `RETURNVAL_` prefix stripped. Do not hand-edit rows; add a `../notes/<name>.md` file instead -- its `Tier`/`Notes` cell is picked up automatically on the next regen. A handler's actual behavior beyond arity/return type -- argument semantics, failure behavior -- requires reading `botcmd_<Name>` in `botcommands.cpp` directly until a `notes/` file exists for it. **Tier:** per row (defaults to C until a `notes/` file promotes it).

| Command | Args | StringArgs | Returns | Tier | Notes |
|---|---|---|---|---|---|
| ACS_Execute | 5 | 0 | VOID | B | [notes](../notes/acs_execute.md) |
| ACS_ExecuteWithResult | 5 | 0 | INT | B | [notes](../notes/acs_executewithresult.md) |
| ACS_NamedExecuteWithResult | 4 | 1 | INT | B | [notes](../notes/acs_namedexecutewithresult.md) |
| BeginAimingAtEnemy | 0 | 0 | VOID | C |  |
| BeginAltFiringWeapon | 0 | 0 | VOID | C |  |
| BeginChatting | 0 | 0 | VOID | C |  |
| BeginCrouching | 0 | 0 | VOID | C |  |
| BeginFiringWeapon | 0 | 0 | VOID | C |  |
| BeginJumping | 0 | 0 | VOID | C |  |
| BeginMoveDown | 0 | 0 | VOID | C |  |
| BeginMoveUp | 0 | 0 | VOID | C |  |
| BeginReloading | 0 | 0 | VOID | C |  |
| BeginSpeed | 0 | 0 | VOID | C |  |
| BeginUser | 1 | 0 | VOID | C |  |
| BeginZooming | 0 | 0 | VOID | C |  |
| changestate | 1 | 0 | VOID | C |  |
| ChangeWeapon | 0 | 1 | VOID | C |  |
| ChatSectionExists | 0 | 1 | BOOLEAN | C |  |
| ChatSectionExistsInChatLump | 0 | 1 | BOOLEAN | C |  |
| ChatSectionExistsInFile | 0 | 2 | BOOLEAN | C |  |
| ChatSectionExistsInLump | 0 | 2 | BOOLEAN | C |  |
| CheckTerrain | 2 | 0 | INT | C |  |
| ClearEnemy | 0 | 0 | VOID | C |  |
| delay | 1 | 0 | VOID | C |  |
| FireWeapon | 0 | 0 | VOID | C |  |
| GetAccuracy | 0 | 0 | INT | C |  |
| GetAnticipation | 0 | 0 | INT | C |  |
| GetArmor | 0 | 0 | INT | C |  |
| GetBaseArmor | 0 | 0 | INT | C |  |
| GetBaseHealth | 0 | 0 | INT | C |  |
| GetBotskill | 0 | 0 | INT | C |  |
| GetChatFrequency | 0 | 0 | INT | C |  |
| GetClosestPlayerEnemy | 0 | 0 | INT | C |  |
| GetCurrentAngle | 0 | 0 | INT | C |  |
| GetCurrentWeapon | 0 | 0 | STRING | C |  |
| GetDistanceToEnemy | 0 | 0 | INT | C |  |
| GetDistanceToItem | 1 | 0 | INT | C |  |
| GetEnemyInvulnerabilityTicks | 0 | 0 | INT | C |  |
| GetEvade | 0 | 0 | INT | C |  |
| GetFavoriteWeapon | 0 | 0 | STRING | C |  |
| GetGameMode | 0 | 0 | INT | C |  |
| GetHealth | 0 | 0 | INT | C |  |
| GetIntellect | 0 | 0 | INT | C |  |
| GetItemName | 1 | 0 | STRING | B | [notes](../notes/getitemname.md) |
| GetLastChatPlayer | 0 | 0 | STRING | C |  |
| GetLastChatString | 0 | 0 | STRING | C |  |
| GetLastJoinedPlayer | 0 | 0 | STRING | C |  |
| GetPathingCostToItem | 1 | 0 | INT | C |  |
| GetPerception | 0 | 0 | INT | C |  |
| GetPlayerDamagedBy | 0 | 0 | INT | C |  |
| GetPlayerName | 1 | 0 | STRING | C |  |
| GetReactionTime | 0 | 0 | INT | C |  |
| GetReceivedMedal | 0 | 0 | INT | C |  |
| GetSpread | 0 | 0 | INT | C |  |
| GetWeaponFromItem | 1 | 0 | STRING | C |  |
| IsDead | 0 | 0 | BOOLEAN | C |  |
| IsEnemyAlive | 0 | 0 | BOOLEAN | C |  |
| IsEnemyVisible | 0 | 0 | BOOLEAN | C |  |
| IsFavoriteWeapon | 0 | 1 | BOOLEAN | C |  |
| IsItemVisible | 1 | 0 | BOOLEAN | C |  |
| IsSkillDecreased | 0 | 0 | BOOLEAN | C |  |
| IsSkillIncreased | 0 | 0 | BOOLEAN | C |  |
| IsSpectating | 0 | 0 | BOOLEAN | C |  |
| IsWeaponOwned | 1 | 0 | BOOLEAN | C |  |
| Jump | 0 | 0 | VOID | C |  |
| LookForAmmo | 2 | 0 | INT | C |  |
| LookForBaseArmor | 2 | 0 | INT | C |  |
| LookForBaseHealth | 2 | 0 | INT | C |  |
| LookForPlayerEnemies | 1 | 0 | INT | C |  |
| LookForPowerups | 2 | 0 | INT | C |  |
| LookForSuperArmor | 2 | 0 | INT | B | [notes](../notes/lookforsuperarmor.md) |
| LookForSuperHealth | 2 | 0 | INT | C |  |
| LookForWeapons | 2 | 0 | INT | C |  |
| MoveBackwards | 1 | 0 | VOID | C |  |
| MoveForward | 1 | 0 | VOID | C |  |
| MoveLeft | 1 | 0 | VOID | C |  |
| MoveRight | 1 | 0 | VOID | C |  |
| PathToGoal | 1 | 0 | INT | B | [notes](../notes/pathtogoal.md) |
| PathToLastHeardSound | 1 | 0 | INT | B | [notes](../notes/pathtolastheardsound.md) |
| PathToLastKnownEnemyPosition | 1 | 0 | INT | B | [notes](../notes/pathtolastknownenemyposition.md) |
| PressUse | 0 | 0 | VOID | C |  |
| QuitJoinQueue | 0 | 0 | VOID | C |  |
| Random | 2 | 0 | INT | C |  |
| Respawn | 0 | 0 | VOID | C |  |
| Roam | 1 | 0 | INT | B | [notes](../notes/roam.md) |
| Say | 0 | 1 | VOID | C |  |
| SayFromChatFile | 0 | 1 | VOID | C |  |
| SayFromChatLump | 0 | 1 | VOID | C |  |
| SayFromFile | 0 | 2 | VOID | C |  |
| SayFromLump | 0 | 2 | VOID | C |  |
| SetEnemy | 1 | 0 | VOID | B | [notes](../notes/setenemy.md) |
| SetGoal | 1 | 0 | VOID | C |  |
| SetGoalTID | 1 | 0 | VOID | C |  |
| SetSkillDecrease | 1 | 0 | VOID | C |  |
| SetSkillIncrease | 1 | 0 | VOID | C |  |
| StopAimingAtEnemy | 0 | 0 | VOID | C |  |
| StopAltFiringWeapon | 0 | 0 | VOID | C |  |
| StopChatting | 0 | 0 | VOID | C |  |
| StopCrouching | 0 | 0 | VOID | C |  |
| StopFiringWeapon | 0 | 0 | VOID | C |  |
| StopForwardMovement | 0 | 0 | VOID | C |  |
| StopJumping | 0 | 0 | VOID | C |  |
| StopMoveDown | 0 | 0 | VOID | C |  |
| StopMovement | 0 | 0 | VOID | C |  |
| StopMoveUp | 0 | 0 | VOID | C |  |
| StopReloading | 0 | 0 | VOID | C |  |
| StopSidewaysMovement | 0 | 0 | VOID | C |  |
| StopSpeed | 0 | 0 | VOID | C |  |
| StopUser | 1 | 0 | VOID | C |  |
| StopZooming | 0 | 0 | VOID | C |  |
| StringsAreEqual | 0 | 2 | BOOLEAN | B | [notes](../notes/stringsareequal.md) |
| Taunt | 0 | 0 | VOID | C |  |
| TryToJoinGame | 0 | 0 | VOID | C |  |
| Turn | 1 | 0 | VOID | C |  |
