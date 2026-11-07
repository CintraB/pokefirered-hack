@ POK-51: o 6º andar, a sala do chefe. O chefe (VAR_OBJ_GFX_ID_0) fica atrás da mesa e os gêmeos guarda-costas
@ (VAR_OBJ_GFX_ID_1) um de cada lado. A cena começa ao sair da escada (gatilhos com VAR_TEMP_1 = 0) ou falando com
@ qualquer um dos três: o chefe fala, a dupla dos gêmeos (só com 2 Pokémon aptos), o chefe fala de novo e luta sozinho
@ (capturável). Vencido ou capturado, ele deixa cair a rosa; perder ou fugir, ele continua ali.
Route23_FamiliaSombra_6F_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, Route23_FamiliaSombra_6F_OnTransition
	map_script MAP_SCRIPT_ON_LOAD, Route23_FamiliaSombra_6F_OnLoad
	.byte 0

@ O quadro atrás do chefe (7..9, 1..2) é o retrato em preto e branco do chefe da ocupação (VAR_FAMILIA_OCUPACAO).
@ Sem chefe (entre ocupações) a variável continua com a última: fica o retrato do último chefe. Os 4 chefes têm retrato
@ (QUADROS em tools/familia_sombra/predio.py, rótulos em metatile_labels.h); o layout já traz o do Dom.
Route23_FamiliaSombra_6F_OnLoad::
	special FamiliaSombra_GetOcupacao
	copyvar VAR_0x8008, VAR_RESULT
	call_if_eq VAR_0x8008, 1, Route23_FamiliaSombra_6F_EventScript_QuadroDom
	call_if_eq VAR_0x8008, 2, Route23_FamiliaSombra_6F_EventScript_QuadroCobrador
	call_if_eq VAR_0x8008, 3, Route23_FamiliaSombra_6F_EventScript_QuadroMercenario
	call_if_eq VAR_0x8008, 4, Route23_FamiliaSombra_6F_EventScript_QuadroPesadelo
	end

Route23_FamiliaSombra_6F_EventScript_QuadroDom::
	setmetatile 7, 1, METATILE_FamiliaSombra_QuadroDom_0_0, TRUE
	setmetatile 8, 1, METATILE_FamiliaSombra_QuadroDom_1_0, TRUE
	setmetatile 9, 1, METATILE_FamiliaSombra_QuadroDom_2_0, TRUE
	setmetatile 7, 2, METATILE_FamiliaSombra_QuadroDom_0_1, TRUE
	setmetatile 8, 2, METATILE_FamiliaSombra_QuadroDom_1_1, TRUE
	setmetatile 9, 2, METATILE_FamiliaSombra_QuadroDom_2_1, TRUE
	return

Route23_FamiliaSombra_6F_EventScript_QuadroCobrador::
	setmetatile 7, 1, METATILE_FamiliaSombra_QuadroCobrador_0_0, TRUE
	setmetatile 8, 1, METATILE_FamiliaSombra_QuadroCobrador_1_0, TRUE
	setmetatile 9, 1, METATILE_FamiliaSombra_QuadroCobrador_2_0, TRUE
	setmetatile 7, 2, METATILE_FamiliaSombra_QuadroCobrador_0_1, TRUE
	setmetatile 8, 2, METATILE_FamiliaSombra_QuadroCobrador_1_1, TRUE
	setmetatile 9, 2, METATILE_FamiliaSombra_QuadroCobrador_2_1, TRUE
	return

Route23_FamiliaSombra_6F_EventScript_QuadroMercenario::
	setmetatile 7, 1, METATILE_FamiliaSombra_QuadroMercenario_0_0, TRUE
	setmetatile 8, 1, METATILE_FamiliaSombra_QuadroMercenario_1_0, TRUE
	setmetatile 9, 1, METATILE_FamiliaSombra_QuadroMercenario_2_0, TRUE
	setmetatile 7, 2, METATILE_FamiliaSombra_QuadroMercenario_0_1, TRUE
	setmetatile 8, 2, METATILE_FamiliaSombra_QuadroMercenario_1_1, TRUE
	setmetatile 9, 2, METATILE_FamiliaSombra_QuadroMercenario_2_1, TRUE
	return

Route23_FamiliaSombra_6F_EventScript_QuadroPesadelo::
	setmetatile 7, 1, METATILE_FamiliaSombra_QuadroPesadelo_0_0, TRUE
	setmetatile 8, 1, METATILE_FamiliaSombra_QuadroPesadelo_1_0, TRUE
	setmetatile 9, 1, METATILE_FamiliaSombra_QuadroPesadelo_2_0, TRUE
	setmetatile 7, 2, METATILE_FamiliaSombra_QuadroPesadelo_0_1, TRUE
	setmetatile 8, 2, METATILE_FamiliaSombra_QuadroPesadelo_1_1, TRUE
	setmetatile 9, 2, METATILE_FamiliaSombra_QuadroPesadelo_2_1, TRUE
	return

Route23_FamiliaSombra_6F_OnTransition::
	setvar VAR_0x8004, 6
	special FamiliaSombra_PrepararAndar
	special FamiliaSombra_GetEstado
	call_if_ne VAR_RESULT, FAMILIA_ESTADO_ATIVA, Route23_FamiliaSombra_6F_EventScript_SalaVazia
	end

Route23_FamiliaSombra_6F_EventScript_SalaVazia::
	setflag FLAG_TEMP_1
	setvar VAR_TEMP_1, 1
	return

Route23_FamiliaSombra_6F_EventScript_Cena::
	goto_if_questlog EventScript_ReleaseEnd
	lockall
	setvar VAR_TEMP_1, 1
	playbgm MUS_ENCOUNTER_ROCKET, 0
	special FamiliaSombra_GetOcupacao
	copyvar VAR_0x8008, VAR_RESULT
	call_if_eq VAR_0x8008, 1, Route23_FamiliaSombra_6F_EventScript_FalaDom
	call_if_eq VAR_0x8008, 2, Route23_FamiliaSombra_6F_EventScript_FalaCobrador
	call_if_eq VAR_0x8008, 3, Route23_FamiliaSombra_6F_EventScript_FalaMercenario
	call_if_eq VAR_0x8008, 4, Route23_FamiliaSombra_6F_EventScript_FalaPesadelo
	goto_if_set FLAG_FAMILIA_GEMEOS_VENCIDOS, Route23_FamiliaSombra_6F_EventScript_Chefe
	@ time de 1 Pokémon: a dupla é recusada pelo trainerbattle; a música de encontro do chefe não pode ficar presa
	special HasEnoughMonsForDoubleBattle
	call_if_ne VAR_RESULT, PLAYER_HAS_TWO_USABLE_MONS, Route23_FamiliaSombra_6F_EventScript_RestaurarMusica
	goto_if_eq VAR_0x8008, 2, Route23_FamiliaSombra_6F_EventScript_GemeosRhydon
	goto_if_eq VAR_0x8008, 3, Route23_FamiliaSombra_6F_EventScript_GemeosGligar
	goto_if_eq VAR_0x8008, 4, Route23_FamiliaSombra_6F_EventScript_GemeosDusclops
	@ com o id do gêmeo A: a dupla vira para o jogador e marca o objeto certo (a cena também vem dos gatilhos)
	trainerbattle TRAINER_BATTLE_CONTINUE_SCRIPT_DOUBLE, TRAINER_FAMILIA_GEMEOS, LOCALID_FAMILIA_6F_GEMEO_A, Route23_FamiliaSombra_6F_Text_GemeosMachamp, Route23_FamiliaSombra_6F_Text_GemeosDerrota, Route23_FamiliaSombra_6F_Text_SoEmDupla, Route23_FamiliaSombra_6F_EventScript_GemeosVencidos
	end

Route23_FamiliaSombra_6F_EventScript_GemeosRhydon::
	trainerbattle TRAINER_BATTLE_CONTINUE_SCRIPT_DOUBLE, TRAINER_FAMILIA_GEMEOS, LOCALID_FAMILIA_6F_GEMEO_A, Route23_FamiliaSombra_6F_Text_GemeosRhydon, Route23_FamiliaSombra_6F_Text_GemeosDerrota, Route23_FamiliaSombra_6F_Text_SoEmDupla, Route23_FamiliaSombra_6F_EventScript_GemeosVencidos
	end

Route23_FamiliaSombra_6F_EventScript_GemeosGligar::
	trainerbattle TRAINER_BATTLE_CONTINUE_SCRIPT_DOUBLE, TRAINER_FAMILIA_GEMEOS, LOCALID_FAMILIA_6F_GEMEO_A, Route23_FamiliaSombra_6F_Text_GemeosGligar, Route23_FamiliaSombra_6F_Text_GemeosDerrota, Route23_FamiliaSombra_6F_Text_SoEmDupla, Route23_FamiliaSombra_6F_EventScript_GemeosVencidos
	end

Route23_FamiliaSombra_6F_EventScript_GemeosDusclops::
	trainerbattle TRAINER_BATTLE_CONTINUE_SCRIPT_DOUBLE, TRAINER_FAMILIA_GEMEOS, LOCALID_FAMILIA_6F_GEMEO_A, Route23_FamiliaSombra_6F_Text_GemeosDusclops, Route23_FamiliaSombra_6F_Text_GemeosDerrota, Route23_FamiliaSombra_6F_Text_SoEmDupla, Route23_FamiliaSombra_6F_EventScript_GemeosVencidos
	end

Route23_FamiliaSombra_6F_EventScript_RestaurarMusica::
	fadedefaultbgm
	return

@ Com os gêmeos já vencidos (voltou depois de perder ou fugir do chefe) ninguém mais manda os guarda-costas falarem.
Route23_FamiliaSombra_6F_EventScript_FalaDom::
	goto_if_set FLAG_FAMILIA_GEMEOS_VENCIDOS, Route23_FamiliaSombra_6F_EventScript_FalaDomSemGemeos
	msgbox Route23_FamiliaSombra_6F_Text_Dom
	return

Route23_FamiliaSombra_6F_EventScript_FalaDomSemGemeos::
	msgbox Route23_FamiliaSombra_6F_Text_DomSemGemeos
	return

Route23_FamiliaSombra_6F_EventScript_FalaCobrador::
	goto_if_set FLAG_FAMILIA_GEMEOS_VENCIDOS, Route23_FamiliaSombra_6F_EventScript_FalaCobradorSemGemeos
	msgbox Route23_FamiliaSombra_6F_Text_Cobrador
	return

Route23_FamiliaSombra_6F_EventScript_FalaCobradorSemGemeos::
	msgbox Route23_FamiliaSombra_6F_Text_CobradorSemGemeos
	return

Route23_FamiliaSombra_6F_EventScript_FalaMercenario::
	goto_if_set FLAG_FAMILIA_GEMEOS_VENCIDOS, Route23_FamiliaSombra_6F_EventScript_FalaMercenarioSemGemeos
	msgbox Route23_FamiliaSombra_6F_Text_Mercenario
	return

Route23_FamiliaSombra_6F_EventScript_FalaMercenarioSemGemeos::
	msgbox Route23_FamiliaSombra_6F_Text_MercenarioSemGemeos
	return

Route23_FamiliaSombra_6F_EventScript_FalaPesadelo::
	goto_if_set FLAG_FAMILIA_GEMEOS_VENCIDOS, Route23_FamiliaSombra_6F_EventScript_FalaPesadeloSemGemeos
	msgbox Route23_FamiliaSombra_6F_Text_Pesadelo
	return

Route23_FamiliaSombra_6F_EventScript_FalaPesadeloSemGemeos::
	msgbox Route23_FamiliaSombra_6F_Text_PesadeloSemGemeos
	return

@ Os gêmeos vencidos não voltam nesta ocupação (FamiliaSombra_Repovoar os traz de volta na próxima).
Route23_FamiliaSombra_6F_EventScript_GemeosVencidos::
	lockall
	setflag FLAG_FAMILIA_GEMEOS_VENCIDOS
	removeobject LOCALID_FAMILIA_6F_GEMEO_A
	removeobject LOCALID_FAMILIA_6F_GEMEO_B
	goto Route23_FamiliaSombra_6F_EventScript_Chefe
	end

Route23_FamiliaSombra_6F_EventScript_Chefe::
	special FamiliaSombra_GetOcupacao
	copyvar VAR_0x8008, VAR_RESULT
	call_if_eq VAR_0x8008, 1, Route23_FamiliaSombra_6F_EventScript_DesafioDom
	call_if_eq VAR_0x8008, 2, Route23_FamiliaSombra_6F_EventScript_DesafioCobrador
	call_if_eq VAR_0x8008, 3, Route23_FamiliaSombra_6F_EventScript_DesafioMercenario
	call_if_eq VAR_0x8008, 4, Route23_FamiliaSombra_6F_EventScript_DesafioPesadelo
	special QuestLog_CutRecording
	special FamiliaSombra_IniciarChefe
	waitstate
	special FamiliaSombra_GetOcupacao
	copyvar VAR_0x8008, VAR_RESULT
	specialvar VAR_RESULT, GetBattleOutcome
	goto_if_eq VAR_RESULT, B_OUTCOME_WON, Route23_FamiliaSombra_6F_EventScript_ChefeCaiu
	goto_if_eq VAR_RESULT, B_OUTCOME_CAUGHT, Route23_FamiliaSombra_6F_EventScript_ChefeCaiu
	call_if_eq VAR_0x8008, 1, Route23_FamiliaSombra_6F_EventScript_FugaDom
	call_if_eq VAR_0x8008, 2, Route23_FamiliaSombra_6F_EventScript_FugaCobrador
	call_if_eq VAR_0x8008, 3, Route23_FamiliaSombra_6F_EventScript_FugaMercenario
	call_if_eq VAR_0x8008, 4, Route23_FamiliaSombra_6F_EventScript_FugaPesadelo
	releaseall
	end

Route23_FamiliaSombra_6F_EventScript_DesafioDom::
	msgbox Route23_FamiliaSombra_6F_Text_DesafioDom
	return

Route23_FamiliaSombra_6F_EventScript_DesafioCobrador::
	msgbox Route23_FamiliaSombra_6F_Text_DesafioCobrador
	return

Route23_FamiliaSombra_6F_EventScript_DesafioMercenario::
	msgbox Route23_FamiliaSombra_6F_Text_DesafioMercenario
	return

Route23_FamiliaSombra_6F_EventScript_DesafioPesadelo::
	msgbox Route23_FamiliaSombra_6F_Text_DesafioPesadelo
	return

Route23_FamiliaSombra_6F_EventScript_FugaDom::
	msgbox Route23_FamiliaSombra_6F_Text_FugaDom
	return

Route23_FamiliaSombra_6F_EventScript_FugaCobrador::
	msgbox Route23_FamiliaSombra_6F_Text_FugaCobrador
	return

Route23_FamiliaSombra_6F_EventScript_FugaMercenario::
	msgbox Route23_FamiliaSombra_6F_Text_FugaMercenario
	return

Route23_FamiliaSombra_6F_EventScript_FugaPesadelo::
	msgbox Route23_FamiliaSombra_6F_Text_FugaPesadelo
	return

@ Vencido ou capturado: a queda conta o período sem chefe, a rosa da ocupação vai para a bolsa e a sala esvazia.
@ Com o bolso de itens-chave cheio (BAG_KEYITEMS_COUNT) a rosa não se perde: a flag FLAG_FAMILIA_ROSA_n já foi ligada
@ por FamiliaSombra_ChefeCaiu e é ela que acende a redoma da Sala de Troféus (Ilha Sete); só o giveitem fica de fora.
Route23_FamiliaSombra_6F_EventScript_ChefeCaiu::
	special FamiliaSombra_ChefeCaiu
	fadescreen FADE_TO_BLACK
	removeobject LOCALID_FAMILIA_6F_CHEFE
	fadescreen FADE_FROM_BLACK
	goto_if_eq VAR_0x8008, 2, Route23_FamiliaSombra_6F_EventScript_RosaDourada
	goto_if_eq VAR_0x8008, 3, Route23_FamiliaSombra_6F_EventScript_RosaAzul
	goto_if_eq VAR_0x8008, 4, Route23_FamiliaSombra_6F_EventScript_RosaNegra
	msgbox Route23_FamiliaSombra_6F_Text_RosaDom
	checkitemspace ITEM_ROSA_VERMELHA
	goto_if_eq VAR_RESULT, FALSE, Route23_FamiliaSombra_6F_EventScript_RosaVermelhaParaSala
	giveitem ITEM_ROSA_VERMELHA
	releaseall
	end

Route23_FamiliaSombra_6F_EventScript_RosaVermelhaParaSala::
	msgbox Route23_FamiliaSombra_6F_Text_BolsaCheiaRosaVermelha
	releaseall
	end

Route23_FamiliaSombra_6F_EventScript_RosaDourada::
	msgbox Route23_FamiliaSombra_6F_Text_RosaCobrador
	checkitemspace ITEM_ROSA_DOURADA
	goto_if_eq VAR_RESULT, FALSE, Route23_FamiliaSombra_6F_EventScript_RosaDouradaParaSala
	giveitem ITEM_ROSA_DOURADA
	releaseall
	end

Route23_FamiliaSombra_6F_EventScript_RosaDouradaParaSala::
	msgbox Route23_FamiliaSombra_6F_Text_BolsaCheiaRosaDourada
	releaseall
	end

Route23_FamiliaSombra_6F_EventScript_RosaAzul::
	msgbox Route23_FamiliaSombra_6F_Text_RosaMercenario
	checkitemspace ITEM_ROSA_AZUL
	goto_if_eq VAR_RESULT, FALSE, Route23_FamiliaSombra_6F_EventScript_RosaAzulParaSala
	giveitem ITEM_ROSA_AZUL
	releaseall
	end

Route23_FamiliaSombra_6F_EventScript_RosaAzulParaSala::
	msgbox Route23_FamiliaSombra_6F_Text_BolsaCheiaRosaAzul
	releaseall
	end

Route23_FamiliaSombra_6F_EventScript_RosaNegra::
	msgbox Route23_FamiliaSombra_6F_Text_RosaPesadelo
	checkitemspace ITEM_ROSA_NEGRA
	goto_if_eq VAR_RESULT, FALSE, Route23_FamiliaSombra_6F_EventScript_RosaNegraParaSala
	giveitem ITEM_ROSA_NEGRA
	releaseall
	end

Route23_FamiliaSombra_6F_EventScript_RosaNegraParaSala::
	msgbox Route23_FamiliaSombra_6F_Text_BolsaCheiaRosaNegra
	releaseall
	end

@ O bilhete da mesa: o livro-caixa do chefe ativo; sem chefe, o aviso da próxima ocupação (depois da 1, o Cobrador; depois
@ da 2, o de fora; depois da 3, a sombra por trás do Dom). Depois da 4 a Família acabou (ENCERRADA): o bilhete diz que a polícia fecha a casa.
Route23_FamiliaSombra_6F_EventScript_Bilhete::
	lockall
	special FamiliaSombra_GetEstado
	goto_if_ne VAR_RESULT, FAMILIA_ESTADO_ATIVA, Route23_FamiliaSombra_6F_EventScript_BilheteSemChefe
	special FamiliaSombra_GetOcupacao
	goto_if_eq VAR_RESULT, 2, Route23_FamiliaSombra_6F_EventScript_Bilhete2
	goto_if_eq VAR_RESULT, 3, Route23_FamiliaSombra_6F_EventScript_Bilhete3
	goto_if_eq VAR_RESULT, 4, Route23_FamiliaSombra_6F_EventScript_Bilhete4
	msgbox Route23_FamiliaSombra_6F_Text_Bilhete1
	releaseall
	end

Route23_FamiliaSombra_6F_EventScript_Bilhete2::
	msgbox Route23_FamiliaSombra_6F_Text_Bilhete2
	releaseall
	end

Route23_FamiliaSombra_6F_EventScript_Bilhete3::
	msgbox Route23_FamiliaSombra_6F_Text_Bilhete3
	releaseall
	end

Route23_FamiliaSombra_6F_EventScript_Bilhete4::
	msgbox Route23_FamiliaSombra_6F_Text_Bilhete4
	releaseall
	end

Route23_FamiliaSombra_6F_EventScript_BilheteSemChefe::
	special FamiliaSombra_GetEstado
	goto_if_eq VAR_RESULT, FAMILIA_ESTADO_ENCERRADA, Route23_FamiliaSombra_6F_EventScript_BilheteEncerrada
	special FamiliaSombra_GetOcupacao
	goto_if_eq VAR_RESULT, 2, Route23_FamiliaSombra_6F_EventScript_BilheteDeFora
	goto_if_ge VAR_RESULT, 3, Route23_FamiliaSombra_6F_EventScript_BilheteSombra
	msgbox Route23_FamiliaSombra_6F_Text_BilheteReforcos
	releaseall
	end

Route23_FamiliaSombra_6F_EventScript_BilheteDeFora::
	msgbox Route23_FamiliaSombra_6F_Text_BilheteDeFora
	releaseall
	end

Route23_FamiliaSombra_6F_EventScript_BilheteSombra::
	msgbox Route23_FamiliaSombra_6F_Text_BilheteSombra
	releaseall
	end

@ O 4º chefe caiu (POK-54): ninguém vai buscar ninguém, a polícia fecha a casa
Route23_FamiliaSombra_6F_EventScript_BilheteEncerrada::
	msgbox Route23_FamiliaSombra_6F_Text_BilheteEncerrada
	releaseall
	end
