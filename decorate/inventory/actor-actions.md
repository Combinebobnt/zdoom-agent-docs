# DECORATE action functions

**Generated:** by `python3 tools/gen_inventory.py decorate-actions` from every `DEFINE_ACTION_FUNCTION`/`DEFINE_ACTION_FUNCTION_PARAMS` call tree-wide in the Zandronum source's `src/` (spread across ~85 files -- see `../CLAUDE.md`'s bucket table), cross-referenced against the UZDoom source's `src/` tree by name for the `UZD` column. `Takes args` records whether the action was declared with the `_PARAMS` macro variant (i.e. callable with DECORATE arguments) -- do not hand-edit rows; use `../actions/<name>.md` for a full writeup (archetype 1) once one earns its cost, same as `a_look.md` -- its `Tier`/`Notes` cell is picked up automatically on the next regen. **Engine:** Zandronum 3.2.1 confirmed present for every row; UZDoom presence per the `UZD` column only. **Tier:** per row.

| Action | Class | Takes args | Zan | UZD | Tier | Notes |
|---|---|---|---|---|---|---|
| A_AccTeleGlitter | AActor | no | yes | — | C |  |
| A_AcolyteBits | AActor | no | yes | — | C |  |
| A_AcolyteDie | AActor | no | yes | — | C |  |
| A_ActiveAndUnblock | AActor | no | yes | — | C |  |
| A_ActiveSound | AActor | no | yes | — | C |  |
| A_AddPlayerRain | AActor | no | yes | — | C |  |
| A_AlertMonsters | AActor | yes | yes | — | A | [notes](../actions/a_alertmonsters.md) |
| A_AlienSpectreDeath | AActor | no | yes | — | C |  |
| A_BabyMetal | AActor | no | yes | — | C |  |
| A_Bang4Cloud | AActor | no | yes | — | C |  |
| A_BarrelDestroy | AActor | no | yes | — | C |  |
| A_BasicAttack | AActor | yes | yes | — | C |  |
| A_BatMove | AActor | no | yes | — | C |  |
| A_BatSpawn | AActor | no | yes | — | C |  |
| A_BatSpawnInit | AActor | no | yes | — | C |  |
| A_Beacon | AActor | no | yes | — | C |  |
| A_BeakAttackPL1 | AActor | no | yes | — | C |  |
| A_BeakAttackPL2 | AActor | no | yes | — | C |  |
| A_BeakRaise | AActor | no | yes | — | C |  |
| A_BellReset1 | AActor | no | yes | — | C |  |
| A_BellReset2 | AActor | no | yes | — | C |  |
| A_BeShadowyFoe | AActor | no | yes | — | C |  |
| A_BetaSkullAttack | AActor | no | yes | — | C |  |
| A_BFGsound | AActor | no | yes | — | C |  |
| A_BFGSpray | AActor | yes | yes | — | C |  |
| A_BishopAttack | AActor | no | yes | — | C |  |
| A_BishopAttack2 | AActor | no | yes | — | C |  |
| A_BishopChase | AActor | no | yes | — | C |  |
| A_BishopDecide | AActor | no | yes | — | C |  |
| A_BishopDoBlur | AActor | no | yes | — | C |  |
| A_BishopMissileWeave | AActor | no | yes | — | C |  |
| A_BishopPainBlur | AActor | no | yes | — | C |  |
| A_BishopPuff | AActor | no | yes | — | C |  |
| A_BishopSpawnBlur | AActor | no | yes | — | C |  |
| A_BlueSpark | AActor | no | yes | — | C |  |
| A_BossDeath | AActor | no | yes | — | A | [notes](../actions/a_bossdeath.md) |
| A_BounceCheck | AActor | no | yes | — | C |  |
| A_BrainAwake | AActor | no | yes | — | C |  |
| A_BrainDie | AActor | no | yes | — | C |  |
| A_BrainExplode | AActor | no | yes | — | C |  |
| A_BrainPain | AActor | no | yes | — | C |  |
| A_BrainScream | AActor | no | yes | — | C |  |
| A_BrainSpit | AActor | yes | yes | — | C |  |
| A_BridgeInit | AActor | yes | yes | — | C |  |
| A_BridgeOrbit | AActor | no | yes | — | C |  |
| A_BruisAttack | AActor | no | yes | — | C |  |
| A_BspiAttack | AActor | no | yes | — | C |  |
| A_BulletAttack | AActor | no | yes | yes | C |  |
| A_BurnArea | AActor | no | yes | — | C |  |
| A_Burnination | AActor | no | yes | — | C |  |
| A_Burst | AActor | yes | yes | yes | C |  |
| A_CallSpecial | AActor | yes | yes | — | C |  |
| A_CentaurDefend | AActor | no | yes | — | C |  |
| A_CFlameAttack | AActor | no | yes | — | C |  |
| A_CFlameMissile | AActor | no | yes | — | C |  |
| A_CFlamePuff | AActor | no | yes | — | C |  |
| A_CFlameRotate | AActor | no | yes | — | C |  |
| A_ChangeFlag | AActor | yes | yes | yes | A | [notes](../actions/a_changeflag.md) |
| A_ChangeVelocity | AActor | yes | yes | — | A | [notes](../actions/a_changevelocity.md) |
| A_Chase | AActor | yes | yes | — | A | [notes](../actions/a_chase.md) |
| A_CheckCeiling | AActor | yes | yes | — | A | [notes](../actions/a_checkceiling.md) |
| A_CheckFlag | AActor | yes | yes | — | A | [notes](../actions/a_checkflag.md) |
| A_CheckFloor | AActor | yes | yes | — | A | [notes](../actions/a_checkfloor.md) |
| A_CheckForReload | AActor | yes | yes | — | C |  |
| A_CheckLOF | AActor | yes | yes | — | A | [notes](../actions/a_checklof.md) |
| A_CheckPlayerDone | AActor | no | yes | — | C |  |
| A_CheckRailReload | AActor | no | yes | — | C |  |
| A_CheckRange | AActor | yes | yes | — | A | [notes](../actions/a_checkrange.md) |
| A_CheckReload | AInventory | no | yes | — | A | [notes](../actions/a_checkreload.md) |
| A_CheckSight | AActor | yes | yes | — | A | [notes](../actions/a_checksight.md) |
| A_CheckSightOrRange | AActor | yes | yes | — | A | [notes](../actions/a_checksightorrange.md) |
| A_CheckTeleRing | AActor | no | yes | — | C |  |
| A_CheckTerrain | AActor | no | yes | yes | C |  |
| A_CheckThrowBomb | AActor | no | yes | — | C |  |
| A_CheckThrowBomb2 | AActor | no | yes | — | C |  |
| A_ChicAttack | AActor | no | yes | — | C |  |
| A_CHolyAttack | AActor | no | yes | — | C |  |
| A_CHolyAttack2 | AActor | no | yes | — | C |  |
| A_CHolyCheckScream | AActor | no | yes | — | C |  |
| A_CHolyPalette | AActor | no | yes | — | C |  |
| A_CHolySeek | AActor | no | yes | — | C |  |
| A_CHolyTail | AActor | no | yes | — | C |  |
| A_ClassBossHealth | AActor | no | yes | yes | C |  |
| A_ClearFlash | AActor | no | yes | — | C |  |
| A_ClearLastHeard | AActor | yes | yes | yes | C |  |
| A_ClearReFire | AInventory | no | yes | — | C |  |
| A_ClearShadow | AActor | no | yes | — | C |  |
| A_ClearSoundTarget | AActor | no | yes | — | C |  |
| A_ClearTarget | AActor | no | yes | — | A | [notes](../actions/a_cleartarget.md) |
| A_ClericAttack | AActor | no | yes | — | C |  |
| A_ClientsideACSExecute | AActor | yes | yes | — | C |  |
| A_CloseShotgun2 | AActor | no | yes | — | C |  |
| A_CMaceAttack | AActor | no | yes | — | C |  |
| A_ComboAttack | AActor | no | yes | — | C |  |
| A_CopyFriendliness | AActor | yes | yes | yes | C |  |
| A_CorpseBloodDrip | AActor | no | yes | — | C |  |
| A_CorpseExplode | AActor | no | yes | — | C |  |
| A_Countdown | AActor | no | yes | — | A | [notes](../actions/a_countdown.md) |
| A_CountdownArg | AActor | yes | yes | yes | A | [notes](../actions/a_countdownarg.md) |
| A_CPosAttack | AActor | no | yes | — | C |  |
| A_CPosRefire | AActor | no | yes | — | C |  |
| A_CrispyPlayer | AActor | no | yes | — | C |  |
| A_CrusaderChoose | AActor | no | yes | — | C |  |
| A_CrusaderDeath | AActor | no | yes | — | C |  |
| A_CrusaderRefire | AActor | no | yes | — | C |  |
| A_CrusaderSweepLeft | AActor | no | yes | — | C |  |
| A_CrusaderSweepRight | AActor | no | yes | — | C |  |
| A_CStaffAttack | AActor | no | yes | — | C |  |
| A_CStaffCheck | AActor | no | yes | — | C |  |
| A_CStaffCheckBlink | AActor | no | yes | — | C |  |
| A_CStaffInitBlink | AActor | no | yes | — | C |  |
| A_CStaffMissileSlither | AActor | no | yes | — | C |  |
| A_CustomBulletAttack | AActor | yes | yes | — | A | [notes](../actions/a_custombulletattack.md) |
| A_CustomComboAttack | AActor | yes | yes | yes | A | [notes](../actions/a_customcomboattack.md) |
| A_CustomMeleeAttack | AActor | yes | yes | yes | A | [notes](../actions/a_custommeleeattack.md) |
| A_CustomMissile | AActor | yes | yes | — | A | [notes](../actions/a_custommissile.md) |
| A_CustomPunch | AActor | yes | yes | — | A | [notes](../actions/a_custompunch.md) |
| A_CustomRailgun | AActor | yes | yes | yes | A | [notes](../actions/a_customrailgun.md) |
| A_CyberAttack | AActor | no | yes | — | C |  |
| A_DamageChildren | AActor | yes | yes | yes | A | [notes](../actions/a_damagechildren.md) |
| A_DamageMaster | AActor | yes | yes | yes | A | [notes](../actions/a_damagemaster.md) |
| A_DamageSiblings | AActor | yes | yes | yes | A | [notes](../actions/a_damagesiblings.md) |
| A_DeathBallImpact | AActor | no | yes | — | C |  |
| A_DelayGib | AActor | no | yes | — | C |  |
| A_DeQueueCorpse | AActor | no | yes | yes | A | [notes](../actions/a_dequeuecorpse.md) |
| A_Detonate | AActor | no | yes | — | C |  |
| A_Die | AActor | yes | yes | — | A | [notes](../actions/a_die.md) |
| A_DragonAttack | AActor | no | yes | — | C |  |
| A_DragonCheckCrash | AActor | no | yes | — | C |  |
| A_DragonFlap | AActor | no | yes | — | C |  |
| A_DragonFlight | AActor | no | yes | — | C |  |
| A_DragonFX2 | AActor | no | yes | — | C |  |
| A_DragonInitFlight | AActor | no | yes | — | C |  |
| A_DragonPain | AActor | no | yes | — | C |  |
| A_DripBlood | AActor | no | yes | — | C |  |
| A_DropFire | AActor | no | yes | — | C |  |
| A_DropInventory | AActor | yes | yes | yes | C |  |
| A_DropItem | AActor | yes | yes | — | C |  |
| A_DropWeaponPieces | AActor | yes | yes | — | C |  |
| A_DualPainAttack | AActor | yes | yes | — | C |  |
| A_EntityAttack | AActor | no | yes | — | C |  |
| A_EntityDeath | AActor | no | yes | — | C |  |
| A_Explode | AActor | yes | yes | — | A | [notes](../actions/a_explode.md) |
| A_Explode512 | AActor | no | yes | — | C |  |
| A_ExtChase | AActor | yes | yes | — | C |  |
| A_ExtraLightOff | AActor | no | yes | — | C |  |
| A_FaceMaster | AActor | yes | yes | — | A | [notes](../families/face-pointer.md) |
| A_FaceTarget | AActor | yes | yes | — | A | [notes](../families/face-pointer.md) |
| A_FaceTracer | AActor | yes | yes | — | A | [notes](../families/face-pointer.md) |
| A_FadeIn | AActor | yes | yes | yes | A | [notes](../actions/a_fadein.md) |
| A_FadeOut | AActor | yes | yes | yes | A | [notes](../actions/a_fadeout.md) |
| A_FadeTo | AActor | yes | yes | yes | A | [notes](../actions/a_fadeto.md) |
| A_Fall | AActor | no | yes | — | A | [notes](../actions/a_noblocking.md) |
| A_FastChase | AActor | no | yes | — | C |  |
| A_FatAttack1 | AActor | yes | yes | — | C |  |
| A_FatAttack2 | AActor | yes | yes | — | C |  |
| A_FatAttack3 | AActor | yes | yes | — | C |  |
| A_FatRaise | AActor | no | yes | — | C |  |
| A_FAxeAttack | AActor | no | yes | — | C |  |
| A_FAxeCheckAtk | AActor | no | yes | — | C |  |
| A_FAxeCheckReady | AActor | no | yes | — | C |  |
| A_FAxeCheckReadyG | AActor | no | yes | — | C |  |
| A_FAxeCheckUp | AActor | no | yes | — | C |  |
| A_FAxeCheckUpG | AActor | no | yes | — | C |  |
| A_Feathers | AActor | no | yes | — | C |  |
| A_FHammerAttack | AActor | no | yes | — | C |  |
| A_FHammerThrow | AActor | no | yes | — | C |  |
| A_FighterAttack | AActor | no | yes | — | C |  |
| A_Fire | AActor | yes | yes | — | A | [notes](../actions/a_fire.md) |
| A_FireArrow | AActor | yes | yes | — | C |  |
| A_FireAssaultGun | AActor | no | yes | — | C |  |
| A_FireBFG | AActor | no | yes | — | C |  |
| A_FireBlasterPL1 | AActor | no | yes | — | C |  |
| A_FireBullets | AActor | yes | yes | — | A | [notes](../actions/a_firebullets.md) |
| A_FireCGun | AActor | no | yes | — | C |  |
| A_FireConePL1 | AActor | no | yes | — | C |  |
| A_FireCrackle | AActor | no | yes | — | C |  |
| A_FireCrossbowPL1 | AActor | no | yes | — | C |  |
| A_FireCrossbowPL2 | AActor | no | yes | — | C |  |
| A_FireCustomMissile | AActor | yes | yes | — | A | [notes](../actions/a_firecustommissile.md) |
| A_FiredAttack | AActor | no | yes | — | C |  |
| A_FiredChase | AActor | no | yes | — | C |  |
| A_FiredRocks | AActor | no | yes | — | C |  |
| A_FiredSplotch | AActor | no | yes | — | C |  |
| A_FireFlamer | AActor | no | yes | — | C |  |
| A_FireGoldWandPL1 | AActor | no | yes | — | C |  |
| A_FireGoldWandPL2 | AActor | no | yes | — | C |  |
| A_FireGrenade | AActor | yes | yes | — | C |  |
| A_FireMacePL1 | AActor | no | yes | — | C |  |
| A_FireMacePL2 | AActor | no | yes | — | C |  |
| A_FireMauler1 | AActor | no | yes | — | C |  |
| A_FireMauler2 | AActor | no | yes | — | C |  |
| A_FireMauler2Pre | AActor | no | yes | — | C |  |
| A_FireMiniMissile | AActor | no | yes | — | C |  |
| A_FireMissile | AActor | no | yes | — | C |  |
| A_FireOldBFG | AActor | no | yes | — | C |  |
| A_FirePhoenixPL1 | AActor | no | yes | — | C |  |
| A_FirePhoenixPL2 | AActor | no | yes | — | C |  |
| A_FirePistol | AActor | no | yes | — | C |  |
| A_FirePlasma | AActor | no | yes | — | C |  |
| A_FireRailgun | AActor | yes | yes | — | C |  |
| A_FireRailgunLeft | AActor | no | yes | — | C |  |
| A_FireRailgunRight | AActor | no | yes | — | C |  |
| A_FireShotgun | AActor | no | yes | — | C |  |
| A_FireShotgun2 | AActor | no | yes | — | C |  |
| A_FireSigil1 | AActor | no | yes | — | C |  |
| A_FireSigil2 | AActor | no | yes | — | C |  |
| A_FireSigil3 | AActor | no | yes | — | C |  |
| A_FireSigil4 | AActor | no | yes | — | C |  |
| A_FireSigil5 | AActor | no | yes | — | C |  |
| A_FireSkullRodPL1 | AActor | no | yes | — | C |  |
| A_FireSkullRodPL2 | AActor | no | yes | — | C |  |
| A_FireSTGrenade | AActor | yes | yes | — | C |  |
| A_FlameDie | AActor | no | yes | — | C |  |
| A_FlameEnd | AActor | no | yes | — | C |  |
| A_FloatGib | AActor | no | yes | — | C |  |
| A_FloatPuff | AActor | no | yes | — | C |  |
| A_FLoopActiveSound | AActor | no | yes | — | C |  |
| A_FogMove | AActor | no | yes | — | C |  |
| A_FogSpawn | AActor | no | yes | — | C |  |
| A_FPunchAttack | AActor | no | yes | — | C |  |
| A_FreezeDeath | AActor | no | yes | — | C |  |
| A_FreezeDeathChunks | AActor | no | yes | — | C |  |
| A_FSwordAttack | AActor | no | yes | — | C |  |
| A_FSwordFlames | AActor | no | yes | — | C |  |
| A_GauntletAttack | AActor | yes | yes | — | C |  |
| A_GenericFreezeDeath | AActor | no | yes | — | C |  |
| A_GenWizard | AActor | no | yes | — | C |  |
| A_GetHurt | AActor | no | yes | — | C |  |
| A_GhostOff | AActor | no | yes | — | C |  |
| A_GiveInventory | AActor | yes | yes | — | A | [notes](../actions/a_giveinventory.md) |
| A_GivePlayerMedal | AActor | yes | yes | — | C |  |
| A_GiveQuestItem | AActor | yes | yes | — | C |  |
| A_GiveToChildren | AActor | yes | yes | — | C |  |
| A_GiveToSiblings | AActor | yes | yes | — | C |  |
| A_GiveToTarget | AActor | yes | yes | — | A | [notes](../actions/a_givetotarget.md) |
| A_Gravity | AActor | no | yes | — | C |  |
| A_GunFlash | AInventory | yes | yes | — | A | [notes](../actions/a_gunflash.md) |
| A_HandLower | AActor | no | yes | — | C |  |
| A_HeadAttack | AActor | no | yes | — | C |  |
| A_HideDecepticon | AActor | no | yes | — | C |  |
| A_HideInCeiling | AActor | no | yes | — | C |  |
| A_HideThing | AActor | no | yes | — | C |  |
| A_Hoof | AActor | no | yes | — | C |  |
| A_IceGuyAttack | AActor | no | yes | — | C |  |
| A_IceGuyChase | AActor | no | yes | — | C |  |
| A_IceGuyDie | AActor | no | yes | — | C |  |
| A_IceGuyLook | AActor | no | yes | — | C |  |
| A_IceGuyMissileExplode | AActor | no | yes | — | C |  |
| A_IceSetTics | AActor | no | yes | — | C |  |
| A_ImpDeath | AActor | no | yes | — | C |  |
| A_ImpExplode | AActor | no | yes | — | C |  |
| A_ImpMsAttack | AActor | no | yes | — | C |  |
| A_ImpXDeath1 | AActor | no | yes | — | C |  |
| A_InitPhoenixPL2 | AActor | no | yes | — | C |  |
| A_InquisitorAttack | AActor | no | yes | — | C |  |
| A_InquisitorCheckLand | AActor | no | yes | — | C |  |
| A_InquisitorDecide | AActor | no | yes | — | C |  |
| A_InquisitorJump | AActor | no | yes | — | C |  |
| A_InquisitorWalk | AActor | no | yes | — | C |  |
| A_ItBurnsItBurns | AActor | no | yes | — | C |  |
| A_JabDagger | AActor | no | yes | — | C |  |
| A_Jump | AActor | yes | yes | yes | A | [notes](../actions/a_jump.md) |
| A_JumpIf | AActor | yes | yes | — | A | [notes](../actions/a_jumpif.md) |
| A_JumpIfArmorType | AActor | yes | yes | — | A | [notes](../actions/a_jumpifarmortype.md) |
| A_JumpIfCloser | AActor | yes | yes | — | A | [notes](../actions/a_jumpifcloser.md) |
| A_JumpIfHealthLower | AActor | yes | yes | — | A | [notes](../actions/a_jumpifhealthlower.md) |
| A_JumpIfInTargetInventory | AActor | yes | yes | — | A | [notes](../actions/a_jumpifintargetinventory.md) |
| A_JumpIfInTargetLOS | AActor | yes | yes | — | A | [notes](../actions/a_jumpifintargetlos.md) |
| A_JumpIfInventory | AActor | yes | yes | — | A | [notes](../actions/a_jumpifinventory.md) |
| A_JumpIfMasterCloser | AActor | yes | yes | — | A | [notes](../actions/a_jumpifmastercloser.md) |
| A_JumpIfNoAmmo | AActor | yes | yes | — | A | [notes](../actions/a_jumpifnoammo.md) |
| A_JumpIfTargetInLOS | AActor | yes | yes | — | A | [notes](../actions/a_jumpiftargetinlos.md) |
| A_JumpIfTargetInsideMeleeRange | AActor | yes | yes | — | A | [notes](../actions/a_jumpiftargetinsidemeleerange.md) |
| A_JumpIfTargetOutsideMeleeRange | AActor | yes | yes | — | A | [notes](../actions/a_jumpiftargetoutsidemeleerange.md) |
| A_JumpIfTracerCloser | AActor | yes | yes | — | A | [notes](../actions/a_jumpiftracercloser.md) |
| A_KBolt | AActor | no | yes | — | C |  |
| A_KBoltRaise | AActor | no | yes | — | C |  |
| A_KeenDie | AActor | yes | yes | — | C |  |
| A_KillChildren | AActor | yes | yes | yes | A | [notes](../actions/a_killchildren.md) |
| A_KillMaster | AActor | yes | yes | yes | A | [notes](../actions/a_killmaster.md) |
| A_KillSiblings | AActor | yes | yes | yes | A | [notes](../actions/a_killsiblings.md) |
| A_KlaxonBlare | AActor | no | yes | — | C |  |
| A_KnightAttack | AActor | no | yes | — | C |  |
| A_KoraxBonePop | AActor | no | yes | — | C |  |
| A_KoraxChase | AActor | no | yes | — | C |  |
| A_KoraxCommand | AActor | no | yes | — | C |  |
| A_KoraxDecide | AActor | no | yes | — | C |  |
| A_KoraxMissile | AActor | no | yes | — | C |  |
| A_KSpiritRoam | AActor | no | yes | — | C |  |
| A_LastZap | AActor | no | yes | — | C |  |
| A_LeafCheck | AActor | no | yes | — | C |  |
| A_LeafSpawn | AActor | no | yes | — | C |  |
| A_LeafThrust | AActor | no | yes | — | C |  |
| A_LichAttack | AActor | no | yes | — | C |  |
| A_LichFireGrow | AActor | no | yes | — | C |  |
| A_LichIceImpact | AActor | no | yes | — | C |  |
| A_Light | AInventory | yes | yes | — | A | [notes](../families/weapon-light.md) |
| A_Light0 | AInventory | no | yes | — | A | [notes](../families/weapon-light.md) |
| A_Light1 | AInventory | no | yes | — | A | [notes](../families/weapon-light.md) |
| A_Light2 | AInventory | no | yes | — | A | [notes](../families/weapon-light.md) |
| A_LightGoesOut | AActor | no | yes | — | C |  |
| A_LightInverse | AActor | no | yes | — | A | [notes](../families/weapon-light.md) |
| A_LightningClip | AActor | no | yes | — | C |  |
| A_LightningReady | AActor | no | yes | — | C |  |
| A_LightningRemove | AActor | no | yes | — | C |  |
| A_LightningZap | AActor | no | yes | — | C |  |
| A_LineEffect | AActor | yes | yes | yes | C |  |
| A_LoadShotgun2 | AActor | no | yes | — | C |  |
| A_Log | AActor | yes | yes | yes | C |  |
| A_LogInt | AActor | yes | yes | yes | C |  |
| A_Look | AActor | no | yes | yes | A | [notes](../actions/a_look.md) |
| A_Look2 | AActor | no | yes | yes | A | [notes](../actions/a_look2.md) |
| A_LookEx | AActor | yes | yes | yes | A | [notes](../actions/a_lookex.md) |
| A_LoopActiveSound | AActor | no | yes | — | A | [notes](../actions/a_loopactivesound.md) |
| A_LoremasterChain | AActor | no | yes | — | C |  |
| A_Lower | AInventory | no | yes | — | A | [notes](../actions/a_lower.md) |
| A_LowGravity | AActor | no | yes | — | C |  |
| A_M_BFGsound | AActor | no | yes | — | C |  |
| A_M_CheckAttack | AActor | no | yes | — | C |  |
| A_M_FireBFG | AActor | no | yes | — | C |  |
| A_M_FireCGun | AActor | yes | yes | — | C |  |
| A_M_FireMissile | AActor | no | yes | — | C |  |
| A_M_FirePistol | AActor | yes | yes | — | C |  |
| A_M_FirePlasma | AActor | no | yes | — | C |  |
| A_M_FireRailgun | AActor | no | yes | — | C |  |
| A_M_FireShotgun | AActor | no | yes | — | C |  |
| A_M_FireShotgun2 | AActor | no | yes | — | C |  |
| A_M_Punch | AActor | yes | yes | — | C |  |
| A_M_Refire | AActor | yes | yes | — | C |  |
| A_M_Saw | AActor | yes | yes | — | C |  |
| A_M_SawRefire | AActor | no | yes | — | C |  |
| A_MaceBallImpact | AActor | no | yes | — | C |  |
| A_MaceBallImpact2 | AActor | no | yes | — | C |  |
| A_MacePL1Check | AActor | no | yes | — | C |  |
| A_MageAttack | AActor | no | yes | — | C |  |
| A_MakePod | AActor | yes | yes | — | C |  |
| A_MarineChase | AActor | no | yes | — | C |  |
| A_MarineLook | AActor | no | yes | — | C |  |
| A_MarineNoise | AActor | no | yes | — | C |  |
| A_MaulerTorpedoWave | AActor | no | yes | — | C |  |
| A_MeleeAttack | AActor | no | yes | — | C |  |
| A_Metal | AActor | no | yes | — | C |  |
| A_MinotaurAtk1 | AActor | no | yes | — | C |  |
| A_MinotaurAtk2 | AActor | no | yes | — | C |  |
| A_MinotaurAtk3 | AActor | no | yes | — | C |  |
| A_MinotaurCharge | AActor | no | yes | — | C |  |
| A_MinotaurChase | AActor | no | yes | — | C |  |
| A_MinotaurDeath | AActor | no | yes | — | C |  |
| A_MinotaurDecide | AActor | no | yes | — | C |  |
| A_MinotaurLook | AActor | no | yes | — | C |  |
| A_MinotaurRoam | AActor | no | yes | — | C |  |
| A_MissileAttack | AActor | no | yes | — | C |  |
| A_MLightningAttack | AActor | yes | yes | — | C |  |
| A_MntrFloorFire | AActor | no | yes | — | C |  |
| A_MonsterRail | AActor | no | yes | yes | C |  |
| A_MonsterRefire | AActor | yes | yes | yes | A | [notes](../actions/a_monsterrefire.md) |
| A_MStaffAttack | AActor | no | yes | — | C |  |
| A_MStaffPalette | AActor | no | yes | — | C |  |
| A_MStaffTrack | AActor | no | yes | — | C |  |
| A_Mushroom | AActor | yes | yes | — | C |  |
| A_NoBlocking | AActor | no | yes | — | A | [notes](../actions/a_noblocking.md) |
| A_NoGravity | AActor | no | yes | — | C |  |
| A_OpenShotgun2 | AActor | no | yes | — | C |  |
| A_Pain | AActor | no | yes | yes | A | [notes](../actions/a_pain.md) |
| A_PainAttack | AActor | yes | yes | — | C |  |
| A_PainDie | AActor | yes | yes | — | C |  |
| A_PhoenixPuff | AActor | no | yes | — | C |  |
| A_PigPain | AActor | no | yes | — | C |  |
| A_PlayerScream | AActor | no | yes | yes | C |  |
| A_PlayerSkinCheck | AActor | yes | yes | — | C |  |
| A_PlaySound | AActor | yes | yes | — | A | [notes](../actions/a_playsound.md) |
| A_PlaySoundEx | AActor | yes | yes | yes | A | [notes](../actions/a_playsoundex.md) |
| A_PlayWeaponSound | AActor | yes | yes | — | A | [notes](../actions/a_playweaponsound.md) |
| A_PodPain | AActor | yes | yes | — | C |  |
| A_PoisonBagCheck | AActor | no | yes | — | C |  |
| A_PoisonBagDamage | AActor | no | yes | — | C |  |
| A_PoisonBagInit | AActor | no | yes | — | C |  |
| A_PoisonShroom | AActor | no | yes | — | C |  |
| A_PosAttack | AActor | no | yes | — | C |  |
| A_PotteryCheck | AActor | no | yes | — | C |  |
| A_PotteryChooseBit | AActor | no | yes | — | C |  |
| A_PotteryExplode | AActor | no | yes | — | C |  |
| A_Print | AActor | yes | yes | yes | C |  |
| A_PrintBold | AActor | yes | yes | yes | C |  |
| A_ProgrammerDeath | AActor | no | yes | — | C |  |
| A_ProgrammerMelee | AActor | no | yes | — | C |  |
| A_Punch | AActor | no | yes | — | C |  |
| A_Quake | AActor | yes | yes | yes | A | [notes](../actions/a_quake.md) |
| A_QueueCorpse | AActor | no | yes | yes | A | [notes](../actions/a_queuecorpse.md) |
| A_RadiusGive | AActor | yes | yes | yes | A | [notes](../actions/a_radiusgive.md) |
| A_RadiusThrust | AActor | yes | yes | — | A | [notes](../actions/a_radiusthrust.md) |
| A_RailAttack | AActor | yes | yes | — | A | [notes](../actions/a_railattack.md) |
| A_RailWait | AActor | no | yes | — | C |  |
| A_RainImpact | AActor | no | yes | — | C |  |
| A_Raise | AInventory | no | yes | — | A | [notes](../actions/a_raise.md) |
| A_RaiseChildren | AActor | no | yes | yes | A | [notes](../actions/a_raisechildren.md) |
| A_RaiseMaster | AActor | no | yes | yes | A | [notes](../actions/a_raisemaster.md) |
| A_RaiseSiblings | AActor | no | yes | yes | A | [notes](../actions/a_raisesiblings.md) |
| A_RandomPowerupFrame | AActor | no | yes | — | C |  |
| A_RearrangePointers | AActor | yes | yes | yes | A | [notes](../actions/a_rearrangepointers.md) |
| A_ReaverRanged | AActor | no | yes | — | C |  |
| A_Recoil | AActor | yes | yes | yes | A | [notes](../actions/a_recoil.md) |
| A_ReFire | AInventory | yes | yes | — | A | [notes](../actions/a_refire.md) |
| A_RemoveChildren | AActor | yes | yes | yes | A | [notes](../actions/a_removechildren.md) |
| A_RemoveForceField | AActor | no | yes | — | C |  |
| A_RemoveMaster | AActor | no | yes | yes | A | [notes](../actions/a_removemaster.md) |
| A_RemovePod | AActor | no | yes | — | C |  |
| A_RemoveSiblings | AActor | yes | yes | yes | A | [notes](../actions/a_removesiblings.md) |
| A_ResetReloadCounter | AActor | no | yes | — | C |  |
| A_Respawn | AActor | yes | yes | yes | C |  |
| A_RestoreSpecialDoomThing | AActor | no | yes | — | C |  |
| A_RestoreSpecialPosition | AActor | no | yes | — | C |  |
| A_RestoreSpecialThing1 | AActor | no | yes | — | C |  |
| A_RestoreSpecialThing2 | AActor | no | yes | — | C |  |
| A_RocketInFlight | AActor | no | yes | — | C |  |
| A_SargAttack | AActor | no | yes | — | C |  |
| A_Saw | AActor | yes | yes | — | C |  |
| A_ScaleVelocity | AActor | yes | yes | — | A | [notes](../actions/a_scalevelocity.md) |
| A_Scream | AActor | no | yes | — | A | [notes](../actions/a_scream.md) |
| A_ScreamAndUnblock | AActor | no | yes | — | C |  |
| A_SeekerMissile | AActor | yes | yes | yes | A | [notes](../actions/a_seekermissile.md) |
| A_SelectPiece | AActor | no | yes | — | C |  |
| A_SelectSigilAttack | AActor | no | yes | — | C |  |
| A_SelectSigilDown | AActor | no | yes | — | C |  |
| A_SelectSigilView | AActor | no | yes | — | C |  |
| A_SelectWeapon | AActor | yes | yes | — | C |  |
| A_SentinelAttack | AActor | no | yes | — | C |  |
| A_SentinelBob | AActor | no | yes | — | A | [notes](../actions/a_sentinelbob.md) |
| A_SentinelRefire | AActor | no | yes | — | C |  |
| A_SerpentCheckForAttack | AActor | no | yes | — | C |  |
| A_SerpentChooseAttack | AActor | no | yes | — | C |  |
| A_SerpentHeadCheck | AActor | no | yes | — | C |  |
| A_SerpentHide | AActor | no | yes | — | C |  |
| A_SerpentHumpDecide | AActor | no | yes | — | C |  |
| A_SerpentLowerHump | AActor | no | yes | — | C |  |
| A_SerpentMeleeAttack | AActor | no | yes | — | C |  |
| A_SerpentRaiseHump | AActor | no | yes | — | C |  |
| A_SerpentSpawnGibs | AActor | no | yes | — | C |  |
| A_SerpentUnHide | AActor | no | yes | — | C |  |
| A_SetAngle | AActor | yes | yes | yes | A | [notes](../actions/a_setangle.md) |
| A_SetArg | AActor | yes | yes | — | A | [notes](../actions/a_setarg.md) |
| A_SetBlend | AActor | yes | yes | yes | A | [notes](../actions/a_setblend.md) |
| A_SetCrosshair | AWeapon | yes | yes | — | C |  |
| A_SetDamageType | AActor | yes | yes | — | C |  |
| A_SetFloat | AActor | no | yes | — | C |  |
| A_SetFloorClip | AActor | no | yes | — | C |  |
| A_SetGravity | AActor | yes | yes | — | C |  |
| A_SetInvulnerable | AActor | no | yes | — | C |  |
| A_SetMass | AActor | yes | yes | — | C |  |
| A_SetPitch | AActor | yes | yes | yes | A | [notes](../actions/a_setpitch.md) |
| A_SetReflective | AActor | no | yes | — | C |  |
| A_SetReflectiveInvulnerable | AActor | no | yes | — | C |  |
| A_SetScale | AActor | yes | yes | — | A | [notes](../actions/a_setscale.md) |
| A_SetShadow | AActor | no | yes | — | C |  |
| A_SetShootable | AActor | no | yes | — | C |  |
| A_SetSolid | AActor | no | yes | — | C |  |
| A_SetSpecial | AActor | yes | yes | — | C |  |
| A_SetTics | AActor | yes | yes | yes | C |  |
| A_SetTranslucent | AActor | yes | yes | yes | A | [notes](../actions/a_settranslucent.md) |
| A_SetUserArray | AActor | yes | yes | yes | A | [notes](../actions/a_setuserarray.md) |
| A_SetUserVar | AActor | yes | yes | yes | A | [notes](../actions/a_setuservar.md) |
| A_ShedShard | AActor | no | yes | — | C |  |
| A_ShootGun | AActor | no | yes | — | C |  |
| A_ShowElectricFlash | AActor | no | yes | — | C |  |
| A_ShutdownPhoenixPL2 | AActor | no | yes | — | C |  |
| A_SigilCharge | AActor | no | yes | — | C |  |
| A_SinkGib | AActor | no | yes | — | C |  |
| A_SkelFist | AActor | no | yes | — | C |  |
| A_SkelMissile | AActor | no | yes | — | C |  |
| A_SkelWhoosh | AActor | no | yes | — | C |  |
| A_SkullAttack | AActor | yes | yes | — | A | [notes](../actions/a_skullattack.md) |
| A_SkullPop | AActor | yes | yes | — | C |  |
| A_SkullRodStorm | AActor | no | yes | — | C |  |
| A_SmBounce | AActor | no | yes | — | C |  |
| A_SnoutAttack | AActor | no | yes | — | C |  |
| A_SoAExplode | AActor | no | yes | — | C |  |
| A_Sor1Chase | AActor | no | yes | — | C |  |
| A_Sor1Pain | AActor | no | yes | — | C |  |
| A_Sor2DthInit | AActor | no | yes | — | C |  |
| A_Sor2DthLoop | AActor | no | yes | — | C |  |
| A_SorcBallOrbit | AActor | no | yes | — | C |  |
| A_SorcBallPop | AActor | no | yes | — | C |  |
| A_SorcBossAttack | AActor | no | yes | — | C |  |
| A_SorcererBishopEntry | AActor | no | yes | — | C |  |
| A_SorcererRise | AActor | no | yes | — | C |  |
| A_SorcFX1Seek | AActor | no | yes | — | C |  |
| A_SorcFX2Orbit | AActor | no | yes | — | C |  |
| A_SorcFX2Split | AActor | no | yes | — | C |  |
| A_SorcFX4Check | AActor | no | yes | — | C |  |
| A_SorcSpinBalls | AActor | no | yes | — | C |  |
| A_SpawnBishop | AActor | no | yes | — | C |  |
| A_SpawnDebris | AActor | yes | yes | yes | A | [notes](../actions/a_spawndebris.md) |
| A_SpawnEntity | AActor | no | yes | — | C |  |
| A_SpawnFizzle | AActor | no | yes | — | C |  |
| A_SpawnFly | AActor | yes | yes | — | C |  |
| A_SpawnItem | AActor | yes | yes | — | A | [notes](../actions/a_spawnitem.md) |
| A_SpawnItemEx | AActor | yes | yes | — | A | [notes](../actions/a_spawnitemex.md) |
| A_SpawnProgrammerBase | AActor | no | yes | — | C |  |
| A_SpawnRippers | AActor | no | yes | — | C |  |
| A_SpawnSingleItem | AActor | yes | yes | — | C |  |
| A_SpawnSound | AActor | no | yes | — | C |  |
| A_SpectralBigBallLightning | AActor | no | yes | — | C |  |
| A_SpectralLightning | AActor | no | yes | — | C |  |
| A_SpectralLightningTail | AActor | no | yes | — | C |  |
| A_Spectre3Attack | AActor | no | yes | — | C |  |
| A_SpectreChunkLarge | AActor | no | yes | — | C |  |
| A_SpectreChunkSmall | AActor | no | yes | — | C |  |
| A_SpeedBalls | AActor | no | yes | — | C |  |
| A_SpidRefire | AActor | no | yes | — | C |  |
| A_SPosAttack | AActor | no | yes | — | C |  |
| A_SPosAttackUseAtkSound | AActor | no | yes | — | C |  |
| A_SpotLightning | AActor | no | yes | — | C |  |
| A_Srcr1Attack | AActor | no | yes | — | C |  |
| A_Srcr2Attack | AActor | no | yes | — | C |  |
| A_Srcr2Decide | AActor | no | yes | — | C |  |
| A_StaffAttack | AActor | yes | yes | — | C |  |
| A_StalkerAttack | AActor | no | yes | — | C |  |
| A_StalkerChaseDecide | AActor | no | yes | — | C |  |
| A_StalkerDrop | AActor | no | yes | — | C |  |
| A_StalkerLookInit | AActor | no | yes | — | C |  |
| A_StalkerWalk | AActor | no | yes | — | C |  |
| A_StartFire | AActor | no | yes | — | C |  |
| A_Stop | AActor | no | yes | — | A | [notes](../actions/a_stop.md) |
| A_StopSound | AActor | yes | yes | — | A | [notes](../actions/a_stopsound.md) |
| A_StopSoundEx | AActor | yes | yes | yes | C |  |
| A_SubEntityDeath | AActor | no | yes | — | C |  |
| A_Summon | AActor | no | yes | — | C |  |
| A_TakeFromChildren | AActor | yes | yes | — | C |  |
| A_TakeFromSiblings | AActor | yes | yes | — | C |  |
| A_TakeFromTarget | AActor | yes | yes | — | A | [notes](../actions/a_takefromtarget.md) |
| A_TakeInventory | AActor | yes | yes | — | A | [notes](../actions/a_takeinventory.md) |
| A_Teleport | AActor | yes | yes | yes | A | [notes](../actions/a_teleport.md) |
| A_TeloSpawnA | AActor | no | yes | — | C |  |
| A_TeloSpawnB | AActor | no | yes | — | C |  |
| A_TeloSpawnC | AActor | no | yes | — | C |  |
| A_TeloSpawnD | AActor | no | yes | — | C |  |
| A_TemplarAttack | AActor | no | yes | — | C |  |
| A_ThrowGrenade | AActor | yes | yes | — | C |  |
| A_ThrustImpale | AActor | no | yes | — | C |  |
| A_ThrustInitDn | AActor | no | yes | — | C |  |
| A_ThrustInitUp | AActor | no | yes | — | C |  |
| A_ThrustLower | AActor | no | yes | — | C |  |
| A_ThrustRaise | AActor | no | yes | — | C |  |
| A_TimeBomb | AActor | no | yes | — | C |  |
| A_TossArm | AActor | no | yes | — | C |  |
| A_TossGib | AActor | no | yes | — | C |  |
| A_Tracer | AActor | no | yes | — | A | [notes](../actions/a_tracer.md) |
| A_Tracer2 | AActor | no | yes | — | A | [notes](../actions/a_tracer2.md) |
| A_TransferPointer | AActor | yes | yes | yes | A | [notes](../actions/a_transferpointer.md) |
| A_TroopAttack | AActor | no | yes | — | C |  |
| A_Turn | AActor | yes | yes | — | C |  |
| A_TurretLook | AActor | no | yes | — | A | [notes](../actions/a_turretlook.md) |
| A_UnHideThing | AActor | no | yes | — | C |  |
| A_UnsetFloat | AActor | no | yes | — | C |  |
| A_UnSetFloorClip | AActor | no | yes | — | C |  |
| A_UnSetInvulnerable | AActor | no | yes | — | C |  |
| A_UnSetReflective | AActor | no | yes | — | C |  |
| A_UnSetReflectiveInvulnerable | AActor | no | yes | — | C |  |
| A_UnSetShootable | AActor | no | yes | — | C |  |
| A_UnsetSolid | AActor | no | yes | — | C |  |
| A_VileAttack | AActor | yes | yes | — | C |  |
| A_VileChase | AActor | no | yes | — | C |  |
| A_VileStart | AActor | no | yes | — | C |  |
| A_VileTarget | AActor | yes | yes | — | C |  |
| A_VolcanoBlast | AActor | no | yes | — | C |  |
| A_VolcanoSet | AActor | no | yes | — | C |  |
| A_VolcBallImpact | AActor | no | yes | — | C |  |
| A_WakeOracleSpectre | AActor | no | yes | — | C |  |
| A_Wander | AActor | no | yes | — | A | [notes](../actions/a_wander.md) |
| A_Warp | AActor | yes | yes | yes | A | [notes](../actions/a_warp.md) |
| A_WeaponReady | AInventory | yes | yes | — | A | [notes](../actions/a_weaponready.md) |
| A_Weave | AActor | yes | yes | yes | A | [notes](../actions/a_weave.md) |
| A_WhirlwindSeek | AActor | no | yes | — | C |  |
| A_WizAtk1 | AActor | no | yes | — | C |  |
| A_WizAtk2 | AActor | no | yes | — | C |  |
| A_WizAtk3 | AActor | no | yes | — | C |  |
| A_WolfAttack | AActor | yes | yes | yes | C |  |
| A_WraithChase | AActor | no | yes | — | C |  |
| A_WraithFX2 | AActor | no | yes | — | C |  |
| A_WraithFX3 | AActor | no | yes | — | C |  |
| A_WraithInit | AActor | no | yes | — | C |  |
| A_WraithMelee | AActor | no | yes | — | C |  |
| A_WraithRaise | AActor | no | yes | — | C |  |
| A_WraithRaiseInit | AActor | no | yes | — | C |  |
| A_XScream | AActor | no | yes | — | A | [notes](../actions/a_xscream.md) |
| A_ZapMimic | AActor | no | yes | — | C |  |
| A_ZoomFactor | AWeapon | yes | yes | — | A | [notes](../actions/a_zoomfactor.md) |
| ACS_NamedExecute | AActor | yes | yes | — | C |  |
| ACS_NamedExecuteAlways | AActor | yes | yes | — | C |  |
| ACS_NamedExecuteWithResult | AActor | yes | yes | — | C |  |
| ACS_NamedLockedExecute | AActor | yes | yes | — | C |  |
| ACS_NamedLockedExecuteDoor | AActor | yes | yes | — | C |  |
| ACS_NamedSuspend | AActor | yes | yes | — | C |  |
| ACS_NamedTerminate | AActor | yes | yes | — | C |  |
| SetFOV | _PlayerInfo | no | yes | yes | C |  |
