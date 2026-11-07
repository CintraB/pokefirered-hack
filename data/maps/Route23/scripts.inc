Route23_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, Route23_OnTransition
	map_script MAP_SCRIPT_ON_LOAD, Route23_OnLoad
	.byte 0

@ POK-51: antes da 8ª insígnia a porta do prédio da Família Sombra fica trancada.
Route23_OnLoad::
	@ CONTINUE de um save em pé na rota só roda o ON_LOAD: atualiza o estado aqui também (idempotente)
	special FamiliaSombra_Atualizar
	special FamiliaSombra_GetEstado
	call_if_eq VAR_RESULT, FAMILIA_ESTADO_FECHADO, Route23_EventScript_TrancarPortaFamilia
	call_if_eq VAR_RESULT, FAMILIA_ESTADO_ATIVA, Route23_EventScript_ArmarPedagio
	end

Route23_EventScript_TrancarPortaFamilia::
	setmetatile 4, 149, METATILE_IndigoPlateau_FamiliaPortaTrancada, TRUE
	return

Route23_EventScript_PortaFamilia::
	lockall
	special FamiliaSombra_GetEstado
	goto_if_ne VAR_RESULT, FAMILIA_ESTADO_FECHADO, Route23_EventScript_PortaFamiliaAberta
	msgbox Route23_Text_PortaFamiliaTrancada
Route23_EventScript_PortaFamiliaAberta::
	releaseall
	end

Route23_OnTransition::
	special FamiliaSombra_Atualizar
	special FamiliaSombra_GetEstado
	call_if_ne VAR_RESULT, FAMILIA_ESTADO_ATIVA, Route23_EventScript_EsconderCobrador
	call_if_eq VAR_RESULT, FAMILIA_ESTADO_ATIVA, Route23_EventScript_ArmarPedagio
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
