"""Checagem estática dos textos do jogo: charmap, terminador, largura/linhas/letras da janela,
códigos de controle e glossário da tradução, e inglês residual.

Fontes varridas (`_sources`): `.string`/`.braille` de `data/text/*.inc`, `data/maps/*/text.inc`,
`data/scripts/*.inc`, `data/event_scripts.s` e `data/mystery_event_msg.s`; todo `_("...")` de
`src/**/*.c|h` (menos o `pokedex_text_lg.h`, que a build FireRed não compila); `english` e
`description_english` do `items.json`; `name` do `region_map_sections.json`.

Regras (nome usado em `excecoes.json`):
  charmap     caractere/placeholder fora do charmap (ou fora do alfabeto braille);
  terminador  bloco `.string`/`.braille` sem `$` no fim;
  largura     linha mais larga que a janela (`WIDTH_RULES`: px, fonte, espaço; os textos com
              `by_usage` — strings.c, Easy Chat, textos soltos de .c — são medidos na janela
              de cada lugar onde o rótulo é usado: esteira/janelas_uso.py); no texto mudado em
              relação à base inglesa, também com {STR_VAR_n}/{B_BUFF*}... no pior caso (VAR_SIZES,
              exceções por contexto em janelas_uso.VAR_CONTENTS), sem passar do que a base passava;
  linhas      mais linhas que a janela comporta; no diálogo padrão (`box_lines`), mais de 2 linhas
              visíveis numa caixa, no texto mudado em relação à base (sem piorar a base);
  letras      campo de nome com mais bytes que o buffer do C;
  controle    os códigos de controle e placeholders diferem do texto da base inglesa
              (`TRANSLATION_BASE`; `\\n`, `\\l` e `\\p` podem mudar);
  glossario   texto mudado em relação à base com variante proibida ou termo inglês do glossário
              (`esteira/glossario.json`);
  ingles      palavras inglesas (`bloqueante`, o modo do pipeline: falha por texto; `progresso`:
              um aviso com o total; `desligado`);
  buffer      texto copiado em tempo de execução para um buffer fixo (gStringVar1/2/3, mapName[25]...)
              maior que ele, sem piorar a base inglesa (esteira/buffers.py; só roda com a base).

Só devolve problemas (`falha`, ou `aviso` para o inglês em progresso, a base ausente e as
exceções obsoletas); texto sem problema não gera `Result`.

Exceções (`exceptions["text"]`, em `test/excecoes.json`) congelam problemas pré-existentes. Cada
uma é um objeto com:
  file, label, rule  - qual achado (arquivo relativo ao repo com `/`, rótulo, regra);
  fingerprint        - sha1 (16 primeiros hex) do texto cru do rótulo na hora do congelamento;
  valor              - medida congelada (px, linhas ou letras), quando a regra mede algo;
  obs                - (opcional) por que o achado fica; não entra na comparação.
A exceção só cala o achado enquanto o fingerprint (e o valor) batem com o texto atual: texto
alterado volta a ser checado normalmente. Exceção cujo rótulo sumiu, cujo texto mudou ou cujo
problema desapareceu vira `aviso` "exceção obsoleta", para a lista poder encolher.
`compute_baseline(repo)` gera a lista de exceções para os problemas atuais.

CLI: `python3 -m esteira.check_text --ingles [arquivo...]` lista as palavras inglesas por arquivo.
"""

import argparse
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, NamedTuple

from esteira.result import Result

PLAYER_NAME_CHARS = 7  # {PLAYER}/{RIVAL}: nome de até 7 letras

# Commit da hack-switch antes da tradução (merge do Hack 7): a versão inglesa de cada texto.
TRANSLATION_BASE = "3a8d861f513f0805d586532acd56b7e2065b89ff"   # 3a8d861f5

# Regra `ingles`: "bloqueante" desde a Task 11 (integração da tradução): cada texto com palavra
# inglesa fora da lista de permissões reprova o build. Os textos que ficam em inglês de propósito
# (mensagens de depuração) são exceções congeladas em `excecoes.json`, com fingerprint.
# "progresso" (um aviso com o total) foi o modo das frentes da tradução, antes da integração.
ENGLISH_MODE = "bloqueante"
ENGLISH_MODES = ("progresso", "bloqueante", "desligado")

# Nome de item: ITEM_NAME_LENGTH = 14 bytes com o terminador (include/constants/global.h:62);
# o buffer da lista da bolsa ([19], src/item_menu.c:70) leva o código de cor de 5 bytes
# (src/item_menu.c:283) + 13 letras + EOS, e o da loja ([ITEM_NAME_LENGTH], src/shop.c:80)
# 13 + EOS. Decisão da Task 1 da tradução: 13 letras (antes os testes pediam 12).
ITEM_NAME_MAX_CHARS = 13


class Rule(NamedTuple):
    """Janela de uma fonte de texto. A primeira regra que casar (arquivo e, se houver, rótulo)
    vale. `prefix`: começo do rótulo, padrão fnmatch se tiver `*`/`?`/`[`, ou o rótulo exato se terminar
    em `$`. `px`/`lines`/
    `chars` = None: aquela medida não se aplica (o motivo fica em `source`)."""
    pattern: str
    prefix: str | None
    px: int | None
    source: str
    font: str = "normal"       # tabela de larguras: normal (= male/female) ou small
    lines: int | None = None   # máximo de linhas (quebras \n, \l, \p + 1)
    chars: int | None = None   # máximo de bytes sem o terminador (campos de nome)
    space: int | None = None   # largura do espaço, quando o renderizador não usa a da tabela
    no_prefix: bool = False    # {B_*_NAME_WITH_PREFIX} é sempre do jogador: só o nome, sem prefixo
    by_usage: bool = False     # a janela sai de onde o rótulo é usado (esteira/janelas_uso.py)
    box_lines: int | None = None   # máximo de linhas visíveis por caixa (entre \p): a caixa de diálogo
                                   # padrão mostra 2; a 3ª linha é cortada sem aviso (box_lines())


# Largura útil (px) por fonte de texto, derivada dos templates de janela do repo (arquivo:linha
# de cada um em `source`). O espaçamento entre letras (`letterSpacing`) não conta: só é somado a
# texto japonês (src/text.c:854).
DIALOG_WIDTH_PX = 26 * 8
# A caixa de diálogo padrão tem 4 tiles de altura = 2 linhas (sStandardTextBox_WindowTemplates,
# src/new_menu_helpers.c:36-44): `\n` desce uma linha, `\l` rola e escreve de novo na mesma linha
# (src/text.c:872-879), `\p` limpa. Uma 3ª linha (dois `\n` na mesma caixa, ou `\n` depois de `\l`
# na 2ª linha) sai fora da janela e CopyGlyphToWindow a corta sem aviso.
DIALOG_BOX_LINES = 2
_DIALOG = ("diálogo padrão: sStandardTextBox_WindowTemplates .width = 26 tiles (src/new_menu_helpers.c:40), "
           "texto em x = 0 (src/new_menu_helpers.c:411)")
_DIALOG_INC = ("aide", "berries", "competitive_brothers", "day_care", "eon_ticket", "flavor_text",
               "ingame_trade", "itemfinder", "obtain_item", "pc", "poke_mart", "route23", "safari_zone",
               "seagallop", "sign_lady", "surf", "trainer_card", "trainers", "white_out")
_BATTLE_MSG = ("janela de mensagem da batalha: sStandardBattleWindowTemplates[B_WIN_MSG] .width = 28 tiles "
               "(src/battle_bg.c:143-148), texto em x = 2 (src/battle_message.c:2406-2409)")
_OAK_OLD_MAN = ("janela do tutorial do Carvalho e do velho: [B_WIN_OAK_OLD_MAN] .width = 26 tiles "
                "(src/battle_bg.c:359-363), FONT_MALE em x = 0 (src/battle_message.c:2694-2697)")
_OAK_TUTORIAL = ("gText_ForPetesSake", "gText_TheTrainerThat", "gText_TryBattling", "gText_InflictingDamageIsKey",
                 "gText_LoweringStats", "gText_KeepAnEyeOnHP", "gText_OakNoRunningFromATrainer",
                 "gText_WinEarnsPrizeMoney", "gText_HowDissapointing")   # src/battle_controller_oak_old_man.c:652-844
_HELP = ("ajuda: HelpSystemRenderText num bitmap de 26 tiles mostrado nas colunas 2-27 "
         "(src/help_system_util.c:265), pergunta e resposta em x = 0 (src/help_system_util.c:598-599); "
         "o espaço avança 4 px (src/help_system_util.c:538); a resposta tem 13 tiles de altura e "
         "linhas de 15 px (src/help_system_util.c:398) e 14 de glifo: 6 * 15 + 14 = 104 px, 7 linhas")
_HELP_MOUSEOVER = ("Help_Text_DescWhatShouldIDo", "Help_Text_DescHowDoIDoThis", "Help_Text_DescWhatDoesThisTermMean",
                   "Help_Text_DescAboutThisGame", "Help_Text_DescTypeMatchupList", "Help_Text_DescExit")
# Itens das listas da ajuda (tópicos, perguntas, "Usando...", termos, assuntos, tipos) e o "Cancelar"
# que fecha cada lista: são lidos das tabelas de src/help_system.c, porque são ~180 rótulos sem prefixo
# comum. Cada um é desenhado numa linha da lista e, depois, como título da resposta.
_HELP_LIST_TABLES = ("sHelpSystemTopicPtrs", "sHelpSystemSpecializedQuestionTextPtrs", "sHelpSystemMenuTopicTextPtrs",
                     "sHelpSystemTermTextPtrs", "sHelpSystemGeneralTopicTextPtrs", "sHelpSystemTypeMatchupTextPtrs")
_HELP_LIST = ("item de lista e título da ajuda: na lista, uma linha por item em x = left + 8 "
              "(src/help_system_util.c:722-724) com left = 0 (src/help_system.c:1965, :2019) no bitmap de 26 tiles "
              "(src/help_system_util.c:265); na resposta, o mesmo texto é o título em x = 0, e a resposta começa "
              "24 px abaixo, em gDecompressionBuffer + 0x9C0 = 3 linhas de tiles (src/help_system_util.c:598-599): "
              "1 linha de 200 px; o espaço avança 4 px (src/help_system_util.c:538); tabelas em src/help_system.c "
              "(sHelpSystem*Ptrs; \"Cancelar\" em src/help_system.c:2014)")


def _help_list_labels(repo: Path) -> tuple[str, ...]:
    """Rótulos das tabelas de itens de lista da ajuda (src/help_system.c) e o Help_Text_Cancel."""
    try:
        source = (repo / "src" / "help_system.c").read_text(encoding="utf-8")
    except OSError:
        return ()
    labels: list[str] = []
    for table in _HELP_LIST_TABLES:
        m = re.search(rf"\b{table}\[[^\]]*\]\s*=\s*\{{(.*?)\}};", source, re.S)
        if m:
            labels += re.findall(r"\bHelp_Text_\w+", m.group(1))
    labels.append("Help_Text_Cancel")
    return tuple(dict.fromkeys(labels))


# Lido do repo da própria ferramenta (as regras são fixas, sem o repo checado); se a regex deixar de
# casar uma tabela, a lista encolhe em silêncio: test_help_list_labels_come_from_the_help_system_tables
# exige mais de 100 rótulos e uma amostra de cada tabela.
_HELP_LIST_LABELS = _help_list_labels(Path(__file__).resolve().parents[2])
_C_RESIDUE = ("textos soltos de outros .c/.h (troca, link, minijogos, menus, cenas): a janela sai de onde "
              "cada rótulo é usado (esteira/janelas_uso.py); rótulo sem uso indexável (macro, item "
              "posicional) fica sem medida")


def _novidades_rules(repo: Path) -> list[Rule]:
    """Janelas da tela de novidades do Prof. Carvalho, com as medidas de include/novidades.h
    (`NOVIDADES_*_PX`/`NOVIDADES_BODY_LINES`): a tela desenha as janelas com as mesmas constantes."""
    try:
        header = (repo / "include" / "novidades.h").read_text(encoding="utf-8")
    except OSError:
        return []
    c: dict[str, int] = {}
    at: dict[str, str] = {}   # constante -> "include/novidades.h:<linha>"
    for m in re.finditer(r"^#define NOVIDADES_(\w+)\s+(\d+)\b", header, re.M):
        c[m.group(1)] = int(m.group(2))
        at[m.group(1)] = f"include/novidades.h:{header.count(chr(10), 0, m.start()) + 1}"
    json_rel = "src/data/novidades/cartoes.json"
    where = "tela de novidades do Prof. Carvalho: "
    return [
        Rule(json_rel, "*.name", c["TOPIC_NAME_WIDTH_PX"], where + f"nome do tópico na grade, FONT_NORMAL, 1 linha "
             f"(NOVIDADES_TOPIC_NAME_WIDTH_PX, {at['TOPIC_NAME_WIDTH_PX']})", lines=1),
        Rule(json_rel, "*.title", c["TITLE_WIDTH_PX"], where + f"título do cartão na barra de cima, FONT_NORMAL, "
             f"1 linha (NOVIDADES_TITLE_WIDTH_PX, {at['TITLE_WIDTH_PX']})", lines=1),
        *[Rule(json_rel, f"*.{field}", c["BEFORE_AFTER_WIDTH_PX"], where + "linha ANTES/AGORA, FONT_SMALL, 1 linha "
              f"(NOVIDADES_BEFORE_AFTER_WIDTH_PX, {at['BEFORE_AFTER_WIDTH_PX']}); o rótulo faz parte do texto",
              font="small", lines=1)
          for field in ("before", "after")],
        Rule(json_rel, "*.body", c["BODY_WIDTH_PX"], where + "corpo do cartão, FONT_SMALL, só `\\n` "
             f"(NOVIDADES_BODY_WIDTH_PX, NOVIDADES_BODY_LINES, {at['BODY_WIDTH_PX']})", font="small",
             lines=c["BODY_LINES"]),
    ]


def _conquistas_rules(repo: Path) -> list[Rule]:
    """Janelas das conquistas e do diário (POK-44), com as larguras de include/conquistas.h
    (`CONQ_NOME_LARGURA`, `DIARIO_NOME_LARGURA`, `DIARIO_LOCAL_LARGURA`; FONT_NORMAL, 1 linha)."""
    try:
        header = (repo / "include" / "conquistas.h").read_text(encoding="utf-8")
    except OSError:
        return []
    c: dict[str, int] = {}
    at: dict[str, str] = {}   # constante -> "include/conquistas.h:<linha>"
    for m in re.finditer(r"^#define (CONQ_NOME_LARGURA|DIARIO_NOME_LARGURA|DIARIO_LOCAL_LARGURA)\s+(\d+)",
                         header, re.M):
        c[m.group(1)] = int(m.group(2))
        at[m.group(1)] = f"include/conquistas.h:{header.count(chr(10), 0, m.start()) + 1}"
    if len(c) != 3:
        return []
    json_rel = "src/data/conquistas/conquistas.json"
    where = "conquistas e diário: "
    return [
        Rule(json_rel, "c.*.nome", c["CONQ_NOME_LARGURA"], where + "nome da conquista na lista, FONT_NORMAL, "
             f"1 linha, {{N}} medido como 300 (CONQ_NOME_LARGURA, {at['CONQ_NOME_LARGURA']})", lines=1),
        Rule(json_rel, "d.*.nome", c["DIARIO_NOME_LARGURA"], where + "nome do evento na lista do diário, "
             f"FONT_NORMAL, 1 linha (DIARIO_NOME_LARGURA, {at['DIARIO_NOME_LARGURA']})", lines=1),
        Rule(json_rel, "d.*.local", c["DIARIO_LOCAL_LARGURA"], where + "local no detalhe do diário, "
             f"FONT_NORMAL, 1 linha (DIARIO_LOCAL_LARGURA, {at['DIARIO_LOCAL_LARGURA']})", lines=1),
    ]


WIDTH_RULES: list[Rule] = [
    Rule("data/maps/*/text.inc", None, DIALOG_WIDTH_PX, _DIALOG, box_lines=DIALOG_BOX_LINES),
    *[Rule(f"data/text/{name}.inc", None, DIALOG_WIDTH_PX, _DIALOG + "; usado só via msgbox/message",
           box_lines=DIALOG_BOX_LINES)
      for name in _DIALOG_INC],
    Rule("data/scripts/*.inc", None, DIALOG_WIDTH_PX, _DIALOG + "; scripts comuns (msgbox/message)",
         box_lines=DIALOG_BOX_LINES),
    Rule("data/event_scripts.s", None, DIALOG_WIDTH_PX, _DIALOG + "; scripts comuns (msgbox/message)",
         box_lines=DIALOG_BOX_LINES),
    Rule("data/mystery_event_msg.s", None, DIALOG_WIDTH_PX, _DIALOG + "; scripts de evento misterioso (msgbox)",
         box_lines=DIALOG_BOX_LINES),
    # -- textos longos (data/text) --
    *[Rule("data/text/help_system.inc", label, 26 * 8 - 2, _HELP + "; descrição do tópico sob o cursor em "
           "x = 2, 5 tiles de altura em y = 6 (src/help_system_util.c:606): 2 linhas", lines=2, space=4)
      for label in _HELP_MOUSEOVER],
    *[Rule("data/text/help_system.inc", label + "$", 26 * 8 - 8, _HELP_LIST, lines=1, space=4)
      for label in _HELP_LIST_LABELS],
    Rule("data/text/help_system.inc", None, 26 * 8, _HELP, lines=7, space=4),
    Rule("data/text/fame_checker.inc", "gFameCheckerFlavorTextOrigin", 0x54,
         "quadro do ícone do Fame Checker: FCWINDOWID_ICONDESC .width = 11 tiles (src/fame_checker.c:503-507), "
         "FONT_SMALL centralizado em 0x54 px (src/fame_checker.c:1404-1409)", font="small"),
    Rule("data/text/fame_checker.inc", None, DIALOG_WIDTH_PX,
         "caixa do Fame Checker: FCWINDOWID_MSGBOX .width = 26 tiles (src/fame_checker.c:494-498), texto em "
         "x = 0 (src/fame_checker.c:966, src/fame_checker.c:977); PokemonJournal_Text_* vão por msgbox; "
         "gFameCheckerPersonName_* e PersonQuote_* também saem aí (sFameCheckerNameAndQuotesPointers, "
         "src/fame_checker.c:965-966); a janela tem 4 tiles de altura = 2 linhas", box_lines=DIALOG_BOX_LINES),
    Rule("data/text/pokedude.inc", None, DIALOG_WIDTH_PX, _OAK_OLD_MAN + "; GetPokedudeText "
         "(src/battle_controller_pokedude.c:2558-2559)"),
    Rule("data/text/new_game_intro.inc", "gNameChoice_", 12 * 8 - 8,
         "lista de nomes da abertura: [WIN_INTRO_NAMES] .width = 12 tiles (src/oak_speech.c:318-323), x = 8 "
         "(src/oak_speech.c:2133); nome de jogador/rival: PLAYER_NAME_LENGTH (include/constants/global.h:64)",
         chars=PLAYER_NAME_CHARS),
    Rule("data/text/new_game_intro.inc", "gOtherText_NewName", 12 * 8 - 8,
         "lista de nomes da abertura: [WIN_INTRO_NAMES] .width = 12 tiles (src/oak_speech.c:318-323), x = 8 "
         "(src/oak_speech.c:2133)"),
    Rule("data/text/new_game_intro.inc", "gControlsGuide_Text_Intro", 30 * 8 - 2,
         "guia de controles, página 1: .width = 30 tiles (src/oak_speech.c:180-186), x = 2 (src/oak_speech.c:803)"),
    Rule("data/text/new_game_intro.inc", "gControlsGuide_Text_", 24 * 8 - 6,
         "guia de controles, páginas 2 e 3: .width = 24 tiles (src/oak_speech.c:203-209), x = 6 "
         "(src/oak_speech.c:825)"),
    Rule("data/text/new_game_intro.inc", "gPikachuIntro_Text_", 28 * 8 - 3,
         "apresentação do Pikachu: [WIN_INTRO_TEXTBOX] .width = 28 tiles (src/oak_speech.c:288-294), x = 3 "
         "(src/oak_speech.c:967, src/oak_speech.c:1026)"),
    Rule("data/text/new_game_intro.inc", "gOakSpeech_Text_", DIALOG_WIDTH_PX,
         "fala do Carvalho: janela 0 do diálogo padrão (InitStandardTextBoxWindows, src/oak_speech.c:754), "
         "FONT_MALE em x = 0 (src/oak_speech.c:1124-1133); " + _DIALOG, box_lines=DIALOG_BOX_LINES),
    Rule("data/text/pokedex_rating.inc", None, DIALOG_WIDTH_PX,
         _DIALOG + "; ShowFieldMessage (src/prof_pc.c:108) e msgbox", box_lines=DIALOG_BOX_LINES),
    Rule("data/text/pc_transfer.inc", None, DIALOG_WIDTH_PX,
         _DIALOG + "; também na tela de nome (janela 0, src/naming_screen.c:752-755) e como mensagem de batalha "
         "(222 px, mais larga): vale a mais estreita"),
    Rule("data/text/save.inc", None, DIALOG_WIDTH_PX,
         _DIALOG + "; PrintSaveTextWithFollowupFunc usa a janela 0 (src/start_menu.c:687-691)",
         box_lines=DIALOG_BOX_LINES),
    Rule("data/text/braille.inc", None, None,
         "braille: alfabeto próprio (tools/preproc/asm_file.cpp, mapa `encoding`) e janela de "
         "src/braille_text.c; só o alfabeto e o terminador são checados"),
    # -- src/strings.c (dona: frente E) --
    Rule("src/strings.c", "gStartMenuDesc_", 30 * 8 - 2,
         "barra de ajuda do menu Start: sHelpMessageWindowTemplate .width = 30 tiles (src/help_message.c:14), "
         "texto em x = 2 (src/help_message.c:97)"),
    # Os {STR_VAR_*} medem 0 aqui; as linhas montadas (nível, item, espécie) de toda espécie são
    # medidas à parte em _evolution_page_results (esteira/evolution_page.py).
    Rule("src/strings.c", "gText_PokeSum_Evo", 28 * 8 - 2,
         "página EVOLUTION do resumo: sWindowTemplates_Evolution[0] .width = 28 tiles "
         "(src/pokemon_summary_screen.c:921), texto em x = EVOLUTION_PAGE_TEXT_X = 2 "
         "(src/pokemon_summary_screen.c:911)"),
    # Hack 5: página IVs/EVs (os pedaços de cada linha; a linha inteira, com as colunas, é
    # medida em _ivev_page_results)
    *[Rule("src/strings.c", prefix, 28 * 8 - 2, "página IVs/EVs do resumo: sWindowTemplates_Ivs[0] .width = 28 tiles (src/pokemon_summary_screen.c:966), texto em x = IVEV_PAGE_TEXT_X = 2 (src/pokemon_summary_screen.c:957); as linhas montadas são medidas em _ivev_page_results")
      for prefix in ("gText_PokeSum_Iv", "gText_PokeSum_Stat", "gText_PokeSum_HiddenPower",
                     "gText_PokeSum_Ev")],
    # POK-44: os pedaços do aviso de conquista (as linhas montadas, com nome e item, são medidas em
    # test/tests/test_conquistas_aviso.py::test_larguras_montadas)
    Rule("src/strings.c", "gText_ConqAviso_", 26 * 8,
         "aviso de conquista: sAvisoWindowTemplate .width = 26 tiles (src/conquistas_aviso.c:53), FONT_NORMAL em "
         "x = 0, 1 linha por pedaço", lines=1),
    Rule("src/strings.c", None, None, "menus e janelas de dezenas de telas: a janela sai de onde cada rótulo "
         "é usado (esteira/janelas_uso.py, USAGE_RULES); texto sem uso no código fica sem medida", by_usage=True),
    # -- tabelas de texto --
    Rule("src/data/text/quest_log.h", None, 30 * 8 - 2,
         "janela de descrição do Quest Log: DESC_WIN_WIDTH = DISPLAY_WIDTH / 8 = 30 tiles (src/quest_log.c:40,163), "
         "texto em x = 2 (src/quest_log.c:1039)"),
    Rule("src/data/text/move_names.h", None, 8 * 8,
         "nome de golpe: MOVE_NAME_LENGTH (include/constants/global.h:67); na batalha, janela "
         "B_WIN_MOVE_NAME .width = 8 tiles (src/battle_bg.c:170-174) em FONT_SMALL, x = 0 "
         "(src/battle_message.c:2442-2445)", font="small", chars=12),
    Rule("src/data/text/abilities.h", "s*Description", 29 * 8 - 2,
         "descrição de habilidade no resumo: [POKESUM_WIN_SKILLS_5] .width = 29 tiles "
         "(src/pokemon_summary_screen.c:848-852), x = 2 (src/pokemon_summary_screen.c:3398); buffer "
         "abilityDescStrBuf[52] (src/pokemon_summary_screen.c:195)", chars=51),
    Rule("src/data/text/abilities.h", None, None,
         "nome de habilidade: ABILITY_NAME_LENGTH (include/battle_main.h:27)", chars=12),
    Rule("src/data/text/trainer_class_names.h", None, None,
         "classe de Treinador: gTrainerClassNames[][13] (include/data.h:24)", chars=12),
    Rule("src/data/text/species_names.h", None, None,
         "nome de espécie: POKEMON_NAME_LENGTH (include/constants/global.h:63)", chars=10),
    Rule("src/data/text/nature_names.h", None, None,
         "nome de natureza sem buffer fixo; aparece montado em \"X nature.\" no resumo (frente E mede a frase)"),
    Rule("src/data/text/teachy_tv.h", "gTeachyTvString_", 22 * 8 - 8,
         "menu da TV Educativa: janela 1 .width = 22 tiles (src/teachy_tv.c:156-160), item_X = 8 "
         "(src/teachy_tv.c:234)"),
    Rule("src/data/text/teachy_tv.h", None, DIALOG_WIDTH_PX,
         "roteiro da TV Educativa: janela 0 .width = 26 tiles (src/teachy_tv.c:147-151), FONT_MALE em x = 0 "
         "(src/teachy_tv.c:679)"),
    Rule("src/data/text/*.h", None, None, "tabela de texto sem janela própria conhecida"),
    *_novidades_rules(Path(__file__).resolve().parents[2]),
    *_conquistas_rules(Path(__file__).resolve().parents[2]),
    # -- batalha (dona: frente G) --
    *[Rule("src/battle_message.c", label, DIALOG_WIDTH_PX,
           _OAK_OLD_MAN + "; impresso em src/battle_controller_oak_old_man.c:652-844") for label in _OAK_TUTORIAL],
    Rule("src/battle_message.c", "gText_WhatWill", 14 * 8 - 2,
         "pergunta de ação: [B_WIN_ACTION_PROMPT] .width = 14 tiles (src/battle_bg.c:152-156), x = 2 "
         "(src/battle_message.c:2418-2421); o Pokémon ativo é o do jogador, sem o prefixo do oponente "
         "(src/battle_message.c:1815-1817)", no_prefix=True),
    *[Rule("src/battle_message.c", label, 12 * 8,
           "menu de ação: [B_WIN_ACTION_MENU] .width = 12 tiles (src/battle_bg.c:161-165), x = 0 "
           "(src/battle_message.c:2430-2433)") for label in ("gText_BattleMenu", "gText_SafariZoneMenu")],
    Rule("src/battle_message.c", "gText_BattleSwitchWhich", 8 * 8,
         "pergunta de troca: [B_WIN_SWITCH_PROMPT] .width = 8 tiles (src/battle_bg.c:242-246), x = 0 "
         "(src/battle_message.c:2538-2541)"),
    Rule("src/battle_message.c", "gText_BattleYesNoChoice", 4 * 8,
         "Sim/Não da batalha: [B_WIN_YESNO] .width = 4 tiles (src/battle_bg.c:269-273), x = 0 "
         "(src/battle_message.c:2574-2577)"),
    *[Rule("src/battle_message.c", label, 64,
           "resultado do link: centralizado em 64 px (src/battle_message.c:2749-2752)")
      for label in ("gText_Win", "gText_Loss", "gText_Draw")],
    Rule("src/battle_message.c", "gText_MoveInterfacePP", 3 * 8,
         "rótulo do PP: [B_WIN_PP] 3 tiles (src/battle_bg.c:206-210), FONT_SMALL x = 0 "
         "(src/battle_message.c:2490-2493); copiado em src/battle_controller_player.c:1389", font="small"),
    Rule("src/battle_message.c", "gText_MoveInterfaceType", 8 * 8 - 6 * 5,
         "rótulo do tipo: [B_WIN_MOVE_TYPE] 8 tiles (src/battle_bg.c:215-219), FONT_SMALL x = 0; o nome do tipo "
         "(até 6 letras de 5 px) vem depois (src/battle_controller_player.c:1413)", font="small"),
    Rule("src/battle_message.c", "gText_MoveInterface", 8 * 8,
         "códigos de cor da janela de golpes: [B_WIN_MOVE_TYPE] 8 tiles (src/battle_bg.c:215-219)", font="small"),
    Rule("src/battle_message.c", None, 28 * 8 - 2, _BATTLE_MSG + "; nomes de Pokémon/golpe/item/habilidade "
         "nos {B_*} medem o maior nome possível (DYNAMIC_LETTERS), e os {B_*_WITH_PREFIX} somam o prefixo "
         "mais largo (sText_*Prefix*)"),
    Rule("src/battle_main.c", "TYPE_", None,
         "nome de tipo: TYPE_NAME_LENGTH (include/battle_main.h:26)", chars=6),
    Rule("src/battle_main.c", None, None, "texto japonês de depuração/status sem janela"),
    # -- descrições e dados --
    Rule("src/move_descriptions.c", None, 15 * 8 - 7,
         "descrição de golpe: no resumo, [POKESUM_WIN_MOVES_4] .width = 15 tiles (src/pokemon_summary_screen.c:879-883) "
         "com x = 7 (src/pokemon_summary_screen.c:3359-3360), a mais estreita; no tutor, janela de 15 tiles "
         "(src/learn_move.c:300-304) com x = 1 (src/learn_move.c:842); 4 linhas (13 tiles de altura a partir "
         "de y = 42 no resumo, 8 tiles no tutor); também é a descrição da MT/MO (src/data/items.json.txt:17-18) "
         "no estojo e na loja de MT: WIN_DESCRIPTION de 18 tiles (src/tm_case.c:254-261) com x = 2 "
         "(src/tm_case.c:744), 142 px e 4 linhas, mais folgada", lines=4),
    Rule("src/data/pokemon/pokedex_text_fr.h", None, 232,
         "entrada da Pokédex: sWindowTemplate_DexEntry_FlavorText .width = 30 tiles "
         "(src/pokedex_screen.c:618-623), centralizada em 240 px pela linha mais larga "
         "(src/pokedex_screen.c:2803-2811), mas a moldura do fundo cobre as colunas 1-2 e 237-238: "
         "232 px deixam 1 px livre de cada lado, sombra inclusive; 7 tiles de altura com o texto em y = 8 "
         "(src/pokedex_screen.c:2882): 3 linhas",
         lines=3),
    Rule("src/data/pokemon/pokedex_entries.h", "*.categoryName", None,
         "categoria da Pokédex: categoryName[12] (include/pokedex.h:104)", chars=11),
    Rule("src/data/pokemon/pokedex_entries.h", None, None, "sem outro texto"),
    Rule("src/berry.c", "*.name", None, "nome de fruta: BERRY_NAME_LENGTH (include/global.berry.h:4)", chars=6),
    Rule("src/berry.c", None, None,
         "descrições de fruta em japonês, sem uso no FRLG: a bolsa de frutas mostra a descrição do "
         "items.json (src/berry_pouch.c:756)"),
    Rule("src/data/decoration/header.h", None, None, "nome de enfeite: name[16] (include/decoration.h:46)",
         chars=15),
    Rule("src/data/decoration/description.h", None, None,
         "sem tela no FRLG: os enfeites só são exportados no cabeçalho da ROM (src/rom_header_gf.c:108)"),
    Rule("src/union_room_message.c", "gText_UR_NameWantedOfferLv", 28 * 8 - 8,
         "cabeçalho do quadro de trocas: sWindowTemplate_TradingBoardHeader .width = 28 tiles "
         "(src/data/union_room.h:292-296), FONT_SMALL em x = 8 (src/union_room.c:3905)", font="small"),
    Rule("src/union_room_message.c", None, DIALOG_WIDTH_PX,
         "Union Room: PrintOnTextbox usa a janela 0 do diálogo (src/union_room.c:3848-3856); " + _DIALOG
         + "; os rótulos de menu (sText_* curtos) também ficam nesse limite"),
    Rule("src/data/region_map/region_map_sections.json", None, 15 * 8 - 12,
         "nome de lugar: no mapa da região vai para `u8 mapName[19]`/`dungeonName[19]` sem limite de cópia "
         "(src/region_map.c:96-97, GetMapName em :1448, StringCopy em :1480): 18 letras; a janela de "
         "calabouço/floresta WIN_DUNGEON_NAME tem 15 tiles (src/region_map.c:476-481) com o texto em "
         "x = 12 (src/region_map.c:1481): 108 px, valendo para todos os nomes (o aviso ao entrar no mapa, "
         "112 px e mapName[25] em src/map_name_popup.c:194-195, é mais folgado)", chars=18),
    Rule("src/data/items.json", "*.name", 110 - 9,
         "nome de item: ITEM_NAME_LENGTH 14 com o terminador (include/constants/global.h:62); buffer da "
         "bolsa [19] (src/item_menu.c:70) = cor de 5 bytes (src/item_menu.c:283) + 13 + EOS; na lista da "
         "bolsa o nome vai em x = 9 (src/item_menu.c:652) e a quantidade em x = 110 (src/item_menu.c:716)",
         chars=ITEM_NAME_MAX_CHARS),
    Rule("src/data/items.json", "ITEM_[TH]M[0-9][0-9]", None,
         "descrição de MT/MO sem tela: o gItems[].description de todo item do estojo de MT aponta para "
         "gMoveDescription_* (src/data/items.json.txt:17-18), então o estojo, a loja de MT e o PC mostram a "
         "descrição do golpe (medida em src/move_descriptions.c) e este texto nunca aparece"),
    Rule("src/data/items.json", "ITEM_*_BERRY", 198,
         "descrição de fruta: na bolsa de frutas, janela 1 de 25 tiles e .height = 4 (src/berry_pouch.c:226-233) "
         "com o texto em x = 0, y = 2 (src/berry_pouch.c:764) e linhas de 14 px: 2 linhas (a 3ª fica com 2 px); "
         "segurada por um Pokémon, aparece no PC de Pokémon em x = 2 (src/pokemon_storage_system_misc.c:1149) "
         "na janela de 25 tiles (src/pokemon_storage_system_tasks.c:207-214): 198 px", lines=2),
    Rule("src/data/items.json", None, 198,
         "descrição de item: na mochila, sDefaultBagWindowsStd[1].width = 25 tiles (src/bag.c:33), texto em "
         "x = 0 (src/item_menu.c:756), 6 tiles de altura (src/bag.c:34): 3 linhas de 200 px; segurado por um "
         "Pokémon, aparece no PC de Pokémon em x = 2 (src/pokemon_storage_system_misc.c:1149) na janela 2 de "
         "25 tiles (src/pokemon_storage_system_tasks.c:207-214): 198 px, a mais estreita (as originais medem "
         "no máx. 198). Loja e PC de itens: 25 tiles com x = 0, mais folgados; frutas e MTs têm regra própria",
         lines=3),
    Rule("src/data/trainers.h", "*.trainerName", None,
         "nome de Treinador: trainerName[12] (include/battle.h:122)", chars=11),
    Rule("src/trainer_tower_sets.c", "*.name*", None,
         "Treinador da Trainer Tower: name[11] (include/cereader_tool.h:9)", chars=10),
    Rule("src/trainer_tower_sets.c", "*.nickname*", None,
         "apelido de Pokémon: nickname[POKEMON_NAME_LENGTH + 1] (include/pokemon.h:166)", chars=10),
    Rule("src/data/ingame_trades.h", "*.nickname*", None,
         "troca no jogo: nickname[POKEMON_NAME_LENGTH + 1] (src/trade_scene.c:58)", chars=10),
    Rule("src/data/ingame_trades.h", "*.otName*", None,
         "troca no jogo: otName[11] (src/trade_scene.c:67)", chars=10),
    Rule("src/data/easy_chat/*", None, None,
         "palavras do Easy Chat: a janela sai do uso (tabelas de grupo -> colunas de 13 tiles, "
         "esteira/janelas_uso.py); a ordem alfabética fica com a frente G", by_usage=True),
    Rule("src/keyboard_text.c", None, None, "layouts de teclado do Easy Chat e da tela de nome"),
    Rule("src/*", None, None, _C_RESIDUE, by_usage=True),
]

# Regras (usadas em `excecoes.json`)
RULE_CHARMAP = "charmap"
RULE_TERMINATOR = "terminador"
RULE_WIDTH = "largura"
RULE_LINES = "linhas"
RULE_CHARS = "letras"
RULE_SYNTAX = "sintaxe"
RULE_CONTROL = "controle"
RULE_GLOSSARY = "glossario"
RULE_ENGLISH = "ingles"
RULE_BUFFER = "buffer"          # esteira/buffers.py: texto copiado para um buffer fixo maior que ele
RULE_OBSOLETE = "obsoleta"

# Placeholders que viram texto em tempo de execução: medem o maior nome possível, em letras da
# fonte (o maior nome de cada campo: include/constants/global.h, include/battle_main.h,
# include/data.h, include/battle.h). Os de conteúdo variado ({STR_VAR_n}, {B_BUFF*}...) ficam em
# VAR_SIZES, medidos no pior caso só nos textos mudados em relação à base inglesa.
_MON = 10
DYNAMIC_LETTERS: dict[str, int] = {
    "PLAYER": PLAYER_NAME_CHARS, "RIVAL": PLAYER_NAME_CHARS,
    **{name: PLAYER_NAME_CHARS for name in (
        "B_PLAYER_NAME", "B_LINK_PLAYER_NAME", "B_LINK_PARTNER_NAME", "B_LINK_OPPONENT1_NAME",
        "B_LINK_OPPONENT2_NAME", "B_LINK_SCR_TRAINER_NAME", "B_PC_CREATOR_NAME")},
    **{name: _MON for name in (
        "B_PLAYER_MON1_NAME", "B_OPPONENT_MON1_NAME", "B_PLAYER_MON2_NAME", "B_OPPONENT_MON2_NAME",
        "B_LINK_PLAYER_MON1_NAME", "B_LINK_OPPONENT_MON1_NAME", "B_LINK_PLAYER_MON2_NAME",
        "B_LINK_OPPONENT_MON2_NAME", "B_ATK_PARTNER_NAME")},
    "B_CURRENT_MOVE": 12, "B_LAST_MOVE": 12, "B_LAST_ITEM": ITEM_NAME_MAX_CHARS,
    **{name: 12 for name in ("B_LAST_ABILITY", "B_ATK_ABILITY", "B_DEF_ABILITY", "B_SCR_ACTIVE_ABILITY",
                             "B_EFF_ABILITY", "B_TRAINER1_CLASS")},
    "B_TRAINER1_NAME": 11,
}
# Nome de Pokémon com o prefixo/sufixo de lado ("Wild ", "Foe "): src/battle_message.c, os
# sText_*Prefix* de BattleStringExpandPlaceholders; o mais largo deles é somado.
_PREFIXED = ("B_ATK_NAME_WITH_PREFIX_MON1", "B_ATK_NAME_WITH_PREFIX", "B_DEF_NAME_WITH_PREFIX",
             "B_EFF_NAME_WITH_PREFIX", "B_ACTIVE_NAME_WITH_PREFIX", "B_SCR_ACTIVE_NAME_WITH_PREFIX")
_PREFIX_ONLY = ("B_ATK_PREFIX1", "B_DEF_PREFIX1", "B_ATK_PREFIX2", "B_DEF_PREFIX2", "B_ATK_PREFIX3",
                "B_DEF_PREFIX3")
_PREFIX_LABEL = re.compile(r"^sText_\w*Prefix\d*$")


class VarSize(NamedTuple):
    """Tamanho no pior caso do que o jogo põe num placeholder variável: `chars` letras na letra mais
    larga da fonte ou, com `digits`, `chars` algarismos no algarismo mais largo."""
    chars: int
    digits: bool = False

    def describe(self) -> str:
        return f"{self.chars} {'algarismos' if self.digits else 'letras'}"


# Placeholders de conteúdo variável (Task T3 da tradução). O inglês confia em nomes curtos e muitas
# vezes estoura nessa medida, por isso ela só vale para texto mudado em relação à base inglesa (ou
# novo), com o critério "sem piorar a base" (_worst_case_problem). Pior caso padrão: 10 letras, o
# tamanho de _MON (POKEMON_NAME_LENGTH, include/constants/global.h:63), que cobre nome de jogador ou
# rival (7), espécie (10) e "LT. SURGE" (9). Um texto cujo conteúdo o código C prova (número de N
# algarismos, nome de item de 13 letras...) declara isso em esteira/janelas_uso.VAR_CONTENTS.
VAR_SIZES: dict[str, VarSize] = {
    # gStringVar1..3 (src/string_util.c:371-384): nome, espécie, item, número, texto de tabela...
    **{name: VarSize(_MON) for name in ("STR_VAR_1", "STR_VAR_2", "STR_VAR_3")},
    # gUnknownStringVar (src/string_util.c:361-364); sem uso no FRLG
    "UNKNOWN_STR": VarSize(_MON),
    # batalha: {B_BUFF1..3} expandem gBattleTextBuff1..3 (src/battle_message.c:1850-1879) com nome de
    # golpe (12), tipo, apelido com ou sem prefixo, atributo, espécie, habilidade (12), item (13) ou
    # número (src/battle_message.c:2211-2304); {B_COPY_VAR_n} = gStringVar1..3 (src/battle_message.c:1881-1889);
    # {B_26} = apelido (src/battle_message.c:2139-2140). Padrão de 10 letras; o contexto pode subir ou descer.
    **{name: VarSize(_MON) for name in ("B_BUFF1", "B_BUFF2", "B_BUFF3", "B_COPY_VAR_1", "B_COPY_VAR_2",
                                        "B_COPY_VAR_3", "B_26")},
    # apelidos do charmap para FD 08/09/0C/0D (nome de Treinador/Pokémon na batalha), sem uso no texto
    **{name: VarSize(_MON) for name in ("ATTACKING_TRAINER", "DEFENDING_TRAINER", "ATTACKING_MON",
                                        "DEFENDING_MON")},
    # textos fixos do R/S (src/strings.c:7-14, o maior de FR/LG), sem uso no FRLG
    "VERSION": VarSize(8), "EVIL_TEAM": VarSize(5), "GOOD_TEAM": VarSize(5), "EVIL_LEADER": VarSize(6),
    "GOOD_LEADER": VarSize(6), "EVIL_LEGENDARY": VarSize(7), "GOOD_LEGENDARY": VarSize(7),
    # {DYNAMIC n} (F7 n): o ponteiro n de DynamicPlaceholderTextUtil_SetPlaceholderPtr
    # (src/dynamic_placeholder_text_util.c:97-110), usado no Quest Log, Union Room, minijogos e diploma:
    # espécie (src/quest_log_events.c:1026), apelido "Ovo" (:1028), gStringVar1 (:1320), jogador...
    "DYNAMIC": VarSize(_MON),
}
# Medem 0 de propósito: {KUN} (gExpandedPlaceholder_Kun/Chan vazios, src/strings.c:5-6) e
# {B_TRAINER1/2_LOSE/WIN_TEXT} (a fala inteira do Treinador, src/battle_message.c:2109-2138, medida
# no próprio rótulo de onde vem).


def var_content_matches(vc, file: str, label: str) -> bool:
    """A exceção por contexto `vc` (janelas_uso.VarContent) vale para este texto? Arquivo e rótulo
    por fnmatch; `gX#2` (rótulo C repetido) também casa com o padrão de `gX`."""
    return fnmatch.fnmatchcase(file, vc.file) and (fnmatch.fnmatchcase(label, vc.label)
                                                   or fnmatch.fnmatchcase(label.split("#")[0], vc.label))


def has_var(text: str, name: str) -> bool:
    """O texto usa o placeholder variável `name` ({STR_VAR_1}, ou {DYNAMIC 0x00} com argumento)?"""
    return re.search(r"\{" + re.escape(name) + r"(?:\s[^}]*)?\}", text) is not None


def var_sizes(file: str, label: str) -> dict[str, VarSize]:
    """Pior caso de cada placeholder variável num texto: VAR_SIZES com as exceções por contexto de
    esteira/janelas_uso.VAR_CONTENTS que casam com o arquivo e o rótulo. Duas entradas para o mesmo
    texto e placeholder são erro (ValueError): a ordem da lista não decide nada."""
    from esteira import janelas_uso
    sizes = dict(VAR_SIZES)
    seen: dict[str, object] = {}
    for vc in janelas_uso.VAR_CONTENTS:
        if var_content_matches(vc, file, label) and vc.var in VAR_SIZES:
            if vc.var in seen:
                raise ValueError(f"VAR_CONTENTS: entradas sobrepostas para {file}: {label} {{{vc.var}}}: "
                                 f"{seen[vc.var]} e {vc}")
            seen[vc.var] = vc
            sizes[vc.var] = VarSize(vc.chars, vc.digits)
    return sizes


# Caneta: {CLEAR_TO n}/{SKIP n} levam a x = n, {CLEAR n} avança n (src/text.c, RenderText)
_PEN_CODES = ("CLEAR_TO", "SKIP", "CLEAR")
_FONT_CODES = {"FONT_SMALL": "small", "FONT_NORMAL_COPY_1": "normal", "FONT_NORMAL": "normal",
               "FONT_NORMAL_COPY_2": "normal", "FONT_MALE": "normal", "FONT_FEMALE": "normal"}
_FONT_TABLES = {"normal": "sFontNormalLatinGlyphWidths", "small": "sFontSmallLatinGlyphWidths"}

# Linhas de charmap: `'A' = BB`, `'\'' = B4`, `PKMN = 53 54`, `'\n' = FE @ comentário`
_CHAR_ENTRY = re.compile(r"^'(\\.|[^'\\])'\s*=\s*((?:[0-9A-Fa-f]{2}\s*)+?)\s*(?:@.*)?$")
_NAME_ENTRY = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*((?:[0-9A-Fa-f]{2}\s*)+?)\s*(?:@.*)?$")
_JAPANESE_SECTION = "@ Hiragana"  # o que vem depois é só japonês/constantes (cores, sons...)
_NUMBER = re.compile(r"^(?:0[xX][0-9A-Fa-f]+|\d+)$")

# Alfabeto do `.braille` (tools/preproc/asm_file.cpp): letras sem acento, dígitos e pontuação
_BRAILLE_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ,.?!:;-/()'#$")

# Quebras de linha de texto: o resto da string continua numa linha nova da caixa
_BREAKS = {"n": "\\n", "l": "\\l", "p": "\\p"}


@dataclass
class _Entry:
    file: str
    label: str
    texts: tuple[str, ...]  # variantes do texto cru (escapes `\n`, `\p` e `{...}` como no fonte)
    needs_terminator: bool
    braille: bool = False


@dataclass
class _Env:
    chars: set[str]                 # todo caractere aceito (latino + japonês)
    latin_width: dict[str, int]     # largura em px dos caracteres da fonte latina normal
    names: set[str]                 # nomes de macro/placeholder definidos no charmap
    glyph_macros: dict[str, int]    # macros que imprimem glifos ({PKMN}, {LV}...) -> largura normal
    name_width: int                 # largura de {PLAYER}/{RIVAL}
    widths: dict[str, dict[str, int]] = field(default_factory=dict)        # fonte -> char -> px
    font_macros: dict[str, dict[str, int]] = field(default_factory=dict)   # fonte -> macro -> px
    max_letter: dict[str, int] = field(default_factory=dict)               # fonte -> letra mais larga
    char_bytes: dict[str, int] = field(default_factory=dict)
    name_bytes: dict[str, int] = field(default_factory=dict)
    prefix_px: dict[str, int] = field(default_factory=dict)                # fonte -> prefixo de batalha
    max_digit: dict[str, int] = field(default_factory=dict)                # fonte -> algarismo mais largo

    def placeholder_px(self, word: str, font: str, no_prefix: bool = False) -> int | None:
        """Largura de um placeholder de nome (None se não for um deles)."""
        if word in DYNAMIC_LETTERS:
            return DYNAMIC_LETTERS[word] * self.max_letter[font]
        if word in _PREFIXED:
            return _MON * self.max_letter[font] + (0 if no_prefix else self.prefix_px.get(font, 0))
        if word in _PREFIX_ONLY:
            return 0 if no_prefix else self.prefix_px.get(font, 0)
        return None


# ---- ambiente: charmap e tabelas de larguras -----------------------------------------------

def _load_table(repo: Path, table: str) -> list[int]:
    source = (repo / "src" / "text.c").read_text(encoding="utf-8")
    m = re.search(rf"{table}\[\]\s*=\s*\{{(.*?)\}};", source, re.S)
    if not m:
        raise RuntimeError(f"{table} não encontrada em src/text.c")
    body = re.sub(r"/\*.*?\*/|//[^\n]*", "", m.group(1), flags=re.S)
    return [int(n) for n in re.findall(r"\d+", body)]


def _load_widths(repo: Path) -> list[int]:
    return _load_table(repo, _FONT_TABLES["normal"])


def _load_env(repo: Path) -> _Env:
    tables = {font: _load_table(repo, table) for font, table in _FONT_TABLES.items()}
    chars: set[str] = set()
    widths: dict[str, dict[str, int]] = {font: {} for font in tables}
    names: set[str] = set()
    font_macros: dict[str, dict[str, int]] = {font: {} for font in tables}
    char_bytes: dict[str, int] = {}
    name_bytes: dict[str, int] = {}
    latin = True
    for raw in (repo / "charmap.txt").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith(_JAPANESE_SECTION):
            latin = False
        m = _CHAR_ENTRY.match(line)
        if m:
            ch = m.group(1)
            if ch.startswith("\\"):
                if ch != "\\'":
                    continue  # '\n', '\l', '\p' são quebras de linha, tratadas à parte
                ch = "'"
            chars.add(ch)
            data = m.group(2).split()
            char_bytes.setdefault(ch, len(data))
            first = int(data[0], 16)
            if latin:
                for font, table in tables.items():
                    widths[font].setdefault(ch, table[first])
            continue
        m = _NAME_ENTRY.match(line)
        if m:
            names.add(m.group(1))
            data = bytes.fromhex(m.group(2).replace(" ", ""))
            name_bytes.setdefault(m.group(1), len(data))
            if latin and all(b < 0xF7 for b in data):
                for font, table in tables.items():
                    font_macros[font][m.group(1)] = sum(table[b] for b in data)
            elif len(data) == 2 and data[0] == 0xF9:
                # símbolo extra (CHAR_EXTRA_SYMBOL): glifo 0x100 | byte (src/text.c:804-806)
                for font, table in tables.items():
                    font_macros[font][m.group(1)] = table[0x100 | data[1]]
    max_letter = {font: max(w for ch, w in widths[font].items() if ch.isalnum() and ch.isascii())
                  for font in tables}
    max_digit = {font: max(w for ch, w in widths[font].items() if ch.isdigit() and ch.isascii())
                 for font in tables}
    return _Env(chars, widths["normal"], names, font_macros["normal"], PLAYER_NAME_CHARS * max_letter["normal"],
                widths, font_macros, max_letter, char_bytes, name_bytes, max_digit=max_digit)


# ---- extração dos textos -------------------------------------------------------------------

_STRING_LINE = re.compile(r'^\s*\.(string|braille)\s+"((?:[^"\\]|\\.)*)"\s*(?:@.*)?$')
_LABEL_LINE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)::?\s*(?:@.*)?$")
_CONDITIONAL = re.compile(r"^[#.]\s*(if\w*|elif|elseif|else|endif)\b")  # cpp (#if) e gas (.if)


def _variants(parts: list[tuple[tuple[tuple[int, int], ...], str]]) -> tuple[str, ...]:
    """Textos possíveis de um bloco: um por combinação de ramos de `#if/#else` (em geral, um só)."""
    ids = sorted({i for conds, _ in parts for i, _branch in conds})
    combos: list[dict[int, int]] = [{}]
    for i in ids:
        branches = sorted({b for conds, _ in parts for j, b in conds if j == i})
        combos = [{**c, i: b} for c in combos for b in branches]
    texts = ["".join(t for conds, t in parts if all(c[i] == b for i, b in conds)) for c in combos]
    return tuple(dict.fromkeys(texts))


def _extract_inc_text(rel: str, source: str) -> Iterator[_Entry | Result]:
    """Blocos de `.string`/`.braille` consecutivos sob o mesmo rótulo viram um texto só.

    Ramos de `#ifdef/#else/#endif` dentro do bloco são analisados cada um como um texto próprio.
    """
    label = None
    parts: list[tuple[tuple[tuple[int, int], ...], str]] = []
    block_label = None
    braille = False
    open_conditionals: list[list[int]] = []  # [linha do #if, ramo atual]

    def flush() -> Iterator[_Entry]:
        nonlocal parts, block_label
        if parts:
            yield _Entry(rel, block_label or "?", _variants(parts), True, braille)
        parts, block_label = [], None

    for number, line in enumerate(source.splitlines(), 1):
        label_match = _LABEL_LINE.match(line)
        if label_match:
            yield from flush()
            label = label_match.group(1)
            continue
        stripped = line.strip()
        cpp = _CONDITIONAL.match(stripped)
        if cpp:
            kind = cpp.group(1)
            if kind.startswith("if"):
                open_conditionals.append([number, 0])
            elif kind == "endif":
                if open_conditionals:
                    open_conditionals.pop()
            elif open_conditionals:
                open_conditionals[-1][1] += 1
        elif stripped.startswith((".string", ".braille")):
            string_match = _STRING_LINE.match(line)
            if not string_match:
                yield Result(f"texto/{RULE_SYNTAX}", "falha",
                             f"{rel}:{number}: linha .string não reconhecida: {stripped}")
                continue
            if not parts:
                block_label = label or f"linha {number}"
                braille = string_match.group(1) == "braille"
            parts.append((tuple((i, b) for i, b in open_conditionals), string_match.group(2)))
        elif stripped and not stripped.startswith("@"):
            yield from flush()  # outra diretiva (.align, .byte...) encerra o bloco
    yield from flush()


def _scan_c_strings(source: str) -> Iterator[tuple[int, str, tuple[int, ...]]]:
    """Acha cada `_( "..." "..." )` fora de comentários; devolve (posição do `_(`, texto cru,
    posições das `{` abertas naquele ponto)."""
    n = len(source)
    braces: list[int] = []
    m = _C_TOKEN.search(source, 0)
    while m:
        tok, i = m.group(), m.start()
        if tok == "//":
            i = source.find("\n", i)
            i = n if i < 0 else i
        elif tok == "/*":
            end = source.find("*/", i + 2)
            i = n if end < 0 else end + 2
        elif tok == '"':
            i = _skip_literal(source, i)
        elif tok == "'":
            lit = _CHAR_LITERAL.match(source, i)
            i = lit.end() if lit else i + 1
        elif tok == "{":
            braces.append(i)
            i += 1
        elif tok == "}":
            if braces:
                braces.pop()
            i += 1
        else:  # `_(`
            parsed = _parse_underscore_call(source, i + 2)
            if parsed is not None:
                text, end = parsed
                yield i, text, tuple(braces)
                i = end
            else:
                i += 2
        m = _C_TOKEN.search(source, i)


_C_TOKEN = re.compile(r"//|/\*|[\"'{}]|(?<![A-Za-z0-9_])_\(")
_LITERAL = re.compile(r'"(?:[^"\\]|\\.)*"', re.S)
_CHAR_LITERAL = re.compile(r"'(?:[^'\\]|\\.)*'")


def _skip_literal(source: str, i: int) -> int:
    m = _LITERAL.match(source, i)
    return m.end() if m else len(source)


def _parse_underscore_call(source: str, i: int) -> tuple[str, int] | None:
    """Lê os literais seguidos (concatenação de strings C) até o `)`; None se não for só literais."""
    parts: list[str] = []
    n = len(source)
    while i < n:
        c = source[i]
        if c.isspace():
            i += 1
        elif source.startswith("//", i):
            i = source.find("\n", i)
            if i < 0:
                return None
        elif source.startswith("/*", i):
            end = source.find("*/", i + 2)
            if end < 0:
                return None
            i = end + 2
        elif c == '"':
            end = _skip_literal(source, i)
            parts.append(source[i + 1:end - 1])
            i = end
        elif c == ")":
            return ("".join(parts), i + 1) if parts else None
        else:
            return None
    return None


_INDEX_LABEL = re.compile(r"(?:^|[\n,{])\s*\[\s*([A-Za-z_]\w*)[^\]\n]*\]\s*(?:\[[^\]]*\]\s*)*=\s*$")
_FIELD_LABEL = re.compile(r"(?:^|[\n,{(])\s*\.([A-Za-z_]\w*)\s*=\s*$")
_VAR_LABEL = re.compile(r"(?<![.\w])([A-Za-z_]\w*)\s*(?:\[[^\]]*\]\s*)*=\s*$")


def _owner(source: str, braces: tuple[int, ...]) -> str | None:
    """Dono de um inicializador: o índice (`[X] = {`) ou a variável (`gX[] = {`) da chave aberta
    mais interna que tenha um; campos (`.trainers = {`) e chaves posicionais são atravessados."""
    for b in reversed(braces):
        before = source[max(0, b - 200):b]
        m = _INDEX_LABEL.search(before)
        if m:
            return m.group(1)
        if _FIELD_LABEL.search(before):
            continue
        m = _VAR_LABEL.search(before)
        if m:
            return m.group(1)
    return None


def _c_label(source: str, pos: int, braces: tuple[int, ...], fallback: str) -> str:
    """Rótulo de um `_(`: o índice (`[MOVE_X] = _(`), o campo com o dono (`[TRAINER_X] = {
    .trainerName = _(` -> `TRAINER_X.trainerName`), a variável (`gText_X[] = _(`) ou o dono
    de um item posicional (`gDecorations`, repetido com #n)."""
    context = source[max(0, pos - 200):pos]
    m = _INDEX_LABEL.search(context)
    if m:
        return m.group(1)
    m = _FIELD_LABEL.search(context)
    if m:
        owner = _owner(source, braces)
        return f"{owner}.{m.group(1)}" if owner else m.group(1)
    m = _VAR_LABEL.search(context)
    if m:
        return m.group(1)
    return _owner(source, braces) or fallback


def _extract_c_text(rel: str, source: str) -> Iterator[_Entry]:
    counter: dict[str, int] = {}
    for pos, text, braces in _scan_c_strings(source):
        line = source.count("\n", 0, pos) + 1
        label = _c_label(source, pos, braces, f"linha {line}")
        counter[label] = counter.get(label, 0) + 1
        if counter[label] > 1:
            label = f"{label}#{counter[label]}"
        yield _Entry(rel, label, (text,), False)


def _extract_items_text(rel: str, source: str) -> Iterator[_Entry]:
    seen: Counter[str] = Counter()
    for item in json.loads(source).get("items", []):
        item_id = item.get("itemId", "?")
        seen[item_id] += 1
        if seen[item_id] > 1:
            item_id = f"{item_id}#{seen[item_id]}"
        if item.get("english") is not None:
            yield _Entry(rel, f"{item_id}.name", (item["english"],), False)
        if item.get("description_english") is not None:
            yield _Entry(rel, item_id, (item["description_english"],), False)


def _extract_region_map_text(rel: str, source: str) -> Iterator[_Entry]:
    for section in json.loads(source).get("map_sections", []):
        if section.get("name") is not None:
            yield _Entry(rel, section.get("id", "?"), (section["name"],), False)


def _extract_novidades_text(rel: str, source: str) -> Iterator[_Entry]:
    """Tela de novidades do Prof. Carvalho (cartoes.json): `<id>.name` de cada tópico e
    `<id>.<n>.title|before|after|body` de cada cartão (n a partir de 1). A quebra de linha do JSON
    (`\\n` de verdade) entra como `\\n` literal, como no `_("...")` que o gerador escreve."""
    for topic in json.loads(source).get("topics", []):
        yield _Entry(rel, f"{topic['id']}.name", (topic["name"].replace("\n", "\\n"),), False)
        for n, card in enumerate(topic.get("cards", []), 1):
            for field in ("title", "before", "after", "body"):
                if card.get(field):
                    yield _Entry(rel, f"{topic['id']}.{n}.{field}", (card[field].replace("\n", "\\n"),), False)


def _extract_conquistas_text(rel: str, source: str) -> Iterator[_Entry]:
    """Conquistas e diário (conquistas.json): `c.<id>.nome` (com o {N} medido como 300, o maior degrau),
    `d.<id>.nome` e `d.<id>.local` de cada evento do diário."""
    data = json.loads(source)
    for conq in data.get("conquistas", []):
        yield _Entry(rel, f"c.{conq['id']}.nome", (conq["nome"].replace("{N}", "300"),), False)
    for evento in data.get("diario", []):
        yield _Entry(rel, f"d.{evento['id']}.nome", (evento["nome"],), False)
        yield _Entry(rel, f"d.{evento['id']}.local", (evento["local"],), False)


# Arquivos C fora da varredura: o que a build FireRed não compila (pokedex_text.h inclui o _fr
# ou o _lg) e os .h gerados pelo build a partir dos JSON (.gitignore), que repetem o texto da fonte
_C_EXCLUDED = {"src/data/pokemon/pokedex_text_lg.h", "src/data/items.h", "src/data/heal_locations.h",
               "src/data/region_map/region_map_entries.h", "src/data/region_map/region_map_entry_strings.h",
               "src/data/wild_encounters.h", "src/data/wild_encounters_time.h",
               "src/data/novidades_cartoes.h", "src/data/conquistas_ids.h", "src/data/conquistas_tabela.h"}
_ITEMS = "src/data/items.json"
_REGION_MAP = "src/data/region_map/region_map_sections.json"
_NOVIDADES = "src/data/novidades/cartoes.json"
_CONQUISTAS = "src/data/conquistas/conquistas.json"


def _source_files(repo: Path) -> list[tuple[str, str]]:
    """(arquivo relativo, formato) de toda fonte de texto, em ordem estável."""
    files: list[tuple[str, str]] = []

    def listdir(rel: str) -> list[os.DirEntry]:
        try:
            with os.scandir(repo / rel) as it:
                return sorted(it, key=lambda e: e.name)
        except OSError:
            return []

    files += [(f"data/text/{e.name}", "inc") for e in listdir("data/text") if e.name.endswith(".inc")]
    files += [(f"data/maps/{e.name}/text.inc", "inc") for e in listdir("data/maps")
              if e.is_dir() and (repo / "data" / "maps" / e.name / "text.inc").is_file()]
    files += [(f"data/scripts/{e.name}", "inc") for e in listdir("data/scripts") if e.name.endswith(".inc")]
    for rel in ("data/event_scripts.s", "data/mystery_event_msg.s"):
        if (repo / rel).is_file():
            files.append((rel, "inc"))
    c_files = []
    for top, dirs, names in os.walk(repo / "src"):
        dirs.sort()
        base = Path(top).relative_to(repo).as_posix()
        c_files += [f"{base}/{name}" for name in names if name.endswith((".c", ".h"))]
    files += [(rel, "c") for rel in sorted(c_files) if rel not in _C_EXCLUDED]
    for rel, kind in ((_ITEMS, "items"), (_REGION_MAP, "region_map"), (_NOVIDADES, "novidades"),
                      (_CONQUISTAS, "conquistas")):
        if (repo / rel).is_file():
            files.append((rel, kind))
    return files


_EXTRACTORS = {"inc": _extract_inc_text, "c": _extract_c_text, "items": _extract_items_text,
               "region_map": _extract_region_map_text, "novidades": _extract_novidades_text,
               "conquistas": _extract_conquistas_text}


def _extract(rel: str, kind: str, source: str) -> Iterator[_Entry | Result]:
    if kind == "c" and "_(" not in source:
        return
    yield from _EXTRACTORS[kind](rel, source)


def _read(repo: Path, rel: str) -> str:
    return (repo / rel).read_text(encoding="utf-8")


def _sources(repo: Path) -> Iterator[_Entry | Result]:
    repo = Path(repo)
    for rel, kind in _source_files(repo):
        yield from _extract(rel, kind, _read(repo, rel))


# ---- regras de janela ----------------------------------------------------------------------

def _label_matches(label: str, prefix: str | None) -> bool:
    if prefix is None:
        return True
    if prefix.endswith("$"):
        return label == prefix[:-1]
    if any(ch in prefix for ch in "*?["):
        return fnmatch.fnmatchcase(label, prefix)
    return label.startswith(prefix)


def rule_for(file: str, label: str) -> Rule | None:
    """A regra de janela do texto (a primeira que casar), ou None se nenhuma casar."""
    for rule in WIDTH_RULES:
        if fnmatch.fnmatchcase(file, rule.pattern) and _label_matches(label, rule.prefix):
            return rule
    return None


def width_limit(file: str, label: str) -> int | None:
    """Largura útil em px da caixa onde o texto aparece, ou None se não foi determinada."""
    rule = rule_for(file, label)
    return rule.px if rule else None


def fingerprint(texts: tuple[str, ...]) -> str:
    """Impressão digital do texto cru de um rótulo (todas as variantes de #if/.if)."""
    return hashlib.sha1("\x00".join(texts).encode("utf-8")).hexdigest()[:16]


# ---- análise de um texto -------------------------------------------------------------------

def _tokenize(text: str) -> Iterator[tuple[str, str]]:
    """('char', c) | ('break', 'n'/'l'/'p') | ('ph', conteúdo) | ('bad', descrição)."""
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == "\\" and i + 1 < n:
            nxt = text[i + 1]
            if nxt in _BREAKS:
                yield "break", nxt
            elif nxt == '"':
                yield "char", '"'
            else:
                yield "bad", f"escape desconhecido \\{nxt}"
            i += 2
        elif c == "{":
            end = text.find("}", i)
            if end < 0:
                yield "bad", "'{' sem '}'"
                return
            yield "ph", text[i + 1:end]
            i = end + 1
        else:
            yield "char", c
            i += 1


def _number(word: str) -> int:
    return int(word, 0)


class _Measure(NamedTuple):
    widest: int                 # px da linha mais larga (só linhas latinas)
    lines: int                  # linhas (quebras + 1, sem contar a quebra final)
    nbytes: int                 # bytes sem o terminador
    bad: list[str]              # caracteres/escapes fora do charmap (ou do braille)
    bad_words: list[str]        # placeholders desconhecidos
    ends_with_terminator: bool


def measure(text: str, env: _Env, font: str = "normal", space: int | None = None,
            braille: bool = False, no_prefix: bool = False,
            variables: dict[str, VarSize] | None = None) -> _Measure:
    """Mede um texto cru como o jogo o imprime. `variables`: tamanho de cada placeholder variável
    ({STR_VAR_n}, {B_BUFF*}...; ver var_sizes); sem ele, esses placeholders medem 0."""
    widest = width = 0
    latin_only = True
    lines = 1
    pending_break = False
    nbytes = 0
    bad: list[str] = []
    bad_words: list[str] = []
    ends = False
    cur_font = font

    def char_px(ch: str) -> int | None:
        if ch == " " and space is not None:
            return space
        return env.widths[cur_font].get(ch)

    for kind, value in _tokenize(text):
        ends = False
        if kind == "break":
            if latin_only:
                widest = max(widest, width)
            width, latin_only = 0, True
            pending_break = True
            nbytes += 1
            continue
        if pending_break and not (kind == "char" and value == "$"):
            lines += 1          # a quebra só abre linha nova se vier texto depois dela
            pending_break = False
        if kind == "bad":
            bad.append(value)
        elif kind == "char":
            if value == "$":
                ends = True     # terminador (FF): não ocupa largura nem conta como letra
                if braille:
                    continue
            if braille:
                if value not in _BRAILLE_CHARS and value not in bad:
                    bad.append(value)
                nbytes += 1
                continue
            if value not in env.chars:
                if value not in bad:
                    bad.append(value)
                nbytes += 1
            elif value != "$":
                nbytes += env.char_bytes.get(value, 1)
                px = char_px(value)
                if px is None:
                    latin_only = False  # japonês: outra fonte/tabela, não dá para medir aqui
                else:
                    width += px
        else:  # placeholder `{PALAVRA arg ...}`
            words = value.split()
            if words and words[0] in _PEN_CODES and len(words) == 2 and _NUMBER.match(words[1]):
                arg = _number(words[1])
                widest = max(widest, width) if latin_only else widest
                width = width + arg if words[0] == "CLEAR" else (max(width, arg) if words[0] == "CLEAR_TO" else arg)
            elif words and words[0] in _FONT_CODES:
                cur_font = _FONT_CODES[words[0]]
            for word in words:
                if word in env.name_bytes:
                    nbytes += env.name_bytes[word]
                elif _NUMBER.match(word):
                    nbytes += 1
                if words[0] in _PEN_CODES:
                    continue
                dynamic = env.placeholder_px(word, cur_font, no_prefix)
                if dynamic is not None:
                    width += dynamic
                elif variables and word in variables:
                    size = variables[word]
                    width += size.chars * (env.max_digit[cur_font] if size.digits else env.max_letter[cur_font])
                elif word in env.font_macros[cur_font]:
                    width += env.font_macros[cur_font][word]
                elif word not in env.names and not _NUMBER.match(word):
                    bad_words.append(word)
    if latin_only:
        widest = max(widest, width)
    return _Measure(widest, lines, nbytes, bad, bad_words, ends)


# problema: (regra, descrição, valor medido ou None)
_Problem = tuple[str, str, int | None]


def _analyze(text: str, needs_terminator: bool, rule: Rule | None, env: _Env,
             braille: bool = False) -> list[_Problem]:
    """Problemas do texto segundo a regra da janela (None = só charmap e terminador)."""
    m = measure(text, env, rule.font if rule else "normal", rule.space if rule else None, braille,
                rule.no_prefix if rule else False)
    problems: list[_Problem] = []
    alphabet = "braille" if braille else "charmap"
    for ch in m.bad:
        shown = ch if ch.startswith("escape") or ch.startswith("'{'") else f"'{ch}'"
        problems.append((RULE_CHARMAP, f"caractere fora do {alphabet}: {shown}", None))
    for word in m.bad_words:
        problems.append((RULE_CHARMAP, f"placeholder fora do charmap: {{{word}}}", None))
    if needs_terminator and not m.ends_with_terminator:
        problems.append((RULE_TERMINATOR, "terminador ausente: bloco .string não termina em '$'", None))
    if rule is not None and rule.px is not None and m.widest > rule.px:
        problems.append((RULE_WIDTH, f"largura excedida: linha com {m.widest} px, limite {rule.px} px", m.widest))
    if rule is not None and rule.lines is not None and m.lines > rule.lines:
        problems.append((RULE_LINES, f"linhas demais: {m.lines} linhas, limite {rule.lines}", m.lines))
    if rule is not None and rule.chars is not None and m.nbytes > rule.chars:
        problems.append((RULE_CHARS, f"nome longo demais: {m.nbytes} letras, limite {rule.chars}", m.nbytes))
    return problems


def box_lines(text: str) -> int:
    """Maior linha que o texto alcança numa caixa: `\\n` desce uma linha, `\\l` rola a caixa e o
    texto seguinte fica na mesma linha (a de cima sobe), `\\p` abre caixa nova. Quebra no fim do texto
    não abre linha."""
    worst = line = 1
    pending = None
    for kind, value in _tokenize(text):
        if kind == "break":
            pending = value
            continue
        if kind == "char" and value == "$":
            break
        if pending is not None:
            # \l rola a janela e volta o X, mas o Y fica (RENDER_STATE_SCROLL_START, src/text.c:872-879)
            line = 1 if pending == "p" else (line + 1 if pending == "n" else line)
            pending = None
        worst = max(worst, line)
    return worst


def _box_lines_problem(entry: _Entry, old: tuple[str, ...] | None, rule: Rule | None) -> _Problem | None:
    """Caixa com mais linhas que a janela mostra (`box_lines`), no texto mudado em relação à base:
    reprova se passa do limite e da mesma medida do rótulo inglês; rótulo novo não pode passar."""
    if rule is None or rule.box_lines is None or entry.braille:
        return None
    cur = max(box_lines(t) for t in entry.texts)
    if cur <= rule.box_lines:
        return None
    base = max(box_lines(t) for t in old) if old else None
    if base is not None and cur <= base:
        return None
    return (RULE_LINES, f"linhas demais numa caixa: {cur} linhas visíveis numa caixa de {rule.box_lines} "
            "(a linha a mais é cortada sem aviso; use \\l para rolar ou \\p para outra caixa)"
            + (f"; a base inglesa ia a {base}" if base is not None and base > rule.box_lines else ""), cur)


def _worst_case_problem(entry: _Entry, old: tuple[str, ...] | None, rule: Rule | None,
                        env: _Env) -> _Problem | None:
    """Largura com os placeholders variáveis no pior caso (var_sizes), para um texto mudado em relação
    à base inglesa (`old`; None = rótulo novo). Critério "sem piorar a base": a linha mais larga pode
    passar da janela só até onde a mesma medida do rótulo inglês já passava; rótulo novo não pode passar."""
    if rule is None or rule.px is None or entry.braille:
        return None
    sizes = var_sizes(entry.file, entry.label)

    def widest(texts: tuple[str, ...]) -> int:
        return max(measure(t, env, rule.font, rule.space, False, rule.no_prefix, sizes).widest for t in texts)

    cur = widest(entry.texts)
    if cur <= rule.px:
        return None
    base = widest(old) if old else None
    if base is not None and cur <= base:
        return None
    used = [f"{{{name}}} = {sizes[name].describe()}" for name in sizes
            if any(has_var(t, name) for t in entry.texts)]
    detail = (f"largura excedida no pior caso ({', '.join(used)}): linha com {cur} px, limite {rule.px} px"
              + (f"; a base inglesa ia a {base} px" if base is not None and base > rule.px else ""))
    return (RULE_WIDTH, detail, cur)


# ---- controle: códigos de controle iguais aos da base inglesa ------------------------------

def control_codes(text: str, glyphs: frozenset[str] = frozenset()) -> Counter[str]:
    """Placeholders/códigos de controle e terminadores de um texto (sem as quebras de linha).
    Macros que só imprimem glifos (`glyphs`: {LV_2}, {PKMN}, {ID}, {NO}...) não contam: trocar
    "{LV_2}" por "Nv." é tradução, não código perdido."""
    codes: Counter[str] = Counter()
    for kind, value in _tokenize(text):
        if kind == "ph":
            if value.split() and all(word in glyphs for word in value.split()):
                continue
            codes["{" + " ".join(value.split()) + "}"] += 1
        elif kind == "char" and value == "$":
            codes["$"] += 1
    return codes


def _control_problem(texts: tuple[str, ...], base_texts: tuple[str, ...],
                     glyphs: frozenset[str] = frozenset()) -> _Problem | None:
    cur = [control_codes(t, glyphs) for t in texts]
    old = [control_codes(t, glyphs) for t in base_texts]
    if len(cur) != len(old):
        cur, old = [sum(cur, Counter())], [sum(old, Counter())]
    missing: Counter[str] = Counter()
    extra: Counter[str] = Counter()
    for c, o in zip(cur, old):
        missing += o - c
        extra += c - o
    if not missing and not extra:
        return None
    parts = []
    if missing:
        parts.append("faltam " + " ".join(sorted(missing.elements())))
    if extra:
        parts.append("sobram " + " ".join(sorted(extra.elements())))
    return (RULE_CONTROL, "códigos de controle diferentes do original: " + "; ".join(parts), None)


# ---- base inglesa (git) --------------------------------------------------------------------

class _Base(NamedTuple):
    texts: dict[tuple[str, str], tuple[str, ...]]   # (arquivo, rótulo) dos arquivos mudados
    changed: set[str]                                # arquivos com conteúdo diferente da base
    present: set[str]                                # arquivos que existem na base


def _git(repo: Path, *args: str, stdin: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], input=stdin, capture_output=True, timeout=120)


def _blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\x00" % len(data) + data).hexdigest()


def _load_base(repo: Path, base: str, contents: dict[str, tuple[str, bytes]]) -> _Base | str | None:
    """Textos da base para os arquivos que mudaram. None = pasta sem `.git` (fixtures, espelho do
    teste lento: sem comparação); str = motivo de a base não estar disponível (vira aviso)."""
    if not (repo / ".git").exists():
        return None
    try:
        top = _git(repo, "rev-parse", "--show-prefix")
    except (OSError, subprocess.SubprocessError) as exc:
        return f"o git não rodou: {exc}"
    if top.returncode != 0:
        return f"git rev-parse falhou: {top.stderr.decode(errors='replace').strip()}"
    prefix = top.stdout.decode().strip()
    if _git(repo, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}").returncode != 0:
        return f"commit base {base} não encontrado neste repositório"
    tree = _git(repo, "ls-tree", "-r", "--full-tree", base, "--", f"{prefix}data", f"{prefix}src")
    if tree.returncode != 0:
        return f"git ls-tree {base} falhou: {tree.stderr.decode(errors='replace').strip()}"
    shas: dict[str, str] = {}
    for line in tree.stdout.decode("utf-8", errors="replace").splitlines():
        meta, _, path = line.partition("\t")
        if path.startswith(prefix):
            shas[path[len(prefix):]] = meta.split()[2]
    changed_paths = [rel for rel, (_kind, data) in contents.items()
                     if rel in shas and _blob_sha(data) != shas[rel]]
    texts: dict[tuple[str, str], tuple[str, ...]] = {}
    changed: set[str] = set()
    if changed_paths:
        batch = _git(repo, "cat-file", "--batch", stdin="".join(f"{shas[r]}\n" for r in changed_paths).encode())
        out, pos = batch.stdout, 0
        for rel in changed_paths:
            header_end = out.find(b"\n", pos)
            header = out[pos:header_end].split() if header_end >= 0 else []
            if len(header) < 3 or header[1] != b"blob":
                # "<sha> missing" (objeto ausente no clone) ou resposta cortada: o arquivo conta
                # como mudado e os rótulos dele como novos (só o glossário roda)
                changed.add(rel)
                pos = header_end + 1 if header_end >= 0 else len(out)
                continue
            size = int(header[2])
            data = out[header_end + 1:header_end + 1 + size].decode("utf-8", errors="replace")
            pos = header_end + 1 + size + 1
            kind, current = contents[rel]
            if data.replace("\r\n", "\n") == current.decode("utf-8").replace("\r\n", "\n"):
                continue
            changed.add(rel)
            for entry in _extract(rel, kind, data):
                if isinstance(entry, _Entry):
                    texts[(entry.file, entry.label)] = entry.texts
    return _Base(texts, changed, set(shas))


# ---- inglês residual -----------------------------------------------------------------------

# Palavras inglesas comuns que não existem em português (nada de "a", "no", "me", "do", "as",
# "for", "come", "more", "time", "some"...): bastam para achar frase sem tradução. Só a primeira
# variante de #if/.if de cada texto é contada.
ENGLISH_WORDS = frozenset("""
the you your yours you're you've you'll you'd and with this that these those have has had having
what are were was is isn't aren't wasn't weren't there their they they're them from will won't
would wouldn't can can't cannot could couldn't should shouldn't not don't doesn't didn't does did
it it's its i'm i've i'll i'd we we're we've our ours us he he's she she's his her him hers who
whom whose which why how when where here now then than been being be because about after before
again just only also too very really any every each other others another all but if or so get gets
got getting give gives gave given take takes took make makes made let let's look looks see sees
saw seen know knows knew think thought want wants wanted need needs tell told say said says go
goes going went gone back still yet way thing things something anything nothing everything
someone anyone everyone people world into out over under through while until please thank
thanks yes yeah well better most much many little big new old first last next one two three day
of to in on at an by my up out off with your yourself myself
""".split())
_WORD = re.compile(r"[A-Za-zÀ-ÿ]+(?:'[A-Za-z]+)?")
# Lista de permissões: arquivos e rótulos que ficam em inglês/japonês de propósito
_ENGLISH_SKIP_FILES = ("src/data/text/species_names.h",)
_ENGLISH_SKIP_LABELS = ("gCreditsString_*", "gJPText_*", "*.trainerName")
# Título da ajuda que é só a sigla "TO" (Treinador Original), sem letra minúscula
_TO_TITLE_LABELS = frozenset({"Help_Text_OT"})


@dataclass
class EnglishCount:
    words: int = 0
    texts: int = 0
    examples: list[str] = field(default_factory=list)


def _plain_words(text: str) -> list[str]:
    plain = re.sub(r"\{[^}]*\}", " ", text)
    plain = re.sub(r"\\[nlp]", " ", plain)
    return _WORD.findall(plain)


def _english_allowed_names(entries: list[_Entry]) -> set[str]:
    """Nomes próprios que coincidem com palavras inglesas: espécies e Treinadores."""
    names: set[str] = set()
    for e in entries:
        if e.file == "src/data/text/species_names.h" or (
                e.file == "src/data/trainers.h" and e.label.endswith(".trainerName")):
            for text in e.texts:
                names.update(w.lower() for w in _plain_words(text))
    return names


def _english_words(entry: _Entry, allowed: set[str]) -> list[str]:
    if entry.file in _ENGLISH_SKIP_FILES or any(fnmatch.fnmatchcase(entry.label, p) for p in _ENGLISH_SKIP_LABELS):
        return []
    found: list[str] = []
    for text in entry.texts[:1]:
        # "TO" = Treinador Original: só vale em frase em PT-BR (tem letra minúscula) ou no título da ajuda;
        # em texto todo em maiúsculas ("BELONGS TO", "A WINDOW TO", "TO ME") é o inglês que ainda falta traduzir
        plain = " ".join(_plain_words(text))
        to_is_acronym = entry.label in _TO_TITLE_LABELS or any(c.islower() for c in plain)
        for word in _plain_words(text):
            if word == "TO" and to_is_acronym:
                continue
            low = word.lower()
            if low in ENGLISH_WORDS and low not in allowed:
                found.append(low)
    return found


def english_report(repo: str, entries: list[_Entry] | None = None) -> dict[str, EnglishCount]:
    """Palavras inglesas por arquivo (só arquivos com alguma)."""
    if entries is None:
        entries = [e for e in _sources(Path(repo)) if isinstance(e, _Entry)]
    allowed = _english_allowed_names(entries)
    report: dict[str, EnglishCount] = {}
    for entry in entries:
        words = _english_words(entry, allowed)
        if words:
            count = report.setdefault(entry.file, EnglishCount())
            count.words += len(words)
            count.texts += 1
            if len(count.examples) < 3:
                count.examples.append(entry.label)
    return report


def _plural(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def _english_progress(report: dict[str, EnglishCount]) -> Result | None:
    if not report:
        return None
    words = sum(c.words for c in report.values())
    texts = sum(c.texts for c in report.values())
    top = sorted(report.items(), key=lambda kv: (-kv[1].words, kv[0]))[:5]
    return Result(f"texto/{RULE_ENGLISH}", "aviso",
                  f"modo progresso: {_plural(words, 'palavra', 'palavras')} em inglês em "
                  f"{_plural(texts, 'texto', 'textos')} de {_plural(len(report), 'arquivo', 'arquivos')}; "
                  "maiores: " + ", ".join(f"{f} ({c.words})" for f, c in top)
                  + "; lista completa: python3 -m esteira.check_text --ingles")


# ---- ponto de entrada ----------------------------------------------------------------------

class _Scan(NamedTuple):
    syntax: list[Result]
    entries: dict[tuple[str, str], tuple[str, list[_Problem]]]
    raw: list[_Entry]
    base_note: str | None          # motivo de a comparação com a base não ter rodado
    rules: dict[tuple[str, str], list[tuple[Rule, str | None]]]   # janelas de cada texto (e onde é usado)
    base: "_Base | None" = None    # textos da base inglesa (None: sem .git ou base indisponível)
    env: "_Env | None" = None


_USAGE_SCRIPTS = ("data/event_scripts.s",)


def _usage_rules(raw: list[_Entry], texts: dict[str, str]) -> dict[tuple[str, str], list[tuple[Rule, str | None]]]:
    """Janelas dos textos com `by_usage`: uma por uso que casa com esteira/janelas_uso.USAGE_RULES."""
    from esteira import janelas_uso
    targets: dict[str, list[_Entry]] = {}
    for e in raw:
        rule = rule_for(e.file, e.label)
        if rule is not None and rule.by_usage:
            # `gX#2` usa os usos de `gX`; `DONO.campo` (item de struct) os da variável DONO
            targets.setdefault(e.label.split("#")[0].split(".")[0], []).append(e)
    index = janelas_uso.usage_index(texts, set(targets))
    out: dict[tuple[str, str], list[tuple[Rule, str | None]]] = {}
    for label, entries in targets.items():
        uses = sorted(index.get(label, ()))
        for e in entries:
            found: dict[tuple, tuple[Rule, str | None]] = {}
            unmatched = []
            for use_file, ctx in uses:
                u = janelas_uso.match(use_file, ctx, label)
                if u is None:
                    unmatched.append(f"{use_file} ({ctx})")
                    continue
                key = (u.px, u.font, u.lines, u.chars, u.source)
                box = DIALOG_BOX_LINES if u.source.startswith(janelas_uso._DIALOG) else None
                found.setdefault(key, (Rule(e.file, e.label, u.px, f"usado em {use_file} ({ctx}): {u.source}",
                                            u.font, u.lines, u.chars, box_lines=box), f"{use_file}, {ctx}"))
            if not found:
                why = ("sem uso no código: texto morto" if not uses
                       else "usado sem regra de janela: " + ", ".join(unmatched[:3]))
                found[("none",)] = (Rule(e.file, e.label, None, why), None)
            out[(e.file, e.label)] = list(found.values())
    return out


def _scan(root: Path, base: str | None, english: str = "desligado") -> _Scan:
    env = _load_env(root)
    files = _source_files(root)
    syntax: list[Result] = []
    raw: list[_Entry] = []
    contents: dict[str, tuple[str, bytes]] = {}   # arquivos com texto: (formato, bytes)
    usage_texts: dict[str, str] = {}             # código onde os rótulos são usados
    for rel, kind in files:
        data = (root / rel).read_bytes()
        found = False
        text = data.decode("utf-8")
        if kind == "c" or rel in _USAGE_SCRIPTS:
            usage_texts[rel] = text
        for entry in _extract(rel, kind, text):
            found = True
            if isinstance(entry, Result):
                syntax.append(entry)
            else:
                raw.append(entry)
        if found:
            contents[rel] = (kind, data)
    env.prefix_px = {font: max((measure(e.texts[0], env, font).widest for e in raw
                                if e.file == "src/battle_message.c" and _PREFIX_LABEL.match(e.label)),
                               default=0)
                     for font in env.widths}
    loaded = _load_base(root, base, contents) if base else None
    base_info = loaded if isinstance(loaded, _Base) else None
    note = loaded if isinstance(loaded, str) else None
    glossary = None
    glyphs = frozenset(env.font_macros["normal"])     # macros que só imprimem glifos
    allowed = _english_allowed_names(raw) if english == "bloqueante" else set()
    entries: dict[tuple[str, str], tuple[str, list[_Problem]]] = {}
    usage = _usage_rules(raw, usage_texts)
    rules_of: dict[tuple[str, str], list[tuple[Rule, str | None]]] = {}
    for entry in raw:
        key = (entry.file, entry.label)
        rules_of[key] = usage.get(key) or [(rule_for(entry.file, entry.label), None)]
        # arquivo mudado: compara rótulo a rótulo; arquivo novo: tudo é novo (sem original)
        compared = base_info is not None and (entry.file in base_info.changed or entry.file not in base_info.present)
        old = base_info.texts.get(key) if compared else None
        changed = compared and old != entry.texts
        problems = []
        seen_rules: set[str] = set()
        for rule, where in rules_of[key]:
            found = [p for text in entry.texts
                     for p in _analyze(text, entry.needs_terminator, rule, env, entry.braille)]
            if changed:
                worst = _worst_case_problem(entry, old, rule, env)
                if worst:
                    found.append(worst)
                boxes = _box_lines_problem(entry, old, rule)
                if boxes:
                    found.append(boxes)
            for name, detail, value in found:
                if name in seen_rules and name in (RULE_WIDTH, RULE_LINES, RULE_CHARS):
                    continue      # a primeira janela que estoura basta
                if where and name in (RULE_WIDTH, RULE_LINES, RULE_CHARS):
                    detail = f"{detail} (janela de {where})"
                if (name, detail, value) not in problems:
                    problems.append((name, detail, value))
                if name in (RULE_WIDTH, RULE_LINES, RULE_CHARS):
                    seen_rules.add(name)
        if compared:
            if changed:
                if old is not None:
                    control = _control_problem(entry.texts, old, glyphs)
                    if control:
                        problems.append(control)
                if glossary is None:
                    from esteira.glossario import load as load_glossary
                    glossary = load_glossary()
                found = list(dict.fromkeys(p for text in entry.texts for p in glossary.problems(text)))
                if found:
                    problems.append((RULE_GLOSSARY, "; ".join(found), None))
        if english == "bloqueante":
            words = _english_words(entry, allowed)
            if words:
                problems.append((RULE_ENGLISH, f"texto em inglês ({len(words)} palavras: "
                                 f"{', '.join(dict.fromkeys(words))})", None))
        entries[(entry.file, entry.label)] = (fingerprint(entry.texts), problems)
    return _Scan(syntax, entries, raw, note, rules_of, base_info, env)


def _evolution_page_results(root: Path) -> list[Result]:
    """Hack 4: largura de cada linha da página EVOLUTION, montada para toda espécie com os
    nomes de verdade (os rótulos gText_PokeSum_Evo* sozinhos não dizem o tamanho final). Repo
    sem os fontes da página (fixtures) não é checado."""
    from esteira.constants import Constants
    from esteira.evolution_page import (LINE_WIDTH_PX, SOURCE_FILES, SOURCE_REF,
                                        check_page_widths)
    if not all((root / path).is_file() for path in SOURCE_FILES):
        return []
    consts = Constants.load(str(root), ["species.h"])
    return [Result(f"texto/{RULE_WIDTH}", "falha",
                   f"src/strings.c: página EVOLUTION de {species}: '{line}' com {px} px, limite "
                   f"{LINE_WIDTH_PX} px ({SOURCE_REF})")
            for species, line, px in check_page_widths(root, consts)]


def _ivev_page_results(root: Path) -> list[Result]:
    """Hack 5: largura das linhas da página IVs/EVs (com as colunas {SKIP x}) para os textos e
    números mais largos possíveis, e colunas que encavalariam. Repo sem os fontes não é checado."""
    from esteira.ivev_page import LINE_WIDTH_PX, SOURCE_FILES, check_page_widths
    if not all((root / path).is_file() for path in SOURCE_FILES):
        return []
    return [Result(f"texto/{RULE_WIDTH}", "falha",
                   f"src/strings.c: página IVs/EVs: '{line}'"
                   + (f" com {px} px, limite {LINE_WIDTH_PX} px" if px else ""))
            for line, px in check_page_widths(root)]


def _shared_row_results(root: Path, raw: list[_Entry]) -> list[Result]:
    """Dois textos que dividem a mesma linha (esteira/janelas_uso.SHARED_ROWS): o da esquerda
    não pode encostar no que vem alinhado à direita."""
    from esteira.janelas_uso import SHARED_ROWS
    env = None
    out: list[Result] = []
    for row in SHARED_ROWS:
        lefts = [e for e in raw if e.file == row.file and fnmatch.fnmatchcase(e.label, row.left)]
        rights = [e for e in raw if e.file == row.file and e.label == row.right]
        if not lefts or not rights:
            continue
        env = env or _load_env(root)
        right_px = max(measure(t.rstrip("$") + row.right_suffix, env, row.font).widest
                       for e in rights for t in e.texts)
        room = row.edge_px - right_px - row.start_px
        for e in lefts:
            px = max(measure(t, env, row.font).widest for t in e.texts)
            if px > room:
                out.append(Result(f"texto/{RULE_WIDTH}", "falha",
                                  f"{row.file}: {e.label}: largura excedida: {px} px, mas só sobram {room} px na "
                                  f"linha que divide com {row.right} ({right_px} px à direita) ({row.source})"))
    return out


class KnownFinding(NamedTuple):
    """Achado de uma regra nova que já está na hack-switch e tem dona: vira `aviso` (não reprova)
    enquanto o texto for o mesmo (fingerprint) e a medida também; corrigido, vira aviso de
    obsoleto. Diferente de `excecoes.json` (que cala), o aviso aparece em todo relatório."""
    file: str
    label: str
    rule: str
    fingerprint: str
    valor: int | None
    why: str


# Achados da regra de linhas por caixa (escopo 9 da T4) de 21/10 foram todos corrigidos (B2c, 22/10): nenhum conhecido
KNOWN_FINDINGS: list[KnownFinding] = []


def check_text(repo: str, exceptions: dict, english: str = ENGLISH_MODE,
               base: str | None = TRANSLATION_BASE) -> list[Result]:
    """Todas as regras sobre os textos de `repo`. `base`: commit da versão inglesa (None = sem
    `controle`/`glossario`); `english`: modo da regra `ingles`."""
    if english not in ENGLISH_MODES:
        raise ValueError(f"modo de inglês desconhecido: {english}")
    scan = _scan(Path(repo), base, english)
    results = (list(scan.syntax) + _evolution_page_results(Path(repo)) + _ivev_page_results(Path(repo))
               + _shared_row_results(Path(repo), scan.raw))
    if scan.base_note:
        for rule in (RULE_CONTROL, RULE_GLOSSARY):
            results.append(Result(f"texto/{rule}", "aviso",
                                  f"base inglesa indisponível ({scan.base_note}): a regra {rule} não rodou"))
        results.append(Result(f"texto/{RULE_WIDTH}", "aviso",
                              f"base inglesa indisponível ({scan.base_note}): a largura no pior caso dos "
                              "placeholders variáveis ({STR_VAR_n}, {B_BUFF*}...) não rodou"))
        results.append(Result(f"texto/{RULE_BUFFER}", "aviso",
                              f"base inglesa indisponível ({scan.base_note}): o estouro de buffer de string "
                              "(esteira/buffers.py) não rodou"))
    elif scan.base is not None:
        # estouro de buffer de string (Task T4): só com a base, pelo critério "sem piorar a base"
        from esteira.buffers import check_buffers
        results += check_buffers(Path(repo), scan.raw, scan.base, scan.env)   # contexto em cache por processo
    entries = scan.entries
    frozen = exceptions.get("text", [])
    applied: set[tuple[str, str, str]] = set()  # exceções que de fato calaram um achado

    def ignored(rule: str) -> bool:
        return rule == RULE_ENGLISH and english != "bloqueante"

    silenced: dict[tuple[str, str, str], dict] = {}
    for exc in frozen:
        key = (exc["file"], exc["label"])
        if key not in entries or ignored(exc["rule"]):
            continue
        if exc.get("fingerprint") != entries[key][0]:
            continue
        silenced[(exc["file"], exc["label"], exc["rule"])] = exc

    known = {(k.file, k.label, k.rule): k for k in KNOWN_FINDINGS}
    known_used: set[KnownFinding] = set()
    for (file, label), (fp, problems) in entries.items():
        for rule, detail, value in problems:
            exc = silenced.get((file, label, rule))
            if exc is not None and exc.get("valor") in (None, value):
                applied.add((file, label, rule))
                continue
            k = known.get((file, label, rule))
            if k is not None and k.fingerprint == fp and k.valor in (None, value):
                known_used.add(k)
                results.append(Result(f"texto/{rule}", "aviso", f"{file}: {label}: {detail} (conhecido: {k.why})"))
                continue
            results.append(Result(f"texto/{rule}", "falha", f"{file}: {label}: {detail}"))
    for k in KNOWN_FINDINGS:
        if k not in known_used and (k.file, k.label) in entries:
            results.append(Result(f"texto/{k.rule}", "aviso",
                                  f"achado conhecido não ocorre mais em {k.file}: {k.label} ({k.rule}); remova-o "
                                  "de KNOWN_FINDINGS (esteira/check_text.py)"))

    for exc in frozen:
        file, label, rule = exc["file"], exc["label"], exc["rule"]
        if ignored(rule) or (file, label, rule) in applied:
            continue
        if (file, label) not in entries:
            why = "o rótulo não existe mais"
        elif exc.get("fingerprint") != entries[(file, label)][0]:
            why = "o texto mudou desde o congelamento"
        else:
            why = "o problema não ocorre mais (ou mudou de valor)"
        results.append(Result(f"texto/{RULE_OBSOLETE}", "aviso",
                              f"exceção obsoleta ({rule}) em {file}: {label}: {why}; remova-a de excecoes.json"))

    if english == "progresso":
        progress = _english_progress(english_report(repo, scan.raw))
        if progress:
            results.append(progress)
    return results


def effective_rules(repo: str) -> dict[tuple[str, str], list[Rule]]:
    """Janelas de cada texto como a checagem as usa: a regra fixa de `WIDTH_RULES` ou, nos textos
    com `by_usage`, uma por janela onde o rótulo é usado (esteira/janelas_uso.py)."""
    scan = _scan(Path(repo), None)
    return {key: [rule for rule, _where in rules] for key, rules in scan.rules.items()}


def coverage_kind(rules: list[Rule | None]) -> str:
    """"largura" (alguma janela mede px), "letras" (só limite de bytes) ou "sem medida"."""
    rules = [r for r in rules if r is not None]
    if any(r.px is not None for r in rules):
        return "largura"
    if any(r.chars is not None or r.lines is not None for r in rules):
        return "letras"
    return "sem medida"


def compute_baseline(repo: str, base: str | None = TRANSLATION_BASE, english: str = ENGLISH_MODE) -> list[dict]:
    """Exceções (ordenadas) que congelam todos os problemas de texto atuais; o inglês residual entra
    só com `english="bloqueante"` (o modo do pipeline), o único em que a regra `ingles` falha por texto."""
    if english not in ENGLISH_MODES:
        raise ValueError(f"modo de inglês desconhecido: {english}")
    scan = _scan(Path(repo), base, english)
    if scan.syntax:
        raise ValueError(f"linhas .string não reconhecidas: {[r.detail for r in scan.syntax]}")
    baseline = []
    for (file, label), (fp, problems) in sorted(scan.entries.items()):
        for rule, _detail, value in sorted(problems, key=lambda p: p[0]):
            exc = {"file": file, "label": label, "rule": rule, "fingerprint": fp}
            if value is not None:
                exc["valor"] = value
            if exc not in baseline:
                baseline.append(exc)
    return baseline


# ---- CLI -----------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m esteira.check_text",
                                     description="Relatórios da checagem de texto.")
    parser.add_argument("--ingles", action="store_true", help="palavras inglesas por arquivo")
    parser.add_argument("--regras", action="store_true",
                        help="quantos textos cada regra de janela cobre (e quais ficam sem medida)")
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("arquivos", nargs="*", help="só estes arquivos (relativos ao repo)")
    args = parser.parse_args(argv)
    if args.regras:
        scan = _scan(Path(args.repo), None)
        counts: Counter[tuple[str, str]] = Counter()
        kinds: Counter[str] = Counter()
        for (file, label), rules in scan.rules.items():
            if args.arquivos and file not in args.arquivos:
                continue
            rules = [r for r, _where in rules]
            kinds[coverage_kind(rules)] += 1
            for rule in rules:
                if rule is None:
                    counts[(file, "sem regra")] += 1
                    continue
                limits = ", ".join(f"{name} {value}" for name, value in (
                    ("px", rule.px), ("linhas", rule.lines), ("letras", rule.chars)) if value is not None)
                where = rule.source.split(":")[0] if rule.source.startswith("usado em") else (rule.prefix or "")
                counts[(file, f"{where}  [{limits or 'sem medida: ' + rule.source}]")] += 1
        for (file, desc), n in sorted(counts.items()):
            print(f"{n:6d}  {file} {desc}")
        print("textos: " + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())))
        return 0
    if not args.ingles:
        parser.error("escolha um relatório (--ingles ou --regras)")
    report = english_report(args.repo)
    wanted = set(args.arquivos)
    rows = sorted((f, c) for f, c in report.items() if not wanted or f in wanted)
    for f, c in rows:
        print(f"{c.words:6d} palavras  {c.texts:5d} textos  {f}  (ex.: {', '.join(c.examples)})")
    for f in sorted(wanted - set(report)):
        print(f"     0 palavras      0 textos  {f}")
    print(f"total: {sum(c.words for _, c in rows)} palavras em {sum(c.texts for _, c in rows)} textos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
