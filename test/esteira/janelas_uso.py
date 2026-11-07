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
    unica: bool = False        # "*" legítimo: a tela só tem esta janela para estes textos

    @property
    def generic(self) -> bool:
        """Regra-pega-tudo (contexto e rótulo "*") que não é de tela de janela única: não pode
        decidir a janela de um texto de tabela ou de menu/lista (teste)."""
        return self.context == "*" and self.label == "*" and not self.unica


def U(file: str, context: str, px: int | None, source: str, **kw) -> UsageRule:
    return UsageRule(file, context, px, source, **kw)


class SharedRow(NamedTuple):
    """Dois textos na mesma linha: um a partir de `start_px`, outro alinhado à direita em
    `edge_px`. A soma tem de caber (cada um sozinho já tem a sua regra em USAGE_RULES)."""
    file: str
    start_px: int
    left: str                  # rótulo(s) do texto da esquerda (fnmatch)
    right: str                 # rótulo do texto alinhado à direita
    right_suffix: str          # o que o código põe depois dele (ex.: o número da página)
    edge_px: int
    font: str
    source: str


SHARED_ROWS: list[SharedRow] = [
    SharedRow("src/strings.c", 8, "gText_Cry", "gText_NextDataCancel", "", 236, "small",
              "barra de baixo da entrada da Pokédex: \"{START_BUTTON}Grito\" em x = 8 e os controles alinhados à "
              "direita em 236 (src/pokedex_screen.c:2894-2895, :2301-2303)"),
    SharedRow("src/strings.c", 8, "gText_Cry", "gText_CancelPreviousData", "", 236, "small",
              "barra de baixo do mapa de área: \"{START_BUTTON}Grito\" em x = 8 e os controles alinhados à "
              "direita em 236 (src/pokedex_screen.c:3074-3075, :2301-2303)"),
    SharedRow("src/strings.c", 8, "gText_DexCategory_*", "gText_Page", "99/99", 232, "normal",
              "título da categoria em x = 8 e \"PÁG. xx/xx\" alinhado à direita em 232 na janela 0 "
              "(src/pokedex_screen.c:2384-2385, :2361-2368, :3371-3379)"),
]


class VarContent(NamedTuple):
    """Exceção por contexto do pior caso de um placeholder variável (check_text.VAR_SIZES: 10 letras).
    Neste arquivo/rótulo, o código que enche o buffer prova o que vai em `var`: `chars` letras (nome de
    item = 13, ITEM_NAME_MAX_CHARS) ou, com `digits`, um número de até `chars` algarismos. `source` cita
    o arquivo:linha desse código (o teste confere). Só declare o que o código prova.
    Vale para a checagem (check_text) e para o reflow de um `.inc`; o `--var` da CLI do reflow é só
    prévia e não chega à checagem."""
    file: str                  # arquivo do texto (fnmatch), ex.: "data/maps/CeladonCity_GameCorner/text.inc"
    label: str                 # rótulo (fnmatch; `gX` também cobre o repetido `gX#2`)
    var: str                   # nome LITERAL de um placeholder de check_text.VAR_SIZES, sem chaves:
                               # "STR_VAR_1", "B_BUFF2", "DYNAMIC" (cobre todo {DYNAMIC n} do texto)
    chars: int
    source: str
    digits: bool = False


# Uma linha por (arquivo, rótulo, placeholder), em ordem alfabética de arquivo e rótulo (as frentes da
# tradução acrescentam em paralelo: a ordem espalha as inserções e evita conflito no merge). A ordem não
# decide nada: duas entradas que casem com o mesmo texto e placeholder são erro (ValueError em
# check_text.var_sizes e teste test_var_contents_never_overlap); padrão largo só sem sobreposição.
_TOWER_TIME = ("tempo da Trainer Tower: minutos, segundos e centésimos com 2 algarismos cada "
               "(PRINT_TOWER_TIME, src/trainer_tower.c:883-885)")
VAR_CONTENTS: list[VarContent] = [
    *(VarContent("data/maps/TrainerTower_Lobby/text.inc", "TrainerTower_Text_XMinYZSec", var, 2,
                 _TOWER_TIME + "; ttower_gettime (data/scripts/trainer_tower.inc:320) chama GetCurrentTime "
                 "(src/trainer_tower.c:888-897)", digits=True) for var in ("STR_VAR_1", "STR_VAR_2", "STR_VAR_3")),
    *(VarContent("src/battle_message.c", "gText_XMinYZSec", var, 2,
                 _TOWER_TIME + "; quadro de tempos (src/trainer_tower.c:913-914, :1066-1067)", digits=True)
      for var in ("STR_VAR_1", "STR_VAR_2", "STR_VAR_3")),
    VarContent("src/strings.c", "gText_Coins", "STR_VAR_1", 4,
               "moedas: ConvertIntToDecimalStringN(gStringVar1, coinAmount, ..., 4) (src/coins.c:54, :72)", digits=True),
    *(VarContent("src/strings.c", "gText_ConqTela_Rodape", var, 2,
                 "rodapé da tela de conquistas: feitas e válidas da aba com 2 algarismos (CONQ_COUNT = 46) "
                 "(src/conquistas_tela.c:777-778)", digits=True)
      for var in ("STR_VAR_2", "STR_VAR_3")),
    # DexNav (POK-47): quantas espécies da aba só aparecem em outro período (até DEXNAV_MAX_ENTRIES = 32)
    *(VarContent("src/strings.c", label, "STR_VAR_1", 2,
                 "linha extra do DexNav: ConvertIntToDecimalStringN(gStringVar1, t->extraN, ..., 2) (src/dexnav.c:1967)",
                 digits=True)
      for label in ("gText_DexNav_MaisNoite", "gText_DexNav_MaisDia", "gText_DexNav_MaisManha",
                    "gText_DexNav_MaisTarde", "gText_DexNav_MaisTardeNoite", "gText_DexNav_MaisOutros")),
    # diário (Task 8): "hh:mm" (o save guarda até 65535 minutos = "1092:15": 6 algarismos medem mais que o texto, o
    # ":" é mais estreito), turnos até 255 e nocautes até 255
    VarContent("src/strings.c", "gText_Diario_TempoTurnos", "STR_VAR_1", 6,
               "tempo do diário: FormatarTempo(gStringVar1, e->minutos) = 4 algarismos de horas e 2 de minutos, com o ':' "
               "(src/conquistas_tela.c:972)", digits=True),
    VarContent("src/strings.c", "gText_Diario_TempoTurnos", "STR_VAR_2", 3,
               "turnos do diário: ConvertIntToDecimalStringN(gStringVar2, e->turnos, ..., 3) (src/conquistas_tela.c:973)",
               digits=True),
    *(VarContent("src/strings.c", label, "STR_VAR_2", 3,
                 "nocautes do MVP: ConvertIntToDecimalStringN(gStringVar2, e->mvpNocautes, ..., 3) "
                 "(src/conquistas_tela.c:980)", digits=True)
      for label in ("gText_Diario_MvpUm", "gText_Diario_MvpVarios")),
    *(VarContent("src/strings.c", "gText_MenuSafariStats", var, n,
                 "Safari: passos (3), limite 600 (3) e bolas (2) (src/start_menu.c:290-292)", digits=True)
      for var, n in (("STR_VAR_1", 3), ("STR_VAR_2", 3), ("STR_VAR_3", 2))),
    VarContent("src/strings.c", "gText_PokeSum_EvoLevelFreeSlot", "STR_VAR_1", 3,
               "nível da evolução (Shedinja, + vaga na equipe): ConvertIntToDecimalStringN(gStringVar1, evo->param, "
               "..., 3) (src/pokemon_summary_screen.c:2647)", digits=True),
    VarContent("src/strings.c", "gText_PokeSum_FriendCount", "STR_VAR_1", 3,
               "amizade (Hack 7): ConvertIntToDecimalStringN(gStringVar1, friendship, ..., 3) "
               "(src/pokemon_summary_screen.c:2745)", digits=True),
    VarContent("src/strings.c", "gText_PokedollarVar1", "STR_VAR_1", 6,
               "dinheiro: ConvertIntToDecimalStringN(gStringVar1, amount, ..., 6) (src/money.c:78, :95); preço na "
               "loja com SHOP_PRICE_DIGITS = 5 (src/shop.c:602, :613)", digits=True),
]


# Chamadas que montam menu/lista: o texto que passa por elas tem de cair numa regra específica
MENU_CALL = re.compile(r"^call:\w*(?:Menu|List|PrintTextArray|ActionText|Multichoice)\w*$")
# Menu montado à mão: AddTextPrinterParameterized* numa função que também põe o cursor de menu
# (menu do PC, Seagallop: src/script_menu.c:1011-1061, :1261-1314)
MENU_PRINT = re.compile(r"^call:AddTextPrinterParameterized\d?$")
_MENU_INIT = re.compile(r"\b(?:Menu_InitCursor\w*|InitMenu\w*|CreateMCMenuInputHandlerTask|ListMenuInit\w*|"
                        r"MultichoiceGrid_InitCursor|CreateYesNoMenu\w*)\s*\(")
_FUNC_BODY = re.compile(r"^[A-Za-z_][\w \t*]*\([^;{}()]*(?:\([^()]*\)[^;{}()]*)*\)\s*\{", re.M)


def menu_function_labels(source: str, labels: set[str]) -> set[str]:
    """Rótulos usados dentro de uma função que também abre um cursor de menu: impressos um a
    um como itens de um menu montado à mão."""
    out: set[str] = set()
    for m in _FUNC_BODY.finditer(source):
        depth, i = 0, m.end() - 1
        while i < len(source):
            if source[i] == "{":
                depth += 1
            elif source[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        body = source[m.end():i]
        if _MENU_INIT.search(body):
            out |= set(re.findall(r"[A-Za-z_]\w*", body)) & labels
    return out


# Textos que só aparecem nos modelos do Easy Chat que o FRLG não abre (sobras do R/S/E)
_EC_UNREACHABLE = (
    "gText_AtTheBattlesStart", "gText_UponWinningABattle", "gText_UponLosingABattle", "gText_MakeMessageSixPhrases",
    "gText_MaxTwoTwelveLetterPhrases", "gText_YourFeelingAtTheBattlesStart", "gText_WhatYouSayIfYouWin",
    "gText_WhatYouSayIfYouLose", "gText_TheBardsSong", "gText_ChangeJustOneWordOrPhrase",
    "gText_AndImproveTheBardsSong", "gText_TheNewSong", "gText_Interview", "gText_FindWordsThatDescribeYour",
    "gText_FeelingsRightNow", "gText_WhatsHipAndHappening", "gText_CombineTwoWordsOrPhrases",
    "gText_AndMakeATrendySaying", "gText_TheTrendySaying",
)


# A primeira que casar com o uso vale. Linhas citadas conferidas em 18/10 (hack-switch 3a8d861f5).
USAGE_RULES: list[UsageRule] = [
    # -- menu Start e salvar --
    U("src/start_menu.c", "table:sStartMenuActionTable", 7 * 8 - 8,
      "rótulo do menu Start: janela de 7 tiles (src/new_menu_helpers.c:670), texto em x = 8 (src/start_menu.c:359)"),
    U("src/start_menu.c", "call:AddTextPrinterParameterized3", 60 - 2,
      "estatísticas do salvamento: nome em x = 2 e valor em x = 60, FONT_SMALL (src/start_menu.c:1072-1088)",
      font="small"),
    U("src/start_menu.c", "call:StringExpandPlaceholders", 10 * 8 - 4,
      "estatísticas da Safari: sSafariZoneStatsWindowTemplate 10 tiles (src/start_menu.c:138-142), x = 4 (src/start_menu.c:294)"),
    U("src/start_menu.c", "*", DIALOG_PX, _DIALOG + "; mensagens de salvar na janela 0 (src/start_menu.c:727, :1015)"),
    # -- opções --
    U("src/option_menu.c", "table:sOptionMenuItemsNames", 0x82 - 8,
      "nome da opção em x = 8 (src/option_menu.c:575) até a coluna de valores em x = 0x82 (src/option_menu.c:488)"),
    U("src/option_menu.c", "table:s*Options", 0x46,
      "valor da opção: coluna em x = 0x82 limpa com 0x46 px (src/option_menu.c:488-490)"),
    U("src/option_menu.c", "call:StringCopy", 0x46 - 8,
      "valor da opção \"tipo de moldura\" + número: coluna de 0x46 px (src/option_menu.c:488-490, :510-513)"),
    U("src/option_menu.c", "call:*PickSwitchCancel*", 0xE4, "controles: FONT_SMALL alinhado à direita em 0xE4 "
      "(src/option_menu.c:333-335)", font="small"),
    U("src/option_menu.c", "call:AddTextPrinterParameterized3", 0xE4, "controles: FONT_SMALL alinhado à direita "
      "em 0xE4 (src/option_menu.c:333-335)", font="small"),
    U("src/option_menu.c", "call:GetStringWidth", 0xE4, "controles: FONT_SMALL alinhado à direita em 0xE4 "
      "(src/option_menu.c:333-335)", font="small"),
    U("src/option_menu.c", "*", 26 * 8 - 8, "título das opções: janela de 26 tiles (src/option_menu.c:72-77), "
      "x = 8 (src/option_menu.c:545)"),
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
    U("src/*.c", "call:DisplayPartyMenuMessage", 28 * 8,
      "mensagem do grupo: janela 6 de 28 tiles (src/data/party_menu.h:180-184), x = 0 (src/party_menu.c:2573)"),
    U("src/data/party_menu.h", "table:sUnionRoomTradeMessages", 28 * 8,
      "troca no Union Room: mensagem do grupo (src/party_menu.c:3883) na janela 6 de 28 tiles "
      "(src/data/party_menu.h:180-184)"),
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
    U("src/pokemon_summary_screen.c", "table:sEggHatchTimeTexts", 15 * 8 - 7,
      "tempo para chocar: painel direito [POKESUM_WIN_INFO_3] 15 tiles (src/pokemon_summary_screen.c:790-794), "
      "x = 7 (src/pokemon_summary_screen.c:2982)"),
    U("src/pokemon_summary_screen.c", "table:sEggOriginTexts", 28 * 8,
      "origem do ovo: memória do Treinador, [POKESUM_WIN_INFO_4] 28 tiles (src/pokemon_summary_screen.c:799-803), "
      "x = 0 (src/pokemon_summary_screen.c:3326)"),
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
    U("src/shop.c", "call:BuyMenuDisplayMessage", DIALOG_PX, _DIALOG + "; mensagens da loja"),
    U("src/shop.c", "call:BuyMenuPrint", 8, "cursor da lista da loja (src/shop.c:666)", label="gText_SelectorArrow2"),
    U("src/shop.c", "call:BuyMenuPrint", 10 * 8,
      "traços no lugar da MT (Cancelar): janela 6 de 10 tiles (src/buy_menu_helpers.c:129-134), x = 0 "
      "(src/shop.c:642-643)", label="gText_*Hyphens"),
    U("src/shop.c", "*", DIALOG_PX, _DIALOG + "; mensagens da loja"),
    U("src/money.c", "*", 8 * 8 - 2, "caixa de dinheiro: 8 tiles (src/money.c:123)"),
    U("src/coins.c", "*", 8 * 8 - 2, "caixa de moedas: 8 tiles (src/coins.c:83), número e \"moedas\" em FONT_SMALL "
      "(src/coins.c:73-75)", font="small", label="gText_Coins"),
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
    U("src/pokemon_storage_system_menu.c", "call:ChooseBoxMenu_PrintTextToSprite", None,
      "\"/30\" desenhado no sprite da escolha de caixa (src/pokemon_storage_system_menu.c:580, :636-640): "
      "número, não texto traduzível"),
    U("src/pokemon_storage_system_menu.c", "*", DIALOG_PX, _DIALOG + "; descrição na janela 0 "
      "(src/pokemon_storage_system_menu.c:253)"),
    U("src/pokemon_storage_system_tasks.c", "table:sMessages", 18 * 8,
      "mensagem do PC (sMessages, src/pokemon_storage_system_tasks.c:275): janela de 18 tiles "
      "(src/pokemon_storage_system_tasks.c:199-203), x = 0 (src/pokemon_storage_system_tasks.c:2588)"),
    U("src/pokemon_storage_system_tasks.c", "*", 18 * 8,
      "mensagem do PC: janela de 18 tiles (src/pokemon_storage_system_tasks.c:199-203), x = 0 "
      "(src/pokemon_storage_system_tasks.c:2588)"),
    U("src/pokemon_storage_system_data.c", "call:StringCopyPadded", 9 * 8 - 6,
      "apelido do ovo no PC: displayMonTexts[0] impresso na janela 0 de 9 tiles em x = 6 "
      "(src/pokemon_storage_system_data.c:1096; src/pokemon_storage_system_tasks.c:190-196, :2295); "
      "conta também como nome de Pokémon, POKEMON_NAME_LENGTH (include/constants/global.h:63)",
      chars=10, label="gText_EggNickname"),
    U("src/pokemon_storage_system_data.c", "table:sMenuTexts", 9 * 8 - 8,
      "menus do PC (Mover, Marcar, papéis de parede...): janela de 9 tiles "
      "(src/pokemon_storage_system_tasks.c:191-195), texto em x = 8"),
    U("src/pokemon_storage_system_misc.c", "*", DIALOG_PX, _DIALOG),
    # -- Pokédex --
    U("src/pokedex_screen.c", "table:sListMenuItems_*DexModeSelect", 20 * 8 - 12,
      "menu da Pokédex: sWindowTemplate_ModeSelect 20 tiles (src/pokedex_screen.c:290-294), item_X = 12 "
      "(src/pokedex_screen.c:350)"),
    U("src/pokedex_screen.c", "table:sDexCategoryNamePtrs", 30 * 8,
      "título da categoria na janela 0 de 30 tiles (src/pokedex_screen.c:246-250), centralizado ou à esquerda "
      "(src/pokedex_screen.c:2380-2384)"),
    U("src/pokedex_screen.c", "call:DexScreen_PrintStringWithAlignment", 30 * 8,
      "título da Pokédex: janela 0 de 30 tiles (src/pokedex_screen.c:246-250), centralizado em 240 "
      "(src/pokedex_screen.c:1162, :3365-3383)"),
    U("src/pokedex_screen.c", "call:DexScreen_PrintControlInfo", 236,
      "controles da Pokédex: FONT_SMALL alinhado à direita em 236 (src/pokedex_screen.c:2301-2303)", font="small"),
    *(U("src/pokedex_screen.c", "*", 52 - 8,
        "\"Kanto\"/\"Nacional\" na contagem: FONT_SMALL em x = 8 com o número em x = 52 "
        "(src/pokedex_screen.c:1140-1147), sWindowTemplate_DexCounts 9 tiles (src/pokedex_screen.c:310-318)",
        font="small", label=lb) for lb in ("gText_Kanto", "gText_National")),
    *(U("src/pokedex_screen.c", "*", 9 * 8,
        "\"Vistos\"/\"Pegos\": linha própria na sWindowTemplate_DexCounts de 9 tiles (src/pokedex_screen.c:310-318), "
        "em FONT_NORMAL_COPY_1 no modo só Kanto (src/pokedex_screen.c:1156-1158) e FONT_SMALL no nacional "
        "(src/pokedex_screen.c:1139, :1144); mede na normal, a mais larga", label=lb)
      for lb in ("gText_Seen", "gText_Owned")),
    U("src/pokedex_screen.c", "*", 88,
      "\"Área desconhecida\": centralizado sobre a elipse de 88 px (src/pokedex_screen.c:3065-3068)",
      font="small", label="gText_AreaUnknown"),
    *(U("src/pokedex_screen.c", "*", 10 * 8,
        "\"Área\"/\"Tamanho\": centralizados nas janelas sWindowTemplate_AreaMap_Area/Size de 10 tiles "
        "(src/pokedex_screen.c:648-667, :2998, :3007)", font="small", label=lb) for lb in ("gText_Area", "gText_Size")),
    U("src/pokedex_screen.c", "*", 236 - 8,
      "\"{START_BUTTON}Grito\": FONT_SMALL em x = 8 na barra de baixo, que divide com os controles alinhados "
      "à direita em 236 (src/pokedex_screen.c:2894, :2303)", font="small", label="gText_Cry"),
    U("src/pokedex_screen.c", "*", 10,
      "\"{NO}\" antes do número, que vem em x + 9 (src/pokedex_screen.c:2215-2219); o glifo original mede "
      "10 px", font="small", label="gText_PokedexNo"),
    U("src/pokedex_screen.c", "*", 13 * 8 - 11 * 5,
      "\"Pokémon \" antes da categoria (até 11 letras FONT_SMALL) na sWindowTemplate_DexEntry_SpeciesStats "
      "de 13 tiles (src/pokedex_screen.c:608-613, :2706-2708)", font="small", label="gText_PokedexPokemonPrefix"),
    U("src/pokedex_screen.c", "*", 30,
      "\"Alt.\"/\"Peso\": FONT_SMALL com o valor em x + 30 (src/pokedex_screen.c:2775, :2766-2768)",
      font="small", label="gText_HT"),
    U("src/pokedex_screen.c", "*", 30,
      "\"Alt.\"/\"Peso\": FONT_SMALL com o valor em x + 30 (src/pokedex_screen.c:2783, :2766-2768)",
      font="small", label="gText_WT"),
    *(U("src/pokedex_screen.c", "*", 88 - 30 - 6 * 5,
        "unidade de altura/peso: no valor que começa em x + 30 (src/pokedex_screen.c:2775, :2783, "
        ":2756-2768), depois de \"999,9 \" (6 casas com espaçamento 5), antes da pegada em x = 88 (src/pokedex_screen.c:2880)",
        font="small", label=lb) for lb in ("gText_Meters", "gText_Kg")),
    U("src/pokedex_screen.c", "*", 200,
      "\"PÁG. 1/ 2\": alinhado à direita em 232 (src/pokedex_screen.c:2361-2368, :3379) na janela 0 de 30 tiles "
      "(src/pokedex_screen.c:246-250), menos \" 99/99\"", label="gText_Page"),
    U("src/pokedex_screen.c", "*", 23 * 8 - 56,
      "item vazio da lista numérica: sListMenuTemplate_OrderedListMenu item_X = 56 (src/pokedex_screen.c:517) "
      "na janela de 23 tiles (src/pokedex_screen.c:499-503); rótulo do item (src/pokedex_screen.c:1396, :1482)",
      label="gText_5Dashes"),
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
      "período no relógio do menu Start (Hack 7): sClockWindowTemplate 13 tiles (src/start_menu.c:152-156), "
      "x = 4 (src/start_menu.c:323), depois de \"00:00 \" (35 px, src/day_night.c:96-104); buffer "
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
    U("src/*.c", "call:PrintMysteryGiftMenuMessage", 28 * 8,
      "mensagem do Presente Misterioso/e-Reader: janela 1 de 28 tiles (src/mystery_gift_menu.c:97-101), x = 0 "
      "(src/mystery_gift_menu.c:528)"),
    U("src/mystery_gift_menu.c", "table:sUnusedMenuTexts", None,
      "tabela sem leitura no código (só definida em src/mystery_gift_menu.c:338): texto morto"),
    U("src/mystery_gift_menu.c", "call:AddTextPrinterParameterized4", 30 * 8 - 2,
      "barra de cima: 30 tiles (src/mystery_gift_menu.c:89-93), x = 2 (src/mystery_gift_menu.c:474)"),
    U("src/mystery_gift_menu.c", "*", 28 * 8,
      "mensagem do Presente Misterioso: janela 1 de 28 tiles (src/mystery_gift_menu.c:97-101), x = 0 "
      "(src/mystery_gift_menu.c:528)"),
    U("src/ereader_screen.c", "*", 28 * 8,
      "mensagem do e-Reader: janela 1 do Presente Misterioso, 28 tiles (src/mystery_gift_menu.c:97-101)"),
    U("src/mystery_event_script.c", "*", DIALOG_PX, _DIALOG),
    # -- multiescolha de script --
    U("src/script_menu.c", "table:sMultichoiceList_TrainerSchoolWhiteboard", 6 * 8,
      "quadro da Escola de Treinadores (src/script_menu.c:94-101): grade de 3 colunas "
      "(data/maps/ViridianCity_School/scripts.inc:56), "
      "célula de (GetMenuWidthFromList + 1) * 8 px com o texto em x = 8 (src/script_menu.c:698-711, :948-955; "
      "src/menu.c:580-591); a janela começa no tile 8 (src/script_menu.c:1211-1213) e a borda tem de caber no "
      "29, logo 3 células <= 21 tiles e o texto <= 6 tiles = 48 px"),
    U("src/script_menu.c", "table:sMultichoiceList_*", 214,
      "multiescolha vertical: a janela cresce com o texto, com (largura + 9) / 8 + 1 de largura em tiles, e se "
      "desloca para caber em 28 (src/script_menu.c:754-756): largura <= 214 px (com left = 0 a borda já sai da tela)"),
    *(U("src/script_menu.c", "call:AddTextPrinterParameterized", 13 * 8 - 8,
        "menu do PC: janela de 13 tiles antes da Pokédex (src/script_menu.c:1011-1017), texto em "
        "x = cursorWidth = 8 (src/script_menu.c:1006, :1043, :1046-1048; src/new_menu_helpers.c:147)", label=lb)
      for lb in ("gText_SomeoneSPc", "gText_BillSPc", "gText_LogOff")),
    *(U("src/script_menu.c", "call:AddTextPrinterParameterized", 14 * 8 - 8,
        "menu do PC com a Pokédex: janela de 14 tiles (src/script_menu.c:1014-1015), texto em x = 8 "
        "(src/script_menu.c:1029-1030, :1042)", label=lb) for lb in ("gText_ProfOakSPc", "gText_HallOfFame_2")),
    U("src/script_menu.c", "call:*", 13 * 8 - 8,
      "\"PC de {PLAYER}\" no menu do PC: janela de 13 tiles (src/script_menu.c:1011-1017), texto em x = 8 "
      "(src/script_menu.c:1049-1050)", label="gText_SPc"),
    U("src/script_menu.c", "table:sSeagallopDestStrings", 11 * 8 - 8,
      "menu do Seagallop: janela de 11 tiles (src/script_menu.c:1285), texto em x = cursorWidth = 8 "
      "(src/script_menu.c:1283, :1292)"),
    *(U("src/script_menu.c", "call:AddTextPrinterParameterized", 11 * 8 - 8,
        "\"Outro\"/\"Sair\" do menu do Seagallop: janela de 11 tiles (src/script_menu.c:1285), texto em x = 8 "
        "(src/script_menu.c:1301-1303)", label=lb) for lb in ("gText_Other", "gOtherText_Exit")),
    U("src/script_menu.c", "table:gStdStringPtrs", DIALOG_PX,
      _DIALOG + "; vai para {STR_VAR_n} pelo bufferstdstring (src/scrcmd.c:1693, src/script_menu.c:592)"),
    # POK-42: o degrau atual na fala da guarda da Liga (data/maps/IndigoPlateau_PokemonCenter_1F/text.inc)
    U("src/rematch_tier.c", "table:sRematchTierNames", DIALOG_PX,
      _DIALOG + "; vai para {STR_VAR_1} pelo special BufferRematchTierName (src/rematch_tier.c:159)"),
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
    U("src/daycare.c", "table:sCompatibilityMessages", DIALOG_PX,
      _DIALOG + "; copiado para gStringVar4 (src/daycare.c:1382)"),
    U("src/daycare.c", "*", DIALOG_PX, _DIALOG),
    U("src/fame_checker.c", "table:sNonTrainerNamePointers", 8 * 8 - 8,
      "nome na lista do Fame Checker: FCWINDOWID_LIST 8 tiles (src/fame_checker.c:476-484), item_X = 8 "
      "(src/fame_checker.c:1436), rótulo da lista (src/fame_checker.c:1566)"),
    U("src/fame_checker.c", "code", 8 * 8 - 8,
      "\"Cancelar\" da lista do Fame Checker: FCWINDOWID_LIST 8 tiles (src/fame_checker.c:476-484), item_X = 8 "
      "(src/fame_checker.c:1436, :1573)", label="gFameCheckerText_Cancel"),
    U("src/fame_checker.c", "code", 188,
      "ajuda de botões: FONT_SMALL alinhado à direita em 188 na FCWINDOWID_UIHELP (src/fame_checker.c:1078-1087)",
      font="small", label="gFameCheckerText_*UI"),
    U("src/fame_checker.c", "call:AddTextPrinterParameterized2", DIALOG_PX,
      "caixa do Fame Checker: FCWINDOWID_MSGBOX 26 tiles (src/fame_checker.c:494-498), x = 0 "
      "(src/fame_checker.c:826, :1523)"),
    U("src/fame_checker.c", "call:AddTextPrinterParameterized4", 8,
      "cursor da lista (src/fame_checker.c:1739)", label="gText_SelectorArrow2"),
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
    U("src/naming_screen.c", "table:s*NamingScreenTemplate*", 16 * 8 - 1,
      "título da tela de nome: WIN_TEXT_ENTRY_BOX 16 tiles (src/naming_screen.c:355-360), x = 1 "
      "(src/naming_screen.c:1710)"),
    U("src/naming_screen.c", "*", 30 * 8, "barra da tela de nome: WIN_BANNER 30 tiles (src/naming_screen.c:364-368)"),
    U("src/clear_save_data_screen.c", "call:AddTextPrinterParameterized4", 23 * 8,
      "apagar o save: mensagem na janela 1 de 23 tiles (src/clear_save_data_screen.c:45-53), x = 0 "
      "(src/clear_save_data_screen.c:109, :141)"),
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
    U("src/novidades.c", "call:AddTextPrinterParameterized4", 148,
      "título da tela de novidades: WIN_TITLE 30 tiles (src/novidades.c:253-258), FONT_NORMAL em x = 4 "
      "(src/novidades.c:828), até 152, antes dos controles", label="sText_Title"),
    U("src/novidades.c", "*", 80,
      "controles da tela de novidades: FONT_SMALL alinhado à direita em 236 na WIN_TITLE "
      "(src/novidades.c:829-830), de 156 em diante", font="small", label="sText_Controls"),
    U("src/conquistas_tela.c", "call:AddTextPrinterParameterized4", 240 - 228,
      "setas de rolagem da tela de conquistas: FONT_NORMAL em SETA_ROLAGEM_X = 228 (src/conquistas_tela.c:55) da "
      "WIN_LISTA de 30 tiles", label="sText_Seta*"),
    U("src/dexnav.c", "call:AddTextPrinterParameterized4", 240 - 228,
      "setas de rolagem do DexNav: FONT_NORMAL em COL_SETA_X = 228 (src/dexnav.c:98) da WIN_LISTA de 30 tiles",
      label="sText_Seta*"),
    U("src/dexnav.c", "call:StringCopy", 240 - 2 * 4,
      "separador das partes do rodapé do DexNav: FONT_SMALL em RODAPE_X = 4 (src/dexnav.c:184) da janela de 240 px "
      "(src/dexnav.c:60); o rodapé montado é medido em test/tests/test_dexnav_tela.py::test_rodape_cabe",
      font="small", label="sText_SeparadorRodape"),
    U("src/credits.c", "*", 30 * 8, "créditos: janela de 30 tiles (src/credits.c:456-460), centralizados",
      unica=True),
    U("src/help_system*.c", "*", 26 * 8, "ajuda: bitmap de 26 tiles (src/help_system_util.c:265)"),
    # -- troca, cartão, link, minijogos --
    U("src/trade.c", "table:sMenuAction_*", 12 * 8 - 8,
      "menu da troca: janela de 12 tiles (src/trade.c:605-609)"),
    U("src/trade.c", "table:sActionTexts", 2 * 32,
      "botão Cancelar da troca: 2 blocos de 32 px copiados para o sprite (DrawTextWindowAndBufferTiles, "
      "src/pokemon_storage_system_menu.c:68-79; src/trade.c:986)", label="gTradeText_Cancel"),
    U("src/trade.c", "table:sActionTexts", 6 * 32,
      "linha de baixo da troca: 6 blocos de 32 px no sprite (DrawBottomRowText, src/trade.c:2646-2648; "
      "src/pokemon_storage_system_menu.c:68-79)"),
    U("src/trade.c", "table:sMessages", 22 * 8,
      "mensagem da troca: janela 0 de 22 tiles (src/trade.c:597-601), x = 0 (src/trade.c:2584)"),
    U("src/trade.c", "*", 22 * 8, "mensagem da troca: janela de 22 tiles (src/trade.c:597-601)"),
    U("src/trade_scene.c", "*", 26 * 8, "mensagem da cena de troca: sTradeMessageWindowTemplates 26 tiles "
      "(src/trade_scene.c:480-485), x = 0 (src/trade_scene.c:2814)"),
    U("src/evolution_scene.c", "*", 26 * 8, "mensagem da evolução na troca: DrawTextOnTradeWindow, 26 tiles "
      "(src/trade_scene.c:480-485, :2808-2814)"),
    U("src/trainer_card.c", "table:sLinkTrainerCardRecordStrings", 27 * 8 - 16,
      "recorde de link no verso do cartão: janela de 27 tiles (src/trainer_card.c:235-239), copiado em "
      "src/trainer_card.c:1315"),
    U("src/trainer_card.c", "*", 27 * 8 - 16,
      "cartão de Treinador: janela de 27 tiles (src/trainer_card.c:235-239), textos a partir de x = 16"),
    U("src/battle_records.c", "*", 27 * 8, "recordes de batalha: janela de 27 tiles (src/battle_records.c:41-46)"),
    U("src/link.c", "*", 28 * 8 - 2, "erro de link: janelas da tela de erro, x = 2 (src/link.c:1488-1547)"),
    U("src/cable_club.c", "table:sTrainerCardColorNames", DIALOG_PX,
      _DIALOG + "; cor do cartão vai para {STR_VAR_2} de um diálogo (src/cable_club.c:996)"),
    U("src/cable_club.c", "*", DIALOG_PX, _DIALOG),
    U("src/union_room_chat_display.c", "table:sMessageWindowInfo", 28 * 8,
      "mensagem do chat: janela de 21 tiles, ou 28 com widerBox (src/union_room_chat_display.c:991-1001); "
      "vale a larga"),
    U("src/union_room_chat_display.c", "call:AddTextPrinterParameterized", 6 * 8 - 8,
      "Sim/Não do chat: janela de 6 tiles com o texto em x = 8 (src/union_room_chat_display.c:940-956)",
      label="gText_Yes"),
    U("src/union_room_chat_display.c", "call:AddTextPrinterParameterized", 6 * 8 - 8,
      "Sim/Não do chat: janela de 6 tiles com o texto em x = 8 (src/union_room_chat_display.c:940-956)",
      label="gText_No"),
    U("src/union_room_chat_display.c", "table:sKeyboardSwapTexts", 7 * 8 - 8,
      "troca de teclado do chat: janela 3 de 7 tiles (src/union_room_chat_display.c:187-191), PrintMenuTable "
      "(src/union_room_chat_display.c:1198) põe o texto depois do cursor, x = 8 (src/menu.c:472-476, "
      "src/new_menu_helpers.c:147); o 14 da chamada é a altura da linha"),
    U("src/union_room_chat_display.c", "call:AddTextPrinterParameterized3", 6 * 8 - 39,
      "reticências depois do nome: janela 2 de 6 tiles (src/union_room_chat_display.c:179-183), FONT_SMALL em "
      "x = 4 + 35 (src/union_room_chat_display.c:1132-1150)", font="small", label="gText_Ellipsis"),
    U("src/union_room_chat.c", "call:StringCopy", None,
      "frase registrada padrão do chat: copiada para registeredTexts[][21] do save (src/union_room_chat.c:1432-1441, "
      "include/global.h:873): 20 letras", chars=20),
    U("src/union_room_chat.c", "call:DynamicPlaceholderTextUtil_ExpandPlaceholders", 21 * 8,
      "entrou/saiu do chat: registro na janela 0 de 21 tiles (src/union_room_chat_display.c:163-168), x = 0 "
      "(src/union_room_chat_display.c:1217); expandido em src/union_room_chat.c:1298, :1318"),
    U("src/union_room_battle.c", "call:UnionRoomBattle_PrintTextOnWindow0", 26 * 8,
      "mensagem da batalha do Union Room: janela 0 de 26 tiles (src/union_room_battle.c:29-35), x = 0 "
      "(src/union_room_battle.c:73-80)"),
    U("src/data/union_room.h", "table:sListMenuItems_RegisterForTrade", 11 * 8 - 8,
      "menu Registrar/Info/Sair: sWindowTemplate_RegisterForTrade 11 tiles (src/data/union_room.h:203-207), "
      "item_X = 8 (src/data/union_room.h:213-227)"),
    U("src/wireless_communication_status_screen.c", "table:sHeaderTexts", 192,
      "título do status sem fio, sHeaderTexts[0] (src/wireless_communication_status_screen.c:128): "
      "centralizado em 192 (src/wireless_communication_status_screen.c:274-275)",
      label="gText_WirelessCommunicationStatus"),
    U("src/wireless_communication_status_screen.c", "table:sHeaderTexts", 22 * 8,
      "linhas do status sem fio: janela 1 de 22 tiles (src/wireless_communication_status_screen.c:100-104), "
      "x = 0 (src/wireless_communication_status_screen.c:279, :283)"),
    U("src/wireless_communication_status_screen.c", "table:sPlayersTextPtrs", None,
      "tabela sem leitura no código (só definida em src/wireless_communication_status_screen.c:120): texto morto"),
    U("src/wireless_communication_status_screen.c", "*", 22 * 8,
      "status da comunicação sem fio: janela de 22 tiles (src/wireless_communication_status_screen.c:100-104)"),
    U("src/berry_crush.c", "table:sMessages", DIALOG_PX,
      _DIALOG + "; janela 0 do diálogo (InitStandardTextBoxWindows, src/berry_crush.c:2547; :1275)"),
    U("src/berry_crush.c", "table:sBCRankingHeaders", 22 * 8,
      "cabeçalho dos resultados: janelas de 22-24 tiles (src/berry_crush.c:599-627), alinhado à direita "
      "(src/berry_crush.c:2925)"),
    U("src/berry_crush.c", "*", 24 * 8,
      "Berry Crush: mensagens e resultados em janelas de 22-24 tiles (src/berry_crush.c:545-549)"),
    U("src/dodrio_berry_picking.c", "table:sRankingTexts", 28 - 8,
      "colocação no ranking: FONT_SMALL em x = 8, com o nome em x = 28 (src/dodrio_berry_picking.c:4467-4471)",
      font="small"),
    U("src/dodrio_berry_picking.c", "table:sRecordsTexts", 224 - 1 - 30,
      "recordes: texto em x = 1 e número alinhado à direita em 224 (até 5 algarismos, 30 px) "
      "(src/dodrio_berry_picking.c:3008-3015)"),
    U("src/dodrio_berry_picking.c", "table:sPlaceholderPlayerNames", None,
      "nomes de enchimento copiados para gLinkPlayers[].name (src/dodrio_berry_picking.c:3077-3078): "
      "PLAYER_NAME_LENGTH (include/constants/global.h:64)", chars=7),
    U("src/dodrio_berry_picking.c", "*", 28 * 8,
      "Dodrio Berry Picking: janelas de 28 tiles (src/dodrio_berry_picking.c:409-433)"),
    U("src/pokemon_jump.c", "table:sRecordsTexts", 0xDE - 30,
      "recordes do Pokémon Jump: texto em x = 0 e número alinhado à direita em 0xDE (até 5 algarismos, 30 px) "
      "(src/pokemon_jump.c:4563-4567)"),
    U("src/pokemon_jump.c", "*", 28 * 8, "Pokémon Jump: janela de 28 tiles (src/pokemon_jump.c:4494-4498)"),
    U("src/slot_machine.c", "*", 20 * 8 - 1, "caça-níquel: janela 0 de 20 tiles (src/slot_machine.c:796-801), "
      "x = 1 (src/slot_machine.c:2336)"),
    U("src/pokemon_special_anim_scene.c", "table:sLevelUpWindowStatNames", 56,
      "atributos ao subir de nível: nome em x = 0 e valor em x = 56 (src/pokemon_special_anim_scene.c:1518-1520)"),
    U("src/pokemon_special_anim_scene.c", "table:s1_2_and_Poof_textPtrs", 28 * 8,
      "\"1, 2 e... Puf!\": copiado para a mensagem (src/pokemon_special_anim_scene.c:426) da janela de 28 tiles "
      "(src/pokemon_special_anim_scene.c:86-90)"),
    U("src/pokemon_special_anim_scene.c", "*", 28 * 8,
      "mensagem do uso de item: janela de 28 tiles (src/pokemon_special_anim_scene.c:86-90)"),
    # -- Easy Chat --
    U("src/data/easy_chat/*", "table:*", (24 * 8 - 2 * 17) // 2,
      "palavra do Easy Chat na moldura da frase: 2 palavras por linha, cada uma depois de um {CLEAR 17} "
      "(PrintECFields, src/easy_chat_3.c:1424-1472), na moldura de 24 tiles dos tipos que o FRLG abre "
      "(sPhraseFrameDimensions[0] e [2], src/easy_chat_3.c:170-185): 17 + p1 + 17 + p2 <= 192, logo 79 px; "
      "é mais estreito que a coluna da lista de palavras, x = 128 (src/easy_chat_3.c:1673) na janela de 28 tiles "
      "(src/easy_chat_3.c:259-263), 96 px"),
    U("src/easy_chat.c", "table:sEasyChatGroupNamePointers", 84,
      "nome de grupo do Easy Chat (src/easy_chat.c:552): colunas a cada 84 px (src/easy_chat_3.c:1587)"),
    U("src/easy_chat.c", "*", 84,
      "nome de grupo do Easy Chat: colunas a cada 84 px (src/easy_chat_3.c:1587)"),
    *(U("src/easy_chat_2.c", "table:sEasyChatScreenTemplates", None,
        "texto morto: modelo do Easy Chat de um tipo que o FRLG nunca abre (BATTLE_*, BARD_SONG, INTERVIEW, "
        "TRENDY_PHRASE, src/easy_chat_2.c:321-396); só PROFILE, MAIL e QUESTIONNAIRE são pedidos "
        "(data/scripts/mystery_event_club.inc:102, data/scripts/questionnaire.inc:6, src/party_menu.c:3538, :5504)",
        label=lb) for lb in _EC_UNREACHABLE),
    U("src/easy_chat_2.c", "table:sEasyChatScreenTemplates.titleText", 128,
      "título do Easy Chat: centralizado em 128 na janela 0 de 16 tiles (src/easy_chat_3.c:240-245, :1337-1339); "
      "lido da tabela em src/easy_chat_2.c:1193"),
    U("src/easy_chat_2.c", "code", 22 * 8,
      "confirmação de sair/apagar do Easy Chat (src/easy_chat_2.c:1236-1252): janela 1 de 22 tiles "
      "(src/easy_chat_3.c:250-257), x = 0 (src/easy_chat_3.c:1395-1398)"),
    U("src/easy_chat_2.c", "table:sEasyChatScreenTemplates", 22 * 8,
      "instruções e confirmações do Easy Chat (src/easy_chat_2.c:1223-1230): janela 1 de 22 tiles "
      "(src/easy_chat_3.c:250-257), x = 0 (src/easy_chat_3.c:1395-1398)"),
    U("src/easy_chat_3.c", "*", 22 * 8, "Easy Chat: janela de 22 tiles (src/easy_chat_3.c:250-254)"),
    # -- batalha --
    U("src/battle_message.c", "table:gTrainerTowerChallengeTypeTexts", DIALOG_PX, _DIALOG),
    U("src/battle_controller_player.c", "table:sStatStageNames", 216 // 4 - 16,
      "status com L/R (POK-40): até 4 rótulos + sinal e dígito (~12 px) + espaço por linha de "
      "STAT_STAGES_LINE_WIDTH = 216 px (src/battle_controller_player.c:249)"),
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
    U("src/list_menu.c", "*", 8, "cursor da lista, um glifo antes do item (src/list_menu.c:390)", unica=True),
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
                field = _FIELD_BEFORE.search(source, max(0, m.start() - 80), m.start())
                if ctx != "code" and field:
                    ctx += f".{field.group(1)}"       # `.titleText = gText_X` -> table:Dono.titleText
            out[tok].add(ctx)
    return out


_FIELD_BEFORE = re.compile(r"\.([A-Za-z_]\w*)\s*=\s*$")


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
    """A primeira regra do arquivo/contexto/rótulo; `table:X` vale também para `table:X.campo`."""
    base = ctx.split(".")[0]
    for rule in USAGE_RULES:
        if (fnmatch.fnmatchcase(use_file, rule.file)
                and (fnmatch.fnmatchcase(ctx, rule.context) or fnmatch.fnmatchcase(base, rule.context))
                and fnmatch.fnmatchcase(label, rule.label)):
            return rule
    return None


def repo_uses(repo) -> dict[str, set[tuple[str, str]]]:
    """Índice de uso do repo inteiro (rótulos com janela pelo uso), como a checagem o monta."""
    from pathlib import Path
    from esteira import check_text as ct
    root = Path(repo)
    raw = [e for e in ct._sources(root) if isinstance(e, ct._Entry)]
    labels = {e.label.split("#")[0].split(".")[0] for e in raw
              if (rule := ct.rule_for(e.file, e.label)) is not None and rule.by_usage}
    texts = {rel: (root / rel).read_text(encoding="utf-8") for rel, kind in ct._source_files(root)
             if kind == "c" or rel in ct._USAGE_SCRIPTS}
    return usage_index(texts, labels)


def repo_menu_uses(repo, uses: dict[str, set[tuple[str, str]]]) -> set[tuple[str, str, str]]:
    """(arquivo, contexto, rótulo) dos usos que montam menu: tabela, chamada de menu/lista
    (`MENU_CALL`) ou AddTextPrinterParameterized* numa função que abre cursor de menu."""
    from pathlib import Path
    root = Path(repo)
    printed: dict[str, set[str]] = defaultdict(set)
    for label, us in uses.items():
        for file, ctx in us:
            if MENU_PRINT.match(ctx):
                printed[file].add(label)
    in_menu = {(file, label) for file, labels in printed.items()
               for label in menu_function_labels((root / file).read_text(encoding="utf-8"), labels)}
    return {(file, ctx, label) for label, us in uses.items() for file, ctx in us
            if ctx.startswith("table:") or MENU_CALL.match(ctx)
            or (MENU_PRINT.match(ctx) and (file, label) in in_menu)}
