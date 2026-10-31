IndigoPlateau_PokemonCenter_1F_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, IndigoPlateau_PokemonCenter_1F_OnTransition
	map_script MAP_SCRIPT_ON_RESUME, CableClub_OnResume
	.byte 0

IndigoPlateau_PokemonCenter_1F_OnTransition::
	setrespawn HEAL_LOCATION_INDIGO_PLATEAU
	specialvar VAR_RESULT, IsNationalPokedexEnabled
	call_if_eq VAR_RESULT, TRUE, IndigoPlateau_PokemonCenter_1F_EventScript_CheckBlockDoor
	end

IndigoPlateau_PokemonCenter_1F_EventScript_CheckBlockDoor::
	goto_if_set FLAG_SYS_CAN_LINK_WITH_RS, EventScript_Return
	setobjectxyperm LOCALID_LEAGUE_DOOR_GUARD, 4, 2
	return

IndigoPlateau_PokemonCenter_1F_EventScript_DoorGuard::
	lock
	faceplayer
	specialvar VAR_RESULT, IsNationalPokedexEnabled
	goto_if_eq VAR_RESULT, TRUE, IndigoPlateau_PokemonCenter_1F_EventScript_CheckSeviiIslandComplete
	call_if_set FLAG_SYS_GAME_CLEAR, IndigoPlateau_PokemonCenter_1F_EventScript_AskTier
	msgbox IndigoPlateau_PokemonCenter_1F_Text_FaceEliteFourGoodLuck
	release
	end

IndigoPlateau_PokemonCenter_1F_EventScript_CheckSeviiIslandComplete::
	goto_if_set FLAG_SYS_CAN_LINK_WITH_RS, IndigoPlateau_PokemonCenter_1F_EventScript_SeviiIslandComplete
	msgbox IndigoPlateau_PokemonCenter_1F_Text_LoreleiIsAbsentClosedForTimeBeing
	call_if_set FLAG_SYS_GAME_CLEAR, IndigoPlateau_PokemonCenter_1F_EventScript_AskTierLeagueClosed
	release
	end

IndigoPlateau_PokemonCenter_1F_EventScript_SeviiIslandComplete::
	call_if_set FLAG_SYS_GAME_CLEAR, IndigoPlateau_PokemonCenter_1F_EventScript_AskTier
	msgbox IndigoPlateau_PokemonCenter_1F_Text_FaceEliteFourGoodLuck
	release
	end

@ POK-42: depois do Hall da Fama, a guarda pergunta o degrau da Liga e das revanches do Vs. Seeker quando o jogador
@ pisa em frente à porta (uma vez por visita: VAR_TEMP_1 zera a cada mapa) ou fala com ela.
IndigoPlateau_PokemonCenter_1F_EventScript_TierTrigger::
	goto_if_questlog EventScript_ReleaseEnd
	goto_if_unset FLAG_SYS_GAME_CLEAR, IndigoPlateau_PokemonCenter_1F_EventScript_TierTriggerOff
	lockall
	textcolor NPC_TEXT_COLOR_FEMALE
	call IndigoPlateau_PokemonCenter_1F_EventScript_AskTier
	releaseall
	end

IndigoPlateau_PokemonCenter_1F_EventScript_TierTriggerOff::
	setvar VAR_TEMP_1, 1
	end

@ Liga aberta: a confirmação cita a Elite Quatro.
IndigoPlateau_PokemonCenter_1F_EventScript_AskTier::
	goto_if_questlog EventScript_Return
	call IndigoPlateau_PokemonCenter_1F_EventScript_ChooseTier
	goto_if_eq VAR_RESULT, SCR_MENU_CANCEL, EventScript_Return
	msgbox IndigoPlateau_PokemonCenter_1F_Text_TierSet
	return

@ Liga fechada (Dex Nacional antes do fim das Ilhas Sevii, Lorelei ausente): o degrau vale só no Vs. Seeker.
IndigoPlateau_PokemonCenter_1F_EventScript_AskTierLeagueClosed::
	goto_if_questlog EventScript_Return
	call IndigoPlateau_PokemonCenter_1F_EventScript_ChooseTier
	goto_if_eq VAR_RESULT, SCR_MENU_CANCEL, EventScript_Return
	msgbox IndigoPlateau_PokemonCenter_1F_Text_TierSetLeagueClosed
	return

@ A pergunta e a lista; com B, VAR_RESULT fica em SCR_MENU_CANCEL (o msgbox não mexe nele) e o degrau não muda.
IndigoPlateau_PokemonCenter_1F_EventScript_ChooseTier::
	setvar VAR_TEMP_1, 1
	special BufferRematchTierName
	message IndigoPlateau_PokemonCenter_1F_Text_AskTier
	waitmessage
	multichoice 20, 0, MULTICHOICE_REMATCH_TIER, FALSE
	goto_if_eq VAR_RESULT, SCR_MENU_CANCEL, IndigoPlateau_PokemonCenter_1F_EventScript_KeepTier
	copyvar VAR_REMATCH_TIER, VAR_RESULT
	special BufferRematchTierName
	return

IndigoPlateau_PokemonCenter_1F_EventScript_KeepTier::
	msgbox IndigoPlateau_PokemonCenter_1F_Text_KeepTier
	return

IndigoPlateau_PokemonCenter_1F_EventScript_GymGuy::
	msgbox IndigoPlateau_PokemonCenter_1F_Text_GymGuyAdvice, MSGBOX_NPC
	end

IndigoPlateau_PokemonCenter_1F_EventScript_Clerk::
	goto_if_questlog EventScript_ReleaseEnd
	lock
	faceplayer
	message Text_MayIHelpYou
	waitmessage
	pokemart IndigoPlateau_PokemonCenter_1F_Items
	msgbox Text_PleaseComeAgain
	release
	end

	.align 2
IndigoPlateau_PokemonCenter_1F_Items::
	.2byte ITEM_ULTRA_BALL
	.2byte ITEM_GREAT_BALL
	.2byte ITEM_FULL_RESTORE
	.2byte ITEM_MAX_POTION
	.2byte ITEM_REVIVE
	.2byte ITEM_FULL_HEAL
	.2byte ITEM_MAX_REPEL
	.2byte ITEM_NONE
	release
	end

IndigoPlateau_PokemonCenter_1F_EventScript_Nurse::
	lock
	faceplayer
	call EventScript_PkmnCenterNurse
	release
	end
