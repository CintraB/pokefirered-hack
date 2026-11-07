@ POK-51: o 1º andar do prédio da Família Sombra (o antigo Route23_UnusedHouse). Os scripts comuns aos andares
@ (capanga vencido, maletas de dinheiro) também ficam aqui.
Route23_UnusedHouse_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, Route23_UnusedHouse_OnTransition
	.byte 0

Route23_UnusedHouse_OnTransition::
	special FamiliaSombra_Atualizar
	setvar VAR_0x8004, 1
	special FamiliaSombra_PrepararAndar
	end

Route23_UnusedHouse_EventScript_Capanga1::
	trainerbattle_single TRAINER_FAMILIA_CAPANGA_1, FamiliaSombra_Text_CapangaIntro, FamiliaSombra_Text_CapangaDerrota, FamiliaSombra_EventScript_CapangaVencido
	end

Route23_UnusedHouse_EventScript_Capanga2::
	trainerbattle_single TRAINER_FAMILIA_CAPANGA_2, FamiliaSombra_Text_CapangaIntro, FamiliaSombra_Text_CapangaDerrota, FamiliaSombra_EventScript_CapangaVencido
	end

Route23_UnusedHouse_EventScript_Capanga3::
	trainerbattle_single TRAINER_FAMILIA_CAPANGA_3, FamiliaSombra_Text_CapangaIntro, FamiliaSombra_Text_CapangaDerrota, FamiliaSombra_EventScript_CapangaVencido
	end

Route23_UnusedHouse_EventScript_Perola::
	finditem ITEM_PEARL
	end

Route23_UnusedHouse_EventScript_Bilhete::
	lockall
	special FamiliaSombra_GetOcupacao
	goto_if_eq VAR_RESULT, 2, Route23_UnusedHouse_EventScript_Bilhete2
	goto_if_eq VAR_RESULT, 3, Route23_UnusedHouse_EventScript_Bilhete3
	goto_if_eq VAR_RESULT, 4, Route23_UnusedHouse_EventScript_Bilhete4
	msgbox Route23_UnusedHouse_Text_Bilhete1
	releaseall
	end

Route23_UnusedHouse_EventScript_Bilhete2::
	msgbox Route23_UnusedHouse_Text_Bilhete2
	releaseall
	end

Route23_UnusedHouse_EventScript_Bilhete3::
	msgbox Route23_UnusedHouse_Text_Bilhete3
	releaseall
	end

Route23_UnusedHouse_EventScript_Bilhete4::
	msgbox Route23_UnusedHouse_Text_Bilhete4
	releaseall
	end

@ ---- comuns aos andares -------------------------------------------------------------------------------------

@ Depois da vitória o capanga some do mapa (a flag do treinador é a flag do objeto) até a próxima ocupação.
FamiliaSombra_EventScript_CapangaVencido::
	removeobject VAR_LAST_TALKED
	releaseall
	end

FamiliaSombra_EventScript_Maleta2000::
	lock
	faceplayer
	goto_if_questlog EventScript_ReleaseEnd
	addmoney 2000
	removeobject VAR_LAST_TALKED
	playfanfare MUS_OBTAIN_ITEM
	message FamiliaSombra_Text_Maleta2000
	waitfanfare
	waitmessage
	waitbuttonpress
	release
	end

FamiliaSombra_EventScript_Maleta3000::
	lock
	faceplayer
	goto_if_questlog EventScript_ReleaseEnd
	addmoney 3000
	removeobject VAR_LAST_TALKED
	playfanfare MUS_OBTAIN_ITEM
	message FamiliaSombra_Text_Maleta3000
	waitfanfare
	waitmessage
	waitbuttonpress
	release
	end

FamiliaSombra_EventScript_Maleta5000::
	lock
	faceplayer
	goto_if_questlog EventScript_ReleaseEnd
	addmoney 5000
	removeobject VAR_LAST_TALKED
	playfanfare MUS_OBTAIN_ITEM
	message FamiliaSombra_Text_Maleta5000
	waitfanfare
	waitmessage
	waitbuttonpress
	release
	end

FamiliaSombra_EventScript_Maleta10000::
	lock
	faceplayer
	goto_if_questlog EventScript_ReleaseEnd
	addmoney 10000
	removeobject VAR_LAST_TALKED
	playfanfare MUS_OBTAIN_ITEM
	message FamiliaSombra_Text_Maleta10000
	waitfanfare
	waitmessage
	waitbuttonpress
	release
	end
