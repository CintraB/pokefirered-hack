SixIsland_GreenPath_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, SixIsland_GreenPath_OnTransition
	map_script MAP_SCRIPT_ON_RESUME, SixIsland_GreenPath_OnResume
	.byte 0

@ POK-28: a "árvore estranha" no recanto ao norte do caminho, a oeste da placa, é um Sudowoodo nv 35 (molde do Jirachi
@ de Tanoby). Escondido por padrão; aparece com a Dex Nacional, se não fugiu e se ainda não foi capturado. Reavaliado a
@ cada entrada no mapa. Derrotado ou com fuga, some até a próxima entrada no Hall da Fama (EventScript_ResetLegendaries);
@ capturado, some para sempre.
SixIsland_GreenPath_OnTransition::
	call SixIsland_GreenPath_EventScript_TryShowSudowoodo
	end

SixIsland_GreenPath_EventScript_TryShowSudowoodo::
	setflag FLAG_HIDE_SUDOWOODO
	goto_if_set FLAG_SUDOWOODO_FLEW_AWAY, EventScript_Return
	specialvar VAR_RESULT, IsNationalPokedexEnabled
	goto_if_eq VAR_RESULT, FALSE, EventScript_Return
	setvar VAR_0x8004, SPECIES_SUDOWOODO
	specialvar VAR_RESULT, IsSpeciesCaught
	goto_if_eq VAR_RESULT, TRUE, EventScript_Return
	clearflag FLAG_HIDE_SUDOWOODO
	return

SixIsland_GreenPath_OnResume::
	call_if_set FLAG_SYS_SPECIAL_WILD_BATTLE, SixIsland_GreenPath_EventScript_TryRemoveSudowoodo
	end

SixIsland_GreenPath_EventScript_TryRemoveSudowoodo::
	specialvar VAR_RESULT, GetBattleOutcome
	goto_if_ne VAR_RESULT, B_OUTCOME_CAUGHT, EventScript_Return
	removeobject LOCALID_GREEN_PATH_SUDOWOODO
	return

@ Batalha selvagem comum (setwildbattle + dowildbattle, como o Snorlax da Rota 12): música e transição de selvagem.
SixIsland_GreenPath_EventScript_Sudowoodo::
	goto_if_questlog EventScript_ReleaseEnd
	@ Reconfere na conversa o que não depende do mapa (fuga, Dex Nacional, já capturado): um save gravado aqui antes da fuga pode trazer o objeto de volta
	@ até a troca de mapa (fica mudo).
	goto_if_set FLAG_SUDOWOODO_FLEW_AWAY, EventScript_ReleaseEnd
	specialvar VAR_RESULT, IsNationalPokedexEnabled
	goto_if_eq VAR_RESULT, FALSE, EventScript_ReleaseEnd
	setvar VAR_0x8004, SPECIES_SUDOWOODO
	specialvar VAR_RESULT, IsSpeciesCaught
	goto_if_eq VAR_RESULT, TRUE, EventScript_ReleaseEnd
	special QuestLog_CutRecording
	lock
	msgbox SixIsland_GreenPath_Text_StrangeTree
	waitse
	playmoncry SPECIES_SUDOWOODO, CRY_MODE_ENCOUNTER
	delay 40
	waitmoncry
	setwildbattle SPECIES_SUDOWOODO, 35
	setflag FLAG_SYS_SPECIAL_WILD_BATTLE
	dowildbattle
	clearflag FLAG_SYS_SPECIAL_WILD_BATTLE
	specialvar VAR_RESULT, GetBattleOutcome
	goto_if_eq VAR_RESULT, B_OUTCOME_WON, SixIsland_GreenPath_EventScript_SudowoodoRanOff
	goto_if_eq VAR_RESULT, B_OUTCOME_RAN, SixIsland_GreenPath_EventScript_SudowoodoRanOff
	goto_if_eq VAR_RESULT, B_OUTCOME_PLAYER_TELEPORTED, SixIsland_GreenPath_EventScript_SudowoodoRanOff
	goto_if_eq VAR_RESULT, B_OUTCOME_MON_FLED, SixIsland_GreenPath_EventScript_SudowoodoRanOff
	release
	end

@ Derrotado ou com fuga: sai correndo e só volta na próxima entrada no Hall da Fama
SixIsland_GreenPath_EventScript_SudowoodoRanOff::
	setflag FLAG_SUDOWOODO_FLEW_AWAY
	fadescreen FADE_TO_BLACK
	removeobject LOCALID_GREEN_PATH_SUDOWOODO
	fadescreen FADE_FROM_BLACK
	msgbox SixIsland_GreenPath_Text_SudowoodoRanOff
	release
	end

SixIsland_GreenPath_EventScript_RightRouteSign::
	msgbox SixIsland_GreenPath_Text_LeftRouteSign, MSGBOX_SIGN
	end

SixIsland_GreenPath_EventScript_LeftRouteSign::
	msgbox SixIsland_GreenPath_Text_RightRouteSign, MSGBOX_SIGN
	end
