SevenIsland_TanobyRuins_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, SevenIsland_TanobyRuins_OnTransition
	map_script MAP_SCRIPT_ON_RESUME, SevenIsland_TanobyRuins_OnResume
	.byte 0

@ Hack 8: Jirachi shows up as a glint of starlight, once per apparition, only when the Deoxys is
@ already caught, it is night with a clear sky and Jirachi was not caught yet. Re-evaluated every
@ time the map is entered (the weather is already rolled by then, in the saved weather).
SevenIsland_TanobyRuins_OnTransition::
	call SevenIsland_TanobyRuins_EventScript_TryShowJirachi
	end

SevenIsland_TanobyRuins_EventScript_TryShowJirachi::
	setflag FLAG_HIDE_JIRACHI
	goto_if_set FLAG_JIRACHI_FLEW_AWAY, EventScript_Return
	setvar VAR_0x8004, SPECIES_DEOXYS
	specialvar VAR_RESULT, IsSpeciesCaught
	goto_if_eq VAR_RESULT, FALSE, EventScript_Return
	setvar VAR_0x8004, SPECIES_JIRACHI
	specialvar VAR_RESULT, IsSpeciesCaught
	goto_if_eq VAR_RESULT, TRUE, EventScript_Return
	specialvar VAR_RESULT, GetDayNightPeriodForScript
	goto_if_ne VAR_RESULT, TIME_NIGHT, EventScript_Return
	specialvar VAR_RESULT, IsSkyClear
	goto_if_eq VAR_RESULT, FALSE, EventScript_Return
	clearflag FLAG_HIDE_JIRACHI
	return

SevenIsland_TanobyRuins_OnResume::
	call_if_set FLAG_SYS_SPECIAL_WILD_BATTLE, SevenIsland_TanobyRuins_EventScript_TryRemoveJirachi
	end

SevenIsland_TanobyRuins_EventScript_TryRemoveJirachi::
	specialvar VAR_RESULT, GetBattleOutcome
	goto_if_ne VAR_RESULT, B_OUTCOME_CAUGHT, EventScript_Return
	removeobject LOCALID_TANOBY_RUINS_JIRACHI
	return

SevenIsland_TanobyRuins_EventScript_Jirachi::
	goto_if_questlog EventScript_ReleaseEnd
	special QuestLog_CutRecording
	lock
	msgbox SevenIsland_TanobyRuins_Text_StarGlintWakes, MSGBOX_DEFAULT
	waitse
	playmoncry SPECIES_JIRACHI, CRY_MODE_ENCOUNTER
	delay 40
	waitmoncry
	setvar VAR_LAST_TALKED, LOCALID_TANOBY_RUINS_JIRACHI
	seteventmon SPECIES_JIRACHI, 30
	setflag FLAG_SYS_SPECIAL_WILD_BATTLE
	special StartLegendaryBattle
	waitstate
	clearflag FLAG_SYS_SPECIAL_WILD_BATTLE
	specialvar VAR_RESULT, GetBattleOutcome
	goto_if_eq VAR_RESULT, B_OUTCOME_WON, SevenIsland_TanobyRuins_EventScript_DefeatedJirachi
	goto_if_eq VAR_RESULT, B_OUTCOME_RAN, SevenIsland_TanobyRuins_EventScript_RanFromJirachi
	goto_if_eq VAR_RESULT, B_OUTCOME_PLAYER_TELEPORTED, SevenIsland_TanobyRuins_EventScript_RanFromJirachi
	release
	end

SevenIsland_TanobyRuins_EventScript_DefeatedJirachi::
	setflag FLAG_JIRACHI_FLEW_AWAY
	setvar VAR_0x8004, SPECIES_JIRACHI
	goto EventScript_MonFlewAway
	end

SevenIsland_TanobyRuins_EventScript_RanFromJirachi::
	setflag FLAG_JIRACHI_FLEW_AWAY
	setvar VAR_0x8004, SPECIES_JIRACHI
	goto EventScript_MonFlewAway
	end

SevenIsland_TanobyRuins_EventScript_Inscription::
	msgbox SevenIsland_TanobyRuins_Text_Inscription, MSGBOX_SIGN
	end
