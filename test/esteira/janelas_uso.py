"""Janela dos textos C que aparecem longe de onde nascem: o `src/strings.c` (1 300+ textos de
dezenas de telas), as palavras do Easy Chat, os pedaços de batalha e os textos soltos de outros
`.c`. A janela de cada um sai de **onde ele é usado**: a varredura indexa toda referência ao
rótulo em `src/**` (e nos scripts de `data/`) com o contexto do uso:

  call:<Função>   o rótulo é argumento de `Função(...)` (ex.: `call:DisplayPartyMenuMessage`);
  table:<Tabela>  o rótulo está no inicializador da variável `Tabela` (ex.: `table:sCursorOptions`);
  code            outro uso dentro de função (atribuição, `return`, comparação);
  script:<macro>  uso num script (`msgbox gText_X`).

Cada uso casa com a primeira `UsageRule` (arquivo e contexto, padrões fnmatch). O texto tem de
caber em **todas** as janelas onde é usado: a checagem mede contra cada regra que casou. Texto
sem nenhum uso no código vira regra explícita "sem uso" (texto morto).
"""

import fnmatch
import re
from collections import defaultdict
from typing import NamedTuple

DIALOG_PX = 26 * 8
_DIALOG = ("diálogo padrão: sStandardTextBox_WindowTemplates .width = 26 tiles (src/new_menu_helpers.c:40), "
           "texto em x = 0 (src/new_menu_helpers.c:411)")


class UsageRule(NamedTuple):
    file: str                  # arquivo que usa o rótulo (fnmatch)
    context: str               # contexto do uso (fnmatch): "call:X", "table:X", "code", "script:X"
    px: int | None
    source: str
    font: str = "normal"
    lines: int | None = None
    chars: int | None = None
    label: str = "*"           # só estes rótulos (fnmatch), quando a mesma chamada/tabela mistura janelas


def U(file: str, context: str, px: int | None, source: str, **kw) -> UsageRule:
    return UsageRule(file, context, px, source, **kw)


# A primeira que casar com o uso vale. Linhas citadas conferidas em 18/10 (hack-switch 3a8d861f5).
USAGE_RULES: list[UsageRule] = [
    # -- menu Start e salvar --
    U("src/start_menu.c", "table:sStartMenuActionTable", 7 * 8 - 8,
      "rótulo do menu Start: janela de 7 tiles (src/new_menu_helpers.c:670), texto em x = 8 (src/start_menu.c:338)"),
    U("src/start_menu.c", "call:AddTextPrinterParameterized3", 60 - 2,
      "estatísticas do salvamento: nome em x = 2 e valor em x = 60, FONT_SMALL (src/start_menu.c:1036-1052)",
      font="small"),
    U("src/start_menu.c", "call:StringExpandPlaceholders", 10 * 8 - 4,
      "estatísticas da Safari: sSafariZoneStatsWindowTemplate 10 tiles (src/start_menu.c:129-133), x = 4 (src/start_menu.c:279)"),
    U("src/start_menu.c", "*", DIALOG_PX, _DIALOG + "; mensagens de salvar na janela 0 (src/start_menu.c:691, :979)"),
    # -- opções --
    U("src/option_menu.c", "table:sOptionMenuItemsNames", 0x82 - 8,
      "nome da opção em x = 8 (src/option_menu.c:563) até a coluna de valores em x = 0x82 (src/option_menu.c:473)"),
    U("src/option_menu.c", "table:s*Options", 0x46,
      "valor da opção: coluna em x = 0x82 limpa com 0x46 px (src/option_menu.c:473-475)"),
    U("src/option_menu.c", "call:StringCopy", 0x46 - 8,
      "valor da opção \"tipo de moldura\" + número: coluna de 0x46 px (src/option_menu.c:473-475, :496-499)"),
    U("src/option_menu.c", "call:*PickSwitchCancel*", 0xE4, "controles: FONT_SMALL alinhado à direita em 0xE4 "
      "(src/option_menu.c:319-321)", font="small"),
    U("src/option_menu.c", "call:AddTextPrinterParameterized3", 0xE4, "controles: FONT_SMALL alinhado à direita "
      "em 0xE4 (src/option_menu.c:319-321)", font="small"),
    U("src/option_menu.c", "call:GetStringWidth", 0xE4, "controles: FONT_SMALL alinhado à direita em 0xE4 "
      "(src/option_menu.c:319-321)", font="small"),
    U("src/option_menu.c", "*", 26 * 8 - 8, "título das opções: janela de 26 tiles (src/option_menu.c:72-76), "
      "x = 8 (src/option_menu.c:527)"),
    # -- grupo de Pokémon --
    U("src/data/party_menu.h", "table:sCursorOptions", 10 * 8 - 8,
      "menu de ações do grupo: 10 tiles (src/party_menu.c:2540), texto em x = 8 (src/party_menu.c:2562)"),
    U("src/data/party_menu.h", "table:sDescriptionStringTable", 64,
      "descrição na caixa do Pokémon (APTO, NÃO PODE...): retângulo de 64 px (src/data/party_menu.h:50), "
      "impresso em src/party_menu.c:2455"),
    U("src/data/party_menu.h", "table:sFieldMoveDescriptionTable", 18 * 8 - 3,
      "descrição de golpe de campo: sFieldMoveDescriptionWindowTemplate 18 tiles (src/data/party_menu.h:541-546), "
      "x = 3 (src/party_menu.c:2640)"),
    U("src/data/party_menu.h", "table:sActionStringTable", 16 * 8,
      "\"o que fazer\" do grupo: sDoWhatWithMonMsgWindowTemplate/sDoWhatWithMailMsgWindowTemplate 16 tiles "
      "(src/data/party_menu.h:431-436, :453-458), x = 0 (src/party_menu.c:2479-2486, :2507)",
      label="gText_DoWhatWith[PM]*"),
    U("src/data/party_menu.h", "table:sActionStringTable", 19 * 8,
      "\"o que fazer com o item\": sDoWhatWithItemMsgWindowTemplate 19 tiles (src/data/party_menu.h:442-447), x = 0",
      label="gText_DoWhatWithItem"),
    U("src/data/party_menu.h", "table:sActionStringTable", 15 * 8,
      "\"qual golpe\": sWhichMoveMsgWindowTemplate 15 tiles (src/data/party_menu.h:464-469), x = 0",
      label="gText_*WhichMove*"),
    U("src/data/party_menu.h", "table:sActionStringTable", 21 * 8,
      "mensagem do grupo: sDefaultPartyMsgWindowTemplate 21 tiles (src/data/party_menu.h:420-425), x = 0 "
      "(src/party_menu.c:2494, :2507)"),
    U("src/party_menu.c", "call:GetStringWidth", 6 * 8,
      "botões Cancelar/OK: 6 tiles (src/data/party_menu.h:387-392, :409-414), centralizados"),
    U("src/party_menu.c", "call:AddTextPrinterParameterized[34]", 6 * 8,
      "botões Cancelar/OK: 6 tiles (src/data/party_menu.h:387-392, :409-414), centralizados"),
    U("src/party_menu.c", "call:PartyMenu_Oak_PrintText", 26 * 8,
      "voz do Carvalho no 1º combate: sWindowTemplate_FirstBattleOakVoiceover 26 tiles (src/data/party_menu.h:530-535)"),
    U("src/party_menu.c", "*", 28 * 8,
      "mensagem do grupo: janela 6 de 28 tiles (src/data/party_menu.h:180-184), x = 0 (src/party_menu.c:2573)"),
    U("src/data/party_menu.h", "*", 28 * 8,
      "mensagem do grupo: janela 6 de 28 tiles (src/data/party_menu.h:180-184), x = 0 (src/party_menu.c:2573)"),
    U("src/fldeff_softboiled.c", "*", 28 * 8,
      "mensagem do grupo: janela 6 de 28 tiles (src/data/party_menu.h:180-184), x = 0 (src/party_menu.c:2573)"),
    # -- resumo --
    U("src/pokemon_summary_screen.c", "call:PokeSum_PrintPageName", 12 * 8 - 4,
      "nome da página: [POKESUM_WIN_PAGE_NAME] 13 tiles (src/pokemon_summary_screen.c:728-732), x = 4 "
      "(src/pokemon_summary_screen.c:2557); os pontos de página começam na coluna 12"),
    U("src/pokemon_summary_screen.c", "call:PokeSum_PrintControlsString", 0x54,
      "controles do resumo: FONT_SMALL alinhado à direita em 0x54 (src/pokemon_summary_screen.c:2568-2570)",
      font="small"),
    U("src/pokemon_summary_screen.c", "*", 28 * 8,
      "página INFO/memória do Treinador: [POKESUM_WIN_INFO_4] 28 tiles (src/pokemon_summary_screen.c:799-803), "
      "x = 0 (src/pokemon_summary_screen.c:3294)"),
    # -- bolsa, loja, PC de itens, estojo de MT, bolsa de frutas --
    U("src/item_menu.c", "table:sPocketNames", 9 * 8,
      "nome do bolso: janela de 9 tiles (src/bag.c:37-41), centralizado"),
    U("src/item_menu.c", "table:*", 7 * 8 - 8,
      "menu de contexto da bolsa: janelas de 7 tiles (src/bag.c:157-185), texto em x = 8"),
    U("src/item_menu.c", "*", 25 * 8,
      "mensagem/descrição da bolsa: sDefaultBagWindowsStd[1] 25 tiles (src/bag.c:33), x = 0 (src/item_menu.c:756)"),
    U("src/bag.c", "*", 9 * 8, "título \"Guardar item\": janela de 9 tiles (src/bag.c:37-41)"),
    U("src/berry_pouch.c", "table:sContextMenuActions", 7 * 8 - 8,
      "menu de contexto da bolsa de frutas: janelas de 7 tiles (src/berry_pouch.c:326-353), texto em x = 8"),
    U("src/berry_pouch.c", "call:BerryPouchPrint", 9 * 8, "título: janela de 9 tiles (src/berry_pouch.c:234-238)"),
    U("src/berry_pouch.c", "call:GetStringWidth", 9 * 8, "título: janela de 9 tiles (src/berry_pouch.c:234-238)"),
    U("src/berry_pouch.c", "*", 26 * 8,
      "mensagem da bolsa de frutas: janela de 26 tiles (src/berry_pouch.c:286-290), x = 0"),
    U("src/tm_case.c", "table:*", 7 * 8 - 8,
      "menu do estojo de MT: janelas de 7 tiles (src/tm_case.c:340-353), texto em x = 8"),
    U("src/tm_case.c", "call:TMCase_Print", 10 * 8, "título: WIN_TITLE de 10 tiles (src/tm_case.c:272-276)"),
    U("src/tm_case.c", "call:*StringWidth*", 10 * 8, "título: WIN_TITLE de 10 tiles (src/tm_case.c:272-276)"),
    U("src/tm_case.c", "call:AddTextPrinterParameterized3", 10 * 8, "título: WIN_TITLE de 10 tiles (src/tm_case.c:272-276)"),
    U("src/tm_case.c", "*", 26 * 8, "mensagem do estojo: WIN_MESSAGE de 26 tiles (src/tm_case.c:299-303), x = 0"),
    U("src/shop.c", "table:sShopMenuActions_BuySellQuit", 12 * 8 - 8,
      "menu da loja: janela de 12 tiles (src/shop.c:154-158), texto em x = 8 (src/shop.c:216)"),
    U("src/shop.c", "table:*", 12 * 8 - 8,
      "menu da loja: janela de 12 tiles (src/shop.c:154-158), texto em x = 8 (src/shop.c:216)"),
    U("src/shop.c", "*", DIALOG_PX, _DIALOG + "; mensagens da loja (BuyMenuDisplayMessage)"),
    U("src/money.c", "*", 8 * 8 - 2, "caixa de dinheiro: 8 tiles (src/money.c:123)"),
    U("src/coins.c", "*", 8 * 8 - 2, "caixa de moedas: 8 tiles (src/coins.c:83)"),
    U("src/berry_powder.c", "*", 8 * 8 - 2, "caixa de pó de frutas: 8 tiles (src/berry_powder.c:120)"),
    U("src/item_pc.c", "table:sItemPcSubmenuOptions", 7 * 8 - 8,
      "submenu do PC de itens: janela de 7 tiles (src/item_pc.c:163-167), texto em x = 8"),
    U("src/item_pc.c", "table:*", 19 * 8 - 9,
      "lista do PC de itens: 19 tiles (src/item_pc.c:131-135), item_X = 9 (src/item_pc.c:495)"),
    U("src/item_pc.c", "*", 26 * 8, "mensagem do PC de itens: janela de 26 tiles (src/item_pc.c:171-175), x = 0"),
    U("src/player_pc.c", "table:sMenuActions_*", 13 * 8 - 8,
      "menus do PC do jogador: janelas de 13-14 tiles (src/player_pc.c:112-136), texto em x = 8"),
    U("src/player_pc.c", "table:sItemStorageActionDescriptionPtrs", DIALOG_PX, _DIALOG),
    U("src/player_pc.c", "call:*", DIALOG_PX, _DIALOG + "; título da caixa de correio centralizado em 80 px "
      "(src/player_pc.c:458)"),
    U("src/player_pc.c", "*", DIALOG_PX, _DIALOG),
    U("src/mailbox_pc.c", "*", DIALOG_PX, _DIALOG + "; \"Cancelar\" da caixa de correio"),
    U("src/item_use.c", "*", DIALOG_PX, _DIALOG + "; ou a mensagem da bolsa (25 tiles, mais larga)"),
    U("src/item.c", "*", DIALOG_PX, _DIALOG),
    # -- PC de Pokémon --
    U("src/pokemon_storage_system_menu.c", "table:sMainMenuTexts", DIALOG_PX,
      _DIALOG + "; descrição da opção do PC na janela 0 (src/pokemon_storage_system_menu.c:253)",
      label="*Description"),
    U("src/pokemon_storage_system_menu.c", "table:*", 17 * 8 - 8,
      "menu do PC: janela de 17 tiles (src/pokemon_storage_system_menu.c:376-380), texto em x = 8 "
      "(src/pokemon_storage_system_menu.c:391)"),
    U("src/pokemon_storage_system_menu.c", "*", DIALOG_PX, _DIALOG + "; descrição na janela 0 "
      "(src/pokemon_storage_system_menu.c:253)"),
    U("src/pokemon_storage_system_tasks.c", "*", 18 * 8,
      "mensagem do PC: janela de 18 tiles (src/pokemon_storage_system_tasks.c:199-203), x = 0 "
      "(src/pokemon_storage_system_tasks.c:2588)"),
    U("src/pokemon_storage_system_data.c", "*", 9 * 8 - 8,
      "menus do PC (Mover, Marcar, papéis de parede...): janela de 9 tiles "
      "(src/pokemon_storage_system_tasks.c:191-195), texto em x = 8"),
    U("src/pokemon_storage_system_misc.c", "*", DIALOG_PX, _DIALOG),
    # -- Pokédex --
    U("src/pokedex_screen.c", "table:sListMenuItems_*DexModeSelect", 20 * 8 - 12,
      "menu da Pokédex: sWindowTemplate_ModeSelect 20 tiles (src/pokedex_screen.c:290-294), item_X = 12 "
      "(src/pokedex_screen.c:350)"),
    U("src/pokedex_screen.c", "table:sDexCategoryNamePtrs", 30 * 8,
      "título da categoria na barra de 30 tiles (src/pokedex_screen.c:246-250)"),
    U("src/pokedex_screen.c", "call:DexScreen_PrintStringWithAlignment", 30 * 8,
      "título da Pokédex: janela 0 de 30 tiles (src/pokedex_screen.c:246-250), centralizado em 240 "
      "(src/pokedex_screen.c:3443-3451)"),
    U("src/pokedex_screen.c", "call:DexScreen_PrintControlInfo", 236,
      "controles da Pokédex: FONT_SMALL alinhado à direita em 236 (src/pokedex_screen.c:2299)", font="small"),
    U("src/pokedex_screen.c", "*", 8 * 8,
      "rótulos da Pokédex (Vistos, Pegos, Alt., Peso, Área...): janelas de 8 tiles (src/pokedex_screen.c:578-602) "
      "em FONT_SMALL", font="small"),
    # -- mapa da região --
    U("src/region_map.c", "table:sDungeonInfo", 25 * 8 - 2,
      "descrição da área: WIN_MAP_PREVIEW 25 tiles (src/region_map.c:486-491), x = 2 (src/region_map.c:2064)"),
    U("src/region_map.c", "call:PrintTopBarText*", 5 * 8,
      "barra de cima: WIN_TOPBAR_LEFT/RIGHT 5 tiles (src/region_map.c:496-510), FONT_SMALL "
      "(src/region_map.c:3845, :3855)", font="small"),
    U("src/region_map.c", "*", 15 * 8 - 12,
      "nome no mapa: WIN_DUNGEON_NAME 15 tiles (src/region_map.c:476-481), x = 12 (src/region_map.c:1481)"),
    U("src/map_name_popup.c", "*", 112, "aviso de nome do mapa: maxWidth = 112 (src/map_name_popup.c:195)"),
    U("src/strings.c", "table:gText_DayNight_PeriodName", 13 * 8 - 4 - 35,
      "período no relógio do menu Start (Hack 7): sClockWindowTemplate 13 tiles (src/start_menu.c:143-147), "
      "x = 4 (src/start_menu.c:308), depois de \"00:00 \" (35 px, src/day_night.c:96-104); buffer "
      "DAY_NIGHT_CLOCK_TEXT_SIZE 20 (include/day_night.h:23) menos 6", chars=13),
    U("src/strings.c", "table:gText_DayNight_PeriodStart", 112,
      "aviso de período (Hack 7): ShowFieldMessagePopup (src/day_night.c:271) usa o aviso de mapa, "
      "maxWidth = 112 e mapName[25] (src/map_name_popup.c:194-195)", chars=24),
    U("src/day_night.c", "*", 112, "aviso de período: ShowFieldMessagePopup na janela do aviso de mapa "
      "(src/map_name_popup.c:195)"),
    # -- Presente Misterioso / e-Reader --
    U("src/mystery_gift_menu.c", "table:sListMenuItems_CardsOrNews", 28 * 8 - 9,
      "menu de 3 opções: a janela cresce com o texto, ((largura + 9) / 8 + 2) tiles até 30 "
      "(src/mystery_gift_menu.c:630-638)"),
    U("src/mystery_gift_menu.c", "table:sListMenuItems_WirelessOrFriend", 28 * 8 - 9,
      "menu de 3 opções: a janela cresce com o texto, ((largura + 9) / 8 + 2) tiles até 30 "
      "(src/mystery_gift_menu.c:630-638)"),
    U("src/mystery_gift_menu.c", "table:sListMenuItems_*", 7 * 8 - 8,
      "lista Receber/Enviar/Jogar fora: sWindowTemplate_GiftSelect_* 7 tiles (src/mystery_gift_menu.c:167-191), "
      "item_X = 8 (src/mystery_gift_menu.c:262)"),
    U("src/mystery_gift_menu.c", "call:AddTextPrinterParameterized4", 30 * 8 - 2,
      "barra de cima: 30 tiles (src/mystery_gift_menu.c:89-93), x = 2 (src/mystery_gift_menu.c:474)"),
    U("src/mystery_gift_menu.c", "*", 28 * 8,
      "mensagem do Presente Misterioso: janela 1 de 28 tiles (src/mystery_gift_menu.c:97-101), x = 0 "
      "(src/mystery_gift_menu.c:528)"),
    U("src/ereader_screen.c", "*", 28 * 8,
      "mensagem do e-Reader: janela 1 do Presente Misterioso, 28 tiles (src/mystery_gift_menu.c:97-101)"),
    U("src/mystery_event_script.c", "*", DIALOG_PX, _DIALOG),
    # -- multiescolha de script --
    U("src/script_menu.c", "*", 28 * 8 - 8,
      "multiescolha: a janela cresce com o texto e se desloca para caber em 28 tiles "
      "(src/script_menu.c:736-738), texto em x = 8 (src/script_menu.c:745)"),
    U("src/field_specials.c", "table:sFloorNamePointers", 56,
      "andar do elevador: alinhado à direita em x = 56 (src/field_specials.c:1108)"),
    U("src/field_specials.c", "call:AddTextPrinterParameterized", 7 * 8,
      "\"Agora no\" do elevador: janela de 7 tiles (src/field_specials.c:727-731), x = 0 "
      "(src/field_specials.c:1105)"),
    U("src/field_specials.c", "table:*", 28 * 8 - 8,
      "listas de script (ListMenu): janela montada pelo script, até 28 tiles com item_X = 8 "
      "(src/field_specials.c:1358, :1380)"),
    U("src/field_specials.c", "*", DIALOG_PX, _DIALOG + "; vai para {STR_VAR_n} de um diálogo"),
    U("src/field_screen_effect.c", "call:PrintWhiteOutRecoveryMessage", 30 * 8 - 2,
      "texto depois de desmaiar: sWindowTemplate_WhiteoutText 30 tiles (src/field_screen_effect.c:21-26), "
      "x = 2 (src/field_screen_effect.c:414, :421)"),
    U("src/field_screen_effect.c", "*", DIALOG_PX, _DIALOG),
    U("src/field_player_avatar.c", "*", DIALOG_PX, _DIALOG + "; pesca (src/field_player_avatar.c:1848)"),
    U("src/itemfinder.c", "*", DIALOG_PX, _DIALOG),
    U("src/trainer_fan_club.c", "*", DIALOG_PX, _DIALOG),
    U("src/daycare.c", "table:sLevelMenuItems", 17 * 8 - 8,
      "lista de Pokémon da creche: janela de 17 tiles (src/daycare.c:90-94), texto em x = 8"),
    U("src/daycare.c", "*", DIALOG_PX, _DIALOG),
    U("src/fame_checker.c", "*", DIALOG_PX,
      "caixa do Fame Checker: FCWINDOWID_MSGBOX 26 tiles (src/fame_checker.c:494-498), x = 0"),
    U("src/learn_move.c", "table:*", 10 * 8 - 8,
      "lista do tutor: janela de 10 tiles (src/learn_move.c:309-313)"),
    U("src/learn_move.c", "*", 26 * 8, "mensagem do tutor: janela de 26 tiles (src/learn_move.c:318-322), x = 0"),
    # -- telas de abertura, título, nome --
    U("src/main_menu.c", "call:AddTextPrinterParameterized3", 62 - 2,
      "menu principal: rótulo em x = 2 até o valor em x = 62 (src/main_menu.c:623-675)",
      label="gText_[PTB][loai]*"),   # Player, Pokedex, Time, Badges
    U("src/main_menu.c", "*", 24 * 8,
      "menu principal: janelas de 24 tiles (src/main_menu.c:75-115), x = 0/2 (src/main_menu.c:603)"),
    U("src/oak_speech.c", "call:AddTextPrinterParameterized3", 9 * 8 - 8,
      "menino/menina: [WIN_INTRO_BOYGIRL] 9 tiles (src/oak_speech.c:298-304), x = 8 (src/oak_speech.c:1298)"),
    U("src/oak_speech.c", "*", 236, "barra de cima (TopBarWindowPrintString): FONT_SMALL alinhado à direita "
      "em 236 (src/menu.c:187-196)", font="small"),
    U("src/naming_screen.c", "table:title", 30 * 8, "título da tela de nome: WIN_BANNER 30 tiles "
      "(src/naming_screen.c:364-368)"),
    U("src/naming_screen.c", "*", 30 * 8, "barra da tela de nome: WIN_BANNER 30 tiles (src/naming_screen.c:364-368)"),
    U("src/clear_save_data_screen.c", "*", DIALOG_PX, _DIALOG),
    U("src/save_failed_screen.c", "*", DIALOG_PX, _DIALOG),
    U("src/hall_of_fame.c", "call:AddTextPrinterParameterized4", 17 * 8 - 4,
      "dados do Treinador no Hall da Fama: janela de 17 tiles (src/hall_of_fame.c:126-130), x = 4 "
      "(src/hall_of_fame.c:1089)"),
    U("src/hall_of_fame.c", "call:TopBarWindowPrint*", 236, "barra de cima (TopBarWindowPrintString): "
      "FONT_SMALL alinhado à direita em 236 (src/menu.c:187-196)", font="small"),
    U("src/hall_of_fame.c", "*", 0xD0, "Hall da Fama: janela 0 do diálogo (src/hall_of_fame.c:1202), "
      "texto centralizado em 0xD0 (src/hall_of_fame.c:986)"),
    U("src/diploma.c", "*", 30 * 8, "diploma: centralizado em 240 px (src/diploma.c:269-273)"),
    U("src/credits.c", "*", 30 * 8, "créditos: janela de 30 tiles (src/credits.c:456-460), centralizados"),
    U("src/help_system*.c", "*", 26 * 8, "ajuda: bitmap de 26 tiles (src/help_system_util.c:265)"),
    # -- troca, cartão, link, minijogos --
    U("src/trade.c", "table:sMenuAction_*", 12 * 8 - 8,
      "menu da troca: janela de 12 tiles (src/trade.c:605-609)"),
    U("src/trade.c", "*", 22 * 8, "mensagem da troca: janela de 22 tiles (src/trade.c:597-601)"),
    U("src/trade_scene.c", "*", 26 * 8, "mensagem da cena de troca: sTradeMessageWindowTemplates 26 tiles "
      "(src/trade_scene.c:480-485), x = 0 (src/trade_scene.c:2814)"),
    U("src/evolution_scene.c", "*", 26 * 8, "mensagem da evolução na troca: DrawTextOnTradeWindow, 26 tiles "
      "(src/trade_scene.c:480-485, :2808-2814)"),
    U("src/trainer_card.c", "*", 27 * 8 - 16,
      "cartão de Treinador: janela de 27 tiles (src/trainer_card.c:235-239), textos a partir de x = 16"),
    U("src/battle_records.c", "*", 27 * 8, "recordes de batalha: janela de 27 tiles (src/battle_records.c:41-46)"),
    U("src/link.c", "*", 28 * 8 - 2, "erro de link: janelas da tela de erro, x = 2 (src/link.c:1488-1547)"),
    U("src/cable_club.c", "*", DIALOG_PX, _DIALOG),
    U("src/union_room_chat_display.c", "table:sMessageWindowInfo", 28 * 8,
      "mensagem do chat: janela de 21 tiles, ou 28 com widerBox (src/union_room_chat_display.c:991-1001); "
      "vale a larga"),
    U("src/union_room*.c", "*", DIALOG_PX, _DIALOG),
    U("src/data/union_room.h", "*", DIALOG_PX, _DIALOG),
    U("src/wireless_communication_status_screen.c", "*", 22 * 8,
      "status da comunicação sem fio: janela de 22 tiles (src/wireless_communication_status_screen.c:100-104)"),
    U("src/berry_crush.c", "*", 24 * 8,
      "Berry Crush: mensagens e resultados em janelas de 22-24 tiles (src/berry_crush.c:545-549)"),
    U("src/dodrio_berry_picking.c", "*", 28 * 8,
      "Dodrio Berry Picking: janelas de 28 tiles (src/dodrio_berry_picking.c:409-433)"),
    U("src/pokemon_jump.c", "*", 28 * 8, "Pokémon Jump: janela de 28 tiles (src/pokemon_jump.c:4494-4498)"),
    U("src/slot_machine.c", "*", 20 * 8 - 1, "caça-níquel: janela 0 de 20 tiles (src/slot_machine.c:796-801), "
      "x = 1 (src/slot_machine.c:2336)"),
    U("src/pokemon_special_anim_scene.c", "table:sLevelUpWindowStatNames", 56,
      "atributos ao subir de nível: nome em x = 0 e valor em x = 56 (src/pokemon_special_anim_scene.c:1518-1520)"),
    U("src/pokemon_special_anim_scene.c", "*", 28 * 8,
      "mensagem do uso de item: janela de 28 tiles (src/pokemon_special_anim_scene.c:86-90)"),
    # -- Easy Chat --
    U("src/data/easy_chat/*", "table:*", 13 * 8,
      "palavra do Easy Chat: colunas em x = 24 e x = 128, 13 tiles cada (src/easy_chat_3.c:1673)"),
    U("src/easy_chat.c", "*", 84,
      "nome de grupo do Easy Chat: colunas a cada 84 px (src/easy_chat_3.c:1587)"),
    U("src/easy_chat_2.c", "*", 28 * 8,
      "instruções do Easy Chat: janela de 28 tiles (src/easy_chat_3.c:259-263)"),
    U("src/easy_chat_3.c", "*", 22 * 8, "Easy Chat: janela de 22 tiles (src/easy_chat_3.c:250-254)"),
    # -- batalha --
    U("src/battle_message.c", "table:gTrainerTowerChallengeTypeTexts", DIALOG_PX, _DIALOG),
    U("src/battle_*.c", "*", 28 * 8 - 2, "mensagem de batalha: B_WIN_MSG 28 tiles (src/battle_bg.c:143-148), x = 2"),
    U("src/battle_setup.c", "*", 28 * 8 - 2, "mensagem de batalha: B_WIN_MSG 28 tiles (src/battle_bg.c:143-148)"),
    # -- nomes que viram {STR_VAR} ou dados --
    U("src/string_util.c", "*", DIALOG_PX,
      _DIALOG + "; placeholder expandido no meio de um diálogo (ExpandPlaceholder, src/string_util.c)"),
    U("src/pokemon.c", "*", None, "apelido padrão (\"EGG\", \"GHOST\"): conta como nome de Pokémon, "
      "POKEMON_NAME_LENGTH (include/constants/global.h:63)", chars=10),
    U("src/quest_log*.c", "*", 30 * 8 - 2, "Quest Log: DESC_WIN_WIDTH 30 tiles (src/quest_log.c:40), x = 2"),
    U("src/pokemon_size_record.c", "*", DIALOG_PX, _DIALOG),
    U("src/scrcmd.c", "*", DIALOG_PX, _DIALOG + "; plural montado em {STR_VAR_n} (src/scrcmd.c)"),
    U("src/mail.c", "*", 24 * 8, "carta: janela de 24 tiles (src/mail.c:114-120)"),
    U("src/menu.c", "*", 6 * 8 - 8, "Sim/Não padrão: sYesNo_WindowTemplate 6 tiles (src/new_menu_helpers.c:48-53), "
      "texto em x = 8"),
    U("src/list_menu.c", "*", 8, "cursor da lista, um glifo antes do item (src/list_menu.c:390)"),
    # -- scripts --
    U("data/*", "script:*", DIALOG_PX, _DIALOG + "; usado por script"),
]

_TOKEN = re.compile(r'//[^\n]*|/\*.*?\*/|"(?:[^"\\\n]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\'|[{}()]'
                    r'|(?<![A-Za-z0-9_])[A-Za-z_]\w*', re.S)
_INDEX = re.compile(r"(?:^|[\n,{])\s*\[[^\]\n]+\]\s*=\s*$")   # designador `[X] =`, não a declaração `gX[] =`
_FIELD = re.compile(r"\.[A-Za-z_]\w*\s*=\s*$")
_VAR = re.compile(r"(?<![.\w])([A-Za-z_]\w*)\s*(?:\[[^\]]*\]\s*)*=\s*$")
_CALL = re.compile(r"([A-Za-z_]\w*)\s*$")
_DEFINITION = re.compile(r"\s*(?:\[[^\]]*\]\s*)*=(?!=)")   # a própria definição: gX[] = _("...") ou sTabela[] = {
_DECLARATION = re.compile(r"\s*(?:\[[^\]]*\]\s*)+;")   # extern const u8 gX[];


def _table_owner(source: str, braces: list[int]) -> str | None:
    for b in reversed(braces):
        before = source[max(0, b - 200):b]
        if _INDEX.search(before) or _FIELD.search(before):
            continue
        m = _VAR.search(before)
        if m:
            return m.group(1)
    return None


def c_contexts(source: str, labels: set[str]) -> dict[str, set[str]]:
    """Contexto de cada uso dos rótulos num arquivo C (comentários e literais pulados)."""
    out: dict[str, set[str]] = defaultdict(set)
    stack: list[tuple[str, object]] = []
    for m in _TOKEN.finditer(source):
        tok = m.group()
        c = tok[0]
        if c in "\"'" or tok.startswith(("//", "/*")):
            continue
        if tok == "(":
            call = _CALL.search(source, max(0, m.start() - 60), m.start())
            stack.append(("(", call.group(1) if call else "?"))
        elif tok == ")":
            while stack and stack.pop()[0] != "(":
                pass
        elif tok == "{":
            stack.append(("{", m.start()))
        elif tok == "}":
            while stack and stack.pop()[0] != "{":
                pass
        elif tok in labels:
            if _DEFINITION.match(source, m.end()) or _DECLARATION.match(source, m.end()):
                continue          # a própria definição `gText_X[] = _(` ou `extern ... gText_X[];`
            if stack and stack[-1][0] == "(":
                ctx = f"call:{stack[-1][1]}"
            else:
                owner = _table_owner(source, [p for kind, p in stack if kind == "{"]) if stack else None
                ctx = f"table:{owner}" if owner and stack and stack[-1][0] == "{" else "code"
            out[tok].add(ctx)
    return out


_SCRIPT_LINE = re.compile(r"^\s*([a-z_]\w*)\b(.*)$", re.M)


def script_contexts(source: str, labels: set[str]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = defaultdict(set)
    for m in _SCRIPT_LINE.finditer(source):
        for word in re.findall(r"[A-Za-z_]\w*", m.group(2)):
            if word in labels:
                out[word].add(f"script:{m.group(1)}")
    return out


def usage_index(sources: dict[str, str], labels: set[str]) -> dict[str, set[tuple[str, str]]]:
    """{rótulo: {(arquivo que usa, contexto)}} sobre os fontes dados (C e scripts)."""
    index: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for rel, text in sources.items():
        present = set(_IDENT.findall(text)) & labels      # filtro barato antes do passe completo
        if not present:
            continue
        found = script_contexts(text, present) if rel.endswith((".inc", ".s")) else c_contexts(text, present)
        for label, ctxs in found.items():
            for ctx in ctxs:
                index[label].add((rel, ctx))
    return index


_IDENT = re.compile(r"(?<![A-Za-z0-9_])[gGs][A-Za-z]\w*")


def match(use_file: str, ctx: str, label: str = "") -> UsageRule | None:
    for rule in USAGE_RULES:
        if (fnmatch.fnmatchcase(use_file, rule.file) and fnmatch.fnmatchcase(ctx, rule.context)
                and fnmatch.fnmatchcase(label, rule.label)):
            return rule
    return None
