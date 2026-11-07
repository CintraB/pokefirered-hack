Route23_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, Route23_OnTransition
	map_script MAP_SCRIPT_ON_LOAD, Route23_OnLoad
	map_script MAP_SCRIPT_ON_FRAME_TABLE, Route23_OnFrame
	.byte 0

@ POK-54: com a Família encerrada (o 4º chefe caiu) a polícia lacra o prédio. A Oficial Jenny, 2 policiais e o Growlithe
@ e o Arcanine ficam na porta (FLAG_TEMP_2 os esconde nos outros estados). Ao sair do prédio pela 1ª vez depois do fim a
@ Jenny vem ao jogador (VAR_TEMP_4 = 1), entrega os chefes apreendidos e oferece o dossiê.
Route23_OnFrame::
	map_script_2 VAR_TEMP_4, 1, Route23_EventScript_CenaPolicia
	.2byte 0

@ POK-51: antes da 8ª insígnia a porta do prédio da Família Sombra fica trancada.
Route23_OnLoad::
	@ CONTINUE de um save em pé na rota só roda o ON_LOAD: atualiza o estado aqui também (idempotente)
	special FamiliaSombra_Atualizar
	special FamiliaSombra_GetEstado
	call_if_eq VAR_RESULT, FAMILIA_ESTADO_FECHADO, Route23_EventScript_TrancarPortaFamilia
	call_if_eq VAR_RESULT, FAMILIA_ESTADO_ATIVA, Route23_EventScript_ArmarPedagio
	call_if_eq VAR_RESULT, FAMILIA_ESTADO_ENCERRADA, Route23_EventScript_LacrarPortaFamilia
	end

Route23_EventScript_TrancarPortaFamilia::
	setmetatile 4, 149, METATILE_IndigoPlateau_FamiliaPortaTrancada, TRUE
	return

@ A porta com as faixas amarelas cruzadas: ladrilhos de verdade, sem comportamento de porta
Route23_EventScript_LacrarPortaFamilia::
	setmetatile 4, 149, METATILE_IndigoPlateau_FamiliaPortaLacrada, TRUE
	return

Route23_EventScript_PortaFamilia::
	lockall
	special FamiliaSombra_GetEstado
	goto_if_eq VAR_RESULT, FAMILIA_ESTADO_ENCERRADA, Route23_EventScript_PortaFamiliaLacrada
	goto_if_ne VAR_RESULT, FAMILIA_ESTADO_FECHADO, Route23_EventScript_PortaFamiliaAberta
	msgbox Route23_Text_PortaFamiliaTrancada
Route23_EventScript_PortaFamiliaAberta::
	releaseall
	end

Route23_EventScript_PortaFamiliaLacrada::
	msgbox Route23_Text_PortaFamiliaLacrada
	releaseall
	end

Route23_OnTransition::
	special FamiliaSombra_Atualizar
	special FamiliaSombra_GetEstado
	call_if_ne VAR_RESULT, FAMILIA_ESTADO_ATIVA, Route23_EventScript_EsconderCobrador
	call_if_eq VAR_RESULT, FAMILIA_ESTADO_ATIVA, Route23_EventScript_ArmarPedagio
	call_if_ne VAR_RESULT, FAMILIA_ESTADO_ENCERRADA, Route23_EventScript_EsconderPolicia
	call_if_eq VAR_RESULT, FAMILIA_ESTADO_ENCERRADA, Route23_EventScript_ChecarCenaPolicia
	clearflag FLAG_HIDE_VICTORY_ROAD_3F_BOULDER
	setflag FLAG_HIDE_VICTORY_ROAD_2F_BOULDER
	setvar VAR_MAP_SCENE_VICTORY_ROAD_1F, 0
	setvar VAR_MAP_SCENE_VICTORY_ROAD_2F_BOULDER1, 0
	setvar VAR_MAP_SCENE_VICTORY_ROAD_2F_BOULDER2, 0
	setvar VAR_MAP_SCENE_VICTORY_ROAD_3F, 0
	end

@ O cobrador do pedágio só existe com chefe ativo: fora disso a flag temporária (zerada a cada mapa) o esconde.
Route23_EventScript_EsconderCobrador::
	setflag FLAG_TEMP_1
	return

@ A polícia só existe com a Família encerrada: fora disso a flag temporária (zerada a cada mapa) a esconde.
Route23_EventScript_EsconderPolicia::
	setflag FLAG_TEMP_2
	return

@ A cena da Jenny: só na 1ª vez e só saindo do prédio (o jogador chega na porta, (4, 149), ou logo à frente dela).
Route23_EventScript_ChecarCenaPolicia::
	goto_if_set FLAG_FAMILIA_POLICIA_CENA, Route23_EventScript_ChecarCenaPoliciaFim
	getplayerxy VAR_0x8004, VAR_0x8005
	goto_if_ne VAR_0x8004, 4, Route23_EventScript_ChecarCenaPoliciaFim
	goto_if_lt VAR_0x8005, 149, Route23_EventScript_ChecarCenaPoliciaFim
	goto_if_gt VAR_0x8005, 150, Route23_EventScript_ChecarCenaPoliciaFim
	setvar VAR_TEMP_4, 1
Route23_EventScript_ChecarCenaPoliciaFim::
	return

@ POK-51: o pedágio da Família Sombra. Os gatilhos ficam nos dois lados do corredor (y 147 = quem sobe, y 145 =
@ quem desce) e disparam enquanto VAR_TEMP_3 == 1 (armado só com chefe ativo, a cada carga do mapa). O script
@ desarma na hora: um gatilho de chão que não muda a variável dispara a cada quadro e prende o jogador no tile.
@ "Voltar depois" arma de novo depois do passo para trás. VAR_TEMP_2 guarda o lado.
@ Só com o cobrador presente: o ON_LOAD roda depois do ON_TRANSITION e o chefe pode ter voltado no meio da visita,
@ quando o Persian já foi escondido (FLAG_TEMP_1); armar assim cobraria sem ninguém no corredor.
Route23_EventScript_ArmarPedagio::
	goto_if_set FLAG_TEMP_1, Route23_EventScript_ArmarPedagioSemCobrador
	setvar VAR_TEMP_3, 1
Route23_EventScript_ArmarPedagioSemCobrador::
	return

Route23_EventScript_PedagioSul::
	setvar VAR_TEMP_2, 0
	goto Route23_EventScript_Pedagio
	end

Route23_EventScript_PedagioNorte::
	setvar VAR_TEMP_2, 1
	goto Route23_EventScript_Pedagio
	end

Route23_EventScript_Pedagio::
	lockall
	setvar VAR_TEMP_3, 0
	goto_if_questlog EventScript_ReleaseEnd
	goto_if_set FLAG_FAMILIA_PEDAGIO_PAGO, Route23_EventScript_PedagioNada
	call_if_eq VAR_TEMP_2, 0, Route23_EventScript_PersianOlhaSul
	call_if_eq VAR_TEMP_2, 1, Route23_EventScript_PersianOlhaNorte
	applymovement LOCALID_FAMILIA_PEDAGIO_COBRADOR, Common_Movement_ExclamationMark
	waitmovement 0
	msgbox Route23_Text_PedagioCobra, MSGBOX_DEFAULT
	checkmoney FAMILIA_PEDAGIO
	goto_if_eq VAR_RESULT, FALSE, Route23_EventScript_PedagioSemDinheiro
	showmoneybox 0, 0
	msgbox Route23_Text_PedagioPagar, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, Route23_EventScript_PedagioRecusou
	removemoney FAMILIA_PEDAGIO
	updatemoneybox
	playse SE_SHOP
	waitse
	hidemoneybox
	setflag FLAG_FAMILIA_PEDAGIO_PAGO
	msgbox Route23_Text_PedagioPago, MSGBOX_DEFAULT
	releaseall
	end

Route23_EventScript_PedagioNada::
	releaseall
	end

Route23_EventScript_PersianOlhaSul::
	applymovement LOCALID_FAMILIA_PEDAGIO_COBRADOR, Route23_Movement_PersianOlhaSul
	waitmovement 0
	return

Route23_EventScript_PersianOlhaNorte::
	applymovement LOCALID_FAMILIA_PEDAGIO_COBRADOR, Route23_Movement_PersianOlhaNorte
	waitmovement 0
	return

Route23_EventScript_PedagioRecusou::
	hidemoneybox
	msgbox Route23_Text_PedagioRecusou, MSGBOX_DEFAULT
	goto Route23_EventScript_PedagioMenu
	end

Route23_EventScript_PedagioSemDinheiro::
	msgbox Route23_Text_PedagioSemDinheiro, MSGBOX_DEFAULT
	goto Route23_EventScript_PedagioMenu
	end

@ "Voltar depois" (0, ou B) ou "Passar à força" (1)
Route23_EventScript_PedagioMenu::
	message Route23_Text_PedagioEscolha
	waitmessage
	multichoice 17, 6, MULTICHOICE_PEDAGIO, FALSE
	goto_if_eq VAR_RESULT, 1, Route23_EventScript_PedagioForca
	closemessage
	msgbox Route23_Text_PedagioVoltar, MSGBOX_DEFAULT
	goto_if_eq VAR_TEMP_2, 1, Route23_EventScript_PedagioRecuaNorte
	applymovement LOCALID_PLAYER, Route23_Movement_JogadorRecuaSul
	waitmovement 0
	setvar VAR_TEMP_3, 1
	releaseall
	end

Route23_EventScript_PedagioRecuaNorte::
	applymovement LOCALID_PLAYER, Route23_Movement_JogadorRecuaNorte
	waitmovement 0
	setvar VAR_TEMP_3, 1
	releaseall
	end

@ Passar à força: 2 lutas seguidas contra membros sorteados do plantel da ocupação. Perder = desmaio normal.
Route23_EventScript_PedagioForca::
	closemessage
	msgbox Route23_Text_PedagioForca, MSGBOX_DEFAULT
	special FamiliaSombra_SortearPedagio
	setvar VAR_LAST_TALKED, LOCALID_FAMILIA_PEDAGIO_COBRADOR
	trainerbattle_no_intro TRAINER_FAMILIA_PEDAGIO_1, Route23_Text_PedagioDerrota1
	trainerbattle_no_intro TRAINER_FAMILIA_PEDAGIO_2, Route23_Text_PedagioDerrota2
	special FamiliaSombra_PedagioVencido
	msgbox Route23_Text_PedagioLivre, MSGBOX_DEFAULT
	releaseall
	end

Route23_EventScript_PedagioCobrador::
	lock
	faceplayer
	goto_if_questlog EventScript_ReleaseEnd
	goto_if_set FLAG_FAMILIA_PEDAGIO_PAGO, Route23_EventScript_PedagioCobradorPago
	msgbox Route23_Text_PedagioCobra, MSGBOX_DEFAULT
	release
	end

Route23_EventScript_PedagioCobradorPago::
	msgbox Route23_Text_PedagioJaPagou, MSGBOX_DEFAULT
	release
	end

Route23_Movement_PersianOlhaSul:
	face_down
	step_end

Route23_Movement_PersianOlhaNorte:
	face_up
	step_end

Route23_Movement_JogadorRecuaSul:
	lock_facing_direction
	walk_down
	unlock_facing_direction
	step_end

Route23_Movement_JogadorRecuaNorte:
	lock_facing_direction
	walk_up
	unlock_facing_direction
	step_end

Route23_EventScript_CascadeBadgeGuard::
	lock
	faceplayer
	setvar VAR_TEMP_1, 2
	bufferstdstring STR_VAR_1, STDSTRING_CASCADE_BADGE
	goto Route23_EventScript_BadgeGuard
	end

Route23_EventScript_ThunderBadgeGuard::
	lock
	faceplayer
	setvar VAR_TEMP_1, 3
	bufferstdstring STR_VAR_1, STDSTRING_THUNDER_BADGE
	goto Route23_EventScript_BadgeGuard
	end

Route23_EventScript_RainbowBadgeGuard::
	lock
	faceplayer
	setvar VAR_TEMP_1, 4
	bufferstdstring STR_VAR_1, STDSTRING_RAINBOW_BADGE
	goto Route23_EventScript_BadgeGuard
	end

Route23_EventScript_SoulBadgeGuard::
	lock
	faceplayer
	setvar VAR_TEMP_1, 5
	bufferstdstring STR_VAR_1, STDSTRING_SOUL_BADGE
	goto Route23_EventScript_BadgeGuard
	end

Route23_EventScript_MarshBadgeGuard::
	lock
	faceplayer
	setvar VAR_TEMP_1, 6
	bufferstdstring STR_VAR_1, STDSTRING_MARSH_BADGE
	goto Route23_EventScript_BadgeGuard
	end

Route23_EventScript_VolcanoBadgeGuard::
	lock
	faceplayer
	setvar VAR_TEMP_1, 7
	bufferstdstring STR_VAR_1, STDSTRING_VOLCANO_BADGE
	goto Route23_EventScript_BadgeGuard
	end

Route23_EventScript_EarthBadgeGuard::
	lock
	faceplayer
	setvar VAR_TEMP_1, 8
	bufferstdstring STR_VAR_1, STDSTRING_EARTH_BADGE
	goto Route23_EventScript_BadgeGuard
	end

Route23_EventScript_CascadeBadgeGuardTrigger::
	lockall
	setvar VAR_TEMP_1, 2
	setvar VAR_0x8009, LOCALID_CASCADE_BADGE_GUARD
	bufferstdstring STR_VAR_1, STDSTRING_CASCADE_BADGE
	goto Route23_EventScript_BadgeGuardTrigger
	end

Route23_EventScript_ThunderBadgeGuardTrigger::
	lockall
	setvar VAR_TEMP_1, 3
	setvar VAR_0x8009, LOCALID_THUNDER_BADGE_GUARD
	bufferstdstring STR_VAR_1, STDSTRING_THUNDER_BADGE
	goto Route23_EventScript_BadgeGuardTrigger
	end

Route23_EventScript_RainbowBadgeGuardTrigger::
	lockall
	setvar VAR_TEMP_1, 4
	setvar VAR_0x8009, LOCALID_RAINBOW_BADGE_GUARD
	bufferstdstring STR_VAR_1, STDSTRING_RAINBOW_BADGE
	goto Route23_EventScript_BadgeGuardTrigger
	end

Route23_EventScript_SoulBadgeGuardTrigger::
	lockall
	setvar VAR_TEMP_1, 5
	setvar VAR_0x8009, LOCALID_SOUL_BADGE_GUARD
	bufferstdstring STR_VAR_1, STDSTRING_SOUL_BADGE
	goto Route23_EventScript_BadgeGuardTrigger
	end

Route23_EventScript_MarshBadgeGuardTrigger::
	lockall
	setvar VAR_TEMP_1, 6
	setvar VAR_0x8009, LOCALID_MARSH_BADGE_GUARD
	bufferstdstring STR_VAR_1, STDSTRING_MARSH_BADGE
	goto Route23_EventScript_BadgeGuardTrigger
	end

Route23_EventScript_VolcanoBadgeGuardTrigger::
	lockall
	setvar VAR_TEMP_1, 7
	setvar VAR_0x8009, LOCALID_VOLCANO_BADGE_GUARD
	bufferstdstring STR_VAR_1, STDSTRING_VOLCANO_BADGE
	goto Route23_EventScript_BadgeGuardTrigger
	end

Route23_EventScript_EarthBadgeGuardTrigger::
	lockall
	setvar VAR_TEMP_1, 8
	setvar VAR_0x8009, LOCALID_EARTH_BADGE_GUARD
	bufferstdstring STR_VAR_1, STDSTRING_EARTH_BADGE
	goto Route23_EventScript_BadgeGuardTrigger
	end

Route23_EventScript_VictoryRoadGateSign::
	msgbox Route23_Text_VictoryRoadGateSign, MSGBOX_SIGN
	end

@ ---- POK-54: a polícia na porta e a Oficial Jenny ---------------------------------------------------------------
@ A cena (ON_FRAME): a Jenny vem do posto (6, 150) até o jogador, que sai do prédio na porta (4, 149) e só tem a saída
@ (4, 150) -> (4, 151) entre os policiais. Por isso, no fim ela volta ao posto e libera o caminho.
@ A flag da cena só liga no fim (sair do mapa no meio refaz tudo; nada se entrega duas vezes: cada entrega tem a flag).
Route23_EventScript_CenaPolicia::
	setvar VAR_TEMP_4, 0
	goto_if_questlog EventScript_ReleaseEnd
	lockall
	applymovement LOCALID_FAMILIA_POLICIA_JENNY, Route23_Movement_JennyAteOJogador
	applymovement LOCALID_PLAYER, Route23_Movement_JogadorOlhaBaixo
	waitmovement 0
	msgbox Route23_Text_JennyCaso, MSGBOX_DEFAULT
	call Route23_EventScript_JennyEntregas
	call Route23_EventScript_JennyOferece
	setflag FLAG_FAMILIA_POLICIA_CENA
	applymovement LOCALID_FAMILIA_POLICIA_JENNY, Route23_Movement_JennyVolta
	waitmovement 0
	releaseall
	end

Route23_Movement_JennyAteOJogador:
	emote_exclamation_mark
	walk_down
	walk_left
	walk_left
	walk_up
	step_end

Route23_Movement_JennyVolta:
	walk_down
	walk_right
	walk_right
	walk_up
	face_down
	step_end

Route23_Movement_JogadorOlhaBaixo:
	face_down
	step_end

@ Entrega, um por vez, os chefes apreendidos que faltam (Garchomp, depois Darkrai). Sem espaço no time e no PC nada se
@ perde: a flag da entrega não liga, a Jenny avisa e oferece de novo na próxima conversa.
Route23_EventScript_JennyEntregas::
	special FamiliaSombra_ApreendidoPendente
	goto_if_eq VAR_RESULT, 0, Route23_EventScript_JennyEntregasFim
	copyvar VAR_0x8008, VAR_RESULT
	call_if_eq VAR_0x8008, 3, Route23_EventScript_JennyApreendido3
	call_if_eq VAR_0x8008, 4, Route23_EventScript_JennyApreendido4
	copyvar VAR_0x8004, VAR_0x8008
	special FamiliaSombra_EntregarApreendido
	bufferspeciesname STR_VAR_1, VAR_0x8005
	goto_if_eq VAR_RESULT, MON_CANT_GIVE, Route23_EventScript_JennyEntregaSemEspaco
	goto_if_eq VAR_RESULT, MON_GIVEN_TO_PC, Route23_EventScript_JennyEntregouAoPC
	playfanfare MUS_OBTAIN_ITEM
	message Route23_Text_JennyRecebeu
	waitmessage
	waitfanfare
	closemessage
	goto Route23_EventScript_JennyEntregas
Route23_EventScript_JennyEntregasFim::
	return

Route23_EventScript_JennyApreendido3::
	msgbox Route23_Text_JennyApreendido3, MSGBOX_DEFAULT
	return

Route23_EventScript_JennyApreendido4::
	msgbox Route23_Text_JennyApreendido4, MSGBOX_DEFAULT
	return

Route23_EventScript_JennyEntregouAoPC::
	playfanfare MUS_OBTAIN_ITEM
	message Route23_Text_JennyEntregouAoPC
	waitmessage
	waitfanfare
	closemessage
	goto Route23_EventScript_JennyEntregas

Route23_EventScript_JennyEntregaSemEspaco::
	msgbox Route23_Text_JennySemEspaco, MSGBOX_DEFAULT
	return

@ "Quer ouvir a história completa?": o dossiê em tela cheia, quantas vezes quiser
Route23_EventScript_JennyOferece::
	msgbox Route23_Text_JennyQuerOuvir, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, Route23_EventScript_JennyNaoQuer
	fadescreen FADE_TO_BLACK
	special Dossie_Abrir
	waitstate
	return

Route23_EventScript_JennyNaoQuer::
	msgbox Route23_Text_JennyObrigada, MSGBOX_DEFAULT
	return

@ Falar com a Jenny: a entrega que ficou pendente e depois a mesma pergunta, para sempre
Route23_EventScript_PoliciaJenny::
	lock
	faceplayer
	goto_if_questlog EventScript_ReleaseEnd
	msgbox Route23_Text_JennyDeNovo, MSGBOX_DEFAULT
	call Route23_EventScript_JennyEntregas
	call Route23_EventScript_JennyOferece
	release
	end

Route23_EventScript_PoliciaPolicial1::
	msgbox Route23_Text_Policial1, MSGBOX_NPC
	end

Route23_EventScript_PoliciaPolicial2::
	msgbox Route23_Text_Policial2, MSGBOX_NPC
	end

Route23_EventScript_PoliciaGrowlithe::
	lock
	faceplayer
	goto_if_questlog EventScript_ReleaseEnd
	playmoncry SPECIES_GROWLITHE, CRY_MODE_NORMAL
	msgbox Route23_Text_Growlithe, MSGBOX_DEFAULT
	waitmoncry
	release
	end

Route23_EventScript_PoliciaArcanine::
	lock
	faceplayer
	goto_if_questlog EventScript_ReleaseEnd
	playmoncry SPECIES_ARCANINE, CRY_MODE_NORMAL
	msgbox Route23_Text_Arcanine, MSGBOX_DEFAULT
	waitmoncry
	release
	end
