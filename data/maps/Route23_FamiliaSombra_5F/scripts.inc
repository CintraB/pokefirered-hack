@ POK-51: o 5º andar do prédio da Família Sombra (escuro: encontros com a Família a cada passo, sem Flash).
Route23_FamiliaSombra_5F_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, Route23_FamiliaSombra_5F_OnTransition
	.byte 0

Route23_FamiliaSombra_5F_OnTransition::
	setvar VAR_0x8004, 5
	special FamiliaSombra_PrepararAndar
	end

Route23_FamiliaSombra_5F_EventScript_Pepitas::
	finditem ITEM_NUGGET, 2
	end

Route23_FamiliaSombra_5F_EventScript_Bilhete::
	lockall
	special FamiliaSombra_GetOcupacao
	goto_if_eq VAR_RESULT, 2, Route23_FamiliaSombra_5F_EventScript_Bilhete2
	msgbox Route23_FamiliaSombra_5F_Text_Bilhete1
	releaseall
	end

Route23_FamiliaSombra_5F_EventScript_Bilhete2::
	msgbox Route23_FamiliaSombra_5F_Text_Bilhete2
	releaseall
	end
