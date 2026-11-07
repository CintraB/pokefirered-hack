@ POK-51: o 4º andar do prédio da Família Sombra (escuro: encontros com a Família a cada passo, sem Flash).
Route23_FamiliaSombra_4F_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, Route23_FamiliaSombra_4F_OnTransition
	.byte 0

Route23_FamiliaSombra_4F_OnTransition::
	setvar VAR_0x8004, 4
	special FamiliaSombra_PrepararAndar
	end

Route23_FamiliaSombra_4F_EventScript_PerolaGrande::
	finditem ITEM_BIG_PEARL
	end

Route23_FamiliaSombra_4F_EventScript_Pepita::
	finditem ITEM_NUGGET
	end

Route23_FamiliaSombra_4F_EventScript_Bilhete::
	lockall
	special FamiliaSombra_GetOcupacao
	goto_if_eq VAR_RESULT, 2, Route23_FamiliaSombra_4F_EventScript_Bilhete2
	goto_if_eq VAR_RESULT, 3, Route23_FamiliaSombra_4F_EventScript_Bilhete3
	goto_if_eq VAR_RESULT, 4, Route23_FamiliaSombra_4F_EventScript_Bilhete4
	msgbox Route23_FamiliaSombra_4F_Text_Bilhete1
	releaseall
	end

Route23_FamiliaSombra_4F_EventScript_Bilhete2::
	msgbox Route23_FamiliaSombra_4F_Text_Bilhete2
	releaseall
	end

Route23_FamiliaSombra_4F_EventScript_Bilhete3::
	msgbox Route23_FamiliaSombra_4F_Text_Bilhete3
	releaseall
	end

Route23_FamiliaSombra_4F_EventScript_Bilhete4::
	msgbox Route23_FamiliaSombra_4F_Text_Bilhete4
	releaseall
	end
