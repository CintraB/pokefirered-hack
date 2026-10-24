ThreeIsland_BerryForest_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, ThreeIsland_BerryForest_OnTransition
	map_script MAP_SCRIPT_ON_RESUME, ThreeIsland_BerryForest_OnResume
	.byte 0

ThreeIsland_BerryForest_OnTransition::
	setworldmapflag FLAG_WORLD_MAP_THREE_ISLAND_BERRY_FOREST
	setescapewarp MAP_THREE_ISLAND_BOND_BRIDGE, 12, 6
	call ThreeIsland_BerryForest_EventScript_TryShowCelebi
	end

@ Celebi: escondido por padrão; aparece só ao amanhecer (TIME_MORNING), depois das Ilhas Sevii
@ (FLAG_SYS_CAN_LINK_WITH_RS), se não voou para longe e ainda não foi capturado.
@ O clima do Bosque é fixo (WEATHER_SHADE): só o horário conta. Reavalia a cada entrada no mapa.
ThreeIsland_BerryForest_EventScript_TryShowCelebi::
	setflag FLAG_HIDE_CELEBI
	goto_if_unset FLAG_SYS_CAN_LINK_WITH_RS, EventScript_Return
	goto_if_set FLAG_CELEBI_FLEW_AWAY, EventScript_Return
	setvar VAR_0x8004, SPECIES_CELEBI
	specialvar VAR_RESULT, IsSpeciesCaught
	goto_if_eq VAR_RESULT, TRUE, EventScript_Return
	specialvar VAR_RESULT, GetDayNightPeriodForScript
	goto_if_ne VAR_RESULT, TIME_MORNING, EventScript_Return
	clearflag FLAG_HIDE_CELEBI
	return

ThreeIsland_BerryForest_OnResume::
	call_if_set FLAG_SYS_SPECIAL_WILD_BATTLE, ThreeIsland_BerryForest_EventScript_TryRemoveCelebi
	end

ThreeIsland_BerryForest_EventScript_TryRemoveCelebi::
	specialvar VAR_RESULT, GetBattleOutcome
	goto_if_ne VAR_RESULT, B_OUTCOME_CAUGHT, EventScript_Return
	removeobject LOCALID_BERRY_FOREST_CELEBI
	return

ThreeIsland_BerryForest_EventScript_Celebi::
	goto_if_questlog EventScript_ReleaseEnd
	@ Reconfere na conversa o que não depende de horário/clima: um save anterior ao Hack 8 gravado
	@ dentro do mapa pode trazer um objeto velho com este script até a troca de mapa (fica mudo).
	goto_if_set FLAG_CELEBI_FLEW_AWAY, EventScript_ReleaseEnd
	goto_if_unset FLAG_SYS_CAN_LINK_WITH_RS, EventScript_ReleaseEnd
	setvar VAR_0x8004, SPECIES_CELEBI
	specialvar VAR_RESULT, IsSpeciesCaught
	goto_if_eq VAR_RESULT, TRUE, EventScript_ReleaseEnd
	special QuestLog_CutRecording
	lock
	faceplayer
	waitse
	playmoncry SPECIES_CELEBI, CRY_MODE_ENCOUNTER
	waitmoncry
	delay 20
	setwildbattle SPECIES_CELEBI, 30
	setflag FLAG_SYS_SPECIAL_WILD_BATTLE
	special StartLegendaryBattle
	waitstate
	clearflag FLAG_SYS_SPECIAL_WILD_BATTLE
	specialvar VAR_RESULT, GetBattleOutcome
	goto_if_eq VAR_RESULT, B_OUTCOME_WON, ThreeIsland_BerryForest_EventScript_DefeatedCelebi
	goto_if_eq VAR_RESULT, B_OUTCOME_RAN, ThreeIsland_BerryForest_EventScript_RanFromCelebi
	goto_if_eq VAR_RESULT, B_OUTCOME_PLAYER_TELEPORTED, ThreeIsland_BerryForest_EventScript_RanFromCelebi
	release
	end

ThreeIsland_BerryForest_EventScript_DefeatedCelebi::
	setflag FLAG_CELEBI_FLEW_AWAY
	setvar VAR_0x8004, SPECIES_CELEBI
	goto EventScript_MonFlewAway
	end

ThreeIsland_BerryForest_EventScript_RanFromCelebi::
	setflag FLAG_CELEBI_FLEW_AWAY
	setvar VAR_0x8004, SPECIES_CELEBI
	goto EventScript_MonFlewAway
	end

ThreeIsland_BerryForest_EventScript_Lostelle::
	lock
	faceplayer
	msgbox ThreeIsland_BerryForest_Text_HelpScaryPokemon
	playse SE_PIN
	applymovement LOCALID_BERRY_FOREST_LOSTELLE, Common_Movement_ExclamationMark
	waitmovement 0
	applymovement LOCALID_BERRY_FOREST_LOSTELLE, ThreeIsland_BerryForest_Movement_LostelleLookAround
	waitmovement 0
	msgbox ThreeIsland_BerryForest_Text_HereItComesAgain
	goto_if_questlog EventScript_ReleaseEnd
	waitse
	playmoncry SPECIES_HYPNO, CRY_MODE_ENCOUNTER
	waitmoncry
	setwildbattle SPECIES_HYPNO, 30
	dowildbattle
	special QuestLog_CutRecording
	applymovement LOCALID_BERRY_FOREST_LOSTELLE, Common_Movement_FacePlayer
	waitmovement 0
	msgbox ThreeIsland_BerryForest_Text_ThankYouHaveThis
	giveitem ITEM_IAPAPA_BERRY
	call_if_eq VAR_RESULT, FALSE, ThreeIsland_BerryForest_EventScript_NoRoomForBerry
	special BufferBigGuyOrBigGirlString
	msgbox ThreeIsland_BerryForest_Text_LetsGoHome
	closemessage
	setflag FLAG_RESCUED_LOSTELLE
	setflag FLAG_HIDE_LOSTELLE_IN_BERRY_FOREST
	setvar VAR_MAP_SCENE_TWO_ISLAND_JOYFUL_GAME_CORNER, 2
	clearflag FLAG_HIDE_TWO_ISLAND_GAME_CORNER_LOSTELLE
	warp MAP_TWO_ISLAND_JOYFUL_GAME_CORNER, 6, 6
	waitstate
	release
	end

ThreeIsland_BerryForest_EventScript_NoRoomForBerry::
	msgbox ThreeIsland_BerryForest_Text_BerryPouchIsFull
	return

ThreeIsland_BerryForest_Movement_LostelleLookAround::
	walk_in_place_faster_left
	delay_16
	walk_in_place_faster_right
	delay_8
	walk_in_place_faster_left
	step_end

ThreeIsland_BerryForest_EventScript_WelcomeSign::
	msgbox ThreeIsland_BerryForest_Text_WelcomeToBerryForest, MSGBOX_SIGN
	end

ThreeIsland_BerryForest_EventScript_ForestWakesWithSunSign::
	msgbox ThreeIsland_BerryForest_Text_ForestWakesWithSun, MSGBOX_SIGN
	end

ThreeIsland_BerryForest_EventScript_BewareSign::
	msgbox ThreeIsland_BerryForest_Text_BewareWildBerryLovingMons, MSGBOX_SIGN
	end
