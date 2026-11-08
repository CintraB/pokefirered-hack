Route19_UnusedHouse_MapScripts::
	.byte 0

@ Pescador da casa de praia (POK-51): como o irmão do Mestre da Pesca da Rota 12, mas para o Krabby.
@ Cada recorde novo rende 1 Pepita; o primeiro recorde batido também rende 1 Doce Raro
@ (FLAG_PESCADOR_PRIMEIRO_RECORDE, ligada só depois de o Doce Raro entrar na mochila).
Route19_UnusedHouse_EventScript_Pescador::
	goto_if_questlog EventScript_ReleaseEnd
	special QuestLog_CutRecording
	lock
	faceplayer
	setvar VAR_0x8004, SPECIES_KRABBY
	specialvar VAR_RESULT, DoesPlayerPartyContainSpecies
	goto_if_eq VAR_RESULT, FALSE, Route19_UnusedHouse_EventScript_SemKrabby
	special GetKrabbySizeRecordInfo
	msgbox Route19_UnusedHouse_Text_MostreOKrabby
	special ChoosePartyMon
	waitstate
	copyvar VAR_RESULT, VAR_0x8004
	goto_if_ge VAR_RESULT, PARTY_SIZE, Route19_UnusedHouse_EventScript_Desistiu
	special CompareKrabbySize
	goto_if_eq VAR_RESULT, 1, Route19_UnusedHouse_EventScript_NaoEKrabby
	goto_if_eq VAR_RESULT, 2, Route19_UnusedHouse_EventScript_NaoBateORecorde
	goto_if_eq VAR_RESULT, 3, Route19_UnusedHouse_EventScript_NovoRecorde
	goto_if_eq VAR_RESULT, 4, Route19_UnusedHouse_EventScript_Empate
	release
	end

Route19_UnusedHouse_EventScript_SemKrabby::
	goto_if_unset FLAG_PESCADOR_PRIMEIRO_RECORDE, Route19_UnusedHouse_EventScript_SemKrabbySemRecorde
	special GetKrabbySizeRecordInfo
	msgbox Route19_UnusedHouse_Text_SemKrabbyComRecorde
	release
	end

Route19_UnusedHouse_EventScript_SemKrabbySemRecorde::
	msgbox Route19_UnusedHouse_Text_SemKrabby
	release
	end

Route19_UnusedHouse_EventScript_Desistiu::
	release
	end

Route19_UnusedHouse_EventScript_NaoEKrabby::
	msgbox Route19_UnusedHouse_Text_NaoEKrabby
	release
	end

Route19_UnusedHouse_EventScript_NaoBateORecorde::
	msgbox Route19_UnusedHouse_Text_NaoBateORecorde
	release
	end

@ O tamanho empatado com o recorde padrão (ninguém ainda trouxe um Krabby) conta como recorde novo, como no Magikarp.
Route19_UnusedHouse_EventScript_Empate::
	goto_if_unset FLAG_PESCADOR_PRIMEIRO_RECORDE, Route19_UnusedHouse_EventScript_NovoRecorde
	msgbox Route19_UnusedHouse_Text_MesmoTamanho
	release
	end

Route19_UnusedHouse_EventScript_NovoRecorde::
	msgbox Route19_UnusedHouse_Text_NovoRecorde
	giveitem ITEM_NUGGET
	goto_if_eq VAR_RESULT, FALSE, Route19_UnusedHouse_EventScript_SemEspaco
	goto_if_unset FLAG_PESCADOR_PRIMEIRO_RECORDE, Route19_UnusedHouse_EventScript_PrimeiroRecorde
	msgbox Route19_UnusedHouse_Text_AteORecordeMaior
	release
	end

Route19_UnusedHouse_EventScript_PrimeiroRecorde::
	msgbox Route19_UnusedHouse_Text_PrimeiroRecorde
	giveitem ITEM_RARE_CANDY
	goto_if_eq VAR_RESULT, FALSE, Route19_UnusedHouse_EventScript_SemEspaco
	setflag FLAG_PESCADOR_PRIMEIRO_RECORDE
	msgbox Route19_UnusedHouse_Text_AteORecordeMaior
	release
	end

Route19_UnusedHouse_EventScript_SemEspaco::
	msgbox Route19_UnusedHouse_Text_SemEspaco
	release
	end
