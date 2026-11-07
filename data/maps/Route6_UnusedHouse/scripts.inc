Route6_UnusedHouse_MapScripts::
	.byte 0

@ Mestre dos Golpes (POK-51): ensina os 15 golpes de tutor quantas vezes o jogador quiser, por ¥3.000 cada.
@ Usa o special original ChooseMonForMoveTutor, mas NÃO liga as flags de "já ensinou" dos tutores originais, e só
@ cobra se o golpe foi aprendido (VAR_RESULT = TRUE na volta da tela da equipe).
Route6_UnusedHouse_EventScript_Mestre::
	goto_if_questlog EventScript_ReleaseEnd
	lock
	faceplayer
	msgbox Route6_UnusedHouse_Text_BoasVindas
Route6_UnusedHouse_EventScript_MestreOferta::
	msgbox Route6_UnusedHouse_Text_QualTecnica
	special MestreGolpes_EscolherGolpe
	waitstate
	goto_if_eq VAR_RESULT, 0xFF, Route6_UnusedHouse_EventScript_MestreCancelou
	copyvar VAR_0x8005, VAR_RESULT
	checkmoney 3000
	goto_if_eq VAR_RESULT, FALSE, Route6_UnusedHouse_EventScript_MestreSemDinheiro
	msgbox Route6_UnusedHouse_Text_QualPokemon
	call EventScript_ChooseMoveTutorMon
	goto_if_eq VAR_RESULT, FALSE, Route6_UnusedHouse_EventScript_MestreDesistiu
	removemoney 3000
	msgbox Route6_UnusedHouse_Text_Ensinado
	msgbox Route6_UnusedHouse_Text_OutraTecnica, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, YES, Route6_UnusedHouse_EventScript_MestreOferta
	msgbox Route6_UnusedHouse_Text_Despedida
	release
	end

Route6_UnusedHouse_EventScript_MestreCancelou::
	msgbox Route6_UnusedHouse_Text_Cancelou
	release
	end

Route6_UnusedHouse_EventScript_MestreSemDinheiro::
	msgbox Route6_UnusedHouse_Text_SemDinheiro
	release
	end

Route6_UnusedHouse_EventScript_MestreDesistiu::
	msgbox Route6_UnusedHouse_Text_Desistiu
	release
	end
