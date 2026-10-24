PokemonMansion_B1F_MapScripts::
	map_script MAP_SCRIPT_ON_LOAD, PokemonMansion_B1F_OnLoad
	map_script MAP_SCRIPT_ON_TRANSITION, PokemonMansion_B1F_OnTransition
	map_script MAP_SCRIPT_ON_RESUME, PokemonMansion_B1F_OnResume
	.byte 0

PokemonMansion_B1F_OnLoad::
	call_if_set FLAG_POKEMON_MANSION_SWITCH_STATE, PokemonMansion_EventScript_PressSwitch_B1F
	call PokemonMansion_B1F_EventScript_TryOpenMewPassage
	end

@ Hack 8: depois de capturar o Mewtwo, abre um corte na parede (x=20..22, y=13..17) igual ao que o
@ B1F já tem em x=5..7. Antes disso o mapa fica como o original.
PokemonMansion_B1F_EventScript_TryOpenMewPassage::
	setvar VAR_0x8004, SPECIES_MEWTWO
	specialvar VAR_RESULT, IsSpeciesCaught
	goto_if_eq VAR_RESULT, FALSE, EventScript_Return
	setmetatile 19, 13, 0x353, 0
	setmetatile 20, 13, METATILE_PokemonMansion_BasementFloor, 0
	setmetatile 21, 13, METATILE_PokemonMansion_BasementFloor, 0
	setmetatile 22, 13, METATILE_PokemonMansion_BasementFloor, 0
	setmetatile 23, 13, 0x351, 0
	setmetatile 19, 14, 0x2F4, 1
	setmetatile 20, 14, METATILE_PokemonMansion_BasementFloor_ShadeFull, 0
	setmetatile 21, 14, METATILE_PokemonMansion_BasementFloor, 0
	setmetatile 22, 14, METATILE_PokemonMansion_BasementFloor, 0
	setmetatile 23, 14, 0x2F3, 1
	setmetatile 19, 15, 0x2FC, 1
	setmetatile 20, 15, METATILE_PokemonMansion_BasementFloor_ShadeFull, 0
	setmetatile 21, 15, METATILE_PokemonMansion_BasementFloor, 0
	setmetatile 22, 15, METATILE_PokemonMansion_BasementFloor, 0
	setmetatile 23, 15, 0x2FB, 1
	setmetatile 19, 16, 0x304, 1
	setmetatile 20, 16, METATILE_PokemonMansion_BasementFloor_ShadeFull, 0
	setmetatile 21, 16, METATILE_PokemonMansion_BasementFloor, 0
	setmetatile 22, 16, METATILE_PokemonMansion_BasementFloor, 0
	setmetatile 23, 16, 0x303, 1
	setmetatile 20, 17, METATILE_PokemonMansion_BasementFloor_ShadeFull, 0
	setmetatile 21, 17, METATILE_PokemonMansion_BasementFloor, 0
	setmetatile 22, 17, METATILE_PokemonMansion_BasementFloor, 0
	return

PokemonMansion_B1F_OnTransition::
	call PokemonMansion_B1F_EventScript_TryShowMew
	end

@ O Mew fica escondido; só aparece com o Mewtwo capturado, o Mew ainda não capturado e sem ter fugido.
PokemonMansion_B1F_EventScript_TryShowMew::
	setflag FLAG_HIDE_MEW
	goto_if_set FLAG_MEW_FLEW_AWAY, EventScript_Return
	setvar VAR_0x8004, SPECIES_MEWTWO
	specialvar VAR_RESULT, IsSpeciesCaught
	goto_if_eq VAR_RESULT, FALSE, EventScript_Return
	setvar VAR_0x8004, SPECIES_MEW
	specialvar VAR_RESULT, IsSpeciesCaught
	goto_if_eq VAR_RESULT, TRUE, EventScript_Return
	clearflag FLAG_HIDE_MEW
	return

PokemonMansion_B1F_OnResume::
	call_if_set FLAG_SYS_SPECIAL_WILD_BATTLE, PokemonMansion_B1F_EventScript_TryRemoveMew
	end

PokemonMansion_B1F_EventScript_TryRemoveMew::
	specialvar VAR_RESULT, GetBattleOutcome
	goto_if_ne VAR_RESULT, B_OUTCOME_CAUGHT, EventScript_Return
	removeobject LOCALID_POKEMON_MANSION_B1F_MEW
	return

PokemonMansion_B1F_EventScript_Mew::
	goto_if_questlog EventScript_ReleaseEnd
	@ Reconfere na conversa o que não depende de horário/clima: um save anterior ao Hack 8 gravado
	@ dentro do mapa pode trazer um objeto velho com este script até a troca de mapa (fica mudo).
	goto_if_set FLAG_MEW_FLEW_AWAY, EventScript_ReleaseEnd
	setvar VAR_0x8004, SPECIES_MEWTWO
	specialvar VAR_RESULT, IsSpeciesCaught
	goto_if_eq VAR_RESULT, FALSE, EventScript_ReleaseEnd
	setvar VAR_0x8004, SPECIES_MEW
	specialvar VAR_RESULT, IsSpeciesCaught
	goto_if_eq VAR_RESULT, TRUE, EventScript_ReleaseEnd
	special QuestLog_CutRecording
	lock
	faceplayer
	waitse
	playmoncry SPECIES_MEW, CRY_MODE_ENCOUNTER
	message PokemonMansion_B1F_Text_Mew
	waitmessage
	waitmoncry
	delay 20
	playbgm MUS_ENCOUNTER_GYM_LEADER, 0
	waitbuttonpress
	setwildbattle SPECIES_MEW, 30
	setflag FLAG_SYS_SPECIAL_WILD_BATTLE
	special StartLegendaryBattle
	waitstate
	clearflag FLAG_SYS_SPECIAL_WILD_BATTLE
	specialvar VAR_RESULT, GetBattleOutcome
	goto_if_eq VAR_RESULT, B_OUTCOME_WON, PokemonMansion_B1F_EventScript_DefeatedMew
	goto_if_eq VAR_RESULT, B_OUTCOME_RAN, PokemonMansion_B1F_EventScript_RanFromMew
	goto_if_eq VAR_RESULT, B_OUTCOME_PLAYER_TELEPORTED, PokemonMansion_B1F_EventScript_RanFromMew
	release
	end

PokemonMansion_B1F_EventScript_DefeatedMew::
	setflag FLAG_MEW_FLEW_AWAY
	setvar VAR_0x8004, SPECIES_MEW
	goto EventScript_MonFlewAway
	end

PokemonMansion_B1F_EventScript_RanFromMew::
	setflag FLAG_MEW_FLEW_AWAY
	setvar VAR_0x8004, SPECIES_MEW
	goto EventScript_MonFlewAway
	end

PokemonMansion_B1F_EventScript_Statue::
	lockall
	setvar VAR_0x8004, 3
	call PokemonMansion_EventScript_SecretSwitch
	playse SE_UNLOCK
	special DrawWholeMapView
	waitse
	releaseall
	end

PokemonMansion_B1F_EventScript_DiarySep1st::
	msgbox PokemonMansion_B1F_Text_MewtwoIsFarTooPowerful, MSGBOX_SIGN
	end

PokemonMansion_B1F_EventScript_DiaryMewHint::
	msgbox PokemonMansion_B1F_Text_DiaryMewHint, MSGBOX_SIGN
	end

PokemonMansion_B1F_EventScript_Lewis::
	trainerbattle_single TRAINER_BURGLAR_LEWIS, PokemonMansion_B1F_Text_LewisIntro, PokemonMansion_B1F_Text_LewisDefeat
	msgbox PokemonMansion_B1F_Text_LewisPostBattle, MSGBOX_AUTOCLOSE
	end

PokemonMansion_B1F_EventScript_Ivan::
	trainerbattle_single TRAINER_SCIENTIST_IVAN, PokemonMansion_B1F_Text_IvanIntro, PokemonMansion_B1F_Text_IvanDefeat
	msgbox PokemonMansion_B1F_Text_IvanPostBattle, MSGBOX_AUTOCLOSE
	end
